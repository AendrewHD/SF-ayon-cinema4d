import pyblish.api
import c4d
from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishValidationError,
    OptionalPyblishPluginMixin
)


class ValidateObjectMode(pyblish.api.ContextPlugin,
                         OptionalPyblishPluginMixin):
    """Validate that the object mode is set to Model (Object) mode.

    Some exports might behave unexpectedly if the user is in Point, Edge or
    Polygon mode.
    """

    order = ValidateContentsOrder
    hosts = ["cinema4d"]
    label = "Validate Object Mode"
    optional = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        doc = context.data["doc"]
        mode = doc.GetMode()

        # Check if we are in one of the component modes
        # c4d.Mpoints, c4d.Medges, c4d.Mpolygons
        if mode in [c4d.Mpoints, c4d.Medges, c4d.Mpolygons]:
            raise PublishValidationError(
                "Cinema 4D is in component mode (Points, Edges or Polygons). "
                "Please switch to Model (Object) mode before publishing.",
                title="Invalid Object Mode"
            )
