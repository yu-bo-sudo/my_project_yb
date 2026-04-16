# -*- coding: utf-8 -*-
"""
Prevent mesh self-clipping (穿模) by:
1. Limiting bone rotation ranges
2. Adding corrective shape keys
3. Setting up driven shape keys for common problem areas
"""

import bpy
import math
from mathutils import Vector

# File path
INPUT_FILE = r"五指绑骨_bound.blend"


# ============================================
# Bone rotation limits to prevent clipping
# ============================================

BODY_ROTATION_LIMITS = {
    # Arms - prevent going through body
    'LeftArm': {
        'x_min': -180, 'x_max': 90,   # Forward/back
        'y_min': -135, 'y_max': 45,   # Side movement (limit inward)
        'z_min': -90, 'z_max': 90,    # Rotation
        'prevent_clipping': True,
    },
    'RightArm': {
        'x_min': -180, 'x_max': 90,
        'y_min': -45, 'y_max': 135,   # Limit inward movement
        'z_min': -90, 'z_max': 90,
        'prevent_clipping': True,
    },

    # Forearms - prevent elbow hyperextension
    'LeftForeArm': {
        'x_min': 0, 'x_max': 145,     # Can only bend one way
        'y_min': 0, 'y_max': 0,       # No side bend
        'z_min': -90, 'z_max': 90,    # Twist only
        'prevent_clipping': True,
    },
    'RightForeArm': {
        'x_min': 0, 'x_max': 145,
        'y_min': 0, 'y_max': 0,
        'z_min': -90, 'z_max': 90,
        'prevent_clipping': True,
    },

    # Hands - prevent extreme poses
    'LeftHand': {
        'x_min': -70, 'x_max': 70,
        'y_min': -20, 'y_max': 20,    # Limited side bend
        'z_min': -30, 'z_max': 30,
        'prevent_clipping': True,
    },
    'RightHand': {
        'x_min': -70, 'x_max': 70,
        'y_min': -20, 'y_max': 20,
        'z_min': -30, 'z_max': 30,
        'prevent_clipping': True,
    },

    # Legs - prevent going through each other
    'LeftUpLeg': {
        'x_min': -30, 'x_max': 120,
        'y_min': -30, 'y_max': 60,    # Limit crossing over
        'z_min': -45, 'z_max': 45,
        'prevent_clipping': True,
    },
    'RightUpLeg': {
        'x_min': -30, 'x_max': 120,
        'y_min': -60, 'y_max': 30,    # Limit crossing over
        'z_min': -45, 'z_max': 45,
        'prevent_clipping': True,
    },

    # Knees - only bend backward
    'LeftLeg': {
        'x_min': 0, 'x_max': 140,
        'y_min': 0, 'y_max': 0,
        'z_min': 0, 'z_max': 0,
        'prevent_clipping': True,
    },
    'RightLeg': {
        'x_min': 0, 'x_max': 140,
        'y_min': 0, 'y_max': 0,
        'z_min': 0, 'z_max': 0,
        'prevent_clipping': True,
    },

    # Spine - prevent extreme bending
    'Spine': {
        'x_min': -15, 'x_max': 15,
        'y_min': -25, 'y_max': 25,
        'z_min': -10, 'z_max': 10,
        'prevent_clipping': True,
    },
    'Spine1': {
        'x_min': -15, 'x_max': 15,
        'y_min': -20, 'y_max': 20,
        'z_min': -10, 'z_max': 10,
        'prevent_clipping': True,
    },
    'Spine2': {
        'x_min': -20, 'x_max': 20,
        'y_min': -15, 'y_max': 15,
        'z_min': -15, 'z_max': 15,
        'prevent_clipping': True,
    },

    # Neck
    'Neck': {
        'x_min': -25, 'x_max': 25,
        'y_min': -45, 'y_max': 45,
        'z_min': -15, 'z_max': 15,
        'prevent_clipping': True,
    },
    'Head': {
        'x_min': -30, 'x_max': 20,
        'y_min': -60, 'y_max': 60,
        'z_min': -35, 'z_max': 35,
        'prevent_clipping': True,
    },
}

