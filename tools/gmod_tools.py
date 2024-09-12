# GPL Licence
import bpy
import math
import os
import time
import subprocess
import shutil
from mathutils import Matrix
import itertools

from ..class_register import wrapper_registry

from .translate import t
from . import core
from .dictionaries import bone_names

from bpy.props import StringProperty, BoolProperty

######### GMOD SCRIPTS #########



# @989onan - I'm sorry for the mess below, but at least I refactored it since this is new place for this code. The most permanent solution is a temporary one.

@wrapper_registry
class ConvertToValveButton(bpy.types.Operator):
    bl_idname = 'tuxedo.convert_to_valve'
    bl_label = t('Tools.convert_to_valve.label')
    bl_description = t('Tools.convert_to_valve.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    armature_name: StringProperty(
        default=''
    )

    @classmethod

    def poll(cls, context):
        if not core.get_armature(context):
            return False
        return True

    def execute(self, context):
        translate_bone_fails = 0
        if self.armature_name == "":
            armature = core.get_armature(context,self.armature_name)
        else:
            armature = context.view_layer.objects.get(self.armature_name)

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
            if core.simplify_bonename(bone.name) in reverse_bone_lookup and reverse_bone_lookup[core.simplify_bonename(bone.name)] in valve_translations:
                bone.name = reverse_bone_lookup[core.simplify_bonename(bone.name)]
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
            self.report({'INFO'}, t('Tools.convert_bones.fail').format(translate_bone_fails=translate_bone_fails))

        self.report({'INFO'}, t('Tools.convert_bones.success'))
        return {'FINISHED'}


