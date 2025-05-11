import collections
import traceback
import bpy
import addon_utils

from . import bake as Bake
from .tools.translate import t
from .tools.tools import GenerateTwistBones, TwistTutorialButton, SmartDecimation, RepairShapekeys, FitClothes, SRanipal_Labels
from .tools import tools
from .tools import gmod_tools
from .tools.presets import AutoDecimatePresetGood, AutoDecimatePresetQuest, AutoDecimatePresetExcellent
from .tools import core

#to make sure all of our ui section tabs get registered, otherwise the @ marker doesn't work on them - @989onan
from .ui_sections import *

from .class_register import wrapper_registry

from bpy.types import UIList, Operator, Panel
from bpy_extras.io_utils import ImportHelper
from .globals import UITab

button_height = 1


class Open_GPU_Settings(Operator):
    bl_idname = "tuxedo_bake.open_gpu_settings"
    bl_label = "Open GPU Settings (Top of the page)"

    def execute(self, context):
        bpy.ops.screen.userpref_show()
        context.preferences.active_section = 'SYSTEM'

        return{'FINISHED'}

class Choose_Steam_Library(Operator, ImportHelper):
    bl_idname = "tuxedo_bake.choose_steam_library"
    bl_label = "Choose Steam Library"

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    @classmethod
    def poll(cls, context):
        bake_platforms = context.scene.bake_platforms
        index = context.scene.bake_platform_index

        return bake_platforms[index].export_format == "GMOD"
    def execute(self, context):
        context.scene.bake_steam_library = self.directory
        return{'FINISHED'}

@wrapper_registry
class ErrorNoSource_OT_Tuxedo(Operator):
    bl_idname = "tuxedo_bake.nosource"
    bl_label = "INSTALL SOURCE"
    bl_options = {'INTERNAL'}
    bl_icon = "ERROR"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        row = col.row(align=True)
        row.label(text=t('BakePanel.nosource_1'))
        row = col.row(align=True)
        row.label(text=t('BakePanel.nosource_2'))
        row = col.row(align=True)
        row.label(text=t('BakePanel.nosource_3'))
        

@wrapper_registry
class Bake_Platform_List(UIList):
    bl_label = ""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # TODO:? We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


@wrapper_registry
class Material_Grouping_UL_List(UIList):
    bl_label = ""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'MATERIAL'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            col = row.column()
            col.label(text=item.name, icon = custom_icon)
            col = row.column()
            col.prop(item, "group", text=t('BakePanel.material_grouping.label'))
            #col = row.column()
            #col.prop(item, "include", text="include")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

@wrapper_registry
class Material_Grouping_UL_List_Reload(Operator):
    bl_idname = "tuxedo_bake.materials_reload"
    bl_label = t('reloadmats')

    def execute(self, context):
        core.materials_list_update(context)

        return{'FINISHED'}

@wrapper_registry
class Bake_Platform_New(Operator):
    bl_idname = "tuxedo_bake.platform_add"
    bl_label = t('add')

    def execute(self, context):
        context.scene.bake_platforms.add()

        return{'FINISHED'}

@wrapper_registry
class Bake_Platform_Delete(Operator):
    bl_idname = "tuxedo_bake.platform_remove"
    bl_label = t('delete')

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
    bl_label = t('add')

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
    bl_label = t('delete')

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
class ToolPanel(Panel):
    bl_label = t('ToolPanel.tools.label')
    bl_idname = 'VIEW3D_PT_tuxtools'
    bl_category = 'Tuxedo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_order = 1

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
        row.label(text=t('Tools.attach_clothes'))

        if len(context.view_layer.objects.selected) <= 1 or not context.view_layer.objects.active or 'Armature' not in context.view_layer.objects.active.modifiers:
            row = col.row(align=True)
            row.scale_y = 1.05
            col.label(text=t('Tools.attach_clothes_err1_1'), icon='INFO')
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text=t('Tools.attach_clothes_err1_2'), icon='BLANK1')
            row = col.row(align=True)
            row.scale_y = 0.75
            row.label(text=t('Tools.attach_clothes_err1_3'), icon='BLANK1')
            return

        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator(FitClothes.bl_idname, icon='MOD_CLOTH')

uitabs: dict[str, UITab] = {}
choices: list[UITab] = []

def register_ui_tab(cls: UITab):
    print("registering a ui tab with enum "+cls.bl_enum)
    choices.append(cls)
    uitabs[cls.bl_enum] = cls
    return cls

def tab_enums(self, context: bpy.types.Context) -> collections.abc.Iterable[
        tuple[str, str, str]
        | tuple[str, str, str, int]
        | tuple[str, str, str, str, int]
        | None
    ]:
    options = []
    for k,cls in enumerate(choices):
        if cls.poll(cls, context):
            options.append((cls.bl_enum,"",cls.bl_description, cls.icon, k))
        else:
            options.append((cls.bl_enum,"",cls.bl_description, "X", k))
    return options
    

    

