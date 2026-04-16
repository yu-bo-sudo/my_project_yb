"""
Blender脚本：自动为3D人物模型添加手指关节骨骼绑定
适用于已有基础骨骼但缺少指关节的模型

使用方法：
blender --background --python auto_finger_rig.py -- <fbx_file_path>

或者在Blender脚本编辑器中直接运行
"""

import bpy
import math
from mathutils import Vector, Matrix
import sys
import os

# ============== 配置参数 ==============
FBX_FILE = "d641c0d695baef34532beb9539643e3f.fbx"  # 默认FBX文件名

# 手指配置
FINGER_CONFIG = {
    # 每根手指的名称前缀和关节数量
    'thumb': {'joints': 3, 'angle': -30},      # 拇指：3个关节
    'index': {'joints': 3, 'angle': 0},        # 食指：3个关节
    'middle': {'joints': 3, 'angle': 0},       # 中指：3个关节
    'ring': {'joints': 3, 'angle': 0},         # 无名指：3个关节
    'pinky': {'joints': 3, 'angle': 0},        # 小指：3个关节
}

# 手掌骨骼名称匹配模式（用于查找现有的手部骨骼）
HAND_BONE_PATTERNS = {
    'left': ['hand_l', 'hand_left', 'Hand_L', 'LeftHand', 'left_hand', 'L_hand'],
    'right': ['hand_r', 'hand_right', 'Hand_R', 'RightHand', 'right_hand', 'R_hand'],
}

# 手指相对于手掌的位置（用于自动定位）
FINGER_OFFSETS = {
    'thumb': {'x': -0.04, 'y': 0.01, 'z': 0.02},
    'index': {'x': -0.02, 'y': 0.0, 'z': 0.08},
    'middle': {'x': 0.0, 'y': 0.0, 'z': 0.09},
    'ring': {'x': 0.02, 'y': 0.0, 'z': 0.08},
    'pinky': {'x': 0.04, 'y': 0.0, 'z': 0.06},
}

# 每个手指关节的长度比例
JOINT_LENGTHS = {
    'thumb': [0.035, 0.025, 0.02],
    'index': [0.03, 0.025, 0.02],
    'middle': [0.032, 0.028, 0.022],
    'ring': [0.03, 0.025, 0.02],
    'pinky': [0.025, 0.02, 0.015],
}


