import bmesh
import bpy
import csv
import math
import os
import webbrowser
import operator
import numpy as np
import copy
import time
import subprocess
import shutil
from mathutils import Matrix
import itertools

from io_scene_fbx import fbx_utils
from mathutils.geometry import intersect_point_line



translation_dictionary = dict()
with open(os.path.dirname(os.path.abspath(__file__)) + "/translations.csv", 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) >= 2:
            translation_dictionary[row[0]] = row[1]

# Bone names from https://github.com/triazo/immersive_scaler/
# Note from @989onan: Please make sure to make your names are lowercase in this array. I banged my head metaphorically till I figured that out...
bone_names = {
    "right_shoulder": ["rightshoulder", "shoulderr", "rshoulder"],
    "right_arm": ["rightarm", "armr", "rarm", "upperarmr", "rightupperarm", "uparmr", "ruparm"],
    "right_elbow": ["rightelbow", "elbowr", "relbow", "lowerarmr", "rightlowerarm", "lowerarmr", "lowarmr", "rlowarm"],
    "right_wrist": ["rightwrist", "wristr", "rwrist", "handr", "righthand", "rhand"],

    #hand l fingers
    "pinkie_0_r": ["littlefinger0r","pinkie0r","pinkiemetacarpalr"],
    "pinkie_1_r": ["littlefinger1r","pinkie1r","pinkieproximalr"],
    "pinkie_2_r": ["littlefinger2r","pinkie2r","pinkieintermediater"],
    "pinkie_3_r": ["littlefinger3r","pinkie3r","pinkiedistalr"],

    "ring_0_r": ["ringfinger0r","ring0r","ringmetacarpalr"],
    "ring_1_r": ["ringfinger1r","ring1r","ringproximalr"],
    "ring_2_r": ["ringfinger2r","ring2r","ringintermediater"],
    "ring_3_r": ["ringfinger3r","ring3r","ringdistalr"],

    "middle_0_r": ["middlefinger0r","middle0r","middlemetacarpalr"],
    "middle_1_r": ["middlefinger1r","middle1r","middleproximalr"],
    "middle_2_r": ["middlefinger2r","middle2r","middleintermediater"],
    "middle_3_r": ["middlefinger3r","middle3r","middledistalr"],

    "index_0_r": ["indexfinger0r","index0r","indexmetacarpalr"],
    "index_1_r": ["indexfinger1r","index1r","indexproximalr"],
    "index_2_r": ["indexfinger2r","index2r","indexintermediater"],
    "index_3_r": ["indexfinger3r","index3r","indexdistalr"],

    "thumb_0_r": ["thumb0r","thumbmetacarpalr"],
    "thumb_1_r": ['thumb0r',"thumbproximalr"],
    "thumb_2_r": ['thumb1r',"thumbintermediater"],
    "thumb_3_r": ['thumb2r',"thumbdistalr"],

    "right_leg": ["rightleg", "legr", "rleg", "upperlegr", "thighr", "rightupperleg", "uplegr", "rupleg"],
    "right_knee": ["rightknee", "kneer", "rknee", "lowerlegr", "calfr", "rightlowerleg", "lowlegr", "rlowleg"],
    "right_ankle": ["rightankle", "ankler", "rankle", "rightfoot", "footr", "rightfoot", "rightfeet", "feetright", "rfeet", "feetr"],
    "right_toe": ["righttoe", "toeright", "toer", "rtoe", "toesr", "rtoes"],

    "left_shoulder": ["leftshoulder", "shoulderl", "rshoulder"],
    "left_arm": ["leftarm", "arml", "rarm", "upperarml", "leftupperarm", "uparml", "luparm"],
    "left_elbow": ["leftelbow", "elbowl", "relbow", "lowerarml", "leftlowerarm", "lowerarml", "lowarml", "llowarm"],
    "left_wrist": ["leftwrist", "wristl", "rwrist", "handl", "lefthand", "lhand"],

    #hand l fingers
    "pinkie_0_l": ["pinkiefinger0l","pinkie0l","pinkiemetacarpall"],
    "pinkie_1_l": ["littlefinger1l","pinkie1l","pinkieproximall"],
    "pinkie_2_l": ["littlefinger2l","pinkie2l","pinkieintermediatel"],
    "pinkie_3_l": ["littlefinger3l","pinkie3l","pinkiedistall"],

    "ring_0_l": ["ringfinger0l","ring0l","ringmetacarpall"],
    "ring_1_l": ["ringfinger1l","ring1l","ringproximall"],
    "ring_2_l": ["ringfinger2l","ring2l","ringintermediatel"],
    "ring_3_l": ["ringfinger3l","ring3l","ringdistall"],

    "middle_0_l": ["middlefinger0l","middle0l","middlemetacarpall"],
    "middle_1_l": ["middlefinger1l","middle_1l","middleproximall"],
    "middle_2_l": ["middlefinger2l","middle_2l","middleintermediatel"],
    "middle_3_l": ["middlefinger3l","middle_3l","middledistall"],

    "index_0_l": ["indexfinger0l","index0l","indexmetacarpall"],
    "index_1_l": ["indexfinger1l","index1l","indexproximall"],
    "index_2_l": ["indexfinger2l","index2l","indexintermediatel"],
    "index_3_l": ["indexfinger3l","index3l","indexdistall"],

    "thumb_0_l": ["thumb0l","thumbmetacarpall"],
    "thumb_1_l": ['thumb0l',"thumbproximall"],
    "thumb_2_l": ['thumb1l',"thumbintermediatel"],
    "thumb_3_l": ['thumb2l',"thumbdistall"],

    "left_leg": ["leftleg", "legl", "rleg", "upperlegl", "thighl", "leftupperleg", "uplegl", "lupleg"],
    "left_knee": ["leftknee", "kneel", "rknee", "lowerlegl", "calfl", "leftlowerleg", 'lowlegl', 'llowleg'],
    "left_ankle": ["leftankle", "anklel", "rankle", "leftfoot", "footl", "leftfoot", "leftfeet", "feetleft", "lfeet", "feetl"],
    "left_toe": ["lefttoe", "toeleft", "toel", "ltoe", "toesl", "ltoes"],

    'hips': ["pelvis", "hips"],
    'spine': ["torso", "spine"],
    'chest': ["chest"],
    'upper_chest': ["upperchest"],
    'neck': ["neck"],
    'head': ["head"],
    'left_eye': ["eyeleft", "lefteye", "eyel", "leye"],
    'right_eye': ["eyeright", "righteye", "eyer", "reye"],
}

# array taken from cats
dont_delete_these_main_bones = [
    'Hips', 'Spine', 'Chest', 'Upper Chest', 'Neck', 'Head',
    'Left leg', 'Left knee', 'Left ankle', 'Left toe',
    'Right leg', 'Right knee', 'Right ankle', 'Right toe',
    'Left shoulder', 'Left arm', 'Left elbow', 'Left wrist',
    'Right shoulder', 'Right arm', 'Right elbow', 'Right wrist',
    'LeftEye', 'RightEye', 'Eye_L', 'Eye_R',
    'Left leg 2', 'Right leg 2',

    'Thumb0_L', 'Thumb1_L', 'Thumb2_L',
    'IndexFinger1_L', 'IndexFinger2_L', 'IndexFinger3_L',
    'MiddleFinger1_L', 'MiddleFinger2_L', 'MiddleFinger3_L',
    'RingFinger1_L', 'RingFinger2_L', 'RingFinger3_L',
    'LittleFinger1_L', 'LittleFinger2_L', 'LittleFinger3_L',

    'Thumb0_R', 'Thumb1_R', 'Thumb2_R',
    'IndexFinger1_R', 'IndexFinger2_R', 'IndexFinger3_R',
    'MiddleFinger1_R', 'MiddleFinger2_R', 'MiddleFinger3_R',
    'RingFinger1_R', 'RingFinger2_R', 'RingFinger3_R',
    'LittleFinger1_R', 'LittleFinger2_R', 'LittleFinger3_R',
]

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
                    print("\nerror below is because it attempted to read a null vertex's vertex groups.\n")
                    print(e)
                    print("\n===== END ERROR =====\n")

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

def get_meshes_objects(context, armature_name=None):
    arm = get_armature(context, armature_name)
    if arm:
        return [obj for obj in arm.children if
                obj.type == "MESH" and
                not obj.hide_get() and
                obj.name in context.view_layer.objects]
    return []

def t(str_key):
    if str_key not in translation_dictionary:
        print("Warning: couldn't find translation for \"" + str_key + "\"")
        return str_key
    else:
        return translation_dictionary[str_key]

def add_shapekey(obj, shapekey_name, from_mix=False):
    if not has_shapekeys(obj) or shapekey_name not in obj.data.shape_keys.key_blocks:
        shape_key = obj.shape_key_add(name=shapekey_name, from_mix=from_mix)

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
    armature = bpy.data.objects[armature_name]
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

class FitClothes(bpy.types.Operator):
    bl_idname = 'tuxedo.fit_clothes'
    bl_label = 'Attach to selected'
    bl_description = 'Auto-rig all selected clothes to the active body. Should have next to no clipping, but its a good idea to delete internal geometry anyway'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.selected

    def execute(self, context):
        active = context.view_layer.objects.active
        armature = next(mod for mod in active.modifiers if mod.type == 'ARMATURE').object

        for obj in context.view_layer.objects.selected:
            # skip the target
            if obj.name == active.name:
                continue
            if obj.type != "MESH":
                continue

            # Ensure the object is parented to the same armature as the active
            obj.parent = armature

            # Create empty vertex groups
            for bone_name in [bone.name for bone in armature.data.bones]:
                if bone_name not in obj.vertex_groups:
                    obj.vertex_groups.new(name=bone_name)

            # Copy vertex weights, by projected face
            trans_modifier = obj.modifiers.new(type='DATA_TRANSFER', name="DataTransfer")
            trans_modifier.object = active
            trans_modifier.use_vert_data = True
            trans_modifier.data_types_verts = {'VGROUP_WEIGHTS'}
            trans_modifier.vert_mapping = 'POLYINTERP_NEAREST'
            context.view_layer.objects.active = obj
            apply_modifier(trans_modifier)

            # Setup armature
            for mod_name in [mod.name for mod in obj.modifiers]:
                if obj.modifiers[mod_name].type == 'ARMATURE':
                    obj.modifiers.remove(obj.modifiers[mod_name])
            arm_modifier = obj.modifiers.new(type='ARMATURE', name='Armature')
            arm_modifier.object = armature

        self.report({'INFO'}, 'Clothes rigged!')
        return {'FINISHED'}

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