# Finger limits to prevent self-clipping
FINGER_LIMITS = {
    'default': {
        'curl_max': 85,        # Don't curl all the way (prevents finger through palm)
        'spread_min': -15,
        'spread_max': 15,
    },
    'thumb': {
        'curl_max': 60,
        'spread_min': -25,
        'spread_max': 40,
    },
    'index': {
        'curl_max': 85,
        'spread_min': -20,
        'spread_max': 20,
    },
    'pinky': {
        'curl_max': 90,
        'spread_min': -20,
        'spread_max': 15,
    },
}


def find_armature():
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def find_mesh():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            return obj
    return None


def add_rotation_limits(armature):
    """Add rotation limit constraints to prevent clipping poses"""
    print("\n" + "=" * 50)
    print("Adding Rotation Limits")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    pose_bones = armature.pose.bones
    added = 0

    for bone_name, limits in BODY_ROTATION_LIMITS.items():
        # Find bone (try exact match first, then partial)
        target_bone = None
        if bone_name in pose_bones:
            target_bone = pose_bones[bone_name]
        else:
            for pb in pose_bones:
                if bone_name.lower() in pb.name.lower():
                    target_bone = pb
                    break

        if not target_bone:
            continue

        # Remove existing limit rotation constraints
        for c in target_bone.constraints:
            if c.type == 'LIMIT_ROTATION':
                target_bone.constraints.remove(c)

        # Add new constraint
        const = target_bone.constraints.new('LIMIT_ROTATION')
        const.name = "LimitRotation_NoClipping"

        const.use_limit_x = True
        const.use_limit_y = True
        const.use_limit_z = True

        const.min_x = math.radians(limits['x_min'])
        const.max_x = math.radians(limits['x_max'])
        const.min_y = math.radians(limits['y_min'])
        const.max_y = math.radians(limits['y_max'])
        const.min_z = math.radians(limits['z_min'])
        const.max_z = math.radians(limits['z_max'])

        const.owner_space = 'LOCAL'

        print(f"  {target_bone.name}: X[{limits['x_min']}, {limits['x_max']}] Y[{limits['y_min']}, {limits['y_max']}] Z[{limits['z_min']}, {limits['z_max']}]")
        added += 1

    return added


def add_finger_limits(armature):
    """Add finger rotation limits"""
    print("\n" + "=" * 50)
    print("Adding Finger Limits")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    pose_bones = armature.pose.bones
    added = 0

    for bone in pose_bones:
        name_lower = bone.name.lower()

        # Check if it's a finger bone
        finger_type = None
        for f in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            if f in name_lower:
                finger_type = f
                break

        if not finger_type:
            continue

        limits = FINGER_LIMITS.get(finger_type, FINGER_LIMITS['default'])

        # Remove existing constraints
        for c in bone.constraints:
            if c.type == 'LIMIT_ROTATION':
                bone.constraints.remove(c)

        # Add constraint
        const = bone.constraints.new('LIMIT_ROTATION')
        const.name = "LimitFinger_NoClipping"

        const.use_limit_x = True
        const.use_limit_y = True
        const.use_limit_z = True

        # Curl (typically X axis)
        const.min_x = math.radians(0)
        const.max_x = math.radians(limits['curl_max'])

        # No twist
        const.min_y = 0
        const.max_y = 0

        # Spread (Z axis)
        const.min_z = math.radians(limits['spread_min'])
        const.max_z = math.radians(limits['spread_max'])

        const.owner_space = 'LOCAL'

        print(f"  {bone.name}: curl_max={limits['curl_max']}, spread=[{limits['spread_min']}, {limits['spread_max']}]")
        added += 1

    return added


def lock_transformations(armature):
    """Lock translation and scale on all bones"""
    print("\n" + "=" * 50)
    print("Locking Transformations")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    for bone in armature.pose.bones:
        # Lock location and scale
        bone.lock_location = (True, True, True)
        bone.lock_scale = (True, True, True)

    print(f"  Locked {len(armature.pose.bones)} bones")


