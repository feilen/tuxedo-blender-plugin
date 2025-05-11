from bpy.types import Scene, PropertyGroup, Object
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, CollectionProperty, StringProperty, FloatVectorProperty
from bpy.utils import register_class

from .tools import core
from .tools.tools import SRanipal_Labels

from .tools.translate import t
from .ui import tab_enums

#this is basically a constant, set at launch. There is no reason to need to set this otherwise unless explictly giving only the user the option to do so.
#this is set via the __init__ file and reads the steam libraries via registry keys at launch, so it will always
#be able to find garry's mod. If it can't, then the game is pirated, so screw them anyway.
gmod_path = {"path":""}

def get_steam_library(self):
    return gmod_path["path"]

#used by __init__ only. Don't touch for any other purpose.
def set_steam_library(arg):
    gmod_path["path"] = arg


class BakePlatformPropertyGroup(PropertyGroup):
        name: StringProperty(name='name', default=t('BakePanel.new_plat'))
        use_decimation: BoolProperty(
            name=t('Scene.bake_use_decimation.label'),
            description=t('Scene.bake_use_decimation.desc'),
            default=True
        )
        max_tris: IntProperty(
            name=t('Scene.tuxedo_max_tris.label'),
            description=t('Scene.tuxedo_max_tris.desc'),
            default=7500,
            min=1,
            max=70000
        )
        use_lods: BoolProperty(
            name=t("Bake.generate_lods.label"),
            description=t("Bake.generate_lods.desc"),
            default=False
        )
        lods: FloatVectorProperty(
            name=t("Bake.lods.label"),
            description=t('Bake.lods.desc'),
            #min=0.0,
            #max=1.0
        )
        use_physmodel: BoolProperty(
            name=t("Bake.generate_physics_model.label"),
            description=t("Bake.generate_physics_model.desc"),
            default=False
        )
        physmodel_lod: FloatProperty(
            name=t("Bake.physmodel_percent.label"),
            default=0.1,
            min=0.0,
            max=1.0
        )
        remove_doubles: BoolProperty(
            name=t('Scene.decimation_remove_doubles.label'),
            description=t('Scene.decimation_remove_doubles.desc'),
            default=True
        )
        preserve_seams: BoolProperty(
            name=t('Scene.bake_preserve_seams.label'),
            description=t('Scene.bake_preserve_seams.desc'),
            default=False
        )
        merge_twistbones: BoolProperty(
            name=t("Bake.merge_twist_bones.label"),
            description=t("Bake.merge_twist_bones.desc"),
            default=False
        )
        metallic_alpha_pack: EnumProperty(
            name=t('Scene.bake_metallic_alpha_pack.label'),
            description=t('Scene.bake_metallic_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_alpha_pack.none.label"), t("Scene.bake_alpha_pack.none.desc")),
                ("SMOOTHNESS", t("Scene.bake_alpha_pack.smoothness.label"), t("Scene.bake_alpha_pack.smoothness.desc"))
            ],
            default="NONE"
        )
        metallic_pack_ao: BoolProperty(
            name=t("Bake.pack_ao_to_metallic_green.label"),
            description=t("Bake.pack_ao_to_metallic_green.desc"),
            default=True
        )
        diffuse_vertex_colors: BoolProperty(
            name=t("Bake.bake_to_vertex_colors.label"),
            description=t("Bake.bake_to_vertex_colors.desc"),
            default=False
        )
        diffuse_alpha_pack: EnumProperty(
            name=t('Scene.bake_diffuse_alpha_pack.label'),
            description=t('Scene.bake_diffuse_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_alpha_pack.none.label"), t("Scene.bake_alpha_pack.none.desc")),
                ("TRANSPARENCY", t("Scene.bake_alpha_pack.transparency.label"), t("Scene.bake_alpha_pack.transparency.desc")),
                ("SMOOTHNESS", t("Scene.bake_alpha_pack.smoothness.label"), t("Scene.bake_alpha_pack.smoothness.desc")),
                ("EMITMASK", t("Scene.bake_alpha_pack.emit.label"), t("Scene.bake_alpha_pack.emit.label"))
            ],
            default="NONE"
        )
        normal_alpha_pack: EnumProperty(
            name=t("Bake.normal_alpha_pack.label"),
            description=t('Bake.normal_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_alpha_pack.none.label"), t("Scene.bake_alpha_pack.none.desc")),
                ("SPECULAR", t("Scene.bake_alpha_pack.specular.label"), t("Scene.bake_alpha_pack.normal.specular.desc")),
                ("SMOOTHNESS", t("Scene.bake_alpha_pack.smoothness.label"), t("Scene.bake_alpha_pack.smoothness.desc")),
            ],
            default="NONE"
        )
        normal_invert_g: BoolProperty(
            name=t("Bake.invert_green_channel.label"),
            description=t("Bake.invert_green_channel.desc"),
            default=False
        )
        diffuse_premultiply_ao: BoolProperty(
            name=t("Bake.premultiply_diffuse_w_ao.label"),
            description=t('Scene.bake_pass_questdiffuse.desc'),
            default=False
        )
        diffuse_premultiply_opacity: FloatProperty(
            name=t('Scene.bake_questdiffuse_opacity.label'),
            description=t('Scene.bake_questdiffuse_opacity.desc'),
            default=1.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            subtype='FACTOR'
        )
        smoothness_premultiply_ao: BoolProperty(
            name=t("Bake.premultiply_smoothness_w_ao.label"),
            description=t("Bake.premultiply_smoothness_w_ao.desc"),
            default=False
        )
        smoothness_premultiply_opacity: FloatProperty(
            name=t('Scene.bake_questdiffuse_opacity.label'),
            description=t('Scene.bake_questdiffuse_opacity.desc'),
            default=1.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            subtype='FACTOR'
        )
        translate_bone_names: EnumProperty(
            name=t("Bake.translate_bone_names.label"),
            description=t("Bake.translate_bone_names.desc"),
            items=[
                ("NONE", "None", "Don't translate any bones"),
                ("VALVE", "Valve", "Translate to Valve conventions when exporting, for use with Source Engine"),
                ("SECONDLIFE", "Second Life", "Translate to Second Life conventions when exporting, for use with Second Life")
            ],
            default="NONE"
        )
        export_format: EnumProperty(
            name=t('Bake.export_format.label'),
            description=t('Bake.export_format.desc'),
            items=[
                ("FBX", "FBX", "FBX export format, for use with Unity"),
                ("DAE", "DAE", "Collada DAE, for use with Second Life and older engines"),
                ("GMOD", "GMOD", "Exports to gmod. Requires TGA image export enabled as well to work")
            ]
        )
        image_export_format: EnumProperty(
            name=t('Bake.image_export_format.label'),
            description=t('Bake.image_export_format.desc'),
            items=[
                ("TGA", ".tga", "targa export format, for use with Gmod"),
                ("PNG", ".png", "png format, for use with most platforms.")
            ]
        )
        specular_setup: BoolProperty(
            name=t('Bake.specular_setup.label'),
            description=t("Bake.specular_setup.desc"),
            default=False
        )
        specular_alpha_pack: EnumProperty(
            name=t("Bake.specular_alpha_channel.label"),
            description=t("Bake.specular_alpha_channel.desc"),
            items=[
                ("NONE", t("Scene.bake_alpha_pack.none.label"), t("Scene.bake_alpha_pack.none.desc")),
                ("SMOOTHNESS", t("Scene.bake_alpha_pack.smoothness.label"), t("Scene.bake_alpha_pack_specular.smoothness.desc"))
            ],
            default="NONE"
        )
        phong_setup: BoolProperty(
            name=t('Bake.phong_setup_source.label'),
            description=t("Bake.phong_setup_source.desc"),
            default=False
        )
        diffuse_emit_overlay: BoolProperty(
            name=t('Bake.diffuse_emission_overlay.label'),
            description=t('Bake.diffuse_emission_overlay.desc'),
            default=False
        )

        specular_smoothness_overlay: BoolProperty(
            name=t('Bake.specular_smoothness_overlay.label'),
            description=t('Bake.specular_smoothness_overlay.desc'),
            default=False
        )
        gmod_model_name: StringProperty(name=t('Gmod.gmod_model_name.label'), description=t('Gmod.gmod_model_name.desc'), default="")
        gmod_male: BoolProperty(name=t('Gmod.gmod_male.label'), default=True)
        prop_bone_handling: EnumProperty(
            name=t('BakePanel.prop_handling.label'),
            description=t('BakePanel.prop_handling.desc'),
            items=[
                ("NONE", t('BakePanel.prop_handling.none.label'), t('BakePanel.prop_handling.none.desc')),
                ("GENERATE", t('BakePanel.prop_handling.generate.label'), t('BakePanel.prop_handling.generate.desc')),
                ("REMOVE", t('BakePanel.prop_handling.remove.label'), t('BakePanel.prop_handling.remove.desc')),
            ],
            default="GENERATE"
        )
        copy_only_handling: EnumProperty(
            name="Copy Only objects",
            description="What to do with objects marked as Copy Only",
            items=[
                ("COPY", "Copy", "Copy and export, but do not bake in"),
                ("REMOVE", "Remove", "Remove completely, for e.g. eye shells"),
            ],
            default="COPY"
        )


