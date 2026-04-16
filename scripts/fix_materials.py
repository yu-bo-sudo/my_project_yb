# -*- coding: utf-8 -*-
"""
Fix material and render settings to display original colors
"""

import bpy
import os

INPUT_FILE = r"五指绑骨_no_clipping.blend"


def find_mesh():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            return obj
    return None


def check_materials():
    """Check existing materials in the scene"""
    print("\n" + "=" * 50)
    print("Checking Materials")
    print("=" * 50)

    materials = bpy.data.materials
    print(f"Total materials in scene: {len(materials)}")

    for mat in materials:
        print(f"\n  Material: {mat.name}")
        print(f"    Use nodes: {mat.use_nodes}")

        if mat.use_nodes and mat.node_tree:
            print(f"    Nodes: {len(mat.node_tree.nodes)}")
            for node in mat.node_tree.nodes:
                print(f"      - {node.type}: {node.name}")

                # Check for image textures
                if node.type == 'TEX_IMAGE':
                    if node.image:
                        print(f"        Image: {node.image.name}")
                        print(f"        Path: {node.image.filepath}")
                    else:
                        print(f"        Image: None")


def check_mesh_materials(mesh_obj):
    """Check materials assigned to mesh"""
    print("\n" + "=" * 50)
    print("Checking Mesh Materials")
    print("=" * 50)

    if not mesh_obj or mesh_obj.type != 'MESH':
        print("No mesh found")
        return

    # Check material slots
    print(f"\nMaterial slots: {len(mesh_obj.material_slots)}")

    for i, slot in enumerate(mesh_obj.material_slots):
        print(f"\n  Slot {i}: {slot.name}")
        if slot.material:
            mat = slot.material
            print(f"    Material: {mat.name}")
            print(f"    Diffuse color: {mat.diffuse_color}")
            print(f"    Use nodes: {mat.use_nodes}")


def setup_render_engine():
    """Setup render engine for better material display"""
    print("\n" + "=" * 50)
    print("Setting Up Render Engine")
    print("=" * 50)

    # Use Cycles for better material rendering
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128

    # Or use Eevee for faster preview
    # bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    print(f"  Render engine: {bpy.context.scene.render.engine}")
    print(f"  Samples: {bpy.context.scene.cycles.samples}")


def fix_materials(mesh_obj):
    """Fix materials to display colors correctly"""
    print("\n" + "=" * 50)
    print("Fixing Materials")
    print("=" * 50)

    if not mesh_obj:
        print("No mesh found")
        return

    # If mesh has no materials, check if there are any in the scene
    if len(mesh_obj.material_slots) == 0:
        print("  No material slots found")

        # Try to find any material with color
        for mat in bpy.data.materials:
            if mat.use_nodes:
                # Check for Principled BSDF
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        # Add this material to mesh
                        mesh_obj.data.materials.append(mat)
                        print(f"  Added material: {mat.name}")
                        break


def create_principled_material(name, base_color):
    """Create a principled BSDF material with a base color"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Get nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = base_color

    # Link nodes
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat


def setup_viewport_shading():
    """Setup viewport shading for material preview"""
    print("\n" + "=" * 50)
    print("Setting Up Viewport Shading")
    print("=" * 50)

    # Set viewport shading to Material Preview
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.shading.use_scene_lights = True
                    print(f"  Set viewport shading to: {space.shading.type}")


def extract_colors_from_fbx():
    """Try to extract original colors from FBX if available"""
    print("\n" + "=" * 50)
    print("Checking for Embedded Textures")
    print("=" * 50)

    # Check for packed images
    for img in bpy.data.images:
        print(f"  Image: {img.name}")
        print(f"    Packed: {img.packed_file is not None}")
        print(f"    Size: {img.size}")
        if img.filepath:
            print(f"    Path: {img.filepath}")


def setup_lighting():
    """Add proper lighting for rendering"""
    print("\n" + "=" * 50)
    print("Setting Up Lighting")
    print("=" * 50)

    # Check existing lights
    lights = [obj for obj in bpy.context.scene.objects if obj.type == 'LIGHT']
    print(f"  Existing lights: {len(lights)}")

    if len(lights) == 0:
        # Add a simple lighting setup
        # Key light
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
        key_light = bpy.context.object
        key_light.name = "KeyLight"
        key_light.data.energy = 3
        key_light.rotation_euler = (0.5, 0.5, 0)
        print("  Added key light")

        # Fill light
        bpy.ops.object.light_add(type='SUN', location=(-5, -5, 5))
        fill_light = bpy.context.object
        fill_light.name = "FillLight"
        fill_light.data.energy = 1
        print("  Added fill light")


def setup_camera():
    """Setup camera for rendering"""
    print("\n" + "=" * 50)
    print("Setting Up Camera")
    print("=" * 50)

    cameras = [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA']
    print(f"  Existing cameras: {len(cameras)}")

    if len(cameras) == 0:
        # Add camera
        bpy.ops.object.camera_add(location=(0, -2, 1))
        camera = bpy.context.object
        camera.rotation_euler = (1.4, 0, 0)
        bpy.context.scene.camera = camera
        print("  Added camera")


def render_preview(output_path):
    """Render a preview image"""
    print("\n" + "=" * 50)
    print("Rendering Preview")
    print("=" * 50)

    # Set render settings
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # Render
    bpy.ops.render.render(write_still=True)
    print(f"  Saved preview: {output_path}")


def main():
    print("\n" + "=" * 60)
    print("MATERIAL & RENDER FIX")
    print("=" * 60)

    # Open file
    script_dir = r"E:\xnrw\xuniren"

    import os
    blend_path = os.path.join(script_dir, INPUT_FILE)

    if os.path.exists(blend_path):
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        print(f"Opened: {blend_path}")
    else:
        print("Working with current scene")

    # Find mesh
    mesh_obj = find_mesh()
    if mesh_obj:
        print(f"Found mesh: {mesh_obj.name}")

    # Check materials
    check_materials()
    check_mesh_materials(mesh_obj)

    # Extract colors from FBX
    extract_colors_from_fbx()

    # Setup render
    setup_render_engine()

    # Fix materials
    fix_materials(mesh_obj)

    # Setup viewport
    setup_viewport_shading()

    # Setup scene
    setup_lighting()
    setup_camera()

    # Save
    output_path = os.path.join(script_dir, "五指绑骨_final.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "=" * 60)
    print("COMPLETED!")
    print("=" * 60)
    print(f"Saved to: {output_path}")
    print("\nTo view colors in Blender:")
    print("1. Open the file")
    print("2. In 3D viewport, click the rightmost sphere icon (Material Preview)")
    print("3. Or press Z key and select 'Material Preview'")


if __name__ == "__main__":
    main()
