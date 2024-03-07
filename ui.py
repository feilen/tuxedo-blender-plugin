import bpy
import addon_utils

from . import bake as Bake
from .tools import t, get_meshes_objects, get_armature
from .tools import GenerateTwistBones, TwistTutorialButton, SmartDecimation, RepairShapekeys
from .tools import AutoDecimatePresetGood, AutoDecimatePresetQuest, AutoDecimatePresetExcellent
from .tools import FitClothes, SRanipal_Labels, has_shapekeys, get_shapekeys_ft, materials_list_update

from .class_register import wrapper_registry

from bpy.types import UIList, Operator, Panel
from bpy_extras.io_utils import ImportHelper
button_height = 1

@wrapper_registry
class Bake_Platform_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


@wrapper_registry
class Material_Grouping_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here...
        custom_icon = 'MATERIAL'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            col = row.column()
            col.label(text=item.name, icon = custom_icon)
            col = row.column()
            col.prop(item, "group", text="group")
            #col = row.column()
            #col.prop(item, "include", text="include")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

@wrapper_registry
class Material_Grouping_UL_List_Reload(Operator):
    bl_idname = "tuxedo_bake.materials_reload"
    bl_label = "Reload Materials"

    def execute(self, context):
        materials_list_update(context)

        return{'FINISHED'}

@wrapper_registry
class Bake_Platform_New(Operator):
    bl_idname = "tuxedo_bake.platform_add"
    bl_label = "Add"

    def execute(self, context):
        context.scene.bake_platforms.add()

        return{'FINISHED'}

@wrapper_registry
class Bake_Platform_Delete(Operator):
    bl_idname = "tuxedo_bake.platform_remove"
    bl_label = "Delete"

    @classmethod
    def poll(cls, context):
        return context.scene.bake_platforms

    def execute(self, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        bake_platforms.remove(index)
        context.scene.bake_platform_index = min(max(0, index - 1), len(bake_platforms) - 1)

        return{'FINISHED'}

@wrapper_registry
class Bake_Lod_New(Operator):
    bl_idname = "tuxedo_bake.lod_add"
    bl_label = "Add"

    @classmethod
    def poll(cls, context):
        return context.scene.bake_platforms

    def execute(self, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        lods = bake_platforms[index].lods
        lods.add()

        return{'FINISHED'}

@wrapper_registry
class Bake_Lod_Delete(Operator):
    bl_idname = "tuxedo_bake.lod_remove"
    bl_label = "Delete"

    @classmethod
    def poll(cls, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        return context.scene.bake_platforms and len(bake_platforms[index].lods) > 1

    def execute(self, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        lods = bake_platforms[index].lods
        lods.remove(len(lods) - 1)

        return{'FINISHED'}

@wrapper_registry
class Open_GPU_Settings(Operator):
    bl_idname = "tuxedo_bake.open_gpu_settings"
    bl_label = "Open GPU Settings (Top of the page)"

    def execute(self, context):
        bpy.ops.screen.userpref_show()
        context.preferences.active_section = 'SYSTEM'

        return{'FINISHED'}



@wrapper_registry
class ToolPanel(Panel):
    bl_label = "Tools"
    bl_idname = 'VIEW3D_PT_tuxtools'
    bl_category = 'Tuxedo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=True)
        row.prop(context.scene, 'decimation_animation_weighting', expand=True)
        if context.scene.decimation_animation_weighting:
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'decimation_animation_weighting_factor', expand=True)
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'decimation_animation_weighting_include_shapekeys', expand=True)
            col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'decimation_remove_doubles')
        row = col.row(align=True)
        row.operator(AutoDecimatePresetGood.bl_idname)
        row.operator(AutoDecimatePresetExcellent.bl_idname)
        row.operator(AutoDecimatePresetQuest.bl_idname)
        row = col.row(align=True)
        row.prop(context.scene, 'tuxedo_max_tris')
        col.separator()
        col.label(text=t('DecimationPanel.warn.notIfBaking'), icon='INFO')

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator(SmartDecimation.bl_idname, icon='MOD_DECIM')

        col.separator()
        col.separator()

        row = col.row(align=True)
        row.scale_y = button_height
        row.operator(RepairShapekeys.bl_idname, icon='MESH_DATA')

        col.separator()
        col.separator()

        row = col.row(align=True)
        row.scale_y = button_height
        row.operator(TwistTutorialButton.bl_idname, icon='QUESTION')

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator(GenerateTwistBones.bl_idname, icon='OUTLINER_DATA_ARMATURE')

        row = col.row(align=True)
        row.scale_y = 1.2
        row.prop(context.scene, 'generate_twistbones_upper')

        col.separator()
        col.separator()

        row = col.row(align=True)
        row.scale_y = 1.05
        row.label(text="Attach Clothes to Body")

        if len(context.view_layer.objects.selected) <= 1 or not context.view_layer.objects.active or 'Armature' not in context.view_layer.objects.active.modifiers:
            row = col.row(align=True)
            row.scale_y = 1.05
            col.label(text='An already rigged body and other meshes required!', icon='INFO')
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text="Make sure the body is the one highlighted.", icon='BLANK1')
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text="Works with any mesh that conforms closely to the body.", icon='BLANK1')
            return

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator(FitClothes.bl_idname, icon='MOD_CLOTH')

