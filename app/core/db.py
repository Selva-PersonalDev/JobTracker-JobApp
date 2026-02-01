from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.storage import download_db_from_gcs

DB_PATH = "/tmp/jobs.db"

download_db_from_gcs()

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
