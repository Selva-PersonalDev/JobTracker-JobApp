import os
from google.cloud import storage

PROJECT_ID = (
    os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("GCP_PROJECT")
    or os.getenv("PROJECT_ID")
)

BUCKET_NAME = (
    f"jobtracker-data-{PROJECT_ID}"
    if PROJECT_ID
    else None
)

client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

DB_OBJECT = "db/jobs.db"
JD_PREFIX = "jd_files/"
LOCAL_DB_PATH = "/tmp/jobs.db"


def download_db_from_gcs():
    blob = bucket.blob(DB_OBJECT)
    if blob.exists():
        blob.download_to_filename(LOCAL_DB_PATH)


def upload_db_to_gcs():
    blob = bucket.blob(DB_OBJECT)
    blob.upload_from_filename(LOCAL_DB_PATH)


def upload_jd_to_gcs(local_path, filename):
    blob = bucket.blob(f"{JD_PREFIX}{filename}")
    blob.upload_from_filename(local_path)


def download_jd_from_gcs(filename, local_path):
    blob = bucket.blob(f"{JD_PREFIX}{filename}")
    blob.download_to_filename(local_path)
