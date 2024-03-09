import bpy
import typing

classes = []
ordered_classes = []

#Stolen from cats. I will not pretend or say I made this - @989onan
def wrapper_registry(class_obj):
    if hasattr(class_obj, 'bl_rna'):
        classes.append(class_obj)
    return class_obj
    

def order_classes():
    global ordered_classes
    deps_dict = {}
    classes_to_register = set(iter_classes_to_register())
    for class_obj in classes_to_register:
        deps_dict[class_obj] = set(iter_own_register_deps(class_obj, classes_to_register))

    # Put all the UI into the list first
    ordered_classes = []
    for class_obj in classes:
        if class_obj.__module__.startswith('ui.'):
            ordered_classes.append(class_obj)

    # Then put everything else sorted into the list
    for class_obj in toposort(deps_dict):
        if not class_obj.__module__.startswith('ui.'):
            ordered_classes.append(class_obj)


def iter_classes_to_register():
    for class_obj in classes:
        yield class_obj


def iter_own_register_deps(class_obj, own_classes):
    yield from (dep for dep in iter_register_deps(class_obj) if dep in own_classes)


def iter_register_deps(class_obj):
    for value in typing.get_type_hints(class_obj, {}, {}).values():
        dependency = get_dependency_from_annotation(value)
        if dependency is not None:
            yield dependency


def get_dependency_from_annotation(value):
    if isinstance(value, tuple) and len(value) == 2:
        if value[0] in (bpy.props.PointerProperty, bpy.props.CollectionProperty):
            return value[1]["type"]
    return None


# Find order to register to solve dependencies
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value : deps_dict[value] - sorted_values for value in unsorted}
    return sorted_list
