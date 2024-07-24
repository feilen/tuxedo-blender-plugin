# GPL Licence
import json
import os
import typing
import bpy


# Thanks to https://www.thegrove3d.com/learn/how-to-translate-a-blender-addon/ for the idea
# Thanks to Resonite by Yellow Dog Man Studios for the idea of translating based on Jsons! (found ideas inside of steam distributable)

""" translation_types: dict[str, list[typing.Callable[[Context], bpy.types.ID]]] = {
    'BONES': [(lambda context: context.object.pose.bones)],
    'OBJECT': [(lambda context: bpy.data.objects)],
    'SHAPEKEYS': [(lambda context: context.object.data.shape_keys.key_blocks)],
    'MATERIALS': [(lambda context: context.object.material_slots)],
    'ALL': [(lambda context: bpy.data.objects), (lambda context: context.object.pose.bones), (lambda context: context.object.data.shape_keys.key_blocks), (lambda context: context.object.material_slots)],
}

def translation_enum(self, context: bpy.types.Context):
    enums = []
    for i,k in translation_types.items():
        try:
            if len(k[0](context)) > 0:
                if hasattr(k[0](context)[0], 'name'):
                    enums.append((i,t('Translations.translation_group.label').format(tgroup=i),t('Translations.translation_group.desc').format(tgroup=i)))
                else:
                    raise AttributeError(str(k[0](context)[0])+' has no name attribute!')
            else:
                raise AttributeError('bpy collection has no items!')
        except AttributeError as e:
            pass

    return enums """



translation_dictionary: dict[str, str] = dict()

language_minor = "en"
if "_" in bpy.app.translations.locale:
    language_minor = bpy.app.translations.locale.split("_")[0]
else:
    language_minor = bpy.app.translations.locale


if not os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'translations', language_minor+".json"))):
    language_minor = "en"

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'translations', language_minor+".json")), 'r') as file:

    translation_dictionary = json.load(fp=file)["messages"]

def t(str_key):
    if str_key not in translation_dictionary:
        print("Warning: couldn't find translation for \"" + str_key + "\"")
        return str_key
    else:
        return translation_dictionary[str_key]

""" def translate_mmd(translate_enum: str, context: bpy.types.Context):
    #thank god for typing because this may work the first time because of such
    if globals.mmd_tools_exist:
        from mmd_tools import translations
        for group in translation_types[translate_enum]:
            try:
                item = group(context)
                item.name = translations.translateFromJp(item.name)
            except:
                pass
        return True
    else:
        return False """



