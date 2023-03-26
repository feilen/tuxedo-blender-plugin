import bmesh
import bpy
import csv
import math
import os
import webbrowser

from io_scene_fbx import fbx_utils
from mathutils.geometry import intersect_point_line

translation_dictionary = dict()
with open(os.path.dirname(os.path.abspath(__file__)) + "/translations.csv", 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) >= 2:
            translation_dictionary[row[0]] = row[1]

# Bone names from https://github.com/triazo/immersive_scaler/
bone_names = {
    "right_shoulder": ["rightshoulder", "shoulderr", "rshoulder"],
    "right_arm": ["rightarm", "armr", "rarm", "upperarmr", "rightupperarm", "uparmr", "ruparm"],
    "right_elbow": ["rightelbow", "elbowr", "relbow", "lowerarmr", "rightlowerarm", "lowerarmr", "lowarmr", "rlowarm"],
    "right_wrist": ["rightwrist", "wristr", "rwrist", "handr", "righthand", "rhand"],

    #hand l fingers
    "pinkie_1_r": ["littlefinger1r"],
    "pinkie_2_r": ["littlefinger2r"],
    "pinkie_3_r": ["littlefinger3r"],

    "ring_1_r": ["ringfinger1r"],
    "ring_2_r": ["ringfinger2r"],
    "ring_3_r": ["ringfinger3r"],

    "middle_1_r": ["middlefinger1r"],
    "middle_2_r": ["middlefinger2r"],
    "middle_3_r": ["middlefinger3r"],

    "index_1_r": ["indexfinger1r"],
    "index_2_r": ["indexfinger2r"],
    "index_3_r": ["indexfinger3r"],

    "thumb_1_r": ['thumb0r'],
    "thumb_2_r": ['thumb1r'],
    "thumb_3_r": ['thumb2r'],

    "right_leg": ["rightleg", "legr", "rleg", "upperlegr", "thighr", "rightupperleg", "uplegr", "rupleg"],
    "right_knee": ["rightknee", "kneer", "rknee", "lowerlegr", "calfr", "rightlowerleg", "lowlegr", "rlowleg"],
    "right_ankle": ["rightankle", "ankler", "rankle", "rightfoot", "footr", "rightfoot", "rightfeet", "feetright", "rfeet", "feetr"],
    "right_toe": ["righttoe", "toeright", "toer", "rtoe", "toesr", "rtoes"],

    "left_shoulder": ["leftshoulder", "shoulderl", "rshoulder"],
    "left_arm": ["leftarm", "arml", "rarm", "upperarml", "leftupperarm", "uparml", "luparm"],
    "left_elbow": ["leftelbow", "elbowl", "relbow", "lowerarml", "leftlowerarm", "lowerarml", "lowarml", "llowarm"],
    "left_wrist": ["leftwrist", "wristl", "rwrist", "handl", "lefthand", "lhand"],

    #hand l fingers
    "pinkie_1_l": ["littlefinger1l"],
    "pinkie_2_l": ["littlefinger2l"],
    "pinkie_3_l": ["littlefinger3l"],

    "ring_1_l": ["ringfinger1l"],
    "ring_2_l": ["ringfinger2l"],
    "ring_3_l": ["ringfinger3l"],

    "middle_1_l": ["middlefinger1l"],
    "middle_2_l": ["middlefinger2l"],
    "middle_3_l": ["middlefinger3l"],

    "index_1_l": ["indexfinger1l"],
    "index_2_l": ["indexfinger2l"],
    "index_3_l": ["indexfinger3l"],

    "thumb_1_l": ['thumb0l'],
    "thumb_2_l": ['thumb1l'],
    "thumb_3_l": ['thumb2l'],

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
        for v in obj.data.vertices:
            for g in v.groups:
                if vgroup_lookup[g.group] in bone_names:
                    bone = armature.data.bones[vgroup_lookup[g.group]]
                    if bone.parent and bone.parent.name in obj.vertex_groups:
                       obj.vertex_groups[bone.parent.name].add([v.index], g.weight, 'ADD')

        for bone_name in bone_names:
            # remove old bones vertex groups
            if bone_name in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups[bone_name])

    # remove old bones
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
    return str_key if str_key not in translation_dictionary else translation_dictionary[str_key]

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
#
#    def poll(cls, context):
#        return True #context.view_layer.objects.active and context.view_layer.objects.selected
#
    def execute(self, context):
        animation_weighting = context.scene.decimation_animation_weighting
        animation_weighting_factor = context.scene.decimation_animation_weighting_factor
        tuxedo_max_tris = context.scene.tuxedo_max_tris
        armature = get_armature(context, armature_name=self.armature_name)
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

        if tris_count == 0:
            self.report({'INFO'}, "No tris found.")
            return {'FINISHED'}

        decimation = 1. + ((tuxedo_max_tris - tris_count) / tris_count)
        print("Decimation: " + str(decimation))
        if decimation >= 1:
            self.report({'INFO'}, "No Decimation needed.")
            return {'FINISHED'}
        elif decimation <= 0:
            self.report({'INFO'}, "Can't reach target decimation level.")
            return {'FINISHED'}

        if animation_weighting:
            for mesh in meshes_obj:
                newweights = self.get_animation_weighting(context, mesh, armature)

                context.view_layer.objects.active = mesh
                bpy.ops.object.vertex_group_add()
                mesh.vertex_groups[-1].name = "Tuxedo Animation"
                for idx, weight in newweights.items():
                    mesh.vertex_groups[-1].add([idx], weight, "REPLACE")

        for mesh_obj in meshes_obj:
            tris = get_tricount(mesh_obj)
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
                me = mesh_obj.data
                for edge in me.edges:
                    if edge.use_seam:
                        edge.select = True

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action="INVERT")
            if animation_weighting:
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.object.mode_set(mode='OBJECT')
                me = mesh_obj.data
                vgroup_idx = mesh_obj.vertex_groups["Tuxedo Animation"].index
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

            if has_shapekeys(mesh_obj):
                for idx in range(1, len(mesh_obj.data.shape_keys.key_blocks) - 1):
                    mesh_obj.active_shape_key_index = idx
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.blend_from_shape(shape="Tuxedo Basis", blend=-1.0, add=True)
                    bpy.ops.object.mode_set(mode='OBJECT')
                mesh_obj.shape_key_remove(key=mesh_obj.data.shape_keys.key_blocks["Tuxedo Basis"])
                mesh_obj.active_shape_key_index = 0
        return {'FINISHED'}

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

