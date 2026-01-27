import os
import c4d

import ayon_core
from ayon_core.pipeline import publish
from ayon_cinema4d.api import lib, exporters


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
        filename = lib.sanitize_filename(instance.name)
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

        # Collect the files
        files = os.listdir(dir_path)
        sequences = lib.collect_sequences(files)

        for seq_name, seq_files in sequences.items():
            if not seq_files:
                continue

            # Sort files
            if isinstance(seq_files, list):
                seq_files.sort()

            # Identify extension
            ext = os.path.splitext(seq_files[0])[1].lstrip(".").lower()

            # Check for Alpha sequence
            is_alpha = os.path.basename(seq_files[0]).lower().startswith("a_")

            # Main representation (sequence or movie)
            representation = {
                "name": "alpha" if is_alpha else ext,
                "ext": ext,
                "files": seq_files if len(seq_files) > 1 else seq_files[0],
                "stagingDir": dir_path,
            }

            if is_alpha:
                representation["outputName"] = "alpha"

            # If it is a video file, tag it as review
            if ext in ["mp4", "mov"] and not is_alpha:
                representation["tags"] = ["review", "ftrackreview"]

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

            # If it is an image sequence, we want to generate a review MP4
            # Skip alpha sequences for review generation
            if ext not in ["mp4", "mov"] and len(seq_files) > 1 and not is_alpha:
                # Generate review
                review_filename = f"{filename}.mp4"
                review_path = os.path.join(dir_path, review_filename)

                # FPS
                fps = instance.data.get("fps", doc.GetFps())

                try:
                    lib.generate_review(seq_files, review_path, fps=fps)

                    review_repre = {
                        "name": "mp4",
                        "ext": "mp4",
                        "files": review_filename,
                        "stagingDir": dir_path,
                        "tags": ["review", "ftrackreview"]
                    }
                    instance.data["representations"].append(review_repre)
                    self.log.info(f"Generated review mp4: {review_path}")
                except Exception as e:
                    self.log.error(f"Failed to generate review mp4: {e}")

        self.log.info(f"Extracted instance '{instance.name}'")
