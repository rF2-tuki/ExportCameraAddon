bl_info = {
    "name": "Export rF2 camera",
    "author": "OpenAI",
    "version": (1, 0),
    "blender": (4, 0, 2),
    "location": "View3D > Sidebar > Camera Export",
    "description": "Export camera and child circle mesh data to a custom format",
    "category": "Import-Export",
}

import bpy
import math
import os
import mathutils
import pathlib
#for grid
import re
from collections import defaultdict

pi = math.pi

class ExportCameraSettings(bpy.types.PropertyGroup):

    LOD_val: bpy.props.FloatProperty(
        name="LOD multiplier",
        description="LOD Multiplier",
        default=1.0,
        min=0.1,
        max=6.0
    )
    use_path_main: bpy.props.BoolProperty(
        name="Main", 
        description="Enable on main path", 
        default=False
    )
    use_path_pit: bpy.props.BoolProperty(
        name="Pit", 
        description="Enable on pit path", 
        default=False
    )
    #set group
    group_1: bpy.props.BoolProperty(
    name="1", 
    description="Group1", 
    default=False
    )
    group_2: bpy.props.BoolProperty(
    name="2", 
    description="Group2", 
    default=False
    )
    group_3: bpy.props.BoolProperty(
    name="3", 
    description="Group3", 
    default=False
    )
    group_4: bpy.props.BoolProperty(
    name="4", 
    description="Group4", 
    default=False
    )
    #for movement camera
    export_controlpoint: bpy.props.BoolProperty(
    name="handle as movement",
    description="when checked camera is handled as movement.",
    default=False
    )
    movement_rate: bpy.props.FloatProperty(
    name="Movement Rate",
    description="Speed of movement",
    default=0.25,
    min=0.0,
    max=1.0
    )


