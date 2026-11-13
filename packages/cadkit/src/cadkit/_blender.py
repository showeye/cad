"""Private offscreen Blender driver; invoked by cadkit.render, no dependency on a product.

The payload may carry a "presentation" dictionary from the product (see cadkit.render). Every
key is optional; without it the scene, views and frame sizes are the original defaults.
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MM = 0.001

VIEWS = {  # location, target (m) and orthographic scale
    "hero": {"location": (-0.23, -0.34, 0.23), "target": (0, 0, 0.055), "scale": 0.264},
    "front": {"location": (0, -0.4, 0.1), "target": (0, 0, 0.052), "scale": 0.215},
    "back": {"location": (0.24, 0.32, 0.25), "target": (0, 0, 0.05), "scale": 0.24},
    "top": {"location": (-0.015, -0.045, 0.48), "target": (0, 0, 0.035), "scale": 0.22},
    "mechanism": {"location": (-0.17, -0.3, 0.25), "target": (-0.024, 0, 0.037), "scale": 0.17},
}
LIGHTS = [  # name, location (m), power (W), size (m)
    ("Key", (-0.19, -0.24, 0.38), 1.3, 0.25),
    ("Fill", (0.25, -0.05, 0.22), 0.6, 0.2),
    ("Rim", (0.02, 0.25, 0.3), 1.5, 0.2),
]


def _linear(colour):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in colour)


def _set(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def main():
    path = Path(sys.argv[sys.argv.index("--") + 1])
    data = json.loads(path.read_text())
    spec = data.get("presentation") or {}
    out = path.parent
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = spec.get("samples", 40)
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
    bg.inputs[0].default_value = (*spec.get("world", (0.72, 0.72, 0.72)), 1)
    bg.inputs[1].default_value = spec.get("world_strength", 0.35)
    scene.world = world

    # Materials: one per colour; a product may give roughness and clear coat by name prefix.
    overrides = spec.get("materials", {})
    objects, materials = {}, {}
    lowest = 0.0
    for name, entry in data["parts"].items():
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([[v * MM for v in p] for p in entry["vertices"]], [], entry["faces"])
        mesh.update()
        lowest = min(lowest, min(p[2] for p in entry["vertices"]))
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        look = next((v for k, v in overrides.items() if name.startswith(k)), {})
        colour = tuple(look.get("colour", entry["colour"]))
        roughness, coat = look.get("roughness", 0.38), look.get("coat", 0.0)
        key = colour if not look else (colour, roughness, coat)
        if key not in materials:
            mat = bpy.data.materials.new(str(key))
            mat.use_nodes = True
            shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            shader.inputs["Base Color"].default_value = (*_linear(colour), 1)
            shader.inputs["Roughness"].default_value = roughness
            if coat:
                _set(shader, ["Coat Weight", "Clearcoat"], coat)
                _set(shader, ["Coat Roughness", "Clearcoat Roughness"], 0.15)
            materials[key] = mat
        obj.data.materials.append(materials[key])
        obj.rotation_mode = "QUATERNION"
        objects[name] = obj

    # The floor lies just under the model's lowest point.
    floor_mat = bpy.data.materials.new("Warm paper")
    floor_mat.use_nodes = True
    shader = next(n for n in floor_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*_linear((0.949, 0.933, 0.898)), 1)
    shader.inputs["Roughness"].default_value = 0.85
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, lowest * MM - 0.0003))
    bpy.context.object.name = "Studio floor"
    bpy.context.object.data.materials.append(floor_mat)

    aim = Vector(spec.get("light_target", (0, 0, 0.045)))
    for name, location, power, size in spec.get("lights", LIGHTS):
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.shape, light.size = power, "DISK", size
        obj = bpy.data.objects.new(name, light)
        obj.location = location
        obj.rotation_euler = (aim - obj.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)

    camera = bpy.data.objects.new(
        "Presentation camera", bpy.data.cameras.new("Presentation camera")
    )
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = 0.001

    def pose(frame):
        """Place the parts as in pose `frame` of the payload (None: as built)."""
        moved = data["poses"][frame] if frame is not None else {}
        for name, obj in objects.items():
            matrix = Matrix(moved[name]) if name in moved else Matrix.Identity(4)
            matrix.translation *= MM
            location, rotation, scale = matrix.decompose()
            obj.location, obj.rotation_quaternion, obj.scale = location, rotation, scale
        bpy.context.view_layer.update()

    def hide(prefixes):
        for name, obj in objects.items():
            obj.hide_render = any(name.startswith(p) for p in prefixes)

    def view(preset, default_size=(1600, 1100)):
        width, height = preset.get("size", default_size)
        scene.render.resolution_x, scene.render.resolution_y = width, height
        if "location" in preset:
            camera.location = preset["location"]
            target = Vector(preset["target"])
            camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera.data.ortho_scale = preset["scale"]
            return
        # Fitted view: a direction, with centre and scale taken from what is in the picture.
        az, el = math.radians(preset["azimuth"]), math.radians(preset["elevation"])
        towards = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        camera.rotation_euler = (-towards).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        right = camera.matrix_world.to_3x3() @ Vector((1, 0, 0))
        up = camera.matrix_world.to_3x3() @ Vector((0, 1, 0))
        fit = preset.get("fit")
        corners = [
            obj.matrix_world @ Vector(corner)
            for name, obj in objects.items()
            if not obj.hide_render and (fit is None or any(name.startswith(p) for p in fit))
            for corner in obj.bound_box
        ]
        if "box" in preset:  # fixed framing in mm: (min corner, max corner)
            low, high = preset["box"]
            corners = [
                Vector((x * MM, y * MM, z * MM))
                for x in (low[0], high[0])
                for y in (low[1], high[1])
                for z in (low[2], high[2])
            ]
        across = [c.dot(right) for c in corners]
        tall = [c.dot(up) for c in corners]
        deep = [c.dot(towards) for c in corners]
        centre = (
            right * (min(across) + max(across)) / 2
            + up * (min(tall) + max(tall)) / 2
            + towards * (min(deep) + max(deep)) / 2
        )
        margin = preset.get("margin", 1.15)
        camera.location = centre + towards * 0.6
        wide, high = max(across) - min(across), max(tall) - min(tall)
        # the orthographic scale spans the longer side of the picture
        if width >= height:
            camera.data.ortho_scale = margin * max(wide, high * width / height)
        else:
            camera.data.ortho_scale = margin * max(high, wide * height / width)

    views = spec.get("views", VIEWS)
    for name, preset in views.items():
        pose(preset.get("frame"))
        hide(preset.get("hide", ()))
        view(preset)
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDER", name, flush=True)
    pose(None)
    hide(())

    # All mesh vertices remain the original CAD tessellation. Only rigid matrices animate.
    film = spec.get("animation", {})
    hide(film.get("hide", ()))
    view(views[film.get("view", "hero")])
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
    if data["poses"] and data.get("animate", True):
        scene.render.engine = "CYCLES"
        # the main film, then any further films of the same poses: other views, parts hidden
        films = {"frames": film}
        films.update({f"frames_{name}": extra for name, extra in spec.get("films", {}).items()})
        for folder, film in films.items():
            scene.frame_set(1)
            hide(film.get("hide", ()))
            view(views[film.get("view", "hero")])
            scene.cycles.samples = film.get("samples", 12)
            scene.render.resolution_x, scene.render.resolution_y = film.get("size", (850, 610))
            (out / folder).mkdir(exist_ok=True)
            for i in range(len(data["poses"])):
                scene.frame_set(1 + i * 2)
                scene.render.filepath = str(out / folder / f"{i:03}.png")
                bpy.ops.render.render(write_still=True)
                print("FRAME", folder, i, flush=True)


if __name__ == "__main__":
    main()
