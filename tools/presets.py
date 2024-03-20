# GPL Licence
import bpy
from ..class_register import wrapper_registry
from .translate import t

@wrapper_registry
class AutoDecimatePresetGood(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_good'
    bl_label = t('DecimationPanel.preset.good.label')
    bl_description = t('DecimationPanel.preset.good.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 70000
        return {'FINISHED'}

@wrapper_registry
class AutoDecimatePresetExcellent(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_excellent'
    bl_label = t('DecimationPanel.preset.excellent.label')
    bl_description = t('DecimationPanel.preset.excellent.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 32000
        return {'FINISHED'}

@wrapper_registry
class AutoDecimatePresetQuest(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_quest'
    bl_label = t('DecimationPanel.preset.quest.label')
    bl_description = t('DecimationPanel.preset.quest.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 5000
        return {'FINISHED'}