@wrapper_registry
class ExportGmodPlayermodel(bpy.types.Operator):
    bl_idname = "tuxedo.export_gmod_addon"
    bl_label = t('Tools.export_gmod_addon.label')
    bl_description = t('Tools.export_gmod_addon.desc')
    bl_options = {'INTERNAL'}

    steam_library_path: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    gmod_model_name: bpy.props.StringProperty(default = "Missing No")
    platform_name: bpy.props.StringProperty(default = "Garrys Mod")
    armature_name: bpy.props.StringProperty(default = "")
    male: BoolProperty(default=True)

    def execute(self, context):
        print("===============START GMOD EXPORT PROCESS===============")
        
        model_name = self.gmod_model_name
        platform_name = self.platform_name
        sanitized_model_name = ""
        offical_model_name = ""

        gender_file: str = "reference_male.smd" if self.male else "reference_female.smd"
        gender_armature_name: str = "reference_male_skeleton" if self.male else "reference_female_skeleton"
        
        try:
            core.Set_Mode(context, "OBJECT")
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
            core.Set_Mode(context, "OBJECT")
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')


        armature = core.get_armature(context,self.armature_name)
        context.view_layer.objects.active = armature

        print("putting armature and objects under reference collection")
        #putting objects and armature under a better collection.
        refcoll_list = [obj for obj in armature.children]
        refcoll_list.append(armature)
        
        #once we get our objects, before anything we wanna sanitize it.
        #santitize object, material, and shapekey names
        for obj in refcoll_list:
            obj.name = sanitized_name(obj.name) #this is needed since objects (not just meshes) will throw errors if named weirdly
            if obj.type == "MESH":
                print("sanitizing material names for gmod for object "+obj.name)
                for material in obj.material_slots:
                    mat = material.material
                    mat.name = sanitized_name(mat.name)
                if core.has_shapekeys(obj):
                    print("sanitizing shapekey names for gmod for object "+obj.name)
                    for shapekey in obj.data.shape_keys.key_blocks:
                        shapekey.name = sanitized_name(shapekey.name)
        
        self.armature_name = armature.name
        
        refcoll = core.Move_to_New_Or_Existing_Collection(context, sanitized_model_name+"_ref", objects_alternative_list = refcoll_list) #put armature and children into alt object list
        

        print("marking which models toggled off by default, and deleting always inactive objects for body groups.")
        hidden_by_default_bodygroups = []
        do_not_toggle_bodygroups = []
        always_hidden_garbage = []
        context.view_layer.objects.active = armature
        for mesh in refcoll.objects:
            if mesh.type == "MESH":
                if (not mesh.gmod_shown_by_default) and (not mesh.gmod_is_toggleable):
                    always_hidden_garbage.append(mesh.name)
                    continue
                if not mesh.gmod_is_toggleable:
                    do_not_toggle_bodygroups.append(mesh.name)
                if not mesh.gmod_shown_by_default:
                    hidden_by_default_bodygroups.append(mesh.name)

        print("deleting always hidden meshes")
        for obj in always_hidden_garbage:
            print("mesh \""+obj.name+"\" always hidden, deleting!")
            core.Destroy_By_Name(context, obj)

        for obj in do_not_toggle_bodygroups:
            mesh = context.view_layer.objects.get(obj)
            mesh.hide_viewport = False
        for obj in hidden_by_default_bodygroups:
            mesh = context.view_layer.objects.get(obj)
            mesh.hide_set(False)


        print("translating bones. if you hit an error here please fix your model using fix model!!!!!! If you have, please ignore the error.")
        bpy.ops.tuxedo.convert_to_valve(armature_name = self.armature_name)

        print("testing if SMD tools exist.")
        try:
            bpy.ops.import_scene.smd('EXEC_DEFAULT',files=[{'name': gender_file}], append = "NEW_ARMATURE",directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")+"/assets/garrysmod/")
        except AttributeError:
            bpy.ops.tuxedo_bake.nosource('INVOKE_DEFAULT')
            return {'FINISHED'}

        #clean imported stuff
        print("cleaning imported armature")


        # move the armature to it's proper collection if it ended up outside. (somehow idk)
        
        barneycollection = core.Move_to_New_Or_Existing_Collection(context, "source_collection", objects_alternative_list = [context.view_layer.objects.get(gender_armature_name)])


        


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
        core.Set_Mode(context,"OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in refcoll.objects:
            obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        core.update_viewport()
        
        print("getting meshes in ref collection")

        parentobj, body_armature = core.Get_Meshes_And_Armature(context, refcoll)


        if (not body_armature) or (len(parentobj) == 0):
            print('Report: Error')
            print(refcoll.name+" gmod baking failed at this point since bake result didn't have at least one armature and one mesh!")


        print("clearing bone rolls")
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        core.Set_Mode(context, "EDIT")
        bpy.ops.armature.reveal()
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.armature.roll_clear()
        core.Set_Mode(context, "OBJECT")
        
        
        print("straightening arm bones")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        core.Set_Mode(context, "EDIT")

        #bpy.ops.pose.select_all(action='SELECT')
        #Set arms straight in edit mode. if the arm bones are messed up by this, user was told to make it t-pose that is user error not our issue. - @989onan
        #This code makes it perfect, since gmod likes to make this stuff twist really badly if it isn't perfectly straight - @989onan
        #This needing to be done is weird because every other game requires the exact opposite - @989onan
        
        positiony = body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].head[1]
        positionz = body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].head[2]
        
        
        #we do head here to get the shoulder joint
        body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].head[1] = positiony
        body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].head[2] = positionz
        
        body_armature.data.edit_bones["ValveBiped.Bip01_R_UpperArm"].head[1] = positiony
        body_armature.data.edit_bones["ValveBiped.Bip01_R_UpperArm"].head[2] = positionz
        
        #we do tail here to get the elbow joint
        body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].tail[1] = positiony 
        body_armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"].tail[2] = positionz
        
        body_armature.data.edit_bones["ValveBiped.Bip01_R_UpperArm"].tail[1] = positiony
        body_armature.data.edit_bones["ValveBiped.Bip01_R_UpperArm"].tail[2] = positionz
        
        #we do tail here again to get the wrist joint
        body_armature.data.edit_bones["ValveBiped.Bip01_L_Forearm"].tail[1] = positiony
        body_armature.data.edit_bones["ValveBiped.Bip01_L_Forearm"].tail[2] = positionz
        
        body_armature.data.edit_bones["ValveBiped.Bip01_R_Forearm"].tail[1] = positiony
        body_armature.data.edit_bones["ValveBiped.Bip01_R_Forearm"].tail[2] = positionz
        
        
        core.Set_Mode(context, "OBJECT")
        print("a-posing armature, if this failed, you do not have standard bone names!")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        core.Set_Mode(context, "POSE")

        bpy.ops.pose.select_all(action='SELECT')

        bpy.ops.pose.reveal(select=True)
        body_armature.pose.bones["ValveBiped.Bip01_L_UpperArm"].rotation_mode = "XYZ"
        body_armature.pose.bones["ValveBiped.Bip01_L_UpperArm"].rotation_euler[0] = -45
        body_armature.pose.bones["ValveBiped.Bip01_R_UpperArm"].rotation_mode = "XYZ"
        body_armature.pose.bones["ValveBiped.Bip01_R_UpperArm"].rotation_euler[0] = -45
        print("doing an apply rest pose")
        bpy.ops.tuxedo.pose_to_rest()
        core.Set_Mode(context, "OBJECT")
        
        core.update_viewport()

        print("grabbing barney armature")
        barney_armature = None
        barneycollection = bpy.data.collections.get("source_collection")

        parentobj, barney_armature = core.Get_Meshes_And_Armature(context, barneycollection)
        assert(barneycollection is not None)
        assert(len(barneycollection.objects) > 0)


        print("duplicating barney armature")
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = barney_armature
        barney_armature.select_set(True)
        with bpy.context.temp_override(object = barney_armature, selected_objects = [barney_armature]): bpy.ops.object.duplicate( linked=False)
        
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
            core.Set_Mode(context, "OBJECT")
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = context.view_layer.objects[body_armature_name]
            core.Set_Mode(context, "EDIT")

            try:
                obj = context.view_layer.objects[barney_armature_name]
                editbone = context.view_layer.objects[body_armature_name].data.edit_bones[barney_bone_name]
                bone = obj.pose.bones[barney_bone_name]
                bone.rotation_mode = "XYZ"
                newmatrix = Matrix.Translation((editbone.matrix[0][3],editbone.matrix[1][3],editbone.matrix[2][3]))
                bone.matrix = newmatrix
                bone.rotation_euler = (0,0,0)
            except Exception as e:
                print("barney bone above failed! may not exist on our armature, which is okay!")
                print(e)



        print("applying barney pose as rest pose")
        core.Set_Mode(context, "OBJECT")

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = context.view_layer.objects[barney_armature_name]
        core.Set_Mode(context, "POSE")
        print("doing an apply rest pose")
        bpy.ops.tuxedo.pose_to_rest()
        core.Set_Mode(context, "OBJECT")
        
        core.update_viewport()

        print("putting barney armature bones on your model")
        core.merge_armature_stage_one(context, body_armature_name, barney_armature_name)


        print("fixing bones to point correct direction in order to mitigate bad bone twists. (includes thighs and jiggle bones)")


        
        twisted_armature = context.view_layer.objects[body_armature_name]
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
        core.Set_Mode(context, "EDIT")
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
        core.Move_to_New_Or_Existing_Collection(context, refcoll.name, objects_alternative_list = [context.view_layer.objects.get(body_armature_name)])

        core.update_viewport()


        print("Duplicating reference collection to make phys collection")
        physcoll = core.Copy_to_existing_collection(context, old_coll = refcoll, new_coll_name=sanitized_model_name+"_phys")

        print("making arms collection and copying over from reference")
        armcoll = core.Copy_to_existing_collection(context, old_coll = refcoll, new_coll_name=sanitized_model_name+"_arms")

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
        core.Set_Mode(context, "OBJECT")
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
                core.Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                core.Set_Mode(context, "EDIT")
                bpy.ops.mesh.select_all(action='DESELECT')
                bones_to_merge_valve = []
                for index,group in enumerate(obj.vertex_groups):
                    if "tail" in group.name.lower():
                        core.Set_Mode(context, "OBJECT")
                        bpy.ops.object.select_all(action='DESELECT')
                        context.view_layer.objects.active = obj
                        core.Set_Mode(context, "EDIT")
                        bpy.ops.mesh.select_all(action='DESELECT')
                        obj.vertex_groups.active_index = index
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.object.vertex_group_remove_from()
                    elif (not (group.name in bone_names_for_phys)): # we wanna merge bones that aren't being used for physics, so we have a simplifed physics rig - @989onan
                        core.Set_Mode(context, "OBJECT")
                        bpy.ops.object.select_all(action='DESELECT')
                        context.view_layer.objects.active = phys_armature
                        core.Set_Mode(context, "EDIT")
                        bpy.ops.armature.select_all(action='DESELECT')
                        bone = phys_armature.data.edit_bones.get(group.name)
                        if bone is not None:
                            #add to select phys bone list
                            print("adding \""+bone.name+"\" bone to be merged to it's parent for phys mesh")
                            bones_to_merge_valve.append(bone.name)
                        else:
                            pass #if the group no longer has a bone who cares. usually.... <- wow this was a bad comment by past me. I meant to say groups for bones that no longer exist basically. Like trash weight data - @989onan
                core.Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')

                #use tuxedo function to yeet dem bones on phys mesh.
                context.view_layer.objects.active = phys_armature
                core.Set_Mode(context, "EDIT")
                core.merge_bone_weights_to_respective_parents(context, phys_armature, bones_to_merge_valve)
                core.Set_Mode(context, "OBJECT")

                #separating into seperate phys objects to join later.
                core.Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                core.Set_Mode(context, "EDIT")
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
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')

        print("joining phys parts and assigning to vertex groups")
        #clear vertex groups and assign each object to their corosponding vertex group.
        for bonename,obj in convexobjects.items():
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = obj
            core.Set_Mode(context, "EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            obj.vertex_groups.clear()
            obj.vertex_groups.new(name=bonename)
            obj.vertex_groups.active_index = 0
            bpy.ops.object.vertex_group_assign()
            core.Set_Mode(context, "OBJECT")
            for i in range(0,len(obj.material_slots)):
                bpy.ops.object.material_slot_remove()

        core.update_viewport()

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
        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armcoll)



        print("step 1 arms: getting entire arm list of bones for each side.")
        arm_bone_names = []
        context.view_layer.objects.active = arms_armature
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        arms_armature.select_set(True)
        core.Set_Mode(context, "EDIT")
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

        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armcoll)

        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in parentobj:
            obj.select_set(True)
        bpy.ops.object.join()

        for obj in parentobj: #do for all meshes, but we have one since the meshes were joined it will probably run once
            if obj.type == 'MESH': #we know parent obj is a mesh this is just for solidarity.
                #deselect all objects and select our obj
                core.Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                core.Set_Mode(context, "EDIT")

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
                core.Set_Mode(context, "OBJECT")
        #select all arm bones and invert selection, then delete bones in edit mode.
        print("deleting leftover bones for arms and finding chest location.")
        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armcoll)


        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = arms_armature
        core.Set_Mode(context, "EDIT")
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
        core.Set_Mode(context, "OBJECT")


        print("moving arms armature to origin and applying transforms")
        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armcoll)

        #move arms armature to origin
        arms_armature.location = [(-1*chestloc[0]),(-1*chestloc[1]),(-1*chestloc[2])]

        for obj in parentobj:
            obj.select_set(True)
        arms_armature.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        core.update_viewport()


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
        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armcoll)

        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature
        body_armature.select_set(True)
        core.Set_Mode(context, "EDIT")
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

        parentobj, body_armature = core.Get_Meshes_And_Armature(context, refcoll)

        context.view_layer.objects.active = body_armature
        core.Set_Mode(context, "OBJECT")

        print("deleting old animations")
        core.Set_Mode(context, "OBJECT")
        animationnames = [j.name for j in bpy.data.actions]
        for animationname in animationnames:
            bpy.data.actions.remove(bpy.data.actions[animationname])

        dummy_anim = core.Make_And_Key_Animation(context, "dummy", body_armature)
        
        print("adding animation data thats a dummy to every armature because otherwise it causes errors with the exporter...")
        print("The animations that need to be exported should be assigned to armatures that have all the bones specified in the animation, then exported")
        for rig in context.view_layer.objects:
            if rig.type == "ARMATURE":
                rig.animation_data_create()
                rig.data.vs.action_selection = "CURRENT"
                rig.data.vs.implicit_zero_bone = False
                rig.animation_data.action = dummy_anim


        print("making animation for idle body")
        core.Make_And_Key_Animation(context, "idle", body_armature)


        refcoll = bpy.data.collections[sanitized_model_name+"_ref"]
        parentobj, body_armature = core.Get_Meshes_And_Armature(context, refcoll)
        body_armature.animation_data.action = None
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = body_armature

        print("Using importer with append enabled to yeet proportions fix anim onto our model")
        bpy.ops.import_scene.smd('EXEC_DEFAULT',files=[{'name': gender_file}], append = "APPEND",directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")+"/assets/garrysmod/")

        print("keying animation reference.")
        bpy.data.actions[gender_file.replace(".smd","")].name = "reference"
        body_armature.animation_data.action = bpy.data.actions["reference"]
        for barney_bone_name in barney_pose_bone_names:
            bone = body_armature.pose.bones.get(barney_bone_name)
            bone.rotation_mode = "XYZ"
            bone.keyframe_insert(data_path="rotation_euler", frame=1)
            bone.keyframe_insert(data_path="location", frame=1)
        core.Set_Mode(context, "OBJECT")

        print("making animation for idle arms")
        armscoll = bpy.data.collections[sanitized_model_name+"_arms"]
        parentobj, arms_armature = core.Get_Meshes_And_Armature(context, armscoll)
        idle_arms_anim = core.Make_And_Key_Animation(context, "idle_arms", arms_armature)
        arms_armature.animation_data.action = idle_arms_anim

        print("making copy of reference armature to export idle")
        parentobj, idle_armature = core.Get_Meshes_And_Armature(context, refcoll)
        idle_collection = core.Copy_to_existing_collection(context, "idle_ref", objects_alternative_list = [idle_armature])
        bpy.context.selected_objects[0].animation_data.action = bpy.data.actions["idle"] 
        bpy.ops.object.select_all(action='DESELECT')

        print("making copy of reference armature to export proportions reference animation")
        parentobj, body_armature = core.Get_Meshes_And_Armature(context, refcoll)
        reference_collection = core.Copy_to_existing_collection(context, "reference_ref", objects_alternative_list = [body_armature])
        reference_armature = bpy.context.selected_objects[0]
        reference_armature.animation_data.action = bpy.data.actions["reference"] 
        bpy.ops.object.select_all(action='DESELECT')

        core.update_viewport()

        print("setting export settings")
        bpy.context.scene.vs.subdir = "anims"
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        time.sleep(1)
        bpy.context.scene.vs.action_selection = "CURRENT"

        print("making body groups, you're almost to exporting!")
        refcoll = bpy.data.collections[sanitized_model_name+"_ref"]
        body_armature = None
        for obj in refcoll.objects:
            if obj.type == "ARMATURE":
                body_armature = obj
                break


        new_body_groups = ""
        body_group_coll = None
        for obj in refcoll.objects[:]:
            if obj.type == "MESH":
                if core.has_shapekeys(obj):
                    print("mesh has shapekeys, giving model shapekey data for model option")
                    shapekey_collection = core.Move_to_New_Or_Existing_Collection(context, obj.name+"_ref", objects_alternative_list = [obj])
                    

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
                    body_group_coll = core.Move_to_New_Or_Existing_Collection(context, obj.name+"_ref", objects_alternative_list = [obj])
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

        core.update_viewport()

        print("\n\n\n====EXPORTING EVERYTHING====\n\n\n")
        body_mesh = None
        for obj in context.view_layer.objects:
            if obj.type == "MESH":
                body_mesh = obj
                core.Set_Mode(context, "OBJECT")
                bpy.ops.object.select_all(action='SELECT')
                context.view_layer.objects.active = body_mesh
                core.Set_Mode(context, "EDIT")
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                core.Set_Mode(context, "OBJECT")
        
        bpy.ops.export_scene.smd(export_scene = True, collection=context.view_layer.layer_collection.collection.children[0].name)

        core.update_viewport()
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
        #bpy.ops.smd.compile_qc(filepath=) <- I wish I could use this but I had to write below since this method is broken - @989onan
        studiomdl = subprocess.Popen([steam_librarypath+"/bin/studiomdl.exe", "-nop4", "-game", steam_librarypath+"/garrysmod", bpy.path.abspath(bpy.context.scene.vs.qc_path)])
        studiomdl.communicate()
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
        core.Set_Mode(context, "OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        try:
            core.Set_Mode(context, "EDIT")
            obj = armature
            editbone1 = armature.data.edit_bones["ValveBiped.Bip01_L_UpperArm"]
            editbone2 = armature.data.edit_bones["ValveBiped.Bip01_L_Forearm"]
            loc1 = [editbone1.matrix[0][3],editbone1.matrix[1][3],editbone1.matrix[2][3]]
            loc2 = [editbone2.matrix[0][3],editbone2.matrix[1][3],editbone2.matrix[2][3]]
            core.Set_Mode(context, "OBJECT")
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
        studiomdl = subprocess.Popen([steam_librarypath+"/bin/studiomdl.exe", "-nop4", "-game", steam_librarypath+"/garrysmod", bpy.path.abspath(bpy.context.scene.vs.qc_path)])
        studiomdl.communicate()

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


        print("Cleaning up")

        bpy.ops.scene.delete()
        bpy.ops.outliner.orphans_purge()


        print("======================FINISHED GMOD PROCESS======================")
        print("Wow that took a long time...")
        return {'FINISHED'}