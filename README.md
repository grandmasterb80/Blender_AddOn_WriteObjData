# Blender_AddOn_WriteObjData
Blender Plugin to write object data on render.

This creates ground truth / annotated data that can be used for further
processing, e.g. AI learning / applications.

The Addon will create entries in
* Properties > Output Properties > Write Object Data
** Format: Allows to enable and determine the targeted file format for the object data.
** A set of options that allow to selected the data to be written to files
*** position
*** rotation
*** scale
*** bones
*** 3D bounding box
*** 2D bounding box (camera coordinates)
** A list with objects for which data will be written.
* Properties > Object Properties > Write Object Data

# ToDo Liste
* Offer files written by CompositorNodeOutputFile as reference file in COCO file output
* Youtube Tutorial