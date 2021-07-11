# import sys; import os; import bpy; import importlib
# mydir="S:\\eigenes\\Dokumente\\Blender\\python_scripts\\"
# mydir="C:\\Users\\danie\\Documents\\development\\github\\Blender_AddOn_WriteObjData\\"
# sys.path.append( mydir )
# import write_object_data
# write_object_data.register()
# write_object_data.unregister()
# importlib.reload(write_object_data)
# write_object_data.register()

# import sys; import os; import bpy; import importlib; mydir="C:\\Users\\danie\\Documents\\development\\github\\Blender_AddOn_WriteObjData\\"; sys.path.append( mydir ); import write_object_data; write_object_data.register()

# write_object_data.unregister(); importlib.reload(write_object_data); write_object_data.register()
#
# or
#
# load file in blender using
# filename="S:\\eigenes\\Dokumente\\Blender\\python_scripts\\addon_add_output_object_data.py"
# exec(compile(open(filename).read(), filename, 'exec'))




bl_info = {
	"name": "Write Object Data / Annotation / Ground Truth",
	"description": "Addon that allows to write object data to ",
	"author": "Daniel Baudisch",
	"version": (0, 1, 0),
	"blender": (2, 80, 0),
	"location": "Properties > Output Properties > Write Object Data; and Properties > Object Properties > Write Object Data",
	"warning": "", # used for warning icon and text in addons panel
	"wiki_url": "https://github.com/grandmasterb80/Blender_AddOn_WriteObjData",
	"tracker_url": "",
	"category": "Object"
}

from glob import glob
from pathlib import Path, PureWindowsPath
import os.path
import bpy
import webbrowser
import pprint
import json
import mathutils
import sys

from bpy.props import (StringProperty,
						BoolProperty,
						CollectionProperty,
						IntProperty,
						FloatProperty,
						FloatVectorProperty,
						EnumProperty,
						PointerProperty,
						)
from bpy.types import (Panel,
						Operator,
						AddonPreferences,
						UIList,
						PropertyGroup,
						FileSelectParams,
						)
from bpy_extras import (object_utils
						)

from bpy.app.handlers import persistent

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# \brief: Check if object v can be converted to a json object

def isJsonable(v):
	if isinstance( v, mathutils.Vector ):
		return True
	elif isinstance( v, mathutils.Matrix ):
		return True
	elif isinstance( v, bpy.types.bpy_prop_collection ):
		return True
	elif isinstance( v, bpy.types.CameraDOFSettings ):
		return True
	else:
		try:
			json.dumps(v)
			return True
		except:
			return False

# ------------------------------------------------------------------------
# \brief: Helper function to print an object to console

def dump_obj(obj):
	for attr in dir(obj):
		try:
			if ( attr[ :2 ] != "__" and attr[ -2: ] != "__" ) and ( not hasattr(attr, '__call__') ) and isJsonable( getattr(obj, attr) ):
				print("obj.%s = %r" % (attr, getattr(obj, attr)))
			else:
				print("(skipping) obj.%s = %r" % (attr, getattr(obj, attr)))
		except AttributeError:
			print("obj.%s not available" % attr)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# \brief: Class to define a single element in the write-object-data-list
# Each element consists of a pointer to the referenced object and its name.

class ListItem(PropertyGroup):
	"""Group of properties representing an item in the list."""

	objectPtr: PointerProperty(
		name="Object",
		type=bpy.types.Object
	)

	name: StringProperty(
		name="Name",
		description="Name of object",
		default="Untitled"
	)

# ------------------------------------------------------------------------
#    Enumeration of some options (mode has multiple use)
# ------------------------------------------------------------------------

mode_options = [
	("OFF", "Off / No Output", '', 0),
	("JSON", "Proprietary JSON", '', 1),
	("CSV", "Comma Separated Value (CSV)", '', 2),
	("VOC", "Pascal VOC", '', 3),
	("COCO", "COCO", '', 4)
]

coord_options = [
	("OBJ", "Object Coord", '', 0),
	("PAR", "(Highest) Parent Object Coord", '', 1),
	("CAM", "Camera Coord", '', 2),
	("WOR", "World Coord", '', 3),
	("ALL", "Parent, Camera and World", '', 4),
]

# ------------------------------------------------------------------------
#    Store properties for the "Output Object Data" in the active scene
# ------------------------------------------------------------------------

class WriteObjDataOutputPropertySettings(bpy.types.PropertyGroup):
	opt_writeObjData_Format : bpy.props.EnumProperty(
		name = "Format",
		items = mode_options,
		description = "If enabled, then data of objects for which Properties->Object Properties->Write Object Data->Enabled is selected, will be written in the selected format.",
		options = {'HIDDEN'},
		default = "OFF"
	)

	opt_writeObjData_Coord : bpy.props.EnumProperty(
		name = "Coord",
		items = coord_options,
		description = "Coordinates will transformed into the selected coordinate system before they are written to the target file.",
		options = {'HIDDEN'},
		default = "ALL"
	)

	opt_writeObjData_Filename : bpy.props.StringProperty(
		name = "Filename",
		description = "Name of files that will contain the object data",
		options = {'HIDDEN'},
		default = "obj_data"
	)

	opt_writeObjData_UseObjName : bpy.props.BoolProperty(
		name = "Use Object Name",
		description = "Object names will be used in the target file. If deselected, the object names will be simply enumerated names. The structure will have the object name as member in any case.",
		options = {'HIDDEN'},
		default = True
	)

