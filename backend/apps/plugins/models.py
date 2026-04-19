"""
Plugin models — PluginConfig with Fernet-encrypted configuration.
"""

from __future__ import annotations

import json

from django.conf import settings
from django.db import models

from common.models import TenantScopedModel


class PluginConfig(TenantScopedModel):
    """
    Per-tenant plugin configuration with Fernet-encrypted credentials.

    The ``config`` property transparently encrypts/decrypts using the
    ``PLUGIN_ENCRYPTION_KEY`` setting.  The raw JSON is never stored in plaintext.

    Attributes:
        plugin_id: Identifies which plugin this config belongs to (e.g. ``"slack"``).
        is_enabled: Toggle without deleting the config.
        _config_encrypted: Fernet-encrypted JSON blob (internal field).
    """

    plugin_id = models.CharField(max_length=100, db_index=True)
    is_enabled = models.BooleanField(default=True)
    _config_encrypted = models.BinaryField()

    class Meta:
        app_label = "plugins"
        unique_together = [("plugin_id",)]  # one config per plugin per tenant

    def __str__(self) -> str:
        return f"{self.plugin_id} ({'enabled' if self.is_enabled else 'disabled'})"

    @property
    def config(self) -> dict:
        """
        Decrypt and return the plugin configuration as a dict.

        Returns:
            Decrypted configuration dictionary.

        Raises:
            ValueError: If ``PLUGIN_ENCRYPTION_KEY`` is not configured.
        """
        from cryptography.fernet import Fernet  # noqa: PLC0415

        if not settings.PLUGIN_ENCRYPTION_KEY:
            raise ValueError("PLUGIN_ENCRYPTION_KEY is not configured.")
        f = Fernet(settings.PLUGIN_ENCRYPTION_KEY)
        return json.loads(f.decrypt(bytes(self._config_encrypted)))

    @config.setter
    def config(self, value: dict) -> None:
        """
        Encrypt and store the plugin configuration.

        Args:
            value: Plain-text configuration dictionary to encrypt.

        Raises:
            ValueError: If ``PLUGIN_ENCRYPTION_KEY`` is not configured.
        """
        from cryptography.fernet import Fernet  # noqa: PLC0415

        if not settings.PLUGIN_ENCRYPTION_KEY:
            raise ValueError("PLUGIN_ENCRYPTION_KEY is not configured.")
        f = Fernet(settings.PLUGIN_ENCRYPTION_KEY)
        self._config_encrypted = f.encrypt(json.dumps(value).encode())
