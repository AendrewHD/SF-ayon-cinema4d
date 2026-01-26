import json
import logging
import os
import shutil
import tempfile

import c4d

log = logging.getLogger(__name__)


FBX_EXPORTER_ID = 1026370

PLAYBLAST_SETTINGS = {
    # Resolution
    "RDATA_XRES": 1920.0,
    "RDATA_YRES": 1080.0,
    "RDATA_LOCKRATIO": True,
    "RDATA_ADAPT_DATARATE": True,
    "RDATA_PIXELRESOLUTION_VIRTUAL": 72.0,
    "RDATA_PIXELRESOLUTIONUNIT": 1.0,
    "RDATA_RENDERREGION": False,
    "RDATA_FILMASPECT": 1.0,
    "RDATA_PIXELASPECT": 1.0,
    # Frame rate and range
    # "RDATA_FRAMERATE": 12,
    # "RDATA_FRAMESEQUENCE": c4d.RDATA_FRAMESEQUENCE_ALLFRAMES,
    # "RDATA_FRAMEFROM": 0,
    # "RDATA_FRAMETO": 11,
    "RDATA_FRAMESTEP": 1,
    "RDATA_FIELD": 0,
    "RDATA_GLOBALSAVE": True,
    "RDATA_SAVEIMAGE": True,
    "RDATA_MULTIPASS_ENABLE": False,
    "RDATA_PROJECTFILE": False,
    "RDATA_FORMAT": c4d.FILTER_MOVIE,  # save as Quicktime movie,
}

HARDWARE_SETTINGS = {
    "VP_PREVIEWHARDWARE_ENHANCEDOPENGL": False,
    "VP_PREVIEWHARDWARE_ANTIALIASING": 2,
    "VP_PREVIEWHARDWARE_SUPERSAMPLING": c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_NONE,
}


class RenderError(RuntimeError):
    pass


def get_plugin_imexport_options(plugin, label=None):
    if label is None:
        label = str(plugin)

    plugin_obj = c4d.plugins.FindPlugin(
        plugin,
        c4d.PLUGINTYPE_SCENESAVER,
    )
    if plugin_obj is None:
        raise Exception(f"Could not find plug-in: {label}.")

    options = {}
    # Send MSG_RETRIEVEPRIVATEDATA to Alembic export plugin
    if plugin_obj.Message(c4d.MSG_RETRIEVEPRIVATEDATA, options):
        if "imexporter" not in options:
            raise Exception(
                f"Could not find options container for the {label} exporter."
            )

    # BaseList2D object stored in "imexporter" key hold the settings
    imexporter_options = options["imexporter"]
    if imexporter_options is None:
        raise Exception(f"Could not find options for the {label} exporter.")

    return imexporter_options


