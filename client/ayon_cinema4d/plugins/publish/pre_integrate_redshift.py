import pyblish.api

class PreIntegrateRedshift(pyblish.api.InstancePlugin):
    """
    Switch product type to 'render' for Redshift renders before integration.

    This ensures that locally rendered Redshift products (which use 'redshiftRender'
    to avoid Deadline submission) are integrated using the standard 'render'
    anatomy template.
    """
    order = pyblish.api.IntegratorOrder - 0.1
    label = "Pre-Integrate Redshift"
    hosts = ["cinema4d"]
    families = ["redshiftRender"]

    def process(self, instance):
        self.log.debug(f"Switching product type for {instance.name} to 'render' for integration.")
        instance.data["productType"] = "render"
        instance.data["family"] = "render"
