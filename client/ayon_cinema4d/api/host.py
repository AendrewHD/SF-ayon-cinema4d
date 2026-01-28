import os
import logging
import contextlib

import c4d
import pyblish.api

from ayon_core.lib import register_event_callback
from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    register_inventory_action_path,
)

import ayon_cinema4d

from . import lib, plugin, pipeline, workio

log = logging.getLogger("ayon_cinema4d")

HOST_DIR = os.path.dirname(os.path.abspath(ayon_cinema4d.__file__))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"


class Cinema4DHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "cinema4d"

    def __init__(self):
        super(Cinema4DHost, self).__init__()

    def install(self):
        # process path mapping
        # dirmap_processor = Cinema4DDirmap("cinema4d", project_settings)
        # dirmap_processor.process_dirmap()

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        pyblish.api.register_host("cinema4d")

        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)

        if os.path.isdir(INVENTORY_PATH) and any(
            os.path.isfile(os.path.join(INVENTORY_PATH, filename))
            for filename in os.listdir(INVENTORY_PATH)
            if filename.endswith(".py")
        ):
            register_inventory_action_path(INVENTORY_PATH)

        self.log.info(PUBLISH_PATH)

        register_event_callback("taskChanged", pipeline.on_task_changed)

    def open_workfile(self, filepath):
        return workio.open_file(filepath)

    def save_workfile(self, filepath=None):
        return workio.save_file(filepath)

    def get_current_workfile(self):
        return workio.current_file()

    def workfile_has_unsaved_changes(self):
        return workio.has_unsaved_changes()

    def get_workfile_extensions(self):
        return workio.file_extensions()

    def get_containers(self):
        return pipeline.iter_containers()

    @contextlib.contextmanager
    def maintained_selection(self):
        with lib.maintained_selection():
            yield

    def _get_context_node(self, create_if_not_exists=False):
        doc = lib.active_document()
        context_node = None
        for creator_id, obj in plugin.iter_instance_objects(doc):
            if creator_id == AYON_CONTEXT_CREATOR_IDENTIFIER:
                context_node = obj

        if context_node is None and create_if_not_exists:
            context_node = plugin.create_selection([], name="AYON_context")
            plugin.parent_to_ayon_null(context_node)

        return context_node

    def update_context_data(self, data, changes):
        if not data:
            return

        context_node = self._get_context_node(create_if_not_exists=True)
        data["id"] = plugin.AYON_INSTANCE_ID
        data["creator_identifier"] = AYON_CONTEXT_CREATOR_IDENTIFIER
        lib.imprint(context_node, data)

    def get_context_data(self):
        context_node = self._get_context_node()
        if context_node is None:
            return {}

        data = lib.read(context_node)

        # Pop our custom data that we use to find the node again
        data.pop("id", None)
        data.pop("creator_identifier", None)

        return data
