import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{current}/external_lib")

# pylint: disable=wrong-import-position
from kikitown_pipeline_manager import animating, exporter

bl_info = {
    "name": "GGLabs_Kikitown_Exporter",
    "author": "GGLabs",
    "version": (4, 6, 0),
    "blender": (3, 4, 1),
    "location": "File > Export > Kikitown",
    "description": "Export Kikitown Resources",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/GoogGangLabs/kikitown_pipeline_manager",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development",
}


def register():
    animating.register()
    exporter.register()


def unregister():
    animating.unregister()
    exporter.unregister()


if __name__ == "__main__":
    unregister()
    register()
