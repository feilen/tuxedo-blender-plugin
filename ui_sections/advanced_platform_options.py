import bpy

from .. import bake as Bake
from ..tools.translate import t
from .. import ui

from ..ui import register_ui_tab #need this for registering our class to the ui



#Making a class that looks like a blender panel just to use it to cut the code up for tabs
#This is kinda a bad look but at least it makes the UI nice! - @989onan
@register_ui_tab
class Bake_PT_advanced_platform_options:
    bl_label = t('BakePanel.advanced_platform_options.label')
    bl_enum = "ADVPLAT"
    bl_description = t('BakePanel.advanced_platform_options.desc')
    icon = "INFO"
    
    def poll(cls, context):
        try:
            return context.scene.bake_platforms[context.scene.bake_platform_index] != None
        except:
            return False
    
    def draw_panel(main_panel, context, col):
        item = context.scene.bake_platforms[context.scene.bake_platform_index]
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
            row.operator(ui.Bake_Lod_New.bl_idname)
            row.operator(ui.Bake_Lod_Delete.bl_idname)
        row = col.row(align=True)
        row.prop(item, 'merge_twistbones', expand=True)
        row = col.row(align=True)
        row.prop(item, 'prop_bone_handling')
        row = col.row(align=True)
        row.operator(Bake.BakeAddProp.bl_idname)
        row.operator(Bake.BakeRemoveProp.bl_idname)
        if main_panel.current_props:
            row = col.row(align=True)
            row.separator()
            row.label(text="Current props:")
            for name in main_panel.current_props:
                row = col.row(align=True)
                row.separator()
                row.label(text=name, icon="OBJECT_DATA")
        row = col.row(align=True)
        row.prop(item, 'copy_only_handling')
        row = col.row(align=True)
        row.operator(Bake.BakeAddCopyOnly.bl_idname)
        row.operator(Bake.BakeRemoveCopyOnly.bl_idname)
        if main_panel.current_copyonlys:
            row = col.row(align=True)
            row.separator()
            row.label(text="Current 'Copy Only's:")
            for name in main_panel.current_copyonlys:
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