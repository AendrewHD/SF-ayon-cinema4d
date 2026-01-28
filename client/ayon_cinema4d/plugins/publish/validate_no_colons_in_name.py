import pyblish.api
from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishValidationError,
    OptionalPyblishPluginMixin
)
import c4d


class ValidateNoColonsInName(pyblish.api.InstancePlugin,
                             OptionalPyblishPluginMixin):
    """Validate that there are no colons in object names.

    Colons are illegal characters in many file systems and can cause issues
    with naming conventions.
    """

    order = ValidateContentsOrder
    hosts = ["cinema4d"]
    families = ["*"]
    label = "Validate No Colons In Name"
    optional = True

    def process(self, instance):
        if not self.is_active(instance.data):
            return

        invalid = []
        for obj in instance:
            if ":" in obj.GetName():
                invalid.append(obj.GetName())

        if invalid:
            raise PublishValidationError(
                "Found objects with colons in their name:\n{}".format(
                    "\n".join(invalid)
                ),
                title="Colons in Object Names"
            )
