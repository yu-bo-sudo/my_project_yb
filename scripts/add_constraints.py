# -*- coding: utf-8 -*-
"""
Add bone constraints to limit unrealistic movements
Makes the rig behave more like a real human body
"""

import bpy
import math
from mathutils import Vector

# Bone constraint settings
# Format: bone_name: {constraint_type: settings}

ROTATION_LIMITS = {
    # Spine - limited rotation for realistic bending
    'Spine': {'x_min': -15, 'x_max': 15, 'y_min': -30, 'y_max': 30, 'z_min': -10, 'z_max': 10},
    'Spine1': {'x_min': -15, 'x_max': 15, 'y_min': -25, 'y_max': 25, 'z_min': -10, 'z_max': 10},
    'Spine2': {'x_min': -20, 'x_max': 20, 'y_min': -20, 'y_max': 20, 'z_min': -15, 'z_max': 15},

    # Neck - limited head rotation
    'Neck': {'x_min': -30, 'x_max': 30, 'y_min': -45, 'y_max': 45, 'z_min': -20, 'z_max': 20},
    'Head': {'x_min': -30, 'x_max': 20, 'y_min': -70, 'y_max': 70, 'z_min': -40, 'z_max': 40},

    # Shoulders - limited rotation
    'LeftShoulder': {'x_min': -20, 'x_max': 20, 'y_min': -20, 'y_max': 20, 'z_min': -15, 'z_max': 15},
    'RightShoulder': {'x_min': -20, 'x_max': 20, 'y_min': -20, 'y_max': 20, 'z_min': -15, 'z_max': 15},

    # Arms - mainly forward/backward and rotation
    'LeftArm': {'x_min': -180, 'x_max': 60, 'y_min': -135, 'y_max': 135, 'z_min': -90, 'z_max': 90},
    'RightArm': {'x_min': -180, 'x_max': 60, 'y_min': -135, 'y_max': 135, 'z_min': -90, 'z_max': 90},

    # Forearms - mainly rotation (twist) and slight bend
    'LeftForeArm': {'x_min': 0, 'x_max': 145, 'y_min': 0, 'y_max': 0, 'z_min': -90, 'z_max': 90},
    'RightForeArm': {'x_min': 0, 'x_max': 145, 'y_min': 0, 'y_max': 0, 'z_min': -90, 'z_max': 90},

    # Hands - limited rotation
    'LeftHand': {'x_min': -70, 'x_max': 70, 'y_min': -30, 'y_max': 30, 'z_min': -20, 'y_max': 20},
    'RightHand': {'x_min': -70, 'x_max': 70, 'y_min': -30, 'y_max': 30, 'z_min': -20, 'z_max': 20},

    # Legs - forward/backward movement
    'LeftUpLeg': {'x_min': -30, 'x_max': 120, 'y_min': -45, 'y_max': 45, 'z_min': -40, 'z_max': 40},
    'RightUpLeg': {'x_min': -30, 'x_max': 120, 'y_min': -45, 'y_max': 45, 'z_min': -40, 'z_max': 40},

    # Knees - only bend backward
    'LeftLeg': {'x_min': 0, 'x_max': 140, 'y_min': 0, 'y_max': 0, 'z_min': 0, 'z_max': 0},
    'RightLeg': {'x_min': 0, 'x_max': 140, 'y_min': 0, 'y_max': 0, 'z_min': 0, 'z_max': 0},

    # Feet
    'LeftFoot': {'x_min': -50, 'x_max': 30, 'y_min': -30, 'y_max': 30, 'z_min': -20, 'z_max': 20},
    'RightFoot': {'x_min': -50, 'x_max': 30, 'y_min': -30, 'y_max': 30, 'z_min': -20, 'z_max': 20},

    # Toes
    'LeftToeBase': {'x_min': 0, 'x_max': 45, 'y_min': 0, 'y_max': 0, 'z_min': 0, 'z_max': 0},
    'RightToeBase': {'x_min': 0, 'x_max': 45, 'y_min': 0, 'y_max': 0, 'z_min': 0, 'z_max': 0},
}

# Finger rotation limits (degrees)
FINGER_LIMITS = {
    # Each finger joint can only bend in one direction
    'default': {
        'curl_min': 0,      # Minimum bend (straight)
        'curl_max': 90,     # Maximum bend (curled)
        'spread_min': -20,  # Side movement minimum
        'spread_max': 20,   # Side movement maximum
    },
    'thumb': {
        'curl_min': 0,
        'curl_max': 70,
        'spread_min': -30,
        'spread_max': 30,
    },
}


def find_armature():
    """Find armature in scene"""
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def add_limit_rotation_constraint(pose_bone, limits):
    """Add limit rotation constraint to a bone"""
    # Remove existing limit rotation constraints
    for c in pose_bone.constraints:
        if c.type == 'LIMIT_ROTATION':
            pose_bone.constraints.remove(c)

    # Add new constraint
    const = pose_bone.constraints.new('LIMIT_ROTATION')
    const.name = "LimitRotation"

    # Set limits
    const.use_limit_x = True
    const.use_limit_y = True
    const.use_limit_z = True

    const.min_x = math.radians(limits.get('x_min', -180))
    const.max_x = math.radians(limits.get('x_max', 180))
    const.min_y = math.radians(limits.get('y_min', -180))
    const.max_y = math.radians(limits.get('y_max', 180))
    const.min_z = math.radians(limits.get('z_min', -180))
    const.max_z = math.radians(limits.get('z_max', 180))

    # Use local space
    const.owner_space = 'LOCAL'
    const.target_space = 'LOCAL'

    return const


