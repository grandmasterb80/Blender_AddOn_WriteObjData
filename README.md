# Blender_AddOn_WriteObjData
Blender Plugin to write object data on render.

This creates ground truth / annotated data that can be used for further
processing, e.g. AI learning / applications.

The Addon will create entries in
* Properties > Output Properties > Write Object Data
** Format: Allows to enable and determine the targeted file format for the object data.
** Target coordinate system for the coordinates that have to be written. Original coordinates will always be written. This option allows to write the coordinate of an object in a differet coordinate system.
** Base name for the file that will be written.
** A list with objects for which data will be written.
** A set of options that allow to selected the data to be written to files. These options are valid for all the selected options and can be overwritten for individual objects in Object Properties > Write Object Data.
*** Write Object Data (only in Object Properties > Write Object Data; alternative way to (de-)select objects for writing data)
*** Use Global Settings (when selected, settings in Properties > Output Properties > Write Object Data are used; when deselected, settings in Object Properties > Write Object Data are used.)
*** location / position
*** rotation
*** scale
*** dimension
*** 3D bounding box
*** 2D bounding box (camera coordinates)
*** animation data
*** camera data (will be written only for camerass)
*** bones

# ToDo List
* Offer files written by CompositorNodeOutputFile as reference file in COCO file output
* Youtube Tutorial