@wrapper_registry
class BakePanel(Panel):
    bl_label = "Tuxedo Bake"
    bl_idname = 'VIEW3D_PT_tuxbake'
    bl_category = 'Tuxedo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=True)
        row.operator(Bake.BakeTutorialButton.bl_idname, icon='FORWARD')
        col.separator()

        # Warnings. Ideally these should be dynamically generated but only take up a limited number of rows
        non_bsdf_mat_names = set()
        multi_bsdf_mat_names = set()
        current_props = set()
        current_copyonlys = set()
        non_node_mat_names = set()
        non_world_scale_names = set()
        empty_material_slots = set()
        too_many_uvmaps = set()
        for obj in get_meshes_objects(context):
            if obj.name not in context.view_layer.objects:
                continue
            if obj.hide_get():
                continue
            for slot in obj.material_slots:
                if slot.material:
                    if (not (slot.material.node_tree)):
                        non_node_mat_names.add(slot.material.name)
                    else:
                        if not slot.material.use_nodes:
                            non_node_mat_names.add(slot.material.name)
                        if not any(node.type == "BSDF_PRINCIPLED" for node in slot.material.node_tree.nodes):
                            non_bsdf_mat_names.add(slot.material.name)
                        if len([node for node in slot.material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"]) > 1:
                            multi_bsdf_mat_names.add(slot.material.name)
                else:
                    if len(obj.material_slots) == 1:
                        empty_material_slots.add(obj.name)
            if len(obj.material_slots) == 0:
                empty_material_slots.add(obj.name)
            if any(dim != 1.0 for dim in obj.scale):
                non_world_scale_names.add(obj.name)
            if len(obj.data.uv_layers) > 6:
                too_many_uvmaps.add(obj.name)
            if 'generatePropBones' in obj and obj['generatePropBones']:
                current_props.add(obj.name)
            if 'bakeCopyOnly' in obj and obj['bakeCopyOnly']:
                current_copyonlys.add(obj.name)

        col.label(text=t('BakePanel.autodetectlabel'))
        row = col.row(align=True)
        row.operator(Bake.BakePresetAll.bl_idname, icon="SHADERFX")
        row = col.row(align=True)
        row.operator(Bake.BakePresetDesktop.bl_idname, icon="ANTIALIASED")
        row.operator(Bake.BakePresetQuest.bl_idname, icon="ALIASED")
        row = col.row(align=True)
        row.operator(Bake.BakePresetSecondlife.bl_idname, icon="VIEW_PAN")
        row = col.row(align=True)
        row.operator(Bake.BakePresetGmod.bl_idname, icon="EVENT_G")
        row.operator(Bake.BakePresetGmodPhong.bl_idname, icon="EVENT_G")
        col.separator()
        row = col.row()
        col.label(text="Material Groupings")
        row = col.row()
        row.template_list("Material_Grouping_UL_List", "The_Mat_List", context.scene,
                          "bake_material_groups", context.scene, "bake_material_groups_index")
        row = col.row(align=True)
        row.operator(Material_Grouping_UL_List_Reload.bl_idname)
        col.separator()
        row = col.row()
        col.label(text="Platforms:")
        row = col.row()
        row.template_list("Bake_Platform_List", "The_List", context.scene,
                          "bake_platforms", context.scene, "bake_platform_index")
        row = col.row(align=True)
        row.operator(Bake_Platform_New.bl_idname)
        row.operator(Bake_Platform_Delete.bl_idname)
        col.separator()
        
        if context.scene.bake_platform_index >= 0 and context.scene.bake_platforms:
            item = context.scene.bake_platforms[context.scene.bake_platform_index]

            row = col.row(align=True)
            row.prop(item, 'name', expand=True)
            row = col.row(align=True)
            row.separator()
            row.prop(item, 'use_decimation', expand=True)
            if item.use_decimation:
                row = col.row(align=True)
                row.separator()
                row.prop(item, 'max_tris', expand=True)
            ### BEGIN ADVANCED PLATFORM OPTIONS
            col.separator()
            row = col.row(align=True)
            row.scale_y = 0.85
            if not context.scene.bake_show_advanced_platform_options:
                row.prop(context.scene, 'bake_show_advanced_platform_options', icon="ADD", emboss=True, expand=False, toggle=False, event=False)
            else:
                row.prop(context.scene, 'bake_show_advanced_platform_options', icon="REMOVE", emboss=True, expand=False, toggle=False, event=False)
                if item.use_decimation:
                    row = col.row(align=True)
                    row.separator()
                    row.prop(item, 'remove_doubles', expand=True)
                    row = col.row(align=True)
                    row.separator()
                    row.prop(item, 'preserve_seams', expand=True)
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_animation_weighting', expand=True)
                    if context.scene.bake_animation_weighting:
                        row = col.row(align=True)
                        row.separator()
                        row.prop(context.scene, 'bake_animation_weighting_factor', expand=True)
                        row = col.row(align=True)
                        row.separator()
                        row.prop(context.scene, 'bake_animation_weighting_include_shapekeys', expand=True)
                row = col.row(align=True)
                row.prop(item, 'use_physmodel', expand=True)
                if item.use_physmodel:
                    row = col.row(align=True)
                    row.prop(item, 'physmodel_lod', expand=True)
                row = col.row(align=True)
                row.prop(item, 'use_lods', expand=True)
                if item.use_lods:
                    row = col.row(align=True)
                    row.prop(item, 'lods', expand=True)
                    row = col.row(align=True)
                    row.operator(Bake_Lod_New.bl_idname)
                    row.operator(Bake_Lod_Delete.bl_idname)
                row = col.row(align=True)
                row.prop(item, 'merge_twistbones', expand=True)
                row = col.row(align=True)
                row.prop(item, 'prop_bone_handling')
                row = col.row(align=True)
                row.operator(Bake.BakeAddProp.bl_idname)
                row.operator(Bake.BakeRemoveProp.bl_idname)
                if current_props:
                    row = col.row(align=True)
                    row.separator()
                    row.label(text="Current props:")
                    for name in current_props:
                        row = col.row(align=True)
                        row.separator()
                        row.label(text=name, icon="OBJECT_DATA")
                row = col.row(align=True)
                row.prop(item, 'copy_only_handling')
                row = col.row(align=True)
                row.operator(Bake.BakeAddCopyOnly.bl_idname)
                row.operator(Bake.BakeRemoveCopyOnly.bl_idname)
                if current_copyonlys:
                    row = col.row(align=True)
                    row.separator()
                    row.label(text="Current 'Copy Only's:")
                    for name in current_copyonlys:
                        row = col.row(align=True)
                        row.separator()
                        row.label(text=name, icon="OBJECT_DATA")

                row = col.row(align=True)
                row.prop(item, 'phong_setup', expand=True)
                row = col.row(align=True)
                row.prop(item, 'specular_setup', expand=True)
                if item.specular_setup:
                    row = col.row(align=True)
                    row.prop(item, 'specular_alpha_pack', expand=True)
                    row = col.row(align=True)
                    row.prop(item, 'specular_smoothness_overlay', expand=True)
                if context.scene.bake_pass_diffuse and context.scene.bake_pass_emit:
                    row = col.row(align=True)
                    row.prop(item, "diffuse_emit_overlay", expand=True)
                if context.scene.bake_pass_diffuse and context.scene.bake_pass_ao:
                    row = col.row(align=True)
                    row.prop(item, "diffuse_premultiply_ao", expand=True)
                    if item.diffuse_premultiply_ao:
                        row = col.row(align=True)
                        row.separator()
                        row.prop(item, 'diffuse_premultiply_opacity', expand=True)
                    row = col.row(align=True)
                    row.prop(item, "smoothness_premultiply_ao", expand=True)
                    if item.smoothness_premultiply_ao:
                        row = col.row(align=True)
                        row.separator()
                        row.prop(item, 'smoothness_premultiply_opacity', expand=True)
                if context.scene.bake_pass_diffuse:
                    if bpy.app.version >= (2, 92, 0):
                        row = col.row(align=True)
                        row.prop(item, 'diffuse_vertex_colors', expand=True)
                if context.scene.bake_pass_diffuse and (context.scene.bake_pass_smoothness or context.scene.bake_pass_alpha) and not item.diffuse_vertex_colors:
                    row = col.row(align=True)
                    row.label(text="Diffuse Alpha:")
                    row.prop(item, 'diffuse_alpha_pack', expand=True)
                    if (item.diffuse_alpha_pack == "TRANSPARENCY") and not context.scene.bake_pass_alpha:
                        col.label(text=t('BakePanel.transparencywarning'), icon="INFO")
                    elif (item.diffuse_alpha_pack == "SMOOTHNESS") and not context.scene.bake_pass_smoothness:
                        col.label(text=t('BakePanel.smoothnesswarning'), icon="INFO")
                if context.scene.bake_pass_normal and (item.specular_setup or item.phong_setup):
                    row = col.row(align=True)
                    row.label(text="Normal Alpha:")
                    row.prop(item, 'normal_alpha_pack', expand=True)
                if context.scene.bake_pass_normal:
                    row = col.row(align=True)
                    row.prop(item, 'normal_invert_g', expand=True)
                if context.scene.bake_pass_metallic and context.scene.bake_pass_smoothness and not item.specular_setup and not item.phong_setup:
                    row = col.row(align=True)
                    row.label(text="Metallic Alpha:")
                    row.prop(item, 'metallic_alpha_pack', expand=True)
                    if item.diffuse_alpha_pack == "SMOOTHNESS" and item.metallic_alpha_pack == "SMOOTHNESS":
                        col.label(text=t('BakePanel.doublepackwarning'), icon="INFO")
                if context.scene.bake_pass_metallic and context.scene.bake_pass_ao:
                    row = col.row(align=True)
                    row.prop(item, 'metallic_pack_ao', expand=True)
                row = col.row(align=True)
                row.label(text="Bone Conversion:")
                row = col.row(align=True)
                row.separator()
                row.prop(item, 'translate_bone_names')
                row = col.row(align=True)
                row.separator()
                row.prop(item, 'export_format')
                row = col.row(align=True)
                row.separator()
                row.prop(item, 'image_export_format')
        # END ADVANCED PLATFORM OPTIONS

        if context.scene.bake_platforms:
            col.separator()
            col.label(text=t('BakePanel.generaloptionslabel'))
            row = col.row(align=True)
            row.prop(context.scene, 'bake_resolution', expand=True)
            row = col.row(align=True)
            row.prop(context.scene, 'bake_ignore_hidden', expand=True)
            row = col.row(align=True)
            row.prop(context.scene, 'bake_generate_uvmap', expand=True)
            if context.scene.bake_generate_uvmap:
                row = col.row(align=True)
                row.separator()
                row.prop(context.scene, 'bake_prioritize_face', expand=True)
                if context.scene.bake_prioritize_face:
                    armature = get_armature(context)
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_face_scale', expand=True)

                row = col.row(align=True)
                row.separator()
                if (not context.scene.bake_pass_ao) and (not any(plat.use_decimation for plat in context.scene.bake_platforms)) and (not context.scene.bake_pass_normal):
                    row.prop(context.scene, 'bake_optimize_solid_materials', expand=True)
                    row = col.row(align=True)
                row.separator()
                row.label(text=t('BakePanel.overlapfixlabel'))
                row.prop(context.scene, 'bake_uv_overlap_correction', expand=True)
                if context.scene.bake_uv_overlap_correction == "REPROJECT":
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_unwrap_angle', expand=True)
                if 'uvpm3_props' in context.scene or 'uvpm2_props' in context.scene:
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'uvp_lock_islands', expand=True)
            row = col.row(align=True)
            row.scale_y = 0.85
            if not context.scene.bake_show_advanced_general_options:
                row.prop(context.scene, 'bake_show_advanced_general_options', icon="ADD", emboss=True, expand=False, toggle=False, event=False)
            else:
                row.prop(context.scene, 'bake_show_advanced_general_options', icon="REMOVE", emboss=True, expand=False, toggle=False, event=False)
                row = col.row(align=True)
                row.prop(context.scene, 'bake_sharpen', expand=True)
                row = col.row(align=True)
                row.prop(context.scene, 'bake_denoise', expand=True)
                row = col.row(align=True)
                row.prop(context.scene, 'bake_cleanup_shapekeys', expand=True)
                row = col.row(align=True)
                row.prop(context.scene, 'bake_apply_keys', expand=True)
                col.separator()
                row = col.row(align=True)
                col.label(text=t('BakePanel.bakepasseslabel'))
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_diffuse', expand=True)
                if context.scene.bake_pass_diffuse:
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_diffuse_indirect', expand=True)
                    if context.scene.bake_diffuse_indirect:
                        row = col.row(align=True)
                        row.separator()
                        row.prop(context.scene, 'bake_diffuse_indirect_opacity', expand=True)
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_normal', expand=True)
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_smoothness', expand=True)
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_ao', expand=True)
                # TODO: warning in UI if you don't have any AO keys
                if context.scene.bake_pass_ao:
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_illuminate_eyes', expand=True)
                    if context.scene.bake_illuminate_eyes:
                        multires_obj_names = []
                        for obj in get_meshes_objects(context):
                            if obj.name not in context.view_layer.objects:
                                continue
                            if obj.hide_get():
                                continue
                            if any(mod.type == "MULTIRES" for mod in obj.modifiers):
                                multires_obj_names.add(obj.name)

                        if multires_obj_names:
                            row = col.row(align=True)
                            row.separator()
                            row.label(text="One or more of your objects are using Multires.", icon="ERROR")
                            row = col.row(align=True)
                            row.separator()
                            row.label(text="This has issues excluding the eyes, try adding")
                            row = col.row(align=True)
                            row.separator()
                            row.label(text="'ambient occlusion' shape keys instead.")

                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_alpha', expand=True)
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_metallic', expand=True)
                col.separator()

                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_emit', expand=True)
                if context.scene.bake_pass_emit:
                    row = col.row(align=True)
                    row.separator()
                    row.prop(context.scene, 'bake_emit_indirect', expand=True)
                    if context.scene.bake_emit_indirect:
                        row = col.row(align=True)
                        row.separator()
                        row.prop(context.scene, 'bake_emit_exclude_eyes', expand=True)

                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_displacement', expand=True)
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'bake_pass_detail', expand=True)

                row = col.row(align=True)
        ### END ADVANCED GENERAL OPTIONS
        else: # if not bake_platforms:
            row = col.row(align=True)
            row.label(text="To get started, press 'Autodetect All' above.", icon="INFO")
            row = col.row(align=True)
            row.label(text="Then if the settings look right, press 'Copy and Bake'.", icon="BLANK1")

        col.separator()
        col.separator()
        if context.preferences.addons['cycles'].preferences.compute_device_type == 'NONE' and context.scene.bake_device == 'GPU':
            row = col.row(align=True)
            row.label(text="No render device configured in Blender settings. Bake will use CPU", icon="INFO")
            row = col.row(align=True)
            row.operator(Open_GPU_Settings.bl_idname, icon="SETTINGS")
        if not addon_utils.check("render_auto_tile_size")[1] and bpy.app.version <= (2, 93):
            row = col.row(align=True)
            row.label(text="Enabling \"Auto Tile Size\" plugin reccomended!", icon="INFO")
        row = col.row(align=True)
        row.prop(context.scene, 'bake_device', expand=True)

        # Bake button
        row = col.row(align=True)
        row.operator(Bake.BakeButton.bl_idname, icon='RENDER_STILL')
        row = col.row(align=True)
        row.prop(context.scene, 'bake_use_draft_quality')

        # Show warnings
        if non_node_mat_names:
            row = col.row(align=True)
            row.label(text="The following materials do not use nodes!", icon="ERROR")
            row = col.row(align=True)
            row.label(text="Ensure they have Use Nodes checked in their properties or Bake will not run.", icon="BLANK1")
            for name in non_node_mat_names:
                row = col.row(align=True)
                row.label(text=name, icon="MATERIAL")
        if non_bsdf_mat_names:
            row = col.row(align=True)
            row.label(text="The following materials do not use Principled BSDF!", icon="INFO")
            row = col.row(align=True)
            row.label(text="Bake may have unexpected results.", icon="BLANK1")
            for name in non_bsdf_mat_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="MATERIAL")
        if multi_bsdf_mat_names:
            row = col.row(align=True)
            row.label(text="The following materials have multiple Principled BSDF!", icon="INFO")
            row = col.row(align=True)
            row.label(text="Bake may have unexpected results.", icon="BLANK1")
            for name in multi_bsdf_mat_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="MATERIAL")
        if empty_material_slots:
            row = col.row(align=True)
            row.label(text="The following objects have no material.", icon="INFO")
            row = col.row(align=True)
            row.label(text="Please assign one before continuing.", icon="BLANK1")
            for name in empty_material_slots:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="OBJECT_DATA")
        if non_world_scale_names:
            row = col.row(align=True)
            row.label(text="The following objects do not have scale applied", icon="INFO")
            row = col.row(align=True)
            row.label(text="The resulting islands will be inversely scaled.", icon="BLANK1")
            for name in non_world_scale_names:
                row = col.row(align=True)
                row.separator()
                row.label(text=name + ": " + "{:.1f}".format(1.0/bpy.data.objects[name].scale[0]) + "x", icon="OBJECT_DATA")
        if too_many_uvmaps:
            row = col.row(align=True)
            row.label(text="The following objects have too many UVMaps!", icon="ERROR")
            row = col.row(align=True)
            row.label(text="Bake will likely fail, you can have at most 6 maps.", icon="BLANK1")
            for name in too_many_uvmaps:
                row = col.row(align=True)
                row.separator()
                row.label(text=name + ": " + "{}".format(len(bpy.data.objects[name].data.uv_layers)), icon="OBJECT_DATA")