class AutoDecimatePresetGood(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_good'
    bl_label = t('DecimationPanel.preset.good.label')
    bl_description = t('DecimationPanel.preset.good.description')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 70000
        return {'FINISHED'}

class AutoDecimatePresetExcellent(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_excellent'
    bl_label = t('DecimationPanel.preset.excellent.label')
    bl_description = t('DecimationPanel.preset.excellent.description')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 32000
        return {'FINISHED'}

class AutoDecimatePresetQuest(bpy.types.Operator):
    bl_idname = 'tuxedo_decimation.preset_quest'
    bl_label = t('DecimationPanel.preset.quest.label')
    bl_description = t('DecimationPanel.preset.quest.description')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.context.scene.tuxedo_max_tris = 5000
        return {'FINISHED'}

def triangulate_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()

class RepairShapekeys(bpy.types.Operator):
    bl_idname = 'tuxedo.repair_shapekeys'
    bl_label = 'Repair Broken Shapekeys'
    bl_description = "Attempt to repair messed up shapekeys caused by some Blender operations"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            return True

        meshes = get_meshes_objects(context)
        return meshes

    def execute(self, context):
        objs = [context.active_object]
        if not objs[0] or (objs[0] and (objs[0].type != 'MESH' or objs[0].data.shape_keys is None)):
            bpy.ops.object.select_all(action='DESELECT')
            meshes = get_meshes_objects(context)
            objs = meshes

        for obj in objs:
            if obj.data.shape_keys is None:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            points = []
            # For each vertex index...
            for vert_idx in range(0, len(obj.data.shape_keys.key_blocks[0].data)):
                # find the most common version of the point in all the non-basis keys
                verts = dict()
                for shape_idx in range(1, len(obj.data.shape_keys.key_blocks)):
                    vert_coord = obj.data.shape_keys.key_blocks[shape_idx].data[vert_idx]
                    if not vert_coord in verts:
                        verts[vert_coord] = 0
                    verts[vert_coord] += 1
                found_coord = max(verts.items(), key=operator.itemgetter(1))[0]
                print(found_coord)
                points.append(found_coord)
            # create a new shapekey
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shape_key_add(from_mix=False)
            obj.active_shape_key.name = "TUXEDO Antibasis"

            # set it to the most-common points
            for vert_idx in range(0, len(obj.data.shape_keys.key_blocks[0].data)):
                obj.active_shape_key.data[vert_idx].co[0] = points[vert_idx].co[0]
                obj.active_shape_key.data[vert_idx].co[1] = points[vert_idx].co[1]
                obj.active_shape_key.data[vert_idx].co[2] = points[vert_idx].co[2]
            # un-apply it to all other shapekeys
            for idx in range(1, len(obj.data.shape_keys.key_blocks) - 1):
                obj.active_shape_key_index = idx
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.blend_from_shape(shape="TUXEDO Antibasis", blend=-1.0, add=True)
                bpy.ops.object.mode_set(mode='OBJECT')
            obj.shape_key_remove(key=obj.data.shape_keys.key_blocks["TUXEDO Antibasis"])
            obj.active_shape_key_index = 0

        self.report({'INFO'}, "Repair complete.")
        return {'FINISHED'}

class SmartDecimation(bpy.types.Operator):
    bl_idname = 'tuxedo.smart_decimation'
    bl_label = 'Smart Decimate'
    bl_description = 'Decimate all meshes attached to the selected armature, preserving shapekeys.'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    armature_name: bpy.props.StringProperty(
        default=''
    )
    preserve_seams: bpy.props.BoolProperty(
        default=False
    )
    preserve_objects: bpy.props.BoolProperty(
        default=False
    )
    max_single_mesh_tris: bpy.props.IntProperty(
        default=9900
    )
    
#    def poll(cls, context):
#        return True #context.view_layer.objects.active and context.view_layer.objects.selected
#
    def execute(self, context):
        animation_weighting = context.scene.decimation_animation_weighting
        animation_weighting_factor = context.scene.decimation_animation_weighting_factor
        tuxedo_max_tris = context.scene.tuxedo_max_tris
        armature = get_armature(context, armature_name=self.armature_name)
        if not self.preserve_objects:
            join_meshes(context, armature.name)
        meshes_obj = get_meshes_objects(context, armature_name=self.armature_name)
        
        
        if len(meshes_obj) == 0:
            self.report({'INFO'}, "No meshes found.")
            return {'FINISHED'}
        if not armature:
            self.report({'INFO'}, "No armature found.")
            return {'FINISHED'}
        tris_count = 0

        for mesh in meshes_obj:
            triangulate_mesh(mesh)
            if context.scene.decimation_remove_doubles:
                remove_doubles(mesh, 0.00001)
            tris_count += get_tricount(mesh.data.polygons)
            add_shapekey(mesh, 'Tuxedo Basis', False)
    
        
        decimation = 1. + ((tuxedo_max_tris - tris_count) / tris_count)
        
        print("Decimation total: " + str(decimation))
        if decimation >= 1:
            
            decimated_a_mesh = False
            for mesh in meshes_obj:
                tris = get_tricount(mesh)
                if tris > self.max_single_mesh_tris:
                    decimation = 1. + ((self.max_single_mesh_tris - tris) / tris)
                    print("Decimation to reduce mesh "+mesh.name+"less than max tris per mesh: " + str(decimation))
                    self.extra_decimation_weights(context, animation_weighting, mesh, armature, animation_weighting_factor, decimation)
                    decimated_a_mesh = True
                
            
            if not decimated_a_mesh:
                self.report({'INFO'}, "No Decimation needed.")
                return {'FINISHED'}
            else:
                self.report({'INFO'}, "Decimated some meshes that went over the individual mesh polygon limit of " + str(self.max_single_mesh_tris))
        else:
            
            if tris_count == 0:
                self.report({'INFO'}, "No tris found.")
                return {'FINISHED'}
            elif decimation <= 0:
                self.report({'INFO'}, "Can't reach target decimation level.")
                return {'FINISHED'}
            for mesh in meshes_obj:
                tris = get_tricount(mesh)
                
                newdecimation = decimation if not ( math.ceil(tris*decimation) > self.max_single_mesh_tris) else (1. + ((self.max_single_mesh_tris - tris) / tris))
                
                self.extra_decimation_weights(context, animation_weighting, mesh, armature, animation_weighting_factor, newdecimation)
        
        
            
        return {'FINISHED'}

    def extra_decimation_weights(self, context, animation_weighting, mesh, armature, animation_weighting_factor, decimation):
        tris = get_tricount(mesh)
        if animation_weighting:
            newweights = self.get_animation_weighting(context, mesh, armature)

            context.view_layer.objects.active = mesh
            bpy.ops.object.vertex_group_add()
            mesh.vertex_groups[-1].name = "Tuxedo Animation"
            for idx, weight in newweights.items():
                mesh.vertex_groups[-1].add([idx], weight, "REPLACE")


        context.view_layer.objects.active = mesh
        # Smart
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="SELECT")

        # TODO: Fix decimation calculation when pinning seams
        # TODO: Add ability to explicitly include/exclude vertices from decimation. So you
        # can manually preserve loops
        if self.preserve_seams:
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.uv.seams_from_islands()

            # select all seams
            bpy.ops.object.mode_set(mode='OBJECT')
            me = mesh.data
            for edge in me.edges:
                if edge.use_seam:
                    edge.select = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action="INVERT")
        if animation_weighting:
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode='OBJECT')
            me = mesh.data
            vgroup_idx = mesh.vertex_groups["Tuxedo Animation"].index
            weight_dict = {vertex.index: group.weight for vertex in me.vertices for group in vertex.groups if group.group == vgroup_idx}
            # We de-select a_w_f worth of polygons, so the remaining decimation must be done in decimation/(1-a_w_f) polys
            selected_verts = sorted([v for v in me.vertices], key=lambda v: 0 - weight_dict.get(v.index, 0.0))[0:int(decimation * tris * animation_weighting_factor)]
            for v in selected_verts:
                v.select = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action="INVERT")



        effective_ratio = decimation if not animation_weighting else (decimation * (1-animation_weighting_factor))
        bpy.ops.mesh.decimate(ratio=effective_ratio,
                              #use_vertex_group=animation_weighting,
                              #vertex_group_factor=animation_weighting_factor,
                              #invert_vertex_group=True,
                              use_symmetry=True,
                              symmetry_axis='X')
        bpy.ops.object.mode_set(mode='OBJECT')

        if has_shapekeys(mesh):
            for idx in range(1, len(mesh.data.shape_keys.key_blocks) - 1):
                mesh.active_shape_key_index = idx
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.blend_from_shape(shape="Tuxedo Basis", blend=-1.0, add=True)
                bpy.ops.object.mode_set(mode='OBJECT')
            mesh.shape_key_remove(key=mesh.data.shape_keys.key_blocks["Tuxedo Basis"])
            mesh.active_shape_key_index = 0


    def get_animation_weighting(self, context, mesh, armature):
        print("Performing animation weighting for {}".format(mesh.name))
        # Weight by multiplied bone weights for every pair of bones.
        # This is O(n*m^2) for n verts and m bones, generally runs relatively quickly.
        # bones_with_children = {bone.parent.name for bone in armature.data.bones if bone.parent}
        valid_vgroup_idxes = {group.index for group in mesh.vertex_groups
                              if group.name in armature.data.bones and group.name in armature.data.bones}
        weights = dict()
        for vertex in mesh.data.vertices:
            for w1 in vertex.groups:
                if w1.weight < 0.001:
                    continue
                if w1.group not in valid_vgroup_idxes:
                    continue
                for w2 in vertex.groups:
                    if w2.weight < 0.001:
                        continue
                    if w2.group not in valid_vgroup_idxes:
                        continue
                    if w2.group != w1.group:
                        # Weight [vgroup * vgroup] for index = <mult>
                        if (w1.group, w2.group) not in weights:
                            weights[(w1.group, w2.group)] = dict()
                        weights[(w1.group, w2.group)][vertex.index] = w1.weight * w2.weight

        # Normalize per vertex group pair
        normalizedweights = dict()
        for pair, weighting in weights.items():
            m_min = 1
            m_max = 0
            for _, weight in weighting.items():
                m_min = min(m_min, weight)
                m_max = max(m_max, weight)

            if pair not in normalizedweights:
                normalizedweights[pair] = dict()
            for v_index, weight in weighting.items():
                try:
                    normalizedweights[pair][v_index] = (weight - m_min) / (m_max - m_min)
                except ZeroDivisionError:
                    normalizedweights[pair][v_index] = weight

        newweights = dict()
        for pair, weighting in normalizedweights.items():
            for v_index, weight in weighting.items():
                try:
                    newweights[v_index] = max(newweights[v_index], weight)
                except KeyError:
                    newweights[v_index] = weight

        if context.scene.decimation_animation_weighting_include_shapekeys:
            s_weights = dict()

            # Weight by relative shape key movement. This is kind of slow, but not too bad. It's O(n*m) for n verts and m shape keys,
            # but shape keys contain every vert (not just the ones they impact)
            # For shape key in shape keys:
            if mesh.data.shape_keys is not None:
                for key_block in mesh.data.shape_keys.key_blocks[1:]:
                    # use same ignore list as the ones we clean up with cleanup_shapekeys
                    if key_block.name[-4:] == "_old" or key_block.name[-11:] == " - Reverted" or key_block.name[-5:] == "_bake":
                        continue
                    basis = mesh.data.shape_keys.key_blocks[0]
                    s_weights[key_block.name] = dict()

                    for idx, vert in enumerate(key_block.data):
                        s_weights[key_block.name][idx] = math.sqrt(math.pow(basis.data[idx].co[0] - vert.co[0], 2.0) +
                                                                   math.pow(basis.data[idx].co[1] - vert.co[1], 2.0) +
                                                                   math.pow(basis.data[idx].co[2] - vert.co[2], 2.0))

            # normalize min/max vert movement
            s_normalizedweights = dict()
            for keyname, weighting in s_weights.items():
                m_min = math.inf
                m_max = 0
                for _, weight in weighting.items():
                    m_min = min(m_min, weight)
                    m_max = max(m_max, weight)

                if keyname not in s_normalizedweights:
                    s_normalizedweights[keyname] = dict()
                for v_index, weight in weighting.items():
                    try:
                        s_normalizedweights[keyname][v_index] = (weight - m_min) / (m_max - m_min)
                    except ZeroDivisionError:
                        s_normalizedweights[keyname][v_index] = weight

            # find max normalized movement over all shape keys
            for pair, weighting in s_normalizedweights.items():
                for v_index, weight in weighting.items():
                    try:
                        newweights[v_index] = max(newweights[v_index], weight)
                    except KeyError:
                        newweights[v_index] = weight

        return newweights

class GenerateTwistBones(bpy.types.Operator):
    bl_idname = 'tuxedo.generate_twist_bones'
    bl_label = "Generate Twist Bones"
    bl_description = "Attempt to generate twistbones for the selected bones"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if not get_armature(context):
            return False
        return context.selected_editable_bones

    def execute(self, context):
        context.object.data.use_mirror_x = False
        context.object.use_mesh_mirror_x = False
        context.object.pose.use_mirror_x = False
        generate_upper = context.scene.generate_twistbones_upper
        armature = context.object
        # For each bone...
        bone_pairs = []
        twist_locations = dict()
        editable_bone_names = [bone.name for bone in context.selected_editable_bones]
        for bone_name in editable_bone_names:
            # Add '<bone>_Twist' and move the head halfway to the tail
            bone = armature.data.edit_bones[bone_name]
            if not generate_upper:
                twist_bone = armature.data.edit_bones.new('~' + bone.name + "_Twist")
                twist_bone.tail = bone.tail
                twist_bone.head[:] = [(bone.head[i] + bone.tail[i]) / 2 for i in range(3)]
                twist_locations[twist_bone.name] = (twist_bone.head[:], twist_bone.tail[:])
            else:
                twist_bone = armature.data.edit_bones.new('~' + bone.name + "_UpperTwist")
                twist_bone.tail[:] = [(bone.head[i] + bone.tail[i]) / 2 for i in range(3)]
                twist_bone.head = bone.head
                twist_locations[twist_bone.name] = (twist_bone.tail[:], twist_bone.head[:])
            twist_bone.parent = bone

            bone_pairs.append((bone.name, twist_bone.name))

        bpy.ops.object.mode_set(mode='OBJECT')
        for bone_name, twist_bone_name in bone_pairs:
            twist_bone_head_tail = twist_locations[twist_bone_name]
            print(twist_bone_head_tail[0])
            print(twist_bone_head_tail[1])
            for mesh in get_meshes_objects(context, armature_name=armature.name):
                if bone_name not in mesh.vertex_groups:
                    continue

                context.view_layer.objects.active = mesh
                context.object.data.use_mirror_vertex_groups = False
                context.object.data.use_mirror_x = False
                context.object.use_mesh_mirror_x = False

                mesh.vertex_groups.new(name=twist_bone_name)

                # twist bone weights are a linear(?) gradient from head to tail, 0-1 * orig weight
                group_idx = mesh.vertex_groups[bone_name].index
                for vertex in mesh.data.vertices:
                    if any(group.group == group_idx for group in vertex.groups):
                        # calculate

                        _, dist = intersect_point_line(vertex.co, twist_bone_head_tail[0], twist_bone_head_tail[1])
                        clamped_dist = max(0.0, min(1.0, dist))
                        # orig bone weights are their original weight minus the twist weight
                        twist_weight = mesh.vertex_groups[bone_name].weight(vertex.index) * clamped_dist
                        untwist_weight = mesh.vertex_groups[bone_name].weight(vertex.index) * (1.0 - clamped_dist)
                        mesh.vertex_groups[twist_bone_name].add([vertex.index], twist_weight, "REPLACE")
                        mesh.vertex_groups[bone_name].add([vertex.index], untwist_weight, "REPLACE")

        self.report({'INFO'}, t('RemoveConstraints.success'))
        return {'FINISHED'}

