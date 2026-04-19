"""Automations models (stub — Phase 2)."""

from django.db import models

from common.models import TenantScopedModel


class Workflow(TenantScopedModel):
    """Stub workflow model. Full implementation in Phase 2."""

    name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        app_label = "automations"

    def __str__(self) -> str:
        return self.name