# ------------------------------------------------------------------------
#    Store properties for the "Output Object Data" in the active scene
# ------------------------------------------------------------------------

class ObjWriteDataOptionsPropertySettings(bpy.types.PropertyGroup):
	def update_opt_writeObjDataObject(self, context):
		obj = context.object
		if obj:
			writeObjDataList = context.scene.writeObjDataList
			if obj.writeObjDataTab.opt_writeObjDataObject_Enabled:
				if self not in [sub.objectPtr for sub in writeObjDataList]:
					writeObjDataList.add()
					iii = writeObjDataList[ -1 ]
					iii.objectPtr = obj
					iii.name = obj.name
			else:
				index = 0
				for e in writeObjDataList:
					if e.objectPtr == obj:
						writeObjDataList.remove(index)
						return
					index = index + 1

	def ObjWriteDataOptionsUpdateSettings(self, context):
		obj = context.object
		if self.opt_writeObjDataObject_UseGlobal:
			print("Option enabled")
		else:
			print("Option disabled")

	opt_writeObjDataObject_Enabled : bpy.props.BoolProperty(
		name="Write Object Data",
		description="If enabled, then the object data of this object will be written to a CSV file. Remark: Properties->Output->Write Object Data->Write Object Data has to be enabled",
		default = True,
		options = {'HIDDEN'},
		update = update_opt_writeObjDataObject
	)

	opt_writeObjDataObject_UseGlobal : bpy.props.BoolProperty(
		name="Use Global Settings",
		description="If enabled, then the data that is written for this object is determined by the options in Properties > Output Properties > Write Object Data. If this option is not selected, the data that is written is determined by the options below.",
		default = True,
		options = {'HIDDEN'},
		update = ObjWriteDataOptionsUpdateSettings
	)

# ------------------------------------------------------------------------
#    Common properties for the "Write Object Data" for output and object property 
# ------------------------------------------------------------------------

