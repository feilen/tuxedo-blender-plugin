# GPL Licence
import threading
import time
import bpy
import numpy as np
from .dictionaries import bone_names
import bmesh
import math
import webbrowser
import typing
import mathutils


from ..globals import blender

# Core is the file where simple and complex methods but not classes used by many things go
# this stores how we do simple functions that happen multiple times, and may need version checking
# because of this, DONT PUT CLASSES HERE.
# Before you make your own method, check here for one that does the same thing, since it will save you time.

def Destroy_By_Name(context, name):
    bpy.ops.object.select_all(action='DESELECT')
    destroyed_object = bpy.data.objects.get(name)
    context.view_layer.objects.active = destroyed_object
    destroyed_object.select_set(True)
    bpy.ops.object.delete(use_global=False)

def get_tricount(obj):
    # Triangulates with Bmesh to avoid messing with the original geometry
    bmesh_mesh = bmesh.new()
    bmesh_mesh.from_mesh(obj.data)

    bmesh.ops.triangulate(bmesh_mesh, faces=bmesh_mesh.faces[:])
    return len(bmesh_mesh.faces)

def get_children_recursive(parent):
    if bpy.app.version < (3, 1):
        objs = []

        def get_child_names(obj):
            for child in obj.children:
                objs.append(child)
                if child.children:
                    get_child_names(child)

        get_child_names(parent)
        return objs
    else:
        return parent.children_recursive

def apply_shapekey_to_basis(context: bpy.types.Context, obj: bpy.types.Object, shape_key_name: str, delete_old: bool = False):
    if shape_key_name not in obj.data.shape_keys.key_blocks:
        return False
    shapekeynum = obj.data.shape_keys.key_blocks.find(shape_key_name)
    
    Set_Mode(context, 'EDIT')

    select_set_all_curmode(context, 'SELECT')

    
    obj.active_shape_key_index = 0
    bpy.ops.mesh.blend_from_shape(shape = shape_key_name, add=True, blend=1)
    obj.active_shape_key_index = shapekeynum
    select_set_all_curmode(context, 'SELECT')
    bpy.ops.mesh.blend_from_shape(shape = shape_key_name, add=True, blend=-2)
    

    select_set_all_curmode(context, 'DESELECT')
    
    Set_Mode(context,'OBJECT')

    if delete_old:
        obj.active_shape_key_index = shapekeynum
        bpy.ops.object.shape_key_remove(all=False)
    return True

def merge_bone_weights(context, armature, bone_names, active_bone_name, remove_old=False):
    if not isinstance(bone_names, list):
        bone_names = [bone_names]
    if not isinstance(active_bone_name, list):
        active_bone_name = [active_bone_name]
    if not isinstance(armature, bpy.types.Object):
        armature = bpy.data.objects[armature]
    if not isinstance(armature.data, bpy.types.Armature):
        raise Exception("Object is not an armature")
    if not armature.data.bones:
        raise Exception("Armature has no bones")
    for bone_name in bone_names:
        if bone_name not in armature.data.bones:
            raise Exception("Armature has no bone named %s" % bone_name)
    for bone_name in active_bone_name:
        if bone_name not in armature.data.bones:
            raise Exception("Armature has no bone named %s" % bone_name)
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        if obj.parent != armature:
            continue
        for v in obj.data.vertices:
            for g in v.groups:
                if g.group >= len(obj.vertex_groups):
                    continue
                if obj.vertex_groups[g.group].name in bone_names:
                    for active_bone_name in active_bone_name:
                        try:
                            active_bone_index = obj.vertex_groups[active_bone_name].index
                            v.groups[active_bone_index].weight += g.weight
                        except KeyError:
                            obj.vertex_groups.new(name=active_bone_name)
                            active_bone_index = obj.vertex_groups[active_bone_name].index
                            v.groups[active_bone_index].weight += g.weight
    if remove_old:
        try:
            bpy.context.view_layer.objects.active = armature
            Set_Mode(context,mode='OBJECT')
            Set_Mode(context,mode='EDIT')
        except:
            print("Oh here comes a crash from the merge bone weights!")
        try:
            bone_names.remove(active_bone_name[0])
        except:
            pass
        for bone_name in bone_names:
            print(bone_name)
            armature.data.edit_bones.remove(armature.data.edit_bones[bone_name])

