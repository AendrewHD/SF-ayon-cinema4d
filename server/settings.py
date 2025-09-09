from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import (
    Cinema4DImageIOModel,
    DEFAULT_IMAGEIO_SETTINGS
)
from .create import (
    CreatePluginsModel,
    DEFAULT_CINEMA4D_CREATE_SETTINGS
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

DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "create": DEFAULT_CINEMA4D_CREATE_SETTINGS
}