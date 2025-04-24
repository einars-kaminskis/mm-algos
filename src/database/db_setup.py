from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL  # You can load this from your .env using python-dotenv

# Create an engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for debugging

# Create a configured "Session" class
SessionLocal = sessionmaker(bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()