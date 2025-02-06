import importlib
import os
import subprocess
import sys
from importlib.util import find_spec
from typing import Dict, List

# Resolve external dependencies
EXTERNAL_PACKAGES = {"pygltflib": "pygltflib", "PyYAML": "yaml"}
WHL_PACKAGES = ["gltf_formatter", "blender_validator"]

current = os.path.dirname(os.path.realpath(__file__))
EXTERNAL_LIB_DIR = f"{current}/external_lib"
for p in [p for p in sys.path if "/external_lib" in p]:
    sys.path.remove(p)
sys.path.insert(0, EXTERNAL_LIB_DIR)


def is_new_version_is_newer(current_version: str, new_version: str) -> bool:
    ret = False
    current_ts = [int(v) for v in current_version.split(".")]
    new_ts = [int(v) for v in new_version.split(".")]

    for idx in range(0, 4):
        if current_ts[idx] < new_ts[idx]:
            ret = True
            break

    return ret


def prepare_external_dependencies(packages: Dict[str, str]):
    missing_pkgs = [
        pkg
        for pkg, module in packages.items()
        if (module not in sys.modules) and (not find_spec(module))
    ]

    if len(missing_pkgs) > 0:
        py_exec = sys.executable
        subprocess.call([py_exec, "-m", "ensurepip", "--user"])
        subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "pip"])

        for pkg in missing_pkgs:
            py_exec = sys.executable
            subprocess.call([py_exec, "-m", "pip", "install", "--user", pkg])


# blender_validator-1.0.2.1-py3-none-any.whl
def upgrade_whl_packages(packages: List[str], force=False):
    missing_pkgs = set()
    installed_pkgs_with_version = {}

    for pkg in packages:
        try:
            m = importlib.import_module(pkg)
        except ModuleNotFoundError:
            missing_pkgs.add(pkg)
        else:
            installed_pkgs_with_version[pkg] = m.__version__

    for filename in os.listdir(EXTERNAL_LIB_DIR):
        (p_pkg, p_version, _) = filename.split("-", 2)
        should_install = is_new_version_is_newer(
            installed_pkgs_with_version.get(p_pkg, "0.0.0.0"), p_version
        )

        if should_install:
            missing_pkgs.add(p_pkg)

    if len(missing_pkgs) > 0:
        py_exec = sys.executable
        for filename in os.listdir(EXTERNAL_LIB_DIR):
            f = os.path.join(EXTERNAL_LIB_DIR, filename)
            if os.path.isfile(f) and f.endswith(".whl"):
                subprocess.call(
                    [py_exec, "-m", "pip", "install", "--upgrade", "--user", f]
                )


if "pytest" not in sys.modules:
    # This doesn't work at random in Windows.
    # prepare_external_dependencies(EXTERNAL_PACKAGES)
    # upgrade_whl_packages(WHL_PACKAGES)
    pass


# pylint: disable=wrong-import-position
from gglabs_art_manager import manager

bl_info = {
    "name": "GGLabs_Art_Manager",
    "author": "GGLabs",
    "version": (1, 0, 1),  # means nothing
    "blender": (4, 3, 1),
    "location": "View3D",
    "description": "Manage and export 3D Resources for GGLabs",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/GoogGangLabs/gglabs_art_manager",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development",
}


def register():
    manager.register()


def unregister():
    manager.unregister()


if __name__ == "__main__":
    unregister()
    register()
