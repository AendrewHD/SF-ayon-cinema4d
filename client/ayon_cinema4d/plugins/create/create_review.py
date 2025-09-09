from ayon_core.lib import NumberDef, EnumDef
from ayon_cinema4d.api import (
    lib,
    plugin,
    exporters,
)


class CreateReview(plugin.Cinema4DCreator):
    """Viewport render reviewable"""

    identifier = "io.ayon.creators.cinema4d.review"
    label = "Review"
    description = __doc__
    product_type = "review"
    icon = "video-camera"
    render_type = "viewport"
    
    image_format_enum = [
            "exr", "jpg", "png",
            "tga", "tif", "mp4",
        ]

    def get_instance_attr_defs(self):
        """Define instance attributes for review creation.

        - Frame range is based on current task entity (AYON standard),
          including handles via `collect_animation_defs`.
        - FPS, width and height default to the current product (task) settings
          so the resulting viewport render matches project standards.
        """

        # Collect basic animation attributes including handles and fps
        defs = lib.collect_animation_defs(self.create_context, fps=True)

        # Add resolution controls defaulting to AYON task attributes
        task_entity = self.create_context.get_current_task_entity()
        attrib = task_entity["attrib"]
        defs.extend([
            EnumDef(
                "imageFormat",
                label="Image Format",
                items=self.image_format_enum,
                default="jpg",
            ),
            NumberDef(
                "reviewWidth",
                label="Width",
                default=int(attrib.get("resolutionWidth", 1920)),
                decimals=0,
            ),
            NumberDef(
                "reviewHeight",
                label="Height",
                default=int(attrib.get("resolutionHeight", 1080)),
                decimals=0,
            ),
            
        ])

        return defs

    # --- Convenience API -------------------------------------------------
    def get_render_settings_from_context(self):
        """Return render settings from the current AYON context.

        Returns a dict with frame_start, frame_end, fps, width, height derived
        from the current task entity (AYON standards).
        """
        task_entity = self.create_context.get_current_task_entity()
        attrib = task_entity["attrib"]

        handle_start = int(attrib.get("handleStart", 0))
        handle_end = int(attrib.get("handleEnd", 0))

        frame_start = int(attrib.get("frameStart", 0)) - handle_start
        frame_end = int(attrib.get("frameEnd", 0)) + handle_end
        fps = int(round(float(attrib.get("fps", 24))))
        width = int(attrib.get("resolutionWidth", 1920))
        height = int(attrib.get("resolutionHeight", 1080))

        return {
            "frame_start": frame_start,
            "frame_end": frame_end,
            "fps": fps,
            "width": width,
            "height": height,
        }

    def render_viewport(self, filepath, instance=None):
        """Render a viewport review movie using AYON product settings.

        This provides a programmatic API for the creator to generate a
        playblast matching the product's frame range and resolution. If an
        instance is provided and contains explicit overrides for fps/size they
        will be preferred.

        Args:
            filepath (str): Output mp4 path.
            instance (Optional[CreatedInstance]): Optional instance to source
                overrides from.
        """
        settings = self.get_render_settings_from_context()

        # Allow instance attribute overrides when provided
        if instance is not None:
            data = getattr(instance, "data", {}) or {}
            # Animation overrides
            fs = data.get("frameStart")
            fe = data.get("frameEnd")
            hs = data.get("handleStart", 0)
            he = data.get("handleEnd", 0)
            if fs is not None and fe is not None:
                settings["frame_start"] = int(fs) - int(hs)
                settings["frame_end"] = int(fe) + int(he)
            # FPS override
            if "fps" in data:
                settings["fps"] = int(round(float(data["fps"])))
            # Resolution overrides (optional)
            if "reviewWidth" in data:
                settings["width"] = int(data["reviewWidth"]) 
            if "reviewHeight" in data:
                settings["height"] = int(data["reviewHeight"]) 

        exporters.render_playblast(
            filepath,
            frame_start=settings["frame_start"],
            frame_end=settings["frame_end"],
            fps=settings["fps"],
            width=settings["width"],
            height=settings["height"],
        )