def merge_bone_weights_to_respective_parents(context, armature, bone_names, remove_old=True):
    if not isinstance(bone_names, list):
        bone_names = [bone_names]
    if not isinstance(armature, bpy.types.Object):
        armature = bpy.data.objects[armature]
    if not isinstance(armature.data, bpy.types.Armature):
        raise Exception("Object is not an armature")
    if not armature.data.bones:
        raise Exception("Armature has no bones")
    for bone_name in bone_names:
        if bone_name not in armature.data.bones:
            raise Exception("Armature has no bone named %s" % bone_name)
    for obj in get_meshes_objects(context, armature_name=armature.name):
        if obj.type != 'MESH':
            continue
        if obj.parent != armature:
            continue
        # TODO: this can be MUCH faster.
        vgroup_lookup = dict([(vgp.index, vgp.name) for vgp in obj.vertex_groups])
        print(vgroup_lookup)
        for v in obj.data.vertices:
            for g in v.groups:
                try:
                    if vgroup_lookup[g.group] in bone_names:
                        bone = armature.data.bones[vgroup_lookup[g.group]]
                        if bone.parent and bone.parent.name in obj.vertex_groups:
                            obj.vertex_groups[bone.parent.name].add([v.index], g.weight, 'ADD')

                except Exception as e:
                    pass # this is because of null vertex group reading, and we kinda don't care all that much about it - @989onan
        for bone_name in bone_names:
            # remove old bones vertex groups
            if bone_name in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups[bone_name])

    # remove old bones
    if remove_old:
        try:
            bpy.context.view_layer.objects.active = armature
            Set_Mode(context,mode='OBJECT')
            Set_Mode(context,mode='EDIT')
        except:
            print("Oh here comes a crash from the merge bone weights!")
        for bone_name in bone_names:
            armature.data.edit_bones.remove(armature.data.edit_bones[bone_name])

def patch_fbx_exporter():
    from io_scene_fbx import fbx_utils #type: ignore
    fbx_utils.get_bid_name = get_bid_name

# Blender-specific key generators - monkeypatched to force name if present
def get_bid_name(bid):
    if isinstance(bid, bpy.types.ID) and 'tuxedoForcedExportName' in bid:
        return bid['tuxedoForcedExportName']
    library = getattr(bid, "library", None)
    if library is not None:
        return "%s_L_%s" % (bid.name, library.name)
    else:
        return bid.name

def get_meshes(self, context):
    choices = []

    for mesh in get_meshes_objects(context):
        choices.append((mesh.name, mesh.name, mesh.name))

    choices2 = []
    choices2.append(("NONE","NONE","NONE"))
    choices2.extend(sorted(choices, key=lambda x: tuple(x[0].lower())))
    bpy.types.Object.Enum = choices2
    return bpy.types.Object.Enum

def get_meshes_objects(context, armature_name=None):
    arm = get_armature(context, armature_name)
    if arm:
        return [obj for obj in arm.children if
                obj.type == "MESH" and
                not obj.hide_get() and
                obj.name in context.view_layer.objects]
    return []



def add_shapekey(obj, shapekey_name, from_mix=False) -> bpy.types.ShapeKey:
    if not has_shapekeys(obj) or shapekey_name not in obj.data.shape_keys.key_blocks:
        shape_key = obj.shape_key_add(name=shapekey_name, from_mix=from_mix)
        return shape_key
    


def get_armature(context, armature_name=None) -> bpy.types.Object:
    if armature_name:
        obj = bpy.data.objects[armature_name]
        if obj.type == "ARMATURE":
            return obj
    if context.view_layer.objects.active:
        obj = context.view_layer.objects.active
        if obj.type == "ARMATURE":
            return obj
    armatures = [obj for obj in context.view_layer.objects if obj.type == "ARMATURE"]
    if len(armatures) == 1:
        return armatures[0]

def simplify_bonename(n):
    return n.lower().translate(dict.fromkeys(map(ord, u" _.")))

