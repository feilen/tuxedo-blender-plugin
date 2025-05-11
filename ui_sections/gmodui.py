import bpy
import addon_utils

from ..properties import get_steam_library
from ..tools.translate import t

from bpy.types import UIList

from ..class_register import wrapper_registry
from ..ui import register_ui_tab

button_height = 1

@wrapper_registry
class Objects_Gmod_Visibility_UL_List(UIList):
    bl_label = ""
    
    def filter_items(self, context, data, propname):
        
        ordered = []
        objects = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(objects)
        
        
        for k,i in enumerate(objects):
            filtered[k] &= self.bitflag_filter_item if i.type == "MESH" else ~self.bitflag_filter_item
            ordered.append(k)
            #print(filtered[k])
        ret = (filtered,ordered)
        return ret
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = "OBJECT_DATAMODE"
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            col = row.column()
            col.label(text=item.name, icon = custom_icon)
            col = row.column()
            col.prop(item, "gmod_is_toggleable")
            col = row.column()
            col.prop(item, "gmod_shown_by_default")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

#Making a class that looks like a blender panel just to use it to cut the code up for tabs
#This is kinda a bad look but at least it makes the UI nice! - @989onan

@register_ui_tab
class GmodPanel:
    bl_label = t('BakePanel.gmod_options.label')
    bl_enum = "GMOD"
    bl_description = t('BakePanel.gmod_options.label')
    icon = "EVENT_G"
    
    
    def poll(cls, context):
        try:
            return context.scene.bake_platforms[context.scene.bake_platform_index].export_format == "GMOD"
        except:
            return False
    
    def draw_panel(main_panel: bpy.types.Panel, context: bpy.types.Context, col: bpy.types.UILayout):
        
        
        item = context.scene.bake_platforms[context.scene.bake_platform_index]
        if get_steam_library(None):
            row = col.row(align=True)
            box = row.box()
            box.label(text=get_steam_library(None), icon="EVENT_G")
        else:
            row = col.row(align=True)
            row.label(text=t('GmodPanel.gmod_not_found'), icon="ERROR")
        row = col.row(align=True)
        row.prop(item, "gmod_model_name", expand=True)
        row.prop(item, "gmod_male", expand=True)
        
        col.label(text=t('GmodPanel.gmod_visibility.list_label'))
        row = col.row()
        #row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)
        row.template_list("Objects_Gmod_Visibility_UL_List", "The_Gmod_Visibility_List", context.scene, "objects", context.scene, "gmod_toggle_list_index", rows=10)
        
        
        
        
        