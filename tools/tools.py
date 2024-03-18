import typing
import bmesh
import bpy
import math
import webbrowser
import operator
import numpy as np

from .. import globals

from .dictionaries import bone_names
from . import core
from .translate import t, translation_enum, translate_mmd

from ..class_register import wrapper_registry

from bpy.types import Context, Operator

from mathutils.geometry import intersect_point_line



@wrapper_registry
class Tuxedo_OT_RemoveDoublesSafely(bpy.types.Operator):
    bl_idname = 'tuxedo.remove_doubles_safely'
    bl_label = t('Tools.remove_doubles_safely.label')
    bl_description = t('Tools.remove_doubles_safely.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (bpy.context.mode == 'OBJECT') and (context.active_object is not None) and (context.active_object.type == "MESH")

    margin: bpy.props.FloatProperty(default=.00001)

    def execute(self, context: bpy.types.Context):
        core.remove_doubles_safely(mesh=context.active_object.data, margin=self.margin)

        return {'FINISHED'}
    
@wrapper_registry
class Tuxedo_OT_CreateDigitigradeLegs(bpy.types.Operator):
    bl_idname = "armature.createdigitigradelegs"
    bl_label = t('Tools.create_digitigrade_legs.label')
    bl_description = t('Tools.create_digitigrade_legs.desc')

    @classmethod
    def poll(cls, context):
        if(context.active_object is None):
            return False
        if(context.selected_editable_bones is not None):
            if(len(context.selected_editable_bones) == 2):
                return True
        return False

    def execute(self, context):

        for digi0 in context.selected_editable_bones:
            digi1 = None
            digi2 = None
            digi3 = None

            try:
                digi1 = digi0.children[0]
                digi2 = digi1.children[0]
                digi3 = digi2.children[0]
            except:
                print("bone format incorrect! Please select a chain of 4 continious bones!")
            digi4 = None
            try:
                digi4 = digi3.children[0]
            except:
                print("no toe bone. Continuing.")
            digi0.select = True
            digi1.select = True
            digi2.select = True
            digi3.select = True
            if(digi4):
                digi4.select = True
            bpy.ops.armature.roll_clear()
            bpy.ops.armature.select_all(action='DESELECT')

            scene = context.scene
            #creating transform for upper leg
            digi0.select = True
            bpy.ops.transform.create_orientation(name="CATS_digi0", overwrite=True)
            bpy.ops.armature.select_all(action='DESELECT')


            #duplicate digi0 and assign it to thigh
            thigh = core.duplicatebone(digi0)
            bpy.ops.armature.select_all(action='DESELECT')

            #make digi2 parrallel to digi1
            digi2.align_orientation(digi0)

            #extrude thigh
            thigh.select_tail = True
            bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked":False},TRANSFORM_OT_translate=None)
            #set new bone to calf varible
            bpy.ops.armature.select_more()
            calf = context.selected_bones[0]
            bpy.ops.armature.select_all(action='DESELECT')

            #set calf end to  digi2 end
            calf.tail = digi2.tail

            #make copy of calf, flip it, and then align bone so that it's head is moved to match in align phase
            flipedcalf = core.duplicatebone(calf)
            bpy.ops.armature.select_all(action='DESELECT')
            flipedcalf.select = True
            bpy.ops.armature.switch_direction()
            bpy.ops.armature.select_all(action='DESELECT')
            flippeddigi1 = core.duplicatebone(digi1)
            bpy.ops.armature.select_all(action='DESELECT')
            flippeddigi1.select = True
            bpy.ops.armature.switch_direction()
            bpy.ops.armature.select_all(action='DESELECT')



            #align flipped calf to flipped middle leg to move the head
            flipedcalf.align_orientation(flippeddigi1)

            flipedcalf.length = flippeddigi1.length

            #assign calf tail to flipped calf head so it moves calf's head
            calf.head = flipedcalf.tail

            #delete helper bones
            bpy.ops.armature.select_all(action='DESELECT')
            flippeddigi1.select = True
            bpy.ops.armature.delete()
            bpy.ops.armature.select_all(action='DESELECT')
            flipedcalf.select = True
            bpy.ops.armature.delete()
            bpy.ops.armature.select_all(action='DESELECT')


            #Tada! It's done! Now to duplicate toes and change parents


            #duplicate old foot and reparent
            newfoot = core.duplicatebone(digi3)
            newfoot.parent = calf
            #create toe bone if it exists
            if(digi4):
                #duplicate old toe and reparent
                newtoe = core.duplicatebone(digi4)
                newtoe.parent = newfoot
            #finally done!
        return {'FINISHED'}
    
    



@wrapper_registry
class Tuxedo_OT_DeleteZeroWeightBones(Operator):
    bl_idname = 'tuxedo.delete_zero_weight_bones'
    bl_label = t('Tools.delete_zero_weight_bones.label')
    bl_description = t('Tools.delete_zero_weight_bones.desc')
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context: bpy.types.Context):
        return context.active_object and context.active_object.type == "ARMATURE" and (context.object.mode == "EDIT" or context.object.mode == "POSE" or context.object.mode == "OBJECT") and (len(context.active_object.children) > 0)

    def execute(self, context: bpy.types.Context):
        armature = context.active_object
        data: bpy.types.Armature = armature.data
        weighted_groups: dict[bpy.types.Object, set[str]] = core.get_zero_and_weight_vertex_groups(armature=armature, invert=True)

        #find similar bones, where the bones are weighted to entirely nothing.
        #https://stackoverflow.com/a/10066661
        result: set[str] = set([i.name for i in data.bones])

        for obj,groups in weighted_groups.items():
            print([i for i in groups])
            result = result - groups
        
        num: int = 0
        prevmode = context.object.mode
        core.Set_Mode(context,mode='EDIT')
        for name in result:
            data.edit_bones.remove(data.edit_bones[name])
            num += 1
        
        core.Set_Mode(context,mode='OBJECT')
        armature.update_tag(refresh={'DATA'})
        core.Set_Mode(context,mode=prevmode)

        self.report({'INFO'}, t('Tools.delete_zero_weight_bones.number').format(amount=num))

        return {'FINISHED'}