def materials_list_update(context):
    choices = []
    try:
        for mesh in get_meshes_objects(context, armature_name=get_armature(context).name):
            for mat in mesh.data.materials:
                if mat.name not in choices:
                    choices.append(mat.name)
    except Exception as e:
        print(e)
    
    material_list_bake = [i.name for i in context.scene.bake_material_groups]
    
    for i in choices:
        if i not in material_list_bake:
            added_item = context.scene.bake_material_groups.add()
            added_item.name = i
    material_list_bake = [i.name for i in context.scene.bake_material_groups]
    for k,i in enumerate(material_list_bake):
        if i not in choices:
            context.scene.bake_material_groups.remove(k)
    
    return choices


def apply_modifier(mod):
    if mod.type == 'ARMATURE':
        # Armature modifiers are a special case: they don't have a show_render
        # property, so we have to use the show_viewport property instead
        if not mod.show_viewport:
            return
    else:
        if not mod.show_render:
            return
    bpy.context.view_layer.objects.active = mod.id_data
    bpy.ops.object.modifier_apply(modifier=mod.name)

def get_modifiers_active(self, context):
    return [(modifier.name, modifier.name, modifier.name) for modifier in context.object.modifiers]

def apply_modifier_for_obj_with_shapekeys(mod,delete_old=False):
    if mod.type == 'ARMATURE':
        # Armature modifiers are a special case: they don't have a show_render
        # property, so we have to use the show_viewport property instead
        if not mod.show_viewport:
            return
    else:
        if not mod.show_render:
            return
    obj = mod.id_data
    old_mod_name = mod.name
    context = bpy.context
    Set_Mode(context,'OBJECT')

    obj_names = []
    print("start applying modifiers for mesh with shapekeys")

    select_set_all_curmode(context,'DESELECT')
    for key in obj.data.shape_keys.key_blocks:
        keyname = key.name
        obj_names.append(keyname)

        newobj = obj.copy()
        newobj.data = obj.data.copy()
        newobj.animation_data_clear()
        
        context.collection.objects.link(newobj)
        select_set_all_curmode(context,'DESELECT')
        select(newobj)
        set_active(newobj)
        try:
            bpy.data.objects[keyname].name += "conflicting_name" #get rid of conflicting name in data model
        except:
            pass
        newobj.name = keyname #set name to allow blender data model to set new name
        

        #assign the key we have iterated to as the active key on the mesh
        for key2 in newobj.data.shape_keys.key_blocks:
            key2.value = 0
        newobj.active_shape_key_index = newobj.data.shape_keys.key_blocks.find(keyname)

        bpy.ops.object.shape_key_move(type='TOP')
        bpy.ops.object.shape_key_move(type='TOP')

        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        print("object duplicated for shapekey "+keyname)
            
        print("applying "+old_mod_name+" modifier for "+newobj.name)
        bpy.ops.object.modifier_move_to_index(modifier=old_mod_name, index=0)
        apply_modifier(newobj.modifiers[old_mod_name])
    
    select_set_all_curmode(context,'DESELECT')
    select(obj)
    set_active(obj)
    for key2 in obj.data.shape_keys.key_blocks:
        key2.value = 0
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

    for bpy_object in obj_names:
        bpy_object_obj = bpy.data.objects[bpy_object]
        select(bpy_object_obj)
    select(obj)
    set_active(obj)

    bpy.ops.object.join_shapes()
    obj.active_shape_key_index = 0 
    bpy.ops.object.shape_key_remove(all=False)

    vertcount = len(bpy.data.objects[obj_names[0]].data.vertices)

    for obj_name in obj_names:
        if len(bpy.data.objects[obj_name].data.vertices) != vertcount:
            return "Shape keys ended up with different number of vertices!\nAll shape keys needs to have the same number of vertices after modifier is applied.\nOtherwise joining such shape keys will fail!"

    select(obj,sel=False)
    for bpy_object in obj_names:
        bpy_object_obj = bpy.data.objects[bpy_object]
        delete(bpy_object_obj)
    
    select(obj)
    set_active(obj)
    if delete_old: bpy.ops.object.modifier_remove(modifier=old_mod_name)

    print("finished applying modifier for object with shapekeys.")

    return True  

