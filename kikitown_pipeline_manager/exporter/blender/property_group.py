import bpy

from kikitown_pipeline_manager.blender import KPM_PGT_Base

__all__ = ["KPM_PGT_Exporter"]


class KPM_PGT_Exporter(KPM_PGT_Base):
    def callback_on_update(self, context):
        fpath = bpy.path.abspath(self.sample_dirpath)

        self.sample_str = fpath

    sample_str: bpy.props.StringProperty(
        name="S",
        description="",
        default="",
    )

    sample_dirpath: bpy.props.StringProperty(
        name="Path Name",
        description="",
        default="//samplepath",
        maxlen=1024,
        update=callback_on_update,
        subtype="DIR_PATH",
    )

    sample_bool: bpy.props.BoolProperty(
        name="B",
        description="",
        default=False,
    )

    sample_choice: bpy.props.EnumProperty(
        name="E",
        description="",
        items=[
            ("id1", "name1", "desc1"),
            ("id2", "name2", "desc2"),
        ],
        default="id1",
    )
