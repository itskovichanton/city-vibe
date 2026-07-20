"""Клиент notification-service."""

from python.libs.clients.domain.notification_service.client import (
    NotificationServiceClient,
    NotificationServiceClientImpl,
)

__all__ = ["NotificationServiceClient", "NotificationServiceClientImpl"]