def connect_bones(context: bpy.types.Context, armature: bpy.types.Armature):
    prev_mode = context.object.mode
    Set_Mode(context, "EDIT")
    bone: bpy.types.EditBone = None
    for bone in (armature.edit_bones if prev_mode != "EDIT" else [i for i in armature.edit_bones if (i.select == True) or (i.select_head == True) or (i.select_tail == True)]):
        if len(bone.children) == 1:
            child: bpy.types.EditBone = bone.children[0]
            bone.tail.xyz = child.head.xyz
            armature.edit_bones.active = child
            armature.edit_bones.active.use_connect = True
    Set_Mode(context, prev_mode)

def dup_and_split_weights_bones(context: bpy.types.Context, armature_obj: bpy.types.Object):
    armature: bpy.types.Armature = armature_obj.data
    prev_mode = context.object.mode
    Set_Mode(context, "EDIT")
    bone: bpy.types.EditBone = None
    bone_set: list[dict[str, str]] = []
    for bone in [i for i in armature.edit_bones if (i.select == True) or (i.select_head == True) or (i.select_tail == True)]:
        bone_copy: bpy.types.EditBone = duplicatebone(bone)
        bone_copy.tail.xyz = bone.tail.xyz
        bone_copy.head.xyz = bone.head.xyz
        bone_copy.roll = bone.roll
        bone_copy.name = bone.name + ".copy"
        bone_set.append({"copy": bone_copy.name, "orig": bone.name})

    #This should be pretty efficient, since we are only iterating the data we need instead of everything
    #first we go over objects that are meshes, then the groups we want, then over all the vertices once per object
    #during every vertex, we check the group we are currently on is on the vertex, and if it is, then divide it's weight by 2, and add half it's weight to a new vertex group that is the copied bone.
    #This way we only do what we need to, rather than iterate over every vertex per group.
    for obj in [i for i in armature_obj.children if i.type == "MESH"]:
        mesh_data: bpy.types.Mesh = obj.data
        group_orig: bpy.types.VertexGroup = None
        for dict_bone in bone_set:
            try:
                group_orig = obj.vertex_groups[dict_bone["orig"]]
                obj.vertex_groups.new(name=dict_bone["copy"])
            except:
                continue
            vertex: bpy.types.MeshVertex = None
            for weight_index,vertex in enumerate(mesh_data.vertices):
                weight = -1
                try:
                    weight = group_orig.weight(weight_index)
                except:
                    continue
                if weight and weight > 0:
                    
                    group_orig.add([weight_index], weight/2, "REPLACE")
                    group_copy: bpy.types.VertexGroup = obj.vertex_groups[dict_bone["copy"]]
                    group_copy.add([weight_index], weight/2, "REPLACE")



            
    
    Set_Mode(context, prev_mode)


def join_meshes(context: bpy.types.Context, armature_name: str) -> None:
    bpy.data.objects[armature_name]
    meshes = get_meshes_objects(context, armature_name)
    if not meshes:
        return
    context.view_layer.objects.active = meshes[0]
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in meshes:
        mesh.select_set(True)
    bpy.ops.object.join()

def has_shapekeys(obj) -> bool:
    return obj.type == 'MESH' and hasattr(obj, 'data') and hasattr(obj.data,'shape_keys') and hasattr(obj.data.shape_keys, 'key_blocks') and len(obj.data.shape_keys.key_blocks) > 1

