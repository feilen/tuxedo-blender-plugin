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
    importlib.reload(gmodui)
    importlib.reload(properties)
    importlib.reload(tools)
    importlib.reload(ui)
else:
    from .tools import FT_OT_CreateShapeKeys, SRanipal_Labels
    from .properties import register_properties
    from bpy.types import Scene
    #this is needed since it doesn't see them unless imported... - @989onan
    from . import bake, gmodui, properties, tools, ui



bl_info = {
    'name': 'Tuxedo Blender Plugin',
    'category': '3D View',
    'author': 'Feilen',
    'location': 'View 3D > Tool Shelf > Tuxedo',
    'description': 'A variety of tools to improve and optimize models for use in a variety of game engines.',
    'version': (0, 4, 2),
    'blender': (4, 0, 0),
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

    # Properties
    register_properties()
    print("========= TUXEDO REGISTRY FINISHED =========")

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
