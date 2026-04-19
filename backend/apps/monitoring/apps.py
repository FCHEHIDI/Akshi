"""AppConfig for the monitoring app."""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.monitoring"
    label = "monitoring"

    def ready(self) -> None:
        import apps.monitoring.signals  # noqa: F401, PLC0415