# Remove doubles using bmesh safely
def remove_doubles_safely(mesh: typing.Union[bpy.types.Mesh], margin: float = .00001, merge_all: bool = True) -> None:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    vert: bmesh.types.BMVert = None
    shared_locs: dict[mathutils.Vector, list[int]] = dict()
    #This isn't very efficient, but it will do for now - @989onan
    for vert in [i for i in bm.verts if i.select == True and merge_all or not merge_all]: #only include selected if merge all is enabled.
        key: mathutils.Vector = vert.co.xyz
        key = key.freeze()
        if key not in shared_locs:
            shared_locs[key] = []
        shared_locs[key].append(vert.index)
    data: bpy.types.bpy_prop_collection[bpy.types.ShapeKeyPoint] = None
    shape_vert: bpy.types.ShapeKeyPoint = None
    #remove vertice groups for vertices that change position too far away from a neighbor in any of the shapekeys, (EX: mouth lips would get sealed if this didn't filter those shapekeys)
    #This doesn't filter verts that don't share points, but this allows us to make sure that if a vertex moves to share grouping with others that stay close together during a shapekey.
    # this is no where near perfect, because it discards points that could move away from each other on a shapekey but on all shapekeys one could still merge with a common neighboring vertex 
    # (ex: a vertex orbiting another at merging distance in 20 different shapekeys. this would invalidat that vertex from merging to any other vertex, but we would ideally wanna merge with the one it's orbiting), but this is close enough.
    #TODO: Can we use scipy? Please? I could try making this perfect with such, or just discard the idea of perfect I guess...
    bm.verts.ensure_lookup_table()
    if hasattr(mesh, "shapekeys"):
        for data in mesh.shape_keys.key_blocks:
            for index,shape_vert in enumerate(data.data):
                key: mathutils.Vector = shape_vert.co.xyz
                key = key.freeze()
                key2: mathutils.Vector = bm.verts[index].co.xyz
                key2 = key2.freeze()
                if (bm.verts[index].co-shape_vert.co).length > margin:
                    try:
                        shared_locs[key2].remove(index)
                    except:
                        pass
    else:
        pass
    bm.free()
    bm = bmesh.new()
    bm.from_mesh(mesh)

    #Finally we take all the filtered indices, get their coorisponding bmesh vert, and then flatten them into a list. This way these verts will be the only ones that are attempted for a merge.
    bm.verts.ensure_lookup_table()
    final_merge: list[bmesh.types.BMVert] = []
    for coord,shared_coord_list in shared_locs.items():
        for vertex_num in shared_coord_list:
            final_merge.append(bm.verts[vertex_num])
            
    prevmode = bpy.context.object.mode
    Set_Mode(context=bpy.context, mode = "OBJECT")
    bmesh.ops.remove_doubles(bm, verts=final_merge, dist=margin)
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    Set_Mode(context=bpy.context, mode = prevmode)
    
def triangulate_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()

# Code below Stolen from Cats Blender Plugin File "common.py", Sorry! But tbf we don't want depenencies. Full credit to the cats blender team!
# Btw the code it's stolen from is GPL
def delete(obj):
    if obj.parent:
        for child in obj.children:
            child.parent = obj.parent

    objs = bpy.data.objects
    objs.remove(objs[obj.name], do_unlink=True)


def Set_Mode(context, mode):
    if context.view_layer.objects.active is None:
        context.view_layer.objects.active = context.view_layer.objects[0]
        bpy.ops.object.mode_set(mode=mode,toggle=False)
    else:
        bpy.ops.object.mode_set(mode=mode,toggle=False)

def duplicatebone(b: bpy.types.EditBone) -> bpy.types.EditBone:
    arm = bpy.context.object.data
    cb = arm.edit_bones.new(b.name)

    cb.head = b.head
    cb.tail = b.tail
    cb.matrix = b.matrix
    cb.parent = b.parent
    return cb


#remove zero weight bones or zero weights <- for control+f this giantic file.
def get_zero_and_weight_vertex_groups(armature: bpy.types.Object, invert: bool = False) -> dict[bpy.types.Object, set[str]]:
    objects_and_groups: dict[bpy.types.Object, set[str]] = dict()
    
    for obj in [i for i in armature.children if i.type == "MESH"]:
        weighted_groups: set[str] = set()
        data: bpy.types.Mesh = obj.data
        vertex_groups: set[str] = set([i.name for i in obj.vertex_groups])
        #we're doing it this way and adding to a set, because being consistent with your parsing is helpful in programming langauges
        #because preventing cache skipping and accessing data in order and only once is good - @989onan 
        for vert in data.vertices:
            for group in vert.groups:
                if (group.weight > 0.0):
                    weighted_groups.add(obj.vertex_groups[group.group].name)
        if(invert):
            unweighted: set[str] = set(weighted_groups)
        else:
            unweighted: set[str] = set(vertex_groups).difference(weighted_groups)
        

        objects_and_groups[obj] = unweighted

    return objects_and_groups

