import pyblish.api
from ayon_cinema4d.api import plugin

class CollectReviewableInstances(plugin.Cinema4DInstancePlugin):
    """Collect Reviewable Instances
    """
    
    order = pyblish.api.CollectorOrder
    label = "Collect Reviewable Instances"
    families = ["review"]
    
    def process(self, instance):
        creator_attribute = instance.data.get ("creator_attribute", {})
        
        instance.data["review"] = creator_attribute.get("review", False)