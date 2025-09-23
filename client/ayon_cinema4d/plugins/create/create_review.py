from ayon_core.lib import (
    EnumDef,    
    NumberDef,
    UILabelDef,
    UISeparatorDef,
    BoolDef,
)
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
        # Add resolution controls defaulting to AYON task attributes
        # UI labels and grouping for clarity
        task_entity = self.create_context.get_current_task_entity()
        attrib = task_entity["attrib"]
        defs = [
            UILabelDef(
                label="Review Settings"
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
            # Blank line
            UILabelDef(
                label="",
            ),  
            NumberDef(
                "frameStart",
                label="Frame Start",
                default=int(attrib.get("frameStart", 1001)),
            ),
            NumberDef(
                "handleStart",
                label="Handle Start",
                default=int(attrib.get("handleStart", 0)),
            ),
            NumberDef(
                "frameEnd",
                label="Frame End",
                default=int(attrib.get("frameEnd", 1100)),
            ),
            NumberDef(
                "handleEnd",
                label="Handle End",
                default=int(attrib.get("handleEnd", 0)),
            ),
            # Blank line
            UILabelDef(
                label=" ",
            ), 
            NumberDef(
                "fps",
                label="FPS",
                default=int(round(float(attrib.get("fps", 24)))),
            ),
            # Blank line
            UILabelDef(
                label="   ",
            ),  
            EnumDef(
                "imageFormat",
                label="Image Format",
                items=self.image_format_enum,
                default="jpg",
            ),
            BoolDef(
                "useAlpha",
                label="Use Alpha",
                default=False,
                tooltip="not availabe for jpg or mp4 fileformats"
            ),
            UISeparatorDef(),
            UILabelDef(
                label="Viewport Render Settings"
            ),
            EnumDef(
                "AA",
                label="Anti-Aliasing",
                items=[
                    (0, "Off"),
                    (1, "FXAA"),
                    (2, "MSAA 2x"),
                    (3, "MSAA 4x"),
                    (4, "MSAA 8x"),
                ],
                default=2,
            ),
            EnumDef(
                "SuperSampling",
                label="Super Sampling",
                items=[
                    (0, "Off"),
                    (1, "2x2"),
                    (2, "3x3"),
                    (3, "4x4"),
                    (4, "5x5"),
                    (5, "8x8"),
                    (6, "16x16"),
                ],
                default=1,
            ),
            # Blank line
            UILabelDef(
                label="    ",
            ),
            UILabelDef(
                label="Effects",
            ),
            BoolDef(
                "useEffects",
                label="Use Effects",
                default=True,
            ),
            BoolDef(
                "useHQNoise",
                label="Use High Quality Noise",
                default=False,
            ),
            BoolDef(
                "useTransparency",
                label="Use Transparency",
                default=True,
            ),
            BoolDef(
                "useShadows",
                label="Use Shadows",
                default=False,
            ),
            BoolDef(
                "useReflections",
                label="Use Reflections",
                default=True,
            ),
            BoolDef(
                "useSSAO",
                label="Use SSAO",
                default=False,
            ),
            BoolDef(
                "useDOF",
                label="Use Depth of Field",
                default=False,
            ),
            # Blank line
            UILabelDef(
                label="     ",
            ),
            UILabelDef(
                label="Filter",
            ),
            BoolDef(
                "useGeoOnly",
                label="Geometry Only",
                default=True,
                is_label_horizontal=False,
                tooltip="disables all filters below",
            ),
            BoolDef(
                "filterGrid",
                label="view World Grid",
                default=False,
            ),
            BoolDef(
                "filterNull",
                label="view Nulls",
                default=False,
            ),
            BoolDef(
                "filterSpline",
                label="view Splines",
                default=False,
            ),
            BoolDef(
                "filterDeformer",
                label="view Deformers",
                default=False,
            ),
            BoolDef(
                "filterField",
                label="view Fields",
                default=False,
            ),
            BoolDef(
                "filterJoint",
                label="view Joints",
                default=False,
            ),
            BoolDef(
                "filterCamera",
                label="view Cameras",
                default=False,
            ),
            BoolDef(
                "filterLight",
                label="view Lights",
                default=False,
            ),
            BoolDef(
                "filterOther",
                label="view Others",
                default=False,
            ),
            BoolDef(
                "filterAnimPath",
                label="view Animation Paths",
                default=False,
            ),
        ]
        
        return defs

    # --- Convenience API -------------------------------------------------
    def get_render_settings_from_context(self):
        """Return render settings from the current AYON context.

        Returns a dict with frame_start, frame_end, fps, width, height derived
        from the current task entity (AYON standards).
        """
        # Review Settings
        task_entity = self.create_context.get_current_task_entity()
        attrib = task_entity["attrib"]

        handle_start = int(attrib.get("handleStart", 0))
        handle_end = int(attrib.get("handleEnd", 0))

        frame_start = int(attrib.get("frameStart", 0)) - handle_start
        frame_end = int(attrib.get("frameEnd", 0)) + handle_end
        fps = int(round(float(attrib.get("fps", 24))))
        width = int(attrib.get("resolutionWidth", 1920))
        height = int(attrib.get("resolutionHeight", 1080))
        image_format = attrib.get("imageFormat", "jpg")
        alpha = attrib.get("useAlpha", False)
        
        # Effects Settings
        hw_rendersettings = {
            "AA" : attrib.get("AA", 2),
            "SuperSampling" : attrib.get("SuperSampling", 2),
            "useEffects" : attrib.get("useEffects", True),
            "useHQNoise" : attrib.get("useHQNoise", False),
            "useTransparency" : attrib.get("useTransparency", True),
            "useShadows" : attrib.get("useShadows", False),
            "useReflections" : attrib.get("useReflections", True),
            "useSSAO" : attrib.get("useSSAO", False),
            "useDOF" : attrib.get("useDOF", False),
            "useGeoOnly" : attrib.get("useGeoOnly", True),
            "filterGrid" : attrib.get("filterGrid", False),
            "filterNull" : attrib.get("filterNull", False),
            "filterSpline" : attrib.get("filterSpline", False),
            "filterDeformer" : attrib.get("filterDeformer", False),
            "filterField" : attrib.get("filterField", False),
            "filterJoint" : attrib.get("filterJoint", False),
            "filterCamera" : attrib.get("filterCamera", False),
            "filterLight" : attrib.get("filterLight", False),
            "filterOther" : attrib.get("filterOther", False),
            "filterAnimPath" : attrib.get("filterAnimPath", False),
        }

        return {
            "frame_start": frame_start,
            "frame_end": frame_end,
            "fps": fps,
            "width": width,
            "height": height,
            "imageFormat": image_format,
            "hw_rendersettings": hw_rendersettings,
            "useAlpha": alpha,
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
            if "imageFormat" in data:
                if data["imageFormat"] in self.image_format_enum:
                    settings["imageFormat"] = data["imageFormat"]

        exporters.render_playblast(
            filepath,
            frame_start=settings["frame_start"],
            frame_end=settings["frame_end"],
            fps=settings["fps"],
            width=settings["width"],
            height=settings["height"],
            file_format=settings["imageFormat"],
            hw_rendersettings=settings["hw_rendersettings"],
        )