class OptimizeStaticShapekeys(bpy.types.Operator):
    bl_idname = 'tuxedo.optimize_static_shapekeys'
    bl_label = 'Optimize Static Shapekeys'
    bl_description = "Move all shapekey-affected geometry into its own mesh, significantly decreasing GPU cost"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            return True

        meshes = get_meshes_objects(context)
        return meshes

    def execute(self, context):
        objs = [context.active_object]
        if not objs[0] or (objs[0] and (objs[0].type != 'MESH' or objs[0].data.shape_keys is None)):
            bpy.ops.mesh.select_all(action="DESELECT")
            meshes = get_meshes_objects(context)
            if len(meshes) == 0:
                return {'FINISHED'}
            objs = meshes

        if len([obj for obj in objs if obj.type == 'MESH']) > 1:
            self.report({'ERROR'}, "Meshes must first be combined for this to be beneficial.")

        for mesh in objs:
            if mesh.type == 'MESH' and mesh.data.shape_keys is not None:
                context.view_layer.objects.active = mesh

                # Ensure auto-smooth is enabled, set custom normals from faces
                if not mesh.data.use_auto_smooth:
                    mesh.data.use_auto_smooth = True
                    mesh.data.auto_smooth_angle = 3.1416
                # TODO: if autosmooth is already enabled, set sharp from edges?

                if not mesh.data.has_custom_normals:
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type="VERT")
                    bpy.ops.mesh.select_all(action='SELECT')
                    # TODO: un-smooth objects aren't handled correctly. A workaround is to run 'split
                    # normals' on all un-smooth objects before baking
                    bpy.ops.mesh.set_normals_from_faces(keep_sharp=True)

                # Separate non-animating
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type="VERT")
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                for key_block in mesh.data.shape_keys.key_blocks[1:]:
                    basis = mesh.data.shape_keys.key_blocks[0]

                    for idx, vert in enumerate(key_block.data):
                        if (math.sqrt(math.pow(basis.data[idx].co[0] - vert.co[0], 2.0) +
                            math.pow(basis.data[idx].co[1] - vert.co[1], 2.0) +
                            math.pow(basis.data[idx].co[2] - vert.co[2], 2.0)) > 0.0001):
                            mesh.data.vertices[idx].select = True

                if not all(v.select for v in mesh.data.vertices):
                    if any(v.select for v in mesh.data.vertices):
                        # Some affected, separate
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_more()
                        bpy.ops.mesh.split()  # required or custom normals aren't preserved
                        bpy.ops.mesh.separate(type='SELECTED')
                        bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.context.object.active_shape_key_index = 0
                    mesh.name = "Static"
                    mesh['tuxedoForcedExportName'] = "Static"
                    # remove all shape keys for 'Static'
                    bpy.ops.object.shape_key_remove(all=True)

        self.report({'INFO'}, "Separation complete.")
        return {'FINISHED'}


class TwistTutorialButton(bpy.types.Operator):
    bl_idname = 'tuxedo.twist_tutorial'
    bl_label = "Twistbones Tutorial"
    bl_description = "This will open a basic tutorial on how to setup and use these constraints. You can skip to the Unity section."
    bl_options = {'INTERNAL'}

    def execute(self, context):
        webbrowser.open("https://github.com/feilen/tuxedo-blender-plugin/wiki/5-Minute-Twistbones")
        return {'FINISHED'}

def get_tricount(obj):
    # Triangulates with Bmesh to avoid messing with the original geometry
    bmesh_mesh = bmesh.new()
    bmesh_mesh.from_mesh(obj.data)

    bmesh.ops.triangulate(bmesh_mesh, faces=bmesh_mesh.faces[:])
    return len(bmesh_mesh.faces)


class ConvertToSecondlifeButton(bpy.types.Operator):
    bl_idname = 'tuxedo.convert_to_secondlife'
    bl_label = 'Convert Bones To Second Life'
    bl_description = 'Converts all main bone names to second life.' \
                     '\nMake sure your model has the standard bone names from after using Fix Model'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    armature_name: bpy.props.StringProperty(
        default=''
    )

    @classmethod
    def poll(cls, context):
        if not get_armature(context):
            return False
        return True

    def execute(self, context):
        armature = get_armature(context, self.armature_name)

        translate_bone_fails = 0
        untranslated_bones = set()

        reverse_bone_lookup = dict()
        for (preferred_name, name_list) in bone_names.items():
            for name in name_list:
                reverse_bone_lookup[name] = preferred_name

        sl_translations = {
            'hips': "mPelvis",
            'spine': "mTorso",
            'chest': "mChest",
            'neck': "mNeck",
            'head': "mHead",
            # SL also specifies 'mSkull', generate by averaging coords of mEyeLeft and mEyeRight
            'left_eye': "mEyeLeft",
            'right_eye': "mEyeRight",
            'right_leg': "mHipRight",
            'right_knee': "mKneeRight",
            'right_ankle': "mAnkleRight",
            'right_toe': 'mToeRight',
            'right_shoulder': "mCollarRight",
            'right_arm': "mShoulderRight",
            'right_elbow': "mElbowRight",
            'right_wrist': "mWristRight",
            'left_leg': "mHipLeft",
            'left_knee': "mKneeLeft",
            'left_ankle': "mAnkleLeft",
            'left_toe': 'mToeLeft',
            'left_shoulder': "mCollarLeft",
            'left_arm': "mShoulderLeft",
            'left_elbow': "mElbowLeft",
            'left_wrist': "mWristLeft"
            #'right_foot': "mFootRight",
            #'left_foot': "mFootLeft",
            # Our translation names any "foot" as "ankle". Best approach is to subdivide toe and rename the upper as foot
            # TODO: if we only have ankle and toe, subdivide toe and rename original to foot
        }

        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')
        old_mirror_setting = context.object.data.use_mirror_x
        context.object.data.use_mirror_x = False

        bpy.ops.object.mode_set(mode='OBJECT')
        for bone in armature.data.bones:
            if simplify_bonename(bone.name) in reverse_bone_lookup and reverse_bone_lookup[simplify_bonename(bone.name)] in sl_translations:
                bone.name = sl_translations[reverse_bone_lookup[simplify_bonename(bone.name)]]
            else:
                untranslated_bones.add(bone.name)
                translate_bone_fails += 1

        # Better foot setup
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        for bone in context.visible_bones:
            if bone.name == "mToeLeft" or bone.name == "mToeRight":
                bone.select = True
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        if context.selected_editable_bones:
            bpy.ops.armature.subdivide()
        bpy.ops.object.mode_set(mode='OBJECT')
        for bone in armature.data.bones:
            if bone.name == "mToeLeft":
                bone.name = "mFootLeft"
            if bone.name == "mToeRight":
                bone.name = "mFootRight"
        for bone in armature.data.bones:
            if bone.name == "mToeLeft.001":
                bone.name = "mToeLeft"
            if bone.name == "mToeRight.001":
                bone.name = "mToeRight"

        # Merge unused or SL rejects
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        for bone in context.visible_bones:
            bone.select = bone.name in untranslated_bones
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        print(untranslated_bones)
        if context.selected_editable_bones:
            merge_bone_weights_to_respective_parents(context, armature, [bone.name for bone in context.selected_editable_bones])

        for bone in context.visible_bones:
            bone.use_connect = False

        for bone in context.visible_bones:
            bone.tail[:] = bone.head[:]
            bone.tail[0] = bone.head[0] + 0.1
            # TODO: clear rolls

        context.object.data.use_mirror_x = old_mirror_setting
        bpy.ops.object.mode_set(mode='OBJECT')

        if translate_bone_fails > 0:
            self.report({'INFO'}, f"Failed to translate {translate_bone_fails} bones! They will be merged to their parent bones.")
        else:
            self.report({'INFO'}, 'Translated all bones!')

        return {'FINISHED'}


# Code below Stolen from Cats Blender Plugin File "common.py", Sorry! But tbf we don't want depenencies. Full credit to the cats blender team!
# Btw the code it's stolen from is GPL

def delete(obj):
    if obj.parent:
        for child in obj.children:
            child.parent = obj.parent

    objs = bpy.data.objects
    objs.remove(objs[obj.name], do_unlink=True)

class PoseToRest(bpy.types.Operator):
    bl_idname = 'tuxedo.pose_to_rest'
    bl_label = "apply pose as rest pose"
    bl_description = "Applies armature's pose as rest pose safely, taking shapekeys into account"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    armature_name: bpy.props.StringProperty(
        default=''
    )
    
    @classmethod
    def poll(cls, context):
        armature = get_armature(context)
        return armature and armature.mode == 'POSE'

    def execute(self, context):
    
        armature_obj = get_armature(context,self.armature_name)
        mesh_objs = get_meshes_objects(context,armature_name=armature_obj.name)
        for mesh_obj in mesh_objs:
            me = mesh_obj.data
            if me:
                if me.shape_keys and me.shape_keys.key_blocks:
                    # The mesh has shape keys
                    shape_keys = me.shape_keys
                    key_blocks = shape_keys.key_blocks
                    if len(key_blocks) == 1:
                        # The mesh only has a basis shape key, so we can remove it and then add it back afterwards
                        # Get basis shape key
                        basis_shape_key = key_blocks[0]
                        # Save the name of the basis shape key
                        original_basis_name = basis_shape_key.name
                        # Remove the basis shape key so there are now no shape keys
                        mesh_obj.shape_key_remove(basis_shape_key)
                        # Apply the pose to the mesh
                        PoseToRest.apply_armature_to_mesh_with_no_shape_keys(armature_obj, mesh_obj)
                        # Add the basis shape key back with the same name as before
                        mesh_obj.shape_key_add(name=original_basis_name)
                    else:
                        # Apply the pose to the mesh, taking into account the shape keys
                        PoseToRest.apply_armature_to_mesh_with_shape_keys(armature_obj, mesh_obj, context.scene)
                else:
                    # The mesh doesn't have shape keys, so we can easily apply the pose to the mesh
                    PoseToRest.apply_armature_to_mesh_with_no_shape_keys(armature_obj, mesh_obj)
        # Once the mesh and shape keys (if any) have been applied, the last step is to apply the current pose of the
        # bones as the new rest pose.
        #
        # From the poll function, armature_obj must already be in pose mode, but it's possible it might not be the
        # active object e.g., the user has multiple armatures opened in pose mode, but a different armature is currently
        # active. We can use an operator override to tell the operator to treat armature_obj as if it's the active
        # object even if it's not, skipping the need to actually set armature_obj as the active object.
        bpy.ops.pose.armature_apply({'active_object': armature_obj})

        # Stop pose mode after operation
        armature = get_armature(context,self.armature_name)
        context.view_layer.objects.active = armature

        # Make all objects visible
        for collection in bpy.data.collections:
            for object in collection.all_objects[:]:
                object.hide_set(False)

        for pb in armature.data.bones:
            pb.hide = False
            pb.select = True

        bpy.ops.pose.rot_clear()
        bpy.ops.pose.scale_clear()
        bpy.ops.pose.transforms_clear()

        for pb in armature.data.bones:
            pb.select = False

        armature = get_armature(context,self.armature_name)
        # armature.data.pose_position = 'REST'

        for mesh in get_meshes_objects(context,armature_name=self.armature_name):
            if has_shapekeys(mesh):
                for shape_key in mesh.data.shape_keys.key_blocks:
                    shape_key.value = 0




        self.report({'INFO'}, t('PoseToRest.success'))
        return {'FINISHED'}

    @staticmethod
    def apply_armature_to_mesh_with_no_shape_keys(armature_obj, mesh_obj):
        armature_mod = mesh_obj.modifiers.new('PoseToRest', 'ARMATURE')
        armature_mod.object = armature_obj
        # In the unlikely case that there was already a modifier with the same name as the new modifier, the new
        # modifier will have ended up with a different name
        mod_name = armature_mod.name
        # Context override to let us run the modifier operators on mesh_obj, even if it's not the active object
        context_override = {'object': mesh_obj}
        # Moving the modifier to the first index will prevent an Info message about the applied modifier not being
        # first and potentially having unexpected results.
        if bpy.app.version >= (2, 90, 0):
            # modifier_move_to_index was added in Blender 2.90
            bpy.ops.object.modifier_move_to_index(context_override, modifier=mod_name, index=0)
        else:
            # The newly created modifier will be at the bottom of the list
            armature_mod_index = len(mesh_obj.modifiers) - 1
            # Move the modifier up until it's at the top of the list
            for _ in range(armature_mod_index):
                bpy.ops.object.modifier_move_up(context_override, modifier=mod_name)
        bpy.ops.object.modifier_apply(context_override, modifier=mod_name)

    @staticmethod
    def apply_armature_to_mesh_with_shape_keys(armature_obj, mesh_obj, scene):
        # The active shape key will be changed, so save the current active index, so it can be restored afterwards
        old_active_shape_key_index = mesh_obj.active_shape_key_index

        # Shape key pinning shows the active shape key in the viewport without blending; effectively what you see when
        # in edit mode. Combined with an armature modifier, we can use this to figure out the correct positions for all
        # the shape keys.
        # Save the current value, so it can be restored afterwards.
        old_show_only_shape_key = mesh_obj.show_only_shape_key
        mesh_obj.show_only_shape_key = True

        # Temporarily remove vertex_groups from and disable mutes on shape keys because they affect pinned shape keys
        me = mesh_obj.data
        shape_key_vertex_groups = []
        shape_key_mutes = []
        key_blocks = me.shape_keys.key_blocks
        for shape_key in key_blocks:
            shape_key_vertex_groups.append(shape_key.vertex_group)
            shape_key.vertex_group = ''
            shape_key_mutes.append(shape_key.mute)
            shape_key.mute = False

        # Temporarily disable all modifiers from showing in the viewport so that they have no effect
        mods_to_reenable_viewport = []
        for mod in mesh_obj.modifiers:
            if mod.show_viewport:
                mod.show_viewport = False
                mods_to_reenable_viewport.append(mod)

        # Temporarily add a new armature modifier
        armature_mod = mesh_obj.modifiers.new('PoseToRest', 'ARMATURE')
        armature_mod.object = armature_obj

        # cos are xyz positions and get flattened when using the foreach_set/foreach_get functions, so the array length
        # will be 3 times the number of vertices
        co_length = len(me.vertices) * 3
        # We can re-use the same array over and over
        eval_verts_cos_array = np.empty(co_length, dtype=np.single)
        
        
        # depsgraph lets us evaluate objects and get their state after the effect of modifiers and shape keys
        depsgraph = None
        evaluated_mesh_obj = None

        def get_eval_cos_array():
            nonlocal depsgraph
            nonlocal evaluated_mesh_obj
            # Get the depsgraph and evaluate the mesh if we haven't done so already
            if depsgraph is None or evaluated_mesh_obj is None:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                evaluated_mesh_obj = mesh_obj.evaluated_get(depsgraph)
            else:
                # If we already have the depsgraph and evaluated mesh, in order for the change to the active shape
                # key to take effect, the depsgraph has to be updated
                depsgraph.update()
            # Get the cos of the vertices from the evaluated mesh
            evaluated_mesh_obj.data.vertices.foreach_get('co', eval_verts_cos_array)
            return eval_verts_cos_array

        for i, shape_key in enumerate(key_blocks):
            # As shape key pinning is enabled, when we change the active shape key, it will change the state of the mesh
            mesh_obj.active_shape_key_index = i
            # The cos of the vertices of the evaluated mesh include the effect of the pinned shape key and all the
            # modifiers (in this case, only the armature modifier we added since all the other modifiers are disabled in
            # the viewport).
            # This combination gives the same effect as if we'd applied the armature modifier to a mesh with the same
            # shape as the active shape key, so we can simply set the shape key to the evaluated mesh position.
            #
            # Get the evaluated cos
            evaluated_cos = get_eval_cos_array()
            # And set the shape key to those same cos
            shape_key.data.foreach_set('co', evaluated_cos)
            # If it's the basis shape key, we also have to set the mesh vertices to match, otherwise the two will be
            # desynced until Edit mode has been entered and exited, which can cause odd behaviour when creating shape
            # keys with from_mix=False or when removing all shape keys.
            if i == 0:
                mesh_obj.data.vertices.foreach_set('co', evaluated_cos)

        # Restore temporarily changed attributes and remove the added armature modifier
        for mod in mods_to_reenable_viewport:
            mod.show_viewport = True
        mesh_obj.modifiers.remove(armature_mod)
        for shape_key, vertex_group, mute in zip(me.shape_keys.key_blocks, shape_key_vertex_groups, shape_key_mutes):
            shape_key.vertex_group = vertex_group
            shape_key.mute = mute
        mesh_obj.active_shape_key_index = old_active_shape_key_index
        mesh_obj.show_only_shape_key = old_show_only_shape_key
        
