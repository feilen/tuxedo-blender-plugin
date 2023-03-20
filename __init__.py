import bpy
from .bake import BakeAddCopyOnly, BakeAddProp, BakeButton, BakePresetAll, BakePresetDesktop, BakePresetGmod, BakePresetGmodPhong, BakePresetQuest, BakePresetSecondlife, BakeRemoveCopyOnly, BakeRemoveProp, BakeTutorialButton
from .ui import BakePanel, Bake_Lod_Delete, Bake_Lod_New, Bake_Platform_Delete, Bake_Platform_List, Bake_Platform_New, Choose_Steam_Library, Open_GPU_Settings, ToolPanel, SmartDecimation
from .tools import ConvertToSecondlifeButton, FitClothes, GenerateTwistBones, OptimizeStaticShapekeys, TwistTutorialButton, AutoDecimatePresetGood, AutoDecimatePresetExcellent, AutoDecimatePresetQuest
from .properties import register_properties

bl_info = {
    'name': 'Tuxedo Blender Plugin',
    'category': '3D View',
    'author': 'Feilen',
    'location': 'View 3D > Tool Shelf > Tuxedo',
    'description': 'A variety of tools to improve and optimize models for use in a variety of game engines.',
    'version': (0, 1, 0),
    'blender': (2, 80, 0),
    'wiki_url': 'https://github.com/feilen/tuxedo-blender-plugin',
    'tracker_url': 'https://github.com/feilen/tuxedo-blender-plugin/issues',
    'warning': '',
}

def register():
    # Auto decimate fns
    bpy.utils.register_class(AutoDecimatePresetGood)
    bpy.utils.register_class(AutoDecimatePresetExcellent)
    bpy.utils.register_class(AutoDecimatePresetQuest)

    # Bake fns
    bpy.utils.register_class(BakeAddCopyOnly)
    bpy.utils.register_class(BakeAddProp)
    bpy.utils.register_class(BakeButton)
    bpy.utils.register_class(BakePresetAll)
    bpy.utils.register_class(BakePresetDesktop)
    bpy.utils.register_class(BakePresetGmod)
    bpy.utils.register_class(BakePresetGmodPhong)
    bpy.utils.register_class(BakePresetQuest)
    bpy.utils.register_class(BakePresetSecondlife)
    bpy.utils.register_class(BakeRemoveCopyOnly)
    bpy.utils.register_class(BakeRemoveProp)
    bpy.utils.register_class(BakeTutorialButton)

    # UI
    bpy.utils.register_class(ToolPanel)
    bpy.utils.register_class(BakePanel)
    bpy.utils.register_class(Bake_Lod_Delete)
    bpy.utils.register_class(Bake_Lod_New)
    bpy.utils.register_class(Bake_Platform_Delete)
    bpy.utils.register_class(Bake_Platform_List)
    bpy.utils.register_class(Bake_Platform_New)
    bpy.utils.register_class(Choose_Steam_Library)
    bpy.utils.register_class(Open_GPU_Settings)

    # Utilities
    bpy.utils.register_class(ConvertToSecondlifeButton)
    bpy.utils.register_class(FitClothes)
    bpy.utils.register_class(GenerateTwistBones)
    bpy.utils.register_class(OptimizeStaticShapekeys)
    bpy.utils.register_class(TwistTutorialButton)
    bpy.utils.register_class(SmartDecimation)

    # Properties
    register_properties()

def unregister():
    # Autodecimate fns
    bpy.utils.register_class(AutoDecimatePresetGood)
    bpy.utils.register_class(AutoDecimatePresetExcellent)
    bpy.utils.register_class(AutoDecimatePresetQuest)

    # Bake fns
    bpy.utils.unregister_class(BakeAddCopyOnly)
    bpy.utils.unregister_class(BakeAddProp)
    bpy.utils.unregister_class(BakeButton)
    bpy.utils.unregister_class(BakePresetAll)
    bpy.utils.unregister_class(BakePresetDesktop)
    bpy.utils.unregister_class(BakePresetGmod)
    bpy.utils.unregister_class(BakePresetGmodPhong)
    bpy.utils.unregister_class(BakePresetQuest)
    bpy.utils.unregister_class(BakePresetSecondlife)
    bpy.utils.unregister_class(BakeRemoveCopyOnly)
    bpy.utils.unregister_class(BakeRemoveProp)
    bpy.utils.unregister_class(BakeTutorialButton)

    # UI
    bpy.utils.unregister_class(BakePanel)
    bpy.utils.unregister_class(Bake_Lod_Delete)
    bpy.utils.unregister_class(Bake_Lod_New)
    bpy.utils.unregister_class(Bake_Platform_Delete)
    bpy.utils.unregister_class(Bake_Platform_List)
    bpy.utils.unregister_class(Bake_Platform_New)
    bpy.utils.unregister_class(Choose_Steam_Library)
    bpy.utils.unregister_class(Open_GPU_Settings)
    bpy.utils.unregister_class(ToolPanel)

    # Utilities
    bpy.utils.unregister_class(ConvertToSecondlifeButton)
    bpy.utils.unregister_class(FitClothes)
    bpy.utils.unregister_class(GenerateTwistBones)
    bpy.utils.unregister_class(OptimizeStaticShapekeys)
    bpy.utils.unregister_class(TwistTutorialButton)
    bpy.utils.unregister_class(SmartDecimation)


if __name__ == '__main__':
    register()
