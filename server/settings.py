from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import (
    Cinema4DImageIOModel,
    DEFAULT_IMAGEIO_SETTINGS
)
from .create import (
    CreatePluginsModel,
    DEFAULT_CINEMA4D_CREATE_SETTINGS
)


class InstallPySideToCinema4DModel(BaseSettingsModel):
    enabled: bool = SettingsField(False, title="Enabled")


class HooksModel(BaseSettingsModel):
    InstallPySideToCinema4D: InstallPySideToCinema4DModel = SettingsField(
        default_factory=InstallPySideToCinema4DModel,
        title="Install PySide to Cinema 4D"
    )


class Cinema4DSettings(BaseSettingsModel):
    imageio: Cinema4DImageIOModel = SettingsField(
        default_factory=Cinema4DImageIOModel,
        title="Color Management (ImageIO)",
    )
    create: CreatePluginsModel = SettingsField(
        default_factory=CreatePluginsModel,
        title="Create Plugins"
    )
    hooks: HooksModel = SettingsField(
        default_factory=HooksModel,
        title="Hooks"
    )


DEFAULT_HOOKS_SETTINGS = {
    "InstallPySideToCinema4D": {
        "enabled": False
    }
}

DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "create": DEFAULT_CINEMA4D_CREATE_SETTINGS,
    "hooks": DEFAULT_HOOKS_SETTINGS
}