class WriteObjDataOutputOptionsPropertySettings(bpy.types.PropertyGroup):
	opt_writeObjData_Location : bpy.props.BoolProperty(
		name="Location",
		description="Write the location of an oobject.",
		options = {'HIDDEN'},
		default = True
	)

	opt_writeObjData_Rotation : bpy.props.BoolProperty(
		name="Rotation",
		description="Write the rotation of an object.",
		options = {'HIDDEN'},
		default = True
	)

	opt_writeObjData_Scale : bpy.props.BoolProperty(
		name="Scale",
		description="Write the scale of an object.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_Dimensions : bpy.props.BoolProperty(
		name="Dimensions",
		description="Write the dimensions of an object.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_bb3d : bpy.props.BoolProperty(
		name="3D Bounding Box",
		description="Write 3D bounding box data of an object.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_bb2d : bpy.props.BoolProperty(
		name="2D Bounding Box",
		description="Write 2D bounding box data of an object (always in image coordinates).",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_bb3dWithChildren : bpy.props.BoolProperty(
		name="3D Bounding Box + Children",
		description="Write 3D bounding box data of the object including child objects. The BB3D will be align according to the parent orientation.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_bb2dWithChildren : bpy.props.BoolProperty(
		name="2D Bounding Box + Children",
		description="Write 2D bounding box data of the object including child objects (always in image coordinates). The BB surrounds all 2D BB of the object and its children objects.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_Animated : bpy.props.BoolProperty(
		name="Animated",
		description="Write animated data of an object.",
		options = {'HIDDEN'},
		default = False
	)

	opt_writeObjData_Camera : bpy.props.BoolProperty(
		name="Camera",
		description="Write camera specific data of a camera, i.e., focal length, aperture, type.",
		options = {'HIDDEN'},
		default = True
	)

	opt_writeObjData_Bones : bpy.props.BoolProperty(
		name="Bones",
		description="Write the bone data of an object.",
		options = {'HIDDEN'},
		default = False
	)

# ------------------------------------------------------------------------
#    UIList to list all the object for which the object data
#    will be written to a file.
# ------------------------------------------------------------------------

class OBJECT_UL_WriteObjList_Class(bpy.types.UIList):
	"""List of objects for which the object data has to be written to a table after each render."""

	# The draw_item function is called for each item of the collection that is visible in the list.
	#   data is the RNA object containing the collection,
	#   item is the current drawn item of the collection,
	#   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
	#   have custom icons ID, which are not available as enum items).
	#   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
	#   active item of the collection).
	#   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
	#   index is index of the current item in the collection.
	#   flt_flag is the result of the filtering process for this item.
	#   Note: as index and flt_flag are optional arguments, you do not have to use/declare them here if you don't
	#   need them.
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
		current_scene = data

		# We could write some code to decide which icon to use here...
		custom_icon = 'OUTLINER_COLLECTION'

		if item:
			# draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
			if self.layout_type in {'DEFAULT', 'COMPACT'}:
				# You should always start your row layout by a label (icon + text), or a non-embossed text field,
				# this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
				# We use icon_value of label, as our given icon is an integer value, not an enum ID.
				# Note "data" names should never be translated!
				layout.prop(item, "name", text="", emboss=False, icon_value=icon)
			# 'GRID' layout type should be as compact as possible (typically a single icon!).
			elif self.layout_type in {'GRID'}:
				layout.alignment = 'CENTER'
				layout.prop(item, "name", text="", emboss=False, icon_value=icon)

# ------------------------------------------------------------------------
#    Operator to add current selection to the list
# ------------------------------------------------------------------------

class OBJECT_UL_WriteObjList_AddSelection(Operator):
	"""Add current selection to the list."""
	bl_idname = "custom_def_list.add_selection"
	bl_label = "Add current selection"

	@classmethod
	def poll(cls, context):
		return context.selected_objects

	def execute(self, context):
		for obj in context.selected_objects:
			writeObjDataList = context.scene.writeObjDataList
			if obj not in [sub.objectPtr for sub in writeObjDataList]:
				writeObjDataList.add()
				newEl = writeObjDataList[ -1 ]
				newEl.objectPtr = obj
				newEl.name = obj.name
				newEl.objectPtr.writeObjDataTab.opt_writeObjDataObject_Enabled = True

		return{'FINISHED'} 

# ------------------------------------------------------------------------
#    Operator to delete an element from the list
# ------------------------------------------------------------------------

class OBJECT_UL_WriteObjList_DeleteItem(Operator):
	"""Delete the selected item from the list."""
	bl_idname = "custom_def_list.delete_item"
	bl_label = "Deletes an item"

	selection: bpy.props.EnumProperty(items=(('ALL', 'All', ""), ('SELECTION', 'Selection', ""),))

	@classmethod
	def poll(cls, context):
		return context.scene.writeObjDataList

	def execute(self, context):
		writeObjDataList = context.scene.writeObjDataList
		print ("writeObjDataList class", writeObjDataList.__class__.__name__)
		if self.selection == "ALL":
			while len( writeObjDataList ) > 0:
				writeObjDataList[0].objectPtr.writeObjDataTab.opt_writeObjDataObject_Enabled = False
				print( "OBJECT_UL_WriteObjList_DeleteItem(Operator): ", writeObjDataList[0].objectPtr.name )
				writeObjDataList.remove(0)
			context.scene.writeObjDataIndex = 0
		else:
			index = context.scene.writeObjDataIndex
			writeObjDataList[index].objectPtr.writeObjDataTab.opt_writeObjDataObject_Enabled = False
			print( "OBJECT_UL_WriteObjList_DeleteItem(Operator): ", writeObjDataList[index].objectPtr.name )
			writeObjDataList.remove(index)
			context.scene.writeObjDataIndex = min(max(0, index - 1), len(writeObjDataList) - 1)

		return{'FINISHED'} 

# ------------------------------------------------------------------------
#    Operator to move an element from the list
# ------------------------------------------------------------------------

class OBJECT_UL_WriteObjList_MoveItem(Operator):
	"""Move an item in the list."""
	bl_idname = "custom_def_list.move_item"
	bl_label = "Move an item in the list"

	direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))

	@classmethod
	def poll(cls, context):
		return context.scene.writeObjDataList

	def move_index(self):
		""" Move index of an item render queue while clamping it. """
		index = bpy.context.scene.writeObjDataIndex
		list_length = len(bpy.context.scene.writeObjDataList) - 1

		# (index starts at 0)
		new_index = index + (-1 if self.direction == 'UP' else 1)
		bpy.context.scene.writeObjDataIndex = max(0, min(new_index, list_length))

	def execute(self, context):
		writeObjDataList = context.scene.writeObjDataList
		index = context.scene.writeObjDataIndex
		neighbor = index + (-1 if self.direction == 'UP' else 1)
		writeObjDataList.move(neighbor, index)
		self.move_index()
		return{'FINISHED'}

# ------------------------------------------------------------------------
#    New options Properties->Output->Write Object Data
#    List of objects for which data has to be written.
#    This one defines the whole list element including
#    add / remove / invert options.
# ------------------------------------------------------------------------

class Panel_OutputOptions_WriteObjectData(Panel):
	"""Creates a Panel in the Output Properties window"""
	bl_idname = "OUTPUT_PT_WriteObjectData"
	bl_label = "Write Object Data"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	#bl_context = "scene"

	def draw(self, context):
		layout = self.layout
		scene = bpy.context.scene
		writeObjDataTab = scene.writeObjDataTab
		writeObjDataOpt = scene.writeObjDataOpt

		# display the properties
		layout.prop(writeObjDataTab, "opt_writeObjData_Format")

		h2 = layout.column()
		h2.prop(writeObjDataTab, "opt_writeObjData_Coord")
		h2.prop(writeObjDataTab, "opt_writeObjData_Filename")
		h2.prop(writeObjDataTab, "opt_writeObjData_UseObjName")

		# template_list now takes two new args.
		# The first one is the identifier of the registered UIList to use (if you want only the default list,
		# with no custom draw code, use "UI_UL_list").
		h2.template_list(
			"OBJECT_UL_WriteObjList_Class",
			"custom_def_list",
			scene,
			"writeObjDataList",
			scene,
			"writeObjDataIndex"
			)
	
		row = h2.row()
		#row.operator('writeObjDataList.new_item', text='NEW')
		row.operator('custom_def_list.delete_item', text='Rem All').selection = 'ALL'
		row.operator('custom_def_list.delete_item', text='Rem Sel').selection = 'SELECTION'
		row.operator('custom_def_list.add_selection', text='Add Sel')
		row.operator('custom_def_list.move_item', text='Mv Up').direction = 'UP'
		row.operator('custom_def_list.move_item', text='Mv Down').direction = 'DOWN'

		h2.active = writeObjDataTab.opt_writeObjData_Format != "OFF"
		h2.prop(writeObjDataOpt, "opt_writeObjData_Location")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Rotation")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Scale")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Dimensions")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb3d")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb2d")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb3dWithChildren")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb2dWithChildren")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Animated")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Camera")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Bones")


