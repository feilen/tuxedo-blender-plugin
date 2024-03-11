import bpy
import io_scene_x3d
import io_scene_valvesource
version = (0, 4, 2)
blender = (4, 0)

#each import should map to a type. even in the case that multiple methods should import together, or have the same import method. Make sure the lambdas match so they get grouped together
import_types = {
    "fbx": (lambda directory, files, filepath : bpy.ops.import_scene.fbx(files=files, directory=directory, filepath=filepath)),
    "smd": (lambda directory, files, filepath : bpy.ops.import_scene.fbx(files=files, directory=directory, filepath=filepath)),
    "dmx": (lambda directory, files, filepath: bpy.ops.import_scene.smd(files=files, directory=directory, filepath=filepath)),
    "gltf": (lambda directory, files, filepath : bpy.ops.import_scene.gltf(files=files, filepath=filepath)),
    "glb": (lambda directory, files, filepath : bpy.ops.import_scene.gltf(files=files, filepath=filepath)),
    "qc": (lambda directory, files, filepath : bpy.ops.import_scene.smd(files=files, directory=directory, filepath=filepath)),
    "obj": (lambda directory, files, filepath : bpy.ops.import_scene.obj(files=files, directory=directory, filepath=filepath)),
    "dae": (lambda directory, files, filepath : bpy.ops.wm.collada_import(filepath=filepath, auto_connect = True, find_chains = True, fix_orientation = True)),
    "3ds": (lambda directory, files, filepath : bpy.ops.import_scene.max3ds(files=files, directory=directory, filepath=filepath)),
    "stl": (lambda directory, files, filepath : bpy.ops.import_mesh.stl(files=files, directory=directory, filepath=filepath)),
    "mtl": (lambda directory, files, filepath : bpy.ops.import_scene.obj(files=files, directory=directory, filepath=filepath)),
    "x3d": (lambda directory, files, filepath : bpy.ops.import_scene.x3d(files=files, directory=directory, filepath=filepath)),
    "wrl": (lambda directory, files, filepath : bpy.ops.import_scene.x3d(files=files, directory=directory, filepath=filepath)),
}

def concat_imports_filter(imports):
    names = ""
    for importer in imports.keys():
        names = names+"*."+importer+";"
    return names

imports = concat_imports_filter(import_types)