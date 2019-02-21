# | Created by Ar4ikov
# | Время: 12.02.2019 - 14:38

from os import listdir, path
from importlib import import_module
from pprint import pprint

from discord.ext.commands import Bot as Client
from core.api import BotPlugin


class Modules:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir

        self.init_file = "__init__"

    def get_modules(self):
        valid_ = []
        invalid_ = []

        test_client = Client

        for plugins in listdir(self.plugins_dir):

            if path.isfile(self.plugins_dir + "/" + plugins + "/" + self.init_file + ".py"):

                module = import_module(self.plugins_dir + "." + plugins + "." + self.init_file)
                error_level = 0

                plugin_cls = None

                for cls in dir(module):
                    if not cls.startswith("__"):
                        if BotPlugin in getattr(getattr(module, cls), "__bases__", []):
                            plugin_cls = cls

                if plugin_cls:
                    if not getattr(getattr(module, plugin_cls)(test_client), "client", None):
                        error_level += 1

                    if not getattr(getattr(module, plugin_cls)(test_client), "plugin_name", None):
                        error_level += 1

                    if not getattr(getattr(module, plugin_cls)(test_client), "plugin_id", None):
                        error_level += 1

                    resp = {
                        "plugin": getattr(module, plugin_cls),
                        "plugin_priority": getattr(module, plugin_cls)(test_client).priority,
                        "plugin_name": getattr(module, plugin_cls)(test_client).plugin_name,
                        "plugin_id": getattr(module, plugin_cls)(test_client).plugin_id,
                        "plugin_version": getattr(module, plugin_cls)(test_client).version,
                        "plugin_author": getattr(module, plugin_cls)(test_client).author,
                        "plugin_tasks": getattr(module, plugin_cls)(test_client).tasks,
                        "error_level": error_level
                    }

                    if error_level > 0:
                        invalid_.append(resp)
                    else:
                        valid_.append(resp)

        return valid_, invalid_
