"""Blender side of the Serce na węgiel concept renders (run by Blender, not by uv).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        -P projects/serce/concept/render_blender.py -- [scene-name-prefix ...]

Reads concept/_build/scenes.json (written by look_concepts.py), renders every scene with Cycles
on a transparent film with a shadow catcher, and writes concept/_build/render/<scene>.png.
compose_sheets.py then puts the renders on the paper background and builds the sheets.

Materials are flat PLA: one colour per filament, no textures. Layer lines are not shown at this
stage; the concept renders are about form, colour and the opening, not print texture.
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BUILD = HERE / "_build"
OUT = BUILD / "render"
MM = 0.01  # Blender units per mm
FLOOR_Z = -17.4  # underside of the foot, mm

# filament: (sRGB hex, roughness, clear-coat weight)
MATERIALS = {
    "coal": ("#101012", 0.26, 0.35),  # standard black PLA: semi-gloss
    "coal_matte": ("#19191B", 0.72, 0.0),  # matte black PLA
    "honey": ("#EDAE1C", 0.48, 0.0),
    "lining": ("#EDAE1C", 0.48, 0.0),
    "bone": ("#ECE5D2", 0.50, 0.0),
    "tile": ("#B4502A", 0.48, 0.0),
}
SMOOTH = {"honey", "bone", "tile"}
RECOLOUR = {"ember": {"lining": "tile"}}  # scene-name suffix: material overrides

# name: (azimuth, elevation, distance mm, target mm, width px, height px, lens mm)
CAMERAS = {
    "hero": (-17, 13, 560, (0, 0, 36), 1400, 1200, 85),
    "back": (156, 13, 560, (0, 0, 34), 1100, 1100, 85),
    "strip": (-14, 12, 600, (0, 0, 33), 900, 900, 85),
    "strip_tall": (-14, 12, 700, (0, 0, 45), 900, 900, 85),
    "strip_wide": (-14, 24, 860, (0, 0, 26), 900, 900, 85),
    "counter": (-20, 42, 600, (0, 0, 34), 1100, 1100, 85),
    "counter_wide": (-20, 42, 860, (0, 0, 26), 1100, 1100, 85),
}


def linear(hex_colour):
    out = []
    for i in (1, 3, 5):
        c = int(hex_colour[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def make_material(name):
    colour, roughness, coat = MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    set_input(bsdf, ["Base Color"], linear(colour))
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Coat Weight", "Clearcoat"], coat)
    set_input(bsdf, ["Coat Roughness", "Clearcoat Roughness"], 0.12)
    return mat


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    try:
        scene.render.engine = "CYCLES"
    except TypeError as exc:
        print("engine:", exc)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            (prefs.refresh_devices if hasattr(prefs, "refresh_devices") else prefs.get_devices)()
            gpus = [dev for dev in prefs.devices if dev.type != "CPU"]
            if not gpus:
                continue
            for dev in prefs.devices:
                dev.use = dev.type != "CPU"
            scene.cycles.device = "GPU"
            break
        except (TypeError, RuntimeError):
            continue
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    for transform in ("Standard",):
        try:
            scene.view_settings.view_transform = transform
        except TypeError as exc:
            print("view transform:", exc)

    # world: soft vertical gradient so that every coal facet reflects a different grey
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    scene.world = world
    nodes, links = world.node_tree.nodes, world.node_tree.links
    background = next(n for n in nodes if n.type == "BACKGROUND")
    coords = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.04, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.9, 0.9, 0.92, 1)
    links.new(coords.outputs["Generated"], split.inputs[0])
    links.new(split.outputs[2], ramp.inputs[0])
    links.new(ramp.outputs[0], background.inputs[0])
    background.inputs[1].default_value = 0.9

    def area(name, location, size, power, target=(0, 0, 0.35)):
        data = bpy.data.lights.new(name, "AREA")
        data.size, data.energy = size, power
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        direction = Vector(target) - Vector(location)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)

    area("key", (-3.2, -3.4, 4.2), 3.0, 420)
    area("fill", (4.2, -2.6, 1.6), 4.0, 110)
    area("rim", (1.8, 4.2, 3.2), 2.0, 260)
    area("top", (0.0, -0.4, 5.5), 5.0, 160)

    floor_mesh = bpy.data.meshes.new("floor")
    r = 60.0
    floor_mesh.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("floor", floor_mesh)
    floor.location = (0, 0, FLOOR_Z * MM)
    floor.is_shadow_catcher = True
    scene.collection.objects.link(floor)

    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera, {name: make_material(name) for name in MATERIALS}


def aim(scene, camera, preset):
    azimuth, elevation, distance, target, width, height, lens = CAMERAS[preset]
    az, el = math.radians(azimuth), math.radians(elevation)
    target = Vector(target) * MM
    offset = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    camera.location = target + offset * distance * MM
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = lens
    camera.data.clip_start, camera.data.clip_end = 0.05, 200
    scene.render.resolution_x, scene.render.resolution_y = width, height


def render(scene, camera, materials, entry):
    made = []
    swap = next((v for k, v in RECOLOUR.items() if entry["name"].endswith(k)), {})
    for material, path in entry["files"].items():
        before = set(bpy.data.objects)
        bpy.ops.wm.stl_import(filepath=path, global_scale=MM)
        for obj in set(bpy.data.objects) - before:
            obj.data.materials.append(materials[swap.get(material, material)])
            if material in SMOOTH:
                obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
                try:
                    obj.data.set_sharp_from_angle(angle=math.radians(32))
                except AttributeError:
                    pass
            made.append(obj)
    aim(scene, camera, entry["camera"])
    scene.render.filepath = str(OUT / f"{entry['name']}.png")
    bpy.ops.render.render(write_still=True)
    for obj in made:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(mesh)


if __name__ == "__main__":
    wanted = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    manifest = json.loads((BUILD / "scenes.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    scene, camera, materials = setup_scene()
    for name, entry in manifest.items():
        if wanted and not any(name.startswith(w) for w in wanted):
            continue
        render(scene, camera, materials, entry)
        print("rendered", name)