def register_properties():
    # Bake
    Scene.bake_use_draft_quality = BoolProperty(
        name='Draft Quality',
        description=t('Scene.draft_quality_desc'),
        default=False
    )

    Scene.bake_animation_weighting = BoolProperty(
        name=t('Scene.decimation_animation_weighting.label'),
        description=t('Scene.decimation_animation_weighting.desc'),
        default=True
    )

    Scene.bake_animation_weighting_factor = FloatProperty(
        name=t('Scene.decimation_animation_weighting_factor.label'),
        description=t('Scene.decimation_animation_weighting_factor.desc'),
        default=0.25,
        min=0,
        max=1,
        step=0.05,
        precision=2,
        subtype='FACTOR'
    )

    Scene.bake_animation_weighting_include_shapekeys = BoolProperty(
        name=t('Tools.anim_weight_incl_shapekeys.name'),
        description=t('Tools.anim_weight_incl_shapekeys.desc'),
        default=False
    )
    
    
    register_class(BakePlatformPropertyGroup)

    Scene.bake_platforms = CollectionProperty(
        type=BakePlatformPropertyGroup
    )
    Scene.bake_platform_index = IntProperty(default=0)
    

    Scene.bake_cleanup_shapekeys = BoolProperty(
        name=t("Bake.cleanup_shapekeys.label"),
        description=t("Bake.cleanup_shapekeys.label"),
        default=True
    )
    
    
    Scene.section_enum = EnumProperty(
        name="",
        description="",
        default=0,
        items=tab_enums
    )
    
    Scene.delete_old_bones_merging = BoolProperty(name = t('Tools.delete_old_bones_merging.label'), description=t('Tools.delete_old_bones_merging.desc'), default=False)
    
    
    #Gmod visiblity for compiling garry's mod model body groups
    Object.gmod_shown_by_default = BoolProperty(name = t('GmodPanel.gmod_visibility.shown_by_default.label'),  description=t('GmodPanel.gmod_visibility.shown_by_default.desc'), default=True)
    Object.gmod_is_toggleable = BoolProperty(name = t('GmodPanel.gmod_visibility.is_toggleable.label'), description=t('GmodPanel.gmod_visibility.is_toggleable.desc'), default=False)
    Scene.gmod_toggle_list_index = IntProperty(default=0, get=(lambda self : -1), set=(lambda self,context : None))
    
    class MaterialListGrouper(PropertyGroup):
        name: StringProperty(name='', default="Null Material")
        group: IntProperty(
            name=t('BakePanel.material_grouping.label'),
            description='',
            default=0,
            min=0,
            max=30
        )
    register_class(MaterialListGrouper)
    
    
    
    
    Scene.bake_material_groups = CollectionProperty(
        type=MaterialListGrouper
    )
    Scene.bake_material_groups_index = IntProperty(default=0)
        
    Scene.bake_resolution = IntProperty(
        name=t('Scene.bake_resolution.label'),
        description=t('Scene.bake_resolution.desc'),
        default=2048,
        min=256,
        max=4096
    )

    Scene.bake_generate_uvmap = BoolProperty(
        name=t('Scene.bake_generate_uvmap.label'),
        description=t('Scene.bake_generate_uvmap.desc'),
        default=True
    )

    Scene.bake_uv_overlap_correction = EnumProperty(
        name=t('Scene.bake_uv_overlap_correction.label'),
        description=t('Scene.bake_uv_overlap_correction.desc'),
        items=[
            ("NONE", t("Scene.bake_uv_overlap_correction.none.label"), t("Scene.bake_uv_overlap_correction.none.desc")),
            ("UNMIRROR", t("Scene.bake_uv_overlap_correction.unmirror.label"), t("Scene.bake_uv_overlap_correction.unmirror.desc")),
            ("REPROJECT", t("Scene.bake_uv_overlap_correction.reproject.label"), t("Scene.bake_uv_overlap_correction.reproject.desc")),
            ("MANUAL", t('BakePanel.manual.label'), t('BakePanel.manual.desc')),
            ("MANUALNOPACK", t('BakePanel.manual_no_pack.label'), t('BakePanel.manual_no_pack.desc'))
        ],
        default="UNMIRROR"
    )

    Scene.uvp_lock_islands = BoolProperty(
        name=t("Bake.keep_overlapping_islands_uvp.label"),
        description=t("Bake.keep_overlapping_islands_uvp.desc"),
        default=False
    )

    Scene.bake_device = EnumProperty(
        name=t('Bake.bake_device.label'),
        description=t('Bake.bake_device.desc'),
        default='GPU',
        items=[
            ('CPU', 'CPU', 'Perform bakes on CPU (Safe)'),
            ('GPU', 'GPU', 'Perform bakes on GPU (Fast)')
        ]
    )

    Scene.bake_prioritize_face = BoolProperty(
        name=t('Scene.bake_prioritize_face.label'),
        description=t('Scene.bake_prioritize_face.desc'),
        default=True
    )

    Scene.bake_face_scale = FloatProperty(
        name=t('Scene.bake_face_scale.label'),
        description=t('Scene.bake_face_scale.desc'),
        default=3.0,
        soft_min=0.5,
        soft_max=4.0,
        step=0.25,
        precision=2,
        subtype='FACTOR'
    )

    Scene.bake_sharpen = BoolProperty(
        name=t("Bake.sharpen_bakes.label"),
        description=t("Bake.sharpen_bakes.desc"),
        default=True
    )

    Scene.bake_denoise = BoolProperty(
        name=t("Bake.denoise_renders.label"),
        description=t("Bake.denoise_renders.desc"),
        default=True
    )

    Scene.bake_illuminate_eyes = BoolProperty(
        name=t('Scene.bake_illuminate_eyes.label'),
        description=t('Scene.bake_illuminate_eyes.desc'),
        default=True
    )

    Scene.bake_pass_smoothness = BoolProperty(
        name=t('Scene.bake_pass_smoothness.label'),
        description=t('Scene.bake_pass_smoothness.desc'),
        default=True
    )

    Scene.bake_pass_diffuse = BoolProperty(
        name=t('Scene.bake_pass_diffuse.label'),
        description=t('Scene.bake_pass_diffuse.desc'),
        default=True
    )

    Scene.bake_pass_normal = BoolProperty(
        name=t('Scene.bake_pass_normal.label'),
        description=t('Scene.bake_pass_normal.desc'),
        default=True
    )

    Scene.bake_pass_displacement = BoolProperty(
        name=t('Scene.bake_pass_displacement.label'),
        description=t('Scene.bake_pass_displacement.desc'),
        default=True
    )

    Scene.bake_pass_detail = BoolProperty(
        name="Detail (Experimental)",
        description="Bake a detail map for use with the detail shader. See documentation for more info.",
        default=False
    )

    Scene.bake_apply_keys = BoolProperty(
        name=t("apply_current_shapekey_mix"),
        description=t("Bake.apply_current_shapekeys.desc"),
        default=False
    )

    Scene.bake_ignore_hidden = BoolProperty(
        name=t("Bake.ignore_hidden_objects.label"),
        description=t("Bake.ignore_hidden_objects.desc"),
        default=True
    )

    Scene.bake_pass_ao = BoolProperty(
        name=t('Scene.bake_pass_ao.label'),
        description=t('Scene.bake_pass_ao.desc'),
        default=False
    )

    Scene.bake_pass_emit = BoolProperty(
        name=t('Scene.bake_pass_emit.label'),
        description=t('Scene.bake_pass_emit.desc'),
        default=False
    )

    Scene.bake_emit_indirect = BoolProperty(
        name=t("Bake.bake_projected_light.label"),
        description=t("Bake.bake_projected_light.desc"),
        default=False
    )

    Scene.bake_emit_exclude_eyes = BoolProperty(
        name=t("Bake.exclude_eyes.label"),
        description=t("Bake.exclude_eyes.desc"),
        default=True
    )

    Scene.bake_pass_alpha = BoolProperty(
        name=t('Scene.bake_pass_alpha.label'),
        description=t('Scene.bake_pass_alpha.desc'),
        default=False
    )

    Scene.bake_pass_metallic = BoolProperty(
        name=t('Scene.bake_pass_metallic.label'),
        description=t('Scene.bake_pass_metallic.desc'),
        default=False
    )

    Scene.bake_optimize_solid_materials = BoolProperty(
        name=t("Bake.optimize_solid_materials.label"),
        description=t("Bake.optimize_solid_materials.desc"),
        default=True
    )

    Scene.bake_unwrap_angle = FloatProperty(
        name=t("Bake.unwrap_angle.label"),
        description=t("Bake.unwrap_angle.desc"),
        default=66.0,
        min=0.1,
        max=89.9,
        step=0.1,
        precision=1
    )

    Scene.bake_steam_library = StringProperty(
        name='Steam Library', 
        default="C:\\Program Files (x86)\\Steam\\",
        get=get_steam_library,
        set = lambda self,arg: print("steam library is set on startup!!")
    )

    Scene.bake_diffuse_indirect = BoolProperty(
        name="Bake indirect light",
        description="Bake reflected light as if the only light source is ambient light",
        default=False
    )

    Scene.bake_diffuse_indirect_opacity = FloatProperty(
        name="Opacity",
        description="How bright the indirect light will be on the diffuse layer",
        default=0.5,
        min=0.0,
        max=1.0,
        step=0.05,
        precision=2,
        subtype='FACTOR'
    )

    Scene.generate_twistbones_upper = BoolProperty(
        name=t("Bake.generate_upperhalf.label"),
        description=t("Bake.generate_upperhalf.desc"),
        default=False
    )

    Scene.decimation_animation_weighting = BoolProperty(
        name=t('Scene.decimation_animation_weighting.label'),
        description=t('Scene.decimation_animation_weighting.desc'),
        default=True
    )

    Scene.decimation_animation_weighting_factor = FloatProperty(
        name=t('Scene.decimation_animation_weighting_factor.label'),
        description=t('Scene.decimation_animation_weighting_factor.desc'),
        default=0.25,
        min=0,
        max=1,
        step=0.05,
        precision=2,
        subtype='FACTOR'
    )

    Scene.decimation_animation_weighting_include_shapekeys = BoolProperty(
        name="Include Shapekeys",
        description="Factor shapekeys into animation weighting. Disable if your model has large body shapekeys.",
        default=False
    )

    Scene.tuxedo_max_tris = IntProperty(
        name=t('Scene.tuxedo_max_tris.label'),
        description=t('Scene.tuxedo_max_tris.desc'),
        default=7500,
        min=1,
        max=70000
    )

    Scene.tuxedo_is_unittest = BoolProperty(
        default=False
    )

    Scene.decimation_remove_doubles = BoolProperty(
        name=t('Scene.decimation_remove_doubles.label'),
        description=t('Scene.decimation_remove_doubles.desc'),
        default=True
    )
    # Mesh Select
    Scene.ft_mesh = EnumProperty(name='Mesh', description='Mesh to apply FT shape keys', items=core.get_meshes)

    # Viseme select
    Scene.ft_aa = EnumProperty(name='aa/Jaw Down', description='This shapekey should ideally only move the mouth down.', items=core.get_shapekeys_ft)
    Scene.ft_ch = EnumProperty(name='ch/Cheese', description='This shapekey should ideally only move the lips to expose the teeth.', items=core.get_shapekeys_ft)
    Scene.ft_oh = EnumProperty(name='oh/Shock/aa/Jaw Down', description='This shapekey should move the bottom lips more than CH but not the top lips,  and may need to be created. Often AA works too.', items=core.get_shapekeys_ft)
    Scene.ft_blink = EnumProperty(name='blink', description='Select shapekey to use for FT', items=core.get_shapekeys_ft)
    Scene.ft_smile = EnumProperty(name='smile', description='Select shapekey to use for FT', items=core.get_shapekeys_ft)
    Scene.ft_frown = EnumProperty(name='frown', description='Select shapekey to use for FT', items=core.get_shapekeys_ft)

    # Shape Keys
    for i, ft_shape in enumerate(SRanipal_Labels):
        setattr(Scene, "ft_shapekey_" + str(i), EnumProperty(
            name='',
            description='Select shapekey to use for SRanipal',
            items=core.get_shapekeys_ft)
        )
    # Enable Shape Key Creation
    for i, ft_shape in enumerate(SRanipal_Labels):
        setattr(Scene, "ft_shapekey_enable_" + str(i), BoolProperty(
            name='',
            description='Enable SRanipal Shapekey Creation',
            default=True)
        )
    