@wrapper_registry
class Tuxedo_OT_DeleteZeroWeightVertexGroups(Operator):
    bl_idname = 'tuxedo.delete_zero_weight_vertex_groups'
    bl_label = t('Tools.delete_zero_weight_vertex_groups.label')
    bl_description = t('Tools.delete_zero_weight_vertex_groups.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context: bpy.types.Context):
        return context.active_object and context.active_object.type == "ARMATURE" and (context.object.mode == "EDIT" or context.object.mode == "POSE" or context.object.mode == "OBJECT") and (len(context.active_object.children) > 0)

    def execute(self, context: bpy.types.Context):
        armature = context.active_object
        zero_weight_vertex_groups: dict[bpy.types.Object, set[str]] = core.get_zero_and_weight_vertex_groups(armature=armature)
        
        num: int = 0

        for obj,groups in zero_weight_vertex_groups.items():
            for group in groups:
                obj.vertex_groups.remove(obj.vertex_groups[group])
                num += 1

        self.report({'INFO'}, t('Tools.delete_zero_weight_vertex_groups.number').format(amount=num))
        return {'FINISHED'}

@wrapper_registry
class Tuxedo_OT_ShapekeyToBasis(Operator):
    bl_idname = 'tuxedo.shapekey_to_basis'
    bl_label = t('Translations.shapekey_to_basis.label')
    bl_description = t('Translations.shapekey_to_basis.desc')
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context: bpy.types.Context):
        return core.has_shapekeys(context.active_object) and hasattr(context.active_object.active_shape_key,'name')
        
    def execute(self, context: bpy.types.Context):
        obj: bpy.types.Object = context.active_object
        data: bpy.types.Mesh = obj.data
        name: str = data.shape_keys.key_blocks[obj.active_shape_key_index].name
        if not core.apply_shapekey_to_basis(context,obj,name,delete_old=False):
            self.report({'ERROR'}, t('Translations.shapekey_to_basis.err1'))
            return {'CANCELLED'}
        else:
            return {'FINISHED'}



@wrapper_registry
class Tuxedo_OT_TranslateMMD(Operator):
    bl_idname = 'tuxedo.translate_mmd'
    bl_label = t('Translations.translate_mmd.label')
    bl_description = t('Translations.translate_mmd.desc')
    bl_options = {'REGISTER', 'UNDO'}

    translation_enum: bpy.props.EnumProperty(name=t('Translations.translation_coll_target.label'),description=t('Translations.translation_coll_target.desc'),items=translation_enum)
    
    def draw(self, context: bpy.types.Context):
        self.layout.prop(self, "translation_enum")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(self, context: bpy.types.Context):
        return (translation_enum(self, context) is not None) and (globals.mmd_tools_exist)

    def execute(self, context: bpy.types.Context):
        translate_mmd(self.translation_enum, context)
        return {'FINISHED'}


