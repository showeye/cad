"""Private offscreen Blender driver; invoked by cadkit.render, no dependency on a product."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MM = 0.001


def _linear(colour):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in colour)


def main():
    path = Path(sys.argv[sys.argv.index("--") + 1])
    data = json.loads(path.read_text())
    out = path.parent
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 40
    scene.cycles.use_denoising = True
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type != "CPU"
        if any(d.use for d in prefs.devices):
            scene.cycles.device = "GPU"
    except (TypeError, RuntimeError):
        pass
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("Soft studio")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.72, 0.72, 0.72, 1)
    bg.inputs[1].default_value = 0.35
    scene.world = world
    objects, materials = {}, {}
    for name, entry in data["parts"].items():
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([[v * MM for v in p] for p in entry["vertices"]], [], entry["faces"])
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        key = tuple(entry["colour"])
        if key not in materials:
            mat = bpy.data.materials.new(str(key))
            mat.use_nodes = True
            shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            shader.inputs["Base Color"].default_value = (*_linear(key), 1)
            shader.inputs["Roughness"].default_value = 0.38
            materials[key] = mat
        obj.data.materials.append(materials[key])
        obj.rotation_mode = "QUATERNION"
        objects[name] = obj

    floor_mat = bpy.data.materials.new("Warm paper")
    floor_mat.use_nodes = True
    shader = next(n for n in floor_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*_linear((0.949, 0.933, 0.898)), 1)
    shader.inputs["Roughness"].default_value = 0.85
    floor_z = min(v[2] for part in data["parts"].values() for v in part["vertices"]) * MM
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, floor_z - 0.0003))
    bpy.context.object.name = "Studio floor"
    bpy.context.object.data.materials.append(floor_mat)

    def area(name, location, power, size):
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.shape, light.size = power, "DISK", size
        obj = bpy.data.objects.new(name, light)
        obj.location = location
        obj.rotation_euler = (
            (Vector((0, 0, 0.045)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        )
        scene.collection.objects.link(obj)

    area("Key", (-0.19, -0.24, 0.38), 1.3, 0.25)
    area("Fill", (0.25, -0.05, 0.22), 0.6, 0.2)
    area("Rim", (0.02, 0.25, 0.3), 1.5, 0.2)
    camera = bpy.data.objects.new(
        "Presentation camera", bpy.data.cameras.new("Presentation camera")
    )
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = 0.001

    def view(location, target, scale, width=1600, height=1100):
        camera.location = location
        camera.rotation_euler = (
            (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = scale
        scene.render.resolution_x, scene.render.resolution_y = width, height

    presets = {
        "hero": ((-0.23, -0.34, 0.23), (0, 0, 0.055), 0.264),
        "front": ((0, -0.4, 0.1), (0, 0, 0.052), 0.215),
        "back": ((0.24, 0.32, 0.25), (0, 0, 0.05), 0.24),
        "top": ((-0.015, -0.045, 0.48), (0, 0, 0.035), 0.22),
        "mechanism": ((-0.17, -0.3, 0.25), (-0.024, 0, 0.037), 0.17),
    }
    for name, preset in presets.items():
        view(*preset)
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDER", name, flush=True)

    # All mesh vertices remain the original CAD tessellation. Only rigid matrices animate.
    view(*presets["hero"])
    scene.render.fps = 24
    previous = {}
    for i, frame in enumerate(data["poses"]):
        time = 1 + i * 2
        for name, matrix in frame.items():
            obj = objects[name]
            matrix = Matrix(matrix)
            matrix.translation *= MM
            location, rotation, scale = matrix.decompose()
            if name in previous:
                rotation.make_compatible(previous[name])
            previous[name] = rotation.copy()
            obj.location, obj.rotation_quaternion, obj.scale = location, rotation, scale
            obj.keyframe_insert(data_path="location", frame=time)
            obj.keyframe_insert(data_path="rotation_quaternion", frame=time)
    scene.frame_end = max(1, 1 + (len(data["poses"]) - 1) * 2)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "presentation.blend"))
    if data["poses"]:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 12
        scene.render.resolution_x, scene.render.resolution_y = 850, 610
        (out / "frames").mkdir(exist_ok=True)
        for i in range(len(data["poses"])):
            scene.frame_set(1 + i * 2)
            scene.render.filepath = str(out / "frames" / f"{i:03}.png")
            bpy.ops.render.render(write_still=True)
            print("FRAME", i, flush=True)


if __name__ == "__main__":
    main()
