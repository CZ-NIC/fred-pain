"""Specific settings for fred-pain."""
import appsettings
from django.apps import AppConfig


class FredPainSettings(appsettings.AppSettings):
    """FredPain settings."""

    corba_netloc = appsettings.StringSetting(default='localhost')
    corba_context = appsettings.StringSetting(default='fred')

    class Meta:
        """Meta class."""

        setting_prefix = 'fred_pain_'


class FredPainConfig(AppConfig):
    """Configuration of fred_pain app."""

    name = 'fred_pain'
    verbose_name = 'FRED interface for PAIN'

    def ready(self):
        """Check whether configuration is OK."""
        FredPainSettings.check()


SETTINGS = FredPainSettings()
