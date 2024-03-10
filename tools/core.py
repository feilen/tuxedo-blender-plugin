# GPL Licence
import bpy
import numpy as np
from .dictionaries import bone_names
import bmesh
import math
from io_scene_fbx import fbx_utils

# Core is the file where simple and complex methods but not classes used by many things go
# this stores how we do simple functions that happen multiple times, and may need version checking
# because of this, DONT PUT CLASSES HERE.
# Before you make your own method, check here for one that does the same thing, since it will save you time.
# 

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

def shape_key_to_basis(context, obj, shape_key_name):
    if shape_key_name not in obj.data.shape_keys.key_blocks:
        return
    shape_key = obj.data.shape_keys.key_blocks[shape_key_name]
    for v in obj.data.vertices:
        v.co = shape_key.data[v.index].co
    obj.data.update()

def merge_bone_weights(context, armature, bone_names, active_bone_name):
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

def merge_bone_weights_to_respective_parents(context, armature, bone_names):
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
    try:
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    except:
        print("Oh here comes a crash from the merge bone weights!")
    for bone_name in bone_names:
        armature.data.edit_bones.remove(armature.data.edit_bones[bone_name])

def patch_fbx_exporter():
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

    bpy.types.Object.Enum = sorted(choices, key=lambda x: tuple(x[0].lower()))
    return bpy.types.Object.Enum

def get_meshes_objects(context, armature_name=None):
    arm = get_armature(context, armature_name)
    if arm:
        return [obj for obj in arm.children if
                obj.type == "MESH" and
                not obj.hide_get() and
                obj.name in context.view_layer.objects]
    return []



def add_shapekey(obj, shapekey_name, from_mix=False):
    if not has_shapekeys(obj) or shapekey_name not in obj.data.shape_keys.key_blocks:
        shape_key = obj.shape_key_add(name=shapekey_name, from_mix=from_mix)
        return shape_key

def get_armature(context, armature_name=None):
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

def join_meshes(context, armature_name):
    bpy.data.objects[armature_name]
    meshes = get_meshes_objects(context, armature_name)
    if not meshes:
        return
    context.view_layer.objects.active = meshes[0]
    bpy.ops.object.select_all(action='DESELECT')
    for mesh in meshes:
        mesh.select_set(True)
    bpy.ops.object.join()

def has_shapekeys(obj):
    return obj.type == 'MESH' and obj.data and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 1

# Remove doubles using bmesh
def remove_doubles(mesh, margin):
    if mesh.type != 'MESH':
        return
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin)
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()
    
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

def unselect_all():
    for obj in get_objects():
        select(obj, False)

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