import os
import c4d

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

        # Export selection to camera
        # Prefer instance-defined resolution when available (from creator)
        width = instance.data.get("reviewWidth")
        height = instance.data.get("reviewHeight")
        fileformat = instance.data.get("imageFormat")
        alpha = instance.data.get("useAlpha", False)

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}".format(instance.name)
        if fileformat in ["mp4", "mov"]:
            path = os.path.join(dir_path, f"{filename}.{fileformat}")
        else:
            path = os.path.join(dir_path, filename)
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

        separate_alpha = False
        if alpha and fileformat == "jpg":
            separate_alpha = True

        kwargs = {
            "frame_start": start,
            "frame_end": end,
            "doc": doc,
            "useAlpha": alpha,
            "separate_alpha": separate_alpha,
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

        # Render thumbnail
        self._render_thumbnail(instance, dir_path, start, end, width, height, hw_rendersettings)

        # Create the full filename with the extension
        if fileformat == "mp4" or fileformat == "mov":
            full_filename = f"{filename}.{fileformat}"
        else:
            full_filename = self.generate_frame_list(filename, start, end, fileformat)

        # Check if the file(s) exist
        if isinstance(full_filename, list):
            check_file = full_filename[0]
        else:
            check_file = full_filename

        full_path = os.path.join(dir_path, check_file)
        if not os.path.exists(full_path):
            raise Exception(f"Review extraction failed. Expected file not found: {full_path}")

        alpha_exists = False
        full_alpha_filename = None
        if alpha:
            alpha_filename = f"a_{filename}"
            if fileformat == "mp4" or fileformat == "mov":
                full_alpha_filename = f"{alpha_filename}.{fileformat}"
            else:
                full_alpha_filename = self.generate_frame_list(
                    alpha_filename, start, end, fileformat
                )

            first_alpha_file = None
            if isinstance(full_alpha_filename, list):
                if full_alpha_filename:
                    first_alpha_file = full_alpha_filename[0]
            else:
                first_alpha_file = full_alpha_filename

            if first_alpha_file and os.path.exists(os.path.join(dir_path, first_alpha_file)):
                alpha_exists = True

        tags = ["review"]
        # Add ftrack tag if ftrack is active (simple check, or just add it as it's harmless)
        # But to be safe and match Blender, let's keep it if standard practice
        tags.append("ftrackreview")

        representation = {
            "name": fileformat,
            "ext": fileformat,
            "files": full_filename,
            "stagingDir": dir_path,
            "tags": tags,
        }

        # Add frame metadata only for sequences, or if we are sure it matches.
        # For simple MP4 review, sometimes less is more.
        # However, AYON usually benefits from fps.
        if fileformat not in ["mp4", "mov"]:
             representation.update({
                "frameStart": start,
                "frameEnd": end,
                "fps": instance.data.get("fps", 25),
             })

        # 'preview' key is not standard AYON representation data, removing it to be safe.

        instance.data.setdefault("representations", []).append(representation)

        if alpha_exists:
            representation_alpha = {
                "name": "alpha",
                "ext": fileformat,
                "files": full_alpha_filename,
                "stagingDir": dir_path,
                "output": "alpha",
                "outputName": "alpha",
                "data": {"output": "alpha"},
                "tags": tags,
            }
            instance.data["representations"].append(representation_alpha)

        self.log.info(f"Extracted instance '{instance.name}' to: {path}.{fileformat}")

    def _render_thumbnail(self, instance, dir_path, start, end, width, height, hw_rendersettings):
        mid_frame = int((start + end) / 2)
        thumbnail_filename = "thumbnail.jpg"
        thumbnail_path = os.path.join(dir_path, thumbnail_filename)

        self.log.info(f"Rendering thumbnail to {thumbnail_path}")

        kwargs = {
            "frame_start": mid_frame,
            "frame_end": mid_frame,
            "doc": instance.context.data["doc"],
            "useAlpha": False,
            "separate_alpha": False,
            "file_format": "jpg",
            "hw_rendersettings": hw_rendersettings
        }
        if width and height:
            kwargs.update({"width": width, "height": height})

        exporters.render_playblast(filepath=thumbnail_path, **kwargs)

        representation = {
            "name": "thumbnail",
            "ext": "jpg",
            "files": thumbnail_filename,
            "stagingDir": dir_path,
            "tags": ["thumbnail"]
        }
        instance.data.setdefault("representations", []).append(representation)

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