# ------------------------------------------------------------------------
#    New options Object Properties->Output Object Data->Write Object Data
#    List of objects for which data has to be written.
#    This one defines the whole list element including
#    add / remove / invert options.
# ------------------------------------------------------------------------

class Panel_ObjectOptions_WriteObjectData(Panel):
	"""Creates a Panel in the Object properties window"""
	bl_idname = "OBJECT_PT_WriteObjectData"
	bl_label = "Write Object Data"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "object"
	#bl_context = "scene"

	def draw(self, context):
		layout = self.layout
		obj = context.object
		scene = context.scene
		writeObjDataTab = obj.writeObjDataTab
		writeObjDataOpt = obj.writeObjDataOpt

		# display the properties
		layout.prop(writeObjDataTab, "opt_writeObjDataObject_Enabled")

		h1 = layout.column()
		h1.active = writeObjDataTab.opt_writeObjDataObject_Enabled
		h1.prop(writeObjDataTab, "opt_writeObjDataObject_UseGlobal")

		h2 = h1.column()
		h2.active = not writeObjDataTab.opt_writeObjDataObject_UseGlobal
		h2.prop(writeObjDataOpt, "opt_writeObjData_Location")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Rotation")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Scale")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Dimensions")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb3d")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb2d")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb3dWithChildren")
		h2.prop(writeObjDataOpt, "opt_writeObjData_bb2dWithChildren")
		h2.prop(writeObjDataOpt, "opt_writeObjData_Animated")

		h3 = h2.column()
		h3.active = obj.type == 'CAMERA'
		h3.prop(writeObjDataOpt, "opt_writeObjData_Camera")

		h4 = h2.column()
		h4.active = obj.type == 'ARMATURE'
		h4.prop(writeObjDataOpt, "opt_writeObjData_Bones")

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# get all children from an object
# https://blenderartists.org/t/how-to-get-a-list-of-an-objects-children/465508

@persistent
def helper_getAllChildren( obj ):
	children = [ob for ob in bpy.data.objects if ob.parent == obj]
	subchildren = []
	for c in children:
		subchildren = subchildren + helper_getAllChildren(children)
	return children + subchildren

# returns the coordinates of the 2D bounding box for the given object in the current scene
@persistent
def helper_getBB2D( scene, cam, obj ):
	bb3d = obj.bound_box
	bb3d_list = [ mathutils.Vector( p ) for p in bb3d ]
	coords_2d = [ object_utils.world_to_camera_view( scene, cam, obj.matrix_world @ p ) for p in bb3d_list ]
	xx = [ p.x for p in coords_2d ]
	yy = [ p.y for p in coords_2d ]
	return ( min( xx ), min( yy ), max( xx ), max( yy ) )

# ------------------------------------------------------------------------

@persistent
def remove_from_obj_write_data_list(context, obj):
	print ("remove_from_obj_write_data_list")
	writeObjDataList = context.scene.writeObjDataList
	index = 0
	for e in writeObjDataList:
		if e.objectPtr == obj:
			writeObjDataList.remove(index)
			return
		index = index + 1

class object_delete_override(bpy.types.Operator):
	"""delete objects and their derivatives"""
	bl_idname = "object.delete"
	bl_label = "Object Delete Operator"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		for obj in context.selected_objects:
			# replace with your function:
			remove_from_obj_write_data_list(context, obj)
		bpy.data.objects.remove(obj)
		return {'FINISHED'}

# ------------------------------------------------------------------------
# Functions compute the project matrix of a camera
# ------------------------------------------------------------------------
@persistent
def get_perspective( camera ):
    """Compute projection matrix of blender camera.

    Arguments:
        camera {bpy.types.Camera} -- Blender camera.

    Returns:
        mathutils.Matrix -- Projection matrix.
    """
    return camera.calc_matrix_camera(
        depsgraph=bpy.context.evaluated_depsgraph_get(),
        x=bpy.context.scene.render.resolution_x,
        y=bpy.context.scene.render.resolution_y,
        scale_x=bpy.context.scene.render.pixel_aspect_x,
        scale_y=bpy.context.scene.render.pixel_aspect_y)

