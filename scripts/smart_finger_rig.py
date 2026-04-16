"""
Blender Auto Rig - Complete Skeleton Binding
Analyzes mesh geometry and creates a full body skeleton with finger bones
"""

import bpy
import math
from mathutils import Vector, Matrix
import sys
import os

FBX_FILE = "d641c0d695baef34532beb9539643e3f.fbx"


class MeshAnalyzer:
    """Analyze mesh geometry to find body part positions"""

    def __init__(self, mesh_obj):
        self.mesh_obj = mesh_obj
        self.world_matrix = mesh_obj.matrix_world
        self.vertices = [self.world_matrix @ v.co for v in mesh_obj.data.vertices]

        # Calculate bounding box
        self.min_x = min(v.x for v in self.vertices)
        self.max_x = max(v.x for v in self.vertices)
        self.min_y = min(v.y for v in self.vertices)
        self.max_y = max(v.y for v in self.vertices)
        self.min_z = min(v.z for v in self.vertices)
        self.max_z = max(v.z for v in self.vertices)

        self.center = Vector((
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2
        ))

        self.height = self.max_z - self.min_z
        self.width = self.max_x - self.min_x
        self.depth = self.max_y - self.min_y

        print(f"\nMesh Analysis:")
        print(f"  Vertices: {len(self.vertices)}")
        print(f"  Height: {self.height:.4f}")
        print(f"  Width: {self.width:.4f}")
        print(f"  Depth: {self.depth:.4f}")
        print(f"  Center: {self.center}")

    def get_vertices_in_region(self, center, radius, min_z=None, max_z=None):
        """Get vertices within a spherical region"""
        result = []
        for v in self.vertices:
            if min_z is not None and v.z < min_z:
                continue
            if max_z is not None and v.z > max_z:
                continue
            if (v - center).length < radius:
                result.append(v)
        return result

    def find_center_of_mass(self, vertices):
        """Find the center of a group of vertices"""
        if not vertices:
            return None
        avg = Vector((0, 0, 0))
        for v in vertices:
            avg += v
        return avg / len(vertices)

    def find_extremity(self, vertices, direction, reference=None):
        """Find the vertex furthest in a given direction"""
        if not vertices:
            return None

        best_v = vertices[0]
        best_proj = -float('inf')

        for v in vertices:
            if reference:
                proj = (v - reference).dot(direction)
            else:
                proj = v.dot(direction)
            if proj > best_proj:
                best_proj = proj
                best_v = v

        return best_v

    def analyze_body(self):
        """Analyze full body structure"""
        data = {}

        # Height percentages for body parts (approximate human proportions)
        # Assuming model is standing upright with feet at min_z

        # Head: top 15% of height
        head_z = self.max_z - self.height * 0.15
        head_verts = [v for v in self.vertices if v.z > head_z]
        if head_verts:
            data['head_top'] = self.find_extremity(head_verts, Vector((0, 0, 1)))
            data['head_bottom'] = self.find_extremity(head_verts, Vector((0, 0, -1)))
            data['head_center'] = self.find_center_of_mass(head_verts)
            print(f"  Head: top={data['head_top']}, bottom={data['head_bottom']}")

        # Neck: between head and shoulders
        neck_z = self.max_z - self.height * 0.18
        neck_verts = [v for v in self.vertices if abs(v.z - neck_z) < self.height * 0.03]
        if neck_verts:
            data['neck'] = self.find_center_of_mass(neck_verts)
            print(f"  Neck: {data['neck']}")

        # Shoulders
        shoulder_z = self.max_z - self.height * 0.22
        shoulder_verts = [v for v in self.vertices if abs(v.z - shoulder_z) < self.height * 0.05]

        # Left shoulder (positive x side or negative depending on model)
        left_shoulder_verts = [v for v in shoulder_verts if v.x > self.center.x]
        right_shoulder_verts = [v for v in shoulder_verts if v.x < self.center.x]

        if left_shoulder_verts:
            data['left_shoulder'] = self.find_extremity(left_shoulder_verts, Vector((1, 0, 0)))
            print(f"  Left shoulder: {data['left_shoulder']}")

        if right_shoulder_verts:
            data['right_shoulder'] = self.find_extremity(right_shoulder_verts, Vector((-1, 0, 0)))
            print(f"  Right shoulder: {data['right_shoulder']}")

        # Spine/Torso
        spine_verts = [v for v in self.vertices if abs(v.x - self.center.x) < self.width * 0.15]
        spine_verts = [v for v in spine_verts if self.min_z + self.height * 0.3 < v.z < shoulder_z]

        if spine_verts:
            data['spine_top'] = Vector((self.center.x, self.center.y, shoulder_z - 0.05))
            data['spine_mid'] = Vector((self.center.x, self.center.y, self.min_z + self.height * 0.55))
            data['spine_base'] = Vector((self.center.x, self.center.y, self.min_z + self.height * 0.35))
            print(f"  Spine: top={data['spine_top']}, mid={data['spine_mid']}, base={data['spine_base']}")

        # Hips/Pelvis
        hip_z = self.min_z + self.height * 0.32
        hip_verts = [v for v in self.vertices if abs(v.z - hip_z) < self.height * 0.05]

        left_hip_verts = [v for v in hip_verts if v.x > self.center.x]
        right_hip_verts = [v for v in hip_verts if v.x < self.center.x]

        if left_hip_verts:
            data['left_hip'] = self.find_center_of_mass(left_hip_verts)
        if right_hip_verts:
            data['right_hip'] = self.find_center_of_mass(right_hip_verts)

        data['pelvis'] = Vector((self.center.x, self.center.y, hip_z))
        print(f"  Pelvis: {data['pelvis']}")

        # Arms
        # Left arm
        left_arm_verts = [v for v in self.vertices if v.x > self.center.x + self.width * 0.15]
        left_arm_verts = [v for v in left_arm_verts if v.z < shoulder_z]

        if left_arm_verts:
            # Upper arm
            upper_arm_verts = [v for v in left_arm_verts if v.z > self.min_z + self.height * 0.45]
            if upper_arm_verts:
                data['left_upper_arm'] = self.find_center_of_mass(upper_arm_verts)
                data['left_elbow'] = self.find_extremity(upper_arm_verts, Vector((0, 0, -1)), data.get('left_shoulder'))

            # Forearm
            forearm_verts = [v for v in left_arm_verts if v.z < self.min_z + self.height * 0.45]
            if forearm_verts:
                data['left_forearm'] = self.find_center_of_mass(forearm_verts)
                data['left_wrist'] = self.find_extremity(forearm_verts, Vector((0, 0, -1)), data.get('left_elbow'))

        # Right arm
        right_arm_verts = [v for v in self.vertices if v.x < self.center.x - self.width * 0.15]
        right_arm_verts = [v for v in right_arm_verts if v.z < shoulder_z]

        if right_arm_verts:
            upper_arm_verts = [v for v in right_arm_verts if v.z > self.min_z + self.height * 0.45]
            if upper_arm_verts:
                data['right_upper_arm'] = self.find_center_of_mass(upper_arm_verts)
                data['right_elbow'] = self.find_extremity(upper_arm_verts, Vector((0, 0, -1)), data.get('right_shoulder'))

            forearm_verts = [v for v in right_arm_verts if v.z < self.min_z + self.height * 0.45]
            if forearm_verts:
                data['right_forearm'] = self.find_center_of_mass(forearm_verts)
                data['right_wrist'] = self.find_extremity(forearm_verts, Vector((0, 0, -1)), data.get('right_elbow'))

        # Hands
        hand_z = self.min_z + self.height * 0.25
        left_hand_verts = [v for v in self.vertices if v.x > self.center.x + self.width * 0.2]
        left_hand_verts = [v for v in left_hand_verts if v.z < hand_z]

        if left_hand_verts:
            data['left_hand'] = self.find_center_of_mass(left_hand_verts)
            data['left_hand_tip'] = self.find_extremity(left_hand_verts, Vector((0, 0, -1)))
            print(f"  Left hand: {data['left_hand']}")

        right_hand_verts = [v for v in self.vertices if v.x < self.center.x - self.width * 0.2]
        right_hand_verts = [v for v in right_hand_verts if v.z < hand_z]

        if right_hand_verts:
            data['right_hand'] = self.find_center_of_mass(right_hand_verts)
            data['right_hand_tip'] = self.find_extremity(right_hand_verts, Vector((0, 0, -1)))
            print(f"  Right hand: {data['right_hand']}")

        # Legs
        # Left leg
        left_leg_verts = [v for v in self.vertices if v.x > self.center.x]
        left_leg_verts = [v for v in left_leg_verts if v.z < hip_z]

        if left_leg_verts:
            # Upper leg (thigh)
            thigh_verts = [v for v in left_leg_verts if v.z > self.min_z + self.height * 0.15]
            if thigh_verts:
                data['left_thigh'] = self.find_center_of_mass(thigh_verts)
                data['left_knee'] = self.find_extremity(thigh_verts, Vector((0, 0, -1)))

            # Lower leg
            lower_leg_verts = [v for v in left_leg_verts if v.z < self.min_z + self.height * 0.15]
            if lower_leg_verts:
                data['left_shin'] = self.find_center_of_mass(lower_leg_verts)
                data['left_ankle'] = self.find_extremity(lower_leg_verts, Vector((0, 0, -1)))

            # Foot
            foot_verts = [v for v in left_leg_verts if v.z < self.min_z + self.height * 0.05]
            if foot_verts:
                data['left_foot'] = self.find_center_of_mass(foot_verts)
                data['left_toe'] = self.find_extremity(foot_verts, Vector((0, -1, 0)))

        # Right leg
        right_leg_verts = [v for v in self.vertices if v.x < self.center.x]
        right_leg_verts = [v for v in right_leg_verts if v.z < hip_z]

        if right_leg_verts:
            thigh_verts = [v for v in right_leg_verts if v.z > self.min_z + self.height * 0.15]
            if thigh_verts:
                data['right_thigh'] = self.find_center_of_mass(thigh_verts)
                data['right_knee'] = self.find_extremity(thigh_verts, Vector((0, 0, -1)))

            lower_leg_verts = [v for v in right_leg_verts if v.z < self.min_z + self.height * 0.15]
            if lower_leg_verts:
                data['right_shin'] = self.find_center_of_mass(lower_leg_verts)
                data['right_ankle'] = self.find_extremity(lower_leg_verts, Vector((0, 0, -1)))

            foot_verts = [v for v in right_leg_verts if v.z < self.min_z + self.height * 0.05]
            if foot_verts:
                data['right_foot'] = self.find_center_of_mass(foot_verts)
                data['right_toe'] = self.find_extremity(foot_verts, Vector((0, -1, 0)))

        return data


