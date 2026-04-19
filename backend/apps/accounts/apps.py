"""AppConfig for the accounts app."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Application configuration for ``apps.accounts``.

    Registers signals in ``ready()`` so they are connected exactly once
    when Django starts up.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self) -> None:
        """Import signals to register them with the Django signal dispatcher."""
        import apps.accounts.signals  # noqa: F401, PLC0415
