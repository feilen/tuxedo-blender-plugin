import typing
from bpy.utils.previews import ImagePreviewCollection
import importlib.util
mmd_tools_exist = importlib.util.find_spec("mmd_tools") is not None





#these get populated by init.
version = None
blender = None
icons_dict: typing.Type[ImagePreviewCollection]
icon_names = {
    "resonite":"RSN_Logomark_Color_1080.png",
    "vrchat":"VRC_Logo.png"
}


