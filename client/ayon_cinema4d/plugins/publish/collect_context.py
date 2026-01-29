import pyblish.api
import c4d

from ayon_cinema4d.api import workio, plugin


class CollectContext(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Cinema4D Current File"
    hosts = ["cinema4d"]

    def process(self, context):
        """Inject the current working file"""
        current_file = workio.current_file()
        context.data['currentFile'] = current_file

        """Inject the current document""" #cinema 4d specific
        context.data['doc'] = c4d.documents.GetActiveDocument()
