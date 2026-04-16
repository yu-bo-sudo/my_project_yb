# -*- coding: utf-8 -*-
"""
Export FBX with materials preserved
"""

import bpy
import os

INPUT_FILE = r"五指绑骨_no_clipping.blend"


def find_mesh():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            return obj
    return None


def find_armature():
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def ensure_materials_exportable():
    """Make sure materials are exportable"""
    print("\n" + "=" * 50)
    print("Checking Materials for Export")
    print("=" * 50)

    mesh_obj = find_mesh()
    if not mesh_obj:
        print("No mesh found")
        return

    for i, slot in enumerate(mesh_obj.material_slots):
        if slot.material:
            mat = slot.material
            print(f"\nMaterial {i}: {mat.name}")

            # Ensure material has a diffuse color for FBX export
            if mat.use_nodes:
                # Find Principled BSDF or create one
                principled = None
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        principled = node
                        break

                if principled:
                    # Get base color from node
                    base_color = principled.inputs['Base Color'].default_value
                    # Also set diffuse color for compatibility
                    mat.diffuse_color = base_color
                    print(f"  Base color: {base_color}")
                else:
                    print("  No Principled BSDF found")
            else:
                print(f"  Not using nodes, diffuse color: {mat.diffuse_color}")


def export_fbx_with_materials(output_path):
    """Export FBX with all material settings"""
    print("\n" + "=" * 50)
    print("Exporting FBX with Materials")
    print("=" * 50)

    # Select all objects
    bpy.ops.object.select_all(action='SELECT')

    # Export settings for maximum compatibility
    bpy.ops.export_scene.fbx(
        filepath=output_path,

        # General
        use_selection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',

        # Axes
        axis_forward='-Z',
        axis_up='Y',

        # Objects
        object_types={'ARMATURE', 'MESH', 'LIGHT', 'CAMERA'},

        # Armature settings
        use_armature_deform_only=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',

        # Animation
        bake_anim=False,

        # Materials - IMPORTANT
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',  # 'OFF', 'FACE', 'EDGE'

        # Embed textures
        embed_textures=True,
        path_mode='COPY',  # 'AUTO', 'ABSOLUTE', 'RELATIVE', 'MATCH', 'STRIP', 'COPY'
        copy_textures=True,

        # Other
        batch_mode='OFF',
    )

    print(f"  Exported to: {output_path}")


def export_glb(output_path):
    """Export as GLB (glTF) - better material support"""
    print("\n" + "=" * 50)
    print("Exporting GLB (glTF)")
    print("=" * 50)

    try:
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format='GLB',
            use_selection=False,
            export_materials='EXPORT',
            export_colors=True,
            export_attributes=True,
            export_cameras=True,
            export_lights=True,
            export_extras=True,
        )
        print(f"  Exported to: {output_path}")
        return True
    except Exception as e:
        print(f"  GLB export failed: {e}")
        print("  (glTF addon may not be enabled)")
        return False


def main():
    print("\n" + "=" * 60)
    print("EXPORT WITH MATERIALS")
    print("=" * 60)

    # Open file
    script_dir = r"E:\xnrw\xuniren"
    blend_path = os.path.join(script_dir, INPUT_FILE)

    if os.path.exists(blend_path):
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        print(f"Opened: {blend_path}")
    else:
        print("Working with current scene")

    # Check materials
    ensure_materials_exportable()

    # Export FBX
    output_fbx = os.path.join(script_dir, "五指绑骨_final.fbx")
    export_fbx_with_materials(output_fbx)

    # Also try GLB (better for web/Unity/Unreal)
    output_glb = os.path.join(script_dir, "五指绑骨_final.glb")
    export_glb(output_glb)

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"\nExported files:")
    print(f"  FBX: {output_fbx}")
    print(f"  GLB: {output_glb}")
    print("\nNote: GLB format has better material compatibility")
    print("      for Unity, Unreal, and web applications.")


if __name__ == "__main__":
    main()
