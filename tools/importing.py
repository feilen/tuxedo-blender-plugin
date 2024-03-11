# GPL Licence
import bpy
from bpy_types import Operator
import io_scene_fbx
import io_scene_gltf2
import io_scene_3ds
from bpy_extras.io_utils import ImportHelper
import os

from .translate import t

from ..class_register import wrapper_registry

from ..globals import imports

@wrapper_registry
class Tuxedo_OT_ImportAnyModel(Operator, ImportHelper):
    bl_idname = 'tuxedo.import_any_model'
    bl_label = t('Tools.import_any_model.label')
    bl_description = t('Tools.import_any_model.desc')
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    files = bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    filter_glob: bpy.props.StringProperty(default = imports, options={'HIDDEN','SKIP_SAVE'})
    directory: bpy.props.StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})


    def execute(self, context):
        filepath = self.directory

        #if(os.)



