import pyblish.api

class PrepareRedshiftFarm(pyblish.api.InstancePlugin):
    """
    Prepare Redshift instance for Farm submission if requested.

    If 'renderOnFarm' is checked, this plugin changes the family to 'render'
    so that the Deadline submitter picks it up.
    """
    order = pyblish.api.CollectorOrder + 0.49 # Run after collection, before Validators/Extractors
    label = "Prepare Redshift Farm"
    hosts = ["cinema4d"]
    families = ["redshiftRender"]

    def process(self, instance):
        if instance.data.get("renderOnFarm"):
            self.log.info(f"Marking {instance.name} for Farm rendering.")
            instance.data["family"] = "render"
            # We keep 'productType' as 'redshiftRender' for now?
            # Deadline submitter likely checks family.
            # But if we change family to 'render', my local extractor (targeting redshiftRender) might skip it?
            # pyblish filtering is based on initial state or dynamic?
            # Usually dynamic. If family changes, subsequent plugins check against new family.

            # Note: CreateRedshiftRender sets product_type="redshiftRender".
            # If we change family to "render", we ensure Deadline sees it.
            # We also need to ensure ExtractRedshiftRender ignores it.
            # ExtractRedshiftRender targets "redshiftRender".

            # If I change family to "render", does "redshiftRender" plugin still run?
            # Only if "redshiftRender" is in families list.
            # By default families = ["redshiftRender"].
            # If I set instance.data["family"] = "render", then families = ["render"].
            # So "redshiftRender" plugin will NOT run. Perfect.

            # However, we must ensure 'render' family logic runs.
            # Usually generic collectors run early.
            pass
