import bpy
from .bake import BakeAddCopyOnly, BakeAddProp, BakeButton, BakePresetAll, BakePresetDesktop, BakePresetGmod, BakePresetGmodPhong, BakePresetQuest, BakePresetSecondlife, BakeRemoveCopyOnly, BakeRemoveProp, BakeTutorialButton
from .ui import BakePanel, Bake_Lod_Delete, Bake_Lod_New, Bake_Platform_Delete, Bake_Platform_List, Bake_Platform_New, Choose_Steam_Library, Open_GPU_Settings, ToolPanel, SmartDecimation, FT_Shapes_UL
from .tools import ConvertToSecondlifeButton, FitClothes, GenerateTwistBones, TwistTutorialButton, AutoDecimatePresetGood, AutoDecimatePresetExcellent, AutoDecimatePresetQuest, RepairShapekeys, ExportGmodPlayermodel, ConvertToValveButton, PoseToRest
from .tools import FT_OT_CreateShapeKeys, SRanipal_Labels
from .properties import register_properties
from bpy.types import Scene

classes = (
    # Auto decimate fns
    AutoDecimatePresetGood,
    AutoDecimatePresetExcellent,
    AutoDecimatePresetQuest,

    # Bake fns
    BakeAddCopyOnly,
    BakeAddProp,
    BakeButton,
    BakePresetAll,
    BakePresetDesktop,
    BakePresetGmod,
    BakePresetGmodPhong,
    BakePresetQuest,
    BakePresetSecondlife,
    BakeRemoveCopyOnly,
    BakeRemoveProp,
    BakeTutorialButton,

    # UI
    ToolPanel,
    BakePanel,
    Bake_Lod_Delete,
    Bake_Lod_New,
    Bake_Platform_Delete,
    Bake_Platform_List,
    Bake_Platform_New,
    Choose_Steam_Library,
    Open_GPU_Settings,

    # Utilities
    ConvertToSecondlifeButton,
    FitClothes,
    GenerateTwistBones,
    TwistTutorialButton,
    SmartDecimation,
    RepairShapekeys,
    ExportGmodPlayermodel,
    ConvertToValveButton,
    PoseToRest,

    # Face Tracking
    FT_OT_CreateShapeKeys,
    FT_Shapes_UL,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Properties
    register_properties()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for i, ft_shape in enumerate(SRanipal_Labels):
        delattr(Scene, "ft_shapekey_" + str(i))

    for i, ft_shape in enumerate(SRanipal_Labels):
        delattr(Scene, "ft_shapekey_enable_" + str(i))

if __name__ == '__main__':
    register()