def extract_alembic(filepath,
                    frame_start=None,
                    frame_end=None,
                    frame_step=1,
                    sub_frames=1,
                    global_matrix=False,
                    selection=True,
                    doc=None,
                    verbose=False,
                    **kwargs):
    """Extract a single Alembic Cache."""
    doc = doc or c4d.documents.GetActiveDocument()

    # Fallback to Cinema4d timeline if no start or end frame provided.
    if frame_start is None:
        frame_start = doc.GetMinTime().GetFrame(doc.GetFps())
    if frame_end is None:
        frame_end = doc.GetMinTime().GetFrame(doc.GetFps())

    # Set export options
    options = get_plugin_imexport_options(c4d.FORMAT_ABCEXPORT,
                                          label="Alembic")

    applied_options = {
        # Animation
        "ABCEXPORT_FRAME_START": frame_start,
        "ABCEXPORT_FRAME_END": frame_end,
        "ABCEXPORT_FRAME_STEP": frame_step,
        "ABCEXPORT_SUBFRAMES": sub_frames,

        # General
        # "ABCEXPORT_SCALE": 1  # "UnitScaleData
        "ABCEXPORT_SELECTION_ONLY": selection,
        "ABCEXPORT_CAMERAS": kwargs.get("cameras", True),
        "ABCEXPORT_SPLINES": kwargs.get("splines", False),
        "ABCEXPORT_HAIR": kwargs.get("hair", False),
        "ABCEXPORT_XREFS": kwargs.get("xrefs", True),
        "ABCEXPORT_GLOBAL_MATRIX": global_matrix,

        # Subdivision surface
        "ABCEXPORT_HYPERNURBS": kwargs.get(
            "subdivisionSurfaces", True
        ),
        "ABCEXPORT_SDS_WEIGHTS": kwargs.get(
            "subdivisionSurfaceWeights", False
        ),
        "ABCEXPORT_PARTICLES": kwargs.get("particles", False),
        "ABCEXPORT_PARTICLE_GEOMETRY": kwargs.get(
            "particleGeometry", False
        ),

        # Optional data
        "ABCEXPORT_VISIBILITY": kwargs.get("visibility", True),
        "ABCEXPORT_UVS": kwargs.get("uvs", True),
        "ABCEXPORT_VERTEX_MAPS": kwargs.get("vertexMaps", False),

        # Vertex normals
        "ABCEXPORT_NORMALS": kwargs.get("normals", False),
        "ABCEXPORT_POLYGONSELECTIONS": kwargs.get("polygonSelections", True),
        "ABCEXPORT_VERTEX_COLORS": kwargs.get("vertexColors", False),
        "ABCEXPORT_POINTS_ONLY": kwargs.get("pointsOnly", False),
        "ABCEXPORT_DISPLAY_COLORS": kwargs.get("displayColors", False),
        "ABCEXPORT_MERGE_CACHE": kwargs.get("mergeCache", False)

        # "ABCEXPORT_GROUP": None,  # ???
        # # Don't export child objects with only selected?
        # "ABCEXPORT_PARENTS_ONLY_MODE": False,
        # "ABCEXPORT_STR_ANIMATION": None,  # ???
        # "ABCEXPORT_STR_GENERAL": None,  # ???
        # "ABCEXPORT_STR_OPTIONS": None,  # ???
    }
    if verbose:
        log.debug(
            "Preparing Alembic export with options: %s",
            json.dumps(applied_options, indent=4),
        )

    for key, value in applied_options.items():
        key_id = getattr(c4d, key)
        # There appears to be a bug where if the value is just set directly
        # that it fails to apply them for the export, e.g. still exporting the
        # whole scene even though `c4d.ABCEXPORT_SELECTION_ONLY` is True.
        # See: https://developers.maxon.net/forum/topic/12767/alembic-export-options-not-working/6  # noqa: E501
        options[key_id] = not value
        options[key_id] = value

    # Ensure output directory exists
    parent_dir = os.path.dirname(filepath)
    os.makedirs(parent_dir, exist_ok=True)

    if c4d.documents.SaveDocument(
        doc,
        filepath,
        c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST,
        c4d.FORMAT_ABCEXPORT,
    ):
        if verbose:
            log.debug("Extracted Alembic to: %s", filepath)
    else:
        log.error("Extraction of Alembic failed: %s", filepath)

    return filepath