# ------------------------------------------------------------------------
# Functions to handle start / post and complete handler
# ------------------------------------------------------------------------
@persistent
def write_object_data_start( scene ):
	print("---------------------------------------------------------------------------")
	print("---------------------------------------------------------------------------")
	print("---------------------------------------------------------------------------")
	print("---------------------------------------------------------------------------")
	print("START - START - START - START - START - START - START - START - START - START")
	print("Log: def write_object_data_start( scene ).")

@persistent
def helper_getFilename( basename, frameCounter, fileFormat ):
	formatMap = {
		"BMP": "bmp",
		"IRIS": "iris",
		"PNG": "png",
		"JPEG": "jpg",
		"JPEG2000": "jpg",
		"JPG": "jpg",
		"TARGA": "tga",
		"TARGA_RAW": "tga",
		"CINEON": "cin",
		"DPX": "dpx",
		"OPEN_EXR_MULTILAYER": "exr",
		"OPEN_EXR": "exr",
		"HDR": "hdr",
		"TIFF": "tiff",
		"AVI_JPEG": "avi",
		"AVI_RAW": "avi",
		"FFMPEG": "ffmpeg",
		"JSON": "json",
		"XML": "xml"
	}
	frameStr = '{:0>4}'.format( frameCounter )
	ext = formatMap[ fileFormat ]
	return bpy.path.ensure_ext( basename + frameStr + ".", ext )

@persistent
def helper_getPath( renderPathDrive, renderPath, path ):
	rp = os.path.dirname( renderPath )
	p = path
	if not os.path.dirname( p ):
		p = os.path.join( rp, p )
	( dr, pa ) = os.path.splitdrive( p )
	if not dr:
		p = os.path.join( renderPathDrive, p )
	return os.path.realpath( p )

@persistent
def helper_getFilesFromCompositorNode( mycd, frame_current, node : bpy.types.CompositorNodeOutputFile ):
	files = [ ]
	for value in node.file_slots.values():
		format = node.format.file_format if value.use_node_format else value.format.file_format
		f = helper_getFilename( value.path, frame_current, format )
		p = helper_getPath( mycd, node.base_path, f )
		files.append( p )
	return files

@persistent
def helper_mkJsonVectorFromVector3( vec3 ):
	return {
		"x" : vec3[0],
		"y" : vec3[1],
		"z" : vec3[2]
	}

@persistent
def helper_mkJsonArrayFromMatrix( matrix ):
	rowList = [list(row) for row in matrix]
	return rowList

@persistent
def helper_mkJsonDOFSetting( dofS ):
	jsonData = {
		"aperture_blades": dofS.aperture_blades,
		"aperture_fstop": dofS.aperture_fstop,
		"aperture_ratio": dofS.aperture_ratio,
		"aperture_rotation": dofS.aperture_rotation,
		"focus_distance": dofS.focus_distance,
		"use_dof": dofS.use_dof
	}
	return jsonData

@persistent
def helper_mkJsonBB3D( obj ):
	jsonData = {
	}
	bb3d = obj.objectPtr.bound_box
	pIndex = 0
	for p in bb3d:
		pointName = "p" + '{:0>1}'.format( pIndex )
		pIndex = pIndex + 1
		jsonData[ pointName ] = helper_mkJsonVectorFromVector3(p)
	return jsonData

@persistent
def helper_mkJsonBB2D( scene, cam, obj ):
	bb3d = obj.objectPtr.bound_box
	bb3d_list = [ mathutils.Vector( p ) for p in bb3d ]
	coords_2d = [ object_utils.world_to_camera_view( scene, cam, obj.objectPtr.matrix_world @ p ) for p in bb3d_list ]
	xx = [ p.x for p in coords_2d ]
	yy = [ p.y for p in coords_2d ]
	jsonData = {
		"x1" : min( xx ),
		"y1" : min( yy ),
		"x2" : max( xx ),
		"y2" : max( yy )
	}
	return jsonData

@persistent
def helper_mkJsonBB3DWithChildren( obj ):
	children = helper_getAllChildren( obj.objectPtr )
	obj_wm = obj.objectPtr.matrix_world.inverted()
	plist = []
	for c in children:
		bb3d_list = [ obj_wm @ c.matrix_world @ mathutils.Vector( p ) for p in c.bound_box ]
		plist = plist + bb3d_list
	xl = [ p.x for p in plist ]
	yl = [ p.y for p in plist ]
	zl = [ p.z for p in plist ]
	bb3d = [
		mathutils.Vector( ( min(xl), min(yl), min(zl) ) ),
		mathutils.Vector( ( min(xl), min(yl), max(zl) ) ),
		mathutils.Vector( ( min(xl), max(yl), max(zl) ) ),
		mathutils.Vector( ( min(xl), max(yl), min(zl) ) ),
		mathutils.Vector( ( max(xl), min(yl), min(zl) ) ),
		mathutils.Vector( ( max(xl), min(yl), max(zl) ) ),
		mathutils.Vector( ( max(xl), max(yl), max(zl) ) ),
		mathutils.Vector( ( max(xl), max(yl), min(zl) ) )
	]

	jsonData = {
	}
	pIndex = 0
	for p in bb3d:
		pointName = "p" + '{:0>1}'.format( pIndex )
		pIndex = pIndex + 1
		jsonData[ pointName ] = helper_mkJsonVectorFromVector3(p)
	return jsonData

