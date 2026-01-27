from ayon_server.settings import BaseSettingsModel, SettingsField

from .imageio import (
    Cinema4DImageIOModel,
    DEFAULT_IMAGEIO_SETTINGS
)
from .create import (
    CreatePluginsModel,
    DEFAULT_CINEMA4D_CREATE_SETTINGS
)
from .publish import (
    PublishPluginsModel,
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
    publish: PublishPluginsModel = SettingsField(
        default_factory=PublishPluginsModel,
        title="Publish Plugins"
    )


DEFAULT_PUBLISH_SETTINGS = {
    "Cinema4DExtractReview": {
        "burnin": {
            "enabled": False,
            "font_size": 42,
            "font_color": "white",
            "font_path": "",
            "top_left": "{asset}",
            "top_center": "{task}",
            "top_right": "{version}",
            "bottom_left": "{date}",
            "bottom_center": "{time}",
            "bottom_right": "Frame: {frame}"
        }
    },
    "ExtractRedshiftRender": {
        "burnin": {
            "enabled": False,
            "font_size": 42,
            "font_color": "white",
            "font_path": "",
            "top_left": "{asset}",
            "top_center": "{task}",
            "top_right": "{version}",
            "bottom_left": "{date}",
            "bottom_center": "{time}",
            "bottom_right": "Frame: {frame}"
        }
    }
}


DEFAULT_VALUES = {
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "create": DEFAULT_CINEMA4D_CREATE_SETTINGS,
    "publish": DEFAULT_PUBLISH_SETTINGS,
}