#end cats blender plugin code block






######### GMOD SCRIPTS #########

def Set_Mode(context, mode):
    if context.view_layer.objects.active is None:
        context.view_layer.objects.active = context.view_layer.objects[0]
        bpy.ops.object.mode_set(mode=mode,toggle=False)
    else:
        bpy.ops.object.mode_set(mode=mode,toggle=False)

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
            
def Destroy_By_Name(context, name):
    bpy.ops.object.select_all(action='DESELECT')
    destroyed_object = bpy.data.objects.get(name)
    context.view_layer.objects.active = destroyed_object
    destroyed_object.select_set(True)
    bpy.ops.object.delete(use_global=False)
    
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

        
    
# @989onan - I'm sorry for the mess below, but at least I refactored it since this is new place for this code. The most permanent solution is a temporary one.


class ConvertToValveButton(bpy.types.Operator):
    bl_idname = 'tuxedo.convert_to_valve'
    bl_label = 'Convert Bones To Valve'
    bl_description = 'Converts all main bone names to default valve bone names.' \
                     '\nMake sure your model has the standard bone names from after using Fix Model'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    armature_name: bpy.props.StringProperty(
        default=''
    )

    @classmethod

    def poll(cls, context):
        if not get_armature(context):
            return False
        return True

    def execute(self, context):
        translate_bone_fails = 0
        if self.armature_name == "":
            armature = get_armature(context,self.armature_name)
        else:
            armature = bpy.data.objects.get(self.armature_name)

        reverse_bone_lookup = dict()
        for (preferred_name, name_list) in bone_names.items():
            for name in name_list:
                reverse_bone_lookup[name] = preferred_name

        valve_translations = {
            'hips': "ValveBiped.Bip01_Pelvis",
            'spine': "ValveBiped.Bip01_Spine",
            'chest': "ValveBiped.Bip01_Spine1",
            'upper_chest': "ValveBiped.Bip01_Spine4",
            'neck': "ValveBiped.Bip01_Neck1",
            'head': "ValveBiped.Bip01_Head1", #head1 is on purpose.
            'left_leg': "ValveBiped.Bip01_L_Thigh",
            'left_knee': "ValveBiped.Bip01_L_Calf",
            'left_ankle': "ValveBiped.Bip01_L_Foot",
            'left_toe': "ValveBiped.Bip01_L_Toe0",
            'right_leg': "ValveBiped.Bip01_R_Thigh",
            'right_knee': "ValveBiped.Bip01_R_Calf",
            'right_ankle': "ValveBiped.Bip01_R_Foot",
            'right_toe': "ValveBiped.Bip01_R_Toe0",
            'left_shoulder': "ValveBiped.Bip01_L_Clavicle",
            'left_arm': "ValveBiped.Bip01_L_UpperArm",
            'left_elbow': "ValveBiped.Bip01_L_Forearm",
            'left_wrist': "ValveBiped.Bip01_L_Hand",
            'right_shoulder': "ValveBiped.Bip01_R_Clavicle",
            'right_arm': "ValveBiped.Bip01_R_UpperArm",
            'right_elbow': "ValveBiped.Bip01_R_Forearm",
            'right_wrist': "ValveBiped.Bip01_R_Hand",
            #need finger bones for Gmod Conversion Script
            'pinkie_1_l': "ValveBiped.Bip01_L_Finger4",
            'pinkie_2_l': "ValveBiped.Bip01_L_Finger41",
            'pinkie_3_l': "ValveBiped.Bip01_L_Finger42",
            'ring_1_l': "ValveBiped.Bip01_L_Finger3",
            'ring_2_l': "ValveBiped.Bip01_L_Finger31",
            'ring_3_l': "ValveBiped.Bip01_L_Finger32",
            'middle_1_l': "ValveBiped.Bip01_L_Finger2",
            'middle_2_l': "ValveBiped.Bip01_L_Finger21",
            'middle_3_l': "ValveBiped.Bip01_L_Finger22",
            'index_1_l': "ValveBiped.Bip01_L_Finger1",
            'index_2_l': "ValveBiped.Bip01_L_Finger11",
            'index_3_l': "ValveBiped.Bip01_L_Finger12",
            'thumb_1_l': "ValveBiped.Bip01_L_Finger0",
            'thumb_2_l': "ValveBiped.Bip01_L_Finger01",
            'thumb_3_l': "ValveBiped.Bip01_L_Finger02",

            'pinkie_1_r': "ValveBiped.Bip01_R_Finger4",
            'pinkie_2_r': "ValveBiped.Bip01_R_Finger41",
            'pinkie_3_r': "ValveBiped.Bip01_R_Finger42",
            'ring_1_r': "ValveBiped.Bip01_R_Finger3",
            'ring_2_r': "ValveBiped.Bip01_R_Finger31",
            'ring_3_r': "ValveBiped.Bip01_R_Finger32",
            'middle_1_r': "ValveBiped.Bip01_R_Finger2",
            'middle_2_r': "ValveBiped.Bip01_R_Finger21",
            'middle_3_r': "ValveBiped.Bip01_R_Finger22",
            'index_1_r': "ValveBiped.Bip01_R_Finger1",
            'index_2_r': "ValveBiped.Bip01_R_Finger11",
            'index_3_r': "ValveBiped.Bip01_R_Finger12",
            'thumb_1_r': "ValveBiped.Bip01_R_Finger0",
            'thumb_2_r': "ValveBiped.Bip01_R_Finger01",
            'thumb_3_r': "ValveBiped.Bip01_R_Finger02"
        }
        
        
        #set bones to standard names first
        for bone in armature.data.bones:
            if simplify_bonename(bone.name) in reverse_bone_lookup and reverse_bone_lookup[simplify_bonename(bone.name)] in valve_translations:
                bone.name = reverse_bone_lookup[simplify_bonename(bone.name)]
            else:
                translate_bone_fails += 1
        
        #this is to fix fingers that start with <fingerbonename>_0_l instead of <fingerbonename>_1_l:
        for bone in armature.data.bones:
            if bone.name.lower() in ["index_0_l","thumb_0_l","middle_0_l","ring_0_l","pinkie_0_l","index_0_r","thumb_0_r","middle_0_r","ring_0_r","pinkie_0_r"]:
                #shift bone name numbers down by 1 towards the end to fix hands, unless there are 4 finger bones, which would indicate fingers in the palms.
                if not armature.data.bones.get(bone.name.lower().replace("0","3")):
                    print("finger chain "+bone.name.lower()+" started with a 0 bone and only has 3 bones, shifting the chain of bones so your hands work!")
                    try:
                        armature.data.bones[bone.name.lower().replace("0","2")].name = bone.name.lower().replace("0","3")
                    except:
                        pass
                    try:
                        armature.data.bones[bone.name.lower().replace("0","1")].name = bone.name.lower().replace("0","2")
                    except:
                        pass
                    bone.name = bone.name.lower().replace("0","1")
                else:
                    print("It is assumed that the finger bone "+bone.name.lower()+" is a bone in your palm, since the total length of finger bones in this finger is 4.")
                    print("You may wanna delete the bone that matches the description of "+bone.name.lower()+" when running this script again, if you're not gonna use it in Gmod for bone posing!")
        
        #finally translate bone names to Source.
        for bone in armature.data.bones:
            if bone.name in valve_translations:
                bone.name = valve_translations[bone.name]
        
        
        if translate_bone_fails > 0:
            self.report({'INFO'}, f"Error! Failed to translate {translate_bone_fails} bones! Make sure your model has standard bone names!")

        self.report({'INFO'}, 'Connected all bones!')
        return {'FINISHED'}