# -------------------------------------------------------------------
# User Interface
# -------------------------------------------------------------------

@wrapper_registry
class FT_Shapes_UL(Panel):
    bl_label = "Face Tracking Generation"
    bl_idname = "FT Shapes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tuxedo"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        ft_mesh = scene.ft_mesh

        #Start Layout
        col = layout.column()

        #Mesh Selection
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(context.scene, 'ft_mesh', icon='MESH_DATA')
        col.separator()
        row = col.row(align=True)

        #Viseme Selection
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.1
        row.label(text="Create from Visemes:", icon='SHADERFX')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_aa', icon='SHAPEKEY_DATA')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_ch', icon='SHAPEKEY_DATA')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_oh', icon='SHAPEKEY_DATA')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_blink', icon='SHAPEKEY_DATA')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_smile', icon='SHAPEKEY_DATA')
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(scene, 'ft_frown', icon='SHAPEKEY_DATA')

        #Check mesh selections
        if ft_mesh and has_shapekeys(bpy.data.objects[ft_mesh]):
            #Info

            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text='Select shape keys to create FT shape keys.', icon='INFO')
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text='Specifying above will attempt to create them for you.', icon='INFO')
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text='Currently requires rotation to be applied.', icon='INFO')
            col.separator()

            #Start Box
            box = layout.box()
            col = box.column(align=True)

            #Start List of Shapekeys from VRCFT labels list
            for i in range(len(SRanipal_Labels)):
                row = col.row(align=True)
                row.scale_y = 1.1
                row.label(text = SRanipal_Labels[i] + ":")
                row.prop(scene, 'ft_shapekey_' + str(i), icon='SHAPEKEY_DATA')
                row.prop(scene, 'ft_shapekey_enable_' + str(i), icon='CHECKMARK')
                # Determine whether this key is already going to be auto-populated
                label = SRanipal_Labels[i]
                basis = get_shapekeys_ft(self, context)[0][0]
                if any(string in label for string in ['Blink', 'squeeze', 'Wide']):
                    if context.scene.ft_blink != basis:
                        row.enabled = False
                if any(string in label for string in ['Jaw']):
                    if context.scene.ft_aa != basis:
                        row.enabled = False
                if any(string in label for string in ['Upper_Up', 'Lower_Down', 'Upper_Left', 'Lower_Right', 'Upper_Right', 'Lower_Left', 'Inside', 'Pout', 'Mouth_Left', 'Mouth_Right', 'Smile', 'Sad']):
                    if (context.scene.ft_ch != basis and
                        context.scene.ft_oh != basis):
                        row.enabled = False
                if any(string in label for string in ['Smile']):
                    if context.scene.ft_smile != basis:
                        row.enabled = False
                if any(string in label for string in ['Sad']):
                    if context.scene.ft_frown != basis:
                        row.enabled = False

            row = layout.row()
            row.operator("ft.create_shapekeys", icon='MESH_MONKEY')
        else:
            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text='Select the mesh with face shape keys.', icon='INFO')
            col.separator()
