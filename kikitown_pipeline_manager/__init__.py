import os
import subprocess
import sys
from importlib.util import find_spec
from typing import List

# Resolve external dependencies
EXTERNAL_PACKAGES = ["pygltflib", "gltf_formatter", "blender_validator"]

current = os.path.dirname(os.path.realpath(__file__))
EXTERNAL_LIB_DIR = f"{current}/external_lib"
sys.path.append(EXTERNAL_LIB_DIR)


def prepare_external_dependencies(packages: List[str]):
    for pkg in EXTERNAL_PACKAGES:
        py_exec = sys.executable
        # subprocess.call([py_exec, "-m", "pip", "uninstall", "-y", pkg])

    missing_pkgs = [pkg for pkg in packages if (pkg not in sys.modules) and (not find_spec(pkg))]

    if len(missing_pkgs) > 0:
        py_exec = sys.executable
        subprocess.call([py_exec, "-m", "ensurepip", "--user"])
        subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "pip"])

        for pkg in missing_pkgs:
            py_exec = sys.executable
            subprocess.call([py_exec, "-m", "pip", "install", "--user", pkg])

        for filename in os.listdir(EXTERNAL_LIB_DIR):
            f = os.path.join(EXTERNAL_LIB_DIR, filename)
            if os.path.isfile(f) and f.endswith(".whl"):
                subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "--user", f])


if "pytest" not in sys.modules:
    prepare_external_dependencies(EXTERNAL_PACKAGES)


# pylint: disable=wrong-import-position
from kikitown_pipeline_manager import exporter, manager

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
    manager.register()
    exporter.register()


def unregister():
    manager.unregister()
    exporter.unregister()


if __name__ == "__main__":
    unregister()
    register()
