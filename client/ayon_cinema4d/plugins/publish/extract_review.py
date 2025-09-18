import os
import c4d

import ayon_core
from ayon_core.pipeline import publish
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

        exporters.render_playblast(path, **kwargs)
        
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
            list: A list of formatted filenames (e.g., ["shot_010_render_1001.exr", ...]).
        """
        frame_list = []
        for frame in range(start_frame, end_frame + 1):
            padded_frame = f"{frame:04d}"
            frame_filename = f"{base_filename}{padded_frame}.{file_format}"
            frame_list.append(frame_filename)
        return frame_list
