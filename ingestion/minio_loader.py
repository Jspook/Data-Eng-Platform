"""
MinIO Data Lake Loader (Bronze Layer Ingestion)
================================================
Handles uploading raw source datasets into the S3-compatible MinIO Data Lake.

Responsibilities:
- Establish connection to MinIO using environment configuration
- Verify / auto-create target bucket
- Idempotently upload raw CSV / Parquet files to the bronze landing zone
"""

import os
import glob
from typing import List, Optional
from dotenv import load_dotenv

# Load local environment configuration
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minio_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minio_password_dev_123")
DEFAULT_BUCKET = os.getenv("MINIO_BUCKET_NAME", "ecommerce-lake")


class MinIODataLakeLoader:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: bool = False
    ):
        # Allow overriding via parameters or environment
        self.endpoint = endpoint or MINIO_ENDPOINT
        self.access_key = access_key or MINIO_ACCESS_KEY
        self.secret_key = secret_key or MINIO_SECRET_KEY
        self.secure = secure
        self._client = None

    @property
    def client(self):
        """Lazy initialization of MinIO client."""
        if self._client is None:
            try:
                from minio import Minio
                # Clean endpoint string if protocol prefix is mistakenly included
                clean_endpoint = self.endpoint.replace("http://", "").replace("https://", "")
                self._client = Minio(
                    clean_endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
            except ImportError:
                raise ImportError("minio package not installed. Run `pip install minio`.")
        return self._client

    def ensure_bucket(self, bucket_name: str = DEFAULT_BUCKET) -> bool:
        """Verify that the target bucket exists, creating it if not."""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            print(f"[MinIO] Bucket '{bucket_name}' created successfully.")
            return True
        return False

    def upload_file(self, local_path: str, bucket_name: str = DEFAULT_BUCKET, object_name: Optional[str] = None) -> str:
        """
        Uploads a single local file to MinIO object storage.
        Overwrites idempotently if already exists.
        """
        self.ensure_bucket(bucket_name)
        if not object_name:
            object_name = f"bronze/{os.path.basename(local_path)}"

        file_size_kb = os.path.getsize(local_path) / 1024.0
        self.client.fput_object(bucket_name, object_name, local_path)
        print(f"[MinIO] Uploaded: {local_path} ({file_size_kb:.2f} KB) -> s3://{bucket_name}/{object_name}")
        return f"s3://{bucket_name}/{object_name}"

    def upload_bronze_directory(self, local_dir: str = "data/bronze", bucket_name: str = DEFAULT_BUCKET) -> List[str]:
        """
        Uploads all raw CSV files in local directory to bronze layer in MinIO.
        """
        csv_files = glob.glob(os.path.join(local_dir, "*.csv"))
        if not csv_files:
            print(f"[MinIO] Warning: No CSV files found in {local_dir}")
            return []

        uploaded_uris = []
        for file_path in csv_files:
            file_name = os.path.basename(file_path)
            object_key = f"bronze/{file_name}"
            uri = self.upload_file(file_path, bucket_name=bucket_name, object_name=object_key)
            uploaded_uris.append(uri)

        print(f"[MinIO] Successfully ingested {len(uploaded_uris)} tables to Bronze Lake.")
        return uploaded_uris


if __name__ == "__main__":
    loader = MinIODataLakeLoader()
    loader.upload_bronze_directory()
