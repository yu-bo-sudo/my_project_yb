# -*- coding: utf-8 -*-
"""
Blender Auto Rig Binding Script
- Check/fix bone parent-child relationships
- Create armature modifier (skin binding)
- Auto-calculate weights
"""

import bpy
import sys
import os
from mathutils import Vector

# File path (use forward slashes or raw string)
BLEND_FILE = r"五指绑骨.blend"


# Standard human skeleton hierarchy
BONE_HIERARCHY = {
    # Spine/Head
    'Hips': {'parent': None},
    'Spine': {'parent': 'Hips'},
    'Spine1': {'parent': 'Spine'},
    'Spine2': {'parent': 'Spine1'},
    'Neck': {'parent': 'Spine2'},
    'Head': {'parent': 'Neck'},

    # Left Arm
    'LeftShoulder': {'parent': 'Spine2'},
    'LeftArm': {'parent': 'LeftShoulder'},
    'LeftForeArm': {'parent': 'LeftArm'},
    'LeftHand': {'parent': 'LeftForeArm'},

    # Right Arm
    'RightShoulder': {'parent': 'Spine2'},
    'RightArm': {'parent': 'RightShoulder'},
    'RightForeArm': {'parent': 'RightArm'},
    'RightHand': {'parent': 'RightForeArm'},

    # Left Leg
    'LeftUpLeg': {'parent': 'Hips'},
    'LeftLeg': {'parent': 'LeftUpLeg'},
    'LeftFoot': {'parent': 'LeftLeg'},
    'LeftToeBase': {'parent': 'LeftFoot'},

    # Right Leg
    'RightUpLeg': {'parent': 'Hips'},
    'RightLeg': {'parent': 'RightUpLeg'},
    'RightFoot': {'parent': 'RightLeg'},
    'RightToeBase': {'parent': 'RightFoot'},
}

# Finger bone patterns
FINGER_PATTERNS = {
    'thumb': ['thumb', 'Thumb', 'pollex'],
    'index': ['index', 'Index', 'pointer'],
    'middle': ['middle', 'Middle', 'major'],
    'ring': ['ring', 'Ring', 'annular'],
    'pinky': ['pinky', 'Pinky', 'little', 'Little'],
}

# Side detection patterns
SIDE_LEFT = ['left', 'Left', 'L_', '_L', '_l']
SIDE_RIGHT = ['right', 'Right', 'R_', '_R', '_r']


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


def get_bone_side(bone_name):
    name_lower = bone_name.lower()
    for pattern in SIDE_LEFT:
        if pattern in bone_name:
            return 'left'
    for pattern in SIDE_RIGHT:
        if pattern in bone_name:
            return 'right'
    if bone_name.endswith('L') or bone_name.endswith('l'):
        return 'left'
    if bone_name.endswith('R') or bone_name.endswith('r'):
        return 'right'
    return 'center'


def is_finger_bone(bone_name):
    name_lower = bone_name.lower()
    for finger, patterns in FINGER_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in name_lower:
                return True
    return False


def get_finger_info(bone_name):
    name_lower = bone_name.lower()
    side = get_bone_side(bone_name)

    for finger, patterns in FINGER_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in name_lower:
                for i in range(1, 4):
                    if str(i) in bone_name:
                        return side, finger, i
                return side, finger, 1
    return None, None, None


def analyze_skeleton(armature):
    print("\n" + "=" * 50)
    print("Analyzing Skeleton Structure")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    print(f"\nTotal bones: {len(edit_bones)}")

    body_bones = []
    finger_bones = []
    other_bones = []

    for bone in edit_bones:
        if is_finger_bone(bone.name):
            finger_bones.append(bone.name)
        elif bone.name in BONE_HIERARCHY:
            body_bones.append(bone.name)
        else:
            other_bones.append(bone.name)

    print(f"\nBody bones: {len(body_bones)}")
    for name in body_bones:
        print(f"  - {name}")

    print(f"\nFinger bones: {len(finger_bones)}")
    for name in finger_bones:
        print(f"  - {name}")

    print(f"\nOther bones: {len(other_bones)}")
    for name in other_bones:
        print(f"  - {name}")

    bpy.ops.object.mode_set(mode='OBJECT')
    return body_bones, finger_bones, other_bones


