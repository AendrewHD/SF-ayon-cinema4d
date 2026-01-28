import logging

import c4d

from ayon_core.lib import is_headless_mode_enabled
from ayon_core.pipeline import (
    get_current_folder_path,
    get_current_task_name,
    AYON_CONTAINER_ID,
)

from . import lib

log = logging.getLogger("ayon_cinema4d")

AYON_CONTAINERS = lib.AYON_CONTAINERS


def parse_container(container):
    """Return the container node's full container data.

    Args:
        container (str): A container node name.

    Returns:
        dict[str, Any]: The container schema data for this container node.

    """
    data = lib.read(container)

    # Backwards compatibility pre-schemas for containers
    data["schema"] = data.get("schema", "ayon:container-3.0")

    # Append transient data
    data["objectName"] = container.GetName()
    data["node"] = container

    return data


def iter_containers(doc=None):
    """Yield all objects in the active document that have 'id' attribute set
    matching an AYON container ID"""
    doc = doc or c4d.documents.GetActiveDocument()
    containers = lib.iter_objects(doc.GetFirstObject())
    for container in containers:
        if lib.get_object_user_data_by_name(container, "id") != AYON_CONTAINER_ID:  # noqa
            continue

        data = parse_container(container)
        yield data


def get_containers_layer(doc=None):
    """Get the layer that holds all container objects.

    To make the scene less cluttered the containers (selection objects) are put
    in a layer 'AYON_CONTAINERS'. This layer is hidden in the outliner.

    Arguments:
        doc (optional c4d.documents.BaseDocument): The document to work on. If
            it is None it uses the active document.
    """

    doc = doc or lib.active_document()
    layer_root = doc.GetLayerObjectRoot()
    for layer in layer_root.GetChildren():
        if layer.GetName() == AYON_CONTAINERS:
            return layer

    layer = c4d.documents.LayerObject()
    layer.SetName(AYON_CONTAINERS)
    layer.InsertUnder(layer_root)
    layer[c4d.ID_LAYER_MANAGER] = False
    layer[c4d.ID_LAYER_VIEW] = False
    layer[c4d.ID_LAYER_RENDER] = False
    layer[c4d.ID_LAYER_COLOR] = c4d.Vector(0.3, 0.66, 0.96)
    layer[c4d.ID_LAYER_LOCKED] = True

    c4d.EventAdd()

    return layer


def containerise(name,
                 namespace,
                 nodes,
                 context,
                 loader,
                 suffix="_CON"):
    """Bundle `nodes` into an assembly and imprint it with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        nodes (list): Long names of nodes to containerise
        context (dict): Asset information
        loader (str): Name of loader used to produce this container.
        suffix (str, optional): Suffix of container, defaults to `_CON`.

    Returns:
        container (c4d.BaseObject): OSelection BaseObject container

    """

    container_name = lib.get_unique_namespace(
        name,
        prefix=namespace + "_",
        suffix=suffix
    )
    with lib.undo_chunk():
        container = c4d.BaseObject(c4d.Oselection)
        container.SetName(container_name)
        in_exclude_data = container[c4d.SELECTIONOBJECT_LIST]
        for node in nodes:
            in_exclude_data.InsertObject(node, 1)
        container[c4d.SELECTIONOBJECT_LIST] = in_exclude_data
        doc = lib.active_document()
        doc.InsertObject(container)

        imprint_container(
            container,
            name,
            namespace,
            context,
            loader
        )

        # Add the container to the AYON_CONTAINERS layer
        avalon_layer = get_containers_layer(doc=doc)
        container.SetLayerObject(avalon_layer)
        # Hide the container in the Object Manager
        # container.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
        c4d.EventAdd()

    return container


def imprint_container(
    container,
    name,
    namespace,
    context,
    loader
):
    """Imprints an object with container metadata and hides it from the user
    by adding it into a hidden layer.
    Arguments:
        container (c4d.BaseObject): The object to imprint.
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        context (dict): Asset information
        loader (str): Name of loader used to produce this container.
    """
    data = {
        "schema": "ayon:container-3.0",
        "id": AYON_CONTAINER_ID,
        "name": name,
        "namespace": namespace,
        "loader": str(loader),
        "representation": str(context["representation"]["id"]),
    }

    lib.imprint(container, data, group="AYON")


def on_task_changed():

    if not is_headless_mode_enabled():
        # Get AYON Context menu command plugin (menu item) by its unique id.
        ayon_context = c4d.plugins.FindPlugin(1064692)
        # Update its value with the new context.
        ayon_context.SetName(
            "{}, {}".format(get_current_folder_path(), get_current_task_name())
        )
