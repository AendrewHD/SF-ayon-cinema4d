import os
import c4d

import ayon_core
from ayon_core.pipeline import publish
from ayon_cinema4d.api import exporters, lib


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
        filename = lib.sanitize_filename("{0}".format(instance.name))
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
            kwargs.update({"fileformat": fileformat})

        exporters.render_playblast(path, **kwargs)
        
        # Create the full filename with the extension
        full_filename = f"{filename}.{fileformat}"

        representation = {
            "name": fileformat,
            "ext": fileformat,
            "files": full_filename,
            "stagingDir": dir_path,
        }
        representation["tags"] = ["review", "preview", "ftrackreview"]
        instance.data.setdefault("representations", []).append(representation)

        self.log.info(f"Extracted instance '{instance.name}' to: {path}.{fileformat}")