def add_finger_constraints(armature):
    """Add constraints to finger bones"""
    pose_bones = armature.pose.bones
    finger_bones = []

    # Find all finger bones
    for bone in pose_bones:
        name_lower = bone.name.lower()
        if any(f in name_lower for f in ['thumb', 'index', 'middle', 'ring', 'pinky']):
            finger_bones.append(bone)

    print(f"\nAdding constraints to {len(finger_bones)} finger bones...")

    for bone in finger_bones:
        name_lower = bone.name.lower()

        # Determine which finger
        finger_type = 'default'
        if 'thumb' in name_lower:
            finger_type = 'thumb'

        limits = FINGER_LIMITS.get(finger_type, FINGER_LIMITS['default'])

        # Remove existing constraints
        for c in bone.constraints:
            if c.type == 'LIMIT_ROTATION':
                bone.constraints.remove(c)

        # Add limit rotation constraint
        const = bone.constraints.new('LIMIT_ROTATION')
        const.name = "LimitFingerRotation"

        # Fingers mainly bend on one axis (typically X or Z depending on orientation)
        const.use_limit_x = True
        const.use_limit_y = True
        const.use_limit_z = True

        # Set curl limits (bending)
        const.min_x = math.radians(limits['curl_min'])
        const.max_x = math.radians(limits['curl_max'])

        # Set spread limits (side movement)
        const.min_z = math.radians(limits['spread_min'])
        const.max_z = math.radians(limits['spread_max'])

        # Lock Y rotation (twist)
        const.min_y = 0
        const.max_y = 0

        const.owner_space = 'LOCAL'

        print(f"  Added constraint to: {bone.name}")


def add_body_constraints(armature):
    """Add constraints to body bones"""
    pose_bones = armature.pose.bones
    added_count = 0

    print("\nAdding constraints to body bones...")

    for bone_name, limits in ROTATION_LIMITS.items():
        if bone_name in pose_bones:
            bone = pose_bones[bone_name]
            const = add_limit_rotation_constraint(bone, limits)
            print(f"  Added constraint to: {bone_name}")
            added_count += 1
        else:
            # Try to find similar bone name
            for pb in pose_bones:
                if bone_name.lower() in pb.name.lower() or pb.name.lower() in bone_name.lower():
                    const = add_limit_rotation_constraint(pb, limits)
                    print(f"  Added constraint to: {pb.name} (matched {bone_name})")
                    added_count += 1
                    break

    return added_count


def lock_unused_axes(armature):
    """Lock translation and scale on all bones"""
    pose_bones = armature.pose.bones

    print("\nLocking unused axes...")

    for bone in pose_bones:
        # Lock location (bones should only rotate, not translate)
        bone.lock_location = (True, True, True)

        # Lock scale
        bone.lock_scale = (True, True, True)

    print(f"  Locked translation and scale for {len(pose_bones)} bones")


def add_ik_constraints(armature):
    """Add IK constraints for arms and legs (optional)"""
    print("\nSetting up IK helpers...")

    pose_bones = armature.pose.bones
    bpy.context.view_layer.objects.active = armature

    # IK setup for legs
    leg_ik_setup = [
        ('LeftLeg', 'LeftFoot'),
        ('RightLeg', 'RightFoot'),
    ]

    for leg_bone, foot_bone in leg_ik_setup:
        if leg_bone in pose_bones and foot_bone in pose_bones:
            # Add copy rotation constraint to help with knee bending
            # This is a simplified IK-like setup
            pass  # IK requires more complex setup with pole targets

    print("  IK setup complete (basic)")


def verify_constraints(armature):
    """Verify all constraints are applied"""
    print("\n" + "=" * 50)
    print("Constraint Verification")
    print("=" * 50)

    pose_bones = armature.pose.bones
    constrained_count = 0

    for bone in pose_bones:
        for c in bone.constraints:
            if c.type == 'LIMIT_ROTATION':
                constrained_count += 1
                print(f"  {bone.name}: {c.name}")
                print(f"    X: {math.degrees(c.min_x):.1f} to {math.degrees(c.max_x):.1f}")
                print(f"    Y: {math.degrees(c.min_y):.1f} to {math.degrees(c.max_y):.1f}")
                print(f"    Z: {math.degrees(c.min_z):.1f} to {math.degrees(c.max_z):.1f}")

    print(f"\nTotal constrained bones: {constrained_count}")


def main():
    print("\n" + "=" * 60)
    print("ADDING BONE CONSTRAINTS")
    print("=" * 60)

    # Find armature
    armature = find_armature()
    if not armature:
        print("Error: No armature found!")
        return

    print(f"Found armature: {armature.name}")

    # Switch to pose mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Add constraints
    body_count = add_body_constraints(armature)
    add_finger_constraints(armature)

    # Lock unused axes
    lock_unused_axes(armature)

    # Verify
    verify_constraints(armature)

    # Save
    output_path = bpy.data.filepath.replace('.blend', '_constrained.blend')
    if not bpy.data.filepath:
        output_path = "E:/xnrw/xuniren/五指绑骨_constrained.blend"

    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"Saved to: {output_path}")
    print("\nNow bones will only rotate within realistic human limits!")


if __name__ == "__main__":
    main()
