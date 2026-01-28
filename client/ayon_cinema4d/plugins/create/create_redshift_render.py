from ayon_core.lib import (
    EnumDef,
    BoolDef,
    NumberDef,
    UILabelDef,
    UISeparatorDef
)
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

        # Get Task Attributes for defaults
        task_entity = self.create_context.get_current_task_entity()
        attrib = task_entity["attrib"] if task_entity else {}

        # Add additional attributes
        defs.extend([
            UISeparatorDef(),
            UILabelDef(label="Image Size"),
            NumberDef(
                "renderWidth",
                label="Width",
                default=int(attrib.get("resolutionWidth", 1920)),
                decimals=0
            ),
            NumberDef(
                "renderHeight",
                label="Height",
                default=int(attrib.get("resolutionHeight", 1080)),
                decimals=0
            ),

            UISeparatorDef(),
            UILabelDef(label="Redshift Options"),

            EnumDef(
                "redshift_renderer",
                label="Renderer",
                items=["Bucket", "Progressive"],
                default="Bucket"
            ),

            UILabelDef(label="Sampling"),
            NumberDef(
                "redshift_threshold",
                label="Threshold",
                default=0.01,
                decimals=4
            ),
            
            UILabelDef(label="Global Illumination"),
            BoolDef(
                "redshift_glob_illumination",
                label="Global Illumination",
                default=True
            ),
            NumberDef(
                "redshift_gi_bounces",
                label="GI Bounces",
                default=3,
                decimals=0
            ),

            UILabelDef(label="Output"),
            BoolDef(
                "redshift_multipart_exr",
                label="Multipart EXR",
                default=True
            ),
            BoolDef(
                "redshift_aovs_export",
                label="Export AOVs",
                default=True
            ),

            UILabelDef(label="Global Overrides"),
            BoolDef("redshift_glob_reflections", label="Reflections", default=True),
            BoolDef("redshift_glob_refractions", label="Refractions", default=True),
            BoolDef("redshift_glob_sss", label="Subsurface Scattering", default=True),
            BoolDef("redshift_glob_emission", label="Emission", default=True),
            BoolDef("redshift_glob_tessellation", label="Tessellation", default=True),
            BoolDef("redshift_glob_displacement", label="Displacement", default=True),

            UILabelDef(label="Motion Blur"),
            BoolDef("redshift_glob_motion_blur", label="Motion Blur", default=False),

            UILabelDef(label="Denoise"),
            BoolDef(
                "redshift_denoise_enabled",
                label="Denoise Enabled",
                default=False
            ),

            UISeparatorDef(),
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
