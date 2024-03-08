import bpy
import addon_utils

from .. import bake as Bake
from ..tools import t, get_meshes_objects, get_armature
from ..tools import GenerateTwistBones, TwistTutorialButton, SmartDecimation, RepairShapekeys
from ..tools import AutoDecimatePresetGood, AutoDecimatePresetQuest, AutoDecimatePresetExcellent
from ..tools import FitClothes, SRanipal_Labels, has_shapekeys, get_shapekeys_ft, materials_list_update

from ..ui import register_ui_tab

@register_ui_tab
class Bake_PT_warnings:
    bl_enum = "WARNINGS"
    bl_label = "Warnings"
    bl_description = "Different warnings before bake."
    icon = "ERROR"
    
    def poll(cls, context):
        return True
    
    def draw_panel(main_panel, context, col):
        has_error = False
        # Warnings. Ideally these should be dynamically generated but only take up a limited number of rows
        if main_panel.non_node_mat_names:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following materials do not use nodes!", icon="ERROR")
            row = col.row(align=True)
            row.label(text="Ensure they have Use Nodes checked in their properties or Bake will not run.", icon="BLANK1")
            for name in main_panel.non_node_mat_names:
                row = col.row(align=True)
                row.label(text=name, icon="MATERIAL")
        if main_panel.non_bsdf_mat_names:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following materials do not use Principled BSDF!", icon="INFO")
            row = col.row(align=True)
            row.label(text="Bake may have unexpected results.", icon="BLANK1")
            for name in main_panel.non_bsdf_mat_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="MATERIAL")
        if main_panel.multi_bsdf_mat_names:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following materials have multiple Principled BSDF!", icon="INFO")
            row = col.row(align=True)
            row.label(text="Bake may have unexpected results.", icon="BLANK1")
            for name in main_panel.multi_bsdf_mat_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="MATERIAL")
        if main_panel.empty_material_slots:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following objects have no material.", icon="INFO")
            row = col.row(align=True)
            row.label(text="Please assign one before continuing.", icon="BLANK1")
            for name in main_panel.empty_material_slots:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="OBJECT_DATA")
        if main_panel.non_world_scale_names:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following objects do not have scale applied", icon="INFO")
            row = col.row(align=True)
            row.label(text="The resulting islands will be inversely scaled.", icon="BLANK1")
            for name in main_panel.non_world_scale_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name + ": " + "{:.1f}".format(1.0/bpy.data.objects[name].scale[0]) + "x", icon="OBJECT_DATA")
        if main_panel.too_many_uvmaps:
            has_error = True
            row = col.row(align=True)
            row.label(text="The following objects have too many UVMaps!", icon="ERROR")
            row = col.row(align=True)
            row.label(text="Bake will likely fail, you can have at most 6 maps.", icon="BLANK1")
            for name in main_panel.too_many_uvmaps:
                row = col.row(align=True)
                row.separator()
                row.label(text=name + ": " + "{}".format(len(bpy.data.objects[name].data.uv_layers)), icon="OBJECT_DATA")
        
        if not has_error:
            row = col.row(align=True)
            row.label(text="No errors", icon="CHECKMARK")
            for i in range(0,5):
                row = col.row(align=True)
                row.label(text="")
        
        

    