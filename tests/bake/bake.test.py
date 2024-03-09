# GPL Licence

import unittest
import sys
import bpy

# Lookup table of expected samples. Bear in mind that these are linear colorspace!
sampling_lookup = {
    'bake.AOtest.blend': {
        'SCRIPT_ao0.png': {
            # Blender 3.4 changed the packing ever so slightly in a way that affects AOtest
            # apparently fixed in 3.5?
            (15,145) if (3, 5, 0) > bpy.app.version >= (3, 4, 0) else (145,15): (0,0,0,255),
            (178,55): (255,255,255,255),
            (32,222): (255,255,255,255),
            #(178,200): (255,255,255,255),
            #(0,0): (255,255,255,255),
            (215,40): (255,255,255,255),
            (215,7): (255,255,255,255),
            (215,24): (255,255,255,255),
            (200,40): (255,255,255,255),
            (232,40): (255,255,255,255),
            (215,56): (255,255,255,255),
            (96,32): (255,255,255,255),
            (96,96): (255,255,255,255),
            (96,160): (255,255,255,255),
            (96,220): (255,255,255,255),
        }
    },
    'bake.eyetest.blend': {
        'SCRIPT_diffuse0.png': {
            # For some reason Blender 2.93 ends up with values off-by-one (but not alpha)
            #(64,64): (0,255,255,255),
            # (178,55): (255,0,255,255),
            # (32,222): (0,0,255,255),
            #(178,200): (5,255,0,255)
        }
    },
    'bake.bakematerialtest.blend': {
        'SCRIPT_diffuse0.png': {
            (0,0): (128,128,128,255),
            (215,40): (255,0,0,255),
            (215,7): (0,0,255,255),
            (215,24): (0,255,0,255),
            (200,40): (231,0,231,255),
            (232,40): (231,231,231,255),
            (215,56): (0,0,0,255),
            (96,32): (188,188,188,255),
            (96,96): (188,188,188,255),
            (96,160): (188,188,188,255),
            (96,220): (188,188,188,255),
        },
        'SCRIPT_emission0.png': {
            (0,0): (0,0,0,255),
            (215,48): (252,252,252,255),
            (215,63): (55,55,55,255),
        },
        'SCRIPT_metallic0.png': {
            (0,0): (0,0,0,255),
            (215,32): (215,215,215,255)
        },
        'SCRIPT_smoothness0.png': {
            (0,0): (0,0,0,255),
            (96,165): (128,128,128,255),
            (215,24): (122,122,122,255),
            (215,17): (234,234,234,255)
        },
        'SCRIPT_alpha0.png': {
            (0,0): (255,255,255,255),
            (216,0): (36,36,36,255)
        },
        'VRChat Desktop Excellent metallic0.png': {
            (215,17): (0,0,0,234),
            (96,220): (0,0,0,127),
            (216,0): (0,0,0,127),
            (215,32): (215,0,0,127),
            (96,32): (0,0,0,127),
            (96,96): (0,0,0,127),
            (96,160): (0,0,0,127),
            (215,24): (0,0,0,122),
            (232,40): (0,0,0,127),
            (200,40): (0,0,0,127),
            (215,56): (0,0,0,127),
            (215,7): (0,0,0,127),
            (0,0): (0,0,0,0),
            (215,48): (0,0,0,127),
            (215,63): (0,0,0,127),
            (215,40): (64,0,0,127),
        },
        'VRChat Desktop Excellent diffuse0.png': {
            (215,17): (0,255,0,255),
            (96,220): (188,188,188,255),
            (216,0): (0,0,255,36),
            (215,32): (255,0,0,255),
            (96,32): (188,188,188,255),
            (96,96): (188,188,188,255),
            (96,160): (188,188,188,255),
            (215,24): (0,255,0,255),
            (232,40): (231,231,231,255),
            (200,40): (231,0,231,255),
            (215,56): (0,0,0,255),
            (215,7): (0,0,255,180),
            (0,0): (128,128,128,255),
            (215,48): (0,0,0,255),
            (215,63): (0,0,0,255),
            (215,40): (255,0,0,255),
        },
        'VRChat Desktop Excellent normal0.png': {
            (215,17): (128,128,255,255),
            (96,220): (127,127,255,255),
            (98,32): (127,127,255,255),
            (96,96): (128,127,255,255),
            (96,160): (127,127,255,255),
            (215,24): (128,128,255,255),
            (232,40): (127,127,255,255),
            #(200,40): (191,64,218,255),
            (215,56): (128,127,255,255),
            (215,7): (128,128,255,255),
            (0,0): (128,128,255,255),
            (215,48): (128,127,255,255),
            (215,63): (128,127,255,255),
            (215,40): (128,127,255,255),
        },
        'VRChat Quest Excellent metallic0.png': {
            (215,17): (0,0,0,234),
            (96,220): (0,0,0,127),
            (216,0): (0,0,0,127),
            (215,32): (215,0,0,127),
            (96,32): (0,0,0,127),
            (96,96): (0,0,0,127),
            (96,160): (0,0,0,127),
            (215,24): (0,0,0,122),
            (232,40): (0,0,0,127),
            (200,40): (0,0,0,127),
            (215,56): (0,0,0,127),
            (215,7): (0,0,0,127),
            (0,0): (0,0,0,0),
            (215,48): (0,0,0,127),
            (215,63): (0,0,0,127),
            (215,40): (64,0,0,127),
        },
        'VRChat Quest Excellent alpha0.png': {
            (215,17): (255,255,255,255),
            (96,220): (255,255,255,255),
            (216,0): (36,36,36,255),
            (215,32): (255,255,255,255),
            (96,32): (255,255,255,255),
            (96,96): (255,255,255,255),
            (96,160): (255,255,255,255),
            (215,24): (255,255,255,255),
            (232,40): (255,255,255,255),
            (200,40): (255,255,255,255),
            (215,56): (255,255,255,255),
            (215,7): (180,180,180,255),
            (0,0): (255,255,255,255),
            (215,48): (255,255,255,255),
            (215,63): (255,255,255,255),
            (215,40): (255,255,255,255),
        },
        'VRChat Quest Excellent smoothness0.png': {
            (215,17): (234,234,234,255),
            (96,220): (127,127,127,255),
            (216,0): (127,127,127,255),
            (215,32): (127,127,127,255),
            (96,32): (127,127,127,255),
            (96,96): (127,127,127,255),
            (96,160): (127,127,127,255),
            (215,24): (122,122,122,255),
            (232,40): (127,127,127,255),
            (200,40): (127,127,127,255),
            (215,56): (127,127,127,255),
            (215,7): (127,127,127,255),
            (0,0): (0,0,0,255),
            (215,48): (127,127,127,255),
            (215,63): (127,127,127,255),
            (215,40): (127,127,127,255),
        },
        'VRChat Quest Excellent diffuse0.png': {
            (215,17): (0,255,0,255),
            (96,220): (188,188,188,255),
            (216,0): (0,0,255,255),
            (215,32): (255,0,0,255),
            (96,32): (188,188,188,255),
            (96,96): (188,188,188,255),
            (96,160): (188,188,188,255),
            (215,24): (0,255,0,255),
            (232,40): (231,231,231,255),
            (200,40): (231,0,231,255),
            (215,56): (0,0,0,255),
            (215,7): (0,0,255,255),
            (0,0): (128,128,128,255),
            (215,48): (0,0,0,255),
            (215,63): (0,0,0,255),
            (215,40): (255,0,0,255),
        },
        'VRChat Quest Excellent normal0.png': {
            (215,17): (128,128,255,255),
            (96,220): (127,127,255,255),
            (96,32): (128,128,255,255),
            (96,96): (128,127,255,255),
            (96,160): (127,127,255,255),
            (215,24): (128,128,255,255),
            (232,40): (127,127,255,255),
            #(200,40): (191,64,218,255),
            (215,56): (128,127,255,255),
            (215,7): (128,128,255,255),
            (0,0): (128,128,255,255),
            (215,48): (128,127,255,255),
            (215,63): (128,127,255,255),
            (215,40): (128,127,255,255),
        },
        'VRChat Quest Good metallic0.png': {
            (215,17): (0,0,0,234),
            (96,220): (0,0,0,127),
            (216,0): (0,0,0,127),
            (215,32): (215,0,0,127),
            (96,32): (0,0,0,127),
            (96,96): (0,0,0,127),
            (96,160): (0,0,0,127),
            (215,24): (0,0,0,122),
            (232,40): (0,0,0,127),
            (200,40): (0,0,0,127),
            (215,56): (0,0,0,127),
            (215,7): (0,0,0,127),
            (0,0): (0,0,0,0),
            (215,48): (0,0,0,127),
            (215,63): (0,0,0,127),
            (215,40): (64,0,0,127),
        },
        'VRChat Quest Good alpha0.png': {
            (215,17): (255,255,255,255),
            (96,220): (255,255,255,255),
            (216,0): (36,36,36,255),
            (215,32): (255,255,255,255),
            (96,32): (255,255,255,255),
            (96,96): (255,255,255,255),
            (96,160): (255,255,255,255),
            (215,24): (255,255,255,255),
            (232,40): (255,255,255,255),
            (200,40): (255,255,255,255),
            (215,56): (255,255,255,255),
            (215,7): (180,180,180,255),
            (0,0): (255,255,255,255),
            (215,48): (255,255,255,255),
            (215,63): (255,255,255,255),
            (215,40): (255,255,255,255),
        },
        'VRChat Quest Good smoothness0.png': {
            (215,17): (234,234,234,255),
            (96,220): (127,127,127,255),
            (216,0): (127,127,127,255),
            (215,32): (127,127,127,255),
            (96,32): (127,127,127,255),
            (96,96): (127,127,127,255),
            (96,160): (127,127,127,255),
            (215,24): (122,122,122,255),
            (232,40): (127,127,127,255),
            (200,40): (127,127,127,255),
            (215,56): (127,127,127,255),
            (215,7): (127,127,127,255),
            (0,0): (0,0,0,255),
            (215,48): (127,127,127,255),
            (215,63): (127,127,127,255),
            (215,40): (127,127,127,255),
        },
        'VRChat Quest Good diffuse0.png': {
            (215,17): (0,255,0,255),
            (96,220): (188,188,188,255),
            (216,0): (0,0,255,255),
            (215,32): (255,0,0,255),
            (96,32): (188,188,188,255),
            (96,96): (188,188,188,255),
            (96,160): (188,188,188,255),
            (215,24): (0,255,0,255),
            (232,40): (231,231,231,255),
            (200,40): (231,0,231,255),
            (215,56): (0,0,0,255),
            (215,7): (0,0,255,255),
            (0,0): (128,128,128,255),
            (215,48): (0,0,0,255),
            (215,63): (0,0,0,255),
            (215,40): (255,0,0,255),
        },
        'VRChat Quest Good normal0.png': {
            (215,17): (128,128,255,255),
            (96,220): (127,127,255,255),
            (96,32): (128,128,255,255),
            (96,96): (128,127,255,255),
            (96,160): (127,127,255,255),
            (215,24): (128,128,255,255),
            (232,40): (127,127,255,255),
            #(200,40): (191,64,218,255),
            (215,56): (128,127,255,255),
            (215,7): (128,128,255,255),
            (0,0): (128,128,255,255),
            (215,48): (128,127,255,255),
            (215,63): (128,127,255,255),
            (215,40): (128,127,255,255),
        },
        'Second Life metallic0.png': {
            (215,17): (0,0,0,255),
            (96,220): (0,0,0,255),
            (216,0): (0,0,0,255),
            (215,32): (215,0,0,255),
            (96,32): (0,0,0,255),
            (96,96): (0,0,0,255),
            (96,160): (0,0,0,255),
            (215,24): (0,0,0,255),
            (232,40): (0,0,0,255),
            (200,40): (0,0,0,255),
            (215,56): (0,0,0,255),
            (215,7): (0,0,0,255),
            (0,0): (0,0,0,255),
            (215,48): (0,0,0,255),
            (215,63): (0,0,0,255),
            (215,40): (64,0,0,255),
        },
        'Second Life alpha0.png': {
            (215,17): (255,255,255,255),
            (96,220): (255,255,255,255),
            (216,0): (36,36,36,255),
            (215,32): (255,255,255,255),
            (96,32): (255,255,255,255),
            (96,96): (255,255,255,255),
            (96,160): (255,255,255,255),
            (215,24): (255,255,255,255),
            (232,40): (255,255,255,255),
            (200,40): (255,255,255,255),
            (215,56): (255,255,255,255),
            (215,7): (180,180,180,255),
            (0,0): (255,255,255,255),
            (215,48): (255,255,255,255),
            (215,63): (255,255,255,255),
            (215,40): (255,255,255,255),
        },
        'Second Life smoothness0.png': {
            (215,17): (234,234,234,255),
            (96,220): (127,127,127,255),
            (216,0): (127,127,127,255),
            (215,32): (127,127,127,255),
            (96,32): (127,127,127,255),
            (96,96): (127,127,127,255),
            (96,160): (127,127,127,255),
            (215,24): (122,122,122,255),
            (232,40): (127,127,127,255),
            (200,40): (127,127,127,255),
            (215,56): (127,127,127,255),
            (215,7): (127,127,127,255),
            (0,0): (0,0,0,255),
            (215,48): (127,127,127,255),
            (215,63): (127,127,127,255),
            (215,40): (127,127,127,255),
        },
        'Second Life diffuse0.png': {
            (215,17): (0,255,0,0),
            (96,220): (188,188,188,0),
            (216,0): (0,0,255,0),
            (215,32): (40,0,0,0),
            (96,32): (188,188,188,0),
            (96,96): (188,188,188,0),
            (96,160): (188,188,188,0),
            (215,24): (0,255,0,0),
            (232,40): (231,231,231,0),
            (200,40): (231,0,231,0),
            (215,7): (0,0,255,0),
            (0,0): (128,128,128,0),
            (215,48): (252,252,252,252),
            (215,63): (55,55,55,55),
            (215,40): (191,0,0,0),
        },
        'Second Life normal0.png': {
            (215,17): (128,128,255,255),
            (96,220): (127,127,255,255),
            (96,32): (128,128,255,255),
            (96,96): (128,127,255,255),
            (96,160): (127,127,255,255),
            (215,24): (128,128,255,255),
            (232,40): (127,127,255,255),
            #(200,40): (191,64,218,255),
            (215,56): (128,127,255,255),
            (215,7): (128,128,255,255),
            (0,0): (128,128,255,255),
            (215,48): (128,127,255,255),
            (215,63): (128,127,255,255),
            (215,40): (128,127,255,255),
        },
    }
}

