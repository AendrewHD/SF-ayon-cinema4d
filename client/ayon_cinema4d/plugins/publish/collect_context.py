import pyblish.api
import c4d

from ayon_cinema4d import api


class CollectContext(pyblish.api.ContextPlugin):
    """Collect current context data.

    Injects:
        - current working file path
        - active c4d document
    """

    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Context"
    hosts = ["cinema4d"]

    def process(self, context):
        # Collect current file
        current_file = api.current_file()
        context.data['currentFile'] = current_file

        # Collect active document
        context.data['doc'] = c4d.documents.GetActiveDocument()

        self.log.debug(f"Collected current file: {current_file}")
