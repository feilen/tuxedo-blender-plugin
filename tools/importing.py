# GPL Licence
import bpy
from bpy_types import Operator
from bpy_extras.io_utils import ImportHelper
import os
import pathlib
import core

from .translate import t

from ..class_register import wrapper_registry

from ..globals import imports, import_types


#Imports any model according to the ..globals imports variable. This uses import_types to import each model type, allowing users to import any model they want.
@wrapper_registry
class Tuxedo_OT_ImportAnyModel(Operator, ImportHelper):
    bl_idname = 'tuxedo.import_any_model'
    bl_label = t('Tools.import_any_model.label')
    bl_description = t('Tools.import_any_model.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    
    
    filter_glob: bpy.props.StringProperty(default = imports, options={'HIDDEN','SKIP_SAVE'})
    directory: bpy.props.StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    
    #since I wrote this myself, a bit more efficent than cats. mostly - @989onan
    def execute(self, context):
        #group our files so our importers can import them together. in the case of OBJ+MTL and others that need grouped files, this is extremely important.
        file_grouping_dict = {}


        #check if we are importing multiple files
        is_multi = False
        try:
            for file in self.files:
                pass
            is_multi = True
        except Exception as e:
            is_multi = False
            print(e)

        #put the files together into lists of same importers
            
        if(is_multi):
            for file in self.files:
                fullpath = os.path.join(self.directory,os.path.basename(file.name))
                name = pathlib.Path(fullpath).suffix.replace(".","")
                #this makes sure our imports that should be grouped stay together.
                #basically the method checks for if the first value has a lambda with the same bytecode as another lambda, then it will use that value's key (ex:"obj"<->"mtl" or "fbx"), keeping same importers together
                try:
                    name2 = next(key for key,value in import_types.items() if value.__code__.co_code == file_grouping_dict[name].__code__.co_code)
                    print(name +" is the same importer as "+name2+", grouping.")
                    name = name2
                except Exception as e:
                    print("error when trying to find a value of the same value in the kinds of importers. May just be an import type that's a singlet:")
                    print(e)
                if name not in file_grouping_dict: file_grouping_dict[name] = []
                import_types[name]
                
                file_grouping_dict[name].append(file)
        else:
            fullpath = os.path.join(os.path.dirname(self.filepath),os.path.basename(self.filepath))
            name = pathlib.Path(fullpath).suffix.replace(".","")
            if name not in file_grouping_dict: file_grouping_dict[name] = []
            file_grouping_dict[name].append(None) #Since the "files" argument is optional, this will cause the importer to import the files as if this argument was never passed
            #therefore, above should not ever be an issue, unless the importer is just severely messed up.
        
        #import the files together to make sure things like obj import together. This is important
        for file_group_name,files in file_grouping_dict.items():
            try:
                if(self.directory):
                    import_types[file_group_name](self.directory,files,self.filepath)
                else:
                    import_types[file_group_name]("",files,self.filepath) #give an empty directory, works just fine for 90%
            except AttributeError as e:
                print("Warning, you may not have the required importer!")
                
                core.open_web_after_delay_multi_threaded(delay=12, url=t('Importing.importer_search_term').format("extension",file_group_name))

                self.report({'ERROR'},t('Importing.need_importer').format("extension", file_group_name))

                print("importer error was:")
                print(e)
                
        


        return {'FINISHED'}



#stolen from cats. Oh wait I made this code riiiiiiight - @989onan
class ImportMMDAnimation(bpy.types.Operator,ImportHelper):
    bl_idname = 'tuxedo.import_mmd_animation'
    bl_label = t('Importer.mmd_anim_importer.label')
    bl_description = t('Importer.mmd_anim_importer.desc')
    bl_options = {'INTERNAL', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.vmd",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        if core.get_armature() is None:
            return False
        return True

    def execute(self, context):

        # Make sure that the first layer is visible
        if hasattr(context.scene, 'layers'):
            context.scene.layers[0] = True

        filename, extension = os.path.splitext(self.filepath)

        if(extension == ".vmd"):

            #A dictionary to change the current model to MMD importer compatable temporarily
            bonedict = {
                "Chest":"UpperBody",
                "Neck":"Neck",
                "Head":"Head",
                "Hips":"Center",
                "Spine":"LowerBody",

                "Right wrist":"Wrist_R",
                "Right elbow":"Elbow_R",
                "Right arm":"Arm_R",
                "Right shoulder":"Shoulder_R",
                "Right leg":"Leg_R",
                "Right knee":"Knee_R",
                "Right ankle":"Ankle_R",
                "Right toe":"Toe_R",


                "Left wrist":"Wrist_L",
                "Left elbow":"Elbow_L",
                "Left arm":"Arm_L",
                "Left shoulder":"Shoulder_L",
                "Left leg":"Leg_L",
                "Left knee":"Knee_L",
                "Left ankle":"Ankle_L",
                "Left toe":"Toe_L"

            }

            armature = core.get_armature()
            new_armature = armature.copy()
            bpy.context.collection.objects.link(new_armature)
            new_armature.data = armature.data.copy()
            new_armature.name = "Cats MMD Rig Proxy"
            new_armature.animation_data_clear()

            core.unselect_all()
            core.Set_Mode('OBJECT')
            core.unselect_all()
            core.set_active(new_armature)
            
            for bone in new_armature.data.bones:
                if bone.name in bonedict:
                    bone.name = bonedict[bone.name]
            try:
                bpy.ops.mmd_tools.import_vmd(filepath=self.filepath,bone_mapper='RENAMED_BONES',use_underscore=True, dictionary='INTERNAL')
            except AttributeError as e:
                core.open_web_after_delay_multi_threaded(delay=12, url=t('Importing.importer_search_term').format("extension",file_group_name))
                self.report({'ERROR'},t('Importing.need_importer').format("extension", "MMD"))
                print("importer error was:")
                print(e)
                return {'CANCELLED'}
                

            #create animation for original if there isn't one.
            if armature.animation_data == None :
                armature.animation_data_create()
            if armature.animation_data.action == None:
                armature.animation_data.action = bpy.data.actions.new("MMD Animation")


            #create animation for new if there isn't one.
            if new_armature.animation_data == None :
                new_armature.animation_data_create()
            if new_armature.animation_data.action == None:
                new_armature.animation_data.action = bpy.data.actions.new("EMPTY_SOURCE")

            active_obj = new_armature
            ad = armature.animation_data

            #iterate through bones and translate them back, therefore blender API will change the animation to be correct.
            reverse_bonedict = {v: k for k, v in bonedict.items()}
            for bone in new_armature.data.bones:
                if bone.name in reverse_bonedict:
                    bone.name = reverse_bonedict[bone.name] #reverse name of bone from value in dictionary back to a key to change the animation.

            #assign animation back to original rig.
            armature.animation_data.action = new_armature.animation_data.action

            #make sure our new armature is selected
            core.unselect_all()
            core.Set_Mode('OBJECT')
            core.unselect_all()
            core.set_active(new_armature)

            #delete active object which is armature.
            bpy.ops.object.delete(use_global=True, confirm=False)
        
        return {'FINISHED'}