class ExportTrackingCameraOperator(bpy.types.Operator):
    bl_idname = "export_scene.tracking_static_camera"
    bl_label = "Export"
    bl_description = "Export selected camera"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        default="camera_export.txt"
    )

    def execute(self, context):
        path = pathlib.Path(self.filepath)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        self.filepath = str(path)

        cam = context.object
        if not cam or cam.type != 'CAMERA':
            self.report({'ERROR'}, "Please select a camera object")
            return {'CANCELLED'}

        cam_name = cam.name
        cam_type = "Static" if cam_name.lower().startswith('s') else "Tracking"
        circles = [child for child in cam.children if child.type == 'MESH' and 'circle' in child.name.lower()]

        if not circles:
            self.report({'ERROR'}, "No child circle mesh found under the camera")
            return {'CANCELLED'}

        cam_loc = cam.location
        cam_rot_euler = cam.rotation_euler
        cam_rot_rad = tuple(cam_rot_euler)

        # Obtained from the camera body, such as FOV
        cam_data = cam.data
        fov_val = math.degrees(cam_data.angle)
        clip_start = cam_data.clip_start
        clip_end = cam_data.clip_end
        settings = context.scene.export_camera_settings
        LOD_val = settings.LOD_val
        main = settings.use_path_main
        pit = settings.use_path_pit

        if main and not pit:
            valid_path = 1
        elif pit and not main:
            valid_path = 2
        else:
            valid_path = 0
            
        # Groups（bit addition）
        group_val = 0
        if settings.group_1:
            group_val += 1
        if settings.group_2:
            group_val += 2
        if settings.group_3:
            group_val += 4
        if settings.group_4:
            group_val += 8
        if group_val == 0:
            group_val = 15 #when nothing are chosen set as all
            
        activation_lines = []
        for circle in circles:
            loc = circle.location
            radius = (circle.dimensions.x + circle.dimensions.y) / 4.0
            activation_lines.append(f"  ActivationLocation=({-loc.x:.6f}, {-loc.z:.6f}, {-loc.y:.6f})\n")
            activation_lines.append(f"  ActivationRadius=({radius:.6f})\n")

        LOD_val = context.scene.export_camera_settings.LOD_val
        settings = context.scene.export_camera_settings
        main = settings.use_path_main
        pit = settings.use_path_pit

        with open(self.filepath, 'w') as f:
            f.write(f"{cam_type}Cam={cam_name} \n")
            f.write("{\n")
            f.write(f"  Fov=(38.000000, {fov_val:.6f})\n")
            f.write("  Clear=FALSE\n")
            f.write("  Color=(0, 0, 0)\n")
            f.write(f"  ClipPlanes=({clip_start:.6f}, {clip_end:.6f})\n")
            f.write(f"  LODMultiplier=({LOD_val:.1f})\n")
            f.write("  Size=(1.000000, 1.000000)\n")
            f.write("  Center=(0.500000, 0.500000)\n")
            f.write("  MipmapLODBias=(1.000000)\n")
            f.write("  Flags1=(2)\n")
            f.write("  Flags2=(0)\n")
            f.write(f"  ValidPaths=({valid_path})\n")
            f.write("  SoundName=\"\"\n")
            f.write("  SoundParams=(1.000,1,15)\n")
            f.write("  MinShadowRange=(0.100)\n")
            f.write("  MaxShadowRange=(200.000)\n")
            f.write("  ShadowSplitRatio=(0.920)\n")
            f.write("  mPostProcessPresetIndex=(3)\n")
            for i in range(6):
                f.write("  ShadowParams=(0.000050,1.000,100.000)\n")
            f.write("  ShadowParams=(0.000050,1.000,0.000)\n")
            f.write("  ShadowParams=(0.000000,0.000,0.000)\n")
            f.write(f"  Position=({-cam_loc.x:.6f}, {-cam_loc.z:.6f}, {-cam_loc.y:.6f})\n")
            f.write(f"  Orientation=({cam_rot_rad[0]-pi/2:.6f}, {cam_rot_rad[2]:.6f}, {cam_rot_rad[1]:.6f})\n")

            for line in activation_lines:
                f.write(line)

            f.write("  ListenerVol=(1.200000)\n")
            f.write("  RainVol=(1.000000)\n")
            f.write(f"  Groups={group_val}\n")
            f.write("  TrackingRate=(30.0)\n")
            f.write("  PositionOffset=(0.000000, 0.000000, 0.000000)\n")
        # Use movement_rate only if export_controlpoint is enabled
            if settings.export_controlpoint:
                movement_rate_val = settings.movement_rate
            else:
                movement_rate_val = 0.0

            f.write(f"  MovementRate=({movement_rate_val:.6f})\n")
            f.write("  MinimumFOV=(10.000006)\n")
            f.write("  MaximumZoomFactor=(0.100000)\n")

            if settings.export_controlpoint:
                # Extract Plane.xxx out of camera children
                plane_children = []
                for child in cam.children:
                    if child.type == 'MESH' and child.name.startswith("Plane"):
                        # Collect child objects named "Plane" or "Plane.xxx"
                        suffix = child.name[5:]  # Portion after "Plane"
                        if suffix.startswith(".") and suffix[1:].isdigit():
                            number = int(suffix[1:])
                        elif suffix == "":
                            number = 0
                        else:
                            continue  # Skip if name is not in expected format, like "PlaneExtra"
                        plane_children.append((number, child))

                if not plane_children:
                    self.report({'ERROR'}, "Camera has no child objects named 'Plane.xxx'")
                    return {'CANCELLED'}
                    
                f.write("  MovementPath\n")
                f.write("  {\n")
                    
                # sort by number and output ControlPoint
                for _, plane_obj in sorted(plane_children, key=lambda x: x[0]):
                    loc = plane_obj.location
                    f.write(f"    ControlPoint=({-loc.x:.6f}, {-loc.z:.6f}, {-loc.y:.6f})\n")
                f.write("  }\n")
            f.write("}\n")

        self.report({'INFO'}, "Camera export successful")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class Camera_PT_ExportPanel(bpy.types.Panel):
    bl_label = "rF2 camera"
    bl_idname = "camera setting"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'rF2 camera'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_camera_settings
        layout.prop(settings, "LOD_val")
        #path activates cam
        layout.label(text="activate on:")
        row = layout.row(align=True)
        row.prop(settings, "use_path_main", toggle=True)
        row.prop(settings, "use_path_pit", toggle=True)
        #group
        layout.label(text="Groups:")
        row = layout.row(align=True)
        row.prop(settings, "group_1", toggle=True)
        row.prop(settings, "group_2", toggle=True)
        row.prop(settings, "group_3", toggle=True)
        row.prop(settings, "group_4", toggle=True)
        layout.prop(settings, "export_controlpoint")
        if settings.export_controlpoint:
            layout.prop(settings, "movement_rate")
        layout.operator("export_scene.tracking_static_camera")

class AddTriangleOperator(bpy.types.Operator):
    bl_idname = "object.add_triangle_at_cursor"
    bl_label = "Add Triangle"
    bl_description = "Add a triangle at the 3D cursor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mesh = bpy.data.meshes.new("TriangleMesh")
        obj = bpy.data.objects.new("[GRID]_Triangle", mesh)

        verts = [
            (0, -2.25, 0),
            (-1, 2.25, 0),
            (1, 2.25, 0)
        ]
        faces = [(0, 1, 2)]
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}
        
class ExportGridSettings(bpy.types.PropertyGroup):
    grid_z_offset: bpy.props.FloatProperty(
        name="Y Offset",
        description="Offset for Y (Blender Z) axis when exporting triangles",
        default=0.0,
        min=0.0,
        max=10.0
    )
    
