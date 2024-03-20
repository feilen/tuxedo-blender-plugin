import bpy

from ..tools.core import get_armature
from ..tools.translate import t
from ..ui import register_ui_tab

#Making a class that looks like a blender panel just to use it to cut the code up for tabs
#This is kinda a bad look but at least it makes the UI nice! - @989onan

@register_ui_tab
class Bake_PT_general_options:
    bl_label = t('BakePanel.generaloptions.label')
    bl_enum = "GENERAL"
    bl_description = t('BakePanel.generaloptions.desc')
    icon = "INFO"
    
    def poll(cls, context):
        return context.scene.bake_platforms
    
    def draw_panel(main_panel, context, col):
        row = col.row(align=True)
        row.prop(context.scene, 'bake_sharpen', expand=True)
        row = col.row(align=True)
        row.prop(context.scene, 'bake_denoise', expand=True)
        row = col.row(align=True)
        row.prop(context.scene, 'bake_cleanup_shapekeys', expand=True)
        row = col.row(align=True)
        row.prop(context.scene, 'bake_apply_keys', expand=True)
        if context.scene.bake_platforms:
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
                row.label(text=t('BakePanel.overlapfix.label'))
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