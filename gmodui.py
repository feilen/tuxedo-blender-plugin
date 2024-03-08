import bpy
import addon_utils

from bpy.types import UIList, Operator, Panel
from bpy_extras.io_utils import ImportHelper

from .class_register import wrapper_registry

button_height = 1

@wrapper_registry
class Choose_Steam_Library(Operator, ImportHelper):
    bl_idname = "tuxedo_bake.choose_steam_library"
    bl_label = "Choose Steam Library"

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    @classmethod
    def poll(cls, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        return bake_platforms[index].export_format == "GMOD"
    def execute(self, context):
        context.scene.bake_steam_library = self.directory
        return{'FINISHED'}

@wrapper_registry
class GmodPanel(Panel):
    bl_label = "Gmod Options For Current Selection"
    bl_idname = 'VIEW3D_PT_tuxgmod'
    bl_category = 'Tuxedo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    @classmethod
    def poll(cls, context):
        return context.scene.bake_platforms[context.scene.bake_platform_index].export_format == "GMOD"
    
    def draw_panel(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=True)
        item = context.scene.bake_platforms[context.scene.bake_platform_index]
        if item.export_format == "GMOD":
            row = col.row(align=True)
            row.label(text = "Click on the button below, if the directory looks incorrect.")
            row.operator(Choose_Steam_Library.bl_idname, icon="FILE_FOLDER")
            row = col.row(align=True)
            row.prop(context.scene, "bake_steam_library", expand=True)
            row = col.row(align=True)
            row.prop(item, "gmod_model_name", expand=True)
            row = col.row(align=True)
        
        