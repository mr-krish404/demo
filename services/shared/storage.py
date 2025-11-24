"""
Evidence storage management using MinIO/S3
"""
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import io
from datetime import timedelta

from .config import settings

class StorageManager:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the evidence bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_file(self, object_name: str, file_data: BinaryIO, length: int, content_type: str = "application/octet-stream") -> bool:
        """Upload a file to storage"""
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                length,
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    def upload_bytes(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload bytes to storage"""
        file_data = io.BytesIO(data)
        return self.upload_file(object_name, file_data, len(data), content_type)
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """Download a file from storage"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return None
    
    def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> Optional[str]:
        """Get a presigned URL for temporary access"""
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """Delete a file from storage"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """List files with a given prefix"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []
