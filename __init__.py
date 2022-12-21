import sys

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

if "bpy" not in locals():
    import bpy
    from . import bake
    from . import bake_ui
else:
    import importlib
    importlib.reload(bake)
    importlib.reload(bake_ui)

def register():
    print("\n### XXX: Loading Tuxedo-blender-plugin")

    # Register all classes
    count = 0
    tools.register.order_classes()
    for cls in tools.register.__bl_classes:
        try:
            bpy.utils.register_class(cls)
            count += 1
        except ValueError:
            pass
    if count < len(tools.register.__bl_classes):
        print('Skipped', len(tools.register.__bl_classes) - count, ' classes.')

    # Register Scene types
    extentions.register()

    # Set preferred Blender options
    if hasattr(tools.common.get_user_preferences(), 'system') and hasattr(tools.common.get_user_preferences().system, 'use_international_fonts'):
        tools.common.get_user_preferences().system.use_international_fonts = True
    elif hasattr(tools.common.get_user_preferences(), 'view') and hasattr(tools.common.get_user_preferences().view, 'use_international_fonts'):
        tools.common.get_user_preferences().view.use_international_fonts = True
    else:
        pass  # From 2.83 on this is no longer needed
    tools.common.get_user_preferences().filepaths.use_file_compression = True
    bpy.context.window_manager.addon_support = {'OFFICIAL', 'COMMUNITY', 'TESTING'}

    print("### Loaded Tuxedo-blender-plugin successfully!\n")


def unregister():
    print("### XXX: Unloading Tuxedo-blender-plugin")

    # Unregister updater
    updater.unregister()

    # Unload all classes in reverse order
    count = 0
    for cls in reversed(tools.register.__bl_ordered_classes):
        try:
            bpy.utils.unregister_class(cls)
            count += 1
        except ValueError:
            pass
        except RuntimeError:
            pass
    print('Unregistered', count, ' classes.')

    # Remove folder from sys path
    if file_dir in sys.path:
        sys.path.remove(file_dir)

    tools.settings.stop_apply_settings_threads()

    print("### Unloaded CATS successfully!\n")


if __name__ == '__main__':
    register()
