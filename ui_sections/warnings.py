import bpy
import addon_utils
import mathutils

from .. import bake as Bake
from ..tools import t, get_meshes_objects, get_armature, simplify_bonename, bone_names
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
        if any(item.export_format == "GMOD" for item in context.scene.bake_platforms):
            has_gmod_error = False
            has_polygon_error = False
            for obj in get_meshes_objects(context):
                #print(len(obj.data.polygons))
                if len(obj.data.polygons) > 9900:
                    has_gmod_error = True
                    has_polygon_error = True
                    row = col.row(align=True)
                    row.label(text=obj.name+" Has more than 9900 polygons.", icon="MESH_DATA")
            
            armature = get_armature(context)
            if armature:
                reverse_bone_lookup = dict()
                bone_arm_list = ["right_wrist","left_wrist","right_arm","left_arm","left_elbow","right_elbow"]
                for (preferred_name, name_list) in bone_names.items():
                    if preferred_name in bone_arm_list:
                        for name in name_list: 
                            reverse_bone_lookup[name] = preferred_name
                #print("dictionary")
                #print(reverse_bone_lookup)
                arm_bones = {}
                for bone in armature.data.bones:
                    if simplify_bonename(bone.name) in reverse_bone_lookup:
                        arm_bones[reverse_bone_lookup[simplify_bonename(bone.name)]] = bone
                #print(arm_bones)
                for bone_name in bone_arm_list:
                    bone_vec = mathutils.Vector((0,1,0))
                    bone_vec.rotate(arm_bones[bone_name].matrix_local.to_euler())
                    bone_vec.normalize()
                    
                    if "_r" in bone_name or "right" in bone_name:
                        bone_vec = bone_vec.dot(mathutils.Vector((-1,0,0)))
                    else:
                        bone_vec = bone_vec.dot(mathutils.Vector((1,0,0)))
                    
                    
                    if 1-bone_vec > .005:
                        has_gmod_error = True
                        row = col.row(align=True)
                        row.label(text="Your "+arm_bones[bone_name].name+" bone in edit mode is not in t-pose! difference:"+str(round((1-bone_vec)*1000)/10)+"%", icon="ARMATURE_DATA")
                    
            
            if has_polygon_error:
                row = col.row(align=True)
                row.label(text="To keep under the hard limit of 10000 per mesh for Gmod, meshes above 9900 will be reduced by Tuxedo during bake.",  icon="EVENT_G")
            if not has_gmod_error:
                row = col.row(align=True)
                row.label(text="No Gmod errors or warnings.", icon="CHECKMARK")
            
            #add our gmod error to if we have errors, for displaying no error dialogue
            has_error = has_gmod_error or has_error
        
        
        
        if not has_error:
            row = col.row(align=True)
            row.label(text="No general errors or warnings.", icon="CHECKMARK")
            for i in range(0,5):
                row = col.row(align=True)
                row.label(text="")
        
        

    