@wrapper_registry
class BakePanel(Panel):
    bl_order = 2
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

        
        
        self.non_bsdf_mat_names = set()
        self.multi_bsdf_mat_names = set()
        self.current_props = set()
        self.current_copyonlys = set()
        self.non_node_mat_names = set()
        self.non_world_scale_names = set()
        self.empty_material_slots = set()
        self.too_many_uvmaps = set()
        self.has_errors = False
        
        for obj in core.get_meshes_objects(context):
            if obj.name not in context.view_layer.objects:
                continue
            if obj.hide_get():
                continue
            for slot in obj.material_slots:
                if slot.material:
                    if (not (slot.material.node_tree)):
                        self.non_node_mat_names.add(slot.material.name)
                    else:
                        if not slot.material.use_nodes:
                            self.non_node_mat_names.add(slot.material.name)
                        if not any(node.type == "BSDF_PRINCIPLED" for node in slot.material.node_tree.nodes):
                            self.non_bsdf_mat_names.add(slot.material.name)
                        if len([node for node in slot.material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"]) > 1:
                            self.multi_bsdf_mat_names.add(slot.material.name)
                else:
                    if len(obj.material_slots) == 1:
                        self.empty_material_slots.add(obj.name)
            if len(obj.material_slots) == 0:
                self.empty_material_slots.add(obj.name)
            if any(dim != 1.0 for dim in obj.scale):
                self.non_world_scale_names.add(obj.name)
            if len(obj.data.uv_layers) > 6:
                self.too_many_uvmaps.add(obj.name)
            if 'generatePropBones' in obj and obj['generatePropBones']:
                self.current_props.add(obj.name)
            if 'bakeCopyOnly' in obj and obj['bakeCopyOnly']:
                self.current_copyonlys.add(obj.name)
        if context.scene.bake_pass_ao:
            if context.scene.bake_illuminate_eyes:
                self.multires_obj_names = []
                for obj in core.get_meshes_objects(context):
                    if obj.name not in context.view_layer.objects:
                        continue
                    if obj.hide_get():
                        continue
                    if any(mod.type == "MULTIRES" for mod in obj.modifiers):
                        self.multires_obj_names.add(obj.name)

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
        col.label(text=t('BakePanel.material_groupings.label'))
        row = col.row()
        row.template_list("Material_Grouping_UL_List", "The_Mat_List", context.scene,
                          "bake_material_groups", context.scene, "bake_material_groups_index")
        row = col.row(align=True)
        row.operator(Material_Grouping_UL_List_Reload.bl_idname)
        col.separator()
        row = col.row()
        col.label(text=t('BakePanel.platforms.label'))
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

        
        if context.scene.bake_platforms:
            row = col.row(align=True)
            #display the different tabs
            row.column(align=True).prop(context.scene, "section_enum", icon_only=True, expand=True)
            box = row.box()
            #display the current UI tab
            
            try:
                
                current = uitabs[context.scene.section_enum]
                section = box.column()
                section.label(text=current.bl_label)
                
                if current.poll(current,context):
                    current.draw_panel(self, context, section)
                else:
                    row = section.row(align=True)
                    section.label(text=t('BakePanel.feature_set_unavailable'), icon='INFO')
            except Exception as e:
                section = box.column(heading ="ERROR")
                section.label(text=t('BakePanel.panel_render_error'), icon='ERROR')
                row = section.row(align=True)
                row.label(text=traceback.format_exc())
                row = section.row(align=True)
                row.label(text=f"enums: {tab_enums(self,context)}")
                
            #bake warnings
            if context.preferences.addons['cycles'].preferences.compute_device_type == 'NONE' and context.scene.bake_device == 'GPU':
                row = col.row(align=True)
                row.label(text=t('BakePanel.warn_using_cpu'), icon="INFO")
                row = col.row(align=True)
            import importlib.util
            if importlib.util.find_spec("cycles.properties") is not None:
                cycles_addon: bpy.types.Addon = context.preferences.addons["cycles"].preferences
                cycles_addon.layout = col
                cycles_addon.draw(context)
            else:
                row = col.row(align=True)
                row.label(text=t('BakePanel.warn_no_cycles_addon'), icon="INFO")
                row = col.row(align=True)
                    
            if not addon_utils.check("render_auto_tile_size")[1] and bpy.app.version <= (2, 93):
                row = col.row(align=True)
                row.label(text=t('BakePanel.warn_auto_tile_size'), icon="INFO")
            row = col.row(align=True)
            row.prop(context.scene, 'bake_device', expand=True)
            
            # Bake button
            if self.has_errors:
                row = col.row(align=True)
                row.label(text=t('BakePanel.warning_errors'), icon="ERROR")
            row = col.row(align=True)
            row.operator(Bake.BakeButton.bl_idname, icon='RENDER_STILL')
            row = col.row(align=True)
            row.prop(context.scene, 'bake_use_draft_quality')
        else:
            row = col.row(align=True)
            row.label(text=t('BakePanel.start_1'), icon="INFO")
            row = col.row(align=True)
            row.label(text=t('BakePanel.start_2'), icon="BLANK1")
# -------------------------------------------------------------------
# User Interface
# -------------------------------------------------------------------

@wrapper_registry
class FT_Shapes_UL(Panel):
    bl_order = 3
    bl_label = t('FT.shapes_panel_label')
    bl_idname = "FT_Shapes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tuxedo"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        ft_mesh = scene.ft_mesh
        if ft_mesh == "NONE":
            ft_mesh = None

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
        row.label(text=t('FT.create_from_visemes'), icon='SHADERFX')
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
        if ft_mesh and core.has_shapekeys(bpy.data.objects[ft_mesh]):
            #Info

            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text=t('FT.select_shapes_1'), icon='INFO')
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text=t('FT.select_shapes_2'), icon='INFO')
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            row.label(text=t('FT.select_shapes_3'), icon='INFO')
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
                basis = core.get_shapekeys_ft(self, context)[0][0]
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
            row.label(text=t('FT.mesh_missing'), icon='INFO')
            col.separator()
