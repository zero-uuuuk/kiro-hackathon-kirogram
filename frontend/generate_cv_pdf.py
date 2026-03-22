#!/usr/bin/env python3
"""SchedAI 시연용 CV PDF 생성 스크립트"""
from fpdf import FPDF
import os

class CVPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        # 한글 폰트 등록
        font_map = [
            ("Korean", "", os.path.expanduser("~/Library/Fonts/NanumSquareR.ttf")),
            ("Korean", "B", os.path.expanduser("~/Library/Fonts/NanumSquareB.ttf")),
        ]
        for name, style, fp in font_map:
            if os.path.exists(fp):
                self.add_font(name, style, fp)
            else:
                raise RuntimeError(f"폰트를 찾을 수 없습니다: {fp}")

    def section_title(self, title):
        self.set_font("Korean", "B", 13)
        self.set_text_color(88, 28, 135)  # purple-800
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(168, 85, 247)  # purple-500
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def body_text(self, text, size=10, bold=False):
        self.set_font("Korean", "B" if bold else "", size)
        self.set_text_color(30, 41, 59)  # slate-800
        self.multi_cell(0, 6, text)
        self.ln(1)

    def bullet(self, text, indent=8):
        x = self.get_x()
        self.set_font("Korean", "", 9.5)
        self.set_text_color(51, 65, 85)  # slate-700
        self.cell(indent)
        self.multi_cell(0, 5.5, f"•  {text}")
        self.ln(0.5)

    def sub_heading(self, text):
        self.set_font("Korean", "B", 11)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def light_text(self, text, size=9):
        self.set_font("Korean", "", size)
        self.set_text_color(100, 116, 139)  # slate-500
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def tag_row(self, tags):
        self.set_font("Korean", "", 9)
        x_start = self.get_x()
        for tag in tags:
            w = self.get_string_width(tag) + 8
            self.set_fill_color(243, 232, 255)  # purple-100
            self.set_text_color(107, 33, 168)  # purple-700
            self.cell(w, 7, tag, fill=True, new_x="RIGHT")
            self.cell(2)
        self.ln(10)


def build_cv():
    pdf = CVPDF()
    pdf.add_page()

    # === 헤더 ===
    pdf.set_fill_color(88, 28, 135)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_font("Korean", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(10)
    pdf.cell(0, 10, "김서준", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Korean", "", 10)
    pdf.set_text_color(216, 180, 254)  # purple-300
    pdf.cell(0, 6, "한양대학교 컴퓨터소프트웨어학부 3학년  |  seojun.kim@hanyang.ac.kr  |  github.com/seojun-kim", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(14)

    # === 자기소개 ===
    pdf.section_title("자기소개")
    pdf.body_text(
        '"사용자에게 실제로 닿는 기술"에 관심이 많은 개발자입니다. '
        "자연어 처리와 웹 개발을 결합하여 사람들이 일상에서 체감할 수 있는 AI 서비스를 만드는 것이 목표입니다. "
        "스타트업 인턴 경험을 통해 빠른 실행력과 팀 협업의 중요성을 배웠고, "
        "알고리즘 대회 활동으로 문제 해결 능력을 꾸준히 키워왔습니다.",
        size=9.5,
    )
    pdf.ln(2)

    # === 기술 스택 ===
    pdf.section_title("기술 스택")
    skills = {
        "Language": ["Python", "JavaScript", "TypeScript", "C++"],
        "Frontend": ["React", "Tailwind CSS", "HTML/CSS"],
        "Backend": ["FastAPI", "Node.js", "Express"],
        "AI/ML": ["PyTorch", "Hugging Face", "LangChain"],
        "Database": ["PostgreSQL", "MongoDB"],
        "DevOps": ["Docker", "GitHub Actions", "Git"],
    }
    for cat, items in skills.items():
        pdf.set_font("Korean", "B", 9.5)
        pdf.set_text_color(88, 28, 135)
        pdf.cell(28, 6, cat)
        pdf.tag_row(items)
    pdf.ln(1)

    # === 프로젝트 경험 ===
    pdf.section_title("프로젝트 경험")

    pdf.sub_heading("KorNLU — 한국어 자연어 처리 감성 분석 서비스")
    pdf.light_text("2025.09 ~ 2025.12  |  팀 프로젝트 (4인)  |  역할: ML 모델링 및 백엔드 API")
    pdf.bullet("Hugging Face KoBERT 모델 Fine-tuning으로 한국어 리뷰 감성 분류기 개발")
    pdf.bullet("FastAPI 기반 REST API 서버 구축 및 React 프론트엔드 대시보드 연동")
    pdf.bullet("네이버 쇼핑 리뷰 약 50,000건 크롤링 및 전처리 파이프라인 구축")
    pdf.bullet("정확도 91.3% 달성, 모델 경량화(Quantization) 적용하여 추론 속도 2.4배 개선")
    pdf.ln(3)

    pdf.sub_heading("CampusHub — 대학생 커뮤니티 웹 플랫폼")
    pdf.light_text("2025.03 ~ 2025.06  |  팀 프로젝트 (3인)  |  역할: 프론트엔드 전체 및 실시간 채팅")
    pdf.bullet("React + Tailwind CSS 기반 SPA 프론트엔드 개발 및 Vercel 배포")
    pdf.bullet("실시간 채팅 기능 (Socket.io), 게시판 CRUD, 알림 시스템 구현")
    pdf.bullet("PostgreSQL + Prisma ORM 데이터 모델링, MAU 약 800명 달성")
    pdf.ln(3)

    pdf.sub_heading("AlgoTracker — 알고리즘 풀이 추적 Chrome 확장 프로그램")
    pdf.light_text("2024.12 ~ 2025.02  |  개인 프로젝트")
    pdf.bullet("백준/프로그래머스 문제 풀이 기록을 자동 수집하여 GitHub에 커밋")
    pdf.bullet("Chrome 웹 스토어 배포, 사용자 약 350명")
    pdf.ln(3)

    # === 인턴 경험 ===
    pdf.section_title("인턴 경험")
    pdf.sub_heading("플렉스팀 (Flex) — 프론트엔드 개발 인턴")
    pdf.light_text("2025.07 ~ 2025.08 (2개월)")
    pdf.bullet("HR SaaS 제품의 React 기반 어드민 대시보드 UI 컴포넌트 개발")
    pdf.bullet("Storybook 활용 디자인 시스템 컴포넌트 문서화")
    pdf.bullet("Jira + Slack 기반 애자일 스프린트 참여 (2주 단위), PR 약 25건 머지")
    pdf.ln(3)

    # === 수상 및 활동 ===
    pdf.section_title("수상 및 활동")
    awards = [
        ("2025.11", "한양대학교 프로그래밍 경진대회 은상 (2위)"),
        ("2025.08", "ICPC 서울 리저널 예선 — 본선 진출"),
        ("2025.05", "네이버 D2 Campus Seminar 발표자 (NLP 주제)"),
        ("2024.09~", "한양대 알고리즘 학회 'HYALGO' 운영진"),
    ]
    for date, desc in awards:
        pdf.set_font("Korean", "B", 9.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(22, 6, date)
        pdf.set_font("Korean", "", 9.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 6, desc, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # === 자격증 ===
    pdf.section_title("자격증")
    certs = [
        ("2025.06", "정보처리기사", "한국산업인력공단"),
        ("2024.11", "SQLD", "한국데이터산업진흥원"),
        ("2024.08", "TOEIC 885점", "ETS"),
    ]
    for date, name, org in certs:
        pdf.set_font("Korean", "B", 9.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(22, 6, date)
        pdf.set_font("Korean", "B", 9.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(50, 6, name)
        pdf.set_font("Korean", "", 9)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 6, org, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    out_path = os.path.join(os.path.dirname(__file__), "demo_cv.pdf")
    pdf.output(out_path)
    print(f"PDF 생성 완료: {out_path}")


if __name__ == "__main__":
    build_cv()