@persistent
def helper_mkJsonBB2DWithChildren( scene, cam, obj ):
	children = helper_getAllChildren(obj.objectPtr)
	children.append( obj.objectPtr )
	l = [ helper_getBB2D( scene, cam, o ) for o in children ]
	x1l = [ x1 for (x1, _, _, _) in l ]
	y1l = [ y1 for (_, y1, _, _) in l ]
	x2l = [ x2 for (_, _, x2, _) in l ]
	y2l = [ y2 for (_, _, _, y2) in l ]
	jsonData = {
		"x1" : min( x1l ),
		"y1" : min( y1l ),
		"x2" : max( x2l ),
		"y2" : max( y2l )
	}
	return jsonData

@persistent
def helper_toJosn( v ):
	if isinstance( v, mathutils.Vector ):
		return helper_mkJsonVectorFromVector3( v )
	elif isinstance( v, mathutils.Matrix ):
		return helper_mkJsonArrayFromMatrix( v )
	elif isinstance( v, bpy.types.CameraDOFSettings ):
		return helper_mkJsonDOFSetting( v )
	elif isinstance( v, bpy.types.bpy_prop_collection ):
		nameList = []
		for i in range( len( v ) ):
			nameList.append( getattr( v[i], "name" ) )
		return nameList
	else:
		return v

@persistent
def helper_mkJsonFrumPyObj( obj ):
	jsonData = {
	}
	#print(" ***************** helper_mkJsonFrumPyObj( obj ) = ", obj)
	for attr in dir(obj):
		try:
			if ( attr[ :2 ] != "__" and attr[ -2: ] != "__" ) and ( not hasattr(attr, '__call__') ) and isJsonable( getattr(obj, attr) ):
				jsonData[ attr ] = helper_toJosn( getattr( obj, attr ) )
		except AttributeError:
			print( "obj.%s not available" % attr )
	return jsonData

@persistent
def helper_mkDictFromBones( bones ):
	jsonData = {
	}
	boneID = 0
	for v in bones.values():
		boneName = "bone_" + '{:0>4}'.format( boneID ) 
		boneID = boneID + 1
		jsonData[ boneName ] = helper_mkJsonFrumPyObj( v )
	return jsonData

@persistent
def helper_mkDictFromPose( pose ):
	jsonData = {
		"use_auto_ik" : pose.use_auto_ik,
		"use_mirror_relative" : pose.use_mirror_relative,
		"use_mirror_x" : pose.use_mirror_x,
		"bones" : helper_mkDictFromBones( pose.bones )
	}
	return jsonData

@persistent
def helper_mkDictFromCamera( camera ):
	#dump_obj( camera )
	return helper_mkJsonFrumPyObj( camera )

