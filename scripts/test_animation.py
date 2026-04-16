# -*- coding: utf-8 -*-
"""
Test bone binding by creating a simple animation
Run this in Blender with the bound file open
"""

import bpy
import math

def test_finger_animation():
    """Create test animation for finger bones"""

    # Find armature
    armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if not armature:
        print("No armature found!")
        return

    print(f"Found armature: {armature.name}")

    # Switch to pose mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Get all finger bones
    finger_bones = []
    for bone in armature.pose.bones:
        name_lower = bone.name.lower()
        if any(f in name_lower for f in ['thumb', 'index', 'middle', 'ring', 'pinky']):
            finger_bones.append(bone.name)

    print(f"Found {len(finger_bones)} finger bones")

    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60

    # Create a simple rotation animation for each finger
    for bone_name in finger_bones:
        pbone = armature.pose.bones[bone_name]

        # Frame 1 - rest position
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = (0, 0, 0)
        pbone.keyframe_insert(data_path='rotation_euler', frame=1)

        # Frame 30 - curled
        pbone.rotation_euler = (0, math.radians(30), 0)
        pbone.keyframe_insert(data_path='rotation_euler', frame=30)

        # Frame 60 - back to rest
        pbone.rotation_euler = (0, 0, 0)
        pbone.keyframe_insert(data_path='rotation_euler', frame=60)

    print("Animation created! Press Play to see fingers curl.")

    # Switch back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Save with animation
    output_path = bpy.data.filepath.replace('.blend', '_test.blend')
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"Saved test file: {output_path}")


if __name__ == "__main__":
    test_finger_animation()