class TestAddon(unittest.TestCase):

    def reset_stage(self):
        for colname in ['VRChat Desktop Excellent', 'VRChat Quest Excellent', 'VRChat Quest Good',
                        'Second Life', 'VRChat Desktop Good', 'VRChat Quest Medium']:
            bpy.data.collections.remove(bpy.data.collections["Tuxedo Bake " + colname],
                                        do_unlink=True)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    def test_bake_button(self):
        bpy.context.scene.tuxedo_is_unittest = True
        bpy.ops.tuxedo_bake.preset_all()
        bpy.context.scene.bake_pass_displacement = False
        test_name = bpy.path.basename(bpy.context.blend_data.filepath)
        # TODO: test each of:
        bpy.context.scene.bake_cleanup_shapekeys = True
        bpy.context.scene.bake_apply_keys = True
        # bpy.context.scene.bake_unwrap_angle = FloatProperty(
        # bpy.context.scene.bake_optimize_solid_materials = BoolProperty(
        # bpy.context.scene.bake_uv_overlap_correction = EnumProperty(
        # bpy.context.scene.bake_generate_uvmap = BoolProperty(

        bpy.context.scene.bake_resolution = 256
        if 'bake.eyetest.blend' == test_name:
            bpy.context.scene.bake_uv_overlap_correction = 'NONE'
        # TODO: presently, all filter_image passes save to disk as an intermediate step, which
        # can introduce an error of +/- 1 value. We should save to a better intermediate format
        for filter_img in [False, True]:
            bpy.context.scene.bake_denoise = filter_img
            bpy.context.scene.bake_sharpen = filter_img
            result = bpy.ops.tuxedo_bake.bake()


            if test_name in sampling_lookup:
                for (bakename, cases) in sampling_lookup[test_name].items():
                    if bakename in bpy.data.images:
                        for (coordinate, _) in cases.items():
                            pxoffset = (coordinate[0] + (coordinate[1] * 256 )) * 4
                            foundcolor = tuple(round(px*255) for px in bpy.data.images[bakename].pixels[pxoffset:pxoffset+4])
                            print("{}@({}, {}): {}".format(bakename,
                                                                      coordinate[0],
                                                                      coordinate[1],
                                                                      foundcolor))

            # Confirm that the expected image result is randomly sampled
            self.assertTrue(test_name in sampling_lookup)
            for (bakename, cases) in sampling_lookup[test_name].items():
                self.assertTrue(bakename in bpy.data.images, bakename)
                #bpy.data.images[bakename].save()
                for (coordinate, color) in cases.items():
                    pxoffset = (coordinate[0] + (coordinate[1] * 256 )) * 4
                    foundcolor = tuple(round(px*255) for px in bpy.data.images[bakename].pixels[pxoffset:pxoffset+4])
                    foundraw = tuple(px for px in bpy.data.images[bakename].pixels[pxoffset:pxoffset+4])
                    if not filter_img:
                        for i in range(4):
                            self.assertTrue(color[i] - 2 <= foundcolor[i] <= color[i] + 2,
                                             "{}@({}, {}): {} != {} ({})".format(bakename,
                                                                                 coordinate[0],
                                                                                 coordinate[1],
                                                                                 color, foundcolor,
                                                                                 foundraw))
                    else:
                        for i in range(4):
                            # Wide margins, since sharpening actually does change it (on purpose)
                            self.assertTrue(color[i] - 40 <= foundcolor[i] <= color[i] + 40,
                                             "{}@({}, {}): {} != {} ({})".format(bakename,
                                                                                 coordinate[0],
                                                                                 coordinate[1],
                                                                                 color, foundcolor,
                                                                                 foundraw))
            test_collection_names = {
                'bake.bakematerialtest.blend': set([
                    'Tuxedo Bake Second Life',
                    'Tuxedo Bake VRChat Desktop Excellent',
                    'Tuxedo Bake VRChat Desktop Good',
                    'Tuxedo Bake VRChat Quest Excellent',
                    'Tuxedo Bake VRChat Quest Good',
                    'Tuxedo Bake VRChat Quest Medium',
                    'Collection',
                ]),
                'bake.eyetest.blend': set([
                    'Tuxedo Bake Second Life',
                    'Tuxedo Bake VRChat Desktop Excellent',
                    'Tuxedo Bake VRChat Desktop Good',
                    'Tuxedo Bake VRChat Quest Excellent',
                    'Tuxedo Bake VRChat Quest Good',
                    'Tuxedo Bake VRChat Quest Medium',
                    'Collection',
                ]),
                'bake.AOtest.blend': set([
                    'Tuxedo Bake Second Life',
                    'Tuxedo Bake VRChat Desktop Excellent',
                    'Tuxedo Bake VRChat Desktop Good',
                    'Tuxedo Bake VRChat Quest Excellent',
                    'Tuxedo Bake VRChat Quest Good',
                    'Tuxedo Bake VRChat Quest Medium',
                    'Collection',
                ])
            }
            self.assertEqual(set([o.name for o in bpy.data.collections]), test_collection_names[test_name])
            self.reset_stage()
        test_object_names = {
            'bake.bakematerialtest.blend': [
                'Armature',
                'Cube',
                'Cube.001'
            ],
            'bake.eyetest.blend': [
                'Armature',
                'CubeHead',
                'CubeHips',
                'CubeLeftEye',
                'CubeRightEye'
            ],
            'bake.AOtest.blend': [
                'Armature',
                'Sphere',
                'Sphere.001',
                'Sphere.002'
            ]
        }
        self.assertEqual([o.name for o in bpy.data.objects], test_object_names[test_name])

        # TODO: tests props

        # TODO: test copyonly

        # TODO: test resulting names

        # TODO: test twist bone removal

        # TODO: custom normal tests
        self.assertTrue(result == {'FINISHED'})

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAddon)
runner = unittest.TextTestRunner()
ret = not runner.run(suite).wasSuccessful()
sys.exit(ret)
