import os
import c4d

import ayon_core
from ayon_core.pipeline import publish
from ayon_core.pipeline.farm.pyblish_functions import get_product_name_and_group_from_template
from ayon_cinema4d.api import exporters


class Cinema4DExtractReview(publish.Extractor):

    label = "Render Review"
    hosts = ["cinema4d"]
    families = ["review"]

    def process(self, instance):

        doc: c4d.BaseDocument = instance.context.data["doc"]

        # Collect the start and end including handles
        start = instance.data["frameStartHandle"]
        end = instance.data["frameEndHandle"]

        # TODO: Allow using members for isolate view
        # nodes = instance[:]
        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}".format(instance.name)
        path = os.path.join(dir_path, filename)

        # Export selection to camera
        # Prefer instance-defined resolution when available (from creator)
        width = instance.data.get("reviewWidth")
        height = instance.data.get("reviewHeight")
        fileformat = instance.data.get("imageFormat")
        alpha = instance.data.get("useAlpha", False)
        hw_rendersettings = {
            "AA" : instance.data.get("AA", 2),
            "SuperSampling" : instance.data.get("SuperSampling", 2),
            "useEffects" : instance.data.get("useEffects", True),
            "useHQNoise" : instance.data.get("useHQNoise", False),
            "useTransparency" : instance.data.get("useTransparency", True),
            "useShadows" : instance.data.get("useShadows", False),
            "useReflections" : instance.data.get("useReflections", True),
            "useSSAO" : instance.data.get("useSSAO", False),
            "useDOF" : instance.data.get("useDOF", False),
            "useGeoOnly" : instance.data.get("useGeoOnly", True),
            "filterGrid" : instance.data.get("filterGrid", False),
            "filterNull" : instance.data.get("filterNull", False),
            "filterSpline" : instance.data.get("filterSpline", False),
            "filterDeformer" : instance.data.get("filterDeformer", False),
            "filterField" : instance.data.get("filterField", False),
            "filterJoint" : instance.data.get("filterJoint", False),
            "filterCamera" : instance.data.get("filterCamera", False),
            "filterLight" : instance.data.get("filterLight", False),
            "filterOther" : instance.data.get("filterOther", False),
            "filterAnimPath" : instance.data.get("filterAnimPath", False),
        }

        kwargs = {
            "frame_start": start,
            "frame_end": end,
            "doc": doc,
        }
        if width is not None and height is not None:
            kwargs.update({
                "width": int(width),
                "height": int(height),
            })
        if fileformat is not None:
            kwargs.update({"file_format": fileformat})
        if hw_rendersettings is not None:
            kwargs.update({"hw_rendersettings": hw_rendersettings})

        exporters.render_playblast(filepath=path, **kwargs)
        
        # Create the full filename with the extension
        if fileformat == "mp4" or fileformat == "mov":
            full_filename = f"{filename}.{fileformat}"
        else:
            full_filename = self.generate_frame_list(filename, start, end, fileformat)
        
        representation = {
            "name": fileformat,
            "ext": fileformat,
            "files": full_filename,
            "stagingDir": dir_path,
        }
        representation["tags"] = ["review", "preview", "ftrackreview"]
        instance.data.setdefault("representations", []).append(representation)

        self.log.info(f"Extracted instance '{instance.name}' to: {path}.{fileformat}")

    def generate_frame_list(self, base_filename, start_frame, end_frame, file_format):
        """
        Generates a list of filenames for a sequence of frames.

        Args:
            base_filename (str): The base name of the file (e.g., "shot_010_render_").
            frame_start (int): The starting frame number.
            frame_end (int): The ending frame number (inclusive).
            file_format (str): The file extension without a dot (e.g., "exr").

        Returns:
            frame_list: A list of formatted filenames.
        """
        frame_list = []
        for frame in range(start_frame, end_frame + 1):
            padded_frame = f"{frame:04d}"
            frame_filename = f"{base_filename}{padded_frame}.{file_format}"
            frame_list.append(frame_filename)
            
        return frame_list
