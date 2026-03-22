"""Recommender agent — matches posts to user profiles via Bedrock Claude."""

import asyncio
import json
import logging
import math
from datetime import datetime

import boto3
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from crawler.config import (
    AWS_ACCESS_KEY_ID,
    AWS_DEFAULT_REGION,
    AWS_SECRET_ACCESS_KEY,
    DATABASE_URL,
)

logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"

_PROMPT = (
    "You are a career recommendation assistant for Korean university students.\n"
    "Given a student profile and a job/competition/hackathon post, evaluate relevance.\n\n"
    "Student profile:\n"
    "- School: {school}\n"
    "- Major: {major}\n"
    "- Grade: {grade}\n"
    "- 정보 중심: {info_focus}\n"
    "- 자기소개: {bio}\n\n"
    "Post:\n"
    "- Title: {title}\n"
    "- Company: {company}\n"
    "- Category: {category}\n"
    "- Deadline: {deadline}\n"
    "- Description: {description}\n\n"
    "Return ONLY a JSON object with these keys:\n"
    '- "reason": a short Korean explanation of why this post is relevant\n'
    '- "todos": an array of objects [{{"task": "할 일", "due": "YYYY-MM-DD"}}]\n'
    '- "relevance_score": float between 0.0 and 1.0\n'
    "Return ONLY valid JSON, no other text."
)

USER_BATCH_SIZE = 50
TOP_K = 10


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url
    return "postgresql+asyncpg://" + url.split("://", 1)[-1]


class RecommenderAgent:
    def __init__(self) -> None:
        self._engine: AsyncEngine = create_async_engine(_async_url(DATABASE_URL))
        self._bedrock = boto3.client(
            "bedrock-runtime",
            region_name=AWS_DEFAULT_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

    async def run(self, since: datetime) -> int:
        """Match posts created after `since` to all users. Returns count of recommendations stored."""
        all_posts = await self._fetch_posts(since)
        if not all_posts:
            return 0

        # Stage 1: pre-compute post embeddings once
        post_embeddings: list[tuple[dict, list[float]]] = []
        for p in all_posts:
            text_ = f"{p.get('title', '')} {p.get('company') or ''} {p.get('category', '')} {(p.get('description') or '')[:500]}"
            emb = await self._embed(text_)
            if emb:
                post_embeddings.append((p, emb))

        stored = 0
        offset = 0
        while True:
            users = await self._fetch_users(offset)
            if not users:
                break
            for user in users:
                excluded = await self._fetch_excluded(user["id"])
                candidates = [(p, e) for p, e in post_embeddings if p["id"] not in excluded]
                if not candidates:
                    continue

                # Stage 1: top-k by embedding similarity
                top_posts = await self._top_k_posts(user, candidates, TOP_K)
                if not top_posts:
                    continue

                # Stage 2: Bedrock Claude scoring on top-k only
                async def _score(u: dict, p: dict) -> tuple[dict, dict | None]:
                    return p, await self._call_bedrock(u, p)

                results = await asyncio.gather(*[_score(user, p) for p in top_posts])
                for post, rec in results:
                    if rec and rec.get("relevance_score", 0) >= 0.5:
                        await self._upsert(user["id"], post["id"], rec)
                        stored += 1
            offset += USER_BATCH_SIZE

        logger.info("Stored %d recommendations", stored)
        return stored

    async def _embed(self, text_: str) -> list[float] | None:
        """Return embedding vector via Bedrock Titan Embeddings v2."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, text_)

    def _embed_sync(self, text_: str) -> list[float] | None:
        try:
            resp = self._bedrock.invoke_model(
                modelId=EMBED_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text_}),
            )
            return json.loads(resp["body"].read())["embedding"]
        except Exception:
            logger.exception("Embedding call failed")
            return None

    async def _top_k_posts(
        self,
        user: dict,
        post_embeddings: list[tuple[dict, list[float]]],
        k: int,
    ) -> list[dict]:
        """Embed user profile, rank posts by cosine similarity, return top-k."""
        info_focus = ", ".join(user.get("info_focus") or []) or "없음"
        user_text = f"학교: {user.get('school', '')}, 전공: {user.get('major', '')}, 학년: {user.get('grade', '')}, 정보 중심: {info_focus}, 자기소개: {user.get('bio') or '없음'}"
        user_emb = await self._embed(user_text)
        if not user_emb:
            return [p for p, _ in post_embeddings[:k]]

        scored = []
        for post, emb in post_embeddings:
            dot = sum(a * b for a, b in zip(user_emb, emb))
            mag_u = math.sqrt(sum(a * a for a in user_emb))
            mag_p = math.sqrt(sum(a * a for a in emb))
            sim = dot / (mag_u * mag_p) if mag_u and mag_p else 0.0
            scored.append((sim, post))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:k]]

    async def _fetch_posts(self, since: datetime) -> list[dict]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT id, title, company, deadline, description, category FROM posts"
                    " WHERE created_at > :since"
                    " AND (deadline IS NULL OR deadline > NOW())"
                ),
                {"since": since},
            )
            return [dict(r._mapping) for r in rows]

    async def _fetch_excluded(self, user_id: int) -> set[int]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text("SELECT post_id FROM ai_recommendations WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            return {r[0] for r in rows}

    async def _fetch_users(self, offset: int) -> list[dict]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text("SELECT id, school, major, grade, info_focus, bio FROM users WHERE school != '' AND major != '' ORDER BY id LIMIT :limit OFFSET :offset"),
                {"limit": USER_BATCH_SIZE, "offset": offset},
            )
            return [dict(r._mapping) for r in rows]

    async def _call_bedrock(self, user: dict, post: dict) -> dict | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_bedrock_sync, user, post)

    def _call_bedrock_sync(self, user: dict, post: dict) -> dict | None:
        info_focus = ", ".join(user.get("info_focus") or []) or "없음"
        prompt = _PROMPT.format(
            school=user.get("school", ""),
            major=user.get("major", ""),
            grade=user.get("grade", ""),
            info_focus=info_focus,
            bio=user.get("bio") or "없음",
            title=post.get("title", ""),
            company=post.get("company") or "N/A",
            category=post.get("category", ""),
            deadline=str(post.get("deadline") or "N/A"),
            description=(post.get("description") or "")[:3000],
        )
        try:
            resp = self._bedrock.invoke_model(
                modelId=MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                }),
            )
            raw = json.loads(resp["body"].read())["content"][0]["text"].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            data = json.loads(raw)
            if isinstance(data, dict) and "relevance_score" in data:
                return data
            return None
        except Exception:
            logger.exception("Bedrock call failed for user=%s post=%s", user["id"], post["id"])
            return None

    async def _upsert(self, user_id: int, post_id: int, rec: dict) -> None:
        stmt = text("""
            INSERT INTO ai_recommendations (user_id, post_id, reason, todos, relevance_score)
            VALUES (:user_id, :post_id, :reason, :todos, :relevance_score)
            ON CONFLICT (user_id, post_id) DO UPDATE SET
                reason = EXCLUDED.reason,
                todos = EXCLUDED.todos,
                relevance_score = EXCLUDED.relevance_score
        """)
        async with self._engine.begin() as conn:
            await conn.execute(stmt, {
                "user_id": user_id,
                "post_id": post_id,
                "reason": rec.get("reason", ""),
                "todos": rec.get("todos", []),
                "relevance_score": float(rec.get("relevance_score", 0)),
            })
