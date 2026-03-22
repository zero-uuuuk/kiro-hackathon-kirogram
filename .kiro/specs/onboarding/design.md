# Onboarding Backend Design

## Schema Changes

### Drop
```sql
DROP TYPE IF EXISTS interest_category CASCADE;  -- drops interests column too
```

### New ENUMs
```sql
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'leave_of_absence', 'graduated');
```

### Altered users table
```sql
ALTER TABLE users
  ADD COLUMN enrollment_status enrollment_status NOT NULL DEFAULT 'enrolled',
  ADD COLUMN info_focus TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN bio TEXT;
-- interests column removed via DROP TYPE CASCADE
```

### Final users table
```sql
CREATE TABLE IF NOT EXISTS users (
    id                    SERIAL PRIMARY KEY,
    email                 TEXT UNIQUE NOT NULL,
    name                  TEXT,
    school                TEXT NOT NULL,
    major                 TEXT NOT NULL,
    enrollment_status     enrollment_status NOT NULL,
    grade                 grade_level NOT NULL,
    info_focus            TEXT[] NOT NULL DEFAULT '{}',
    bio                   TEXT,
    google_calendar_token JSONB,
    created_at            TIMESTAMP DEFAULT NOW()
);
```

## info_focus valid values (enforced at API layer, not DB)
`spec_building` | `campus_info` | `job` | `hackathon` | `competition` | `scholarship`

## API Layer (`backend/api/`)

### Models (`backend/api/models.py`)
```python
class EnrollmentStatus(str, Enum):
    enrolled = "enrolled"
    leave_of_absence = "leave_of_absence"
    graduated = "graduated"

class GradeLevel(str, Enum):
    one = "1"; two = "2"; three = "3"; four = "4"
    graduate = "graduate"; other = "other"

class UserCreate(BaseModel):
    email: str
    name: str | None = None
    school: str
    major: str
    enrollment_status: EnrollmentStatus
    grade: GradeLevel
    info_focus: list[str] = []
    bio: str | None = None

class UserUpdate(BaseModel):  # all optional
    name: str | None = None
    school: str | None = None
    major: str | None = None
    enrollment_status: EnrollmentStatus | None = None
    grade: GradeLevel | None = None
    info_focus: list[str] | None = None
    bio: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    school: str
    major: str
    enrollment_status: str
    grade: str
    info_focus: list[str]
    bio: str | None
    created_at: datetime
```

## RecommenderAgent Prompt Update
Replace `interests` field reference with `info_focus` + `bio` in the Bedrock prompt:
```
정보 중심: {info_focus}
자기소개: {bio}
```

## Key Design Decisions
- D1: `info_focus` is TEXT[] not a new ENUM — allows flexible values without schema migration per new category.
- D2: Migration script handles existing DB (DROP TYPE CASCADE + ALTER TABLE).
- D3: `UserUpdate` uses all-optional fields for PATCH semantics.
- D4: `custom_sources` table unchanged — already supports URL + natural language description.
