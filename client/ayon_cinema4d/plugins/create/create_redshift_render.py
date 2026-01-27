from ayon_core.lib import EnumDef, BoolDef
from ayon_cinema4d.api import (
    lib,
    plugin
)


class CreateRedshiftRender(plugin.Cinema4DCreator):
    """Redshift Render"""

    identifier = "io.ayon.creators.cinema4d.redshiftrender"
    label = "Redshift Render"
    product_type = "redshiftRender"
    icon = "video-camera"

    # Standard render formats
    image_format_enum = [
            "exr", "jpg", "png",
            "tga", "tif",
        ]

    def create(self, product_name, instance_data, pre_create_data):
        # Override create to handle product type switching based on farm selection
        # Note: We rely on the base class create but modify data if needed

        # Check if "Render on Farm" is selected
        # pre_create_data contains values from the pre-creation dialog if one exists
        # But we are adding attributes to instance_attr_defs which appear in the publisher UI
        # after creation.
        # So we can't change product_type here based on those attributes easily because
        # they are instance attributes, not pre-create.

        # However, if we want the instance to BE a "render" instance for Deadline,
        # it must have product_type "render".
        # If we change it later, the Creator identifying it might fail?
        # Actually, the Creator is bound by identifier.

        # Strategy: Keep product_type as "redshiftRender".
        # In Publish plugins:
        # If "renderOnFarm" is True -> Convert to "render" (for Deadline).
        # If "renderOnFarm" is False -> Keep "redshiftRender" (for Local).

        # But where to convert?
        # If we convert in a Collector, Deadline (Extractor) will see "render".
        # If we convert, my Local Extractor must ignore "render" (or check flag).

        return super().create(product_name, instance_data, pre_create_data)

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
            BoolDef(
                "renderOnFarm",
                label="Render on Farm",
                default=False
            )
        ])

        return defs
