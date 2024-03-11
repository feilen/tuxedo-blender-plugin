import os
import typing
import bpy
import pathlib
version = (0, 4, 2)
blender = (4, 0)

def import_multi_files(method = None, directory: typing.Optional[str] = None, files: typing.Union[bpy.types.OperatorFileListElement, typing.Any] = None, filepath: typing.Optional[str] = ""):
    if not filepath:
        method(directory, filepath)
    else:
        for file in files:
            fullpath = os.path.join(directory,os.path.basename(file.name))
            print("run method!")
            method(directory, fullpath)



#each import should map to a type. even in the case that multiple methods should import together, or have the same import method. Make sure the lambdas match so they get grouped together
#In the case of a file importer that takes only one file argument and each one needs individual import, use above method. (example of it in use is ".dae" format)
import_types = {
    "fbx": (lambda directory, files, filepath : bpy.ops.import_scene.fbx(files=files, directory=directory, filepath=filepath)),
    "smd": (lambda directory, files, filepath : bpy.ops.import_scene.fbx(files=files, directory=directory, filepath=filepath)),
    "dmx": (lambda directory, files, filepath: bpy.ops.import_scene.smd(files=files, directory=directory, filepath=filepath)),
    "gltf": (lambda directory, files, filepath : bpy.ops.import_scene.gltf(files=files, filepath=filepath)),
    "glb": (lambda directory, files, filepath : bpy.ops.import_scene.gltf(files=files, filepath=filepath)),
    "qc": (lambda directory, files, filepath : bpy.ops.import_scene.smd(files=files, directory=directory, filepath=filepath)),
    "obj": (lambda directory, files, filepath : bpy.ops.import_scene.obj(files=files, directory=directory, filepath=filepath)),
    "dae": (lambda directory, files, filepath : import_multi_files(directory=directory, files=files, filepath=filepath, method = (lambda directory, filepath:  bpy.ops.wm.collada_import(filepath=filepath, auto_connect = True, find_chains = True, fix_orientation = True)))),
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