def clear_scene():
    """清除场景中的所有对象"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 清除孤立数据
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)


def import_fbx(filepath):
    """导入FBX文件"""
    if not os.path.exists(filepath):
        print(f"错误：找不到FBX文件: {filepath}")
        return False

    bpy.ops.import_scene.fbx(filepath=filepath)
    print(f"成功导入FBX文件: {filepath}")
    return True


def find_armature():
    """查找场景中的骨架对象"""
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def find_hand_bones(armature, side):
    """查找手掌骨骼"""
    if not armature:
        return None

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = armature.data.edit_bones

    # 尝试匹配手掌骨骼名称
    for pattern in HAND_BONE_PATTERNS[side]:
        if pattern in edit_bones:
            bpy.ops.object.mode_set(mode='OBJECT')
            return edit_bones[pattern]

    # 如果找不到，尝试搜索包含hand和方向关键词的骨骼
    for bone in edit_bones:
        bone_name_lower = bone.name.lower()
        if 'hand' in bone_name_lower:
            if side == 'left' and ('l' in bone_name_lower or 'left' in bone_name_lower):
                bpy.ops.object.mode_set(mode='OBJECT')
                return bone
            elif side == 'right' and ('r' in bone_name_lower or 'right' in bone_name_lower):
                bpy.ops.object.mode_set(mode='OBJECT')
                return bone

    bpy.ops.object.mode_set(mode='OBJECT')
    return None


def create_finger_bones(armature, hand_bone, side, finger_name, config):
    """为单个手指创建骨骼链"""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = armature.data.edit_bones

    # 获取手掌骨骼的位置作为基准
    hand_head = hand_bone.head
    hand_tail = hand_bone.tail
    hand_matrix = hand_bone.matrix

    # 获取手指配置
    num_joints = config['joints']
    finger_angle = math.radians(config['angle'])

    # 获取偏移和长度
    offset = FINGER_OFFSETS[finger_name]
    lengths = JOINT_LENGTHS[finger_name]

    # 侧边标识
    side_suffix = '_l' if side == 'left' else '_r'

    # 计算手指起始位置
    finger_base = hand_head.copy()
    finger_base.x += offset['x'] * (-1 if side == 'left' else 1)
    finger_base.y += offset['y']
    finger_base.z += offset['z']

    # 创建手指骨骼链
    parent_bone = hand_bone
    created_bones = []

    for i in range(num_joints):
        # 骨骼名称
        joint_names = ['1', '2', '3']  # metacarpal, proximal, distal
        bone_name = f"{finger_name}{joint_names[i]}{side_suffix}"

        # 创建骨骼
        bone = edit_bones.new(bone_name)

        # 设置骨骼位置
        bone.head = finger_base.copy()

        # 计算尾部位置
        direction = Vector((0, -lengths[i], 0))

        # 应用手指角度旋转
        rot_matrix = Matrix.Rotation(finger_angle, 3, 'Z')
        direction = rot_matrix @ direction

        bone.tail = bone.head + direction

        # 设置父骨骼
        bone.parent = parent_bone
        bone.use_connect = (i > 0)  # 第一个骨骼不连接，后续骨骼连接到父骨骼

        # 更新下一个骨骼的起始位置
        finger_base = bone.tail.copy()
        parent_bone = bone

        created_bones.append(bone_name)

    bpy.ops.object.mode_set(mode='OBJECT')
    return created_bones


def create_all_finger_bones(armature):
    """为双手创建所有手指骨骼"""
    created_bones = {}

    for side in ['left', 'right']:
        hand_bone = find_hand_bones(armature, side)

        if hand_bone is None:
            print(f"警告：找不到{side}手的手掌骨骼，跳过")
            continue

        print(f"找到{side}手的手掌骨骼: {hand_bone.name}")

        side_bones = {}
        for finger_name, config in FINGER_CONFIG.items():
            bones = create_finger_bones(armature, hand_bone, side, finger_name, config)
            side_bones[finger_name] = bones
            print(f"  创建{side}手{finger_name}手指骨骼: {bones}")

        created_bones[side] = side_bones

    return created_bones


def auto_weight_paint(armature, mesh_obj):
    """自动为网格分配骨骼权重"""
    if not armature or not mesh_obj:
        return False

    # 选择网格对象
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)

    # 绑定骨架到网格
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # 使用自动权重绑定
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    print(f"已自动绑定 {mesh_obj.name} 到骨架 {armature.name}")
    return True


def find_mesh_objects():
    """查找场景中的所有网格对象"""
    return [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']


def setup_for_animation(armature):
    """设置骨架以便于动画"""
    if not armature:
        return

    # 设置骨架为姿态模式可用
    armature.data.pose_position = 'REST'

    # 为所有骨骼添加IK约束的准备工作
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # 可以在这里添加IK约束或其他动画设置

    bpy.ops.object.mode_set(mode='OBJECT')


def export_fbx(output_path):
    """导出为FBX文件"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        object_types={'ARMATURE', 'MESH'},
        use_armature_deform_only=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        embed_textures=False,
        path_mode='AUTO',
    )

    print(f"已导出到: {output_path}")


def main():
    """主函数"""
    # 获取FBX文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fbx_path = os.path.join(script_dir, FBX_FILE)

    # 检查命令行参数
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
        if argv:
            fbx_path = argv[0]

    print(f"\n{'='*50}")
    print("开始处理3D模型手指骨骼绑定")
    print(f"{'='*50}")
    print(f"FBX文件: {fbx_path}")

    # 检查文件是否存在
    if not os.path.exists(fbx_path):
        print(f"错误：FBX文件不存在: {fbx_path}")
        return

    # 清除场景
    print("\n1. 清除场景...")
    clear_scene()

    # 导入FBX
    print("\n2. 导入FBX文件...")
    if not import_fbx(fbx_path):
        return

    # 查找骨架
    print("\n3. 查找骨架...")
    armature = find_armature()
    if not armature:
        print("错误：未找到骨架对象")
        return
    print(f"找到骨架: {armature.name}")

    # 查找网格对象
    mesh_objects = find_mesh_objects()
    print(f"找到 {len(mesh_objects)} 个网格对象")

    # 创建手指骨骼
    print("\n4. 创建手指骨骼...")
    created_bones = create_all_finger_bones(armature)

    if not created_bones:
        print("警告：未能创建任何手指骨骼")
        print("尝试使用自动检测方法...")

        # 如果标准方法失败，尝试自动检测
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        # 列出所有骨骼帮助调试
        print("\n现有骨骼列表:")
        for bone in armature.data.edit_bones:
            print(f"  - {bone.name}")

        bpy.ops.object.mode_set(mode='OBJECT')

    # 设置动画
    print("\n5. 设置动画...")
    setup_for_animation(armature)

    # 导出结果
    print("\n6. 导出结果...")
    output_path = fbx_path.replace('.fbx', '_with_fingers.fbx')
    export_fbx(output_path)

    print(f"\n{'='*50}")
    print("处理完成!")
    print(f"输出文件: {output_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