def mix_weights(mesh, vg_from, vg_to, mix_strength=1.0, mix_mode='ADD', delete_old_vg=True):
    """Mix the weights of two vertex groups on the mesh, optionally removing the vertex group named vg_from."""
    mesh.active_shape_key_index = 0
    mod = mesh.modifiers.new("VertexWeightMix", 'VERTEX_WEIGHT_MIX')
    mod.vertex_group_a = vg_to
    mod.vertex_group_b = vg_from
    mod.mix_mode = mix_mode
    mod.mix_set = 'B'
    mod.mask_constant = mix_strength
    apply_modifier(mod)
    if delete_old_vg:
        mesh.vertex_groups.remove(mesh.vertex_groups.get(vg_from))
    mesh.active_shape_key_index = 0

# end code stolen from cats

def Get_Meshes_And_Armature(context, targcollection):

    Set_Mode(context, "OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    parentobj = []
    body_armature = None
    for collection in bpy.data.collections:
        for object in collection.all_objects[:]:
            object.hide_set(False)

    for obj in targcollection.objects:
        if obj.type == "MESH":
            parentobj.append(obj)
            obj.select_set(True)
        if obj.type == "ARMATURE":
            body_armature = obj

    return parentobj, body_armature
    


def duplicate_shapekey(string):
    active_object = bpy.context.active_object

    #Check shape keys if duplicate
    if active_object.data.shape_keys.key_blocks.find(string) >= 0:
        #print("Duplicate shape key found!")
        return True
    else:
        return False

def version_2_79_or_older():
    return bpy.app.version < (2, 80)

#this is done because the version our addon is made for may not be minor or patch specific. In this case, just check what we specify for our version
#This allows us to specify "(4, 0)" and ignore any 4.0.x version patches. - @989onan
def version_too_new():
    is_too_new = False
    for i in range(0,3):
        try:
            if (bpy.app.version[i] > blender[i]):
                is_too_new = True
        except Exception:
            pass
    
    return is_too_new

def unselect_all():
    
        for obj in get_objects():
            select(obj, False)
    

#nice wrapper method to change modes
def select_set_all_curmode(context=bpy.context,action='DESELECT'):
    if(context.object.mode == 'OBJECT'):
        bpy.ops.object.select_all(action=action)
    elif(context.object.mode == 'EDIT'):
        for obj in bpy.context.selected_objects: #iterate over all objects, this thankfully includes the active object.
            if obj.type == 'MESH':
                bpy.ops.mesh.select_all(action=action)
            if obj.type == 'CURVE':
                bpy.ops.curve.select_all(action=action)
            if obj.type == 'ARMATURE':
                bpy.ops.armature.select_all(action=action)
    elif(context == 'POSE'):
        bpy.ops.pose.select_all(action=action)
    
def get_objects():
    return bpy.context.scene.objects if version_2_79_or_older() else bpy.context.view_layer.objects

def set_active(obj, skip_sel=False):
    if not skip_sel:
        select(obj)
    if version_2_79_or_older():
        bpy.context.scene.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj

def select(obj, sel=True):
    if sel:
        hide(obj, False)
    if version_2_79_or_older():
        obj.select = sel
    else:
        obj.select_set(sel)

def hide(obj, val=True):
    if hasattr(obj, 'hide'):
        obj.hide = val
    if not version_2_79_or_older():
        obj.hide_set(val)

def get_shapekeys_ft(self, context):
    return get_shapekeys(context, [], False, False)

def get_shapekeys(context, names, no_basis, return_list):
    choices = []
    choices_simple = []
    meshes_list = get_meshes_objects(context)

    if meshes_list:
        meshes = [get_objects().get(context.scene.ft_mesh)]
    else:
        bpy.types.Object.Enum = choices
        return bpy.types.Object.Enum

    for mesh in meshes:
        if not mesh or not has_shapekeys(mesh):
            bpy.types.Object.Enum = choices
            return bpy.types.Object.Enum

        for shapekey in mesh.data.shape_keys.key_blocks:
            name = shapekey.name
            if name in choices_simple:
                continue
            if no_basis and name == 'Basis':
                continue
            # 1. Will be returned by context.scene
            # 2. Will be shown in lists
            # 3. will be shown in the hover description (below description)
            choices.append((name, name, ''))
            choices_simple.append(name)

#    choices.sort(key=lambda x: tuple(x[0].lower()))

    choices2 = []
    for name in names:
        if name in choices_simple and len(choices) > 1 and choices[0][0] != name:
            choices2.append((name, name, name))

    for choice in choices:
        choices2.append(choice)

    bpy.types.Object.Enum = choices2

    if return_list:
        shape_list = []
        for choice in choices2:
            shape_list.append(choice[0])
        return shape_list

    return bpy.types.Object.Enum

# Returns [delta_v in 3 parts, by vert idx], and a bounding box (-x, +x, -y, +y, -z, +z)
def get_shapekey_delta(mesh, shapekey_name):
    bounding_box = [math.inf, -math.inf, math.inf, -math.inf, math.inf, -math.inf]

    basis_key = mesh.data.shape_keys.key_blocks["Basis"]
    basis_key_data = np.empty((len(basis_key.data), 3), dtype=np.float32)
    basis_key.data.foreach_get("co", np.ravel(basis_key_data))
    active_key = mesh.data.shape_keys.key_blocks[shapekey_name]
    active_key_data = np.empty((len(active_key.data), 3), dtype=np.float32)
    active_key.data.foreach_get("co", np.ravel(active_key_data))
    deltas = (active_key_data - basis_key_data)
    absolute_difference = np.sum(np.abs(deltas), axis=1)
    for idx, delta_total in enumerate(absolute_difference):
        # If this vertex moved any, adjust our bounding box
        if delta_total > 0.001:
            bounding_box[0] = min(bounding_box[0], basis_key_data[idx][0])
            bounding_box[1] = max(bounding_box[1], basis_key_data[idx][0])
            bounding_box[2] = min(bounding_box[2], basis_key_data[idx][1])
            bounding_box[3] = max(bounding_box[3], basis_key_data[idx][1])
            bounding_box[4] = min(bounding_box[4], basis_key_data[idx][2])
            bounding_box[5] = max(bounding_box[5], basis_key_data[idx][2])

    return deltas, bounding_box

# Map a range 0-1 where the middle e.g. 0.2x is linearly interpolated
def crossfade(val, min_x, max_x, middle_percent):
    val_norm = (val - min_x) / (max_x - min_x)
    if val_norm < (.5 - (middle_percent / 2)):
        # full
        return 1
    if val_norm > (.5 + (middle_percent / 2)):
        # other side
        return 0
    else:
        # middle, linear falloff
        return 1 - ((val_norm - (.5 - (middle_percent / 2))) / middle_percent)


def merge_armature_stage_one(context, base_armature_name, merge_armature_name):

    base_armature = bpy.data.objects[base_armature_name]
    merge_armature = bpy.data.objects[merge_armature_name]

    merge_armature_bone_names = [i.name for i in merge_armature.data.bones]
    base_armature_bone_names = [i.name for i in base_armature.data.bones]



    context.view_layer.objects.active = base_armature
    base_armature.select_set(True)
    Set_Mode(context, "EDIT")

    bone_parenting_array = {}
    bones_children_parent_found_list = []

    common_bone_names = list(set(merge_armature_bone_names).intersection(base_armature_bone_names))

    for bone in common_bone_names:
        print("bone name :\""+bone+"\"found in both armatures. Merging")
        base_armature.data.edit_bones[bone].use_connect = False

        bone_parenting_array[bone] = []



        for bone_child in base_armature.data.edit_bones[bone].children:
            if (not (bone_child.name in common_bone_names)) and (not (bone_child.name in bones_children_parent_found_list)):
                print("bone \""+bone_child.name+"\" is under bone \""+base_armature.data.edit_bones[bone].name+"\", right? Hope so!")
                bone_parenting_array[bone].append(bone_child.name)
                bones_children_parent_found_list.append(bone_child.name)
        try:
            base_armature.data.edit_bones.remove(base_armature.data.edit_bones[bone])
        except Exception as e:
            print("Failed to delete a bone while merging that should be there!")
            print(e)

    Set_Mode(context, "OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    merge_armature.select_set(True)
    base_armature.select_set(True)
    context.view_layer.objects.active = base_armature
    bpy.ops.object.join()
    base_armature = context.object
    Set_Mode(context, "EDIT")

    for bone in bone_parenting_array:
        for child in bone_parenting_array[bone]:
            try:
                base_armature.data.edit_bones[child].use_connect = False
                base_armature.data.edit_bones[child].parent = base_armature.data.edit_bones[bone]
            except Exception as e:
                print("Bone \""+bone+"\" failed to connect back up to a parent!")
                print(e)



    Set_Mode(context, "OBJECT")
    return base_armature

def Move_to_New_Or_Existing_Collection(context, new_coll_name, old_coll=None, objects_alternative_list = None):

    try:
        Set_Mode(context, "OBJECT")
    except:
        pass
    bpy.ops.object.select_all(action='DESELECT')

    new_coll = bpy.data.collections.get(new_coll_name)
    if not new_coll:
        new_coll = bpy.data.collections.new(new_coll_name)
    try:
        context.view_layer.layer_collection.collection.children.link(new_coll)
    except:
        pass
    new_coll = bpy.data.collections[new_coll_name]

    names = []
    if objects_alternative_list:
        names = [i.name for i in objects_alternative_list]
    else:
        names = [i.name for i in old_coll.objects]

    for name in names:
        obj = bpy.data.objects.get(name)
        for collection in bpy.data.collections:
            try:
                collection.objects.unlink(obj)
            except:
                pass
        try:
            context.view_layer.layer_collection.collection.objects.unlink(obj)
        except:
            try:
                context.view_layer.layer_collection.collection.objects.unlink(obj)
            except:
                pass
        new_coll.objects.link(obj)

    return new_coll


def Copy_to_existing_collection(context,new_coll_name, old_coll=None, objects_alternative_list = None):
    try:
        Set_Mode(context, "OBJECT")
    except:
        pass
    bpy.ops.object.select_all(action='DESELECT')

    new_coll = bpy.data.collections.get(new_coll_name)
    if not new_coll:
        new_coll = bpy.data.collections.new(new_coll_name)
    try:
        context.view_layer.layer_collection.collection.children.link(new_coll)
    except:
        pass
    new_coll = bpy.data.collections[new_coll_name]


    if objects_alternative_list:
        for j in [i.name for i in objects_alternative_list]:
            bpy.data.objects.get(j).select_set(True)
    else:
        for obj in old_coll.objects:
            obj.select_set(True)

    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
    names = [i.name for i in context.selected_objects]
    for name in names:
        obj = bpy.data.objects.get(name)
        for collection in bpy.data.collections:
            try:
                collection.objects.unlink(obj)
            except:
                pass
        try:
            context.view_layer.layer_collection.collection.objects.unlink(obj)
        except:
            pass
        new_coll.objects.link(obj)

    return new_coll

def Make_And_Key_Animation(context, new_anim_name, armature):
    if bpy.data.actions.get(new_anim_name):
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = armature
        try:
            armature.animation_data_create()
        except:
            pass
        armature.animation_data.action = bpy.data.actions[new_anim_name]
    else:
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = armature
        try:
            armature.animation_data_create()
        except:
            pass
        armature.animation_data.action = bpy.data.actions.new(name=new_anim_name)
    bpy.data.actions[new_anim_name].use_fake_user = True

    print("keying "+new_anim_name+" animation")
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = armature
    armature.animation_data.action = bpy.data.actions[new_anim_name]
    armature.select_set(True)
    Set_Mode(context, "POSE")
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.keyframe_insert(data_path="rotation_euler", frame=1)
        bone.keyframe_insert(data_path="location", frame=1)
    Set_Mode(context, "OBJECT")
    return bpy.data.actions.get(new_anim_name)

def update_viewport(): #this isn't needed nessarily, it's a hack for asthetic purposes since this script takes a long time. Allows users to see progress - @989onan
    try:
        #gotten from https://blender.stackexchange.com/a/270716

        area_type = 'VIEW_3D' # change this to use the correct Area Type context you want to process in
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]

        if len(areas) <= 0:
            pass #raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")
        else:
            with bpy.context.temp_override(window=bpy.context.window,area=areas[0],region=[region for region in areas[0].regions if region.type == 'WINDOW'][0],screen=bpy.context.window.screen):
                bpy.ops.view3d.view_all(use_all_regions=True)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
    except Exception as e:
        print(e)