@wrapper_registry
class Tuxedo_OT_ConvertToResonite(Operator):
    bl_idname = 'tuxedo.convert_to_resonite'
    bl_label = t('Tools.convert_to_resonite.label')
    bl_description = t('Tools.convert_to_resonite.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if not core.get_armature(context):
            return False
        return True
        
    def execute(self, context: bpy.types.Context):
        armature = core.get_armature(context)

        translate_bone_fails = 0
        untranslated_bones = set()

        reverse_bone_lookup = dict()
        for (preferred_name, name_list) in bone_names.items():
            for name in name_list:
                reverse_bone_lookup[name] = preferred_name

        resonite_translations = {
            'hips': "Hips",
            'spine': "Spine",
            'chest': "Chest",
            'neck': "Neck",
            'head': "Head",
            'left_eye': "Eye.L",
            'right_eye': "Eye.R",
            'right_leg': "UpperLeg.R",
            'right_knee': "Calf.R",
            'right_ankle': "Foot.R",
            'right_toe': 'Toes.R',
            'right_shoulder': "Shoulder.R",
            'right_arm': "UpperArm.R",
            'right_elbow': "ForeArm.R",
            'right_wrist': "Hand.R",
            'left_leg': "UpperLeg.L",
            'left_knee': "Calf.L",
            'left_ankle': "Foot.L",
            'left_toe': "Toes.L",
            'left_shoulder': "Shoulder.L",
            'left_arm': "UpperArm.L",
            'left_elbow': "ForeArm.L",
            'left_wrist': "Hand.R",

            'pinkie_1_l': "pinkie1.L",
            'pinkie_2_l': "pinkie2.L",
            'pinkie_3_l': "pinkie3.L",
            'ring_1_l': "ring1.L",
            'ring_2_l': "ring2.L",
            'ring_3_l': "ring3.L",
            'middle_1_l': "middle1.L",
            'middle_2_l': "middle2.L",
            'middle_3_l': "middle3.L",
            'index_1_l': "index1.L",
            'index_2_l': "index2.L",
            'index_3_l': "index3.L",
            'thumb_1_l': "thumb1.L",
            'thumb_2_l': "thumb2.L",
            'thumb_3_l': "thumb3.L",

            'pinkie_1_r': "pinkie1.R",
            'pinkie_2_r': "pinkie2.R",
            'pinkie_3_r': "pinkie3.R",
            'ring_1_r': "ring1.R",
            'ring_2_r': "ring2.R",
            'ring_3_r': "ring3.R",
            'middle_1_r': "middle1.R",
            'middle_2_r': "middle2.R",
            'middle_3_r': "middle3.R",
            'index_1_r': "index1.R",
            'index_2_r': "index2.R",
            'index_3_r': "index3.R",
            'thumb_1_r': "thumb1.R",
            'thumb_2_r': "thumb2.R",
            'thumb_3_r': "thumb3.R"
        }

                

        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.object.mode_set(mode='OBJECT')
        for bone in armature.data.bones:
            if core.simplify_bonename(bone.name) in reverse_bone_lookup and reverse_bone_lookup[core.simplify_bonename(bone.name)] in resonite_translations:
                bone.name = resonite_translations[reverse_bone_lookup[core.simplify_bonename(bone.name)]]
            else:
                untranslated_bones.add(bone.name)
                translate_bone_fails += 1
            
        bpy.ops.object.mode_set(mode='OBJECT')

        if translate_bone_fails > 0:
            self.report({'INFO'}, t('Tools.convert_bones_resonite.fail').format(translate_bone_fails=translate_bone_fails))
        else:
            self.report({'INFO'}, t('Tools.convert_bones.success'))


        return {'FINISHED'}

@wrapper_registry
class Tuxedo_OT_MergeBoneWeightsToActive(Operator):
    bl_idname = 'tuxedo.merge_weights_to_active'
    bl_label = t('Tools.merge_weights_to_active.label')
    bl_description = t('Tools.merge_weights_to_active.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (bpy.context.mode == 'EDIT_ARMATURE') and (core.get_armature(context) is not None)

    def execute(self, context: bpy.types.Context):
        
        armature: bpy.types.Armature = core.get_armature(context).data

        original_edit = armature.use_mirror_x


        core.Set_Mode(context, 'EDIT')
        armature.use_mirror_x = False
        core.merge_bone_weights(context, core.get_armature(context), bone_names=[i.name for i in context.selected_editable_bones], active_bone_name=context.active_bone.name, remove_old=context.scene.delete_old_bones_merging)

        armature.use_mirror_x = original_edit
        return {'FINISHED'}

@wrapper_registry
class Tuxedo_OT_MergeBoneWeightsToParents(Operator):
    bl_idname = 'tuxedo.merge_weights_to_parents'
    bl_label = t('Tools.merge_weights_to_parents.label')
    bl_description = t('Tools.merge_weights_to_parents.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (bpy.context.mode == 'EDIT_ARMATURE') and (core.get_armature(context) is not None)

    def execute(self, context: bpy.types.Context):
        armature: bpy.types.Armature = core.get_armature(context).data

        original_edit = armature.use_mirror_x


        core.Set_Mode(context, 'EDIT')
        armature.use_mirror_x = False
        core.merge_bone_weights_to_respective_parents(context, core.get_armature(context), bone_names=[i.name for i in context.selected_editable_bones], remove_old=context.scene.delete_old_bones_merging)
        
        armature.use_mirror_x = original_edit
        return {'FINISHED'}

#a vastly improved and simplified apply modifier for object with shape keys.
@wrapper_registry
class Tuxedo_OT_ApplyModifierForObjectWithShapeKeys(bpy.types.Operator):
    bl_idname = 'tuxedo.apply_modifier_for_object_with_shape_keys'
    bl_label = t('Tools.apply_modifier_for_object_with_shape_keys.label')
    bl_description = t('Tools.apply_modifier_for_object_with_shape_keys.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (bpy.context.mode == 'OBJECT') and (context.active_object is not None) and core.has_shapekeys(context.active_object)

    modifiers: bpy.props.EnumProperty(name=t('Tools.modifiers_enum_label.label'), description=t('Tools.modifiers_enum_label.desc'), items=core.get_modifiers_active)

    def draw(self, context):
        self.layout.label(text=t('Tools.apply_modifier_for_object_with_shape_keys.drawlabel1').format(name=context.object.name))
        self.layout.prop(self, "modifiers")

    def execute(self, context: bpy.types.Context):
        
        result = core.apply_modifier_for_obj_with_shapekeys(context.object.modifiers[self.modifiers],delete_old=True)
        if (result != True):
            self.report({'ERROR'}, result)

        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

@wrapper_registry
class Tuxedo_OT_StartPoseMode(bpy.types.Operator):
    bl_idname = 'tuxedo.start_pose_mode'
    bl_label = t('Tools.start_pose_mode.label')
    bl_description = t('Tools.start_pose_mode.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return core.get_armature(context)

    def execute(self, context: bpy.types.Context):
        armature = core.get_armature(context)

        core.Set_Mode(context,'OBJECT')
        core.unselect_all()
        core.select(armature)
        core.set_active(armature)
        core.Set_Mode(context,'POSE')
        #the next 3 lines allow us to clear the pose without ruining the user's selection.
        bpy.ops.pose.transforms_clear()
        core.select_set_all_curmode(context, 'INVERT')
        bpy.ops.pose.transforms_clear()
        return {'FINISHED'}

@wrapper_registry
class Tuxedo_OT_EndPoseMode(bpy.types.Operator):
    bl_idname = 'tuxedo.end_pose_mode'
    bl_label = t('Tools.end_pose_mode.label')
    bl_description = t('Tools.end_pose_mode.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return core.get_armature(context)

    def execute(self, context: Context):
        bpy.ops.tuxedo.start_pose_mode() #take advantage of start pose method
        core.Set_Mode(context,'OBJECT')
        return {'FINISHED'}

#didn't know this existed already as PoseToRest - @989onan
"""@wrapper_registry
class Tuxedo_OT_ApplyAsRest(bpy.types.Operator):
    bl_idname = 'tuxedo.armature_apply_as_rest'
    bl_label = t('Tools.armature_apply_as_rest.label')
    bl_description = t('Tools.armature_apply_as_rest.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
     def poll(cls, context: Context):
        return core.get_armature(context)

    def execute(self, context: Context):
        meshes_and_armature = core.get_meshes_objects(context,core.get_armature(context).name )
        armature = core.get_armature(context)
        

        for obj in meshes_and_armature:
            if obj.type == 'MESH':
                modifier = None
                for mod in obj.modifiers:
                    if mod.type == "ARMATURE" and mod.object == armature:
                        modifier = mod
                        break
                
                if modifier == None: continue
                if core.has_shapekeys(obj):
                    result = core.apply_modifier_for_obj_with_shapekeys(modifier)
                    if (result != True):
                        self.report({'ERROR'},result)
                else:
                    core.apply_modifier(modifier)
        
        core.Set_Mode(context,'OBJECT')
        core.unselect_all()
        core.select(armature)
        core.set_active(armature)
        core.Set_Mode(context,'POSE')

        bpy.ops.pose.armature_apply()
        core.Set_Mode(context,'OBJECT')
        return {'FINISHED'} """

@wrapper_registry
class Tuxedo_OT_SavePoseAsShapekey(bpy.types.Operator):
    bl_idname = 'tuxedo.save_pose_as_shapekey'
    bl_label = t('Tools.save_pose_as_shapekey.label')
    bl_description = t('Tools.save_pose_as_shapekey.desc')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return core.get_armature(context)

    def execute(self, context):
        meshes_and_armature = core.get_meshes_objects(context,core.get_armature(context).name )
        armature = core.get_armature(context)
        
        core.Set_Mode(context,'OBJECT')
        for obj in meshes_and_armature:
            if obj.type == 'MESH':
                
                core.unselect_all()
                core.select(obj)
                core.set_active(obj)
                modifier = None
                for mod in obj.modifiers:
                    if mod.type == "ARMATURE" and mod.object == armature:
                        modifier = mod
                        break
                
                if modifier == None: continue
                bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier=modifier.name)

        
        core.unselect_all()
        core.select(armature)
        core.set_active(armature)
        core.Set_Mode(context,'POSE')
        return {'FINISHED'}

@wrapper_registry
class FitClothes(bpy.types.Operator):
    bl_idname = 'tuxedo.fit_clothes'
    bl_label = t('Tools.fit_clothes.label')
    bl_description = t('Tools.fit_clothes.desc')
    bl_options = {'REGISTER', 'UNDO'}

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
            core.apply_modifier(trans_modifier)

            # Setup armature
            for mod_name in [mod.name for mod in obj.modifiers]:
                if obj.modifiers[mod_name].type == 'ARMATURE':
                    obj.modifiers.remove(obj.modifiers[mod_name])
            arm_modifier = obj.modifiers.new(type='ARMATURE', name='Armature')
            arm_modifier.object = armature

        self.report({'INFO'}, t('Tools.fit_clothes.success'))
        return {'FINISHED'}




@wrapper_registry
class RepairShapekeys(bpy.types.Operator):
    bl_idname = 'tuxedo.repair_shapekeys'
    bl_label = t('Tools.repair_shapekeys.label')
    bl_description = t('Tools.repair_shapekeys.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            return True

        meshes = core.get_meshes_objects(context)
        return meshes

    def execute(self, context):
        objs = [context.active_object]
        if not objs[0] or (objs[0] and (objs[0].type != 'MESH' or objs[0].data.shape_keys is None)):
            bpy.ops.object.select_all(action='DESELECT')
            meshes = core.get_meshes_objects(context)
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

        self.report({'INFO'}, t('Tools.repair_shapekeys.success'))
        return {'FINISHED'}

@wrapper_registry
class SmartDecimation(bpy.types.Operator):
    bl_idname = 'tuxedo.smart_decimation'
    bl_label = t('Tools.smart_decimate.label')
    bl_description = t('Tools.smart_decimate.desc')
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
        armature = core.get_armature(context, armature_name=self.armature_name)
        if not self.preserve_objects:
            core.join_meshes(context, armature.name)
        meshes_obj = core.get_meshes_objects(context, armature_name=self.armature_name)

        if len(meshes_obj) == 0:
            self.report({'INFO'}, t('no_meshes_found'))
            return {'FINISHED'}
        if not armature:
            self.report({'INFO'}, t('no_armature_found'))
            return {'FINISHED'}
        tris_count = 0

        for mesh in meshes_obj:
            core.triangulate_mesh(mesh)
            if context.scene.decimation_remove_doubles:
                core.remove_doubles_safely(mesh.data, 0.00001)
            tris_count += get_tricount(mesh.data.polygons)
            core.add_shapekey(mesh, 'Tuxedo Basis', False)

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
                self.report({'INFO'}, t('SmartDecimation.no_decimation_needed'))
                return {'FINISHED'}
            else:
                self.report({'INFO'}, t('SmartDecimation.decimated_some_meshes') + str(self.max_single_mesh_tris))
        else:

            if tris_count == 0:
                self.report({'INFO'}, t('no_tris'))
                return {'FINISHED'}
            elif decimation <= 0:
                self.report({'INFO'}, t('SmartDecimation.error_too_many_polys'))
                return {'FINISHED'}
            for mesh in meshes_obj:
                tris = get_tricount(mesh)

                newdecimation = decimation if not (math.ceil(tris*decimation) > self.max_single_mesh_tris) else (1. + ((self.max_single_mesh_tris - tris) / tris))

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

        if core.has_shapekeys(mesh):
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

@wrapper_registry
class GenerateTwistBones(bpy.types.Operator):
    bl_idname = 'tuxedo.generate_twist_bones'
    bl_label = t('Tools.gen_twist_bones.label')
    bl_description = t('Tools.gen_twist_bones.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if not core.get_armature(context):
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
            for mesh in core.get_meshes_objects(context, armature_name=armature.name):
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

        self.report({'INFO'}, t('Tools.gen_twist_bones.success'))
        return {'FINISHED'}

@wrapper_registry
class TwistTutorialButton(bpy.types.Operator):
    bl_idname = 'tuxedo.twist_tutorial'
    bl_label = t('Tools.twist_tutorial.label')
    bl_description = t('Tools.twist_tutorial.desc')
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

@wrapper_registry
class ConvertToSecondlifeButton(bpy.types.Operator):
    bl_idname = 'tuxedo.convert_to_secondlife'
    bl_label = t('Tools.convert_to_secondlife.label')
    bl_description = t('Tools.convert_to_secondlife.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    armature_name: bpy.props.StringProperty(
        default=''
    )

    @classmethod
    def poll(cls, context):
        if not core.get_armature(context):
            return False
        return True

    def execute(self, context):
        armature = core.get_armature(context, self.armature_name)

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
            if core.simplify_bonename(bone.name) in reverse_bone_lookup and reverse_bone_lookup[core.simplify_bonename(bone.name)] in sl_translations:
                bone.name = sl_translations[reverse_bone_lookup[core.simplify_bonename(bone.name)]]
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
            core.merge_bone_weights_to_respective_parents(context, armature, [bone.name for bone in context.selected_editable_bones])

        for bone in context.visible_bones:
            bone.use_connect = False

        for bone in context.visible_bones:
            bone.tail[:] = bone.head[:]
            bone.tail[0] = bone.head[0] + 0.1
            bone.roll = 0

        context.object.data.use_mirror_x = old_mirror_setting
        bpy.ops.object.mode_set(mode='OBJECT')

        if translate_bone_fails > 0:
            self.report({'INFO'}, t('Tools.convert_bones.fail').format(translate_bone_fails=translate_bone_fails))
        else:
            self.report({'INFO'}, t('Tools.convert_bones.success'))

        return {'FINISHED'}



# Code below Stolen from Cats Blender Plugin File "common.py", Sorry! But tbf we don't want depenencies. Full credit to the cats blender team!
# Btw the code it's stolen from is GPL
@wrapper_registry
class PoseToRest(bpy.types.Operator):
    bl_idname = 'tuxedo.pose_to_rest'
    bl_label = t('Tools.pose_to_rest.label')
    bl_description = t('Tools.pose_to_rest.label')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    armature_name: bpy.props.StringProperty(
        default=''
    )

    @classmethod
    def poll(cls, context):
        armature = core.get_armature(context)
        return armature and armature.mode == 'POSE'

    def execute(self, context):

        armature_obj = core.get_armature(context,self.armature_name)
        mesh_objs = core.get_meshes_objects(context,armature_name=armature_obj.name)
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
        with bpy.context.temp_override(active_object = armature_obj): bpy.ops.pose.armature_apply()

        # Stop pose mode after operation
        armature = core.get_armature(context,self.armature_name)
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

        armature = core.get_armature(context,self.armature_name)
        # armature.data.pose_position = 'REST'

        for mesh in core.get_meshes_objects(context,armature_name=self.armature_name):
            if core.has_shapekeys(mesh):
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
        # Moving the modifier to the first index will prevent an Info message about the applied modifier not being
        # first and potentially having unexpected results.
        with bpy.context.temp_override(object= mesh_obj):
            if bpy.app.version >= (2, 90, 0):
                # modifier_move_to_index was added in Blender 2.90
                bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=0)
            else:
                # The newly created modifier will be at the bottom of the list
                armature_mod_index = len(mesh_obj.modifiers) - 1
                # Move the modifier up until it's at the top of the list
                for _ in range(armature_mod_index):
                    bpy.ops.object.modifier_move_up( modifier=mod_name)
            bpy.ops.object.modifier_apply( modifier=mod_name)
        
        
    
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
# -------------------------------------------------------------------
# SRanipal Facetracking Shapekey List
# -------------------------------------------------------------------

SRanipal_Labels = [
    "Eye_Left_squeeze",
    "Eye_Right_squeeze",
    "Eye_Left_Blink",
    "Eye_Left_Right",
    "Eye_Left_Left",
    "Eye_Left_Down",
    "Eye_Left_Up",
    "Eye_Right_Blink",
    "Eye_Right_Right",
    "Eye_Right_Left",
    "Eye_Right_Down",
    "Eye_Right_Up",
    "Eye_Left_Wide",
    "Eye_Right_Wide",
    "Eye_Left_Dilation",
    "Eye_Left_Constrict",
    "Eye_Right_Dilation",
    "Eye_Right_Constrict",
    "Jaw_Right",
    "Jaw_Left",
    "Jaw_Forward",
    "Jaw_Open",
    "Mouth_Ape_Shape",
    "Mouth_Left",
    "Mouth_Right",
    "Mouth_Upper_Right",
    "Mouth_Upper_Left",
    "Mouth_Lower_Right",
    "Mouth_Lower_Left",
    "Mouth_Smile_Right",
    "Mouth_Smile_Left",
    "Mouth_Sad_Right",
    "Mouth_Sad_Left",
    "Mouth_Pout",
    "Cheek_Puff_Right",
    "Cheek_Puff_Left",
    "Cheek_Suck",
    "Mouth_Upper_Up",
    "Mouth_Lower_Down",
    "Mouth_Upper_UpRight",
    "Mouth_Upper_UpLeft",
    "Mouth_Lower_DownRight",
    "Mouth_Lower_DownLeft",
    "Mouth_O_Shape",
    "Mouth_Upper_Overturn",
    "Mouth_Lower_Overturn",
    "Mouth_Upper_Inside",
    "Mouth_Lower_Inside",
    "Mouth_Lower_Overlay",
    "Tongue_LongStep1",
    "Tongue_LongStep2",
    "Tongue_Down",
    "Tongue_Up",
    "Tongue_Right",
    "Tongue_Left",
    "Tongue_Roll",
    "Tongue_UpRight_Morph",
    "Tongue_UpLeft_Morph",
    "Tongue_DownRight_Morph",
    "Tongue_DownLeft_Morph",
]

# -------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# Shape Key Operators
# -------------------------------------------------------------------

@wrapper_registry
class FT_OT_CreateShapeKeys(Operator):
    """Creates SRanipal Facetracking Shape Keys"""
    bl_label = "Create SRanipal Face Tracking Shape Keys"
    bl_idname = "ft.create_shapekeys"

    def execute(self, context):

        object = bpy.context.object
        scene = context.scene
        ft_mesh = scene.ft_mesh
        active_object = bpy.context.active_object
        mesh = bpy.ops.mesh
        ops = bpy.ops

        #Set the selected mesh to active object 
        mesh = core.get_objects()[ft_mesh]
        self.report({'INFO'}, "Selected mesh is: " + str(ft_mesh))
        core.set_active(mesh)

        #Check if there is shape keys on the mesh
        if object.data.shape_keys:

            #Create beginning seperation marker for VRCFT Shape Keys
            if core.duplicate_shapekey("~~ SRanipal Face Tracking ~~") == False :
                object.shape_key_add(name="~~ SRanipal Face Tracking ~~", from_mix=False)

            #Clear all existing values for shape keys
            ops.object.shape_key_clear()

            basis_key = core.get_shapekeys_ft(self, context)[0][0]
            basis_key_ref = object.data.shape_keys.key_blocks[basis_key]
            basis_key_data = np.empty((len(basis_key_ref.data), 3), dtype=np.float32)
            basis_key_ref.data.foreach_get("co", np.ravel(basis_key_data))
            if context.scene.ft_ch != basis_key:
                ch_deltas, bounding_box = core.get_shapekey_delta(object, context.scene.ft_ch)
                crossfade_l = lambda f: core.crossfade(f, bounding_box[0], bounding_box[1], 0.2)
                crossfade_factors = np.vectorize(crossfade_l)(basis_key_data[:, 0])
            for x in range(len(SRanipal_Labels)):
                curr_key = eval("scene.ft_shapekey_" + str(x))
                curr_key_enable = eval("scene.ft_shapekey_enable_" + str(x))
                #Skip key if shape is disabled
                if not curr_key_enable:
                    continue
                # determine if we're going to be working with visemes
                label = SRanipal_Labels[x]
                generate_eyes = (any(string in label for string in ['Blink', 'squeeze', 'Wide']) and
                    context.scene.ft_blink != basis_key )
                generate_jaw = (any(string in label for string in ['Jaw']) and context.scene.ft_aa != basis_key)
                generate_mouth = (any(string in label for string in ['Upper_Up', 'Lower_Down', 'Upper_Left', 'Lower_Right', 'Upper_Right', 'Lower_Left', 'Inside', 'Pout', 'Mouth_Left', 'Mouth_Right']) and context.scene.ft_ch != basis_key and context.scene.ft_oh != basis_key)
                generate_smile = (any(string in label for string in ['Smile']) and context.scene.ft_smile != basis_key)
                generate_frown = (any(string in label for string in ['Sad']) and context.scene.ft_frown != basis_key)
                if context.scene.ft_ch != basis_key:
                    crossfade_arr = 1 - crossfade_factors if 'Left' in label else crossfade_factors

                #Check if blend with 'Basis' shape key
                if curr_key == "Basis" and not (generate_eyes or generate_jaw or generate_frown or generate_mouth or generate_smile):
                    #Check for duplicates
                    if not core.duplicate_shapekey(SRanipal_Labels[x]):
                        object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                    #Do not overwrite if the shape key exists and is on 'Basis'

                else:
                    #Check for duplicates
                    if not core.duplicate_shapekey(SRanipal_Labels[x]):
                        # Special handling for visemes
                        if generate_eyes:
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                            deltas, _ = core.get_shapekey_delta(object, context.scene.ft_blink)
                            factor = 1
                            if 'squeeze' in label:
                                factor = 1.1
                            elif 'Wide' in label:
                                factor = -0.15
                            if 'Left' in label:
                                side_relevant = basis_key_data[:, 0] > 0
                            if 'Right' in label:
                                side_relevant = basis_key_data[:, 0] < 0
                            deltas[~side_relevant] = 0.0
                            object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(basis_key_data + (deltas * factor)))
                        elif generate_mouth:
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                            oh_deltas, _ = core.get_shapekey_delta(object, context.scene.ft_oh)

                            # consider vertices where delta(v_ch) > delta(v_oh) upper lip, and vice versa
                            ch_should_be_greater = 'Upper' in label
                            both_lips = any(string in label for string in ['Pout', 'Mouth_Left', 'Mouth_Right'])

                            lip_magnitude = np.linalg.norm(ch_deltas, axis=1)
                            if not both_lips:
                                ch_greater = np.linalg.norm(ch_deltas, axis=1) >= np.linalg.norm(oh_deltas, axis=1)
                                if ch_should_be_greater:
                                    lip_mask = ch_greater
                                else:
                                    lip_mask = ~ch_greater
                                lip_magnitude[~lip_mask] = 0.0
                            new_key = basis_key_data.copy()
                            if any(string in label for string in ['Upper_Left', 'Lower_Right', 'Upper_Right', 'Lower_Left', 'Mouth_Left', 'Mouth_Right']):
                                # instead of blending, we take the magnitude of movement * .1 and direct it to the left/right
                                multiplier = -1 if 'Right' in label else 1
                                new_key[:, 0] = new_key[:, 0] - (lip_magnitude * 0.75 * multiplier)
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            elif any(string in label for string in ['Inside']):
                                new_key[:, 1] += lip_magnitude * 0.75
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            elif any(string in label for string in ['Pout']):
                                new_key[:, 1] -= lip_magnitude * 0.75
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            elif any(string in label for string in ['UpLeft', 'UpRight', 'DownLeft', 'DownRight']):
                                new_key += (ch_deltas * crossfade_arr[:, None] * (lip_mask).astype(float)[:, None])
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            else:
                                new_key += (ch_deltas * (lip_mask).astype(float)[:, None])
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                        elif generate_smile:
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                            smile_deltas, _ = core.get_shapekey_delta(object, context.scene.ft_smile)

                            object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel((smile_deltas * crossfade_arr[:, None] + basis_key_data)))
                        elif generate_frown:
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                            frown_deltas, _ = core.get_shapekey_delta(object, context.scene.ft_frown)

                            object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel((frown_deltas * crossfade_arr[:, None] + basis_key_data)))
                        elif generate_jaw:
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=False)
                            aa_deltas, _ = core.get_shapekey_delta(object, context.scene.ft_aa)
                            jaw_magnitude = np.linalg.norm(aa_deltas, axis=1)

                            new_key = basis_key_data.copy()
                            if any(string in label for string in ['Left', 'Right']):
                                # instead of blending, we take the magnitude of movement * .1 and direct it to the left/right
                                multiplier = -1 if 'Right' in label else 1
                                new_key[:, 0] -= jaw_magnitude * 0.75 * multiplier
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            elif any(string in label for string in ['Forward']):
                                new_key[:, 1] -= jaw_magnitude * 0.5
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(new_key))
                            else:
                                object.data.shape_keys.key_blocks[label].data.foreach_set("co", np.ravel(aa_deltas * 2.0 + basis_key_data))
                        else:
                            # Find shapekey enterred and mix to create new shapekey
                            object.active_shape_key_index = active_object.data.shape_keys.key_blocks.find(curr_key)
                            object.data.shape_keys.key_blocks[curr_key].value = 1
                            object.shape_key_add(name=SRanipal_Labels[x], from_mix=True)
                    else:
                        #Mix to existing shape key duplicate
                        object.active_shape_key_index = active_object.data.shape_keys.key_blocks.find(SRanipal_Labels[x])
                        object.data.shape_keys.key_blocks[curr_key].value = 1
                        ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_mode(type="VERT")
                        ops.mesh.select_all(action='SELECT')
                        ops.mesh.blend_from_shape(shape=curr_key, blend=1.0, add=False)
                        self.report({'INFO'}, "Existing SRanipal face tracking shape key: " + SRanipal_Labels[x] + " has been overwritten with: " + curr_key)
                    #Clear shape key weights
                    ops.object.shape_key_clear()

            self.report({'INFO'}, "SRanipal face tracking shapekeys have been created on mesh")


            #Cleanup mode state
            ops.object.mode_set(mode='OBJECT', toggle=False)

            #Move active shape to 'Basis'
            active_object.active_shape_key_index = 0

        else:
            #Error message if basis does not exist
            self.report({'WARNING'}, "No shape keys found on mesh")
        return{'FINISHED'}