class ExportGridDataOperator(bpy.types.Operator):
    bl_idname = "export_scene.grid_data"
    bl_label = "Export Grid Data"
    bl_description = "Export triangle-based grid data"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        default="grid_export.txt"
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        path = pathlib.Path(self.filepath)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        self.filepath = str(path)

        sections = {
            "grid": [],
            "altgrid": [],
            "teleport": [],
            "aux": [],
            "pits": defaultdict(lambda: {"pit": None, "garages": []}),
        }

        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            name = obj.name.lower()
            base_name = name.split('.')[0]  

            # インデックス抽出（grid.001 → 1、garage.001_2 → 1）
            match = re.search(r"\.(\d+)", name)
            index = int(match.group(1)) if match else 0

            # _nが付くか？ garage.001_2
            extra_gar_match = re.search(r"_(\d+)$", name)
            extra_suffix = int(extra_gar_match.group(1)) if extra_gar_match else None

            # 座標と回転の変換
            pos = obj.location
            rot = obj.rotation_euler
            conv_pos = (-pos.x, -pos.z, -pos.y)
            conv_rot = (rot.x - pi/2, rot.z, rot.y)

            if name.startswith("grid"):
                sections["grid"].append((index, conv_pos, conv_rot))

            elif name.startswith("altgrid"):
                sections["altgrid"].append((index, conv_pos, conv_rot))

            elif name.startswith("teleport"):
                sections["teleport"].append((index, conv_pos, conv_rot))

            elif name.startswith("aux"):
                sections["aux"].append((index, conv_pos, conv_rot))

            elif name.startswith("pit"):
                sections["pits"][index]["pit"] = (conv_pos, conv_rot)

            elif name.startswith("garage"):
                sections["pits"][index]["garages"].append((extra_suffix or 1, conv_pos, conv_rot))

        # 書き出し開始
        with open(self.filepath, 'w') as f:
            def write_section(title, data, index_name):
                f.write(f"[{title.upper()}]\n")
                for i, (idx, pos, ori) in enumerate(sorted(data, key=lambda x: x[0])):
                    f.write(f"{index_name}={idx}\n")
                    f.write(f"Pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f})\n")
                    f.write(f"Ori=({ori[0]:.3f},{ori[1]:.3f},{ori[2]:.3f})\n")
                f.write("\n")  # ← セクション末尾に空行（中身が空でも付ける）

            write_section("GRID", sections["grid"], "GridIndex")
            write_section("ALTGRID", sections["altgrid"], "GridIndex")
            write_section("TELEPORT", sections["teleport"], "GridIndex")

            # PITS
            f.write("[PITS]\n")
            any_written = False
            for team_index in sorted(sections["pits"].keys()):
                pit_data = sections["pits"][team_index]
                if pit_data["pit"]:
                    any_written = True
                    pit_pos, pit_ori = pit_data["pit"]
                    f.write(f"TeamIndex={team_index}\n")
                    f.write(f"PitPos=({pit_pos[0]:.3f},{pit_pos[1]:.3f},{pit_pos[2]:.3f})\n")
                    f.write(f"PitOri=({pit_ori[0]:.3f},{pit_ori[1]:.3f},{pit_ori[2]:.3f})\n")
                    for _, gar_pos, gar_ori in sorted(pit_data["garages"], key=lambda x: x[0]):
                        f.write(f"GarPos=({gar_pos[0]:.3f},{gar_pos[1]:.3f},{gar_pos[2]:.3f})\n")
                        f.write(f"GarOri=({gar_ori[0]:.3f},{gar_ori[1]:.3f},{gar_ori[2]:.3f})\n")
            f.write("\n")  # ← PITSも必ず空行

            write_section("AUX", sections["aux"], "LocationIndex")

        self.report({'INFO'}, "Grid data exported successfully.")
        return {'FINISHED'}
        
class Grid_PT_ExportPanel(bpy.types.Panel):
    bl_label = "rF2 Grid"
    bl_idname = "Grid_PT_setting"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'rF2 camera'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.add_triangle_at_cursor", text="Add Triangle")
        layout.operator("export_scene.grid_data", text="Export")

classes = [
    ExportCameraSettings,
    ExportTrackingCameraOperator,
    Camera_PT_ExportPanel,
    AddTriangleOperator,
    ExportGridSettings,
    ExportGridDataOperator,
    Grid_PT_ExportPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.export_camera_settings = bpy.props.PointerProperty(type=ExportCameraSettings)
    bpy.types.Scene.export_grid_settings = bpy.props.PointerProperty(type=ExportGridSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.export_camera_settings
    del bpy.types.Scene.export_grid_settings

if __name__ == "__main__":
    register()
