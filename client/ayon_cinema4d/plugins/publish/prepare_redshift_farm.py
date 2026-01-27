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
            # Ensure 'families' also reflects this if it exists
            if "families" in instance.data:
                if "redshiftRender" in instance.data["families"]:
                    instance.data["families"].remove("redshiftRender")
                if "render" not in instance.data["families"]:
                    instance.data["families"].append("render")
        else:
            # Ensure 'render' is NOT in family/families for local render
            # This is a safety measure against accidental family pollution
            if instance.data.get("family") == "render":
                 instance.data["family"] = "redshiftRender"

            if "families" in instance.data and "render" in instance.data["families"]:
                instance.data["families"].remove("render")
                if "redshiftRender" not in instance.data["families"]:
                     instance.data["families"].append("redshiftRender")
