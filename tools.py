import bpy
import math
from mathutils.geometry import intersect_point_line

from .main import ToolPanel
from .main import add_button_with_small_button
from ..tools import armature_manual as Armature_manual
from ..tools.register import register_wrap
from ..tools.translations import t

@register_wrap
class FitClothes(bpy.types.Operator):
    bl_idname = 'cats_custom.fit_clothes'
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
            Common.apply_modifier(trans_modifier)

            # Setup armature
            for mod_name in [mod.name for mod in obj.modifiers]:
                if obj.modifiers[mod_name].type == 'ARMATURE':
                    obj.modifiers.remove(obj.modifiers[mod_name])
            arm_modifier = obj.modifiers.new(type='ARMATURE', name='Armature')
            arm_modifier.object = armature


        self.report({'INFO'}, 'Clothes rigged!')
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
            v_weights = [group.weight for group in vertex.groups]
            v_mults = []
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

    def TODO_SMART_DECIMATION():
        if animation_weighting:
            for mesh in meshes_obj:
                newweights = self.get_animation_weighting(context, mesh, armature)

                # TODO: ignore shape keys which move very little?
                context.view_layer.objects.active = mesh
                bpy.ops.object.vertex_group_add()
                mesh.vertex_groups[-1].name = "CATS Animation"
                for idx, weight in newweights.items():
                    mesh.vertex_groups[-1].add([idx], weight, "REPLACE")

        animation_weighting = context.scene.decimation_animation_weighting
        animation_weighting_factor = context.scene.decimation_animation_weighting_factor
                # Smart
                Common.switch('EDIT')
                bpy.ops.mesh.select_mode(type="VERT")
                bpy.ops.mesh.select_all(action="SELECT")
                # TODO: Fix decimation calculation when pinning seams
                # TODO: Add ability to explicitly include/exclude vertices from decimation. So you
                # can manually preserve loops
                if self.preserve_seams:
                    bpy.ops.mesh.select_all(action="DESELECT")
                    bpy.ops.uv.seams_from_islands()

                    # select all seams
                    Common.switch('OBJECT')
                    me = mesh_obj.data
                    for edge in me.edges:
                        if edge.use_seam:
                            edge.select = True

                    Common.switch('EDIT')
                    bpy.ops.mesh.select_all(action="INVERT")
                if animation_weighting:
                    bpy.ops.mesh.select_all(action="DESELECT")
                    Common.switch('OBJECT')
                    me = mesh_obj.data
                    vgroup_idx = mesh_obj.vertex_groups["CATS Animation"].index
                    weight_dict = {vertex.index: group.weight for vertex in me.vertices for group in vertex.groups if group.group == vgroup_idx}
                    # We de-select a_w_f worth of polygons, so the remaining decimation must be done in decimation/(1-a_w_f) polys
                    selected_verts = sorted([v for v in me.vertices], key=lambda v: 0 - weight_dict.get(v.index, 0.0))[0:int(decimation * tris * animation_weighting_factor)]
                    for v in selected_verts:
                        v.select = True

                    Common.switch('EDIT')
                    bpy.ops.mesh.select_all(action="INVERT")


                effective_ratio = decimation if not animation_weighting else (decimation * (1-animation_weighting_factor))
                bpy.ops.mesh.decimate(ratio=effective_ratio,
                                      #use_vertex_group=animation_weighting,
                                      #vertex_group_factor=animation_weighting_factor,
                                      #invert_vertex_group=True,
                                      use_symmetry=True,
                                      symmetry_axis='X')
                Common.switch('OBJECT')


            if smart_decimation and Common.has_shapekeys(mesh_obj):
                for idx in range(1, len(mesh_obj.data.shape_keys.key_blocks) - 1):
                    mesh_obj.active_shape_key_index = idx
                    Common.switch('EDIT')
                    bpy.ops.mesh.blend_from_shape(shape="CATS Basis", blend=-1.0, add=True)
                    Common.switch('OBJECT')
                mesh_obj.shape_key_remove(key=mesh_obj.data.shape_keys.key_blocks["CATS Basis"])
                mesh_obj.active_shape_key_index = 0


@register_wrap
class GenerateTwistBones(bpy.types.Operator):
    bl_idname = 'cats_manual.generate_twist_bones'
    bl_label = "Generate Twist Bones"
    bl_description = "Attempt to generate twistbones for the selected bones"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if not Common.get_armature():
            return False
        return context.selected_editable_bones

    def execute(self, context):
        saved_data = Common.SavedData()

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

        Common.switch('OBJECT')
        for bone_name, twist_bone_name in bone_pairs:
            twist_bone_head_tail = twist_locations[twist_bone_name]
            print(twist_bone_head_tail[0])
            print(twist_bone_head_tail[1])
            for mesh in Common.get_meshes_objects(armature_name=armature.name):
                if not bone_name in mesh.vertex_groups:
                    continue

                Common.set_active(mesh)
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

        Common.set_default_stage()

        saved_data.load()
        self.report({'INFO'}, t('RemoveConstraints.success'))
        return {'FINISHED'}


@register_wrap
class OptimizeStaticShapekeys(bpy.types.Operator):
    bl_idname = 'cats_manual.optimize_static_shapekeys'
    bl_label = 'Optimize Static Shapekeys'
    bl_description = "Move all shapekey-affected geometry into its own mesh, significantly decreasing GPU cost"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            return True

        meshes = Common.get_meshes_objects(check=False)
        return meshes

    def execute(self, context):
        saved_data = Common.SavedData()

        objs = [context.active_object]
        if not objs[0] or (objs[0] and (objs[0].type != 'MESH' or objs[0].data.shape_keys is None)):
            Common.unselect_all()
            meshes = Common.get_meshes_objects()
            if len(meshes) == 0:
                saved_data.load()
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
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_mode(type="VERT")
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    # TODO: un-smooth objects aren't handled correctly. A workaround is to run 'split
                    # normals' on all un-smooth objects before baking
                    bpy.ops.mesh.set_normals_from_faces(keep_sharp=True)

                # Separate non-animating
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.mesh.select_mode(type="VERT")
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
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
                        bpy.ops.object.mode_set(mode = 'EDIT')
                        bpy.ops.mesh.select_more()
                        bpy.ops.mesh.split() # required or custom normals aren't preserved
                        bpy.ops.mesh.separate(type='SELECTED')
                        bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.context.object.active_shape_key_index = 0
                    mesh.name = "Static"
                    mesh['catsForcedExportName'] = "Static"
                    # remove all shape keys for 'Static'
                    bpy.ops.object.shape_key_remove(all=True)

        Common.set_default_stage()

        saved_data.load()
        self.report({'INFO'}, "Separation complete.")
        return {'FINISHED'}


@register_wrap
class TwistTutorialButton(bpy.types.Operator):
    bl_idname = 'cats_manual.twist_tutorial'
    bl_label = t('cats_bake.tutorial_button.label')
    bl_description = "This will open a basic tutorial on how to setup and use these constraints. You can skip to the Unity section."
    bl_options = {'INTERNAL'}

    def execute(self, context):
        webbrowser.open("https://web.archive.org/web/20211014084533/https://vrcat.club/threads/tutorial-guide-twist-bones-what-are-they-and-how-do-you-use-them.3622/")
        return {'FINISHED'}

def get_tricount(obj):
    # Triangulates with Bmesh to avoid messing with the original geometry
    bmesh_mesh = bmesh.new()
    bmesh_mesh.from_mesh(obj.data)

    bmesh.ops.triangulate(bmesh_mesh, faces=bmesh_mesh.faces[:])
    return len(bmesh_mesh.faces)

