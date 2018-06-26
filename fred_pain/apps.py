"""Application config for fred-pain."""
from django.apps import AppConfig

from .settings import FredPainSettings


class FredPainConfig(AppConfig):
    """Configuration of fred_pain app."""

    name = 'fred_pain'
    verbose_name = 'FRED interface for PAIN'

    def ready(self):
        """Check whether configuration is OK."""
        FredPainSettings.check()
