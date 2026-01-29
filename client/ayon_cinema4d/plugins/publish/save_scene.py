import pyblish.api
from ayon_core.pipeline import registered_host, KnownPublishError
import c4d


def get_document_path(doc: c4d.documents.BaseDocument):
    doc_root = doc.GetDocumentPath()
    doc_name = doc.GetDocumentName()
    if doc_root and doc_name:
        return os.path.join(doc_root, doc_name)
    return


class SaveCurrentSceneBlender(pyblish.api.ContextPlugin):
    """Save current scene.

    Always ensure the current scene is saved before we continue extracting,
    so that our scene state is reproducable and consistent.
    """

    label = "Save current file"
    order = pyblish.api.ExtractorOrder - 0.49
    hosts = ["cinema4d"]

    def process(self, context):
        host = registered_host()

        doc: c4d.documents.BaseDocument = context.data["doc"]
        # If file has no modifications, skip forcing a file save

        current_file = host.get_current_document()
        assert context.data['currentFile'] == current_file

        self.log.debug(f"Saving current file: {current_file}")
        c4d.documents.SaveDocument(
            doc, current_file,
            saveflags=c4d.SAVEDOCUMENTFLAGS_NONE,
            format=c4d.FORMAT_C4DEXPORT
        )
