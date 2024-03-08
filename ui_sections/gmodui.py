import bpy
import addon_utils

from bpy.types import UIList, Operator, Panel
from bpy_extras.io_utils import ImportHelper

from ..class_register import wrapper_registry
from ..ui import register_ui_tab

button_height = 1


@register_ui_tab
class GmodPanel:
    bl_label = "Gmod"
    bl_enum = "GMOD"
    bl_description = "Gmod Options For Current Selection"
    icon = "EVENT_G"
    
    
    def poll(cls, context):
        return context.scene.bake_platforms[context.scene.bake_platform_index].export_format == "GMOD"
    
    def draw_panel(self, context, col):

        row = col.row(align=True)
        item = context.scene.bake_platforms[context.scene.bake_platform_index]
        if item.export_format == "GMOD":
            row = col.row(align=True)
            row.prop(item, "gmod_model_name", expand=True)
            row = col.row(align=True)
        
        