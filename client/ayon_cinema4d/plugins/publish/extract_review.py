import os
import c4d

import ayon_core
from ayon_core.pipeline import publish
from ayon_cinema4d.api import lib, exporters


class Cinema4DExtractReview(publish.Extractor):

    label = "Extract Review"
    hosts = ["cinema4d"]
    families = ["review"]

    def process(self, instance):
        # We only want to run this extractor for the "review" instance
        # which is the one that generates the playblast.
        # Other instances (like Redshift) might have the "review" family
        # added to trigger the global ExtractReview plugin, but we don't
        # want to generate a playblast for them.
        if instance.data.get("family") != "review":
            self.log.debug("Skipping Playblast extraction for non-review family instance.")
            return

        doc: c4d.BaseDocument = instance.context.data["doc"]

        # Collect the start and end including handles
        start = instance.data["frameStartHandle"]
        end = instance.data["frameEndHandle"]
        fps = instance.data["fps"]
        

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
            "hw_rendersettings": hw_rendersettings,
        }
        if width is not None and height is not None:
            kwargs.update({
                "width": int(width),
                "height": int(height),
            })
        if fileformat is not None:
            kwargs.update({"file_format": fileformat})

        exporters.render_playblast(path, **kwargs)

        # Collect the files
        files = os.listdir(dir_path)
        sequences = lib.collect_sequences(files)

        for seq_name, seq_files in sequences.items():
            if not seq_files:
                continue;

            # Sort files
            if isinstance(seq_files, list):
                seq_files.sort()

            # Identify extension
            ext = os.path.splitext(seq_files[0])[1].lstrip(".").lower()

            # Check for Alpha sequence
            is_alpha = os.path.basename(seq_files[0]).lower().startswith("a_")

            # Main representation (sequence or movie)
            representation = {
                "name": ext,
                "ext": ext,
                "files": seq_files if len(seq_files) > 1 else seq_files[0],
                "stagingDir": dir_path,
                "frameStart": start,
                "frameEnd": end,
                "fps": fps,
                "tags": ["review"]
            }

            if is_alpha:
                representation["outputName"] = "alpha"
            
            if representation["ext"] == "mp4":
                representation["tags"].append("review")

            instance.data.setdefault("representations", []).append(representation)

            # Generate thumbnail if not alpha and sequence
            if not is_alpha and len(seq_files) > 0:
                thumb_filename = "thumbnail.jpg"
                thumb_path = os.path.join(dir_path, thumb_filename)

                # Check if thumbnail already exists (e.g. from previous loop)
                if not os.path.exists(thumb_path):
                    # Pick middle frame
                    middle_index = len(seq_files) // 2
                    source_file = seq_files[middle_index]
                    source_path = os.path.join(dir_path, source_file)

                    try:
                        lib.generate_thumbnail(source_path, thumb_path)

                        thumb_repre = {
                            "name": "thumbnail",
                            "ext": "jpg",
                            "files": thumb_filename,
                            "stagingDir": dir_path,
                            "tags": ["thumbnail"]
                        }
                        instance.data.setdefault("representations", []).append(thumb_repre)
                    except Exception as e:
                        self.log.warning(f"Failed to generate thumbnail: {e}")


        self.log.info(f"Extracted instance '{instance.name}'")
