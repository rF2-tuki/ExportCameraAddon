# Export rF2 Camera

A Blender add-on to export camera and child circle mesh data to a custom `.txt` format for use in **rFactor 2**.

## Features

- Exports selected camera object with its transformation data.
- Detects and exports child circle mesh objects as activation points.
- Outputs field of view (FOV), clipping planes, LOD multiplier, and various camera properties in the required format.
- Automatically converts orientation and position to match rFactor 2's coordinate system.
- Provides a user interface in the 3D View Sidebar (N-panel).

## Installation

1. Download or clone this repository.
2. Open Blender (version 4.0.2 or later).
3. Go to `Edit` > `Preferences` > `Add-ons` > `Install...`
4. Select the `ExportrF2camera.py` file.
5. Enable the add-on by checking the box next to **Export rF2 camera**.

## Usage

1. In the 3D Viewport, open the Sidebar (press `N`).
2. Navigate to the **rF2 camera** tab.
3. Select a camera object. Make sure its name is "static~" or "tracking~" and it has at least one child mesh named with "circle" in its name.
4. Adjust the parameters:
   - **FOV** (Field of View)
   - **Clip in** (near clipping distance)
   - **Clip Out** (far clipping distance)
   - **LOD multiplier** (Level of Detail multiplier)
5. Click **Export** and choose a location to save the `.txt` file.

## Notes

- Only camera objects are supported.
- Child meshes with "circle" in the name are treated as activation zones. Their locations and radii are exported.
- The orientation is converted to rFactor 2 format, assuming Blender's camera orientation as base.

## File Format

The exported file includes:

- Camera type (`Static` or `Tracking`)
- Position and orientation
- Camera settings (FOV, clipping, LOD)
- Activation locations and radii (from child circle meshes)
- Preset rF2 visual and shadow settings

## License

MIT License

---

© 2025 – Developed with ❤️ using Blender and Python.

