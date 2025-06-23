bl_info = {
    "name": "Export rF2 camera",
    "author": "OpenAI",
    "version": (1, 5),
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

pi = math.pi

class ExportCameraSettings(bpy.types.PropertyGroup):
    fov_value: bpy.props.FloatProperty(
        name="FOV",
        description="Field of View",
        default=60.0,
        min=20.0,
        max=90.0,
    )
    clip_start: bpy.props.FloatProperty(
        name="Clip in",
        description="Near clipping plane",
        default=1.0,
        min=0.01,
        max=10.0
    )
    clip_end: bpy.props.FloatProperty(
        name="Clip Out",
        description="Far clipping plane",
        default=1500.0,
        min=0.01,
        max=10000.0
    )
    LOD_val: bpy.props.FloatProperty(
        name="LOD multiplier",
        description="LOD Multiplier",
        default=1.0,
        min=0.1,
        max=6.0
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

        activation_lines = []
        for circle in circles:
            loc = circle.location
            radius = (circle.scale.x + circle.scale.y) / 2.0
            activation_lines.append(f"  ActivationLocation=({-loc.x:.6f}, {-loc.z:.6f}, {-loc.y:.6f})\n")
            activation_lines.append(f"  ActivationRadius=({radius:.6f})\n")

        fov_val = context.scene.export_camera_settings.fov_value
        clip_start = context.scene.export_camera_settings.clip_start
        clip_end = context.scene.export_camera_settings.clip_end
        LOD_val = context.scene.export_camera_settings.LOD_val

        with open(self.filepath, 'w') as f:
            f.write(f"{cam_type}Cam={cam_name} \n")
            f.write("{\n")
            f.write("  Fov=(38.000000, {:.6f})\n".format(fov_val))
            f.write("  Clear=FALSE\n")
            f.write("  Color=(0, 0, 0)\n")
            f.write(f"  ClipPlanes=({clip_start:.6f}, {clip_end:.6f})\n")
            f.write(f"  LODMultiplier=({LOD_val:.6f})\n")
            f.write("  Size=(1.000000, 1.000000)\n")
            f.write("  Center=(0.500000, 0.500000)\n")
            f.write("  MipmapLODBias=(1.000000)\n")
            f.write("  Flags1=(2)\n")
            f.write("  Flags2=(0)\n")
            f.write("  ValidPaths=(1)\n")
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
            f.write("  Groups=15\n")
            f.write("  TrackingRate=(30.0)\n")
            f.write("  PositionOffset=(0.000000, 0.000000, 0.000000)\n")
            f.write("  MovementRate=(0.000000)\n")
            f.write("  MinimumFOV=(10.000006)\n")
            f.write("  MaximumZoomFactor=(0.100000)\n")
            f.write("}\n")

        self.report({'INFO'}, "Camera export successful")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CameraExportPanel(bpy.types.Panel):
    bl_label = "rF2 camera"
    bl_idname = "VIEW3D_PT_camera_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'rF2 camera'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_camera_settings
        layout.prop(settings, "fov_value")
        layout.prop(settings, "clip_start")
        layout.prop(settings, "clip_end")
        layout.prop(settings, "LOD_val")
        layout.operator("export_scene.tracking_static_camera")

classes = [
    ExportCameraSettings,
    ExportTrackingCameraOperator,
    CameraExportPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.export_camera_settings = bpy.props.PointerProperty(type=ExportCameraSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.export_camera_settings

if __name__ == "__main__":
    register()
