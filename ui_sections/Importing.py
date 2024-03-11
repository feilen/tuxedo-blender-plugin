import bpy

from bpy.types import UIList, Operator, Panel
from ..globals import blender as blenderversion

from ..tools.core import version_too_new

from ..tools.importing import Tuxedo_OT_ImportAnyModel

from ..tools.translate import t

from ..class_register import wrapper_registry


@wrapper_registry
class Tuxedo_PT_ImportingPanel(Panel):
    bl_label = t('Importing.import_any_model.label')
    bl_idname = "tuxedo.import_any_model"
    bl_description = t('Importing.import_any_model.desc')
    bl_idname = 'VIEW3D_PT_tuximport'
    bl_category = 'Tuxedo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = -100


    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)


        

        if(version_too_new()):
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text=t('Tuxedo.unsupported_version.1'), icon="INFO")
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text=t('Tuxedo.unsupported_version.2'), icon="BLANK1")
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text=t('Tuxedo.unsupported_version.3').format(ver=str(blenderversion).replace("(","").replace(")","").replace(",",".").replace(" ","")), icon="BLANK1")

        row = col.row()
        row.label(text=t('Tools.import_any_model.desc'))
        
        row = col.row(align=True)
        row.operator(Tuxedo_OT_ImportAnyModel.bl_idname,icon="ARMATURE_DATA")


        

