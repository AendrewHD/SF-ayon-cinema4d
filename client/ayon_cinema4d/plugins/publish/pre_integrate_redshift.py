import pyblish.api

class PreIntegrateRedshift(pyblish.api.InstancePlugin):
    """
    Switch product type to 'render' for Redshift renders before integration.

    This ensures that locally rendered Redshift products (which use 'redshiftRender'
    to avoid Deadline submission) are integrated using the standard 'render'
    anatomy template.

    We DO NOT change the family to 'render' here, as that might trigger other
    plugins (like Deadline) if they run late or in a second pass. Changing
    'productType' is sufficient for the Integrate plugin to select the correct
    Anatomy template.
    """
    order = pyblish.api.IntegratorOrder - 0.1
    label = "Pre-Integrate Redshift"
    hosts = ["cinema4d"]
    families = ["redshiftRender"]

    def process(self, instance):
        self.log.debug(f"Switching product type for {instance.name} to 'render' for integration.")
        instance.data["productType"] = "render"
        # instance.data["family"] = "render"  <-- Removed to prevent triggering 'render' family plugins
