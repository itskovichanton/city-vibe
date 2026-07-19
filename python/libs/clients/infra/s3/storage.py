"""Асинхронное хранилище файлов в S3-совместимом API (MinIO / AWS)."""

from __future__ import annotations

import logging
from typing import Protocol
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from src.mybootstrap_ioc_itskovichanton.ioc import bean

logger = logging.getLogger(__name__)


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
        """Загружает файл и возвращает публичный URL."""
        ...

    async def delete(self, key_or_url: str) -> None:
        """Удаляет объект по ключу или полному URL."""
        ...


@bean(
    endpoint_url=("s3.endpoint_url", str, "http://localhost:9000"),
    access_key=("s3.access_key", str, "minioadmin"),
    secret_key=("s3.secret_key", str, "minioadmin"),
    bucket=("s3.bucket", str, "city-vibe"),
    region=("s3.region", str, "us-east-1"),
    public_base_url=("s3.public_base_url", str, "http://localhost:9000/city-vibe"),
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
        self.public_base_url = kwargs.get(
            "public_base_url",
            getattr(self, "public_base_url", ""),
        ).rstrip("/")

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
        url = f"{self.public_base_url}/{key}"
        logger.debug("Файл загружен в S3: %s", url)
        return url

    async def delete(self, key_or_url: str) -> None:
        import asyncio

        key = key_or_url
        if key_or_url.startswith("http"):
            # Вытаскиваем ключ из URL: .../bucket/avatars/xxx.jpg → avatars/xxx.jpg
            prefix = f"{self.public_base_url}/"
            key = key_or_url[len(prefix):] if key_or_url.startswith(prefix) else key_or_url.rsplit("/", 2)[-1]

        def _delete() -> None:
            assert self._client is not None
            self._client.delete_object(Bucket=self.bucket, Key=key)

        await asyncio.to_thread(_delete)
