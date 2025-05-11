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
    print("========= STARTING TUXEDO REGISTRY =========")
    order_classes()
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            try:
                print("registered class "+cls.bl_label)
            except Exception as e:
                print("tried to register class with no label.")
                print(e)
        except ValueError as e1:
            try:
                print("failed to register "+cls.bl_label)
                print(e1)
            except Exception as e2:
                print("tried to register class with no label.")
                print(e1)
                print(e2)

    classes.clear()

    globals.version = bl_info['version']
    globals.blender = bl_info['blender']
    # Properties
    register_properties()
    custom_icons()
    print("========= TUXEDO REGISTRY FINISHED =========")
    #needs to be after registering properties, because it accesses a property - @989onan
    print("========= READING STEAM REGISTRY KEYS FOR GMOD =========")
    
    try:
        import subprocess
        import sys
        batch_path = dirname(__file__)+"/assets/tools/readregistrysteamkey.bat"
        process = subprocess.Popen([batch_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        
        if out:
            print("found steam install, it is")
            print(out)
            libraryfolders = str(out.decode()).replace("b", "").strip().replace("\"","")[:-9]+"steamapps/libraryfolders.vdf"
            
            print("rooting around in your steam libraries for gmod...")
            f = open(libraryfolders, "r")
            library_path = ""
            for line in f.readlines():
                #print(line)
                if line.strip().startswith("\"path\""):
                    print("found a library")
                    print("previous library didn't have garry's mod")
                    library_path = line.strip().replace("\\\\", "/").replace("\"path\"", "").strip().replace("\"","")+"/"
                    print(library_path)
                else:
                    if line.strip().startswith("\"4000\""):
                        print("above library has garrys mod, setting to that.")
                        set_steam_library(library_path)
                        break
        else:
            print("could not find steam install! Please check your steam installation!")
    except Exception as e:
        print("Could not read steam libraries! Error below.")
        print(e)
    print("========= FINISHED READING STEAM REGISTRY KEYS FOR GMOD =========")



def custom_icons():
    import bpy.utils.previews
    globals.icons_dict = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "images", "icons")

    for icon,file in globals.icon_names.items():
        globals.icons_dict.load(icon, os.path.join(icons_dir, file), 'IMAGE')


def unregister():
    print("========= DEREGISTERING TUXEDO =========")
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except ValueError:
            pass

    for i, ft_shape in enumerate(SRanipal_Labels):
        delattr(Scene, "ft_shapekey_" + str(i))

    for i, ft_shape in enumerate(SRanipal_Labels):
        delattr(Scene, "ft_shapekey_enable_" + str(i))
    print("========= DEREGISTERING TUXEDO FINISHED =========")
    bpy.utils.previews.remove(globals.icons_dict)

if __name__ == '__main__':
    register()
