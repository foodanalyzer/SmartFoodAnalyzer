from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# ── Load .env manually (no dependency on load_dotenv finding the file) ────────
env_path = Path(__file__).resolve().parent.parent / ".env"

if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"\n\nDATABASE_URL is missing!\n"
        f"Looked for .env at: {env_path}\n"
        f"Make sure the file exists and contains:\n"
        f"DATABASE_URL=postgresql://...\n"
    )

# ── Supabase / PostgreSQL connection fix ──────────────────────────────────────
# 1. SQLAlchemy needs 'postgresql://' not 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Add SSL (required by Supabase)
if "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{separator}sslmode=require"

# ── Create engine ─────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # test connection before using it
    pool_recycle=300,          # recycle connections every 5 min (prevents timeout)
    connect_args={
        "connect_timeout": 10,  # fail fast if can't connect
        "sslmode": "require"
    }
)

# ── Test the connection immediately so you know if it works ───────────────────
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("\n✅ Database connected successfully!\n")
except Exception as e:
    print(f"\n❌ Database connection FAILED: {e}\n")
    print("Check your DATABASE_URL in .env\n")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()