class ExportGmodPlayermodel(bpy.types.Operator):
    bl_idname = "tuxedo.export_gmod_addon"
    bl_label = "Export Gmod Addon"
    bl_description = "Export as Gmod Playermodel Addon to your addons and make GMA beside Blender file. May not always work."
    bl_options = {'INTERNAL'}

    steam_library_path: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    gmod_model_name: bpy.props.StringProperty(default = "Missing No")
    platform_name: bpy.props.StringProperty(default = "Garrys Mod")
    armature_name: bpy.props.StringProperty(default = "")

    def execute(self, context):
        print("===============START GMOD EXPORT PROCESS===============")

        model_name = self.gmod_model_name
        platform_name = self.platform_name
        sanitized_model_name = ""
        offical_model_name = ""

        try:
            Set_Mode(context, "OBJECT")
        except:
            pass
        # this is feilen's code 
        def sanitized_name(orig_name):
                #sanitizing name since everything needs to be simple characters and "_"'s
                sanitized = ""
                for i in orig_name.lower():
                    if i.isalnum() or i == "_":
                        sanitized += i
                    else:
                        sanitized += "_"
                return sanitized
        sanitized_model_name = sanitized_name(model_name)
        sanitized_platform_name = sanitized_name(platform_name)
        #feilen's code ends here
        
        
        #for name that appears in playermodel selection screen.
        for i in model_name:
            if i.isalnum() or i == "_" or i == " ":
                offical_model_name += i
            else:
                offical_model_name += "_"

        print("sanitized model name:"+sanitized_model_name)
        print("Playermodel Selection Menu Name"+offical_model_name)
        print("armature name:"+self.armature_name)

        self.steam_library_path = self.steam_library_path.replace("\\\\","/").replace("\\","/")
        print("Fixed library path name: \""+self.steam_library_path+"\"")

        steam_librarypath = self.steam_library_path+"steamapps/common/GarrysMod" #add the rest onto it so that we can get garrysmod only.
        addonpath = steam_librarypath+"/garrysmod/addons/"+sanitized_model_name+"_playermodel/"
        
        print("Deleting old DefineBones.qci")
        if os.path.exists(bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/DefineBones.qci")):
            os.remove(bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/DefineBones.qci"))
            print("DefineBones.qci deleted! Soon to be replaced.")
        
        
        try:
            Set_Mode(context, "OBJECT")
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        
        
        #TODO: Ask the user to add an upper chest bone instead - @989onan
        #print("checking if model has an upper chest or not.")
        #context.view_layer.objects.active = armature 
        #Set_Mode(context, "OBJECT")
        #bpy.ops.object.select_all(action='DESELECT')
        #Set_Mode(context, "EDIT")
        #if not ("ValveBiped.Bip01_Spine4" in armature.data.edit_bones):
        #    print("Model does not have upper chest, auto generating...")
        #    chest_bone = armature.data.edit_bones["ValveBiped.Bip01_Spine1"]
        #    bpy.ops.armature.select_all(action='DESELECT')
        #    chest_bone.select_head = True
        #    chest_bone.select_tail = True
        #    chest_bone.select = True
        #    # There needs to be a parenting thing here, since subdivided bones keep the parents to the original bone
        #    chest_bone.children[0].name = "ValveBiped.Bip01_Spine4"
        #    bpy.ops.armature.subdivide()
        #    bpy.ops.armature.select_all(action='DESELECT')
        armature = get_armature(context,self.armature_name)
        context.view_layer.objects.active = armature

        print("putting armature and objects under reference collection")
        #putting objects and armature under a better collection.
        refcoll_list = [obj for obj in armature.children]
        refcoll_list.append(armature)
        refcoll = Move_to_New_Or_Existing_Collection(context, sanitized_model_name+"_ref", objects_alternative_list = refcoll_list) #put armature and children into alt object list
                    
                    
        print("marking which models toggled off by default, and deleting always inactive objects for body groups.")
        hidden_by_default_bodygroups = []
        do_not_toggle_bodygroups = []
        always_hidden_garbage = []
        context.view_layer.objects.active = armature
        for mesh in refcoll.objects:
            if mesh.type == "MESH":
                if mesh.hide_viewport and mesh.hide_get():
                    always_hidden_garbage.append(mesh.name)
                    continue
                if mesh.hide_viewport:
                    do_not_toggle_bodygroups.append(mesh.name)
                    print("mesh \""+mesh.name+"\" hidden with monitor icon, it will always be on and untoggleable!")
                if mesh.hide_get():
                    hidden_by_default_bodygroups.append(mesh.name)
                    print("mesh \""+mesh.name+"\" hidden with eyeball icon, it will be toggled off in gmod by default!")
        
        print("deleting always hidden meshes")
        for obj in always_hidden_garbage:
            print("mesh \""+obj.name+"\" always hidden, deleting!")
            Destroy_By_Name(context, obj)
        
        for obj in do_not_toggle_bodygroups:
            mesh = bpy.data.objects.get(obj)
            mesh.hide_viewport = False
        for obj in hidden_by_default_bodygroups:
            mesh = bpy.data.objects.get(obj)
            mesh.hide_set(False)
        
        
        print("translating bones. if you hit an error here please fix your model using fix model!!!!!! If you have, please ignore the error.")
        bpy.ops.tuxedo.convert_to_valve(armature_name = self.armature_name)
        
        print("testing if SMD tools exist.")
        try:
            bpy.ops.import_scene.smd('EXEC_DEFAULT',files=[{'name': "barney_reference.smd"}], append = "NEW_ARMATURE",directory=os.path.dirname(os.path.abspath(__file__))+"/assets/garrysmod/")
        except AttributeError:
            #TODO: Replace with tuxedo dialouge, since this is a pretty serious error. HIGH PRIORITY!
            #bpy.ops.cats_importer.install_source('INVOKE_DEFAULT') 
            return
            
        #clean imported stuff
        print("cleaning imported armature")
        
        #delete imported mesh
        Destroy_By_Name(context, "barney_reference")
        
        
        # move the armature to it's proper collection if it ended up outside. (somehow idk)
        barneycollection = Move_to_New_Or_Existing_Collection(context, "barney_collection", objects_alternative_list = [bpy.data.objects.get("barney_reference_skeleton")])
        
        
        #santitize material names
        for obj in refcoll.objects:
            objname = obj.name
            if bpy.data.objects[objname].type == "MESH":
                print("sanitizing material names for gmod for object "+objname)
                for material in bpy.data.objects[objname].material_slots:
                    mat = material.material
                    mat.name = sanitized_name(mat.name)
                if has_shapekeys(bpy.data.objects[objname]):
                    print("sanitizing shapekey names for gmod for object "+objname)
                    for shapekey in bpy.data.objects[objname].data.shape_keys.key_blocks:
                        shapekey.name = sanitized_name(shapekey.name)
            

        print("zeroing transforms and then scaling to gmod scale, then applying transforms.")
        #zero armature position, scale to gmod size, and then apply transforms
        armature.rotation_euler[0] = 0
        armature.rotation_euler[1] = 0
        armature.rotation_euler[2] = 0
        armature.location[0] = 0
        armature.location[1] = 0
        armature.location[2] = 0
        armature.scale[0] = 52.4934383202 #meters to hammer units
        armature.scale[1] = 52.4934383202 #meters to hammer units
        armature.scale[2] = 52.4934383202 #meters to hammer units
        #apply transforms of all objects in ref collection
        Set_Mode(context,"OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in refcoll.objects:
            obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        print("getting meshes in ref collection")
                
        parentobj, body_armature = Get_Meshes_And_Armature(context, refcoll)
        
        
        if (not body_armature) or (len(parentobj) == 0):
            print('Report: Error')
            print(refcoll.name+" gmod baking failed at this point since bake result didn't have at least one armature and one mesh!")
        
        
        print("clearing bone rolls")
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature 
        Set_Mode(context, "EDIT")
        bpy.ops.armature.reveal()
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.armature.roll_clear()
        Set_Mode(context, "OBJECT")

        print("a-posing armature")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        Set_Mode(context, "POSE")
        
        bpy.ops.pose.select_all(action='SELECT')
        
        bpy.ops.pose.reveal(select=True)
        body_armature.pose.bones["ValveBiped.Bip01_L_UpperArm"].rotation_mode = "XYZ"
        body_armature.pose.bones["ValveBiped.Bip01_L_UpperArm"].rotation_euler[0] = -45
        body_armature.pose.bones["ValveBiped.Bip01_R_UpperArm"].rotation_mode = "XYZ"
        body_armature.pose.bones["ValveBiped.Bip01_R_UpperArm"].rotation_euler[0] = -45
        print("doing an apply rest pose")
        bpy.ops.tuxedo.pose_to_rest()
        Set_Mode(context, "OBJECT")

        update_viewport()

        print("grabbing barney armature")
        barney_armature = None
        barneycollection = bpy.data.collections.get("barney_collection")
        
        parentobj, barney_armature = Get_Meshes_And_Armature(context, barneycollection)
        assert(barneycollection is not None)
        assert(len(barneycollection.objects) > 0)
        
        
        print("duplicating barney armature")
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = barney_armature
        barney_armature.select_set(True)
        bpy.ops.object.duplicate({"object" : barney_armature, "selected_objects" : [barney_armature]}, linked=False)
        barney_armature = context.object
        

        def children_bone_recursive(parent_bone):
            child_bones = []
            child_bones.append(parent_bone)
            for child in parent_bone.children:
                child_bones.extend(children_bone_recursive(child))
            return child_bones

        print("positioning bones for barney armature at your armature's bones PLEASE HAVE A PELVIS BONE")
        barney_pose_bone_names = [j.name for j in children_bone_recursive(barney_armature.pose.bones["ValveBiped.Bip01_Pelvis"])] #bones are default in order of parent child.

        print("barney bone names in order of hiearchy:" +str(barney_pose_bone_names))
        armature_matrixes = dict()
        barney_armature_name = barney_armature.name
        body_armature_name = body_armature.name
        
        
        
        for barney_bone_name in barney_pose_bone_names:
            print("this is a barney bone name:" +barney_bone_name)
            Set_Mode(context, "OBJECT")
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = bpy.data.objects[body_armature_name]
            Set_Mode(context, "EDIT")
            
            try:
                obj = bpy.data.objects[barney_armature_name]
                editbone = bpy.data.objects[body_armature_name].data.edit_bones[barney_bone_name]
                bone = obj.pose.bones[barney_bone_name]
                bone.rotation_mode = "XYZ"
                newmatrix = Matrix.Translation((editbone.matrix[0][3],editbone.matrix[1][3],editbone.matrix[2][3]))
                bone.matrix = newmatrix
                bone.rotation_euler = (0,0,0)
            except Exception as e:
                print("barney bone above failed! may not exist on our armature, which is okay!")
                print(e)
        
        
        
        print("applying barney pose as rest pose")
        Set_Mode(context, "OBJECT")
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = bpy.data.objects[barney_armature_name]
        Set_Mode(context, "POSE")
        print("doing an apply rest pose")
        bpy.ops.tuxedo.pose_to_rest()
        Set_Mode(context, "OBJECT")
        
        
        print("putting barney armature bones on your model")
        merge_armature_stage_one(context, body_armature_name, barney_armature_name)
        
        
        print("fixing bones to point correct direction in order to mitigate bad bone twists. (includes thighs and jiggle bones)")
        
        
        #twisted_armature_bone_names may not be referenced because I thought it was causing issues - @989onan
        #TODO: Verify this. I probably put it back idk. This is a note for future me.
        twisted_armature = bpy.data.objects[body_armature_name]
        twisted_armature_bone_names = list(set([j.name for j in children_bone_recursive(twisted_armature.pose.bones["ValveBiped.Bip01_Pelvis"])]) - set(barney_pose_bone_names))
        
        def rotatebone(bone_name = ""):
            editing_bone = twisted_armature.data.edit_bones[bone_name]
            
            print("\""+editing_bone.name+"\" is gonna be rotated 90 degrees on the z normal axis now.")
            editing_bone.use_connect = False
            
            # changing bone length to .25 since we can't edit the bone length value directly since it's read_only.
            editing_bone.tail.x = editing_bone.head.x+(((editing_bone.tail.x-editing_bone.head.x)/editing_bone.length)*.25)
            editing_bone.tail.y = editing_bone.head.y+(((editing_bone.tail.y-editing_bone.head.y)/editing_bone.length)*.25)
            editing_bone.tail.z = editing_bone.head.z+(((editing_bone.tail.z-editing_bone.head.z)/editing_bone.length)*.25)
            
            
            
            
            editing_bone.select_head = True
            editing_bone.select_tail = True
            editing_bone.select = True
            bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
            bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z', orient_type='NORMAL')
            editing_bone.select_head = False
            editing_bone.select_tail = False
            editing_bone.select = False
        
        bpy.context.view_layer.objects.active = twisted_armature
        Set_Mode(context, "EDIT")
        bpy.ops.armature.select_all(action='DESELECT')
        leglist = {"ValveBiped.Bip01_R_Calf":"ValveBiped.Bip01_R_Foot","ValveBiped.Bip01_L_Calf":"ValveBiped.Bip01_L_Foot","ValveBiped.Bip01_R_Thigh":"ValveBiped.Bip01_R_Calf","ValveBiped.Bip01_L_Thigh":"ValveBiped.Bip01_L_Calf"}
        for bone in itertools.chain(twisted_armature_bone_names, leglist):
            if hasattr(twisted_armature.data.edit_bones[bone], "children"):
                if len(twisted_armature.data.edit_bones[bone].children) >= 1:
                    editing_bone = twisted_armature.data.edit_bones[bone]
                    target_bone = None
                    if len(twisted_armature.data.edit_bones[bone].children) > 1:
                        for bonechild in twisted_armature.data.edit_bones[bone].children:
                            if bonechild.name in barney_pose_bone_names:
                                target_bone = bonechild
                        if target_bone is None:
                            rotatebone(bone_name = bone)
                            continue
                    else:
                        target_bone = twisted_armature.data.edit_bones[bone].children[0]
                        
                        
                    
                    
                    print("\""+editing_bone.name +"\" is going to point at \""+target_bone.name+"\" on the x axis now.")
                    
                    original_length = 0.25#This causes jiggle bones issues, so we're setting it to the same length as garry's mod ones-> editing_bone.length
                    
                    bonedir = [0,0,0]
                    bonedir[0] = (target_bone.head.x - editing_bone.head.x)
                    bonedir[1] = (target_bone.head.y - editing_bone.head.y)
                    bonedir[2] = (target_bone.head.z - editing_bone.head.z)
                    
                    
                    length_dir = math.sqrt((math.pow(bonedir[0],2.0)+math.pow(bonedir[1],2.0)+math.pow(bonedir[2],2.0)))
                    if length_dir < 0.01:
                        continue
                    
                    print([(i/length_dir)*original_length for i in bonedir])
                    
                    editing_bone.tail.x = ((bonedir[0]/length_dir)*original_length)+editing_bone.head.x
                    editing_bone.tail.y = ((bonedir[1]/length_dir)*original_length)+editing_bone.head.y
                    editing_bone.tail.z = ((bonedir[2]/length_dir)*original_length)+editing_bone.head.z
                    
                    rotatebone(bone_name = bone)
                    
                else:
                    rotatebone(bone_name = bone)
            else:
                rotatebone(bone_name = bone)
            
        

        print("putting armature back under reference collection")
        Move_to_New_Or_Existing_Collection(context, refcoll.name, objects_alternative_list = [bpy.data.objects.get(body_armature_name)])
        
        update_viewport()
        
        
        print("Duplicating reference collection to make phys collection")
        physcoll = Copy_to_existing_collection(context, old_coll = refcoll, new_coll_name=sanitized_model_name+"_phys")

        print("making arms collection and copying over from reference")
        armcoll = Copy_to_existing_collection(context, old_coll = refcoll, new_coll_name=sanitized_model_name+"_arms")

        print("making phys parts")
        #bone names to make phys parts for. Max of 30 pleasee!!! Gmod cannot handle more than 30 but can do up to and including 30.
        bone_names_for_phys = [
        "ValveBiped.Bip01_L_UpperArm",
        "ValveBiped.Bip01_R_UpperArm",
        "ValveBiped.Bip01_L_Forearm",
        "ValveBiped.Bip01_R_Forearm",
        "ValveBiped.Bip01_L_Hand",
        "ValveBiped.Bip01_R_Hand",
        "ValveBiped.Bip01_L_Thigh",
        "ValveBiped.Bip01_R_Thigh",
        "ValveBiped.Bip01_L_Calf",
        "ValveBiped.Bip01_R_Calf",
        "ValveBiped.Bip01_L_Foot",
        "ValveBiped.Bip01_R_Foot",
        "ValveBiped.Bip01_Pelvis",
        "ValveBiped.Bip01_Spine",
        "ValveBiped.Bip01_Spine1",
        "ValveBiped.Bip01_Neck1",
        "ValveBiped.Bip01_Head1"
        ]
        convexobjects = dict()
        original_object_phys = None
        phys_armature = None
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in physcoll.objects:
            if obj.type == "ARMATURE":
                phys_armature = obj
            if obj.type == "MESH":
                context.view_layer.objects.active = obj
                obj.select_set(True)
                try:
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=False)
                except:
                    print("No shapekeys, skipping")
                bpy.ops.object.select_all(action='DESELECT')
        
        for obj in physcoll.objects:
            obj.select_set(True)
        bpy.ops.object.join()
        
        for obj in physcoll.objects:
            if obj.type == 'MESH':
                #deselect all objects and select our obj
                original_object_phys = obj
                #delete all bad vertex groups we are not using by merging
                Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                Set_Mode(context, "EDIT")
                bpy.ops.mesh.select_all(action='DESELECT')
                bones_to_merge_valve = []
                for index,group in enumerate(obj.vertex_groups):
                    if "tail" in group.name.lower():
                        Set_Mode(context, "OBJECT")
                        bpy.ops.object.select_all(action='DESELECT')
                        context.view_layer.objects.active = obj
                        Set_Mode(context, "EDIT")
                        bpy.ops.mesh.select_all(action='DESELECT')
                        obj.vertex_groups.active_index = index
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.object.vertex_group_remove_from()
                    elif (not (group.name in bone_names_for_phys)): # we wanna merge bones that aren't being used for physics, so we have a simplifed physics rig - @989onan
                        Set_Mode(context, "OBJECT")
                        bpy.ops.object.select_all(action='DESELECT')
                        context.view_layer.objects.active = phys_armature
                        Set_Mode(context, "EDIT")
                        bpy.ops.armature.select_all(action='DESELECT')
                        bone = phys_armature.data.edit_bones.get(group.name)
                        if bone is not None:
                            #add to select phys bone list
                            print("adding \""+bone.name+"\" bone to be merged to it's parent for phys mesh")
                            bones_to_merge_valve.append(bone.name)
                        else:
                            pass #if the group no longer has a bone who cares. usually.... <- wow this was a bad comment by past me. I meant to say groups for bones that no longer exist basically. Like trash weight data - @989onan
                Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                
                #use tuxedo function to yeet dem bones on phys mesh.
                context.view_layer.objects.active = phys_armature
                Set_Mode(context, "EDIT")
                merge_bone_weights_to_respective_parents(context, phys_armature, bones_to_merge_valve)
                Set_Mode(context, "OBJECT")
                
                #separating into seperate phys objects to join later.
                Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                Set_Mode(context, "EDIT")
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.vertex_group_normalize()
                bpy.ops.object.vertex_group_clean(group_select_mode='ALL', keep_single=True, limit=0.001)
                bpy.ops.object.vertex_group_quantize(group_select_mode='ALL', steps=1)#this quantize limit is very important. It makes sure we only have 1 weight assignment per vertex, giving those sharp borders we want to make our convex hulls
                
                
                
                for bone in bone_names_for_phys:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    #select vertices belonging to bone
                    try:
                        for index,group in enumerate(obj.vertex_groups):
                            if group.name == bone:
                                obj.vertex_groups.active_index = index
                                bpy.ops.object.vertex_group_select()
                                break
                    except:
                        print("failed to find vertex group "+bone+" On phys obj. Skipping.")
                        continue
                    #duplicate and make convex hull then separate
                    try:
                        bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1})
                        bpy.ops.mesh.convex_hull()
                        bpy.ops.mesh.faces_shade_smooth()
                        bpy.ops.mesh.separate(type = 'SELECTED')
                    except Exception as e:
                        print("phys joint failed for bone "+bone+". Ignoring!!")
                        print(e)
                        continue
                break
        selected_objects_memory = context.selected_objects
        for obj in selected_objects_memory:
            convexobjects[obj.vertex_groups[obj.vertex_groups.active_index].name+""] = obj
        #clear selection
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        print("joining phys parts and assigning to vertex groups")
        #clear vertex groups and assign each object to their corosponding vertex group.
        for bonename,obj in convexobjects.items():
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = obj
            Set_Mode(context, "EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            obj.vertex_groups.clear()
            obj.vertex_groups.new(name=bonename)
            obj.vertex_groups.active_index = 0
            bpy.ops.object.vertex_group_assign()
            Set_Mode(context, "OBJECT")
        
        update_viewport()

        #clear selection
        bpy.ops.object.select_all(action='DESELECT')
        #since objects already have their armature modifiers, just join into one
        for bonename,obj in convexobjects.items():
            obj.select_set(True)
        print("if this doesn't work, then you have bad weights!!")
        context.view_layer.objects.active = list(convexobjects.values())[0]
        bpy.ops.object.join() #join all objects separated into one.
        bpy.ops.object.select_all(action='DESELECT')#unselect all and delete original object
        context.view_layer.objects.active = original_object_phys
        original_object_phys.select_set(True)
        bpy.ops.object.delete(use_global=False)

        print("deleting rest of mesh for arms collection except arm bones")
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armcoll)



        print("step 1 arms: getting entire arm list of bones for each side.")
        arm_bone_names = []
        context.view_layer.objects.active = arms_armature
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        arms_armature.select_set(True)
        Set_Mode(context, "EDIT")
        #get armature bone names here since we have armature in edit mode.
        #this is changed later to exlude arm bones
        arms_armature_bone_names_list = [j.name for j in arms_armature.data.edit_bones]
        bpy.ops.armature.reveal()
        bpy.ops.armature.select_all(action='DESELECT')
        for side in ["L","R"]:
            upper_arm_name = "ValveBiped.Bip01_"+side+"_UpperArm"
            #get arm bone for this side
            bone = arms_armature.data.edit_bones.get(upper_arm_name)
            if bone is not None:
                #select arm bone
                bone.select = True
                bone.select_head = True
                bone.select_tail = True
                arms_armature.data.edit_bones.active = bone
            else:
                print("Getting upper arm for side "+side+" Has failed! Exiting!")
                return

            #select arm bone children and add to list of arm bone names
            bpy.ops.armature.select_similar(type='CHILDREN')
            for bone in bpy.context.selected_editable_bones:
                arm_bone_names.append(bone.name)
                
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armcoll)
        
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')  
        for obj in parentobj:
            obj.select_set(True)
        bpy.ops.object.join()
        
        for obj in parentobj: #do for all meshes, but we have one since the meshes were joined it will probably run once
            if obj.type == 'MESH': #we know parent obj is a mesh this is just for solidarity.
                #deselect all objects and select our obj
                Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                Set_Mode(context, "EDIT")
                
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.vertex_group_normalize()
                bpy.ops.object.vertex_group_clean(group_select_mode='ALL', keep_single=True, limit=0.001)
                bpy.ops.object.vertex_group_limit_total(limit=4)
                

                
                bpy.ops.mesh.select_all(action='DESELECT') #deselecting entire mesh so we can select the mesh parts not belonging to arm bones and delete them

                #remove arms from armature bone names list
                for i in arm_bone_names:
                    if i in arms_armature_bone_names_list:
                        arms_armature_bone_names_list.remove(i)


                for bonename in arms_armature_bone_names_list:
                    #select vertices belonging to bones that are not arms for deletion
                    try:
                        for index,group in enumerate(obj.vertex_groups):
                            if group.name == bonename:
                                obj.vertex_groups.active_index = index
                                bpy.ops.object.vertex_group_select()
                                break
                    except:
                        print("failed to find vertex group "+bone+" On arms. Skipping.")
                        continue
                bpy.ops.mesh.delete(type='VERT') #delete dem vertices so we have only arms.
                Set_Mode(context, "OBJECT")
        #select all arm bones and invert selection, then delete bones in edit mode.
        print("deleting leftover bones for arms and finding chest location.")
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armcoll)
                
        
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = arms_armature
        Set_Mode(context, "EDIT")
        chestloc = None
        bpy.ops.armature.select_all(action='DESELECT')
        for bone in arms_armature.data.edit_bones:
            bone.select = False
            bone.select_head = False
            bone.select_tail = False
            for side in ["L","R"]:
                #this list is generated soon before - @989onan
                #arm_bone_names = ["ValveBiped.Bip01_"+side+"_UpperArm",  "ValveBiped.Bip01_"+side+"_Hand",  "ValveBiped.Bip01_"+side+"_Forearm",  "ValveBiped.Bip01_"+side+"_Finger4",  "ValveBiped.Bip01_"+side+"_Finger41",  "ValveBiped.Bip01_"+side+"_Finger42",  "ValveBiped.Bip01_"+side+"_Finger3",  "ValveBiped.Bip01_"+side+"_Finger31",  "ValveBiped.Bip01_"+side+"_Finger32",  "ValveBiped.Bip01_"+side+"_Finger2",  "ValveBiped.Bip01_"+side+"_Finger21",  "ValveBiped.Bip01_"+side+"_Finger22",  "ValveBiped.Bip01_"+side+"_Finger1",  "ValveBiped.Bip01_"+side+"_Finger11",  "ValveBiped.Bip01_"+side+"_Finger12",  "ValveBiped.Bip01_"+side+"_Finger0",  "ValveBiped.Bip01_"+side+"_Finger01",  "ValveBiped.Bip01_"+side+"_Finger02"]
                if bone.name in arm_bone_names:
                    bone.select = True
                    bone.select_head = True
                    bone.select_tail = True
                    arms_armature.data.edit_bones.active = bone
                if bone.name == "ValveBiped.Bip01_Spine1" and chestloc == None:
                    chestloc = (bone.matrix[0][3],bone.matrix[1][3],bone.matrix[2][3])
                if bone.name == "ValveBiped.Bip01_Spine2":
                    chestloc = (bone.matrix[0][3],bone.matrix[1][3],bone.matrix[2][3])
        #once we are done selecting bones, invert and delete so we delete non arm bones.
        bpy.ops.armature.select_all(action='INVERT')
        bpy.ops.armature.delete()
        Set_Mode(context, "OBJECT")


        print("moving arms armature to origin and applying transforms")
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armcoll)
        
        #move arms armature to origin
        arms_armature.location = [(-1*chestloc[0]),(-1*chestloc[1]),(-1*chestloc[2])]
        
        for obj in parentobj:
            obj.select_set(True)
        arms_armature.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        update_viewport()
        

        print("configuring game and compiler paths")
        bpy.context.scene.vs.export_format = "SMD"
        bpy.context.scene.vs.engine_path = steam_librarypath+"/bin/"
        bpy.context.scene.vs.game_path = steam_librarypath+"/garrysmod/"


        print("generating compiling script file for body (.qc file)")
        jiggle_bone_list = ""
        
        #the stuff in the string below gets written to the file, which will tell the end user they can change values and what they mean.
        
        jiggle_bone_entry = """\n$jigglebone \"{bone name here}\" {//feel free to edit the bone values. This worked for me I don't know if it will work for you!
    is_flexible {
		yaw_stiffness 100 // how hard it is for the bone to start moving, make this value and the one below match.
        pitch_stiffness 100
		yaw_damping 6 //how fast the bone stops. make this value and the one below match. (RANGE: 0.0 - 10.0)
        pitch_damping 6
		length 20 //this makes the jiggling more intense as the length decreases. Think of this as your end bone length in VRC dynamic/phys bones essentially.
        tip_mass 100 // how heavy the end of the bone is. This affects things like gravity influence and how much extra stiffness you need to counteract it.
		angle_constraint 30 // this is the exact same as the VRC physbone angle limit. It's like an impeneratble cone this bone cannot rotate past compared to it's parent.
	}
}\n"""
        print("finding tail jiggle bones for compiling script")
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armcoll)
        
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        body_armature.select_set(True)
        Set_Mode(context, "EDIT")
        for bone in body_armature.data.edit_bones:
            skip = False
            for excluded in ["root","source","arm","leg"]:
                if excluded in bone.name.lower():
                    skip = True
                    break
            if not skip:
                for name in ["hair","tail","ear","bewb","boob","breast","ass","butt","wing","shaft","antenna","fluff","rope"]:
                    
                    if (name in bone.name.lower()):
                        jiggle_bone_list += jiggle_bone_entry.replace("{bone name here}", bone.name)
                        break
        
        qcfile = """$modelname \""""+sanitized_model_name+"""/"""+sanitized_model_name+""".mdl\"

{put body groups here}

$surfaceprop \"flesh\"

$contents \"solid\"

$illumposition -0.007 -0.637 35.329

$eyeposition 0 0 70

$ambientboost

$mostlyopaque

$cdmaterials \"models\\"""+sanitized_model_name+"""\\\"

$attachment \"eyes\" \"ValveBiped.Bip01_Head1\" 3.47 -3.99 -0.1 rotate 0 -80.1 -90
$attachment \"mouth\" \"ValveBiped.Bip01_Head1\" 0.8 -5.8 -0.15 rotate 0 -80 -90
$attachment \"chest\" \"ValveBiped.Bip01_Spine2\" 5 4 0 rotate 0 90 90
$attachment \"anim_attachment_head\" \"ValveBiped.Bip01_Head1\" 0 0 0 rotate -90 -90 0

$cbox 0 0 0 0 0 0

$bbox -13 -13 0 13 13 72

{put define bones here}

$bonemerge \"ValveBiped.Bip01_Pelvis\"
$bonemerge \"ValveBiped.Bip01_Spine\"
$bonemerge \"ValveBiped.Bip01_Spine1\"
$bonemerge \"ValveBiped.Bip01_Spine2\"
$bonemerge \"ValveBiped.Bip01_Spine4\"
$bonemerge \"ValveBiped.Bip01_R_Clavicle\"
$bonemerge \"ValveBiped.Bip01_R_UpperArm\"
$bonemerge \"ValveBiped.Bip01_R_Forearm\"
$bonemerge \"ValveBiped.Bip01_R_Hand\"
$bonemerge \"ValveBiped.Anim_Attachment_RH\"\n\n"""+jiggle_bone_list+"""\n\n
$ikchain \"rhand\" \"ValveBiped.Bip01_R_Hand\" knee 0.707 0.707 0
$ikchain \"lhand\" \"ValveBiped.Bip01_L_Hand\" knee 0.707 0.707 0
$ikchain \"rfoot\" \"ValveBiped.Bip01_R_Foot\" knee 0.707 -0.707 0
$ikchain \"lfoot\" \"ValveBiped.Bip01_L_Foot\" knee 0.707 -0.707 0

{put_anims_here}

$includemodel \"m_anm.mdl\"
$includemodel \"m_shd.mdl\"
$includemodel \"m_pst.mdl\"
$includemodel \"m_gst.mdl\"
$includemodel \"player/m_ss.mdl\"
$includemodel \"player/cs_fix.mdl\"
$includemodel \"player/global_include.mdl\"
$includemodel \"humans/male_shared.mdl\"
$includemodel \"humans/male_ss.mdl\"
$includemodel \"humans/male_gestures.mdl\"
$includemodel \"humans/male_postures.mdl\"

$collisionjoints \""""+physcoll.name+""".smd\"
{
    $mass 90
    $inertia 10
    $damping 0.01
    $rotdamping 1.5

    $jointconstrain \"ValveBiped.Bip01_R_UpperArm\" x limit -39 39 0
    $jointconstrain \"ValveBiped.Bip01_R_UpperArm\" y limit -79 95 0
    $jointconstrain \"ValveBiped.Bip01_R_UpperArm\" z limit -93 23 0

    $jointconstrain \"ValveBiped.Bip01_L_UpperArm\" x limit -30 30 0
    $jointconstrain \"ValveBiped.Bip01_L_UpperArm\" y limit -95 84 0
    $jointconstrain \"ValveBiped.Bip01_L_UpperArm\" z limit -86 26 0

    $jointconstrain \"ValveBiped.Bip01_L_Forearm\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Forearm\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Forearm\" z limit -149 4 0

    $jointconstrain \"ValveBiped.Bip01_L_Hand\" x limit -37 37 0
    $jointconstrain \"ValveBiped.Bip01_L_Hand\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Hand\" z limit -57 59 0

    $jointconstrain \"ValveBiped.Bip01_R_Forearm\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Forearm\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Forearm\" z limit -149 4 0

    $jointconstrain \"ValveBiped.Bip01_R_Hand\" x limit -60 60 0
    $jointconstrain \"ValveBiped.Bip01_R_Hand\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Hand\" z limit -57 70 0

    $jointconstrain \"ValveBiped.Bip01_R_Thigh\" x limit -12 12 0
    $jointconstrain \"ValveBiped.Bip01_R_Thigh\" y limit -8 75 0
    $jointconstrain \"ValveBiped.Bip01_R_Thigh\" z limit -97 32 0

    $jointconstrain \"ValveBiped.Bip01_R_Calf\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Calf\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Calf\" z limit -12 126 0

    $jointconstrain \"ValveBiped.Bip01_Head1\" x limit -20 20 0
    $jointconstrain \"ValveBiped.Bip01_Head1\" y limit -25 25 0
    $jointconstrain \"ValveBiped.Bip01_Head1\" z limit -13 30 0

    $jointconstrain \"ValveBiped.Bip01_L_Thigh\" x limit -12 12 0
    $jointconstrain \"ValveBiped.Bip01_L_Thigh\" y limit -73 6 0
    $jointconstrain \"ValveBiped.Bip01_L_Thigh\" z limit -93 30 0

    $jointconstrain \"ValveBiped.Bip01_L_Calf\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Calf\" y limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Calf\" z limit -8 126 0

    $jointconstrain \"ValveBiped.Bip01_L_Foot\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_L_Foot\" y limit -19 19 0
    $jointconstrain \"ValveBiped.Bip01_L_Foot\" z limit -15 35 0

    $jointconstrain \"ValveBiped.Bip01_R_Foot\" x limit 0 0 0
    $jointconstrain \"ValveBiped.Bip01_R_Foot\" y limit -25 6 0
    $jointconstrain \"ValveBiped.Bip01_R_Foot\" z limit -15 35 0

    $jointcollide \"ValveBiped.Bip01_R_Forearm\" \"ValveBiped.Bip01_R_Thigh\"
    $jointcollide \"ValveBiped.Bip01_R_Forearm\" \"ValveBiped.Bip01_L_Thigh\"
    $jointcollide \"ValveBiped.Bip01_L_Forearm\" \"ValveBiped.Bip01_R_Thigh\"
    $jointcollide \"ValveBiped.Bip01_L_Forearm\" \"ValveBiped.Bip01_L_Thigh\"
    $jointcollide \"ValveBiped.Bip01_L_Foot\" \"ValveBiped.Bip01_R_Calf\"
    $jointcollide \"ValveBiped.Bip01_L_Foot\" \"ValveBiped.Bip01_R_Foot\"
    $jointcollide \"ValveBiped.Bip01_R_Thigh\" \"ValveBiped.Bip01_L_Thigh\"
    $jointcollide \"ValveBiped.Bip01_R_Forearm\" \"ValveBiped.Bip01_Pelvis\"
    $jointcollide \"ValveBiped.Bip01_L_Forearm\" \"ValveBiped.Bip01_Pelvis\"
}"""




        

        print("configuring export path. If this throws an error, save your file!!")
        bpy.context.scene.vs.export_path = "//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/"
        bpy.context.scene.vs.qc_path = "//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/"+sanitized_model_name+".qc"

        
        refcoll = bpy.data.collections[sanitized_model_name+"_ref"]
        
        parentobj, body_armature = Get_Meshes_And_Armature(context, refcoll)
        
        context.view_layer.objects.active = body_armature
        Set_Mode(context, "OBJECT")
        
        print("deleting old animations")
        Set_Mode(context, "OBJECT")
        animationnames = [j.name for j in bpy.data.actions]
        for animationname in animationnames:
            bpy.data.actions.remove(bpy.data.actions[animationname])
        

        print("making animation for idle body")
        Make_And_Key_Animation(context, "idle", body_armature)

        
        print("making animation for reference body")
        
        refcoll = bpy.data.collections[sanitized_model_name+"_ref"]
        parentobj, body_armature = Get_Meshes_And_Armature(context, refcoll)
        
        
        body_armature.animation_data.action = None
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        
        print("Using importer with append enabled to yeet proportions fix anim onto our model")
        bpy.ops.import_scene.smd('EXEC_DEFAULT',files=[{'name': "reference.smd"}], append = "APPEND",directory=os.path.dirname(os.path.abspath(__file__))+"/assets/garrysmod/")
        
        print("keying animation reference.")
        body_armature.animation_data.action = bpy.data.actions["reference"]
        for barney_bone_name in barney_pose_bone_names:
            bone = body_armature.pose.bones.get(barney_bone_name)
            bone.rotation_mode = "XYZ"
            bone.keyframe_insert(data_path="rotation_euler", frame=1)
            bone.keyframe_insert(data_path="location", frame=1)
        Set_Mode(context, "OBJECT")
        
        print("making animation for idle arms")
        armscoll = bpy.data.collections[sanitized_model_name+"_arms"]
        parentobj, arms_armature = Get_Meshes_And_Armature(context, armscoll)
        Make_And_Key_Animation(context, "idle_arms", arms_armature)
        arms_armature.animation_data.action = None
        
        print("making copy of reference armature to export idle")
        parentobj, idle_armature = Get_Meshes_And_Armature(context, refcoll)
        idle_collection = Copy_to_existing_collection(context, "idle_ref", objects_alternative_list = [idle_armature])
        bpy.context.selected_objects[0].animation_data.action = bpy.data.actions["idle"] #since above we are just copying the body_armature, it should still be selected in the new collection.
        bpy.ops.object.select_all(action='DESELECT')
        
        print("making copy of reference armature to export proportions reference animation")
        parentobj, body_armature = Get_Meshes_And_Armature(context, refcoll)
        reference_collection = Copy_to_existing_collection(context, "reference_ref", objects_alternative_list = [body_armature])
        reference_armature = bpy.context.selected_objects[0]
        reference_armature.animation_data.action = bpy.data.actions["reference"] #since above we are just copying the body_armature, it should still be selected in the new collection.
        bpy.ops.object.select_all(action='DESELECT')
        
        
        
        # probably don't need this - @989onan
        # print("moving copy of body armature to origin for arms and applying transforms")
        # context.view_layer.objects.active = reference_armature
        # bpy.ops.object.select_all(action='DESELECT')
        # reference_armature.select_set(True)
        # bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        # arms_reference_anim_armature = bpy.context.selected_objects[0]
        # arms_ref_collection = bpy.data.collections.new("reference_arms")
        
        # for collection in bpy.data.collections:
            # try:
                # collection.objects.unlink(arms_reference_anim_armature)
            # except:
                # pass
        # try:
            # context.view_layer.layer_collection.collection.children.unlink(arms_reference_anim_armature)
        # except:
            # pass
        # arms_ref_collection.objects.link(arms_reference_anim_armature)
        # context.view_layer.layer_collection.collection.children.link(arms_ref_collection)
        # #move arms reference anim armature to origin
        
        
        
        # print("deleting old reference_arms animations")
        # context.view_layer.objects.active = arms_reference_anim_armature
        # Set_Mode(context, "OBJECT")
        # animationnames = [j.name for j in bpy.data.actions]
        # for animationname in animationnames:
            # if "." in animationname:
                # if animationname.split(".")[0] == "reference_arms":
                    # bpy.data.actions.remove(bpy.data.actions[animationname])
            # if animationname == "reference_arms":
                # bpy.data.actions.remove(bpy.data.actions[animationname])
        
        # print("keying animation reference_arms.")
        
        # arms_reference_anim_armature.animation_data.action = bpy.data.actions.new(name="reference_arms")
        # for barney_bone_name in barney_pose_bone_names:
            # bone = arms_reference_anim_armature.pose.bones.get(barney_bone_name)
            # bone.rotation_mode = "XYZ"
            # bone.keyframe_insert(data_path="rotation_euler", frame=1)
            # bone.keyframe_insert(data_path="location", frame=1)
        
        # arms_reference_anim_armature.location = [(-1*chestloc[0]),(-1*chestloc[1]),(-1*chestloc[2])]
        # bpy.ops.object.select_all(action='DESELECT')
        # arms_reference_anim_armature.select_set(True)
        # context.view_layer.objects.active = arms_reference_anim_armature
        # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        update_viewport()
        
        print("adding animation data to every armature because otherwise it causes errors with the exporter...")
        for rig in bpy.data.objects:
            if rig.type == "ARMATURE":
                rig.animation_data_create()
                rig.vs.action_filter = "*"
                rig.data.vs.action_selection = "FILTERED"
                rig.data.vs.implicit_zero_bone = False
        
        print("setting export settings")
        bpy.context.scene.vs.subdir = "anims"
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        time.sleep(1)
        bpy.context.scene.vs.action_selection = "FILTERED"
        
        print("making body groups, you're almost to exporting!")
        refcoll = bpy.data.collections[sanitized_model_name+"_ref"]
        body_armature = None
        for obj in refcoll.objects:
            if obj.type == "ARMATURE":
                body_armature = obj
                break
        
        def dup_collection_only_mesh(body_armature,obj):
            context.view_layer.objects.active = body_armature
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
            
            bpy.ops.object.select_all(action='DESELECT')
            
            body_group_coll = bpy.data.collections.new(obj.name+"_ref")
            
            for collection in bpy.data.collections:
                try:
                    collection.objects.unlink(obj)
                except:
                    pass
            try:
                context.view_layer.layer_collection.collection.objects.unlink(obj)
            except:
                pass
            body_group_coll.objects.link(obj)
            context.view_layer.layer_collection.collection.children.link(body_group_coll)
            return body_group_coll
        
        new_body_groups = ""
        body_group_coll = None
        for obj in refcoll.objects[:]:
            if obj.type == "MESH":
                if has_shapekeys(obj):
                    print("mesh has shapekeys, giving model shapekey data for model option")
                    shapekey_collection = dup_collection_only_mesh(body_armature,obj)
                    
                    
                    flex_block_model = """\n$model \""""+shapekey_collection.name+"""\" \""""+shapekey_collection.name+""".smd" {
    
	flexfile \""""+shapekey_collection.name+""".vta" 
	{
		defaultflex frame 0
        {put flexes here}
	}
    
    {put flexcontrollers here}
    
    {put percent thingies here}
}"""                
                    replace_flex_with = ""
                    replace_flexcontrollers_with = ""
                    replace_percent_thingies_with = ""
                    shape_flex_counter = 0
                    for shapekey in obj.data.shape_keys.key_blocks[1:]: #we wanna skip the first item since that's basis.
                        shape_flex_counter += 1
                        replace_flex_with += "flex \""+shapekey.name+"\" frame "+str(shape_flex_counter)+"\n\t\t"
                        replace_flexcontrollers_with += "flexcontroller "+shapekey.name+" range 0 1 \""+shapekey.name+"\"\n\t"
                        replace_percent_thingies_with += "%"+shapekey.name+" = "+shapekey.name+"\n\t"
                    new_body_groups += flex_block_model.replace("{put flexes here}",replace_flex_with).replace("{put flexcontrollers here}",replace_flexcontrollers_with).replace("{put percent thingies here}",replace_percent_thingies_with)
                else:
                    body_group_coll = dup_collection_only_mesh(body_armature,obj)
                    if not (obj.name in do_not_toggle_bodygroups):
                        if obj.name in hidden_by_default_bodygroups:
                            #ignore weird formatting below, indenting it will mess it up. - @989onan
                            new_body_groups +="""\n$BodyGroup \""""+obj.name+"""\"
{
    blank
    studio \""""+body_group_coll.name+""".smd\"
}
"""
                        else:
                            #ignore weird formatting below, indenting it will mess it up. - @989onan
                            new_body_groups +="""\n$BodyGroup \""""+obj.name+"""\"
{
    studio \""""+body_group_coll.name+""".smd\"
    blank
}
"""
                    else: #this is for bodies that were hidden from viewport
                        new_body_groups +="\n$body "+obj.name+" \""+body_group_coll.name+".smd\"\n"
                    
        body_animation_qc="""$sequence \"reference\" {
    \"anims/reference.smd\"
    fadein 0.2
    fadeout 0.2
    fps 1
}

$animation \"a_proportions\" \""""+refcoll.name+""".smd\"{
    fps 30

    subtract \"reference\" 0
}
$Sequence \"ragdoll\" {
    \"anims/idle.smd\"
    activity \"ACT_DIERAGDOLL\" 1
    fadein 0.2
    fadeout 0.2
    fps 30
}
$sequence \"proportions\"{
    \"a_proportions\"
    predelta
    autoplay
    fadein 0.2
    fadeout 0.2
}"""
        body_armature.animation_data.action = bpy.data.actions["idle"] #this carries a lot of weight... (basically without it, the usage of refcoll above in the qc won't work and it will break) - @989onan 
        bpy.context.scene.frame_current += 1
        
        
        
        
        print("writing body script file iteration 1. If this errors, please save your file!")
        target_dir = bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/")
        os.makedirs(target_dir,0o777,True)
        compilefile = open(target_dir+sanitized_model_name+".qc", "w")
        compilefile.write(qcfile.replace("{put_anims_here}","").replace("{put define bones here}","").replace("{put body groups here}",new_body_groups))
        compilefile.close()
        
        update_viewport()
        
        print("\n\n\n====EXPORTING EVERYTHING====\n\n\n")
        bpy.ops.export_scene.smd(export_scene = True, collection=context.view_layer.layer_collection.collection.children[0].name)
        
        update_viewport()
        print("waiting 10 seconds to prevent breakage.")# Lazy fix for a race condition before studiomdl.exe is called
        time.sleep(10)
        
        
        print("Generating bone definitions so your model doesn't collapse on itself. (takes a bit, this is done by studiomdl.exe)")
        output = subprocess.run([steam_librarypath+"/bin/studiomdl.exe", "-game", steam_librarypath+"/garrysmod", "-definebones", "-nop4", "-verbose", bpy.path.abspath(bpy.context.scene.vs.qc_path)],stdout=subprocess.PIPE)
        
        
        print("Writing DefineBones.qci")
        define_bones_file = open(bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/DefineBones.qci"), "w")
        index = output.stdout.decode('utf-8').find('$')
        define_bones_file.write(output.stdout.decode('utf-8')[index:])
        define_bones_file.close()


        print("Rewriting QC to include animations and definebones file qci and body groups since we finished compiling define bones")
        compilefile = open(bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/"+sanitized_model_name+".qc"), "w")
        compilefile.write(qcfile.replace("{put_anims_here}",body_animation_qc).replace("{put define bones here}","$include \"DefineBones.qci\"").replace("{put body groups here}",new_body_groups))
        compilefile.close()

        print("============= Compiling model! =============\n(THIS CAN TAKE A LONG TIME AND IS PRONE TO ERRORS!!!!)")
        bpy.ops.smd.compile_qc(filepath=bpy.path.abspath(bpy.context.scene.vs.qc_path))
        #to prevent errors due to missing data because it changes
        
        print("Moving compiled model to addon folder.")
        #path after models must match model path in QC.
        #thanks to "https://stackoverflow.com/a/41827240" for helping me make sure this would work correctly.
        source_dir = steam_librarypath+"/garrysmod/models/"+sanitized_model_name
        target_dir = addonpath+"models/"+sanitized_model_name
        
        file_names = None
        try:
            file_names = os.listdir(source_dir)
        except:
            print("THIS IS AN ERROR: Your model failed to compile!")
            return {'FINISHED'}
        
        os.makedirs(target_dir,0o777,True)
        for file_name in file_names:
            if os.path.exists(os.path.join(target_dir, file_name)):
                os.remove(os.path.join(target_dir, file_name))
            shutil.move(os.path.join(source_dir, file_name), target_dir)
        
        
        print("Making materials folder")
        os.makedirs((addonpath+"materials/models/"+sanitized_model_name),0o777,True)
        
        
        

        print("Making lua file for adding playermodel to playermodel list in game")
        os.makedirs(addonpath+"lua/autorun", exist_ok=True)
        luafile = open(addonpath+"lua/autorun/"+sanitized_model_name+"_playermodel_adder.lua","w")
        luafile_content = """player_manager.AddValidModel( \""""+offical_model_name+"""\", \""""+"models/"+sanitized_model_name+"/"+sanitized_model_name+""".mdl\" );
list.Set( "PlayerOptionsModel", \""""+offical_model_name+"""\", \""""+"models/"+sanitized_model_name+"/"+sanitized_model_name+""".mdl\");
player_manager.AddValidHands( \""""+offical_model_name+"""\", \""""+"models/"+sanitized_model_name+"/"+sanitized_model_name+"""_arms.mdl\", 0, "00000000" );"""
        luafile.write(luafile_content)
        luafile.close()

        print("resizing arms")

        arms_scale_factor = None
        collection = bpy.data.collections[sanitized_model_name+"_arms"]
        armature = None
        for obj in collection.objects:
            if obj.type == "ARMATURE":
                armature = obj
                break
        context.view_layer.objects.active = armature
        Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        try:
            Set_Mode(context, "EDIT")
            obj = armature
            editbone1 = armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"]
            editbone2 = armature.data.edit_bones["ValveBiped.Bip01_L_Forearm"]
            loc1 = [editbone1.matrix[0][3],editbone1.matrix[1][3],editbone1.matrix[2][3]]
            loc2 = [editbone2.matrix[0][3],editbone2.matrix[1][3],editbone2.matrix[2][3]]
            Set_Mode(context, "OBJECT")
            distance = math.sqrt(((loc2[0]-loc1[0])*(loc2[0]-loc1[0]))+((loc2[1]-loc1[1])*(loc2[1]-loc1[1]))+((loc2[2]-loc1[2])*(loc2[2]-loc1[2])))
            arms_scale_factor = 11.692535032476918/distance #random number is distance between upper and lower arm for barney armature

        except Exception as e:
            print("ARMS SOMEHOW DON'T HAVE ARM BONES. SCALER BROKE. PLEASE SEE USER \"434468177062133772\" ON CATS/TUXEDO DISCORD.")
            print("ERROR IS AS FOLLOWS: ",e)
        if arms_scale_factor is not None:
            armature.scale = (arms_scale_factor,arms_scale_factor,arms_scale_factor)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)
        
        

        print("generating qc file for arms")
        qcfile = """$modelname \""""+sanitized_model_name+"""/"""+sanitized_model_name+"""_arms.mdl\"

$BodyGroup \""""+sanitized_model_name+"""_arms\"
{
    studio \""""+sanitized_model_name+"""_arms.smd\"
}


$SurfaceProp \"flesh\"

$Contents \"solid\"

$EyePosition 0 0 70

$MaxEyeDeflection 90

$MostlyOpaque

$CDMaterials \"models\\"""+sanitized_model_name+"""\\\"

$CBox 0 0 0 0 0 0

$BBox -13 -13 0 13 13 72

$Sequence \"idle\" {
    \"anims/idle_arms.smd\"
    fps 1
}"""
        print("writing qc file for arms. If this errors, please save your file!")
        compilefile = open(bpy.path.abspath("//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/"+sanitized_model_name+"_arms.qc"), "w")
        compilefile.write(qcfile)
        compilefile.close()
        
        
        bpy.context.scene.vs.qc_path = "//Tuxedo Bake/" + sanitized_platform_name + "/"+sanitized_model_name+"/"+sanitized_model_name+"_arms.qc"
        print("Compiling arms model! (THIS CAN TAKE A LONG TIME AND IS PRONE TO ERRORS!!!!)")
        bpy.ops.smd.compile_qc(filepath=bpy.path.abspath(bpy.context.scene.vs.qc_path))

        print("Moving compiled arms model to addon folder.")
        #path after models must match model path in QC.
        #thanks to "https://stackoverflow.com/a/41827240" for helping me make sure this would work correctly.
        #this is the same as body because they should both be put in the same folder. This could be called once at the end of the script but eh i don't think it's needed.
        source_dir = steam_librarypath+"/garrysmod/models/"+sanitized_model_name
        target_dir = addonpath+"models/"+sanitized_model_name
        file_names = os.listdir(source_dir)
        os.makedirs(target_dir,0o777,True)
        for file_name in file_names:
            if os.path.exists(os.path.join(target_dir, file_name)):
                os.remove(os.path.join(target_dir, file_name))
            shutil.move(os.path.join(source_dir, file_name), target_dir)


        print("======================FINISHED GMOD PROCESS======================")
        print("Wow that took a long time...")
        return {'FINISHED'}




