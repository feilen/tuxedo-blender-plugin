import bpy

from bpy.types import UIList, Operator, Panel
from ..globals import blender as blenderversion
from .. import globals

from ..tools.core import version_too_new

from ..tools.importing import Tuxedo_OT_ImportAnyModel, Tuxedo_OT_ExportVRC, Tuxedo_OT_ExportResonite

from ..tools.tools import Tuxedo_OT_ApplyAsRest, Tuxedo_OT_SavePoseAsShapekey, Tuxedo_OT_StartPoseMode, Tuxedo_OT_EndPoseMode

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
        row.scale_y = 2
        row.operator(Tuxedo_OT_ImportAnyModel.bl_idname,icon="ARMATURE_DATA")
        row = col.row(align=False)
        row.label(text="")
        row = col.row(align=True)
        row.operator(Tuxedo_OT_ExportVRC.bl_idname,icon_value=globals.icons_dict["vrchat"].icon_id)
        row = col.row(align=True)
        row.operator(Tuxedo_OT_ExportResonite.bl_idname,icon_value=globals.icons_dict["resonite"].icon_id)


        row = col.row(align=False)
        row.label(text="")
        col2 = col.column(align=True)
        row = col2.row(align=True)
        if context.mode == 'POSE':
            row.operator(Tuxedo_OT_EndPoseMode.bl_idname,icon='POSE_HLT')
            row = col2.row(align=True)
            row.operator(Tuxedo_OT_ApplyAsRest.bl_idname,icon='SHAPEKEY_DATA')
            row = col2.row(align=True)
            row.operator(Tuxedo_OT_SavePoseAsShapekey.bl_idname,icon='POSE_HLT')
        else:
            row.operator(Tuxedo_OT_StartPoseMode.bl_idname,icon='POSE_HLT')
            
            

        

