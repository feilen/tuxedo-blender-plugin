# GPL Licence
import unittest
import sys
import bpy
from mathutils import Vector
import random

# Create a bone, create a sphere, parent the sphere to the bone with weight painting, then use
# GenerateTwistBones to generate a new bone. Test that it twists nicely
class TestGenerateTwistBones(unittest.TestCase):
    def test_generate_twistbones(self):
        # Create armature
        bpy.ops.object.add(type='ARMATURE', enter_editmode=True)
        armature = bpy.context.object
        bone = armature.data.edit_bones.new('TestBone')
        bone.tail = (0, 0, 1)
        bone.head = (0, 0, 0)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Create sphere
        bpy.ops.mesh.primitive_uv_sphere_add()
        sphere = bpy.context.object

        # Parent sphere to bone with armature deform
        sphere.parent = armature
        sphere.modifiers.new("Armature", 'ARMATURE')
        sphere.modifiers["Armature"].object = armature
        sphere.modifiers["Armature"].use_deform_preserve_volume = True
        sphere.modifiers["Armature"].use_vertex_groups = True

        # Select sphere
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = sphere

        # Set vertex weight to 1.0
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_assign_new()
        sphere.vertex_groups.active.name = "TestBone"
        bpy.ops.object.mode_set(mode='OBJECT')

        # Test that we have one bone, one vertex group so far
        self.assertEqual(len(armature.data.bones), 1)
        self.assertEqual(len(sphere.vertex_groups), 1)

        # Select armature
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)

        # Select TestBone
        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature.data.edit_bones["TestBone"]
        armature.data.edit_bones.active = bone
        bone.select = True

        # Generate twistbones
        self.assertEqual(bpy.ops.tuxedo.generate_twist_bones(), {'FINISHED'})
        self.assertEqual(len(armature.data.bones), 2)
        self.assertEqual(len(sphere.vertex_groups), 2)

        # Cleanup
        bpy.data.objects.remove(sphere)
        bpy.data.objects.remove(armature)

# Test smart decimation: create a sphere, add shapekeys, decimate and ensure decimated shapekeys are
# roughly similar to the original shapekeys
class TestSmartDecimation(unittest.TestCase):
    def test_smart_decimation(self):
        # Create a sphere
        bpy.ops.mesh.primitive_uv_sphere_add()
        sphere = bpy.context.object
        sphere.name = "TestSmartDecimation"

        # Create armature
        bpy.ops.object.add(type='ARMATURE', enter_editmode=True)
        new_arm = bpy.context.object
        new_arm.name = "TestSmartDecimationArmature"
        bone = new_arm.data.edit_bones.new('TestBone')
        bone.tail = (0, 0, 1)
        bone.head = (0, 0, 0)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Parent sphere to armature
        sphere.parent = new_arm
        sphere.modifiers.new("Armature", 'ARMATURE')
        sphere.modifiers["Armature"].object = new_arm

        # Add shape keys
        sphere.shape_key_add(name="Test1")
        sphere.shape_key_add(name="Test2")
        sphere.shape_key_add(name="Test3")
        sphere.shape_key_add(name="Test4")

        # Add some noise to the sphere
        for vert in sphere.data.vertices:
            vert.co = vert.co + Vector((random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)))

        # Add some noise to the shape keys
        for key in sphere.data.shape_keys.key_blocks[1:]:
            for vert in key.data:
                vert.co = vert.co + Vector((random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)))

        # Decimate
        bpy.context.scene.tuxedo_max_tris = 5
        bpy.ops.tuxedo.smart_decimation(armature_name=new_arm.name, preserve_seams=False,  preserve_objects=False, max_single_mesh_tris=bpy.context.scene.tuxedo_max_tris)

        # Ensure shape keys are similar
        for key in sphere.data.shape_keys.key_blocks[1:]:
            print("Testing shape key {}".format(key.name))
            for vert, decimated_vert in zip(key.data, sphere.data.vertices):
                self.assertAlmostEqual(vert.co.x, decimated_vert.co.x, delta=0.1)
                self.assertAlmostEqual(vert.co.y, decimated_vert.co.y, delta=0.1)
                self.assertAlmostEqual(vert.co.z, decimated_vert.co.z, delta=0.1)

        # Cleanup
        bpy.data.objects.remove(sphere)

# Test repair shapekeys: create an object with shapekeys, make modifications to several, then call
# RepairShapekeys and ensure shapekeys return to normal
class TestRepairShapekeys(unittest.TestCase):
    def test_repair_shapekeys(self):
        # Create object
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.name = "Test Repair Shapekeys"
        # Add shapekeys
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Basis"
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Test Shapekey 1"
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Test Shapekey 2"
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Test Shapekey 3"

        # Confirm number of shapekeys
        self.assertEqual(len(obj.data.shape_keys.key_blocks), 4)

        # Move a couple vertices in each shapekey
        obj.active_shape_key_index = 1
        obj.active_shape_key.data[4].co[0] = 3.0
        obj.active_shape_key.data[4].co[1] = 3.0
        obj.active_shape_key.data[4].co[2] = 3.0
        obj.active_shape_key_index = 2
        obj.active_shape_key.data[3].co[0] = 4.0
        obj.active_shape_key.data[3].co[1] = 4.0
        obj.active_shape_key.data[3].co[2] = 4.0
        obj.active_shape_key_index = 3
        obj.active_shape_key.data[5].co[0] = 5.0
        obj.active_shape_key.data[5].co[1] = 5.0
        obj.active_shape_key.data[5].co[2] = 5.0
        obj.data.update()

        # Decimate in edit mode, thereby messing up shapekeys
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.decimate(ratio=0.5)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Call repair
        self.assertEqual(bpy.ops.tuxedo.repair_shapekeys(), {'FINISHED'})

        # Check results
        obj.active_shape_key_index = 1
        for v in obj.active_shape_key.data:
            print(v.co)
        self.assertTrue(any(v.co[0] == v.co[1] == v.co[2] == 3.0 for v in obj.active_shape_key.data))
        obj.active_shape_key_index = 2
        for v in obj.active_shape_key.data:
            print(v.co)
        obj.active_shape_key_index = 3
        for v in obj.active_shape_key.data:
            print(v.co)

        # Delete object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.delete()

suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestGenerateTwistBones))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestSmartDecimation))
#suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestRepairShapekeys))

runner = unittest.TextTestRunner()
ret = not runner.run(suite).wasSuccessful()
sys.exit(ret)
