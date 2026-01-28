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
        # SKIP PROCESSING IF FARM RENDERING IS REQUESTED
        # The 'PrepareRedshiftFarm' plugin (Collector) should have changed the family to 'render'
        # so this extractor (targeting 'redshiftRender') shouldn't even run.
        # But if it does run (e.g. dynamic family updates issue), check the flag explicitly.
        if instance.data.get("renderOnFarm"):
            self.log.debug("Instance is marked for farm rendering. Skipping local extraction.")
            return

        doc = instance.context.data["doc"]

        self.log.info(f"Processing {instance.name}")

        # Get settings
        # Handle handles? Usually render includes handles.
        frame_start = instance.data["frameStartHandle"]
        frame_end = instance.data["frameEndHandle"]
        fps = instance.data["fps"]
        width = int(instance.data.get("renderWidth") or instance.data.get("resolutionWidth", 1920))
        height = int(instance.data.get("renderHeight") or instance.data.get("resolutionHeight", 1080))
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
        c4d.EventAdd() # Ensure context updates

        # Initialize Bitmap for capturing render result
        bmp = c4d.bitmaps.BaseBitmap()
        bmp.Init(width, height)

        # Thumbnail Setup
        thumb_filename = "thumbnail.jpg"
        thumb_path = os.path.join(staging_dir, thumb_filename)

        try:
            # Modify the RenderData Object Directly

            # Set Renderer to Redshift
            rd[c4d.RDATA_RENDERENGINE] = REDSHIFT_RENDERER_ID

            # Apply Redshift Settings from Instance
            self._apply_redshift_settings(rd, instance.data)

            # Set Resolution
            rd[c4d.RDATA_XRES] = float(width)
            rd[c4d.RDATA_YRES] = float(height)

            # Set Format
            c4d_format = self.get_c4d_format(image_format)
            rd[c4d.RDATA_FORMAT] = c4d_format

            # Set Output Path
            # We use a folder per render to easily collect AOVs
            # C4D/Redshift appends frame numbers, so we provide the prefix.
            output_path_prefix = os.path.join(staging_dir, filename_base)
            rd[c4d.RDATA_PATH] = output_path_prefix
            rd[c4d.RDATA_SAVEIMAGE] = True
            rd[c4d.RDATA_GLOBALSAVE] = True

            # Force frame sequence manual
            rd[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL

            # Set frame range
            start_time = c4d.BaseTime(frame_start, fps)
            end_time = c4d.BaseTime(frame_end, fps)
            rd[c4d.RDATA_FRAMEFROM] = start_time
            rd[c4d.RDATA_FRAMETO] = end_time

            # Update the object
            rd.Message(c4d.MSG_UPDATE)

            self.log.debug("Rendering")

            # Render using RenderDocument
            # We pass the Container of the Active Render Data (which is `rd`)
            # RenderDocument(doc, settings, bmp, flags)
            # Since we set `rd` as active, passing its container should trigger correct VideoPost execution

            # IMPORTANT: Removing RENDERFLAGS_NODOCUMENTCLONE allows C4D to handle the scene translation
            # which might be critical for Redshift to pick up the active render data settings correctly.
            res = c4d.documents.RenderDocument(
                doc,
                rd.GetData(),
                bmp,
                c4d.RENDERFLAGS_EXTERNAL
            )

            if res != c4d.RENDERRESULT_OK:
                raise RuntimeError(f"Render failed with error {res}")



        finally:
            # Restore previous active render data
            if prev_active_rd:
                doc.SetActiveRenderData(prev_active_rd)
                c4d.EventAdd()

            # Clean up the temporary render data
            if rd:
                rd.Remove()

        # Remove the logic that changes family to 'render' here, as it triggers Deadline.
        # This is now handled by PreIntegrateRedshift (Integrator) which runs AFTER Deadline check.

        # Collect generated files
        files = os.listdir(staging_dir)
        self.log.debug(f"Generated files: {files}")

        if thumb_filename in files:
            files.remove(thumb_filename)

        sequences = lib.collect_sequences(files)

        # Verify if any render files (other than review) were generated
        if not sequences:
             self.log.error("No render output files found. Redshift may have failed to save images, or the output path is incorrect.")

        # Identify main sequence for thumbnail
        main_seq_files = None
        for seq_name, seq_files in sequences.items():
             prefix = seq_name.split("#")[0]
             is_alpha = os.path.basename(seq_files[0]).lower().startswith("a_")
             if prefix == filename_base and not is_alpha and len(seq_files) > 0:
                  main_seq_files = seq_files
                  break

        # Generate thumbnail from main sequence if it doesn't exist
        if main_seq_files and not os.path.exists(thumb_path):
            try:
                middle_index = len(main_seq_files) // 2
                source_file = main_seq_files[middle_index]
                source_path = os.path.join(staging_dir, source_file)
                lib.generate_thumbnail(source_path, thumb_path)
            except Exception as e:
                self.log.warning(f"Failed to generate thumbnail: {e}")

        # Add thumbnail representation if it exists
        if os.path.exists(thumb_path):
            repre = {
                "name": "thumbnail",
                "ext": "jpg",
                "files": thumb_filename,
                "stagingDir": staging_dir,
                "tags": ["thumbnail"]
            }
            instance.data.setdefault("representations", []).append(repre)

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

            repre = {
                "name": "alpha" if is_alpha else ext,
                "ext": ext,
                "files": seq_files if len(seq_files) > 1 else seq_files[0],
                "stagingDir": staging_dir,
            }

            if is_alpha:
                repre["outputName"] = "alpha"

            instance.data.setdefault("representations", []).append(repre)

            # Generate review from sequence
            # Only generate review for main pass (prefix matches filename_base)
            prefix = seq_name.split("#")[0]
            if (
                ext not in ["mp4", "mov"]
                and len(seq_files) > 1
                and not is_alpha
                and prefix == filename_base
            ):
                review_filename = f"{filename_base}_review.mp4"
                review_path = os.path.join(staging_dir, review_filename)
                try:
                    lib.generate_review(seq_files, review_path, fps=fps)

                    review_repre = {
                        "name": "mp4",
                        "ext": "mp4",
                        "files": review_filename,
                        "stagingDir": staging_dir,
                        "preview": True,
                        "tags": ["review", "ftrackreview"]
                    }
                    instance.data["representations"].append(review_repre)
                    self.log.info(f"Generated review mp4: {review_path}")
                except Exception as e:
                    self.log.error(f"Failed to generate review mp4: {e}")

    def get_c4d_format(self, ext):
        formats = {
            "exr": 1016606, # OpenEXR
            "jpg": c4d.FILTER_JPG,
            "png": c4d.FILTER_PNG,
            "tif": c4d.FILTER_TIF,
            "tga": c4d.FILTER_TGA,
        }
        return formats.get(ext, 1016606)

    def _apply_redshift_settings(self, rd, data):
        """Apply Redshift settings from instance data to the RenderData VideoPost."""
        # Find Redshift VideoPost
        vp = rd.GetFirstVideoPost()
        redshift_vp = None
        while vp:
            if vp.CheckType(REDSHIFT_RENDERER_ID):
                redshift_vp = vp
                break
            vp = vp.GetNext()

        if not redshift_vp:
            # If not found (unlikely if we just set the engine), try to create/add it?
            # Setting RDATA_RENDERENGINE usually ensures it's active/created, but finding it might require
            # the scene to update. We called EventAdd() and inserted rd, but maybe we need to fetch it again?
            # Actually, `rd` is a clone we inserted. It should have the VP if the original did,
            # or if setting the engine added it.
            # If the original scene wasn't Redshift, setting RDATA_RENDERENGINE might not immediately spawn the VP in Python?
            # Let's log if missing.
            self.log.warning("Redshift VideoPost not found in RenderData. Cannot apply specific settings.")
            return

        self.log.info("Applying Redshift settings...")

        # Mapping: Instance Key -> C4D Constant Name (Attribute on c4d module)
        # Note: We use string names for the constants because we rely on c4d module having them.
        # If they are missing, we log a warning.

        # User provided constants:
        # Redshift[c4d.REDSHIFT_RENDERER_DENOISE_ENABLED]
        # Redshift[c4d.REDSHIFT_RENDERER_MOTION_BLUR_ENABLED]
        # Redshift[c4d.REDSHIFT_RENDERER_REFLECTIONS_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_SUBSURFACE_SCATTERING_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_REFRACTIONS_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_EMISSION_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_TESSELLATION_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_DISPLACEMENT_ENABLE]
        # Redshift[c4d.REDSHIFT_RENDERER_AOV_MULTIPART]
        # Redshift[c4d.REDSHIFT_RENDERER_AOV_GLOBAL_MODE]

        mapping = {
            "redshift_denoise_enabled": "REDSHIFT_RENDERER_DENOISE_ENABLED",
            "redshift_glob_motion_blur": "REDSHIFT_RENDERER_MOTION_BLUR_ENABLED",
            "redshift_glob_reflections": "REDSHIFT_RENDERER_REFLECTIONS_ENABLE",
            "redshift_glob_sss": "REDSHIFT_RENDERER_SUBSURFACE_SCATTERING_ENABLE",
            "redshift_glob_refractions": "REDSHIFT_RENDERER_REFRACTIONS_ENABLE",
            "redshift_glob_emission": "REDSHIFT_RENDERER_EMISSION_ENABLE",
            "redshift_glob_tessellation": "REDSHIFT_RENDERER_TESSELLATION_ENABLE",
            "redshift_glob_displacement": "REDSHIFT_RENDERER_DISPLACEMENT_ENABLE",
            "redshift_multipart_exr": "REDSHIFT_RENDERER_AOV_MULTIPART",
            "redshift_aovs_export": "REDSHIFT_RENDERER_AOV_GLOBAL_MODE",
            "redshift_glob_illumination": "REDSHIFT_RENDERER_GI_ENABLED",
            "redshift_gi_bounces": "REDSHIFT_RENDERER_COMBINED_GI_BOUNCES",
            "redshift_threshold": "REDSHIFT_RENDERER_UNIFIED_ADAPTIVE_ERROR_THRESHOLD",
        }

        # For GI and Sampling, since we don't have definitive IDs from the user,
        # we will attempt to set them ONLY if we can find the constant.
        # If not, we skip them to avoid errors.

        # Special handling for AOV export if needed?
        # "multipart exr doesnt check in the AOV render settings" -> Handled by redshift_multipart_exr mapping.

        for key, const_name in mapping.items():
            if key in data:
                val = data[key]
                if hasattr(c4d, const_name):
                    param_id = getattr(c4d, const_name)
                    try:
                        redshift_vp[param_id] = val
                        self.log.debug(f"Set {const_name} to {val}")
                    except Exception as e:
                         self.log.warning(f"Failed to set {const_name}: {e}")
                else:
                    self.log.debug(f"Constant c4d.{const_name} not found. Skipping {key}.")
