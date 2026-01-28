import pyblish.api

from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishValidationError,
    OptionalPyblishPluginMixin
)


class ValidateWorkfile(pyblish.api.ContextPlugin, OptionalPyblishPluginMixin):
    """Validate that the current workfile is saved."""

    order = ValidateContentsOrder
    label = "Validate Workfile"
    hosts = ["cinema4d"]
    optional = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        current_file = context.data.get("currentFile")
        if not current_file:
            raise PublishValidationError(
                "Current file is not saved. Please save the file before publishing.",
                title="Workfile Not Saved"
            )

        # Check for unsaved changes?
        # Typically we might want to check doc.GetChanged() but explicit save plugins handle that.
