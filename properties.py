from bpy.types import Scene, PropertyGroup, Object, OperatorFileListElement
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, CollectionProperty, StringProperty, FloatVectorProperty
from bpy.utils import register_class

from .tools import core
from .tools.tools import SRanipal_Labels
from .globals import import_types

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
    
    class BakePlatformPropertyGroup(PropertyGroup):
        name: StringProperty(name='name', default=t('BakePanel.new_plat'))
        use_decimation: BoolProperty(
            name=t('Scene.bake_use_decimation.label'),
            description=t('Scene.bake_use_decimation.desc'),
            default=True
        )
        max_tris: IntProperty(
            name=t('Scene.max_tris.label'),
            description=t('Scene.max_tris.desc'),
            default=7500,
            min=1,
            max=70000
        )
        use_lods: BoolProperty(
            name=t("generate_lods"),
            description=t("generate_courser_decimation_levels_for_efficient_rendering"),
            default=False
        )
        lods: FloatVectorProperty(
            name=t("lods"),
            description=t('lod_generation_levels_as_a_percent_of_the_max_tris'),
            #min=0.0,
            #max=1.0
        )
        use_physmodel: BoolProperty(
            name=t("generate_physics_model"),
            description=t("generate_an_additional_lod_used_for_simplified_physics_interactions"),
            default=False
        )
        physmodel_lod: FloatProperty(
            name=t("physmodel_percent"),
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
            name=t("merge_twist_bones"),
            description=t("merge_any_bone_with_twist_in_the_name_useful_as_quest_does_not_support_constraints"),
            default=False
        )
        metallic_alpha_pack: EnumProperty(
            name=t('Scene.bake_metallic_alpha_pack.label'),
            description=t('Scene.bake_metallic_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_metallic_alpha_pack.none.label"), t("Scene.bake_metallic_alpha_pack.none.desc")),
                ("SMOOTHNESS", t("Scene.bake_metallic_alpha_pack.smoothness.label"), t("Scene.bake_metallic_alpha_pack.smoothness.desc"))
            ],
            default="NONE"
        )
        metallic_pack_ao: BoolProperty(
            name=t("pack_ao_to_metallic_green"),
            description=t("pack_ambient_occlusion_to_the_green_channel_saves_a_texture_as_unity_uses_g_for_ao_r_for_metallic"),
            default=True
        )
        diffuse_vertex_colors: BoolProperty(
            name=t("bake_to_vertex_colors"),
            description=t("rebake_to_vertex_colors_after_initial_bake_avoids_an_entire_extra_texture_if_your_colors_are_simple_enough_incorperates_ao"),
            default=False
        )
        diffuse_alpha_pack: EnumProperty(
            name=t('Scene.bake_diffuse_alpha_pack.label'),
            description=t('Scene.bake_diffuse_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_diffuse_alpha_pack.none.label"), t("Scene.bake_diffuse_alpha_pack.none.desc")),
                ("TRANSPARENCY", t("Scene.bake_diffuse_alpha_pack.transparency.label"), t("Scene.bake_diffuse_alpha_pack.transparency.desc")),
                ("SMOOTHNESS", t("Scene.bake_diffuse_alpha_pack.smoothness.label"), t("Scene.bake_diffuse_alpha_pack.smoothness.desc")),
                ("EMITMASK", "Emit Mask", "A single-color emission mask, for use with preapplied emission")
            ],
            default="NONE"
        )
        normal_alpha_pack: EnumProperty(
            name=t("normal_alpha_pack"),
            description=t('Scene.bake_diffuse_alpha_pack.desc'),
            items=[
                ("NONE", t("Scene.bake_diffuse_alpha_pack.none.label"), t("Scene.bake_diffuse_alpha_pack.none.desc")),
                ("SPECULAR", "Specular", t("Scene.bake_diffuse_alpha_pack.none.desc")),
                ("SMOOTHNESS", "Smoothness", t("Scene.bake_diffuse_alpha_pack.none.desc")),
            ],
            default="NONE"
        )
        normal_invert_g: BoolProperty(
            name=t("invert_green_channel"),
            description=t("source_engine_uses_an_inverse_green_channel_this_fixes_that_on_export"),
            default=False
        )
        diffuse_premultiply_ao: BoolProperty(
            name=t("premultiply_diffuse_w_ao"),
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
            name=t("premultiply_smoothness_w_ao"),
            description=t("while_not_technically_accurate_this_avoids_the_shine_effect_on_obscured_portions_of_your_model"),
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
            name=t("translate_bone_names"),
            description=t("target_another_bone_naming_standard_when_exporting_requires_standard_bone_names"),
            items=[
                ("NONE", "None", "Don't translate any bones"),
                ("VALVE", "Valve", "Translate to Valve conventions when exporting, for use with Source Engine"),
                ("SECONDLIFE", "Second Life", "Translate to Second Life conventions when exporting, for use with Second Life")
            ],
            default="NONE"
        )
        export_format: EnumProperty(
            name=t('export_format'),
            description=t('model_format_to_use_when_exporting'),
            items=[
                ("FBX", "FBX", "FBX export format, for use with Unity"),
                ("DAE", "DAE", "Collada DAE, for use with Second Life and older engines"),
                ("GMOD", "GMOD", "Exports to gmod. Requires TGA image export enabled as well to work")
            ]
        )
        image_export_format: EnumProperty(
            name=t('image_export_format'),
            description=t('image_type_to_use_when_exporting'),
            items=[
                ("TGA", ".tga", "targa export format, for use with Gmod"),
                ("PNG", ".png", "png format, for use with most platforms.")
            ]
        )
        specular_setup: BoolProperty(
            name=t('specular_setup'),
            description=t("convert_diffuse_and_metallic_to_premultiplied_diffuse_and_specular_compatible_with_older_engines"),
            default=False
        )
        specular_alpha_pack: EnumProperty(
            name=t("specular_alpha_channel"),
            description=t("what_to_pack_to_the_alpha_channel_of_specularity"),
            items=[
                ("NONE", t("Scene.bake_metallic_alpha_pack.none.label"), t("Scene.bake_metallic_alpha_pack.none.desc")),
                ("SMOOTHNESS", t("Scene.bake_metallic_alpha_pack.smoothness.label"), "Smoothness, for use with Second Life")
            ],
            default="NONE"
        )
        phong_setup: BoolProperty(
            name=t('phong_setup_source'),
            description=t("for_source_engine_only_provides_diffuse_lighting_reflections_for_nonmetallic_objects"),
            default=False
        )
        diffuse_emit_overlay: BoolProperty(
            name=t('diffuse_emission_overlay'),
            description=t('blends_emission_into_the_diffuse_map_for_engines_without_a_seperate_emission_map'),
            default=False
        )
        specular_smoothness_overlay: BoolProperty(
            name=t('specular_smoothness_overlay'),
            description=t('merges_smoothness_into_the_specular_map_for_engines_without_a_seperate_smoothness_map'),
            default=False
        )
        gmod_model_name: StringProperty(name='Gmod Model Name', default="")
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

    register_class(BakePlatformPropertyGroup)

    Scene.bake_platforms = CollectionProperty(
        type=BakePlatformPropertyGroup
    )
    Scene.bake_platform_index = IntProperty(default=0)
    

    Scene.bake_cleanup_shapekeys = BoolProperty(
        name=t("cleanup_shapekeys"),
        description=t("remove_backup_shapekeys_in_the_final_result_eg_key__reverted_or_blinkold"),
        default=True
    )
    
    
    Scene.section_enum = EnumProperty(
        name="",
        description="",
        items=tab_enums
    )
    
    
    
    #Gmod visiblity for compiling garry's mod model body groups
    Object.gmod_shown_by_default = BoolProperty(name = t('GmodPanel.gmod_visibility.shown_by_default'), default=True)
    Object.gmod_is_toggleable = BoolProperty(name = t('GmodPanel.gmod_visibility.is_toggleable'), default=False)
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
        name=t("keep_overlapping_islands_uvp"),
        description=t("experimental_try_to_keep_uvps_lock_overlapping_enabled"),
        default=False
    )

    Scene.bake_device = EnumProperty(
        name=t('bake_device'),
        description=t('device_to_bake_on_gpu_gives_a_significant_speedup_but_can_cause_issues_depending_on_your_graphics_drivers'),
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
        name=t("sharpen_bakes"),
        description=t("sharpen_resampled_images_after_baking_diffusesmoothnessmetallic_reccomended_as_any_sampling_will_cause_blur"),
        default=True
    )

    Scene.bake_denoise = BoolProperty(
        name=t("denoise_renders"),
        description=t("denoise_the_resulting_image_after_emitao_reccomended_as_this_will_reduce_the_grainy_quality_of_inexpensive_rendering"),
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
        description=t("when_selected_currently_active_shape_keys_will_be_applied_to_the_basis_this_is_extremely_beneficial_to_performance_if_your_avatar_is_intended_to_default_to_one_shapekey_mix_as_having_active_shapekeys_all_the_time_is_expensive_keys_ending_in_bake_are_always_applied_to_the_basis_and_removed_completely_regardless_of_this_option"),
        default=False
    )

    Scene.bake_ignore_hidden = BoolProperty(
        name=t("ignore_hidden_objects"),
        description=t("ignore_currently_hidden_objects_when_copying"),
        default=True
    )

    Scene.bake_show_advanced_general_options = BoolProperty(
        name=t("advanced_general_options"),
        description=t("will_show_extra_options_related_to_which_bake_passes_are_performed_and_how"),
        default=False
    )

    Scene.bake_show_advanced_platform_options = BoolProperty(
        name=t("advanced_platform_options"),
        description=t("will_show_extra_options_related_to_applicable_bones_and_texture_packing_setups"),
        default=False
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
        name=t("bake_projected_light"),
        description=t("bake_the_effect_of_emission_on_nearby_surfaces_results_in_much_more_realistic_lighting_effects_but_can_animate_less_well"),
        default=False
    )

    Scene.bake_emit_exclude_eyes = BoolProperty(
        name=t("exclude_eyes"),
        description=t("bakes_the_effect_of_any_eye_glow_onto_surrounding_objects_but_not_viceversa_improves_animation_when_eyes_are_moving_around"),
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
        name=t("optimize_solid_materials"),
        description=t("optimizes_solid_materials_by_making_a_small_area_for_them_ao_pass_will_nullify"),
        default=True
    )

    Scene.bake_unwrap_angle = FloatProperty(
        name=t("unwrap_angle"),
        description=t("the_angle_reproject_uses_when_unwrapping_larger_angles_yield_less_islands_but_more_stretching_and_smaller_does_opposite"),
        default=66.0,
        min=0.1,
        max=89.9,
        step=0.1,
        precision=1
    )

    Scene.bake_steam_library = StringProperty(
        name='Steam Library', 
        default="C:\\Program Files (x86)\\Steam\\",
        get=get_steam_library
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
        name=t("generate_upperhalf"),
        description=t("generate_the_twistbones_on_the_upper_half_of_the_bone_usually_used_for_upper_legs"),
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