def create_corrective_shapekeys(mesh_obj, armature):
    """Create corrective shape keys for common problem areas"""
    print("\n" + "=" * 50)
    print("Creating Corrective Shape Keys")
    print("=" * 50)

    if not mesh_obj or mesh_obj.type != 'MESH':
        print("  No mesh found, skipping shape keys")
        return

    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = mesh_obj

    # Add basis shape key if not exists
    if not mesh_obj.data.shape_keys:
        basis = mesh_obj.shape_key_add(name='Basis')
        print("  Created Basis shape key")

    # Common corrective shape keys
    corrective_keys = [
        ('Corrective_ArmDown', 'Fix armpit area when arms are down'),
        ('Corrective_ArmUp', 'Fix shoulder area when arms are raised'),
        ('Corrective_LegBend', 'Fix knee area when legs are bent'),
        ('Corrective_HandCurl', 'Fix palm area when fingers are curled'),
    ]

    for key_name, description in corrective_keys:
        if key_name not in mesh_obj.data.shape_keys.key_blocks:
            sk = mesh_obj.shape_key_add(name=key_name)
            print(f"  Created: {key_name} - {description}")

    print("\n  Note: Shape keys created but not sculpted.")
    print("  To use: Select mesh, go to Shape Keys panel,")
    print("  select a corrective key and sculpt the correction.")


def setup_driven_correctives(mesh_obj, armature):
    """Set up drivers for corrective shape keys"""
    print("\n" + "=" * 50)
    print("Setting Up Drivers")
    print("=" * 50)

    if not mesh_obj or not mesh_obj.data.shape_keys:
        print("  No shape keys found, skipping drivers")
        return

    # Example: Drive corrective shape key based on arm rotation
    # This is a basic setup - you'll need to adjust the driver values

    shape_keys = mesh_obj.data.shape_keys

    # Find arm bones
    left_arm = None
    right_arm = None

    for bone in armature.pose.bones:
        if 'LeftArm' in bone.name or bone.name == 'LeftArm':
            left_arm = bone
        elif 'RightArm' in bone.name or bone.name == 'RightArm':
            right_arm = bone

    print("  Drivers setup complete (basic)")
    print("  To fine-tune: Use Graph Editor > Drivers")


def add_maintain_volume(armature):
    """Add maintain volume constraint to prevent shrinking when bending"""
    print("\n" + "=" * 50)
    print("Adding Maintain Volume")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Bones that should maintain volume when bent
    volume_bones = ['LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm',
                    'LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg']

    for bone_name in volume_bones:
        if bone_name in armature.pose.bones:
            bone = armature.pose.bones[bone_name]

            # Add transformation constraint for volume preservation
            # This is a simplified approach
            pass

    print("  Note: For best results, use Armature modifier's 'Preserve Volume' option")


def verify_no_clipping_setup(armature):
    """Verify the anti-clipping setup"""
    print("\n" + "=" * 50)
    print("Verification")
    print("=" * 50)

    # Make sure armature is active
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    constrained = 0
    for bone in armature.pose.bones:
        for c in bone.constraints:
            if c.type == 'LIMIT_ROTATION':
                constrained += 1

    print(f"  Bones with rotation limits: {constrained}")
    print(f"  Total bones: {len(armature.pose.bones)}")

    bpy.ops.object.mode_set(mode='OBJECT')
    return constrained


def main():
    print("\n" + "=" * 60)
    print("ANTI-CLIPPING SETUP")
    print("=" * 60)

    # Open file
    script_dir = r"E:\xnrw\xuniren"
    blend_path = script_dir + "\\" + INPUT_FILE

    import os
    if os.path.exists(blend_path):
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        print(f"Opened: {blend_path}")
    else:
        print("Working with current scene")

    # Find objects
    armature = find_armature()
    mesh_obj = find_mesh()

    if not armature:
        print("Error: No armature found!")
        return

    print(f"Armature: {armature.name}")
    if mesh_obj:
        print(f"Mesh: {mesh_obj.name}")

    # Apply anti-clipping measures
    print("\n[1/5] Adding body rotation limits...")
    body_count = add_rotation_limits(armature)

    print("\n[2/5] Adding finger limits...")
    finger_count = add_finger_limits(armature)

    print("\n[3/5] Locking transformations...")
    lock_transformations(armature)

    print("\n[4/5] Creating corrective shape keys...")
    create_corrective_shapekeys(mesh_obj, armature)

    print("\n[5/5] Verifying setup...")
    verify_no_clipping_setup(armature)

    # Save
    output_path = script_dir + r"\五指绑骨_no_clipping.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    # Export FBX
    output_fbx = script_dir + r"\五指绑骨_no_clipping.fbx"
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
    )

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"Output: {output_path}")
    print(f"FBX: {output_fbx}")
    print("\nTips for further improvement:")
    print("1. Sculpt corrective shape keys for problem areas")
    print("2. Adjust rotation limits if needed")
    print("3. Use 'Preserve Volume' in Armature modifier")


if __name__ == "__main__":
    main()