def extract_fbx(filepath, verbose=False, **kwargs):
    """Extract a single fbx file."""

    doc = c4d.documents.GetActiveDocument()
    options = get_plugin_imexport_options(FBX_EXPORTER_ID,
                                                     label="FBX")

    # File format
    options[c4d.FBXEXPORT_FBX_VERSION] = kwargs.get("fbxVersion", 0)
    options[c4d.FBXEXPORT_ASCII] = kwargs.get("fbxAscii", False)

    # General
    options[c4d.FBXEXPORT_SELECTION_ONLY] = kwargs.get("selectionOnly", False)
    options[c4d.FBXEXPORT_CAMERAS] = kwargs.get("cameras", True)
    options[c4d.FBXEXPORT_SPLINES] = kwargs.get("splines", True)
    options[c4d.FBXEXPORT_INSTANCES] = kwargs.get("instances", True)
    options[c4d.FBXEXPORT_GLOBAL_MATRIX] = kwargs.get("globalMatrix", False)
    options[c4d.FBXEXPORT_SDS] = kwargs.get("subdivisionSurfaces", True)
    options[c4d.FBXEXPORT_LIGHTS] = kwargs.get("lights", True)

    # Animation
    options[c4d.FBXEXPORT_TRACKS] = kwargs.get("tracks", False)
    options[c4d.FBXEXPORT_BAKE_ALL_FRAMES] = kwargs.get(
        "bakeAllFrames", False
    )
    options[c4d.FBXEXPORT_PLA_TO_VERTEXCACHE] = kwargs.get(
        "plaToVertexCache", False
    )

    # Geometry
    options[c4d.FBXEXPORT_SAVE_NORMALS] = kwargs.get("normals", False)
    options[c4d.FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS] = kwargs.get(
        "vertexMapsAsColors", False
    )
    options[c4d.FBXEXPORT_SAVE_VERTEX_COLORS] = kwargs.get(
        "vertexColors", False
    )
    options[c4d.FBXEXPORT_TRIANGULATE] = kwargs.get("triangulate", False)
    options[c4d.FBXEXPORT_SDS_SUBDIVISION] = kwargs.get(
        "bakedSubdivisionSurfaces", False
    )
    options[c4d.FBXEXPORT_LOD_SUFFIX] = kwargs.get("lodSuffix", False)

    # Additional
    if hasattr(c4d, "FBXEXPORT_TEXTURES"):
        # Cinema4d S22 doesn't have this option anymore
        options[c4d.FBXEXPORT_TEXTURES] = kwargs.get("textures", False)
    if hasattr(c4d, "FBXEXPORT_BAKE_MATERIALS"):
        # Cinema4d S22 now has the ability to bake materials
        options[c4d.FBXEXPORT_BAKE_MATERIALS] = kwargs.get(
            "bakeMaterials", False
        )
    options[c4d.FBXEXPORT_EMBED_TEXTURES] = kwargs.get(
        "embedTextures", False
    )
    options[c4d.FBXEXPORT_FLIP_Z_AXIS] = kwargs.get("flipZAxis", False)
    options[c4d.FBXEXPORT_SUBSTANCES] = kwargs.get("substances", False)
    options[c4d.FBXEXPORT_UP_AXIS] = kwargs.get(
        "upAxis", c4d.FBXEXPORT_UP_AXIS_Y
    )

    # Ensure output directory exists
    parent_dir = os.path.dirname(filepath)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    if verbose:
        log.debug(
            "Preparing FBX export with options: %s",
            json.dumps(kwargs, indent=4),
        )

    if c4d.documents.SaveDocument(
        doc,
        filepath,
        c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST,
        FBX_EXPORTER_ID,
    ):
        if verbose:
            log.debug("Extracted FBX to: %s", filepath)
    else:
        log.error("Extraction of FBX failed: %s", filepath)

    return filepath


