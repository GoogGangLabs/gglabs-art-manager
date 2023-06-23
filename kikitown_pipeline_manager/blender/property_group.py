from typing import Any, Optional

import bpy

# Declare necessary states for running Kikitown Pipeline Manager's Operators.
# Covers all configurations for running the operator (either from user input or a pre-defined files)
# and internal states to be shown to users such as `Load Complete` marks.
# Also provides helper methods to register/access itself to any given bpy container object. (e.g. `Scene`)


class KPM_PGT_Base(bpy.types.PropertyGroup):
    @classmethod
    def register_key(cls) -> str:
        return f"{cls.__name__}_values".lower()

    @classmethod
    def register_property_group(cls):
        setattr(
            bpy.types.Scene,
            cls.register_key(),
            bpy.props.PointerProperty(type=cls),
        )

    @classmethod
    def unregister_property_group(cls):
        if hasattr(bpy.types.Scene, cls.register_key()):
            pgt: bpy.types.PropertyGroup = getattr(bpy.types.Scene, cls.register_key())
            del pgt

    @classmethod
    def getprops(cls):
        return getattr(bpy.context.scene, cls.register_key())

    @classmethod
    def setattr(cls, attr: str, value: any):
        props: bpy.types.PropertyGroup = cls.getprops()
        setattr(props, attr, value)

    @classmethod
    def getattr(cls, attr: str, vtype: type = str) -> Optional[Any]:
        res = None
        props: bpy.types.PropertyGroup = cls.getprops()

        if hasattr(props, attr):
            v = getattr(props, attr)
            if isinstance(v, vtype):
                res = v

        return res

    @classmethod
    def getattr_int(cls, attr: str) -> Optional[int]:
        return cls.getattr(attr, int)

    @classmethod
    def getattr_str(cls, attr: str) -> Optional[str]:
        return cls.getattr(attr, str)

    @classmethod
    def getattr_bool(cls, attr: str) -> Optional[bool]:
        return cls.getattr(attr, bool)

    @classmethod
    def getattr_abspath(cls, attr: str) -> Optional[str]:
        return bpy.path.abspath(cls.getattr_str(attr))
