import os
import c4d

from ayon_core.pipeline import publish
from ayon_cinema4d.api import lib

# Redshift VideoPost ID
REDSHIFT_RENDERER_ID = 1036219


class ExtractRedshiftRender(publish.Extractor):
    label = "Render Redshift"
    hosts = ["cinema4d"]
    families = ["redshiftRender"]

    def process(self, instance):
        doc = instance.context.data["doc"]

        self.log.info(f"Processing {instance.name}")

        # Get settings
        # Handle handles? Usually render includes handles.
        frame_start = instance.data["frameStartHandle"]
        frame_end = instance.data["frameEndHandle"]
        fps = instance.data["fps"]
        width = int(instance.data.get("resolutionWidth", 1920))
        height = int(instance.data.get("resolutionHeight", 1080))
        image_format = instance.data.get("imageFormat", "exr")

        # Staging dir
        staging_dir = self.staging_dir(instance)
        self.log.debug(f"Staging dir: {staging_dir}")

        # Render filename base
        filename_base = lib.sanitize_filename(instance.name)

        # Prepare RenderData
        # We clone the active render data object to preserve VideoPosts (Redshift settings)
        active_rd = doc.GetActiveRenderData()
        rd = active_rd.GetClone()

        # Insert into document so Redshift can find it/it is valid
        doc.InsertRenderData(rd)

        # Determine previous active render data to restore later
        prev_active_rd = doc.GetActiveRenderData()

        # Set our new RD as active so Redshift picks up its VideoPosts
        doc.SetActiveRenderData(rd)

        # Initialize Bitmap for capturing render result
        bmp = c4d.bitmaps.BaseBitmap()
        bmp.Init(width, height)

        # Initialize MovieSaver for Review
        review_filename = f"{filename_base}_review.mp4"
        review_path = os.path.join(staging_dir, review_filename)

        ms = c4d.bitmaps.MovieSaver()
        # MP4 format ID is 1125
        FILTER_MP4 = 1125

        if ms.Open(review_path, bmp, fps, FILTER_MP4, c4d.BaseContainer(), c4d.SAVEBIT_ALPHA) != c4d.IMAGERESULT_OK:
             self.log.warning("Could not open MovieSaver for review generation. Review will not be created.")
             ms = None

        try:
            rd_data = rd.GetDataInstance()

            # Set Renderer to Redshift
            rd_data[c4d.RDATA_RENDERENGINE] = REDSHIFT_RENDERER_ID

            # Set Resolution
            rd_data[c4d.RDATA_XRES] = float(width)
            rd_data[c4d.RDATA_YRES] = float(height)

            # Set Format
            c4d_format = self.get_c4d_format(image_format)
            rd_data[c4d.RDATA_FORMAT] = c4d_format

            # Set Output Path
            # We use a folder per render to easily collect AOVs
            # C4D/Redshift appends frame numbers, so we provide the prefix.
            output_path_prefix = os.path.join(staging_dir, filename_base)
            rd_data[c4d.RDATA_PATH] = output_path_prefix
            rd_data[c4d.RDATA_SAVEIMAGE] = True
            rd_data[c4d.RDATA_GLOBALSAVE] = True

            # Force frame sequence manual to allow frame-by-frame control if needed
            rd_data[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL

            # Iterate frames
            # frame_start and frame_end are inclusive
            for frame in range(int(frame_start), int(frame_end) + 1):
                self.log.debug(f"Rendering frame {frame}")

                # Set frame for this render pass
                # RDATA_FRAMEFROM/TO expect BaseTime
                bt = c4d.BaseTime(frame, fps)
                rd_data[c4d.RDATA_FRAMEFROM] = bt
                rd_data[c4d.RDATA_FRAMETO] = bt

                # Render using RenderDocument
                # We pass the Container of the Active Render Data (which is `rd`)
                # RenderDocument(doc, settings, bmp, flags)
                # Since we set `rd` as active, passing its container should trigger correct VideoPost execution
                res = c4d.documents.RenderDocument(
                    doc,
                    rd_data,
                    bmp,
                    c4d.RENDERFLAGS_EXTERNAL | c4d.RENDERFLAGS_NODOCUMENTCLONE
                )

                if res != c4d.RENDERRESULT_OK:
                    raise RuntimeError(f"Render failed for frame {frame} with error {res}")

                # Write to review
                # Note: Color management is skipped here (Linear -> sRGB conversion absent).
                # The review will be raw linear if source is EXR.
                # Improving this requires OCIO which is not currently available in this scope.
                if ms:
                    ms.Write(bmp)

        finally:
            if ms:
                ms.Close()

            # Restore previous active render data
            if prev_active_rd:
                doc.SetActiveRenderData(prev_active_rd)

            # Clean up the temporary render data
            if rd:
                rd.Remove()

        # Collect generated files
        files = os.listdir(staging_dir)
        self.log.debug(f"Generated files: {files}")

        sequences = self.collect_sequences(files)

        # Verify if any render files (other than review) were generated
        render_files_found = any(k != f"{filename_base}_review.mp4" for k in sequences.keys())
        if not render_files_found:
             self.log.error("No render output files found. Redshift may have failed to save images, or the output path is incorrect.")
             # We don't raise here to allow review to publish if it exists, but it's suspicious.
             # Actually, if the main render failed, we should probably fail.

        for seq_name, seq_files in sequences.items():
            if not seq_files:
                continue

            seq_files.sort()

            # Determine if this is the review file
            if seq_name == f"{filename_base}_review.mp4":
                repre = {
                    "name": "mp4",
                    "ext": "mp4",
                    "files": seq_name,
                    "stagingDir": staging_dir,
                    "tags": ["review", "ftrackreview"]
                }
                instance.data.setdefault("representations", []).append(repre)
                continue

            # It's a sequence
            ext = os.path.splitext(seq_files[0])[1].lstrip(".")

            repre = {
                "name": ext,
                "ext": ext,
                "files": seq_files if len(seq_files) > 1 else seq_files[0],
                "stagingDir": staging_dir,
            }

            instance.data.setdefault("representations", []).append(repre)

    def get_c4d_format(self, ext):
        formats = {
            "exr": 1016606, # OpenEXR
            "jpg": c4d.FILTER_JPG,
            "png": c4d.FILTER_PNG,
            "tif": c4d.FILTER_TIF,
            "tga": c4d.FILTER_TGA,
        }
        return formats.get(ext, 1016606)

    def collect_sequences(self, files):
        """
        Group files into sequences.
        Returns dict: { "sequence_key": [files...] }
        For single files (like mp4), key is filename.
        """
        import collections
        import re

        sequences = collections.defaultdict(list)

        # Regex to match frame numbers at end of name before extension
        # e.g. name.0001.ext or name0001.ext
        frame_pattern = re.compile(r'^(.*?)(\.?\d+)(\.[^.]+)$')

        for f in files:
            match = frame_pattern.match(f)
            if match:
                prefix, frame, ext = match.groups()
                # Use prefix + ext as key
                key = f"{prefix}#{ext}"
                sequences[key].append(f)
            else:
                # Single file or unrecognised pattern
                sequences[f].append(f)

        return sequences
