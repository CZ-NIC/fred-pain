"""Specific settings for fred-pain."""
import appsettings


class FredPainSettings(appsettings.AppSettings):
    """FredPain settings."""

    corba_netloc = appsettings.StringSetting(default='localhost')
    corba_context = appsettings.StringSetting(default='fred')

    class Meta:
        """Meta class."""

        setting_prefix = 'fred_pain_'


SETTINGS = FredPainSettings()
