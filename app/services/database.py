from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔥 Update with your actual password
DATABASE_URL = "postgresql://postgres:password@localhost:5432/codebase_db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False  # set True if you want SQL logs
)

# Session (DB connection)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# 🔥 Dependency (optional but clean for FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()