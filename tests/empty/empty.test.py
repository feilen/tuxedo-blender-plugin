# GPL Licence
import unittest
import sys
import bpy

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

        # Create sphere
        bpy.ops.mesh.primitive_uv_sphere_add()
        sphere = bpy.context.object
        sphere.parent = armature
        sphere.parent_type = 'BONE'
        sphere.parent_bone = bone.name

        # Paint weights
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.paint.weight_paint_toggle()
        bpy.ops.paint.weight_set(value=1.0)
        bpy.ops.paint.weight_paint_toggle()
        bpy.ops.object.mode_set(mode='EDIT')

        # Generate twistbones
        bpy.ops.tuxedo.generate_twist_bones()
        self.assertEqual(len(armature.data.edit_bones), 2)
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
        decimate(sphere, 0.1)

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
        obj.active_shape_key.name = "Test Shapekey 1"
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Test Shapekey 2"
        bpy.ops.object.shape_key_add(from_mix=False)
        obj.active_shape_key.name = "Test Shapekey 3"
        # Apply shapekeys
        for idx in range(1, len(obj.data.shape_keys.key_blocks)):
            obj.active_shape_key_index = idx
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 1", blend=1.0, add=True)
            bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 2", blend=1.0, add=True)
            bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 3", blend=1.0, add=True)
            bpy.ops.object.mode_set(mode='OBJECT')
        # Make modifications to shapekeys
        obj.active_shape_key_index = 1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 1", blend=1.0, add=True)
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 2", blend=1.0, add=True)
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 3", blend=1.0, add=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.active_shape_key_index = 2
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 1", blend=1.0, add=True)
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 2", blend=1.0, add=True)
        bpy.ops.mesh.blend_from_shape(shape="Test Shapekey 3", blend=1.0, add=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.active_shape_key_index = 0
        # Call repair
        repair_shapekeys(obj)
        # Check results
        obj.active_shape_key_index = 0
        self.assertEqual(obj.active_shape_key.data[0].co[0], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[1], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[2], 1.0)
        obj.active_shape_key_index = 1
        self.assertEqual(obj.active_shape_key.data[0].co[0], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[1], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[2], 1.0)
        obj.active_shape_key_index = 2
        self.assertEqual(obj.active_shape_key.data[0].co[0], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[1], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[2], 1.0)
        obj.active_shape_key_index = 3
        self.assertEqual(obj.active_shape_key.data[0].co[0], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[1], 1.0)
        self.assertEqual(obj.active_shape_key.data[0].co[2], 1.0)

        # Delete object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.delete()

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAddon)
runner = unittest.TextTestRunner()
ret = not runner.run(suite).wasSuccessful()
sys.exit(ret)