def extract_redshiftproxy(
        filepath,
        frame_start=None,
        frame_end=None,
        frame_step=1,
        selection=True,
        export_lights=True,
        export_compress=True,
        export_polygon_connectivity=False,
        doc=None,
        verbose=False):
    """Extract a Redshift Proxy."""

    # Redshift may not be available so we import here
    import redshift  # noqa

    doc = doc or c4d.documents.GetActiveDocument()

    # Fallback to Cinema4d timeline if no start or end frame provided.
    if frame_start is None:
        frame_start = doc.GetMinTime().GetFrame(doc.GetFps())
    if frame_end is None:
        frame_end = doc.GetMinTime().GetFrame(doc.GetFps())

    # Export at default 1cm scale
    scale = c4d.UnitScaleData()
    scale.SetUnitScale(1.0, c4d.DOCUMENT_UNIT_CM)

    # Set export options
    options = get_plugin_imexport_options(redshift.Frsproxyexport,
                                          label="Alembic")

    applied_options = {
        "REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_END": frame_end,
        "REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_START": frame_start,
        "REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_STEP": frame_step,
        "REDSHIFT_PROXYEXPORT_ANIMATION_RANGE": c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE_MANUAL,
        "REDSHIFT_PROXYEXPORT_EXPORT_COMPRESS": export_compress,
        "REDSHIFT_PROXYEXPORT_EXPORT_LIGHTS": export_lights,
        "REDSHIFT_PROXYEXPORT_EXPORT_POLYGON_CONNECTIVITY": export_polygon_connectivity,
        "REDSHIFT_PROXYEXPORT_OBJECTS": (
            c4d.REDSHIFT_PROXYEXPORT_OBJECTS_SELECTION if selection
            else c4d.REDSHIFT_PROXYEXPORT_OBJECTS_ALL
        ),

        # Proxy Origin:
        #   - World Origin: REDSHIFT_PROXYEXPORT_ORIGIN_WORLD
        #   - Object Bounds: REDSHIFT_PROXYEXPORT_ORIGIN_OBJECTS
        "REDSHIFT_PROXYEXPORT_ORIGIN": c4d.REDSHIFT_PROXYEXPORT_ORIGIN_WORLD,

        # Include default beauty AOV
        # Keep the default beauty config in the proxy. Used primarily when
        # exporting entire scenes for rendering with the redshiftCmdLine tool
        "REDSHIFT_PROXYEXPORT_AOV_DEFAULT_BEAUTY": False,

        "REDSHIFT_PROXYEXPORT_AUTOPROXY_CREATE": False,
        # "REDSHIFT_PROXYEXPORT_AUTOPROXY_PREFIX": "RS Proxy",

        # Do not remove the exported objects
        "REDSHIFT_PROXYEXPORT_REMOVE_OBJECTS": False,

        "REDSHIFT_PROXYEXPORT_SCALE": scale,

        # TODO: Set more parameters
        # "REDSHIFT_PROXYEXPORT_GROUP": ...,
        # "REDSHIFT_PROXYEXPORT_GROUP_ANIMATION": ...,
        # "REDSHIFT_PROXYEXPORT_GROUP_AOV": ...,
        # "REDSHIFT_PROXYEXPORT_GROUP_AUTOPROXY": ...,
        # "REDSHIFT_PROXYEXPORT_GROUP_OPTIONS": ...,
    }
    if verbose:
        log.debug(
            "Preparing Redshift Proxy export with options: %s",
            json.dumps(applied_options, indent=4, default=str),
        )

    for key, value in applied_options.items():
        key_id = getattr(c4d, key)
        # There appears to be a bug where if the value is just set directly
        # that it fails to apply them for the export, e.g. still exporting the
        # whole scene even though `c4d.ABCEXPORT_SELECTION_ONLY` is True.
        # See: https://developers.maxon.net/forum/topic/12767/alembic-export-options-not-working/6  # noqa: E501
        if isinstance(value, (bool, int)):
            options[key_id] = not value
        options[key_id] = value

    # Ensure output directory exists
    parent_dir = os.path.dirname(filepath)
    os.makedirs(parent_dir, exist_ok=True)

    if c4d.documents.SaveDocument(
        doc,
        filepath,
        c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST,
        redshift.Frsproxyexport,
    ):
        if verbose:
            log.debug("Extracted Redshift Proxy to: %s", filepath)
    else:
        log.error("Extraction of Redshift Proxy failed: %s", filepath)

    return filepath


