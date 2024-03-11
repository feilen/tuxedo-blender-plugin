# GPL Licence
import bpy
from bpy_types import Operator
from bpy_extras.io_utils import ImportHelper
import os
import pathlib
from .core import open_web_after_delay_multi_threaded

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
                
                open_web_after_delay_multi_threaded(delay=12, url="https://search.brave.com/search?q=blender+"+file_group_name+"+importer+addon&source=web")

                self.report({'ERROR'},"You do not have the required importer for the \"."+file_group_name+"\" type! Opening web browser for importer search term...")

                print("importer error was:")
                print(e)
                
        


        return {'FINISHED'}

