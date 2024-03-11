from .globals import blender, version

is_reloading = False
if "bpy" not in locals():
    import bpy
    is_reloading = False
else:
    is_reloading = True

from .class_register import order_classes, classes

if is_reloading:
    import importlib
    #reload our imports so they reload when we hit F8.
    importlib.reload(bake)
    #supressWarnings
    importlib.reload(properties)
    importlib.reload(tools)
    importlib.reload(ui)
    #reload the imports of the ui elements
    import glob
    modules = glob.glob(join(dirname(__file__), "ui_sections/*.py"))
    for ui_obj in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
        exec("importlib.reload("+ui_obj+")")
    #reload the imports of the tools files
    modules = glob.glob(join(dirname(__file__), "tools/*.py"))
    for ui_obj in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
        exec("importlib.reload("+ui_obj+")")
else:
    from .properties import register_properties, gmod_path, set_steam_library
    from .tools.tools import SRanipal_Labels
    from bpy.types import Scene
    #this is needed since it doesn't see them unless imported... - @989onan
    from . import bake, properties, ui
    from . import tools
    
    from os.path import dirname, basename, isfile, join
    
    #this... is awful I'm sorry but this is the only way of dynamically load all the files under the directory
    import glob
    modules = glob.glob(join(dirname(__file__), "ui_sections/*.py"))
    for module_name in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
        exec("from .ui_sections import "+module_name)
    #tools importing same bad way
    modules = glob.glob(join(dirname(__file__), "tools/*.py"))
    for module_name in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
        exec("from .tools import "+module_name)


bl_info = {
    'name': 'Tuxedo Blender Plugin',
    'category': '3D View',
    'author': 'Feilen',
    'location': 'View 3D > Tool Shelf > Tuxedo',
    'description': 'A variety of tools to improve and optimize models for use in a variety of game engines.',
    'version': version,
    'blender': blender,
    'wiki_url': 'https://github.com/feilen/tuxedo-blender-plugin',
    'tracker_url': 'https://github.com/feilen/tuxedo-blender-plugin/issues',
    'warning': '',
}







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

    # Properties
    register_properties()
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

if __name__ == '__main__':
    register()
