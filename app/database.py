from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 🔽 Dependencies function for database connection 🔽
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()