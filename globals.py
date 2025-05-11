import typing
from bpy.utils.previews import ImagePreviewCollection
import importlib.util
import bpy
mmd_tools_exist = importlib.util.find_spec("mmd_tools") is not None


class UITab():
    bl_enum: str
    bl_idname: str
    bl_label: str
    bl_description: str
    icon: str
    
    def poll(cls, context: bpy.types.Context):
        pass
    def draw_panel(main_panel: bpy.types.Panel, context: bpy.types.Context, col: bpy.types.UILayout):
        pass

blender = [4,4,5]

icons_dict: typing.Type[ImagePreviewCollection]
icon_names = {
    "resonite":"RSN_Logomark_Color_1080.png",
    "vrchat":"VRC_Logo.png"
}