@persistent
def helper_mkJsonFromObjects( scene ):
	jsonData = {
	}
	#bpy.types.Scene.writeObjDataList
	#bpy.types.Scene.writeObjDataTab = PointerProperty(type=WriteObjDataOutputPropertySettings)
	#bpy.types.Scene.writeObjDataOpt = PointerProperty(type=WriteObjDataOutputOptionsPropertySettings)
	objID = 0
	targetCoords = scene.writeObjDataTab.opt_writeObjData_Coord
	useObjName = scene.writeObjDataTab.opt_writeObjData_UseObjName

	for obj in scene.writeObjDataList:
		if useObjName:
			objName = obj.objectPtr.name
		else:
			objName = "object_" + '{:0>4}'.format( objID ) 
		objID = objID + 1
		jsonData[ objName ] = {
			"name" : obj.objectPtr.name,
			"type" : obj.objectPtr.type
		}
		useGlobal = obj.objectPtr.writeObjDataTab.opt_writeObjDataObject_UseGlobal
		writeLocation = scene.writeObjDataOpt.opt_writeObjData_Location if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Location
		writeRotation = scene.writeObjDataOpt.opt_writeObjData_Rotation if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Rotation
		writeScale = scene.writeObjDataOpt.opt_writeObjData_Scale if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Scale
		writeDimensions = scene.writeObjDataOpt.opt_writeObjData_Dimensions if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Dimensions
		writeBB3D = scene.writeObjDataOpt.opt_writeObjData_bb3d if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_bb3d
		writeBB2D = scene.writeObjDataOpt.opt_writeObjData_bb2d if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_bb2d
		writebb3dWithChildren = scene.writeObjDataOpt.opt_writeObjData_bb3dWithChildren if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_bb3dWithChildren
		writebb2dWithChildren = scene.writeObjDataOpt.opt_writeObjData_bb2dWithChildren if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_bb2dWithChildren
		writeAnimated = scene.writeObjDataOpt.opt_writeObjData_Animated if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Animated
		writeBones = scene.writeObjDataOpt.opt_writeObjData_Bones if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Bones
		writeBones = writeBones and ( obj.objectPtr.type == "ARMATURE" )
		writeCamera = scene.writeObjDataOpt.opt_writeObjData_Camera if useGlobal else obj.objectPtr.writeObjDataOpt.opt_writeObjData_Camera
		writeCamera = writeCamera and ( obj.objectPtr.type == "CAMERA" )
		#
		#
		#
		# obj.calc_matrix_camera
		#
		# animation_data = None
		# animation_data_clear = <bpy_func Object.animation_data_clear()>
		# animation_data_create = <bpy_func Object.animation_data_create()>
		# animation_visualization = bpy.data.objects['Armature']...AnimViz
		# camera_fit_coords
		# make_local
		# mode
		# modifiers
		# matrix_basis, matrix_local, matrix_parent_inverse, matrix_world
		# pose
		# pose_library
		# rotation_axis_angle
		# type
		# up_axis
		# convert_space
		cams = bpy.data.cameras
		active_cam = bpy.context.scene.camera

		# print("**********************************************************************")
		# for a in bpy.data.armatures:
			# print(a.name)
			# #dump_obj(a)
		# print("**********************************************************************")
		# for a in bpy.data.objects:
			# #if a.type == "ARMATURE":
			# print(a.name, ", ", a.type)
			# #dump_obj(o)
		# print("**********************************************************************")
		if writeLocation:
			np = mathutils.Vector( (0.0, 0.0, 0.0) )
			nm = mathutils.Matrix.Identity(4)
			jsonData[ objName ][ "location" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.location )
			if targetCoords == "PAR" or targetCoords == "ALL":
				p = np
				m = nm
				co = obj.objectPtr
				while co.parent != None:
					p = co.matrix_local @ p
					m = co.matrix_local @ m
					co = co.parent
				jsonData[ objName ][ "location_sys_parent" ] = helper_mkJsonVectorFromVector3( p )
				jsonData[ objName ][ "transformation_sys_parent" ] = helper_mkJsonArrayFromMatrix( m )
			if targetCoords == "CAM" or targetCoords == "ALL":
				jsonData[ objName ][ "location_sys_cam" ] = helper_mkJsonVectorFromVector3( object_utils.world_to_camera_view( scene, active_cam, obj.objectPtr.matrix_world @ np ) )
				m1 = obj.objectPtr.matrix_world
				m2 = active_cam.matrix_world.inverted()
				m3 = get_perspective( active_cam )
				m = mathutils.Matrix.Identity(4)
				m = m1 @ m
				m = m2 @ m
				m = m3 @ m
				jsonData[ objName ][ "transformation_sys_cam" ] = helper_mkJsonArrayFromMatrix( m  )
			if targetCoords == "WOR" or targetCoords == "ALL":
				jsonData[ objName ][ "location_sys_world" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.matrix_world @ np )
				jsonData[ objName ][ "transformation_sys_world" ] = helper_mkJsonArrayFromMatrix( obj.objectPtr.matrix_world )
		if writeRotation:
			jsonData[ objName ][ "rotation_mode" ] = obj.objectPtr.rotation_mode
			jsonData[ objName ][ "rotation_euler" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.rotation_euler )
			jsonData[ objName ][ "rotation_quaternion" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.rotation_quaternion )
		if writeScale:
			jsonData[ objName ][ "scale" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.scale )
		if writeDimensions:
			jsonData[ objName ][ "dimensions" ] = helper_mkJsonVectorFromVector3( obj.objectPtr.dimensions )
		if writeAnimated:
			print( "I will write the animated parameters for ", obj.objectPtr.name )
		if writeBB3D:
			jsonData[ objName ][ "bb3d" ] = helper_mkJsonBB3D( obj )
		if writeBB2D:
			jsonData[ objName ][ "bb2d" ] = helper_mkJsonBB2D( scene, active_cam, obj )
		if writebb3dWithChildren:
			jsonData[ objName ][ "bb3dWithChildren" ] = helper_mkJsonBB3DWithChildren( obj )
		if writebb2dWithChildren:
			jsonData[ objName ][ "bb2dWithChildren" ] = helper_mkJsonBB2DWithChildren( scene, active_cam, obj )
		if writeBones:
			# check obj.objectPtr.find_armature()
			jj = helper_mkDictFromPose( obj.objectPtr.pose )
			jsonData[ objName ][ "pose" ] = jj
			# print ( "*******************************************************" )
			# json.dump( jj, sys.stdout, indent = 4 )
			# print ( "*******************************************************" )
			# for a in bpy.data.armatures:
				# if a == obj.objectPtr or a.parent == obj.objectPtr:
					# armature = a
			# if armature is not None:
				# jsonData[ objName ][ "bones" ] = helper_mkDictFromBones( armature.bones )
		if writeCamera:
			jsonData[ objName ][ "cameras" ] = helper_mkDictFromCamera( cams[ obj.objectPtr.name ] )

	return jsonData