def render_playblast(filepath,
                     frame_start=None,
                     frame_end=None,
                     fps=None,
                     width=1920,
                     height=1080,
                     file_format="jpg",
                     useAlpha=False,
                     separate_alpha=False,
                     doc=None,
                     hw_rendersettings=None):
    """Create a playblast of the given or active document.

    Args:
        filepath(str): The filepath to render the movie to.
        frame_start (Optional[int]): Frame start.
            Defaults to document start time if not provided.
        frame_end (Optional[int]): Frame end.
            Defaults to document end time if not provided.
        fps (int): Frames per seconds.
        width (int): Resolution width for the render.
        height (int): Resolution height for the render.
        file_format (str): Image format for the render.
        doc (Optional[c4d.documents.BaseDocument]): Document to operate in.
            Defaults to active document if not set.
        rendersettings (Optional[dict]): Dictionary of hardware render settings.

    Returns:
        str: The filepath of the rendered movie.
    """
    doc = doc or c4d.documents.GetActiveDocument()
    doc_fps = doc.GetFps()
    if fps is None:
        fps = doc_fps
    if frame_start is None:
        frame_start = doc.GetMinTime().GetFrame(doc_fps)
    if frame_end is None:
        frame_end = doc.GetMaxTime().GetFrame(doc_fps)
        
    #duplicate = False
    name = "Playblast"

    # Get render settings
    renderdata = doc.GetFirstRenderData()

    while renderdata:
        renderdata_next = renderdata.GetNext()
        if renderdata.GetName() == name:
            # Found a match, now set it as the active render setting
            doc.SetActiveRenderData(renderdata)
            renderdata.Remove()
            #duplicate = True
            break
        renderdata = renderdata_next

    renderdata = c4d.documents.RenderData()
    
    rendersettings = renderdata.GetDataInstance()

    rendersettings[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE

    # Set FPS and frame range
    rendersettings[c4d.RDATA_FRAMERATE] = float(fps)
    rendersettings[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL
    rendersettings[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(frame_start/fps)
    rendersettings[c4d.RDATA_FRAMETO] = c4d.BaseTime(frame_end/fps)

    # Ensure saving to disk
    rendersettings[c4d.RDATA_SAVEIMAGE] = True
    # Ensure consistent naming (Name0000)
    rendersettings[c4d.RDATA_NAMEFORMAT] = 0

    # Set Fileformat
    if file_format == "jpg":
        rendersettings[c4d.RDATA_FORMAT] = c4d.FILTER_JPG
    elif file_format == "png":
        rendersettings[c4d.RDATA_FORMAT] = c4d.FILTER_PNG
    elif file_format == "tif":
        rendersettings[c4d.RDATA_FORMAT] = c4d.FILTER_TIF
    elif file_format == "tga":
        rendersettings[c4d.RDATA_FORMAT] = c4d.FILTER_TGA
    elif file_format == "exr":
        rendersettings[c4d.RDATA_FORMAT] = 1016606  # c4d.FILTER_EXR
    elif file_format == "mp4":
        rendersettings[c4d.RDATA_FORMAT] = 1125 # c4d.FILTER_mp4
        
    # Set Alpha
    rendersettings[c4d.RDATA_ALPHACHANNEL] = useAlpha
    rendersettings[c4d.RDATA_SEPARATEALPHA] = separate_alpha

    # Set resolution
    rendersettings[c4d.RDATA_XRES] = float(width)
    rendersettings[c4d.RDATA_YRES] = float(height)

    set_hardware_render_settings(hw_rendersettings=hw_rendersettings, renderdata=renderdata)

    # initialize bitmap
    bmp = c4d.bitmaps.BaseBitmap()
    bmp.Init(x=width, y=height, depth=24)
    if bmp is None:
        raise RenderError(
            "An error occurred during rendering: could not create bitmap."
        )

    c4d.StopAllThreads()
    renderdata.SetName(name)
    doc.InsertRenderData(renderdata)
    doc.SetActiveRenderData(renderdata)
    c4d.EventAdd()

    try:
        # Use a temporary directory for rendering to ensure control over naming
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_name = "render"
            temp_path = os.path.join(temp_dir, temp_name)
            renderdata[c4d.RDATA_PATH] = temp_path

            # Renders the document
            result = c4d.documents.RenderDocument(
                doc,
                renderdata.GetDataInstance(),
                bmp,
                c4d.RENDERFLAGS_NODOCUMENTCLONE
            )

            if result != c4d.RENDERRESULT_OK:
                raise RenderError(
                    "Failed to render {filepath}. (error code: {result})".format(
                        filepath=filepath, result=result
                    )
                )

            # Move and rename generated files to the target destination
            dest_dir = os.path.dirname(filepath)
            dest_filename = os.path.basename(filepath)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            generated_files = os.listdir(temp_dir)
            if not generated_files:
                # Double check rendersettings
                save_image = renderdata[c4d.RDATA_SAVEIMAGE]
                global_save = renderdata[c4d.RDATA_GLOBALSAVE]
                raise RenderError(
                    f"Render reported success, but no files found in {temp_dir}. "
                    f"RDATA_SAVEIMAGE={save_image}, RDATA_GLOBALSAVE={global_save}"
                )

            is_movie = file_format in ["mp4", "mov", "avi"]

            for f in generated_files:
                # If we only have one file and it doesn't match the prefix, but we expect a movie
                # or single frame, we might want to be lenient.
                # However, for now, let's stick to the prefix check but log what we found if it fails.
                if not f.startswith(temp_name):
                    log.warning(f"Found unexpected file in temp dir: {f} (expected prefix: {temp_name})")
                    # If it's the only file there, assume it is the render
                    if len(generated_files) == 1:
                        log.warning(f"Assuming {f} is the correct render artifact despite naming mismatch.")
                    else:
                        continue

                src_path = os.path.join(temp_dir, f)

                # Determine suffix
                # If the file starts with the temp_name, strip it.
                # If we are in the "fallback" mode (single file, wrong name), take the extension.
                if f.startswith(temp_name):
                    suffix = f[len(temp_name):] # e.g. "0000.jpg" or ".mp4"
                else:
                    _, ext = os.path.splitext(f)
                    suffix = ext

                if is_movie:
                    # For movies, we expect the destination filename to already include the extension
                    # (handled by extract_review.py)
                    # output: reviewMain.mp4
                    new_name = dest_filename
                else:
                    # Check if this is a single frame render requesting a specific filename
                    # (e.g. thumbnail.jpg)
                    is_single_frame = (frame_start == frame_end)
                    ext_match = dest_filename.lower().endswith(f".{file_format.lower()}")

                    if is_single_frame and ext_match:
                        # Use destination filename exactly (ignore frame number suffix)
                        new_name = dest_filename
                    else:
                        # For sequences (or single frames without explicit extension):
                        # destination filename is the prefix (e.g. reviewMain)
                        # output: reviewMain0000.jpg
                        new_name = dest_filename + suffix

                dst_path = os.path.join(dest_dir, new_name)
                shutil.move(src_path, dst_path)
                log.info(f"Moved rendered file {src_path} to {dst_path}")

    finally:
        renderdata.Remove()
        c4d.EventAdd()

    return filepath


def set_hardware_render_settings(hw_rendersettings, renderdata):
    """Set the hardware render settings for the active document.
    Args:
        hw_rendersettings (dict): Dictionary of hardware render settings.
        renderdata (c4d.documents.RenderData): Render data to apply settings to.
    Returns: c4d.documents.RenderData
    """
    
    hw_rd = c4d.BaseList2D(c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE)
    # Effects Settings
    hw_rd[c4d.VP_PREVIEWHARDWARE_ANTIALIASING] = hw_rendersettings.get("AA", 2)
    if hw_rendersettings.get("SuperSampling", 2) == 0:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_NONE
    elif hw_rendersettings.get("SuperSampling", 2) == 1:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_2
    elif hw_rendersettings.get("SuperSampling", 2) == 2:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_3
    elif hw_rendersettings.get("SuperSampling", 2) == 3:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_4
    elif hw_rendersettings.get("SuperSampling", 2) == 4:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_5
    elif hw_rendersettings.get("SuperSampling", 2) == 5:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_8
    elif hw_rendersettings.get("SuperSampling", 2) == 6:
        hw_rd[c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING] = c4d.VP_PREVIEWHARDWARE_SUPERSAMPLING_16
    hw_rd[c4d.VP_PREVIEWHARDWARE_ENHANCEDOPENGL] = hw_rendersettings.get("useEffects", True)
    hw_rd[c4d.VP_PREVIEWHARDWARE_NOISE] = hw_rendersettings.get("useHQNoise", False)
    hw_rd[c4d.VP_PREVIEWHARDWARE_TRANSPARENCY] = hw_rendersettings.get("useTransparency", True)
    hw_rd[c4d.VP_PREVIEWHARDWARE_SHADOW] = hw_rendersettings.get("useShadows", False)
    hw_rd[c4d.VP_PREVIEWHARDWARE_REFLECTIONS] = hw_rendersettings.get("useReflections", True)
    hw_rd[c4d.VP_PREVIEWHARDWARE_SSAO] = hw_rendersettings.get("useSSAO", False)
    hw_rd[c4d.VP_PREVIEWHARDWARE_DEPTHOFFIELD] = hw_rendersettings.get("useDOF", False)
    
    # Filter Settings
    hw_rd[c4d.VP_PREVIEWHARDWARE_ONLY_GEOMETRY] = hw_rendersettings.get("useGeoOnly", True)
    if hw_rendersettings.get("useGeoOnly", False) == False:
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_GRID] = hw_rendersettings.get("filterGrid", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_NULL] = hw_rendersettings.get("filterNull", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_SPLINE] = hw_rendersettings.get("filterSpline", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_DEFORMER] = hw_rendersettings.get("filterDeformer", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_FIELD] = hw_rendersettings.get("filterField", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_JOINT] = hw_rendersettings.get("filterJoint", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_CAMERA] = hw_rendersettings.get("filterCamera", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_LIGHT] = hw_rendersettings.get("filterLight", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DISPLAYFILTER_OTHER] = hw_rendersettings.get("filterOther", False)
        hw_rd[c4d.VP_PREVIEWHARDWARE_DATA_SHOWPATH] = hw_rendersettings.get("filterAnimPath", False)

    renderdata.InsertVideoPost(hw_rd)

    return renderdata

