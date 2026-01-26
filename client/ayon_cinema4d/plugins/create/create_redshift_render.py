from ayon_core.lib import EnumDef
from ayon_cinema4d.api import (
    lib,
    plugin
)


class CreateRedshiftRender(plugin.Cinema4DCreator):
    """Redshift Render"""

    identifier = "io.ayon.creators.cinema4d.redshiftrender"
    label = "Redshift Render"
    product_type = "render"
    icon = "video-camera"

    # Standard render formats
    image_format_enum = [
            "exr", "jpg", "png",
            "tga", "tif",
        ]

    def get_instance_attr_defs(self):
        """Define instance attributes for render creation."""

        # Collect basic animation attributes including handles and fps
        defs = lib.collect_animation_defs(self.create_context, fps=True)

        # Add additional attributes
        defs.extend([
            EnumDef(
                "imageFormat",
                label="Image Format",
                tooltip="Format of the rendered images.",
                items=self.image_format_enum,
                default="exr",
            ),
        ])

        return defs