class SkeletonBuilder:
    """Build skeleton from analyzed data"""

    def __init__(self, armature, body_data, mesh_analyzer):
        self.armature = armature
        self.body_data = body_data
        self.analyzer = mesh_analyzer
        self.bones = {}

    def create_bone(self, name, head, tail, parent=None):
        """Create a single bone"""
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones

        if name in edit_bones:
            bone = edit_bones[name]
            bone.head = head
            bone.tail = tail
        else:
            bone = edit_bones.new(name)
            bone.head = head
            bone.tail = tail

        if parent and parent in edit_bones:
            bone.parent = edit_bones[parent]
            bone.use_connect = False

        bpy.ops.object.mode_set(mode='OBJECT')

        self.bones[name] = bone
        return bone

    def build_spine(self):
        """Build spine and head bones"""
        data = self.body_data

        # Pelvis/Hips
        pelvis = data.get('pelvis', self.analyzer.center - Vector((0, 0, self.analyzer.height * 0.3)))

        # Spine
        spine_base = data.get('spine_base', pelvis + Vector((0, 0, self.analyzer.height * 0.1)))
        spine_mid = data.get('spine_mid', pelvis + Vector((0, 0, self.analyzer.height * 0.25)))
        spine_top = data.get('spine_top', pelvis + Vector((0, 0, self.analyzer.height * 0.4)))

        # Create spine chain
        self.create_bone('Hips', pelvis, spine_base)
        self.create_bone('Spine', spine_base, spine_mid, 'Hips')
        self.create_bone('Spine1', spine_mid, spine_top, 'Spine')

        # Neck and Head
        neck = data.get('neck', spine_top + Vector((0, 0, self.analyzer.height * 0.05)))
        head_bottom = data.get('head_bottom', neck + Vector((0, 0, self.analyzer.height * 0.03)))
        head_top = data.get('head_top', neck + Vector((0, 0, self.analyzer.height * 0.15)))

        self.create_bone('Neck', spine_top, neck, 'Spine1')
        self.create_bone('Head', neck, head_top, 'Neck')

        print("  Created spine and head bones")

    def build_arms(self):
        """Build arm bones"""
        data = self.body_data

        for side in ['left', 'right']:
            prefix = 'Left' if side == 'left' else 'Right'
            suffix = '_l' if side == 'left' else '_r'

            # Get positions
            shoulder = data.get(f'{side}_shoulder')
            upper_arm = data.get(f'{side}_upper_arm')
            elbow = data.get(f'{side}_elbow')
            forearm = data.get(f'{side}_forearm')
            wrist = data.get(f'{side}_wrist')
            hand = data.get(f'{side}_hand')
            hand_tip = data.get(f'{side}_hand_tip')

            if not shoulder:
                continue

            # Shoulder
            spine_top = self.body_data.get('spine_top', self.analyzer.center)
            self.create_bone(f'{prefix}Shoulder', spine_top, shoulder, 'Spine1')

            # Arm chain
            if elbow:
                self.create_bone(f'{prefix}Arm', shoulder, elbow, f'{prefix}Shoulder')
            else:
                mid_arm = (shoulder + (hand or shoulder)) / 2
                self.create_bone(f'{prefix}Arm', shoulder, mid_arm, f'{prefix}Shoulder')
                elbow = mid_arm

            if wrist:
                self.create_bone(f'{prefix}ForeArm', elbow, wrist, f'{prefix}Arm')
            else:
                forearm_end = elbow + (hand or elbow - shoulder).normalized() * self.analyzer.height * 0.1
                self.create_bone(f'{prefix}ForeArm', elbow, forearm_end, f'{prefix}Arm')
                wrist = forearm_end

            # Hand
            if hand:
                hand_end = hand_tip if hand_tip else hand + Vector((0, 0, -self.analyzer.height * 0.05))
                self.create_bone(f'{prefix}Hand', wrist, hand, f'{prefix}ForeArm')

                # Build fingers
                self.build_fingers(side, hand, hand_tip)

            print(f"  Created {side} arm bones")

    def build_fingers(self, side, hand_pos, hand_tip):
        """Build finger bones for a hand"""
        data = self.body_data
        prefix = 'Left' if side == 'left' else 'Right'

        # Get hand vertices for finger detection
        hand_verts = []
        if side == 'left':
            hand_verts = [v for v in self.analyzer.vertices if v.x > self.analyzer.center.x]
        else:
            hand_verts = [v for v in self.analyzer.vertices if v.x < self.analyzer.center.x]

        hand_verts = [v for v in hand_verts if v.z < self.analyzer.min_z + self.analyzer.height * 0.25]

        if not hand_verts:
            # Fallback to calculated positions
            self._create_fingers_calculated(side, hand_pos, hand_tip)
            return

        # Find finger tips by clustering
        hand_min_x = min(v.x for v in hand_verts)
        hand_max_x = max(v.x for v in hand_verts)
        hand_width = hand_max_x - hand_min_x

        # Finger regions (from thumb to pinky)
        if side == 'left':
            finger_regions = [
                ('thumb', hand_max_x - hand_width * 0.2, hand_max_x),
                ('index', hand_max_x - hand_width * 0.4, hand_max_x - hand_width * 0.2),
                ('middle', hand_max_x - hand_width * 0.6, hand_max_x - hand_width * 0.4),
                ('ring', hand_max_x - hand_width * 0.8, hand_max_x - hand_width * 0.6),
                ('pinky', hand_min_x, hand_max_x - hand_width * 0.8),
            ]
        else:
            finger_regions = [
                ('thumb', hand_min_x, hand_min_x + hand_width * 0.2),
                ('index', hand_min_x + hand_width * 0.2, hand_min_x + hand_width * 0.4),
                ('middle', hand_min_x + hand_width * 0.4, hand_min_x + hand_width * 0.6),
                ('ring', hand_min_x + hand_width * 0.6, hand_min_x + hand_width * 0.8),
                ('pinky', hand_min_x + hand_width * 0.8, hand_max_x),
            ]

        for finger_name, x_min, x_max in finger_regions:
            finger_verts = [v for v in hand_verts if x_min <= v.x <= x_max]

            if not finger_verts:
                continue

            # Find tip (furthest from hand center in hand direction)
            hand_dir = (hand_tip - hand_pos).normalized() if hand_tip else Vector((0, 0, -1))
            tip = hand_pos
            max_dist = 0

            for v in finger_verts:
                dist = (v - hand_pos).dot(hand_dir)
                if dist > max_dist:
                    max_dist = dist
                    tip = v

            # Create 3 joints
            finger_length = max_dist
            if finger_length < 0.01:
                finger_length = self.analyzer.height * 0.03

            joint_len = finger_length / 3.2

            current_pos = hand_pos + (tip - hand_pos).normalized() * 0.01
            direction = (tip - hand_pos).normalized()

            # Special direction for thumb
            if finger_name == 'thumb':
                if side == 'left':
                    direction = Vector((1, -0.3, -0.3)).normalized()
                else:
                    direction = Vector((-1, -0.3, -0.3)).normalized()
                joint_len *= 0.8

            parent = f'{prefix}Hand'

            for i in range(3):
                bone_name = f'{finger_name}_{i+1}_{side[0]}'
                tail = current_pos + direction * joint_len
                self.create_bone(bone_name, current_pos, tail, parent)
                parent = bone_name
                current_pos = tail

        print(f"    Created {side} finger bones")

    def _create_fingers_calculated(self, side, hand_pos, hand_tip):
        """Fallback finger creation using calculated positions"""
        prefix = 'Left' if side == 'left' else 'Right'

        finger_offsets = {
            'thumb': Vector((0.04 if side == 'left' else -0.04, 0, 0)),
            'index': Vector((0.02 if side == 'left' else -0.02, 0, 0.01)),
            'middle': Vector((0, 0, 0.015)),
            'ring': Vector((-0.02 if side == 'left' else 0.02, 0, 0.01)),
            'pinky': Vector((-0.04 if side == 'left' else 0.04, 0, 0)),
        }

        finger_lengths = {
            'thumb': 0.06,
            'index': 0.07,
            'middle': 0.08,
            'ring': 0.07,
            'pinky': 0.05,
        }

        direction = Vector((0, 0, -1)) if not hand_tip else (hand_tip - hand_pos).normalized()

        for finger_name, offset in finger_offsets.items():
            base = hand_pos + offset
            length = finger_lengths[finger_name]
            joint_len = length / 3

            current_pos = base
            parent = f'{prefix}Hand'

            for i in range(3):
                bone_name = f'{finger_name}_{i+1}_{side[0]}'
                tail = current_pos + direction * joint_len
                self.create_bone(bone_name, current_pos, tail, parent)
                parent = bone_name
                current_pos = tail

    def build_legs(self):
        """Build leg bones"""
        data = self.body_data

        for side in ['left', 'right']:
            prefix = 'Left' if side == 'left' else 'Right'

            # Get positions
            hip = data.get(f'{side}_hip')
            thigh = data.get(f'{side}_thigh')
            knee = data.get(f'{side}_knee')
            shin = data.get(f'{side}_shin')
            ankle = data.get(f'{side}_ankle')
            foot = data.get(f'{side}_foot')
            toe = data.get(f'{side}_toe')

            pelvis = data.get('pelvis', self.analyzer.center)

            if not hip:
                # Calculate hip position
                hip = pelvis + Vector((0.1 if side == 'left' else -0.1, 0, -0.05))

            # UpLeg (thigh)
            if knee:
                self.create_bone(f'{prefix}UpLeg', hip, knee, 'Hips')
            else:
                knee_calc = hip + Vector((0, 0, -self.analyzer.height * 0.25))
                self.create_bone(f'{prefix}UpLeg', hip, knee_calc, 'Hips')
                knee = knee_calc

            # Leg (shin)
            if ankle:
                self.create_bone(f'{prefix}Leg', knee, ankle, f'{prefix}UpLeg')
            else:
                ankle_calc = knee + Vector((0, 0, -self.analyzer.height * 0.25))
                self.create_bone(f'{prefix}Leg', knee, ankle_calc, f'{prefix}UpLeg')
                ankle = ankle_calc

            # Foot
            if foot:
                self.create_bone(f'{prefix}Foot', ankle, foot, f'{prefix}Leg')

                # Toe
                if toe:
                    self.create_bone(f'{prefix}ToeBase', foot, toe, f'{prefix}Foot')

            print(f"  Created {side} leg bones")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fbx_path = os.path.join(script_dir, FBX_FILE)

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
        if argv:
            fbx_path = argv[0]

    print("\n" + "=" * 60)
    print("Complete Auto Rig Generator")
    print("=" * 60)
    print(f"Input: {fbx_path}")

    if not os.path.exists(fbx_path):
        print(f"Error: File not found - {fbx_path}")
        return

    # Clear scene
    print("\n[1/5] Clearing scene...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean up orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)

    # Import FBX
    print("\n[2/5] Importing FBX...")
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    # Find mesh
    mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh_obj = obj
            break

    if not mesh_obj:
        print("Error: No mesh found")
        return

    print(f"Found mesh: {mesh_obj.name}")

    # Analyze mesh
    print("\n[3/5] Analyzing mesh geometry...")
    analyzer = MeshAnalyzer(mesh_obj)
    body_data = analyzer.analyze_body()

    # Create new armature
    print("\n[4/5] Building skeleton...")

    # Create armature object
    armature_data = bpy.data.armatures.new('Skeleton')
    armature_obj = bpy.data.objects.new('Armature', armature_data)
    bpy.context.collection.objects.link(armature_obj)

    # Build skeleton
    builder = SkeletonBuilder(armature_obj, body_data, analyzer)

    print("\n  Building spine...")
    builder.build_spine()

    print("\n  Building arms...")
    builder.build_arms()

    print("\n  Building legs...")
    builder.build_legs()

    # Setup armature modifier and auto weights
    print("\n[5/5] Setting up weights...")

    # Add armature modifier
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature_obj

    # Parent mesh to armature with auto weights
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.select_all(action='DESELECT')
    armature_obj.select_set(True)
    mesh_obj.select_set(True)

    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        print("  Applied automatic weights")
    except Exception as e:
        print(f"  Warning: Could not apply auto weights: {e}")

    # Export
    output_path = fbx_path.replace('.fbx', '_autorig.fbx')
    print(f"\nExporting to: {output_path}")

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
    )

    print("\n" + "=" * 60)
    print("Done!")
    print(f"Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
