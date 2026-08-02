"""Асинхронное хранилище файлов в S3-совместимом API (MinIO / AWS)."""

from __future__ import annotations

import logging
from typing import Protocol
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from src.mybootstrap_ioc_itskovichanton.ioc import bean

logger = logging.getLogger(__name__)


class FileNotFoundInStorageError(FileNotFoundError):
    """Объект не найден в bucket."""


class FileStorage(Protocol):
    """Контракт файлового хранилища (аватарки и т.п.)."""

    async def upload(
        self,
        data: bytes,
        *,
        content_type: str,
        key_prefix: str = "avatars",
        extension: str = "jpg",
    ) -> str:
        """Загружает файл и возвращает S3-ключ (не публичный URL)."""
        ...

    async def download(self, key: str) -> tuple[bytes, str]:
        """Читает объект по ключу: (body, content_type)."""
        ...

    async def delete(self, key_or_url: str) -> None:
        """Удаляет объект по ключу или legacy URL."""
        ...


@bean(
    endpoint_url=("s3.endpoint_url", str, "http://localhost:9000"),
    access_key=("s3.access_key", str, "minioadmin"),
    secret_key=("s3.secret_key", str, "minioadmin"),
    bucket=("s3.bucket", str, "city-vibe"),
    region=("s3.region", str, "us-east-1"),
)
class S3FileStorage(FileStorage):
    """
    Реализация FileStorage через boto3 (S3 API).

    Для локальной разработки используем MinIO из infra/docker-compose.yml.
    Вызовы boto3 синхронные — оборачиваем через asyncio.to_thread.
    """

    _client: BaseClient | None = None

    def init(self, **kwargs):
        self.endpoint_url = kwargs.get("endpoint_url", getattr(self, "endpoint_url", None))
        self.access_key = kwargs.get("access_key", getattr(self, "access_key", None))
        self.secret_key = kwargs.get("secret_key", getattr(self, "secret_key", None))
        self.bucket = kwargs.get("bucket", getattr(self, "bucket", "city-vibe"))
        self.region = kwargs.get("region", getattr(self, "region", "us-east-1"))

        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Создаёт bucket, если его ещё нет (удобно для локального MinIO)."""
        assert self._client is not None
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                logger.info("Создаём S3 bucket '%s'", self.bucket)
                self._client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                # Не валим старт сервиса — bucket создадим при первой загрузке
                logger.warning("Не удалось подготовить S3 bucket '%s': %s", self.bucket, e)

    @staticmethod
    def normalize_key(key_or_url: str, *, bucket: str) -> str:
        """S3-ключ из ключа или legacy URL (`http://host:9000/bucket/avatars/...`)."""
        raw = (key_or_url or "").strip()
        if not raw:
            return raw
        if raw.startswith("http://") or raw.startswith("https://"):
            from urllib.parse import urlparse

            path = urlparse(raw).path.lstrip("/")
            bucket_prefix = f"{bucket.strip('/')}/"
            if path.startswith(bucket_prefix):
                return path[len(bucket_prefix) :]
            return path
        return raw.lstrip("/")

    async def upload(
        self,
        data: bytes,
        *,
        content_type: str,
        key_prefix: str = "avatars",
        extension: str = "jpg",
    ) -> str:
        import asyncio

        key = f"{key_prefix.strip('/')}/{uuid4().hex}.{extension.lstrip('.')}"

        def _put() -> None:
            assert self._client is not None
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        await asyncio.to_thread(_put)
        logger.debug("Файл загружен в S3: %s", key)
        return key

    async def download(self, key: str) -> tuple[bytes, str]:
        import asyncio

        normalized = self.normalize_key(key, bucket=self.bucket)

        def _get() -> tuple[bytes, str]:
            assert self._client is not None
            try:
                resp = self._client.get_object(Bucket=self.bucket, Key=normalized)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code in {"NoSuchKey", "404", "NotFound"}:
                    raise FileNotFoundInStorageError(normalized) from e
                raise
            body = resp["Body"].read()
            content_type = resp.get("ContentType") or "application/octet-stream"
            return body, content_type

        return await asyncio.to_thread(_get)

    async def delete(self, key_or_url: str) -> None:
        import asyncio

        key = self.normalize_key(key_or_url, bucket=self.bucket)

        def _delete() -> None:
            assert self._client is not None
            self._client.delete_object(Bucket=self.bucket, Key=key)

        await asyncio.to_thread(_delete)
