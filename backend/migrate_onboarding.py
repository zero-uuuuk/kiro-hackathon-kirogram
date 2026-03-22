"""Migration: replace interest_category/interests with enrollment_status, info_focus, bio."""

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

STEPS = [
    ("Drop interest_category type (cascades interests column)",
     "DROP TYPE IF EXISTS interest_category CASCADE;"),
    ("Create enrollment_status type",
     "DO $$ BEGIN CREATE TYPE enrollment_status AS ENUM ('enrolled', 'leave_of_absence', 'graduated'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;"),
    ("Add enrollment_status column",
     "ALTER TABLE users ADD COLUMN IF NOT EXISTS enrollment_status enrollment_status NOT NULL DEFAULT 'enrolled';"),
    ("Add info_focus column",
     "ALTER TABLE users ADD COLUMN IF NOT EXISTS info_focus TEXT[] NOT NULL DEFAULT '{}';"),
    ("Add bio column",
     "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;"),
]


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        for desc, sql in STEPS:
            await conn.execute(sql)
            print(f"✓ {desc}")
        print("\nMigration complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
