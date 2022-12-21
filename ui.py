

@register_wrap
class ManualPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_manual_v3'
    bl_label = t('ManualPanel.label')
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        button_height = 1

        col = box.column(align=True)
        col.separator()
        add_button_with_small_button(col, Armature_manual.GenerateTwistBones.bl_idname, 'OUTLINER_DATA_ARMATURE',
                                     Armature_manual.TwistTutorialButton.bl_idname, 'QUESTION', scale=button_height)
        row = col.row(align=True)
        row.scale_y = button_height
        row.prop(context.scene, 'generate_twistbones_upper')

        row = col.row(align=True)
        row.prop(context.scene, 'decimation_animation_weighting', expand=True)
        if context.scene.decimation_animation_weighting: # and context.scene.decimation_mode != "LOOP":
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'decimation_animation_weighting_factor', expand=True)
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'decimation_animation_weighting_include_shapekeys', expand=True)
            col.separator()
            row = col.row(align=True)
            row.scale_y = button_height
            row.operator(Armature_manual.OptimizeStaticShapekeys.bl_idname, icon='MESH_DATA')
