# GPL License

import os
import bpy
import math
import numpy as np
import subprocess
import shutil
import webbrowser

from .class_register import wrapper_registry
from .tools.translate import t
from .tools import core

if bpy.app.version >= (4, 0, 0):
    EMISSION_INPUT = "Emission Color"
    SPECULAR_INPUT = "Specular IOR Level"
else:
    EMISSION_INPUT = "Emission"
    SPECULAR_INPUT = "Specular"

@wrapper_registry
class BakeTutorialButton(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.tutorial'
    bl_label = t('tuxedo_bake.tutorial_button.label')
    bl_description = t('tuxedo_bake.tutorial_button.desc')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        webbrowser.open(t('tuxedo_bake.tutorial_button.URL'))

        self.report({'INFO'}, t('tuxedo_bake.tutorial_button.success'))
        return {'FINISHED'}

# Convienience filter function for retrieving objects
def get_objects(objects, filter_type=set(), filter_func=None):
    return [obj for obj in objects if (len(filter_type) == 0 or obj.type in filter_type) and
                                      (filter_func is None or filter_func(obj))]

# filter definition for 'copy only' objects
def not_copyonly(obj):
    return 'bakeCopyOnly' not in obj or not obj['bakeCopyOnly']

def autodetect_passes(self, context, item, tricount, platform, use_phong=False):
    item.max_tris = tricount
    # Autodetect passes based on BSDF node inputs
    bsdf_nodes = []
    output_mat_nodes = []
    objects = get_objects(core.get_meshes_objects(context), filter_func=lambda obj:
                          not obj.hide_get() or not context.scene.bake_ignore_hidden)
    for obj in objects:
        for slot in obj.material_slots:
            if slot.material:
                if not slot.material.use_nodes or not slot.material.node_tree:
                    self.report({'ERROR'}, t('tuxedo_bake.warn_missing_nodes'))
                    return {'FINISHED'}
                tree = slot.material.node_tree
                for node in tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        output_mat_nodes.append(node)
                    if node.type == "BSDF_PRINCIPLED":
                        bsdf_nodes.append(node)
    # Decimate if we're over the limit
    total_tricount = sum(core.get_tricount(obj) for obj in objects)
    item.use_decimation = total_tricount > tricount
    
    # Diffuse: on if >1 unique color input or if any has non-default base color input on bsdf
    context.scene.bake_pass_diffuse = (any(node.inputs["Base Color"].is_linked for node in bsdf_nodes)
                                       or len(set(node.inputs["Base Color"].default_value[:] for node in bsdf_nodes)) > 1)

    # Smoothness: similar to diffuse
    context.scene.bake_pass_smoothness = (any(node.inputs["Roughness"].is_linked for node in bsdf_nodes)
                                          or len(set(node.inputs["Roughness"].default_value for node in bsdf_nodes)) > 1)

    # Emit: similar to diffuse
    context.scene.bake_pass_emit = (any(node.inputs[EMISSION_INPUT].is_linked for node in bsdf_nodes)
                                    or len(set(node.inputs[EMISSION_INPUT].default_value[:] for node in bsdf_nodes)) > 1)

    # Transparency: similar to diffuse
    context.scene.bake_pass_alpha = (any(node.inputs["Alpha"].is_linked for node in bsdf_nodes)
                                     or len(set(node.inputs["Alpha"].default_value for node in bsdf_nodes)) > 1)

    # Metallic: similar to diffuse
    context.scene.bake_pass_metallic = (any(node.inputs["Metallic"].is_linked for node in bsdf_nodes)
                                        or len(set(node.inputs["Metallic"].default_value for node in bsdf_nodes)) > 1)

    # Normal: on if any normals connected or if decimating... so, always on for this preset
    context.scene.bake_pass_normal = (item.use_decimation
                                      or any(node.inputs["Normal"].is_linked for node in bsdf_nodes))

    # Displacement: if any displacement is linked to the output for material output nodes
    context.scene.bake_pass_displacement = any(node.inputs["Displacement"].is_linked for node in output_mat_nodes)

    context.scene.bake_pass_detail = False

    if any("Target" in obj.data.uv_layers for obj in core.get_meshes_objects(context)):
        context.scene.bake_uv_overlap_correction = 'MANUAL'
    elif any(plat.use_decimation for plat in context.scene.bake_platforms) and context.scene.bake_pass_normal:
        context.scene.bake_uv_overlap_correction = 'UNMIRROR'

    # Quest has no use for twistbones
    item.merge_twistbones = platform != "DESKTOP"

    # AO: up to user, don't override as part of this. Possibly detect if using a toon shader in the future?
    item.diffuse_premultiply_ao = platform != "DESKTOP"
    item.smoothness_premultiply_ao = platform != "DESKTOP"

    # alpha packs: arrange for maximum efficiency.
    # Its important to leave Diffuse alpha alone if we're not using it, as Unity will try to use 4bpp if so
    item.diffuse_alpha_pack = "NONE"
    item.metallic_alpha_pack = "NONE"
    if platform == "DESKTOP":
        item.export_format = "FBX"
        item.image_export_format = "PNG"
        item.translate_bone_names = "NONE"
        # If 'smoothness' and 'transparency', we need to force metallic to bake so we can pack to it.
        if context.scene.bake_pass_smoothness and context.scene.bake_pass_alpha:
            context.scene.bake_pass_metallic = True
        # If we have transparency, it needs to go in diffuse alpha
        if context.scene.bake_pass_alpha:
            item.diffuse_alpha_pack = "TRANSPARENCY"
        # Smoothness to diffuse is only the most efficient when we don't have metallic or alpha
        if context.scene.bake_pass_smoothness and not context.scene.bake_pass_metallic and not context.scene.bake_pass_alpha:
            item.diffuse_alpha_pack = "SMOOTHNESS"
        if context.scene.bake_pass_metallic and context.scene.bake_pass_smoothness:
            item.metallic_alpha_pack = "SMOOTHNESS"
        if context.scene.bake_pass_metallic and context.scene.bake_pass_ao:
            item.metallic_pack_ao = True
        item.use_lods = False
        item.use_physmodel = False
    elif platform == "QUEST":
        item.export_format = "FBX"
        item.image_export_format = "PNG"
        item.translate_bone_names = "NONE"
        item.prop_bone_handling = "GENERATE"
        item.copy_only_handling = "REMOVE"
        # Diffuse vertex color bake? Only if there's already no texture inputs!
        if not any([node.inputs["Base Color"].is_linked for node in bsdf_nodes]):
            item.diffuse_vertex_colors = True

        # alpha packs: arrange for maximum efficiency.
        # Its important to leave Diffuse alpha alone if we're not using it, as Unity will try to use 4bpp if so
        item.diffuse_alpha_pack = "NONE"
        item.metallic_alpha_pack = "NONE"
        # Smoothness to diffuse is only the most efficient when we don't have metallic
        if context.scene.bake_pass_smoothness and not context.scene.bake_pass_metallic:
            item.diffuse_alpha_pack = "SMOOTHNESS"
        if context.scene.bake_pass_metallic and context.scene.bake_pass_smoothness:
            item.metallic_alpha_pack = "SMOOTHNESS"
        item.metallic_pack_ao = False
        item.use_lods = False
        item.use_physmodel = False
    elif platform == "SECONDLIFE":
        item.export_format = "DAE"
        item.image_export_format = "PNG"
        item.translate_bone_names = "SECONDLIFE"
        item.prop_bone_handling = "REMOVE"
        item.copy_only_handling = "COPY"
        if context.scene.bake_pass_emit:
            item.diffuse_alpha_pack = "EMITMASK"
        item.specular_setup = context.scene.bake_pass_diffuse and context.scene.bake_pass_metallic
        item.specular_alpha_pack = "SMOOTHNESS" if context.scene.bake_pass_smoothness else "NONE"
        item.diffuse_emit_overlay = context.scene.bake_pass_emit
        item.use_physmodel = True
        item.physmodel_lod = 0.1
        item.use_lods = True
        item.lods = (1./4, 1./16, 1./32)
    elif platform == "GMOD":
        # https://developer.valvesoftware.com/wiki/Adapting_PBR_Textures_to_Source with some adjustments
        item.export_format = "GMOD"
        item.image_export_format = "TGA"
        item.translate_bone_names = "VALVE"
        item.gmod_model_name = ""
        item.prop_bone_handling = "REMOVE"
        item.copy_only_handling = "REMOVE"
        if not use_phong:
            if context.scene.bake_pass_normal:
                item.normal_alpha_pack = "SPECULAR"
                item.normal_invert_g = True
            item.specular_setup = True
            item.phong_setup = False
            item.specular_smoothness_overlay = context.scene.bake_pass_smoothness
        else:
            if context.scene.bake_pass_normal:
                item.normal_alpha_pack = "SMOOTHNESS"
                item.normal_invert_g = True
            item.specular_setup = False
            item.phong_setup = True
            item.specular_smoothness_overlay = False
        item.diffuse_emit_overlay = context.scene.bake_pass_emit
        item.diffuse_premultiply_ao = context.scene.bake_pass_ao
        item.smoothness_premultiply_ao = context.scene.bake_pass_ao and context.scene.bake_pass_smoothness
        #TBD: basetexture specular pack
        if context.scene.bake_pass_emit:
            item.diffuse_alpha_pack = "EMITMASK"
        elif context.scene.bake_pass_alpha:
            item.diffuse_alpha_pack = "TRANSPARENCY"
        else:
            item.diffuse_alpha_pack = "NONE"

        if len(objects) > 0:
            item.use_decimation = max(core.get_tricount(obj) for obj in objects) > 9950



def img_channels_as_nparray(image_name):
    image = bpy.data.images[image_name]
    pixel_buffer = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(pixel_buffer)
    return pixel_buffer.reshape(4, -1, order='F')

def nparray_channels_to_img(image_name, nparr):
    image = bpy.data.images[image_name]
    assert(nparr.shape[0] == 4)
    assert(nparr.shape[1] == image.size[0] * image.size[1])
    image.pixels.foreach_set(np.ravel(nparr, order='F'))

@wrapper_registry
class BakePresetDesktop(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_desktop'
    bl_label = t('tuxedo_bake.preset_desktop.label')
    bl_description = t('tuxedo_bake.preset_desktop.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        item = context.scene.bake_platforms.add()
        item.name = t('BakePanel.vrc_d_excellent')
        autodetect_passes(self, context, item, 32000, "DESKTOP")
        itemgood = context.scene.bake_platforms.add()
        itemgood.name = t('BakePanel.vrc_d_good')
        autodetect_passes(self, context, itemgood, 70000, "DESKTOP")
        return {'FINISHED'}

@wrapper_registry
class BakePresetQuest(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_quest'
    bl_label = t('tuxedo_bake.preset_quest.label')
    bl_description = t('tuxedo_bake.preset_quest.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        item = context.scene.bake_platforms.add()
        item.name = t('BakePanel.vrc_q_excellent')
        autodetect_passes(self, context, item, 7500, "QUEST")
        itemgood = context.scene.bake_platforms.add()
        itemgood.name = t('BakePanel.vrc_q_good')
        autodetect_passes(self, context, itemgood, 10000, "QUEST")
        itemmedium = context.scene.bake_platforms.add()
        itemmedium.name = t('BakePanel.vrc_q_medium')
        autodetect_passes(self, context, itemmedium, 15000, "QUEST")
        context.scene.bake_animation_weighting = True
        return {'FINISHED'}

@wrapper_registry
class BakePresetSecondlife(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_secondlife'
    bl_label = t('BakePanel.second_life') 
    bl_description = t('BakePanel.second_life_detect.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        item = context.scene.bake_platforms.add()
        item.name = t('BakePanel.second_life') 
        autodetect_passes(self, context, item, 21844, "SECONDLIFE")
        return {'FINISHED'}

@wrapper_registry
class BakePresetGmod(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_gmod'
    bl_label = t('BakePanel.garrys_mod_metallic')
    bl_description = t('BakePanel.garrys_mod_detect.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        item = context.scene.bake_platforms.add()
        item.name = t('BakePanel.garrys_mod_metallic')
        autodetect_passes(self, context, item, 65500, "GMOD")
        return {'FINISHED'}

@wrapper_registry
class BakePresetGmodPhong(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_gmod_phong'
    bl_label = t('BakePanel.garrys_mod_organic')
    bl_description = t('BakePanel.garrys_mod_detect.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        item = context.scene.bake_platforms.add()
        item.name = t('BakePanel.garrys_mod_organic')
        autodetect_passes(self, context, item, 65500, "GMOD", use_phong=True)
        return {'FINISHED'}

@wrapper_registry
class BakePresetAll(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.preset_all'
    bl_label = t('BakePanel.all_detect.label')
    bl_description = t('BakePanel.all_detect.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        bpy.ops.tuxedo_bake.preset_desktop()
        bpy.ops.tuxedo_bake.preset_quest()
        bpy.ops.tuxedo_bake.preset_secondlife()
        return {'FINISHED'}

@wrapper_registry
class BakeAddCopyOnly(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.add_copyonly'
    bl_label = t('BakePanel.add_copyonly.label')
    bl_description = t('BakePanel.add_copyonly.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.selected and any(obj.type == "MESH" for obj in context.view_layer.objects.selected)

    def execute(self, context):
        for obj in get_objects(context.view_layer.objects.selected):
            obj['bakeCopyOnly'] = True
        return {'FINISHED'}

@wrapper_registry
class BakeRemoveCopyOnly(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.remove_copyonly'
    bl_label = t('BakePanel.remove_copyonly.label')
    bl_description = t('BakePanel.remove_copyonly.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.selected and any(obj.type == "MESH" for obj in context.view_layer.objects.selected)

    def execute(self, context):
        for obj in get_objects(context.view_layer.objects.selected):
            obj['bakeCopyOnly'] = False
        return {'FINISHED'}

@wrapper_registry
class BakeAddProp(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.add_prop'
    bl_label = t('BakePanel.add_prop.label')
    bl_description = t('BakePanel.add_prop.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.selected and any(obj.type == "MESH" for obj in context.view_layer.objects.selected)

    def execute(self, context):
        for obj in get_objects(context.view_layer.objects.selected):
            obj['generatePropBones'] = True
        return {'FINISHED'}

@wrapper_registry
class BakeRemoveProp(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.remove_prop'
    bl_label = t('BakePanel.remove_prop.label')
    bl_description = t('BakePanel.remove_prop.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.selected and any(obj.type == "MESH" for obj in context.view_layer.objects.selected)

    def execute(self, context):
        for obj in get_objects(context.view_layer.objects.selected):
            obj['generatePropBones'] = False
        return {'FINISHED'}

@wrapper_registry
class BakeButton(bpy.types.Operator):
    bl_idname = 'tuxedo_bake.bake'
    bl_label = t('tuxedo_bake.bake.label')
    bl_description = t('tuxedo_bake.bake.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        for obj in core.get_meshes_objects(context):
            if obj.name not in context.view_layer.objects:
                continue
            if obj.hide_get():
                continue
            for slot in obj.material_slots:
                if slot.material:
                    if not slot.material.use_nodes:
                        return False
                else:
                    if len(obj.material_slots) == 1:
                        return False

        return context.scene.bake_platforms


    # Force displacment normals to go either - or + Y, so we can bake and normalize them
    # This will likely break if 'Normal' is already linked, but that's uncommon for typical material setups.
    def prepare_displacement(self, objects, inverted=False, restore = False):
        desired_material_trees = {slot.material.node_tree for obj in objects
                                   for slot in obj.material_slots if slot.material}
        desired_material_trees |= {node_group for node_group in bpy.data.node_groups}

        for tree in desired_material_trees:
            for node_name in [node.name for node in tree.nodes]:
                node = tree.nodes[node_name]
                if not restore:
                    if node.type == "DISPLACEMENT":
                        bake_node = tree.nodes.new("ShaderNodeCombineXYZ")
                        bake_node.name = node.name + ".BAKE"
                        bake_node.label = t('Bake.debug_bad_object')
                        bake_node.inputs["Y"].default_value = 1. if not inverted else -1.
                        tree.links.new(node.inputs["Normal"], bake_node.outputs["Vector"])
                else:
                    # Remove created displacement input nodes
                    if node.type == "COMBXYZ" and node.name[-5:] == ".BAKE":
                        # Make the bake Vector take over all outputs
                        if node.outputs["Vector"].is_linked:
                            while node.outputs["Vector"].is_linked:
                                tree.links.remove(node.outputs["Vector"].links[0])

                        tree.nodes.remove(node)


    # For all output nodes, swap selected inputs
    def swap_inputs(self, objects, desired_inputs, node_type):
        desired_material_trees = {slot.material.node_tree for obj in objects
                                   for slot in obj.material_slots if slot.material}
        desired_material_trees |= {node_group for node_group in bpy.data.node_groups}

        for tree in desired_material_trees:
            for node_name in [node.name for node in tree.nodes]:
                node = tree.nodes[node_name]
                if node.type == node_type:
                    for desired_input, connect_to in desired_inputs.items():
                        desired_orig = node.inputs[desired_input].links[0].from_socket if node.inputs[desired_input].is_linked else None
                        connect_orig = node.inputs[connect_to].links[0].from_socket if node.inputs[connect_to].is_linked else None
                        while node.inputs[desired_input].is_linked:
                            tree.links.remove(node.inputs[desired_input].links[0])
                        while node.inputs[connect_to].is_linked:
                            tree.links.remove(node.inputs[connect_to].links[0])
                        if desired_orig:
                            tree.links.new(node.inputs[connect_to], desired_orig)
                        if connect_orig:
                            tree.links.new(node.inputs[desired_input], connect_orig)

    # For every found BSDF, duplicate it, rename the new one to '.BAKE', and set bake-able defaults
    # Attach the links and copy the dv, but only for desired_inputs
    def genericize_bsdfs(self, objects, desired_inputs, base_black=False, flat_ior=False):
        desired_material_trees = {slot.material.node_tree for obj in objects
                                   for slot in obj.material_slots if slot.material}
        desired_material_trees |= {node_group for node_group in bpy.data.node_groups}

        for tree in desired_material_trees:
            for node_name in [node.name for node in tree.nodes]:
                node = tree.nodes[node_name]
                if node.type == "BSDF_PRINCIPLED":
                    bake_node = tree.nodes.new("ShaderNodeBsdfPrincipled")
                    bake_node.name = node.name + ".BAKE"
                    bake_node.label = t('Bake.debug_bad_object')
                    for desired_input, connect_to in desired_inputs.items():
                        if node.inputs[desired_input].is_linked:
                            tree.links.new(bake_node.inputs[connect_to],
                                           node.inputs[desired_input].links[0].from_socket)

                    # Make the bake BSDF take over all outputs
                    if node.outputs["BSDF"].is_linked:
                        to_sockets = [link.to_socket for link in node.outputs["BSDF"].links]
                        while node.outputs["BSDF"].is_linked:
                            tree.links.remove(node.outputs["BSDF"].links[0])
                        for to_socket in to_sockets:
                            tree.links.new(to_socket, bake_node.outputs["BSDF"])

                    if base_black:
                        bake_node.inputs["Base Color"].default_value = [0., 0., 0., 1.]
                    else:
                        bake_node.inputs["Base Color"].default_value = [1., 1., 1., 1.]
                    if bpy.app.version < (4, 0, 0):
                        bake_node.inputs["Subsurface"].default_value = 0.0
                    elif flat_ior:
                        bake_node.inputs["IOR"].default_value = 1.0 # Without this, diffuse color gets all messed up
                    bake_node.inputs["Metallic"].default_value = 0.0
                    bake_node.inputs[SPECULAR_INPUT].default_value = 0.5
                    bake_node.inputs["Roughness"].default_value = 0.5
                    bake_node.inputs["Alpha"].default_value = 1.0

                    for desired_input, connect_to in desired_inputs.items():
                        if type(bake_node.inputs[connect_to].default_value) != type(node.inputs[desired_input].default_value):
                            # Assume for color
                            assert connect_to == "Base Color"
                            dv = node.inputs[desired_input].default_value
                            bake_node.inputs[connect_to].default_value = [dv, dv, dv, 1.]
                        else:
                            bake_node.inputs[connect_to].default_value = node.inputs[desired_input].default_value

    # Find generated bakenodes and restore their outputs, then delete them
    def restore_bsdfs(self, objects):
        desired_material_trees = {slot.material.node_tree for obj in objects
                                   for slot in obj.material_slots if slot.material}
        desired_material_trees |= {node_group for node_group in bpy.data.node_groups}

        for tree in desired_material_trees:
            for bake_node_name in [node.name for node in tree.nodes]:
                bake_node = tree.nodes[bake_node_name]
                if bake_node.type == "BSDF_PRINCIPLED" and bake_node.name[-5:] == ".BAKE":
                    # we've found a bake node, restore the outputs to their rightful owner and del
                    node = tree.nodes[bake_node.name[:-5]]

                    # Make the bake BSDF take over all outputs
                    if bake_node.outputs["BSDF"].is_linked:
                        to_sockets = [link.to_socket for link in bake_node.outputs["BSDF"].links]
                        while bake_node.outputs["BSDF"].is_linked:
                            tree.links.remove(bake_node.outputs["BSDF"].links[0])
                        for to_socket in to_sockets:
                            tree.links.new(to_socket, node.outputs["BSDF"])

                    tree.nodes.remove(bake_node)

    # filter_node_create is a function which, given a tree, returns a tuple of
    # (input, output)
    def filter_image(self, context, image, filter_create, matgroupnum, use_linear=False):
        # This is performed in our throwaway scene, so we don't have to keep settings
        context.scene.view_settings.view_transform = "Standard"
        orig_colorspace = bpy.data.images[image].colorspace_settings.name
        # Bizarrely, getting the pixels from a render result is extremely difficult.
        # To keep things simple, we perform a render here and then reload from disk.
        bpy.data.images[image].save()
        bpy.data.images[image].colorspace_settings.name = 'sRGB'
        # set up compositor
        context.scene.use_nodes = True
        tree = context.scene.node_tree
        for node in tree.nodes:
            tree.nodes.remove(node)
        image_node = tree.nodes.new(type="CompositorNodeImage")
        image_node.image = bpy.data.images[image]
        filter_input, filter_output = filter_create(context, tree, matgroupnum)
        tree.links.new(filter_input, image_node.outputs["Image"])
        viewer_node = tree.nodes.new(type="CompositorNodeComposite")
        tree.links.new(viewer_node.inputs["Alpha"], image_node.outputs["Alpha"])
        tree.links.new(viewer_node.inputs["Image"], filter_output)

        # rerender image
        context.scene.render.resolution_x = bpy.data.images[image].size[0]
        context.scene.render.resolution_y = bpy.data.images[image].size[1]
        context.scene.render.resolution_percentage = 100
        context.scene.render.filepath = bpy.data.images[image].filepath
        # Immediately overwrite when we do this
        bpy.ops.render.render(write_still=True, scene=context.scene.name)
        bpy.data.images[image].reload()
        bpy.data.images[image].colorspace_settings.name = orig_colorspace

    def denoise_create(context, tree, matgroupnum):
        denoise_node = tree.nodes.new(type="CompositorNodeDenoise")
        if context.scene.bake_pass_normal:
            normal_node = tree.nodes.new(type="CompositorNodeImage")
            normal_node.image = bpy.data.images["SCRIPT_world"+str(matgroupnum)+".png"]
            tree.links.new(denoise_node.inputs["Normal"], normal_node.outputs["Image"])
        return denoise_node.inputs["Image"], denoise_node.outputs["Image"]

    def sharpen_create(context, tree, matgroupnum):
        sharpen_node = tree.nodes.new(type="CompositorNodeFilter")
        sharpen_node.filter_type = "SHARPEN"
        sharpen_node.inputs["Fac"].default_value = 0.1
        return sharpen_node.inputs["Image"], sharpen_node.outputs["Image"]

    def deselect_all_objects():
        bpy.ops.object.select_all(action='DESELECT')

    def select_and_set_active_object(context, obj):
        obj.select_set(True)
        context.view_layer.objects.active = obj

    def print_baking_info(bake_name, objects):
        print("Baking " + bake_name + " for objects: " + ",".join(obj.name for obj in objects))

    def clear_image_if_exists(bake_name):
        if "SCRIPT_" + bake_name + ".png" in bpy.data.images:
            image = bpy.data.images["SCRIPT_" + bake_name + ".png"]
            image.user_clear()
            bpy.data.images.remove(image)

    def create_new_image(bake_name, bake_size, background_color):
        bpy.ops.image.new(name="SCRIPT_" + bake_name + ".png", width=bake_size[0], height=bake_size[1], color=background_color,
                          generated_type="BLANK", alpha=True)
        image = bpy.data.images["SCRIPT_" + bake_name + ".png"]
        image.filepath = bpy.path.abspath("//Tuxedo Bake/" + "SCRIPT_" + bake_name + ".png")
        image.alpha_mode = "STRAIGHT"
        image.generated_color = background_color
        image.generated_width = bake_size[0]
        image.generated_height = bake_size[1]
        image.scale(bake_size[0], bake_size[1])
        return image

    def set_image_colorspace(image, bake_type, bake_name):
        if bake_name == 'normal' or bake_name == 'world' or bake_name == 'smoothness':
            image.colorspace_settings.name = 'Non-Color'
        if bake_name == 'diffuse' or bake_name == 'metallic':  # For packing smoothness to alpha
            image.alpha_mode = 'CHANNEL_PACKED'

    def set_image_pixels(image, background_color, bake_size):
        image.pixels[:] = background_color * bake_size[0] * bake_size[1]

    def select_objects_for_baking(objects):
        if not objects:
            print("No objects selected!")
            return
        for obj in objects:
            obj.select_set(True)

    def change_value_node_for_materials(objects, bake_name, reverse_material_name_dict):
        for obj in objects:
            for slot in obj.material_slots:
                if slot.material:
                    for node in obj.active_material.node_tree.nodes:
                        if node.type == "VALUE" and node.label == "bake_" + bake_name + str(reverse_material_name_dict[slot.material.name]):
                            node.outputs["Value"].default_value = 1

    def assign_bake_node_for_materials(objects, bake_name, reverse_material_name_dict):
        for obj in objects:
            for slot in obj.material_slots:
                if slot.material:
                    for node in slot.material.node_tree.nodes:
                        # Assign bake node
                        tree = slot.material.node_tree
                        node = None
                        if "bake" in tree.nodes:
                            node = tree.nodes["bake"]
                        else:
                            node = tree.nodes.new("ShaderNodeTexImage")
                        node.name = "bake"
                        node.label = t('Bake.debug_bad_object')
                        node.select = True
                        node.image = bpy.data.images["SCRIPT_" + bake_name + str(reverse_material_name_dict[slot.material.name]) + ".png"]
                        tree.nodes.active = node
                        node.location.x += 500
                        node.location.y -= 500

    def run_bake(context, bake_type, bake_pass_filter, bake_samples, clear, bake_active, bake_margin, bake_multires, normal_space, bake_ray_distance, material_name_groups=dict()):
        context.scene.cycles.bake_type = bake_type
        context.scene.cycles.use_denoising = False # https://developer.blender.org/T94573
        context.scene.render.bake.use_pass_direct = "DIRECT" in bake_pass_filter
        context.scene.render.bake.use_pass_indirect = "INDIRECT" in bake_pass_filter
        context.scene.render.bake.use_pass_color = "COLOR" in bake_pass_filter
        context.scene.render.bake.use_pass_diffuse = "DIFFUSE" in bake_pass_filter
        context.scene.render.bake.use_pass_emit = "EMIT" in bake_pass_filter
        if bpy.app.version >= (2, 92, 0):
            context.scene.render.bake.target = "VERTEX_COLORS" if "VERTEX_COLORS" in bake_pass_filter else "IMAGE_TEXTURES"
        if bpy.app.version <= (3, 0, 0):
            context.scene.render.bake.use_pass_ambient_occlusion = "AO" in bake_pass_filter
        context.scene.cycles.samples = bake_samples
        context.scene.render.image_settings.color_mode = 'RGB'
        context.scene.render.bake.use_clear = clear and bake_type == 'NORMAL'
        context.scene.render.bake.use_selected_to_active = (bake_active != None)
        context.scene.render.bake.margin = bake_margin
        context.scene.render.use_bake_multires = bake_multires
        context.scene.render.bake.normal_space = normal_space
        bpy.ops.object.bake(type=bake_type,
                            # pass_filter=bake_pass_filter,
                            use_clear=clear and bake_type == 'NORMAL',
                            # uv_layer="SCRIPT",
                            use_selected_to_active=(bake_active != None),
                            cage_extrusion=bake_ray_distance,
                            normal_space=normal_space
                            )

    def reset_value_node_for_materials(objects, bake_name):
        for obj in objects:
            for slot in obj.material_slots:
                if slot.material:
                    for node in obj.active_material.node_tree.nodes:
                        if node.type == "VALUE" and node.label == "bake_" + bake_name:
                            node.outputs["Value"].default_value = 0
    
    #delete meshes with no polygons since they're fucked anyway - @989onan
    def remove_no_polygon_meshes(context, objects):
        bpy.ops.object.select_all(action='DESELECT')
        # Shallow copy for this array. I hate python sometimes and I know this is bad code. - @989onan
        newarray = []
        for obj in objects:
            newarray.append(obj) 

        objects = []
        no_polygons = []
        for obj in newarray:
            if obj.type != 'MESH':
                objects.append(obj)
                continue
            me = obj.data
            if len(me.polygons) > 0:
                objects.append(obj)
                continue
            obj.select_set(True)
        bpy.ops.object.delete(use_global=False)
        bpy.ops.object.select_all(action='DESELECT')
        return objects
    
    def optimize_solid_materials(context, objects, bake_size, solidmaterialcolors, bake_name, image):
        #solid material optimization making 4X4 squares of solid color for this pass - @989onan
        if (context.scene.bake_optimize_solid_materials and
            (not any(plat.use_decimation for plat in context.scene.bake_platforms)) and
            (not context.scene.bake_pass_ao) and (not context.scene.bake_pass_normal)):
            #arranging old pixels and assignment to image pixels this way makes only one update per pass, so many many times faster - @989onan
            old_pixels = image.pixels[:]
            old_pixels = list(old_pixels)

            #in pixels
            #Thanks to @Sacred#9619 on discord for this one.
            margin = int(math.ceil(0.0078125 * context.scene.bake_resolution / 2)) #has to be the same as "pixelmargin"
            n = int( bake_size[0]/margin )
            n2 = int( bake_size[1]/margin )
            #lastly, slap our solid squares on top of bake atlas, to make a nice solid square without interuptions from the rest of the bake - @989onan
            for obj in get_objects(objects, {"MESH"}): #grab all mesh objects being baked
                for matindex,material in enumerate(obj.data.materials):
                    if material.name in solidmaterialcolors and (bake_name+"_color") in solidmaterialcolors[material.name]:
                        index = list(solidmaterialcolors.keys()).index(material.name)

                        #in pixels
                        #Thanks to @Sacred#9619 on discord for this one.
                        X = margin/2 + margin * int( index % n )
                        Y = margin/2 + margin * int( index / n2 )
                        square_center_coord = [X,Y]

                        color = solidmaterialcolors[material.name][bake_name+"_color"]
                        #while in pixels inside image but 4 pixel padding around our solid center square position
                        for x in range(max(0,int(square_center_coord[0]-(margin/2))),min(bake_size[0], int(square_center_coord[0]+(margin/2)))):
                            for y in range(max(0,int(square_center_coord[1]-(margin/2))),min(bake_size[1], int(square_center_coord[1]+(margin/2)))):
                                for channel,rgba in enumerate(color):
                                    #since the array is one dimensional, (kinda like old minecraft schematics) we have to convert 2d cords to 1d cords, then multiply by 4 since there are 4 channels, then add current channel.
                                    old_pixels[(((y*bake_size[0])+x)*4)+channel] = rgba
            image.pixels[:] = old_pixels[:]

    # "Bake pass" function. Run a single bake to "<bake_name>.png" against all selected objects.
    def bake_pass(self, context, bake_name, bake_type, bake_pass_filter, objects, bake_size, bake_samples, bake_ray_distance, background_color, clear, bake_margin, bake_active=None, bake_multires=False,
                      normal_space='TANGENT',solidmaterialcolors=dict(),material_name_groups=dict()):
        BakeButton.deselect_all_objects()
        if bake_active is not None:
            BakeButton.select_and_set_active_object(context, bake_active)
        objects = BakeButton.remove_no_polygon_meshes(context, objects)
        BakeButton.print_baking_info(bake_name, objects)
        reverse_material_name_dict = {}
        
        for group_num,group in material_name_groups.items():
            for mat in group:
                reverse_material_name_dict[mat] = group_num
        images = [] #so we can have multi image
        for group_num,group in material_name_groups.items():
            if clear:
                BakeButton.clear_image_if_exists(bake_name + str(group_num))
                image = BakeButton.create_new_image(bake_name + str(group_num), bake_size, background_color)
                BakeButton.set_image_colorspace(image, bake_type, bake_name)
                BakeButton.set_image_pixels(image, background_color, bake_size)
            image = bpy.data.images["SCRIPT_" + bake_name + str(group_num) + ".png"]
            images.append(image)
        BakeButton.select_objects_for_baking(objects)
        for obj in objects:
            BakeButton.select_and_set_active_object(context, obj)
        BakeButton.change_value_node_for_materials(objects, bake_name, reverse_material_name_dict)
        BakeButton.assign_bake_node_for_materials(objects, bake_name, reverse_material_name_dict)
        core.materials_list_update(context) #Make sure materials list is up to date. Yes the unaccounted for materials will be added to group "0". This is fine.
        BakeButton.run_bake(context, bake_type, bake_pass_filter, bake_samples, clear, bake_active, bake_margin, bake_multires, normal_space, bake_ray_distance)
        BakeButton.reset_value_node_for_materials(objects, bake_name)
        for group_num,group in material_name_groups.items():
            imagefound = None
            #idk how to use find - @989onan
            for image in images:
                if bake_name + str(group_num) in image.name: 
                    imagefound = image
            BakeButton.optimize_solid_materials(context, objects, bake_size, solidmaterialcolors, bake_name + str(group_num), imagefound)

    def copy_ob(self, ob, parent, collection):
        # copy ob
        copy = ob.copy()
        if not 'tuxedoForcedExportName' in ob:
            copy['tuxedoForcedExportName'] = ob.name[:-4] if len(ob.name) >= 4 and ob.name[-4] == '.' else ob.name
        else:
            copy['tuxedoForcedExportName'] = ob['tuxedoForcedExportName']
        copy.data = ob.data.copy()
        copy.parent = parent
        copy.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
        # copy particle settings
        for ps in copy.particle_systems:
            ps.settings = ps.settings.copy()
        collection.objects.link(copy)
        return copy

    def tree_copy(self, ob, parent, collection, ignore_hidden, levels=3, view_layer=None, filter_func=None):
        def recurse(ob, parent, depth, ignore_hidden, view_layer=None):
            if depth > levels:
                return
            if ob.hide_get() and ob.type != 'ARMATURE' and ignore_hidden:
                return
            if view_layer and ob.name not in view_layer.objects:
                return
            if not ob.data:
                return
            if filter_func and not filter_func(ob):
                return
            copy = self.copy_ob(ob, parent, collection)

            for child in ob.children:
                recurse(child, copy, depth + 1, ignore_hidden, view_layer=view_layer)

            return copy

        return recurse(ob, ob.parent, 0, ignore_hidden, view_layer=view_layer)

    def execute(self, context):
        if not get_objects(core.get_meshes_objects(context), filter_func=lambda obj:
                           not obj.hide_get() or not context.scene.bake_ignore_hidden):
            self.report({'ERROR'}, t('tuxedo_bake.error.no_meshes'))
            return {'FINISHED'}
        if any(obj.hide_render and not obj.hide_get()
               for obj in core.get_armature(context).children
               if obj.name in context.view_layer.objects):
            self.report({'ERROR'}, t('tuxedo_bake.error.render_disabled'))
            return {'FINISHED'}
        if not bpy.data.is_saved:
            self.report({'ERROR'}, t('Bake.error_save_file'))
            return {'FINISHED'}

        # Change render engine to cycles and save the current one
        render_engine_tmp = context.scene.render.engine
        render_device_tmp = context.scene.cycles.device
        context.scene.render.engine = 'CYCLES'
        if context.scene.bake_device == 'GPU':
            context.scene.cycles.device = 'GPU'
        else:
            context.scene.cycles.device = 'CPU'

        # Change decimate settings, run bake, change them back
        tuxedo_max_tris = context.scene.tuxedo_max_tris
        decimation_remove_doubles = context.scene.decimation_remove_doubles
        decimation_animation_weighting = context.scene.decimation_animation_weighting
        decimation_animation_weighting_factor = context.scene.decimation_animation_weighting_factor
        decimation_animation_weighting_include_shapekeys = context.scene.decimation_animation_weighting_include_shapekeys
        context.scene.decimation_animation_weighting = context.scene.bake_animation_weighting
        context.scene.decimation_animation_weighting_factor = context.scene.bake_animation_weighting_factor
        context.scene.decimation_animation_weighting_include_shapekeys = context.scene.bake_animation_weighting_include_shapekeys
        
        core.materials_list_update(context) #Make sure materials list is up to date. Yes the unaccounted for materials will be added to group "0". This is fine.
        
        self.perform_bake(context)

        context.scene.tuxedo_max_tris = tuxedo_max_tris
        context.scene.decimation_remove_doubles = decimation_remove_doubles
        context.scene.decimation_animation_weighting = decimation_animation_weighting
        context.scene.decimation_animation_weighting_factor = decimation_animation_weighting_factor
        context.scene.decimation_animation_weighting_include_shapekeys = decimation_animation_weighting_include_shapekeys

        # Change render engine back to original
        context.scene.render.engine = render_engine_tmp
        context.scene.cycles.device = render_device_tmp

        return {'FINISHED'}

    #this samples curve to recalculate original smoothness to new smoothness
    def sample_curve_smoothness(self,sample_val):
        samplecurve = [0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000334,0.000678,0.001033,0.001400,0.001779,0.002170,0.002575,0.002993,0.003424,0.003871,0.004332,0.004808,0.005301,0.005810,0.006335,0.006878,0.007439,0.008018,0.008616,0.009233,0.009870,0.010527,0.011204,0.011903,0.012624,0.013367,0.014132,0.014920,0.015732,0.016568,0.017429,0.018314,0.019225,0.020163,0.021126,0.022117,0.023134,0.024180,0.025255,0.026358,0.027490,0.028652,0.029845,0.031068,0.032323,0.033610,0.034928,0.036280,0.037664,0.039083,0.040535,0.042022,0.043544,0.045102,0.046696,0.048327,0.049994,0.051699,0.053442,0.055224,0.057045,0.058905,0.060805,0.062745,0.064729,0.066758,0.068831,0.070948,0.073109,0.075311,0.077555,0.079841,0.082166,0.084531,0.086935,0.089377,0.091856,0.094371,0.096923,0.099510,0.102131,0.104786,0.107474,0.110195,0.112947,0.115729,0.118542,0.121385,0.124256,0.127155,0.130082,0.133035,0.136013,0.139018,0.142046,0.145098,0.148173,0.151270,0.154389,0.157529,0.160689,0.163868,0.167066,0.170282,0.173515,0.176765,0.180030,0.183310,0.186605,0.189914,0.193235,0.196569,0.199914,0.203270,0.206635,0.210011,0.213395,0.216786,0.220185,0.223591,0.227002,0.230418,0.233838,0.237263,0.240690,0.244119,0.247549,0.250980]

        #256 values in curve
        return samplecurve[round(255*sample_val)]

    #this samples for roughness map curve
    def sample_curve_roughness(self,sample_val):
        samplecurve = [0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.002133,0.004309,0.006529,0.008791,0.011097,0.013447,0.015840,0.018276,0.020756,0.023280,0.025847,0.028459,0.031114,0.033813,0.036557,0.039344,0.042176,0.045053,0.047973,0.050938,0.053948,0.057002,0.060102,0.063245,0.066434,0.069668,0.072947,0.076271,0.079640,0.083054,0.086514,0.090019,0.093570,0.097166,0.100808,0.104495,0.108229,0.112008,0.115834,0.119705,0.123623,0.127586,0.131596,0.135653,0.139756,0.143905,0.148101,0.152343,0.156633,0.160969,0.165352,0.169782,0.174259,0.178784,0.183355,0.187974,0.192640,0.197354,0.202115,0.206924,0.211781,0.216685,0.221637,0.226637,0.231685,0.236781,0.241926,0.247118,0.252359,0.257648,0.262986,0.268372,0.273807,0.279291,0.284823,0.290404,0.296035,0.301714,0.307442,0.313220,0.319046,0.324922,0.330848,0.336823,0.342847,0.348921,0.355045,0.361219,0.367443,0.373716,0.380040,0.386413,0.392837,0.399311,0.405836,0.412410,0.419036,0.425712,0.432438,0.439216,0.446181,0.453467,0.461066,0.468971,0.477176,0.485674,0.494457,0.503519,0.512853,0.522451,0.532307,0.542413,0.552764,0.563351,0.574168,0.585208,0.596464,0.607929,0.619596,0.631458,0.643508,0.655739,0.668144,0.680716,0.693449,0.706335,0.719367,0.732538,0.745842,0.759271,0.772819,0.786478,0.800241,0.814102,0.828054,0.842089,0.856201,0.870382,0.884626,0.898926,0.913275,0.927665,0.942090,0.956543,0.971017,0.985505,1.000000]

        #256 values in curve
        return samplecurve[round(255*sample_val)]

    #needed because it likes to pause blender entirely for a key input in console and we don't want that garbage - @989onan
    def compile_gmod_tga(self,steam_library_path,images_path,texturename):

        print("Start Texture bake for \""+texturename+"\".")
        #this prevents the sub process for asking for stoopid key input. YEET! Or is supposed to... https://stackoverflow.com/a/23478570
        proc = subprocess.Popen([steam_library_path+"steamapps/common/GarrysMod/bin/vtex.exe", "-nopause", "-mkdir", images_path+"materialsrc/"+texturename])
        proc.wait()
        print("Finished Texture bake for \""+texturename+"\"!")

    def perform_bake(self, context: bpy.types.Context):
        is_unittest = context.scene.tuxedo_is_unittest
        if is_unittest:

            # for version consistency we use old style margins here. Really there should be a second set
            # of test cases
            if 'render.bake.margin_type' in context.scene:
                context.scene.render.bake.margin_type = 'EXTEND'

        print('START BAKE')
        # Global options
        resolution = context.scene.bake_resolution
        steam_library_path = context.scene.bake_steam_library.replace("\\", "/")
        generate_uvmap = context.scene.bake_generate_uvmap
        prioritize_face = context.scene.bake_prioritize_face
        prioritize_factor = context.scene.bake_face_scale
        uv_overlap_correction = context.scene.bake_uv_overlap_correction
        pack_uvs = (not uv_overlap_correction == "MANUALNOPACK")
        margin = 0.0078125 # we want a 1-pixel margin around each island at 256x256, so 1/256, and since it's the space between islands we multiply it by two
        quick_compare = True
        apply_keys = context.scene.bake_apply_keys
        optimize_solid_materials = context.scene.bake_optimize_solid_materials
        unwrap_angle = context.scene.bake_unwrap_angle

        # Tweaks for 'draft' quality
        draft_quality = context.scene.bake_use_draft_quality
        if draft_quality:
            resolution = min(resolution, 1024)
        draft_render = is_unittest or draft_quality
        pixelmargin = int(math.ceil(margin * resolution / 2))

        # Passes
        pass_diffuse = context.scene.bake_pass_diffuse
        pass_normal = context.scene.bake_pass_normal
        pass_smoothness = context.scene.bake_pass_smoothness
        pass_ao = context.scene.bake_pass_ao
        pass_emit = context.scene.bake_pass_emit
        pass_alpha = context.scene.bake_pass_alpha
        pass_metallic = context.scene.bake_pass_metallic
        pass_displacement = context.scene.bake_pass_displacement
        pass_detail = context.scene.bake_pass_detail
        pass_thickness = False

        # Pass options
        illuminate_eyes = context.scene.bake_illuminate_eyes
        supersample_normals = context.scene.bake_pass_normal
        emit_indirect = context.scene.bake_emit_indirect
        emit_exclude_eyes = context.scene.bake_emit_exclude_eyes
        cleanup_shapekeys = context.scene.bake_cleanup_shapekeys # Reverted and _old shapekeys
        ignore_hidden = context.scene.bake_ignore_hidden
        diffuse_indirect = context.scene.bake_diffuse_indirect
        diffuse_indirect_opacity = context.scene.bake_diffuse_indirect_opacity

        # Filters
        sharpen_bakes = context.scene.bake_sharpen
        denoise_bakes = context.scene.bake_denoise

        #also disable optimize solid materials if other things are enabled that will break it
        optimize_solid_materials = optimize_solid_materials and (not any(plat.use_decimation for plat in context.scene.bake_platforms)) and (not pass_ao) and (not pass_normal)

        # Save reference to original armature
        armature = core.get_armature(context)
        orig_armature_name = armature.name

        # Create an output collection
        collection = bpy.data.collections.new("Tuxedo Bake")
        context.scene.collection.children.link(collection)

        # Make note of the original object name, then name it a placeholder
        orig_largest_obj_name = sorted(get_objects(armature.children, {"MESH"},
                                                   filter_func=lambda obj:
                                                   not obj.hide_get()),
            key=lambda obj: obj.dimensions.x * obj.dimensions.y * obj.dimensions.z,
            reverse=True)[0].name
        if len(orig_largest_obj_name) >= 4 and orig_largest_obj_name[-4] == '.':
            orig_largest_obj_name = orig_largest_obj_name[:-4]
            
        #generate structure for storing which materials should be grouped for multi-material bake output
        material_name_groups = {}
        reverse_material_name_dict = {}

        for i in context.scene.bake_material_groups:
            if not material_name_groups.get(i.group):
                material_name_groups[i.group] = []
            
            material_name_groups[i.group].append(i.name)
        
        for group_num,group in material_name_groups.items():
            for mat in group:
                reverse_material_name_dict[mat] = group_num

        # Tree-copy all meshes - exclude copy-only, and copy them just before export
        arm_copy = self.tree_copy(armature, None, collection, ignore_hidden,
                                  view_layer=context.view_layer, filter_func=not_copyonly)

        # Create an extra scene to render in
        orig_scene_name = context.scene.name
        orig_view_layer = context.view_layer
        bpy.ops.scene.new(type="EMPTY") # copy keeps existing settings
        context.scene.name = "Tuxedo Scene"
        orig_scene = bpy.data.scenes[orig_scene_name]
        context.scene.collection.children.link(collection)
        tuxedo_world = bpy.data.worlds.new("Tuxedo World")
        context.scene.world = tuxedo_world
        if draft_quality:
            context.scene.render.use_simplify = True
            bpy.context.scene.render.simplify_subdivision_render = 1

        # Make sure all armature modifiers target the new armature
        for obj in get_objects(collection.all_objects):
            for modifier in obj.modifiers:
                if modifier.type == "ARMATURE":
                    modifier.object = arm_copy
                if modifier.type == "MULTIRES":
                    modifier.render_levels = modifier.total_levels
            #moved weight paint cleanup to inside the platforms because this interferes with Gmod needing a certain weight cleanup method - @989onan

        # Copy default values from the largest diffuse BSDF
        objs_size_descending = sorted(get_objects(collection.all_objects, {"MESH"}),
            key=lambda obj: obj.dimensions.x * obj.dimensions.y * obj.dimensions.z,
            reverse=True)

        def first_bsdf(objs):
            for obj in get_objects(objs_size_descending):
                for slot in obj.material_slots:
                    if slot.material:
                        tree = slot.material.node_tree
                        for node in tree.nodes:
                            if node.type == "BSDF_PRINCIPLED":
                                return node

        bsdf_original = first_bsdf(objs_size_descending)
        tuxedo_uv_layers = set()

        #first fix broken colors by adding their textures, then add the results of color only materials/solid textures to see if they need special UV treatment.
        #To detect and fix UV's for materials that are solid and don't need entire uv maps if all the textures are consistent throught. Also adds solid textures for BSDF's with default values but no texture
        solidmaterialnames = dict()

        #to store the colors for each pass for each solid material to apply to bake atlas later.
        solidmaterialcolors = dict()
        if optimize_solid_materials:
            for obj in get_objects(collection.all_objects, {"MESH"}):
                for matindex,material in enumerate(obj.data.materials):
                    for node in material.node_tree.nodes:
                        if node.type == "BSDF_PRINCIPLED":#For each material bsdf in every object in each material

                            def check_if_tex_solid(bsdfinputname,node_prinipled):
                                node_image = node_prinipled.inputs[bsdfinputname].links[0].from_node
                                if node_image.type != "TEX_IMAGE": #To catch normal maps
                                    return [False,[0.,0.,0.,1.]] #if not image then it's some type of node chain that is too complicated so return false
                                old_pixels = node_image.image.pixels[:]
                                solidimagepixels = np.tile(old_pixels[0:4], int(len(old_pixels)/4))
                                if np.array_equal(solidimagepixels,old_pixels):
                                    return [True,old_pixels[0:4]]
                                return [False,[0.,0.,0.,1.]]

                            #each pass below makes solid color textures or reads the texture and checks if it's solid using numpy.
                            node_prinipled = node
                            solid_colors = {
                                "diffuse": [0.,0.,0.,1.],
                                "smoothness": [0.,0.,0.,1.],
                                "metallic": [0.,0.,0.,1.],
                                "alpha": [1.,1.,1.,1.],
                            }
                            for (use_pass, pass_key, pass_slot) in [
                                    (pass_diffuse, "diffuse", "Base Color"),
                                    (pass_emit, "emit", EMISSION_INPUT),
                                    (pass_smoothness, "smoothness", "Roughness"),
                                    (pass_metallic, "metallic", "Metallic"),
                                    (pass_alpha, "alpha", "Alpha"),
                            ]:
                                if use_pass:
                                    if not node.inputs[pass_slot].is_linked:
                                        node_image = material.node_tree.nodes.new(type="ShaderNodeTexImage")
                                        node_image.image = bpy.data.images.new(pass_slot, width=8, height=8, alpha=True)
                                        node_image.location = (1101, -500)
                                        node_image.label = pass_slot

                                        #assign to image so it's baked
                                        node_image.image.generated_color = node.inputs[pass_slot].default_value
                                        solid_colors[pass_key] = node.inputs[pass_slot].default_value
                                        node_image.image.file_format = 'PNG'
                                        material.node_tree.links.new(node_image.outputs['Color'], node_prinipled.inputs['Base Color'])
                                    else:
                                        pass_solid,pass_color = check_if_tex_solid(pass_slot,node_prinipled)
                                        if pass_solid:
                                            solid_colors[pass_key] = pass_color
                                        else:
                                            del solid_colors[pass_key]

                            #now we check based on all the passes if our material is solid.
                            if all(pass_key in solid_colors for pass_key in ["diffuse", "smoothness", "metallic", "alpha"]) or "emit" in solid_colors:
                                solidmaterialnames[obj.data.materials[matindex].name] = len(solidmaterialnames) #put materials into an index order because we wanna put them into a grid
                                solidmaterialcolors[obj.data.materials[matindex].name] = {"diffuse_color":solid_colors['diffuse'],
                                                                                            "emission_color":solid_colors.get('emit', [0., 0., 0., 1.]),
                                                                                            "smoothness_color":solid_colors['smoothness'],
                                                                                            "metallic_color":solid_colors['metallic'],
                                                                                            "alpha_color":solid_colors['alpha']}
                                print("Object: \""+obj.name+"\" with Material: \""+obj.data.materials[matindex].name+"\" is solid!")
                            else:
                                print("Object: \""+obj.name+"\" with Material: \""+obj.data.materials[matindex].name+"\" is NOT solid!")
                                pass #don't put an entry, and assume if there is no entry, then it isn't solid.

                            break #since we found our principled and did our stuff we can break the node scanning loop on this material.

        if generate_uvmap:
            bpy.ops.object.select_all(action='DESELECT')
            # Make copies of the currently render-active UV layer, name "Tuxedo UV"
            for obj in get_objects(collection.all_objects, {"MESH"}):
                obj.select_set(True)
                context.view_layer.objects.active = obj
                # make sure to copy the render-active UV only
                active_uv = None
                for uvmap in obj.data.uv_layers:
                    if uvmap.active_render:
                        obj.data.uv_layers.active = uvmap
                        active_uv = uvmap
                reproject_anyway = (len(obj.data.uv_layers) == 0 or
                                    all(set(loop.uv[:]).issubset({0,1}) for loop in active_uv.data))
                bpy.ops.mesh.uv_texture_add()
                obj.data.uv_layers[-1].name = 'Tuxedo UV'
                tuxedo_uv_layers.add('Tuxedo UV')
                if supersample_normals:
                    bpy.ops.mesh.uv_texture_add()
                    obj.data.uv_layers[-1].name = 'Tuxedo UV Super'
                    tuxedo_uv_layers.add('Tuxedo UV Super')

                if uv_overlap_correction == "REPROJECT" or reproject_anyway:
                    for layer in tuxedo_uv_layers:
                        idx = obj.data.uv_layers.active_index
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.data.uv_layers[layer].active = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        for matindex,material in enumerate(obj.data.materials):
                            #select each material individually and unwrap. The averaging and packing will take care of overlaps. - @989onan
                            bpy.ops.mesh.select_all(action='DESELECT')
                            obj.active_material_index = matindex
                            bpy.ops.object.material_slot_select()

                            bpy.ops.uv.select_all(action='SELECT')
                            bpy.ops.uv.smart_project(angle_limit=unwrap_angle, island_margin=margin)
                        bpy.ops.object.mode_set(mode='OBJECT')
                        obj.data.uv_layers.active_index = idx
                elif uv_overlap_correction == "UNMIRROR":
                    # TODO: issue a warning if any source images don't use 'wrap'
                    # Select all faces in +X
                    print("Un-mirroring source Tuxedo UV data")
                    uv_layer = (obj.data.uv_layers["Tuxedo UV Super"].data if
                               supersample_normals else
                               obj.data.uv_layers["Tuxedo UV"].data)
                    for poly in obj.data.polygons:
                        if poly.center[0] > 0:
                            for loop in poly.loop_indices:
                                uv_layer[loop].uv.x += 1
                elif uv_overlap_correction in ["MANUAL", "MANUALNOPACK"]:
                    if "Target" in obj.data.uv_layers:
                        for idx, loop in enumerate(obj.data.uv_layers["Target"].data):
                            obj.data.uv_layers["Tuxedo UV"].data[idx].uv = loop.uv
                            if supersample_normals:
                                obj.data.uv_layers["Tuxedo UV Super"].data[idx].uv = loop.uv

            #PLEASE DO THIS TO PREVENT PROBLEMS WITH UV EDITING LATER ON:
            bpy.data.scenes["Tuxedo Scene"].tool_settings.use_uv_select_sync = False

            if optimize_solid_materials:
                #go through the solid materials on all the meshes and scale their UV's down to 0 in a grid of rows of squares so that they bake on a small separate part of the image mostly in the top left -@989onan
                for obj in get_objects(collection.all_objects, {"MESH"}):
                    for matindex,material in enumerate(obj.data.materials):
                        if material.name in solidmaterialnames:
                            for layer in tuxedo_uv_layers:
                                print("processing solid material: \""+material.name+"\" on layer: \""+layer+"\" on object: \""+obj.name+"\"")
                                idx = obj.data.uv_layers.active_index
                                obj.data.uv_layers[layer].active = True
                                bpy.ops.object.mode_set(mode='EDIT')
                                #deselect all geometry and uv, select material that we are on that is solid, and then select all on visible UV. This will isolate the solid material UV's on this layer and object.

                                bpy.ops.mesh.select_all(action='SELECT') #select all mesh
                                bpy.ops.uv.select_all(action='DESELECT') #deselect all UV
                                bpy.ops.mesh.select_all(action='DESELECT') #deselect all mesh

                                bpy.ops.mesh.select_mode(type="FACE")
                                bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
                                obj.active_material_index = matindex
                                bpy.ops.object.material_slot_select() #select our material on mesh
                                bpy.ops.uv.select_all(action='SELECT') #select all uv

                                #https://blender.stackexchange.com/a/75095
                                #Scale a 2D vector v, considering a scale s and a pivot point p
                                def Scale2D( v, s, p ):
                                    return ( p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]) )

                                bpy.ops.object.mode_set(mode='OBJECT')#idk why this has to be here but it breaks without it - @989onan
                                index = solidmaterialnames[material.name]

                                #Thanks to @Sacred#9619 on discord for this one.
                                squaremargin = pixelmargin
                                n = int( resolution/squaremargin )
                                X = squaremargin/2 + squaremargin * int( index % n )
                                Y = squaremargin/2 + squaremargin * int( index / n )

                                uv_layer = obj.data.uv_layers[layer].data
                                for poly in obj.data.polygons:
                                    for loop in poly.loop_indices:
                                        if uv_layer[loop].select: #make sure that it is selected (only visible will be selected in this case)
                                            #Here we scale the UV's down to 0 starting at the bottom left corner and going up row by row of solid materials.
                                            uv_layer[loop].uv = Scale2D( uv_layer[loop].uv, (0,0), ((X/resolution),(Y/resolution))  )
                                bpy.ops.object.mode_set(mode='EDIT')
                                #deselect UV's and hide mesh for scaling uv's out the way later. this also prevents the steps for averaging islands and prioritizing head size from going bad later.
                                bpy.ops.uv.select_all(action='DESELECT')
                                bpy.ops.mesh.hide(unselected=False)

            # Select all meshes. Select all UVs. Average islands scale
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            for layer in tuxedo_uv_layers:
                bpy.ops.object.mode_set(mode='OBJECT')
                if pack_uvs:
                    for obj in get_objects(collection.all_objects, {"MESH"}):
                        obj.data.uv_layers.active = obj.data.uv_layers[layer]
                        context.view_layer.objects.active = obj
                        obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.uv.select_all(action='SELECT')
                    bpy.ops.uv.average_islands_scale()  # Use blender average so we can make our own tweaks.
                    bpy.ops.object.mode_set(mode='OBJECT')

            # Scale up textures most likely to be looked closer at (in this case, eyes)
            if prioritize_face and pack_uvs:
                for obj in get_objects(collection.all_objects, {"MESH"}):
                    # Build set of relevant vertices
                    affected_vertices = set()
                    for group in ['LeftEye', 'lefteye', 'Lefteye', 'Eye.L', "Eye_L", 'RightEye', 'righteye', 'Righteye', 'Eye.R', "Eye_R"]:
                        if group in obj.vertex_groups:
                            vgroup_idx = obj.vertex_groups[group].index
                            for vert in obj.data.vertices:
                                if any(v_group.group == vgroup_idx and v_group.weight > 0. for v_group in vert.groups):
                                    affected_vertices.add(vert.index)

                    # Then for each UV (cause of the viewport thing) scale up by the selected factor
                    for layer in tuxedo_uv_layers:
                        uv_layer = obj.data.uv_layers[layer].data
                        for poly in obj.data.polygons:
                            if all(vert_idx in affected_vertices for vert_idx in poly.vertices):
                                for loop in poly.loop_indices:
                                    uv_layer[loop].uv.x *= prioritize_factor
                                    uv_layer[loop].uv.y *= prioritize_factor

            # Pack islands. Optionally use UVPackMaster if it's available
            for layer in tuxedo_uv_layers:
                for obj in get_objects(collection.all_objects, {"MESH"}):
                    obj.data.uv_layers.active = obj.data.uv_layers[layer]
                    obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.reveal()
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.select_all(action='SELECT')
                # have a UI-able toggle, if UVP is detected, to keep lock overlapping in place
                # otherwise perform blender pack here

                if pack_uvs:
                    if not context.scene.uvp_lock_islands:
                        if bpy.app.version < (3, 6, 0) or not is_unittest:
                            bpy.ops.uv.pack_islands(rotate=True, margin=margin)
                        else:
                            bpy.ops.uv.pack_islands(rotate=True, margin=margin, rotate_method="AXIS_ALIGNED")

                    # detect if UVPackMaster installed and configured: apparently UVP doesn't always
                    # self-initialize? So just force it
                    # if 'uvpm3_props' in context.scene:
                    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
                    try:
                        context.scene.uvpm3_props.normalize_islands = False
                        # Tuxedo UV Super is where we do the World normal bake, so it must be totally
                        # non-overlapping.
                        context.scene.uvpm3_props.lock_overlapping_enable = layer != 'Tuxedo UV Super'
                        context.scene.uvpm3_props.lock_overlapping_mode = '2'
                        context.scene.uvpm3_props.pack_to_others = False
                        context.scene.uvpm3_props.margin = margin
                        context.scene.uvpm3_props.simi_threshold = 3
                        context.scene.uvpm3_props.precision = 1000
                        context.scene.uvpm3_props.rotation_enable = True
                        context.scene.uvpm3_props.rotation_step = 90
                        
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        context.view_layer.objects.active = obj
                        bpy.ops.object.mode_set(mode='OBJECT')

                        
                        for group_num,group in material_name_groups.items():
                            #iterate over every material in said group, select that material on all meshes
                            bpy.ops.object.select_all(action='DESELECT')
                            for material_name in group:
                                print("selecting material "+material_name+" in group "+str(group_num))
                                
                                for mesh in core.get_meshes_objects(context, armature_name=core.get_armature(context).name):
                                    context.view_layer.objects.active = mesh
                                    mesh.select_set(True)
                                    bpy.ops.object.mode_set(mode='EDIT')
                                    for mat_index,matslot in enumerate(mesh.material_slots):
                                        if matslot.material:
                                            if matslot.material.name == material_name:
                                                #select material on all meshes
                                                mesh.active_material_index = mat_index
                                                bpy.ops.object.material_slot_select()

                                   
                                    bpy.ops.object.mode_set(mode='OBJECT')
                                    mesh.select_set(False)
                                
                            bpy.ops.object.select_all(action='SELECT')
                            bpy.ops.object.mode_set(mode='EDIT')
                            
                            print("Group " +str(group) + " selected. Packing islands")
                            # Give UVP a static number of iterations to do TODO: make this configurable?
                            for _ in range(1, 3):
                                bpy.ops.uvpackmaster3.pack(mode_id='pack.single_tile')
                            
                            #deselect mesh geometry in preperation for next group
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.mode_set(mode='OBJECT')
                        
                    except:
                        try:
                            context.scene.uvp2_props.normalize_islands = False
                            context.scene.uvp2_props.lock_overlapping_mode = ('0' if
                                                                              layer == 'Tuxedo UV Super' else
                                                                              '2')
                            context.scene.uvp2_props.pack_to_others = False
                            context.scene.uvp2_props.margin = margin
                            context.scene.uvp2_props.similarity_threshold = 3
                            context.scene.uvp2_props.precision = 1000
                            
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            context.view_layer.objects.active = obj
                            bpy.ops.object.mode_set(mode='OBJECT')
                            
                            for group_num,group in material_name_groups.items():
                                #iterate over every material in said group, select that material on all meshes
                                bpy.ops.object.select_all(action='DESELECT')
                                for material_name in group:
                                    print("selecting material "+material_name+" in group "+str(group_num))
                                    
                                    for mesh in core.get_meshes_objects(context, armature_name=core.get_armature(context).name):
                                        context.view_layer.objects.active = mesh
                                        mesh.select_set(True)
                                        bpy.ops.object.mode_set(mode='EDIT')
                                        for mat_index,matslot in enumerate(mesh.material_slots):
                                            if matslot.material:
                                                if matslot.material.name == material_name:
                                                    #select material on all meshes
                                                    mesh.active_material_index = mat_index
                                                    bpy.ops.object.material_slot_select()

                                       
                                        bpy.ops.object.mode_set(mode='OBJECT')
                                        mesh.select_set(False)
                                    
                                bpy.ops.object.select_all(action='SELECT')
                                bpy.ops.object.mode_set(mode='EDIT')
                                
                                print("Group " +str(group) + " selected. Packing islands")
                                # Give UVP a static number of iterations to do TODO: make this configurable?
                                for _ in range(1, 3):
                                    bpy.ops.uvpackmaster2.uv_pack()
                                
                                #deselect mesh geometry in preperation for next group
                                bpy.ops.mesh.select_all(action='DESELECT')
                                bpy.ops.object.mode_set(mode='OBJECT')
                            
                        except:
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            context.view_layer.objects.active = obj
                            bpy.ops.object.mode_set(mode='OBJECT')
                        
                            for group_num,group in material_name_groups.items():
                                #iterate over every material in said group, select that material on all meshes
                                bpy.ops.object.select_all(action='DESELECT')
                                for material_name in group:
                                    print("selecting material "+material_name+" in group "+str(group_num))
                                    
                                    for mesh in core.get_meshes_objects(context, armature_name=core.get_armature(context).name):
                                        context.view_layer.objects.active = mesh
                                        mesh.select_set(True)
                                        bpy.ops.object.mode_set(mode='EDIT')
                                        for mat_index,matslot in enumerate(mesh.material_slots):
                                            if matslot.material:
                                                if matslot.material.name == material_name:
                                                    #select material on all meshes
                                                    mesh.active_material_index = mat_index
                                                    bpy.ops.object.material_slot_select()

                                       
                                        bpy.ops.object.mode_set(mode='OBJECT')
                                        mesh.select_set(False)
                                    
                                bpy.ops.object.select_all(action='SELECT')
                                bpy.ops.object.mode_set(mode='EDIT')
                                
                                print("Group " +str(group) + " selected. Packing islands")
                                if bpy.app.version < (3, 6, 0) or not is_unittest:
                                    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
                                else:
                                    bpy.ops.uv.pack_islands(rotate=True, margin=margin, rotate_method="AXIS_ALIGNED")
                                
                                #deselect mesh geometry in preperation for next group
                                bpy.ops.mesh.select_all(action='DESELECT')
                                bpy.ops.object.mode_set(mode='OBJECT')
                                
                            pass

                bpy.ops.object.mode_set(mode='OBJECT')

            if optimize_solid_materials:
                #unhide geometry from step before pack islands that fixed solid material uvs, then scale uv's to be short enough to avoid color squares at top right. - @989onan
                for obj in get_objects(collection.all_objects, {"MESH"}):
                    for layer in tuxedo_uv_layers:
                        idx = obj.data.uv_layers.active_index
                        obj.data.uv_layers[layer].active = True
                        bpy.ops.object.mode_set(mode='EDIT')

                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.uv.select_all(action='SELECT')

                        #https://blender.stackexchange.com/a/75095
                        #Scale a 2D vector v, considering a scale s and a pivot point p
                        def Scale2D( v, s, p ):
                            return ( p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]) )

                        last_index = len(solidmaterialnames)

                        #Thanks to @Sacred#9619 on discord for this one.
                        squaremargin = pixelmargin
                        n = int( resolution/squaremargin )
                        Y = squaremargin/2 + squaremargin * int( last_index / n )

                        bpy.ops.object.mode_set(mode='OBJECT')#idk why this has to be here but it breaks without it - @989onan
                        for poly in obj.data.polygons:
                            for loop in poly.loop_indices:
                                uv_layer = obj.data.uv_layers[layer].data
                                if uv_layer[loop].select: #make sure that it is selected (only visible will be selected in this case)
                                    #scale UV upwards so square stuff below can fit for solid colors
                                    uv_layer[loop].uv = Scale2D( uv_layer[loop].uv, (1,1-((Y+(pixelmargin+squaremargin))/resolution)), (0,1) )

                    #unhide all mesh polygons from our material hiding for scaling
                    for layer in tuxedo_uv_layers:
                        idx = obj.data.uv_layers.active_index
                        obj.data.uv_layers[layer].active = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.uv.select_all(action='SELECT')
                        bpy.ops.mesh.reveal(select=True)
                        bpy.ops.object.mode_set(mode='OBJECT') #below will error if it isn't in object because of poll error

            #lastly make our target UV map active
            for obj in get_objects(collection.all_objects, {"MESH"}):
                obj.data.uv_layers.active = obj.data.uv_layers["Tuxedo UV"]

        if os.path.exists(bpy.path.abspath("//Tuxedo Bake/")):
            shutil.rmtree(bpy.path.abspath("//Tuxedo Bake/"))
        os.mkdir(bpy.path.abspath("//Tuxedo Bake/"))

        # Perform 'Bake' renders: non-normal that never perform ray-tracing
        for (bake_conditions, bake_name, bake_type, bake_pass_filter, background_color,
             desired_inputs, use_linear, invert, flat_ior) in [
                 (pass_diffuse, "diffuse", "DIFFUSE", {"COLOR"}, [0.5, 0.5, 0.5, 1.], {"Base Color": "Base Color"}, False, False, True),
                 (pass_smoothness, "smoothness", "DIFFUSE", {"COLOR"}, [1., 1., 1., 1.], {"Roughness": "Base Color"}, True, True, True),
                 (pass_alpha, "alpha", "DIFFUSE", {"COLOR"}, [1, 1, 1, 1.], {"Alpha": "Alpha"}, False, False, True),
                 (pass_metallic, "metallic", "DIFFUSE", {"COLOR"}, [1., 1., 1., 1.], {"Metallic": "Metallic"}, False, True, True),
                 (pass_emit and not emit_indirect, "emission", "EMIT", set(), [0, 0, 0, 1.], {EMISSION_INPUT: EMISSION_INPUT, "Emission Strength": "Emission Strength"}, False, False, True),
                 (pass_detail, "detail", "EMIT", set(), [0, 0, 0, 1.], {EMISSION_INPUT: EMISSION_INPUT}, False, False, True),
        ]:
            # TODO: Linearity will be determined by end channel. Alpha is linear, RGB is sRGB
            if bake_conditions:
                self.genericize_bsdfs(get_objects(collection.all_objects, {"MESH"}),
                                      desired_inputs, flat_ior=flat_ior)
                #assert bake_name != "smoothness"
                self.bake_pass(context, bake_name, bake_type, bake_pass_filter,
                               get_objects(collection.all_objects, {"MESH"}),
                               (resolution, resolution), 1 if draft_render else 32, 0,
                               background_color, True, pixelmargin,
                               solidmaterialcolors=solidmaterialcolors,material_name_groups=material_name_groups)
                self.restore_bsdfs(get_objects(collection.all_objects, {"MESH"}))

                if invert:
                    for matgroup in material_name_groups.keys():
                        pixel_buffer = img_channels_as_nparray("SCRIPT_" + bake_name + str(matgroup) + ".png")
                        pixel_buffer[:3] -= 1.0
                        nparray_channels_to_img("SCRIPT_" + bake_name + str(matgroup) + ".png", np.abs(pixel_buffer))

                if sharpen_bakes:
                    for matgroup in material_name_groups.keys():
                        self.filter_image(context, "SCRIPT_" + bake_name + str(matgroup) + ".png", BakeButton.sharpen_create,
                                          use_linear = use_linear, matgroupnum=matgroup)

        # Bake displacement sides A and B, make one negative, select greater magnitude, normalize from 0 to 1
        if pass_displacement:
            self.swap_inputs(get_objects(collection.all_objects, {"MESH"}),
                              {"Surface": "Displacement"}, "OUTPUT_MATERIAL")

            self.prepare_displacement(get_objects(collection.all_objects, {"MESH"}),
                                      inverted=False)
            self.bake_pass(context, "displacement", "EMIT", {},
                           get_objects(collection.all_objects, {"MESH"}),
                           (resolution, resolution), 1 if draft_render else 32, 0,
                           [0., 0., 0., 1.], True, pixelmargin,
                           solidmaterialcolors=solidmaterialcolors,material_name_groups=material_name_groups)
            self.prepare_displacement(get_objects(collection.all_objects, {"MESH"}),
                                      restore=True)

            self.prepare_displacement(get_objects(collection.all_objects, {"MESH"}),
                                      inverted=True)
            self.bake_pass(context, "displacement_inverse", "EMIT", {},
                           get_objects(collection.all_objects, {"MESH"}),
                           (resolution, resolution), 1 if draft_render else 32, 0,
                           [0., 0., 0., 1.], True, pixelmargin,
                           solidmaterialcolors=solidmaterialcolors,material_name_groups=material_name_groups)
            self.prepare_displacement(get_objects(collection.all_objects, {"MESH"}),
                                      restore=True)
            # TODO: we could also account for multires displacement by adding the bake result to the
            # above, but detaching displacements first

            self.swap_inputs(get_objects(collection.all_objects, {"MESH"}),
                              {"Surface": "Displacement"}, "OUTPUT_MATERIAL")
            for matgroup in material_name_groups.keys():
                # The above creates two images with their green channels either positive or negative
                # displacement. Here we map that back into a single image around 0.5
                dp1 = img_channels_as_nparray("SCRIPT_displacement"+ str(matgroup) +".png")
                dp2 = img_channels_as_nparray("SCRIPT_displacement_inverse"+ str(matgroup) +".png")
                # normalize each 0 to 1 using the same magnitude
                # always expect 'min' for each to be 0, so skip that
                overall_max = max(dp1[1], dp2[1])
                with open(bpy.path.abspath("//Tuxedo Bake/displacement"+ str(matgroup) +".txt"), "w") as fi:
                    # The height value in the shader does (x * height) - (height/2), which means the
                    # total magnitude (min - max) is = height. overall_max is only the positive or
                    # negative component of our height (whichever is greater) so we need to double it.
                    fi.write("Height Value: {}".format(overall_max * 2.))
                if overall_max > 0.:
                    dp1[1] = dp1[1]/overall_max
                    dp2[1] = - dp2[1]/overall_max
                    # mix, then map to 0 to 1
                    dp1[1] += dp2[1]
                    dp1[1] = (dp1[1] + 1.) / 2.

                    nparray_channels_to_img("SCRIPT_displacement"+ str(matgroup) +".png", dp1)
                    bpy.data.images["SCRIPT_displacement"+ str(matgroup) +".png"].save()

        # Save and disable shape keys
        shapekey_values = dict()
        if not apply_keys:
            for obj in get_objects(collection.all_objects):
                if core.has_shapekeys(obj):
                    # This doesn't work for keys which have different starting
                    # values... but generally that's not what you should do anyway
                    for key in obj.data.shape_keys.key_blocks:
                        # Always ignore '_bake' keys so they're baked in
                        if key.name[-5:] != '_bake':
                            shapekey_values[key.name] = key.value
                            key.value = 0.0

        # TODO: this seems to be kinda flaky
        # Option to apply current shape keys, otherwise normals bake weird
        # If true, apply all shapekeys and remove '_bake' keys
        # Otherwise, only apply '_bake' keys
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if apply_keys:
            for obj in get_objects(collection.all_objects, filter_func=lambda obj: core.has_shapekeys(obj)):
                meshobj: bpy.types.Object = obj
                core.add_shapekey(meshobj, "Tuxedo applykey", True)
                core.apply_shapekey_to_basis(context, meshobj, "Tuxedo applykey")
                obj.active_shape_key_index = 0
                # Ensure all keys are now set to 0.0
                for key in obj.data.shape_keys.key_blocks:
                    key.value = 0.0

        # Joining meshes causes issues with materials. Instead. apply location for all meshes, so object and world space are the same
        for obj in get_objects(collection.all_objects):
            if obj.type in ["MESH", "ARMATURE"]:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)

        # Bake normals in object coordinates
        if pass_normal:
            if generate_uvmap:
                for obj in get_objects(collection.all_objects, filter_type="MESH"):
                    if supersample_normals:
                        obj.data.uv_layers.active = obj.data.uv_layers["Tuxedo UV Super"]
                    else:
                        obj.data.uv_layers.active = obj.data.uv_layers["Tuxedo UV"]
            bake_size = ((resolution * 2, resolution * 2) if
                         supersample_normals else
                         (resolution, resolution))
            self.bake_pass(context, "world", "NORMAL", set(), get_objects(collection.all_objects, {"MESH"}),
                           bake_size, 1 if draft_render else 128, 0, [0.5, 0.5, 1., 1.], True, pixelmargin, normal_space="OBJECT",solidmaterialcolors=solidmaterialcolors,material_name_groups=material_name_groups)

        # Reset UV
        for obj in get_objects(collection.all_objects):
             if obj.type == 'MESH' and generate_uvmap and supersample_normals:
                  obj.data.uv_layers.active = obj.data.uv_layers["Tuxedo UV"]

        # Perform 'Indirect' renders: ray traced, at least sometimes
        for (bake_conditions, displace_eyes,  bake_name, bake_type, bake_pass_filter,
             background_color, world_color, desired_inputs, base_black) in [
            (pass_ao, illuminate_eyes, "ao", "AO", {"AO"}, [1., 1., 1., 1.], None, None, False),
            (pass_emit and emit_indirect, emit_exclude_eyes, "emission", "COMBINED",
             {"COLOR", "DIRECT", "INDIRECT", "EMIT", "AO", "DIFFUSE"}, [0., 0., 0., 1.], (0,0,0), None, False),
             # the MOST correct way to bake subsurface light only would be to set Base Color to black,
             # multiply Base Color and Subsurface Color and plug into Subsurface Color, then bake Diffuse color
             # then multiply by normalized thickness.
            (pass_diffuse and diffuse_indirect, True, "diffuse_indirect", "DIFFUSE", {"INDIRECT"}, [0., 0., 0., 1.], (1,1,1), None, False),
            # bake 'thickness' by baking subsurface as albedo, normalizing, and inverting
                 (pass_thickness, True, "thickness", "DIFFUSE", {"COLOR"}, [1., 1., 1., 1.], None, {"Subsurface Weight": "Alpha"}, False),
             # bake 'subsurface' by baking Diffuse Color when Base Color is black
                 (False, True, "subsurface", "DIFFUSE", {"COLOR"}, [0., 0., 0., 1.], None, {"Base Color": "Base Color", "Subsurface": "Subsurface"}, True),
             ]:
            if bake_conditions:
                if world_color:
                     tuxedo_world.color = world_color
                # Enable all AO keys
                for obj in get_objects(collection.all_objects, filter_func=lambda obj: core.has_shapekeys(obj)):
                    for key in obj.data.shape_keys.key_blocks:
                        if ('ambient' in key.name.lower() and 'occlusion' in key.name.lower()) or key.name[-3:] == '_ao':
                            key.value = 1.0

                # If conditions are met, move eyes up by 25m (so they don't get shadows)
                if displace_eyes:
                    # Add modifiers that prevent LeftEye and RightEye being baked
                    for obj in get_objects(collection.all_objects, {"MESH"}):
                        for group in ['LeftEye', 'lefteye', 'Lefteye', 'Eye.L', "Eye_L",
                                      'RightEye', 'righteye', 'Righteye', 'Eye.R', "Eye_R"]:
                            if group in obj.vertex_groups:
                                bakeeyemask = obj.modifiers.new(type='DISPLACE', name="bakeeyemask")
                                bakeeyemask.vertex_group = group
                                bakeeyemask.direction = 'Z'
                                bakeeyemask.strength = 25
                                bakeeyemask.mid_level = 0

                if desired_inputs is not None:
                    self.genericize_bsdfs(get_objects(collection.all_objects, {"MESH"}),
                                          desired_inputs, base_black=base_black)
                self.bake_pass(context, bake_name, bake_type, bake_pass_filter,
                               get_objects(collection.all_objects, {"MESH"}),
                               (resolution, resolution), 16 if draft_render else 512, 0,
                               background_color, True, pixelmargin,
                               solidmaterialcolors=solidmaterialcolors,material_name_groups=material_name_groups)
                if desired_inputs is not None:
                    self.restore_bsdfs(get_objects(collection.all_objects, {"MESH"}))

                if displace_eyes:
                    for obj in get_objects(collection.all_objects):
                        for modifier_name in [mod.name for mod in obj.modifiers]:
                            if 'bakeeyemask' in modifier_name:
                                obj.modifiers.remove(obj.modifiers[modifier_name])

                if denoise_bakes:
                    for matgroup in material_name_groups.keys():
                        self.filter_image(context, "SCRIPT_" + bake_name + str(matgroup) + ".png", BakeButton.denoise_create, matgroupnum=matgroup
                                          )
                # Disable all AO keys
                for obj in get_objects(collection.all_objects):
                    if core.has_shapekeys(obj):
                        for key in obj.data.shape_keys.key_blocks:
                            if ('ambient' in key.name.lower() and 'occlusion' in key.name.lower()) or key.name[-3:] == '_ao':
                                key.value = 0.0

        # Remove multires modifiers
        for obj in get_objects(collection.all_objects):
            mods = []
            for mod in obj.modifiers:
                if mod.type == "MULTIRES":
                    mods.append(mod.name)
            for mod in mods:
                obj.modifiers.remove(obj.modifiers[mod])

        # Apply any masking modifiers before decimation
        print("Applying mask modifiers")
        for obj in get_objects(collection.all_objects):
            if not any(mod.type == "MASK" and mod.show_viewport for mod in obj.modifiers):
                continue
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = obj

            vgroup_idxes = {obj.vertex_groups[mod.vertex_group].index for mod in obj.modifiers
                            if mod.show_viewport and mod.type == 'MASK'}
            for group in vgroup_idxes:
                print("Deleting vertices from {} on obj {}".format(group, obj.name))
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode="OBJECT")
            for vert in obj.data.vertices:
                vert.select = any(group.group in vgroup_idxes and group.weight > 0. for group in vert.groups)

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.delete(type="VERT")
            bpy.ops.object.mode_set(mode="OBJECT")

        ########### BEGIN PLATFORM SPECIFIC CODE ###########
        for platform_number, platform in enumerate(context.scene.bake_platforms):
            image_extension = ""
            if platform.image_export_format == "TGA":
                image_extension = ".tga"
            elif platform.image_export_format == "PNG":
                image_extension = ".png"

            def platform_img(img_pass):
                return platform_name + " " + img_pass + image_extension
            def sanitized_name(orig_name):
                #sanitizing name since everything needs to be simple characters and "_"'s
                sanitized = ""
                for i in orig_name.lower():
                    if i.isalnum() or i == "_":
                        sanitized += i
                    else:
                        sanitized += "_"
                return sanitized.replace("_tga", ".tga")

            platform_name = platform.name
            merge_twistbones = platform.merge_twistbones
            diffuse_alpha_pack = platform.diffuse_alpha_pack
            metallic_alpha_pack = platform.metallic_alpha_pack
            metallic_pack_ao = platform.metallic_pack_ao
            diffuse_premultiply_ao = platform.diffuse_premultiply_ao
            diffuse_premultiply_opacity = platform.diffuse_premultiply_opacity
            smoothness_premultiply_ao = platform.smoothness_premultiply_ao
            smoothness_premultiply_opacity = platform.smoothness_premultiply_opacity
            use_decimation = platform.use_decimation
            preserve_seams = platform.preserve_seams
            diffuse_vertex_colors = platform.diffuse_vertex_colors
            translate_bone_names = platform.translate_bone_names
            export_format = platform.export_format
            specular_setup = platform.specular_setup
            phong_setup = platform.phong_setup
            specular_alpha_pack = platform.specular_alpha_pack
            specular_smoothness_overlay = platform.specular_smoothness_overlay
            normal_alpha_pack = platform.normal_alpha_pack
            normal_invert_g = platform.normal_invert_g
            diffuse_emit_overlay = platform.diffuse_emit_overlay
            use_physmodel = platform.use_physmodel
            physmodel_lod = platform.physmodel_lod
            use_lods = platform.use_lods
            lods = platform.lods

            # For GMOD
            if export_format == "GMOD":
                gmod_model_name = platform.gmod_model_name
                sanitized_platform_name = sanitized_name(platform_name)
                sanitized_model_name = sanitized_name(gmod_model_name)
                vmtfile = "\"VertexlitGeneric\"\n{\n    \"$surfaceprop\" \"Flesh\""
                
                images_path = steam_library_path+"steamapps/common/GarrysMod/garrysmod/"
                target_dir = steam_library_path+"steamapps/common/GarrysMod/garrysmod/addons/"+sanitized_model_name+"_playermodel/materials/models/"+sanitized_model_name
                os.makedirs(target_dir,0o777,True)

            copy_only_handling = platform.copy_only_handling
            prop_bone_handling = platform.prop_bone_handling

            if not os.path.exists(bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/")):
                os.mkdir(bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/"))

            # for cleanliness create platform-specific copies here
            for (bakepass, bakename) in [
                (pass_diffuse, 'diffuse'),
                (pass_normal, 'normal'),
                (pass_smoothness, 'smoothness'),
                (pass_ao, 'ao'),
                (pass_emit, 'emission'),
                (pass_alpha, 'alpha'),
                (pass_metallic, 'metallic'),
                (specular_setup, 'specular'),
                (phong_setup, 'phong')
            ]:
                if not bakepass:
                    continue
                for matgroup in material_name_groups.keys():
                    if platform_img(bakename+str(matgroup)) in bpy.data.images:
                        image = bpy.data.images[platform_img(bakename+str(matgroup))]
                        image.user_clear()
                        bpy.data.images.remove(image)
                    bpy.ops.image.new(name=platform_img(bakename+str(matgroup)), width=resolution, height=resolution,
                                      generated_type="BLANK", alpha=False)
                    image = bpy.data.images[platform_img(bakename+str(matgroup))]
                    if export_format != "GMOD":
                        image.filepath = bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + platform_img(bakename+str(matgroup)))
                    else:
                        image.filepath = bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + sanitized_name(platform_img(bakename+str(matgroup))))
                    image.generated_width = resolution
                    image.generated_height = resolution
                    image.scale(resolution, resolution)
                    # already completed passes
                    if bakename not in ["specular", "normal", "phong"]:
                        orig_image = bpy.data.images["SCRIPT_" + bakename+str(matgroup)+'.png']
                        image.pixels.foreach_set(orig_image.pixels[:])

            # Create yet another output collection
            plat_collection = bpy.data.collections.new("Tuxedo Bake " + platform_name)
            #context.scene.collection.children.link(plat_collection)
            orig_scene.collection.children.link(plat_collection)
            
            # Tree-copy all meshes
            plat_arm_copy = self.tree_copy(arm_copy, None, plat_collection, ignore_hidden,
                                           filter_func=lambda obj:
                                           (prop_bone_handling != "REMOVE") or
                                           'generatePropBones' not in obj or not obj['generatePropBones'])
            plat_arm_copy.name = "Tuxedo Armature" #<- this is referenced when exporting gmod, so make sure to change it there too if changing this string - @989onan

            # Create an extra scene to render in
            bpy.ops.scene.new(type="EMPTY") # copy keeps existing settings
            context.scene.name = "Tuxedo Scene " + platform_name
            context.scene.collection.children.link(plat_collection)

            # Make sure all armature modifiers target the new armature
            for obj in get_objects(plat_collection.all_objects):
                for modifier in obj.modifiers:
                    if modifier.type == "ARMATURE":
                        modifier.object = plat_arm_copy
                    if modifier.type == "MULTIRES":
                        modifier.render_levels = modifier.total_levels
                # Do a little weight painting cleanup here
                if obj.type == "MESH" and export_format != "GMOD": #wanna exclude gmod since gmod does this itself.
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
                    # Unity maxes out at 4 deforms, remove here
                    bpy.ops.object.vertex_group_limit_total(group_select_mode='BONE_DEFORM')
                    # Remove insiginificant weights
                    bpy.ops.object.vertex_group_clean(group_select_mode='BONE_DEFORM', limit=0.00001)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    obj['tuxedoForcedExportName'] = orig_largest_obj_name

            # Optionally cleanup bones if we're not going to use them
            if merge_twistbones:
                print("merging bones")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = plat_arm_copy
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.armature.select_all(action="DESELECT")
                bone_children = dict()
                for editbone in context.visible_bones:
                    if not editbone.parent:
                        continue
                    if not editbone.parent.name in bone_children:
                        bone_children[editbone.parent.name] = []
                    bone_children[editbone.parent.name].append(editbone.name)
                for editbone in context.visible_bones:
                    if 'twist' in editbone.name.lower() and not editbone.children:
                        editbone.select = True
                        if editbone.parent:
                            # only select if bone is alphabetically after all non-twistbones. Prevents hierarchy problems
                            if any(otherbone > editbone.name for otherbone in bone_children[editbone.parent.name]
                                   if not 'twist' in otherbone.lower()):
                                editbone.select = False
                if context.selected_editable_bones:
                    core.merge_bone_weights_to_respective_parents(context, plat_arm_copy, [bone.name for bone in context.selected_editable_bones])
                bpy.ops.object.mode_set(mode="OBJECT")

            if prop_bone_handling == "GENERATE":
                # Find any mesh that's weighted to a single bone, duplicate and rename that bone, move mesh's vertex group to the new bone
                all_path_strings = dict()
                vgroup_deforms_meshes = dict()
                mesh_has_vertex_groups = dict()
                for obj in get_objects(plat_collection.objects, {"MESH"}):
                    # Create a dict of vgroup: [meshnames..]
                    orig_obj_name = obj.name[:-4] if len(obj.name) >= 4 and obj.name[-4] == '.' else obj.name
                    found_vertex_groups = set([vgp.group for vertex in obj.data.vertices
                                                for vgp in vertex.groups if vgp.weight > 0.00001])

                    vgroup_lookup = dict([(vgp.index, vgp.name) for vgp in obj.vertex_groups])

                    if orig_obj_name not in mesh_has_vertex_groups:
                        mesh_has_vertex_groups[orig_obj_name] = set()
                    mesh_has_vertex_groups[orig_obj_name].update(found_vertex_groups)

                    for idx in found_vertex_groups:
                        if vgroup_lookup[idx] not in vgroup_deforms_meshes:
                            vgroup_deforms_meshes[vgroup_lookup[idx]] = set()
                        vgroup_deforms_meshes[vgroup_lookup[idx]].add(orig_obj_name)

                for obj in get_objects(plat_collection.objects, {"MESH"}):
                    if 'generatePropBones' not in obj or not obj['generatePropBones']:
                        continue
                    orig_obj_name = obj.name[:-4] if len(obj.name) >= 4 and obj.name[-4] == '.' else obj.name
                    found_vertex_groups = mesh_has_vertex_groups[orig_obj_name]
                    if len(found_vertex_groups) == 0:
                        continue

                    vgroup_lookup = dict([(vgp.index, vgp.name) for vgp in obj.vertex_groups])
                    for vgp in found_vertex_groups:
                        if vgp not in vgroup_lookup:
                            continue
                        vgroup_name = vgroup_lookup[vgp]
                        if vgroup_name not in vgroup_deforms_meshes:
                            continue
                        #if not plat_arm_copy.data.bones[vgroup_name].children:
                        #    #TODO: this doesn't account for props attached to something which has existing attachments
                        #    bpy.ops.object.mode_set(mode="OBJECT")
                        #    print("Object " + obj.name + " already has no children, skipping")
                        #    continue

                        # if the prop is the ONLY mesh weighted to that bone, don't create a duplicate, just create the animations
                        only_deformed_mesh_for_bone = len(vgroup_deforms_meshes[vgroup_name]) == 1

                        # If the obj has ".001" or similar, trim it
                        if only_deformed_mesh_for_bone:
                            print("Object " + obj.name + " is an eligible prop on " + vgroup_name + " and is the sole deformed mesh.")
                            newbonename = vgroup_name
                        else:
                            print("Object " + obj.name + " is an eligible prop on " + vgroup_name + "! Creating prop bone...")
                            newbonename = "~" + vgroup_name + "_Prop_" + orig_obj_name

                        if newbonename not in obj.vertex_groups:
                            obj.vertex_groups[vgroup_name].name = newbonename
                        elif not only_deformed_mesh_for_bone:
                            # if newbonename already exists as a name, merge new vgroup with existing
                            # this means "Obj" and "Obj.001" will get the same bone
                            core.mix_weights(obj, obj.vertex_groups[vgroup_name], obj.vertex_groups[newbonename])
                            obj.vertex_groups.remove(vgroup_name)

                        context.view_layer.objects.active = plat_arm_copy
                        bpy.ops.object.mode_set(mode="EDIT")
                        if not vgroup_name in plat_arm_copy.data.edit_bones:
                            continue
                        orig_bone = plat_arm_copy.data.edit_bones[vgroup_name]
                        if newbonename not in plat_arm_copy.data.edit_bones:
                            prop_bone = plat_arm_copy.data.edit_bones.new(newbonename)
                            prop_bone.head = orig_bone.head
                            prop_bone.tail[:] = [(orig_bone.head[i] + orig_bone.tail[i]) / 2 for i in range(3)]
                            prop_bone.parent = orig_bone
                            # To create en/disable animation files
                            next_bone = prop_bone.parent
                            path_string = prop_bone.name
                            while next_bone != None:
                                path_string = next_bone.name + "/" + path_string
                                next_bone = next_bone.parent
                            path_string = orig_armature_name + "/" + path_string
                            if orig_obj_name not in all_path_strings:
                                all_path_strings[orig_obj_name] = set()
                            all_path_strings[orig_obj_name].add(path_string)
                            bpy.ops.object.mode_set(mode="OBJECT")

                for orig_obj_name, path_strings in all_path_strings.items():
                    # A bit of a hacky string manipulation, just create a curve for each bone based on the editor path. Output file is YAML
                    # {EDITOR_VALUE} = 1
                    # {SCALE_VALUE} = {x: 1, y: 1, z: 1}
                    with open(os.path.dirname(os.path.abspath(__file__)) + "/enable.anim", 'r') as infile:
                        newname = "Enable " + orig_obj_name
                        editor_curves = ""
                        scale_curves = ""
                        for path_string in sorted(path_strings):
                            with open(os.path.dirname(os.path.abspath(__file__)) + "/m_ScaleCurves.anim.part", 'r') as infilepart:
                                scale_curves += "".join([line.replace("{PATH_STRING}", path_string).replace("{SCALE_VALUE}", "{x: 1, y: 1, z: 1}") for line in infilepart])
                            with open(os.path.dirname(os.path.abspath(__file__)) + "/m_EditorCurves.anim.part", 'r') as infilepart:
                                editor_curves += "".join([line.replace("{PATH_STRING}", path_string).replace("{EDITOR_VALUE}", "1") for line in infilepart])

                        with open(bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + newname + ".anim"), 'w') as outfile:
                            for line in infile:
                                outfile.write(line.replace("{NAME_STRING}", newname).replace("{EDITOR_CURVES}", editor_curves).replace("{SCALE_CURVES}", scale_curves))
                    with open(os.path.dirname(os.path.abspath(__file__)) + "/disable.anim", 'r') as infile:
                        newname = "Disable " + orig_obj_name
                        editor_curves = ""
                        scale_curves = ""
                        for path_string in sorted(path_strings):
                            with open(os.path.dirname(os.path.abspath(__file__)) + "/m_ScaleCurves.anim.part", 'r') as infilepart:
                                scale_curves += "".join([line.replace("{PATH_STRING}", path_string).replace("{SCALE_VALUE}", "{x: 0, y: 0, z: 0}") for line in infilepart])
                            with open(os.path.dirname(os.path.abspath(__file__)) + "/m_EditorCurves.anim.part", 'r') as infilepart:
                                editor_curves += "".join([line.replace("{PATH_STRING}", path_string).replace("{EDITOR_VALUE}", "0") for line in infilepart])

                        with open(bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + newname + ".anim"), 'w') as outfile:
                            for line in infile:
                                outfile.write(line.replace("{NAME_STRING}", newname).replace("{EDITOR_CURVES}", editor_curves).replace("{SCALE_CURVES}", scale_curves))

            if translate_bone_names == "SECONDLIFE":
                bpy.ops.tuxedo.convert_to_secondlife()
            if translate_bone_names == "VALVE":
                bpy.ops.tuxedo.convert_to_valve()
            
            if generate_uvmap:
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    uv_layers = [layer.name for layer in obj.data.uv_layers]
                    while uv_layers:
                        layer = uv_layers.pop()
                        if ("Tuxedo" not in layer) and layer != "Detail Map":
                            print("Removing UV {}".format(layer))
                            obj.data.uv_layers.remove(obj.data.uv_layers[layer])
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    obj.data.uv_layers.active = obj.data.uv_layers["Tuxedo UV"]
                # Ensure 'Detail Map' is at the end, if it exists here
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    if "Detail Map" in obj.data.uv_layers:
                        context.view_layer.objects.active = obj
                        obj.data.uv_layers["Detail Map"].active = True
                        bpy.ops.mesh.uv_texture_add()
                        obj.data.uv_layers.remove(obj.data.uv_layers["Detail Map"])
                        obj.data.uv_layers[-1].name = 'Detail Map'

            print("Decimating")
            context.scene.decimation_remove_doubles = platform.remove_doubles

            # Make note of which objects are going to be exported
            export_groups = [
                ("Bake", [plat_arm_copy.name])
            ]

            # Physmodel does a couple extra things like ensuring doubles are removed, wire display
            if use_physmodel:
                new_arm = self.tree_copy(plat_arm_copy, None, plat_collection, ignore_hidden, view_layer=context.view_layer)
                for obj in get_objects(new_arm.children):
                    obj.display_type = "WIRE"
                context.scene.tuxedo_max_tris = int(platform.max_tris * physmodel_lod)
                bpy.ops.tuxedo.smart_decimation(armature_name=new_arm.name, preserve_seams=False, preserve_objects=(export_format == "GMOD"), max_single_mesh_tris=(9900 if (export_format == "GMOD") else (bpy.context.scene.tuxedo_max_tris)))
                for obj in get_objects(new_arm.children):
                    obj.name = "LODPhysics"
                new_arm.name = "ArmatureLODPhysics"
                export_groups.append(("LODPhysics", ["LODPhysics", "ArmatureLODPhysics"]))

            if use_lods:
                for idx, lod in enumerate(lods):
                    new_arm = self.tree_copy(plat_arm_copy, None, plat_collection, ignore_hidden, view_layer=context.view_layer)
                    context.scene.tuxedo_max_tris = int(platform.max_tris * lod)
                    bpy.ops.tuxedo.smart_decimation(armature_name=new_arm.name, preserve_seams=preserve_seams, preserve_objects=(export_format == "GMOD"), max_single_mesh_tris=(9900 if (export_format == "GMOD") else (bpy.context.scene.tuxedo_max_tris)))
                    for obj in get_objects(new_arm.children):
                        obj.name = "LOD" + str(idx + 1)
                    new_arm.name = "ArmatureLOD" + str(idx + 1)
                    export_groups.append(("LOD" + str(idx + 1), ["LOD" + str(idx + 1), "ArmatureLOD" + str(idx + 1)]))

            if use_decimation:
                # Decimate. If 'preserve seams' is selected, forcibly preserve seams (seams from islands, deselect seams)
                context.scene.tuxedo_max_tris = int(platform.max_tris)
                bpy.ops.tuxedo.smart_decimation(armature_name=plat_arm_copy.name, preserve_seams=preserve_seams, preserve_objects=(export_format == "GMOD"), max_single_mesh_tris=(9900 if (export_format == "GMOD") else (bpy.context.scene.tuxedo_max_tris)))
            else:
                # join meshes here if we didn't decimate
                if export_format != "GMOD":
                    core.join_meshes(context, armature_name=plat_arm_copy.name)
            
            
            
            
            
           
            if pass_normal:
                self.bake_pass(context, "normal", "NORMAL", set(), get_objects(plat_collection.all_objects, {"MESH"}, filter_func=lambda obj: not "LOD" in obj.name), (resolution, resolution), 1 if draft_render else 128, 0, [0.5, 0.5, 1., 1.], True, pixelmargin, solidmaterialcolors=solidmaterialcolors, material_name_groups=material_name_groups)
            
            for group_num, group in material_name_groups.items():
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                print("Group "+str(group_num) + " selected. assigning and generating material.")
                
                # Apply generated material (object normals -> normal map -> BSDF normal and other textures)
                mat = bpy.data.materials.get("Tuxedo Baked " + platform_name + "_" + str(group_num))
                if mat is not None:
                    bpy.data.materials.remove(mat, do_unlink=True)
                # create material
                mat = bpy.data.materials.new(name="Tuxedo Baked " + platform_name + "_" + str(group_num))
                mat.use_nodes = True
                mat.use_backface_culling = True
                # add a normal map and image texture to connect the world texture, if it exists
                tree = mat.node_tree
                
                for obj in get_objects(plat_collection.all_objects):
                    if obj.type == 'MESH':
                        
                        context.view_layer.objects.active = obj
                        obj.select_set(True)
                        bpy.ops.object.material_slot_add()
                        new_mat_index = obj.active_material_index
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')

                        for indexmat, mattwo in enumerate(obj.material_slots):
                            if mattwo.material:
                                if mattwo.material.name in group:
                                    obj.active_material_index = indexmat
                                    bpy.ops.object.material_slot_select()
                        obj.active_material_index = new_mat_index
                        obj.material_slots[obj.active_material_index].material = mat
                        bpy.ops.object.material_slot_assign()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.material_slot_remove_unused()
                        obj.select_set(False)
                
                
                vmtfile = "\"VertexlitGeneric\"\n{\n    \"$surfaceprop\" \"Flesh\""
                
                if pass_alpha:
                    # Ensure baked alpha is RGB-only, changed in 3.3
                    pixel_buffer = img_channels_as_nparray("SCRIPT_alpha"+ str(group_num)+".png")
                    pixel_buffer[3:] = 1.0
                    nparray_channels_to_img("SCRIPT_alpha"+ str(group_num)+".png", pixel_buffer)

                # Blend diffuse and AO to create Quest Diffuse (if selected)
                # Overlay emission onto diffuse, dodge metallic if specular
                if pass_diffuse:
                    pixel_buffer = img_channels_as_nparray(platform_img("diffuse"+ str(group_num)))
                    if diffuse_indirect:
                        diffuse_indirect_buffer = img_channels_as_nparray("SCRIPT_diffuse_indirect"+ str(group_num)+".png")
                        # Map range: screen the diffuse_indirect onto diffuse
                        pixel_buffer[:3] = 1. - ((1. - (diffuse_indirect_buffer[:3] * diffuse_indirect_opacity)) * (1. - pixel_buffer[:3]))
                    if pass_ao and diffuse_premultiply_ao:
                        ao_buffer = img_channels_as_nparray("SCRIPT_ao"+ str(group_num)+".png")
                        # Map range: set the black point up to 1-opacity
                        pixel_buffer[:3] = pixel_buffer[:3] * ((1. - diffuse_premultiply_opacity) + (diffuse_premultiply_opacity * ao_buffer[:3]))
                    if specular_setup and pass_metallic:
                        metallic_buffer = img_channels_as_nparray("SCRIPT_metallic"+ str(group_num)+".png")
                        # Map range: metallic blocks diffuse light
                        pixel_buffer[:3] *= (1. - metallic_buffer[:3])
                    if pass_emit and diffuse_emit_overlay:
                        emit_buffer = img_channels_as_nparray("SCRIPT_emission"+ str(group_num)+".png")
                        # Map range: screen the emission onto diffuse
                        pixel_buffer[:3] = 1. - ((1. - emit_buffer[:3]) * (1. - pixel_buffer[:3]))
                    if export_format == "GMOD":
                        vmtfile += "\n    \"$basetexture\" \"models/"+sanitized_model_name+"/"+sanitized_name(platform_img("diffuse"+ str(group_num))).replace(".tga","")+"\""
                    nparray_channels_to_img(platform_img("diffuse"+ str(group_num)), pixel_buffer)

                # Preultiply AO into smoothness if selected, to avoid shine in dark areas
                if pass_smoothness and pass_ao and smoothness_premultiply_ao:
                    pixel_buffer = img_channels_as_nparray("SCRIPT_smoothness"+ str(group_num)+".png")
                    ao_buffer = img_channels_as_nparray("SCRIPT_ao"+ str(group_num)+".png")
                    # Map range: set the black point up to 1-opacity
                    pixel_buffer[:3] *= ((1. - smoothness_premultiply_opacity) + (smoothness_premultiply_opacity * ao_buffer[:3]))
                    # Alpha is unused on quest, set to 1 to make sure unity doesn't keep it
                    pixel_buffer[3:] = 1.0
                    nparray_channels_to_img(platform_img("smoothness"+ str(group_num)), pixel_buffer)

                # Pack to diffuse alpha (if selected)
                if pass_diffuse and ((diffuse_alpha_pack == "SMOOTHNESS" and pass_smoothness) or
                                     (diffuse_alpha_pack == "TRANSPARENCY" and pass_alpha) or
                                     (diffuse_alpha_pack == "EMITMASK" and pass_emit)):
                    pixel_buffer = img_channels_as_nparray(platform_img("diffuse"+ str(group_num)))
                    print("Packing to diffuse alpha")
                    alpha_buffer = None
                    if diffuse_alpha_pack == "SMOOTHNESS":
                        alpha_buffer = img_channels_as_nparray(platform_img("smoothness"+ str(group_num)))
                        if export_format == "GMOD":
                            vmtfile += "\n    \"$basealphaenvmapmask\" 1"
                    elif diffuse_alpha_pack == "TRANSPARENCY":
                        alpha_buffer = img_channels_as_nparray("SCRIPT_alpha"+ str(group_num)+".png")
                        if export_format == "GMOD":
                            vmtfile += "\n    \"$translucent\" 1"
                    elif diffuse_alpha_pack == "EMITMASK":
                        alpha_buffer = img_channels_as_nparray("SCRIPT_emission"+ str(group_num)+".png")
                        # "By default, $selfillum uses the alpha channel of the base texture as a mask.
                        # If the alpha channel of your base texture is used for something else, you can
                        # specify a separate $selfillummask texture."
                        # https://developer.valvesoftware.com/wiki/Glowing_Textures
                        # TODO: independent emit if transparency "\n    \"$selfillummask\" \"models/"+
                        # sanitized_model_name+"/"+baked_emissive_image.name.replace(".tga","")+"\""
                        if export_format == "GMOD":
                            vmtfile += "\n    \"$selfillum\" 1"
                    pixel_buffer[3] = (alpha_buffer[0] * 0.299) + (alpha_buffer[1] * 0.587) + (alpha_buffer[2] * 0.114)
                    nparray_channels_to_img(platform_img("diffuse"+ str(group_num)), pixel_buffer)

                # Metallic is sampled from 'r', while ao is 'g', smoothness is 'a'
                if pass_metallic:
                    print("Packing to metallic alpha")
                    pixel_buffer = img_channels_as_nparray("SCRIPT_metallic"+ str(group_num)+".png")
                    smoothness_channel = np.ones(len(pixel_buffer[0]), dtype=np.float32)
                    if metallic_alpha_pack == "SMOOTHNESS" and pass_smoothness:
                        smoothness_channel = img_channels_as_nparray(platform_img("smoothness"+ str(group_num)))[0]
                    ao_channel = np.zeros(len(pixel_buffer[0]), dtype=np.float32)
                    if pass_ao and metallic_pack_ao:
                        ao_channel = img_channels_as_nparray(platform_img("ao"+ str(group_num)))[0]
                    nparray_channels_to_img(platform_img("metallic"+ str(group_num)),
                                            np.vstack((pixel_buffer[0],
                                                       ao_channel,
                                                       np.zeros(len(pixel_buffer[0]), dtype=np.float32),
                                                       smoothness_channel)))

                # Create specular map
                if specular_setup:
                    # TODO: Valve has their own suggested curve ramps, which are indexed above.
                    # Add an an option to apply it for a more "source-ey" specular setup
                    pixel_buffer = img_channels_as_nparray(platform_img("specular"+ str(group_num)))
                    if pass_metallic:
                        # Use the unaltered diffuse map
                        diffuse_buffer = img_channels_as_nparray("SCRIPT_diffuse"+ str(group_num)+".png")
                        metallic_buffer = img_channels_as_nparray("SCRIPT_metallic"+ str(group_num)+".png")
                        # Simple specularity: most nonmetallic objects have about 4% reflectiveness
                        pixel_buffer[:3] = (diffuse_buffer[:3] * metallic_buffer[:3]) + (.04 * (1-metallic_buffer[:3]))
                    else:
                        pixel_buffer[:3] = 0.04
                    if specular_alpha_pack == "SMOOTHNESS" and pass_smoothness:
                        alpha_buffer = img_channels_as_nparray(platform_img("smoothness"+ str(group_num)))
                        pixel_buffer[3] = alpha_buffer[0]
                    # for source games, screen(specular, smoothness) to create envmapmask
                    if specular_smoothness_overlay and pass_smoothness:
                        smoothness_buffer = img_channels_as_nparray(platform_img("smoothness"+ str(group_num)))
                        pixel_buffer[:3] *= smoothness_buffer[:3]

                    nparray_channels_to_img(platform_img("specular"+ str(group_num)), pixel_buffer)

                # Phong texture (R: smoothness, G: metallic, pack smoothness * AO to normalmap alpha as mask)
                if phong_setup and pass_smoothness:
                    # Use the unaltered smoothness
                    red_channel = img_channels_as_nparray("SCRIPT_smoothness"+ str(group_num)+".png")[0]
                    green_channel = np.zeros(len(red_channel), dtype=np.float32)
                    blue_channel = np.zeros(len(red_channel), dtype=np.float32)
                    alpha_channel = np.zeros(len(red_channel), dtype=np.float32)

                    if pass_normal:
                        # Has to be specified first!
                        if export_format == "GMOD":
                            vmtfile += "\n    \"$bumpmap\" \"models/"+sanitized_model_name+"/"+sanitized_name(platform_img("normal"+ str(group_num))).replace(".tga","")+"\""
                    if export_format == "GMOD":
                        vmtfile += "\n    \"$phong\" 1"
                        vmtfile += "\n    \"$phongboost\" 1.0"
                        vmtfile += "\n    \"$phongfresnelranges\" \"[0 0.5 1.0]\""
                        vmtfile += "\n    \"$phongexponenttexture\" \"models/"+sanitized_model_name+"/"+sanitized_name(platform_img("phong"+ str(group_num))).replace(".tga","")+"\""

                    if pass_metallic:
                        # Use the unaltered metallic
                        green_channel = img_channels_as_nparray("SCRIPT_metallic"+ str(group_num)+".png")[0]
                        if export_format == "GMOD":
                            vmtfile += "\n    \"$phongalbedotint\" 1"

                    nparray_channels_to_img(platform_img("phong"+ str(group_num)),
                                            np.vstack((red_channel,
                                            green_channel,
                                            blue_channel,
                                            alpha_channel)))
                
                

                
                bsdfnode = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
                if bsdf_original is not None:
                    #this was failing catestrophically. Putting a number based one.
                    for k,bsdfinput in enumerate(bsdfnode.inputs):
                        bsdfinput.default_value = bsdf_original.inputs[k].default_value
                if pass_normal:
                    normaltexnode = tree.nodes.new("ShaderNodeTexImage")
                    normaltexnode.image = bpy.data.images["SCRIPT_world"+str(group_num)+".png"]
                    # If not supersampling, sample SCRIPT_WORLD 1:1 so we don't blur it
                    if not supersample_normals:
                        normaltexnode.interpolation = "Closest"
                    normaltexnode.location.x -= 500
                    normaltexnode.location.y -= 200

                    normalmapnode = tree.nodes.new("ShaderNodeNormalMap")
                    normalmapnode.space = "OBJECT"
                    normalmapnode.location.x -= 200
                    normalmapnode.location.y -= 200

                    tree.links.new(normalmapnode.inputs["Color"], normaltexnode.outputs["Color"])
                    tree.links.new(bsdfnode.inputs["Normal"], normalmapnode.outputs["Normal"])

                    if generate_uvmap:
                        for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                            if supersample_normals:
                                obj.data.uv_layers["Tuxedo UV Super"].active_render = True
                            else:
                                obj.data.uv_layers["Tuxedo UV"].active_render = True
                
                
                if pass_normal:
                    # Bake tangent normals
                    image = bpy.data.images[platform_img("normal"+str(group_num))]
                    image.colorspace_settings.name = 'Non-Color'
                    normal_image = bpy.data.images["SCRIPT_normal"+str(group_num)+".png"] 
                    image.pixels.foreach_set(normal_image.pixels[:])
                    if export_format == "GMOD":
                        vmtfile += "\n    \"$bumpmap\" \"models/"+sanitized_model_name+"/"+sanitized_name(image.name).replace(".tga","")+"\""
                    if ((normal_alpha_pack == "SMOOTHNESS" and pass_smoothness) or (normal_alpha_pack == "SPECULAR" and specular_setup)):
                        print("Packing to normal alpha")
                        if normal_alpha_pack == "SPECULAR":
                            alpha_image = bpy.data.images[platform_img("specular"+str(group_num))]
                            if export_format == "GMOD":
                                vmtfile += "\n    \"$normalmapalphaenvmapmask\" 1"
                                vmtfile += "\n    \"$envmap\" env_cubemap"
                        elif normal_alpha_pack == "SMOOTHNESS":
                            # 'There must be a Phong mask. The alpha channel of a bump map acts as a Phong mask by default.'
                            alpha_image = bpy.data.images[platform_img("smoothness"+str(group_num))]
                        pixel_buffer = list(image.pixels)
                        alpha_buffer = alpha_image.pixels[:]
                        for idx in range(3, len(pixel_buffer), 4):
                            pixel_buffer[idx] = (alpha_buffer[idx - 3] * 0.299) + (alpha_buffer[idx - 2] * 0.587) + (alpha_buffer[idx - 1] * 0.114)
                        image.pixels[:] = pixel_buffer
                    if normal_invert_g:
                        pixel_buffer = list(image.pixels)
                        for idx in range(1, len(pixel_buffer), 4):
                            pixel_buffer[idx] = 1. - pixel_buffer[idx]
                        image.pixels[:] = pixel_buffer
                    
                # Reapply keys
                if not apply_keys:
                    for obj in get_objects(plat_collection.all_objects):
                        if core.has_shapekeys(obj):
                            for key in obj.data.shape_keys.key_blocks:
                                if key.name in shapekey_values:
                                    key.value = shapekey_values[key.name]


                

                # Always remove existing vertex colors here
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    if obj.data.vertex_colors is not None and len(obj.data.vertex_colors) > 0:
                        while len(obj.data.vertex_colors) > 0:
                            context.view_layer.objects.active = obj
                            if bpy.app.version < (3, 4, 0):
                                bpy.ops.mesh.vertex_color_remove()
                            else:
                                bpy.ops.geometry.color_attribute_remove()

                # Update generated material to preview all of our passes
                if pass_normal:
                    normaltexnode.image = bpy.data.images[platform_img("normal"+str(group_num))]
                    normalmapnode.space = "TANGENT"
                    normaltexnode.interpolation = "Linear"
                if pass_metallic:
                    metallictexnode = tree.nodes.new("ShaderNodeTexImage")
                    metallictexnode.image = bpy.data.images[platform_img("metallic"+str(group_num))]
                    metallictexnode.location.x -= 300
                    metallictexnode.location.y += 200
                    seprgbnode = tree.nodes.new("ShaderNodeSeparateRGB")

                    tree.links.new(seprgbnode.inputs["Image"], metallictexnode.outputs["Color"])
                    tree.links.new(bsdfnode.inputs["Metallic"], seprgbnode.outputs["R"])
                if pass_diffuse:
                    diffusetexnode = tree.nodes.new("ShaderNodeTexImage")
                    diffusetexnode.image = bpy.data.images[platform_img("diffuse"+str(group_num))]
                    diffusetexnode.location.x -= 300
                    diffusetexnode.location.y += 500

                    # If AO, blend in AO.
                    if pass_ao and not diffuse_premultiply_ao:
                        # AO -> Math (* ao_opacity + (1-ao_opacity)) -> Mix (Math, diffuse) -> Color
                        multiplytexnode = tree.nodes.new("ShaderNodeMath")
                        multiplytexnode.operation = "MULTIPLY_ADD"
                        multiplytexnode.inputs[1].default_value = diffuse_premultiply_opacity
                        multiplytexnode.inputs[2].default_value = 1. - diffuse_premultiply_opacity
                        multiplytexnode.location.x -= 400
                        multiplytexnode.location.y += 700
                        if pass_metallic and metallic_pack_ao:
                            tree.links.new(multiplytexnode.inputs[0], seprgbnode.outputs["G"])
                        else:
                            aotexnode = tree.nodes.new("ShaderNodeTexImage")
                            aotexnode.image = bpy.data.images[platform_img("ao"+str(group_num))]
                            aotexnode.location.x -= 700
                            aotexnode.location.y += 800
                            tree.links.new(multiplytexnode.inputs[0], aotexnode.outputs["Color"])

                        mixnode = tree.nodes.new("ShaderNodeMixRGB")
                        mixnode.blend_type = "MULTIPLY"
                        mixnode.inputs["Fac"].default_value = 1.0
                        mixnode.location.x -= 200
                        mixnode.location.y += 700
                        tree.links.new(mixnode.inputs["Color1"], multiplytexnode.outputs["Value"])
                        tree.links.new(mixnode.inputs["Color2"], diffusetexnode.outputs["Color"])

                        tree.links.new(bsdfnode.inputs["Base Color"], mixnode.outputs["Color"])
                    else:
                        tree.links.new(bsdfnode.inputs["Base Color"], diffusetexnode.outputs["Color"])
                if pass_smoothness:
                    if pass_diffuse and (diffuse_alpha_pack == "SMOOTHNESS"):
                        invertnode = tree.nodes.new("ShaderNodeInvert")
                        diffusetexnode.location.x -= 200
                        invertnode.location.x -= 200
                        invertnode.location.y += 200
                        tree.links.new(invertnode.inputs["Color"], diffusetexnode.outputs["Alpha"])
                        tree.links.new(bsdfnode.inputs["Roughness"], invertnode.outputs["Color"])
                    elif pass_metallic and (metallic_alpha_pack == "SMOOTHNESS"):
                        invertnode = tree.nodes.new("ShaderNodeInvert")
                        metallictexnode.location.x -= 200
                        invertnode.location.x -= 200
                        invertnode.location.y += 100
                        tree.links.new(invertnode.inputs["Color"], metallictexnode.outputs["Alpha"])
                        tree.links.new(bsdfnode.inputs["Roughness"], invertnode.outputs["Color"])
                    else:
                        smoothnesstexnode = tree.nodes.new("ShaderNodeTexImage")
                        smoothnesstexnode.image = bpy.data.images[platform_img("smoothness"+str(group_num))]
                        invertnode = tree.nodes.new("ShaderNodeInvert")
                        tree.links.new(invertnode.inputs["Color"], smoothnesstexnode.outputs["Color"])
                        tree.links.new(bsdfnode.inputs["Roughness"], invertnode.outputs["Color"])
                if pass_alpha:
                    if pass_diffuse and (diffuse_alpha_pack == "TRANSPARENCY"):
                        tree.links.new(bsdfnode.inputs["Alpha"], diffusetexnode.outputs["Alpha"])
                    else:
                        alphatexnode = tree.nodes.new("ShaderNodeTexImage")
                        alphatexnode.image = bpy.data.images[platform_img("alpha"+str(group_num))]
                        tree.links.new(bsdfnode.inputs["Alpha"], alphatexnode.outputs["Color"])
                    mat.blend_method = 'CLIP'
                if pass_emit:
                    emittexnode = tree.nodes.new("ShaderNodeTexImage")
                    emittexnode.image = bpy.data.images[platform_img("emission"+str(group_num))]
                    emittexnode.location.x -= 800
                    emittexnode.location.y -= 150
                    tree.links.new(bsdfnode.inputs[EMISSION_INPUT], emittexnode.outputs["Color"])

                
                if pass_diffuse and diffuse_vertex_colors:
                    # TODO: If we're not baking anything else in, remove all UV maps entirely

                    # Update material preview
                    #tree.nodes.remove(diffusetexnode)
                    diffusevertnode = tree.nodes.new("ShaderNodeVertexColor")
                    diffusevertnode.layer_name = "Col"
                    diffusevertnode.location.x -= 300
                    diffusevertnode.location.y += 500
                    tree.links.new(bsdfnode.inputs["Base Color"], diffusevertnode.outputs["Color"])
                    
                if export_format == "GMOD":
                    vmtfile += "\n}"
                    vmtfiledir = open(target_dir+"/tuxedo_baked_"+sanitized_platform_name+"_"+str(group_num)+".vmt","w")
                    vmtfiledir.write(vmtfile)
                    vmtfiledir.close()
                    collection = bpy.data.collections["Tuxedo Bake"]
            
            #material merging and combining ends here.
            
            # Remove Tuxedo UV Super
            if generate_uvmap and supersample_normals:
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    uv_layers = [layer.name for layer in obj.data.uv_layers]
                    while uv_layers:
                        layer = uv_layers.pop()
                        if layer == "Tuxedo UV Super":
                            print("Removing UV {}".format(layer))
                            obj.data.uv_layers.remove(obj.data.uv_layers[layer])
            
            
            
            # Try to only output what you'll end up importing into unity.
            context.scene.render.image_settings.file_format = 'TARGA' if export_format == "GMOD" else 'PNG'
            context.scene.render.image_settings.color_mode = 'RGBA'
            for (bakepass, bakeconditions) in [
                ("diffuse", pass_diffuse and not diffuse_vertex_colors),
                ("smoothness", pass_smoothness and (diffuse_alpha_pack != "SMOOTHNESS") and (metallic_alpha_pack != "SMOOTHNESS") and (specular_alpha_pack != "SMOOTHNESS") and (normal_alpha_pack != "SMOOTHNESS") and not specular_smoothness_overlay),
                ("ao", pass_ao and not diffuse_premultiply_ao and not (metallic_pack_ao and pass_metallic)),
                ("emission", pass_emit and not diffuse_alpha_pack == "EMITMASK"),
                ("alpha", pass_alpha and (diffuse_alpha_pack != "TRANSPARENCY")),
                ("metallic", pass_metallic and not specular_setup and not phong_setup),
                ("specular", specular_setup and normal_alpha_pack != "SPECULAR"),
                ("phong", phong_setup),
                ("normal", pass_normal)
            ]:
                
                if not bakeconditions:
                    continue
                for group_num, group in material_name_groups.items():
                    image = bpy.data.images[platform_img(bakepass+str(group_num))]
                    if bpy.app.version < (4, 0, 0):
                        context.scene.display_settings.display_device = 'None' if use_linear else 'sRGB'
                    context.scene.view_settings.view_transform = "Raw" if use_linear else "Standard"
                    image.save_render(bpy.path.abspath(image.filepath), scene=context.scene)
                    if export_format == "GMOD":
                        image.filepath_raw = images_path+"materialsrc/"+sanitized_name(image.name)
                        image.save_render(image.filepath_raw,scene=context.scene)
                        if(os.stat(image.filepath_raw).st_size > 33554400):
                            raise Exception("Your file named "+sanitized_name(image.name)+" is bigger than the max (33,554,432 bytes) allowed VTF Size!!! EXITING!")
                        self.compile_gmod_tga(steam_library_path,images_path,sanitized_name(image.name))
                        if os.path.isfile(target_dir+"/"+sanitized_name(image.name).replace(".tga",".vtf")):
                            os.remove(target_dir+"/"+sanitized_name(image.name).replace(".tga",".vtf"))
                        shutil.move(images_path+"materials/"+sanitized_name(image.name).replace(".tga",".vtf"), target_dir)

            if cleanup_shapekeys:
                for mesh in plat_collection.all_objects:
                    if mesh.type == 'MESH' and mesh.data.shape_keys is not None:
                        names = [key.name for key in mesh.data.shape_keys.key_blocks]
                        for name in names:
                            if name[-4:] == "_old" or name[-11:] == " - Reverted":
                                mesh.shape_key_remove(key=mesh.data.shape_keys.key_blocks[name])

            # '_bake' shapekeys are always applied and removed.
            for mesh in plat_collection.all_objects:
                if mesh.type == 'MESH' and mesh.data.shape_keys is not None:
                    names = [key.name for key in mesh.data.shape_keys.key_blocks]
                    for name in names:
                        if name[-5:] == "_bake":
                            mesh.shape_key_remove(key=mesh.data.shape_keys.key_blocks[name])

            # Remove all materials for export - blender will try to embed materials but it doesn't work with our setup
            #exception is Gmod because Gmod needs textures to be applied to work - @989onan
            
            objmaterials = dict()
            
            if export_format not in ["GMOD"] and copy_only_handling != "COPY":
                for obj in get_objects(plat_collection.all_objects):
                    objmaterials[obj.name] = dict()
                    if obj.type == 'MESH':
                        context.view_layer.objects.active = obj
                        for matindex, slot in enumerate(obj.material_slots):
                            objmaterials[obj.name][matindex] = slot.material.name
                            slot.material = None
                            

            # Re-apply the old armature transforms on the new-armature, then inverse-apply to the data of the armature
            # This prevents animations designed for the old avatar from breaking
            if export_format not in ["GMOD", "DAE"]:
                plat_arm_copy.scale = armature.scale
                plat_arm_copy.rotation_euler = armature.rotation_euler

                context.view_layer.objects.active = plat_arm_copy
                bpy.ops.object.mode_set(mode="EDIT")
                # Performing these changes in edit mode avoids a scene update issue, but may not be totally neccesary.
                plat_arm_copy.data.transform(armature.matrix_basis.inverted())
                bpy.ops.object.mode_set(mode="OBJECT")
                for obj in get_objects(plat_collection.all_objects):
                    if obj.type == 'MESH':
                        obj.data.transform(armature.matrix_basis.inverted(), shape_keys=True)
                        obj.data.update()

            # Copy all of our 'copyonly' objects here, and add them to the export group
            if copy_only_handling == "COPY":
                for obj in get_objects(armature.children, {"MESH"}, filter_func=lambda obj:
                                       not not_copyonly(obj)):
                    new_obj = self.tree_copy(obj, plat_arm_copy, plat_collection, ignore_hidden,
                                              view_layer=orig_view_layer)
                    if not new_obj:
                        continue
                    new_obj.parent = plat_arm_copy
                    new_obj['tuxedoForcedExportName'] = obj.name

                    # Make sure all armature modifiers target the new armature
                    for modifier in new_obj.modifiers:
                        if modifier.type == "ARMATURE":
                            modifier.object = plat_arm_copy
                        if modifier.type == "MULTIRES":
                            modifier.render_levels = modifier.total_levels

                bpy.ops.object.select_all(action='DESELECT')
                for obj in get_objects(core.get_children_recursive(plat_arm_copy), {"MESH"}):
                    obj.select_set(True)

                # Join to save on skinned mesh renderers
                # 989onan - We don't want this for Gmod since Gmod allows for multiple object groups.
                if export_format != "GMOD":
                    core.join_meshes(context, armature_name=plat_arm_copy.name)
                    for obj in get_objects(core.get_children_recursive(plat_arm_copy), {"MESH"}):
                        obj['tuxedoForcedExportName'] = orig_largest_obj_name

            # Prep export group 1
            export_groups[0][1].extend(obj.name for obj in core.get_children_recursive(plat_arm_copy))

            for export_group in export_groups:
                assert(all(obj_name in plat_collection.all_objects for obj_name in export_group[1]), export_group)
                bpy.ops.object.select_all(action='DESELECT')
                for obj in get_objects(plat_collection.all_objects):
                    if obj.name in export_group[1]:
                        obj.select_set(True)
                if export_format == "FBX":
                    # Monkeypatch the FBX exporter to use 'tuxedoForcedExportName' instead of obj.name
                    core.patch_fbx_exporter()
                    bpy.ops.export_scene.fbx(filepath=bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + export_group[0] + ".fbx"), check_existing=False, filter_glob='*.fbx',
                                             use_selection=True,
                                             use_active_collection=False, global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                                             bake_space_transform=False, object_types={'ARMATURE', 'MESH'},
                                             use_mesh_modifiers=False, use_mesh_modifiers_render=False, mesh_smooth_type='OFF', use_subsurf=False,
                                             use_mesh_edges=False, use_tspace=False, use_custom_props=False, add_leaf_bones=False, primary_bone_axis='Y',
                                             secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=True,
                                             path_mode='AUTO',
                                             embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True,
                                             axis_forward='-Z', axis_up='Y')
                elif export_format == "DAE":
                    bpy.ops.wm.collada_export(filepath=bpy.path.abspath("//Tuxedo Bake/" + platform_name + "/" + export_group[0] + ".dae"), check_existing=False, filter_blender=False, filter_backup=False, filter_image=False, filter_movie=False,
                                              filter_python=False, filter_font=False, filter_sound=False, filter_text=False, filter_archive=False, filter_btx=False,
                                              filter_collada=True, filter_alembic=False, filter_usd=False, filter_volume=False, filter_folder=True,
                                              filter_blenlib=False, filemode=8, display_type='DEFAULT', prop_bc_export_ui_section='main',
                                              apply_modifiers=False, export_mesh_type=0, export_mesh_type_selection='view', export_global_forward_selection='Y',
                                              export_global_up_selection='Z', apply_global_orientation=False, selected=True, include_children=False,
                                              include_armatures=True, include_shapekeys=False, deform_bones_only=False, include_animations=True, include_all_actions=True,
                                              export_animation_type_selection='sample', sampling_rate=1, keep_smooth_curves=False, keep_keyframes=False, keep_flat_curves=False,
                                              active_uv_only=False, use_texture_copies=False, triangulate=True, use_object_instantiation=True, use_blender_profile=True,
                                              sort_by_name=False, export_object_transformation_type=0, export_object_transformation_type_selection='matrix',
                                              export_animation_transformation_type=0, open_sim=False,
                                              limit_precision=False, keep_bind_info=False)
                elif export_format == "GMOD":
                    gmod_male = platform.gmod_male
                    #compile model. (TAKES JUST AS LONG AS BAKE OR MORE)
                    bpy.ops.tuxedo.export_gmod_addon(steam_library_path=steam_library_path,gmod_model_name=gmod_model_name,platform_name=platform_name,armature_name="Tuxedo Armature", male=gmod_male)
                    print("Starting back up Tuxedo baking system")
            
            # Reapply tuxedo material
            if export_format != "GMOD":
                for obj in get_objects(plat_collection.all_objects, {"MESH"}):
                    if len(obj.material_slots) == 0:
                        obj.data.materials.append(mat)
                    else:
                        for slot in obj.material_slots:
                            if slot.material == None:
                                slot.material = mat

            # Delete our duplicate scene
            #edit, Users who wanna see what the script creates and make any last minute changes will want this disabled for gmod.
            if export_format != "GMOD":
                bpy.ops.scene.delete()
            else: #go back to the scene before, so that when we create the next one, it switches away from this one. therefore saving it from destruction
                bpy.context.window.scene = bpy.data.scenes[bpy.data.scenes.find(bpy.context.scene.name)-1]
            
            # Move armature so we can see it
            if quick_compare and export_format != "GMOD":
                for obj in get_objects(plat_collection.objects, filter_type={"ARMATURE"}):
                    obj.location.x += armature.dimensions.x * (1 + platform_number)
                for idx, _ in enumerate(lods):
                    if "ArmatureLOD" + str(idx + 1) in plat_collection.objects:
                        plat_collection.objects["ArmatureLOD" + str(idx + 1)].location.z += armature.dimensions.z * (1 + idx)

        # Delete our duplicate scene and the platform-agnostic Tuxedo Bake
        bpy.context.window.scene = bpy.data.scenes[bpy.data.scenes.find("Tuxedo Scene")]
        bpy.ops.scene.delete()
        
        try:
            for obj in get_objects(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)

            bpy.data.collections.remove(collection)
        except:
            print("huh couldn't delete the baking scenes. Oh well.")
        
        #clean unused data
        if not is_unittest:
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        # set viewport to material preview
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "MATERIAL"

        self.report({'INFO'}, t('tuxedo_bake.info.success'))

        print("BAKE COMPLETE!")
