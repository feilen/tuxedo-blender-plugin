import bpy
import mathutils
from ..properties import get_steam_library
from ..tools.translate import t
from ..tools import core
from ..tools.dictionaries import bone_names
import typing

from ..ui import register_ui_tab

#Making a class that looks like a blender panel just to use it to cut the code up for tabs
#This is kinda a bad look but at least it makes the UI nice! - @989onan

@register_ui_tab
class Bake_PT_warnings:
    bl_enum = "WARNINGS"
    bl_label = t('BakePanel.WarningPanel.label')
    bl_description = t('BakePanel.WarningPanel.desc') 
    icon = "ERROR"
    
    def poll(cls, context):
        return True
    
    def draw_panel(main_panel: bpy.types.Panel, context: bpy.types.Context, col: bpy.types.UILayout):
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
        armature = core.get_armature(context)
        armature_data: bpy.types.Armature = None
        if(armature):
            armature_data = armature.data
         
        if armature_data:
            missing_prefered_names: list[str] = []


            reverse_bone_lookup: dict[str, str] = dict()
            for (preferred_name, name_list) in bone_names.items():
                missing_prefered_names.append(preferred_name)
                for name in name_list: 
                    reverse_bone_lookup[name] = preferred_name
                    
            for bone in armature_data.bones:
                if core.simplify_bonename(bone.name) in reverse_bone_lookup:
                    if reverse_bone_lookup[core.simplify_bonename(bone.name)] in missing_prefered_names:
                        missing_prefered_names.remove(reverse_bone_lookup[core.simplify_bonename(bone.name)])
                        
            for name in missing_prefered_names:
                row = col.row(align=True)
                has_error = True
                row.label(text="Your armature is missing the "+core.simplify_bonename(name)+" bone! Try renaming it to that name to fix it!", icon="ARMATURE_DATA")

            
                    
        if any(item.export_format == "GMOD" for item in context.scene.bake_platforms):
            has_gmod_error = False
            has_polygon_error = False
            for obj in core.get_meshes_objects(context):
                #print(len(obj.data.polygons))
                if len(obj.data.polygons) > 9900:
                    has_gmod_error = True
                    has_polygon_error = True
                    row = col.row(align=True)
                    row.label(text=obj.name+" Has more than 9900 polygons.", icon="MESH_DATA")
            if has_polygon_error:
                row = col.row(align=True)
                col2 = row.column(align=True)
                col2.label(text="To keep under the hard limit of 10000 per mesh for Gmod,")
                col2.label(text="meshes above 9900 will be reduced by Tuxedo during bake.")
            if armature_data:
                reverse_bone_lookup: dict[str, str] = dict()
                bone_arm_list: list[str] = ["right_wrist","left_wrist","right_arm","left_arm","left_elbow","right_elbow"]
                for (preferred_name, name_list) in bone_names.items():
                    if preferred_name in bone_arm_list:
                        for name in name_list: 
                            reverse_bone_lookup[name] = preferred_name
                #print("dictionary")
                #print(reverse_bone_lookup)
                arm_bones: dict[str, bpy.types.Bone] = {}
                for bone in armature_data.bones:
                    if core.simplify_bonename(bone.name) in reverse_bone_lookup:
                        arm_bones[reverse_bone_lookup[core.simplify_bonename(bone.name)]] = bone
                #print(arm_bones)
                for name,bone in arm_bones.items():
                    bone_vec = mathutils.Vector((0,1,0))
                    bone_vec.rotate(bone.matrix_local.to_euler())
                    bone_vec.normalize()
                    
                    if "right" in name:
                        bone_vec = bone_vec.dot(mathutils.Vector((-1,0,0)))
                    else:
                        bone_vec = bone_vec.dot(mathutils.Vector((1,0,0)))
                    
                    
                    if 1-bone_vec > .005:
                        has_gmod_error = True
                        row = col.row(align=True)
                        row.label(text="Your "+bone.name+" bone in edit mode is not in t-pose! difference:"+str(round((1-bone_vec)*1000)/10)+"%", icon="ARMATURE_DATA")
            
            
            if not get_steam_library(None):
                row = col.row(align=True)
                has_gmod_error = True
                col2 = row.column(align=True)
                col2.label(text="Tuxedo was not able to find Gmod on your machine!", icon="ERROR")
                col2.label(text="You may be on mac, linux, or don't have gmod with steam installed.", icon="ERROR")
            
            if not has_gmod_error:
                row = col.row(align=True)
                row.label(text="No Gmod errors or warnings.", icon="CHECKMARK")
            #add our gmod error to if we have errors, for displaying no error dialogue
            has_error = has_gmod_error or has_error
        
        
        
        if not has_error:
            main_panel.has_errors = False
            row = col.row(align=True)
            row.label(text="No general errors or warnings.", icon="CHECKMARK")
            for i in range(0,5):
                row = col.row(align=True)
                row.label(text="")
        else:
            main_panel.has_errors = True
        
        

    