def fix_parent_relationships(armature):
    print("\n" + "=" * 50)
    print("Fixing Parent Relationships")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    fixed_count = 0

    # Fix body bones
    for bone_name, config in BONE_HIERARCHY.items():
        if bone_name not in edit_bones:
            continue

        bone = edit_bones[bone_name]
        expected_parent = config['parent']

        if expected_parent is None:
            if bone.parent is not None:
                print(f"  [Fix] {bone_name}: Removing parent (should be root)")
                bone.parent = None
                fixed_count += 1
        else:
            if expected_parent in edit_bones:
                if bone.parent != edit_bones[expected_parent]:
                    print(f"  [Fix] {bone_name}: Setting parent to {expected_parent}")
                    bone.parent = edit_bones[expected_parent]
                    bone.use_connect = False
                    fixed_count += 1

    # Fix finger bones
    print("\n  Processing finger bones...")

    finger_groups = {}
    for bone in edit_bones:
        if is_finger_bone(bone.name):
            side, finger, joint = get_finger_info(bone.name)
            if side and finger:
                key = (side, finger)
                if key not in finger_groups:
                    finger_groups[key] = []
                finger_groups[key].append((joint, bone.name))

    for (side, finger), bones in finger_groups.items():
        bones.sort(key=lambda x: x[0])
        hand_name = 'LeftHand' if side == 'left' else 'RightHand'

        for i, (joint, bone_name) in enumerate(bones):
            bone = edit_bones[bone_name]

            if i == 0:
                if hand_name in edit_bones:
                    if bone.parent != edit_bones[hand_name]:
                        print(f"  [Fix] {bone_name}: Setting parent to {hand_name}")
                        bone.parent = edit_bones[hand_name]
                        bone.use_connect = False
                        fixed_count += 1
            else:
                prev_bone_name = bones[i-1][1]
                if prev_bone_name in edit_bones:
                    if bone.parent != edit_bones[prev_bone_name]:
                        print(f"  [Fix] {bone_name}: Setting parent to {prev_bone_name}")
                        bone.parent = edit_bones[prev_bone_name]
                        bone.use_connect = False
                        fixed_count += 1

    # Handle remaining bones without parent
    for bone in edit_bones:
        if bone.parent is None and bone.name not in ['Hips', 'hips']:
            best_parent = None
            best_dist = float('inf')

            for potential_parent in edit_bones:
                if potential_parent == bone:
                    continue
                dist = (bone.head - potential_parent.tail).length
                if dist < best_dist and dist < 0.1:
                    best_dist = dist
                    best_parent = potential_parent

            if best_parent:
                print(f"  [Auto] {bone.name}: Setting parent to {best_parent.name}")
                bone.parent = best_parent
                bone.use_connect = False
                fixed_count += 1

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"\nTotal fixes: {fixed_count}")
    return fixed_count


def create_armature_modifier(mesh_obj, armature):
    print("\n" + "=" * 50)
    print("Creating Armature Modifier")
    print("=" * 50)

    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            print(f"  Removing existing modifier: {mod.name}")
            mesh_obj.modifiers.remove(mod)

    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature

    print(f"  Created armature modifier: {mod.name}")
    print(f"  Target armature: {armature.name}")
    return mod


def calculate_auto_weights(mesh_obj, armature):
    print("\n" + "=" * 50)
    print("Calculating Auto Weights")
    print("=" * 50)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    mesh_obj.select_set(True)

    print(f"  Armature: {armature.name}")
    print(f"  Mesh: {mesh_obj.name}")
    print(f"  Vertices: {len(mesh_obj.data.vertices)}")

    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        print("\n  SUCCESS: Automatic weights applied!")
        return True
    except Exception as e:
        print(f"\n  ERROR: Failed to apply auto weights: {e}")
        return False


def verify_weights(mesh_obj, armature):
    print("\n" + "=" * 50)
    print("Verifying Weights")
    print("=" * 50)

    vg_count = len(mesh_obj.vertex_groups)
    print(f"  Vertex groups: {vg_count}")

    bone_count = len(armature.data.bones)
    print(f"  Bones: {bone_count}")

    missing_groups = []
    for bone in armature.data.bones:
        if bone.name not in mesh_obj.vertex_groups:
            missing_groups.append(bone.name)

    if missing_groups:
        print(f"\n  Warning: {len(missing_groups)} bones missing vertex groups")
    else:
        print("\n  All bones have vertex groups!")

    weighted_count = 0
    unweighted_count = 0

    for vert in mesh_obj.data.vertices:
        if len(vert.groups) > 0:
            weighted_count += 1
        else:
            unweighted_count += 1

    print(f"\n  Weighted vertices: {weighted_count}")
    print(f"  Unweighted vertices: {unweighted_count}")

    return unweighted_count == 0


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    blend_path = os.path.join(script_dir, BLEND_FILE)

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
        if argv:
            blend_path = argv[0]

    print("\n" + "=" * 60)
    print("AUTO RIG BINDING SCRIPT")
    print("=" * 60)
    print(f"Input file: {blend_path}")

    if not os.path.exists(blend_path):
        print(f"\nError: File not found - {blend_path}")
        return

    print("\n[1/6] Opening blend file...")
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    print("  File loaded successfully")

    print("\n[2/6] Finding objects...")
    armature = find_armature()
    mesh_obj = find_mesh()

    if not armature:
        print("Error: No armature found!")
        return
    print(f"  Found armature: {armature.name}")

    if not mesh_obj:
        print("Error: No mesh found!")
        return
    print(f"  Found mesh: {mesh_obj.name}")
    print(f"  Mesh vertices: {len(mesh_obj.data.vertices)}")

    print("\n[3/6] Analyzing skeleton...")
    analyze_skeleton(armature)

    print("\n[4/6] Fixing parent relationships...")
    fix_parent_relationships(armature)

    print("\n[5/6] Creating armature modifier...")
    create_armature_modifier(mesh_obj, armature)

    print("\n[6/6] Calculating automatic weights...")
    success = calculate_auto_weights(mesh_obj, armature)

    if success:
        verify_weights(mesh_obj, armature)

    output_blend = blend_path.replace('.blend', '_bound.blend')
    print(f"\nSaving blend file: {output_blend}")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)

    output_fbx = blend_path.replace('.blend', '_bound.fbx')
    print(f"\nExporting FBX: {output_fbx}")
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
    )

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"Output blend: {output_blend}")
    print(f"Output FBX: {output_fbx}")


if __name__ == "__main__":
    main()