@persistent
def write_object_data( scene ):
	# current camera: scene.camera
	# current frame:  scene.frame_current
	# first frame:  scene.frame_start
	# last frame:  scene.frame_end
	# step size:  scene.frame_step
	print("---------------------------------------------------------------------------")
	print("WRITE - WRITE - WRITE - WRITE - WRITE - WRITE - WRITE - WRITE - WRITE - WRITE")
	print("scene.writeObjDataTab.opt_writeObjData_Format = ", scene.writeObjDataTab.opt_writeObjData_Format)
	print("scene.writeObjDataTab.opt_writeObjData_Coord = ", scene.writeObjDataTab.opt_writeObjData_Coord)
	frame_start = scene.frame_start
	frame_last = scene.frame_end
	frame_current = scene.frame_current

	# print("Log: def write_object_data_data( scene ).")
	renderFileName = scene.render.frame_path(frame = frame_current)
	( mycd, renderFilePath ) = os.path.splitdrive( renderFileName )

	# create a list of all render output files (includes
	# the files created by compositor nodes)
	fileOutputNodes = [ c for c in scene.node_tree.nodes if c.bl_idname == "CompositorNodeOutputFile" ]
	fileList = [ renderFileName ]
	for node in fileOutputNodes:
		fileList += helper_getFilesFromCompositorNode( mycd, frame_current, node )

	if scene.writeObjDataTab.opt_writeObjData_Format == "OFF":
		# nothing to do
		pass
	elif scene.writeObjDataTab.opt_writeObjData_Format == "JSON":
		objectData = helper_mkJsonFromObjects( scene )
		jsonData = {
			"frame" :
				{
					"frame_current" : frame_current,
					"render_file" : renderFileName,
					"files" : fileList,
					"objects" : objectData
				}
		}
		targetFileName = helper_getFilename( scene.writeObjDataTab.opt_writeObjData_Filename, frame_current, "JSON" )
		targetFile = helper_getPath( mycd, renderFilePath, targetFileName )
		print( "Writing object data in JSON to \"", targetFile, "\"" )
		with open( targetFile, 'w') as outfile:
			json.dump( jsonData, outfile, indent = 4 )
	elif scene.writeObjDataTab.opt_writeObjData_Format == "CSV":
		print( "CSV object data output not implemented, yet" )
	elif scene.writeObjDataTab.opt_writeObjData_Format == "VOC":
		print( "VOC object data output not implemented, yet" )
	elif scene.writeObjDataTab.opt_writeObjData_Format == "COCO":
		print( "COCO object data output not implemented, yet" )
	else:
		print( "Unknown object data output %. Please contact developer.", scene.writeObjDataTab.opt_writeObjData_Format )

@persistent
def write_object_data_end( scene ):
	print("---------------------------------------------------------------------------")
	print("COMPLETE - COMPLETE - COMPLETE - COMPLETE - COMPLETE - COMPLETE - COMPLETE - COMPLETE")
	frame_start = scene.frame_start
	frame_last = scene.frame_end
	frame_current = scene.frame_current
	print("Log: def write_object_data_end( scene ). Frames [", frame_start, ", ", frame_last, "]; current = ", frame_current)

# ------------------------------------------------------------------------
#     Registration
# ------------------------------------------------------------------------

classes = (
	ListItem,
	OBJECT_UL_WriteObjList_Class,
	OBJECT_UL_WriteObjList_DeleteItem,
	OBJECT_UL_WriteObjList_AddSelection,
	OBJECT_UL_WriteObjList_MoveItem,
	WriteObjDataOutputPropertySettings,
	ObjWriteDataOptionsPropertySettings,
	WriteObjDataOutputOptionsPropertySettings,
	Panel_OutputOptions_WriteObjectData,
	Panel_ObjectOptions_WriteObjectData,
	object_delete_override
)

def register():
	from bpy.utils import register_class

	for cls in classes:
		register_class(cls)

	# register 'on render' handler
	# bpy.app.handlers.render_write.append(write_object_data)
	# bpy.app.handlers.render_pre.append(write_object_data_start)
	bpy.app.handlers.render_init.append(write_object_data_start)
	bpy.app.handlers.render_complete.append(write_object_data_end)
	bpy.app.handlers.render_post.append(write_object_data)
	# bpy.app.handlers.frame_change_pre.append(my_handler)

	bpy.types.Scene.writeObjDataTab = PointerProperty(type=WriteObjDataOutputPropertySettings)
	bpy.types.Scene.writeObjDataOpt = PointerProperty(type=WriteObjDataOutputOptionsPropertySettings)
	bpy.types.Scene.writeObjDataList = CollectionProperty(type = ListItem)
	bpy.types.Scene.writeObjDataIndex = IntProperty(name = "Index for writeObjDataList", default = 0)

	bpy.types.Object.writeObjDataTab = PointerProperty(type=ObjWriteDataOptionsPropertySettings)
	bpy.types.Object.writeObjDataOpt = PointerProperty(type=WriteObjDataOutputOptionsPropertySettings)


def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)

	handler_list = [
		bpy.app.handlers.render_init,
		bpy.app.handlers.render_write,
		bpy.app.handlers.render_complete,
		bpy.app.handlers.render_pre,
		bpy.app.handlers.render_post,
		bpy.app.handlers.frame_change_pre
	]
	handler_fns = [
		write_object_data_start,
		write_object_data,
		write_object_data_end
	]
	for fn in handler_fns:
		for hn in handler_list:
			if fn in hn:
				hn.remove( fn )

	del bpy.types.Object.writeObjDataTab

	del bpy.types.Scene.writeObjDataList
	del bpy.types.Scene.writeObjDataIndex
	del bpy.types.Scene.writeObjDataTab


if __name__ == "__main__":
	register()
