# import sys; import os; import bpy; import importlib
# mydir="S:\\eigenes\\Dokumente\\Blender\\python_scripts\\"
# mydir="C:\\Users\\danie\\Documents\\development\\github\\Blender_AddOn_WriteObjData\\"
# sys.path.append( mydir )
# import write_object_data
# write_object_data.register()
# write_object_data.unregister()
# importlib.reload(write_object_data)
# write_object_data.register()
# write_object_data.unregister(); importlib.reload(write_object_data); write_object_data.register()
#
# or
#
# load file in blender using
# filename="S:\\eigenes\\Dokumente\\Blender\\python_scripts\\addon_add_output_object_data.py"
# exec(compile(open(filename).read(), filename, 'exec'))




	# print("-------------------------------------------------")
	# print("my test function", self, context)
	# print("my test function", type(self), type(context.object))
	# print("my test function", obj.name)
	# for attr in dir(obj):
		# print("obj.%s = %r" % (attr, getattr(obj, attr) ) )
	# print("my test function", obj.name)
	# print("my test function", obj["opt_writeObjDataObject"])
	# print("my test function", obj.opt_writeObjDataObject)
	# print("my test function", obj.parent)
#
#
#
#

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

import bpy

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
						)

from bpy.app.handlers import persistent


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

def remove_from_obj_write_data_list(context, obj):
	print ("remove_from_obj_write_data_list")
	writeObjDataList = context.scene.writeObjDataList
	index = 0
	for e in writeObjDataList:
		if e.objectPtr == obj:
			writeObjDataList.remove(index)
			return
		index = index + 1

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

def update_opt_writeObjDataObject(self, context):
	obj = context.object
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

# ------------------------------------------------------------------------
#    Class to define a single element in the write-object-data-list
# ------------------------------------------------------------------------

class ListItem(PropertyGroup):
	"""Group of properties representing an item in the list."""

	#name = StringProperty() -> Instantiated by default
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
#    Store properties for the "Output Object Data" in the active scene
# ------------------------------------------------------------------------

class WriteObjDataOutputPropertySettings(bpy.types.PropertyGroup):
	mode_options = [
		("OFF", "Off / No Output", '', 0),
		("CSV", "Comma Separated Value (CSV)", '', 1),
		("VOC", "Pascal VOC", '', 2),
		("COCO", "COCO", '', 3)
	]

	opt_writeObjData_Format : bpy.props.EnumProperty(
		name = "Format",
		items = mode_options,
		description = "If enabled, then data of objects for which Properties->Object Properties->Write Object Data->Enabled is selected, will be written in the selected format.",
		options = {'HIDDEN'},
		default = "OFF"
	)

	coord_options = [
		("CAM", "Camera Coord", '', 0),
		("WOR", "World Coord", '', 1),
		("CAW", "Camera and World", '', 2),
	]

	opt_writeObjData_Coord : bpy.props.EnumProperty(
		name = "Coord",
		items = coord_options,
		description = "Coordinates will transformed into the selected coordinate system before they are written to the target file.",
		options = {'HIDDEN'},
		default = "CAM"
	)

# ------------------------------------------------------------------------
#    Store properties for the "Output Object Data" in the active scene
# ------------------------------------------------------------------------

class ObjWriteDataOptionsPropertySettings(bpy.types.PropertyGroup):
	opt_writeObjDataObject_Enabled : bpy.props.BoolProperty(
		name="Write Object Data",
		description="If enabled, then the object data of this object will be written to a CSV file. Remark: Properties->Output->Write Object Data->Write Object Data has to be enabled",
		default = True,
		update = update_opt_writeObjDataObject
		)

	opt_writeObjDataObject_Overwrite : bpy.props.BoolProperty(
		name="Overwrite Default Write Object Data",
		description="If enabled, then the data that is written for this object is determined by the options below. If this option is not selected, the data that is written is determined by the options in Properties->Output->Write Object Data",
		default = False
		)

# ------------------------------------------------------------------------
#    Common properties for the "Write Object Data" for output and object property 
# ------------------------------------------------------------------------

class WriteObjDataOutputOptionsPropertySettings(bpy.types.PropertyGroup):
	opt_writeObjData_Position : bpy.props.BoolProperty(
		name="Position",
		description="Write the position of an oobject.",
		default = True
	)

	opt_writeObjData_Rotation : bpy.props.BoolProperty(
		name="Rotation",
		description="Write the rotation of an object.",
		default = True
	)

	opt_writeObjData_Scale : bpy.props.BoolProperty(
		name="Scale",
		description="Write the scale of an object.",
		default = False
	)

	opt_writeObjData_Bones : bpy.props.BoolProperty(
		name="Bones",
		description="Write the bone data of an object.",
		default = False
	)

	opt_writeObjData_Animated : bpy.props.BoolProperty(
		name="Animated",
		description="Write animated data of an object.",
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

		# draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
		if self.layout_type in {'DEFAULT', 'COMPACT'}:
			# You should always start your row layout by a label (icon + text), or a non-embossed text field,
			# this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
			# We use icon_value of label, as our given icon is an integer value, not an enum ID.
			# Note "data" names should never be translated!
			if item:
				layout.prop(item, "name", text="", emboss=False, icon_value=icon)
				layout.label(text="vier fünf sechs", translate=False, icon_value=icon)
			else:
				layout.label(text="eins zwei drei", translate=False, icon_value=icon)
		# 'GRID' layout type should be as compact as possible (typically a single icon!).
		elif self.layout_type in {'GRID'}:
			layout.alignment = 'CENTER'
			layout.label(text="", icon_value=icon)

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
				iii = writeObjDataList[ -1 ]
				iii.objectPtr = obj
				iii.name = obj.name
				iii.objectPtr.writeObjDataTab.opt_writeObjDataObject_Enabled = True

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
			context.scene.custom_index = 0 
		else:
			index = context.scene.custom_index
			writeObjDataList[index].objectPtr.writeObjDataTab.opt_writeObjDataObject_Enabled = False
			print( "OBJECT_UL_WriteObjList_DeleteItem(Operator): ", writeObjDataList[index].objectPtr.name )
			writeObjDataList.remove(index)
			context.scene.custom_index = min(max(0, index - 1), len(writeObjDataList) - 1)

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
		index = bpy.context.scene.custom_index
		list_length = len(bpy.context.scene.writeObjDataList) - 1

		# (index starts at 0)
		new_index = index + (-1 if self.direction == 'UP' else 1)
		bpy.context.scene.custom_index = max(0, min(new_index, list_length))

	def execute(self, context):
		writeObjDataList = context.scene.writeObjDataList
		index = context.scene.custom_index
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
		#scn = bpy.data
		writeObjDataTab = scene.writeObjDataTab
		writeObjDataOpt = scene.writeObjDataOpt
		#objs = scn.objects

		# display the properties
		layout.prop(writeObjDataTab, "opt_writeObjData_Format")
		layout.prop(writeObjDataTab, "opt_writeObjData_Coord")

		# template_list now takes two new args.
		# The first one is the identifier of the registered UIList to use (if you want only the default list,
		# with no custom draw code, use "UI_UL_list").
		layout.template_list(
			"OBJECT_UL_WriteObjList_Class",
			"custom_def_list",
			scene,
			"writeObjDataList",
			scene,
			"custom_index"
			)
	
		row = layout.row()
		#row.operator('writeObjDataList.new_item', text='NEW')
		row.operator('custom_def_list.delete_item', text='Rem All').selection = 'ALL'
		row.operator('custom_def_list.delete_item', text='Rem Sel').selection = 'SELECTION'
		row.operator('custom_def_list.add_selection', text='Add Sel')
		row.operator('custom_def_list.move_item', text='Mv Up').direction = 'UP'
		row.operator('custom_def_list.move_item', text='Mv Down').direction = 'DOWN'

		layout.prop(writeObjDataOpt, "opt_writeObjData_Position")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Rotation")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Scale")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Bones")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Animated")

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

		row = layout.row()
		if obj is not None:
			row.label(text="Active object is: " + obj.name)
			row = layout.row()
			row.prop(obj, "name")

		# display the properties
		layout.prop(writeObjDataTab, "opt_writeObjDataObject_Enabled")
		layout.prop(writeObjDataTab, "opt_writeObjDataObject_Overwrite")

		layout.prop(writeObjDataOpt, "opt_writeObjData_Coord")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Position")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Rotation")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Scale")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Bones")
		layout.prop(writeObjDataOpt, "opt_writeObjData_Animated")

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

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
# ------------------------------------------------------------------------

@persistent
def write_object_data_start( scene ):
	print("Log: def write_object_data_start( scene ).")

@persistent
def write_object_data( scene ):
	if ( scene.writeObjDataTab.opt_writeObjData_Format != "OFF" ):
		print("Log: Writing object data")
		print("(C) Frame Change", scene.frame_current)
		print("(C) Load Handler:", bpy.data.filepath)
		for obj in bpy.data.objects:
			print( "(C) Name:", obj.name )
			print( "(C) Bound Box:", obj.bound_box )
			print( "(C) Dimensions:", obj.dimensions )
			print( "(C) Locataion:", obj.location )
			print( "(C) Rotation Euler:", obj.rotation_euler )
			print( "(C) Rotation Mode:", obj.rotation_mode )
			print( "(C) Rotation Quaternion:", obj.rotation_quaternion )
			print( "(C) Scale:", obj.scale )
			print( "(C) ------------" )
	else:
		print("Log: Writing object data disabled.")

@persistent
def write_object_data_end( scene ):
	print("Log: def write_object_data_end( scene ).")

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
	bpy.app.handlers.render_complete.append(write_object_data_end)
	bpy.app.handlers.render_pre.append(write_object_data_start)
	bpy.app.handlers.render_post.append(write_object_data)
	# bpy.app.handlers.frame_change_pre.append(my_handler)

	bpy.types.Scene.writeObjDataTab = PointerProperty(type=WriteObjDataOutputPropertySettings)
	bpy.types.Scene.writeObjDataOpt = PointerProperty(type=WriteObjDataOutputOptionsPropertySettings)
	bpy.types.Scene.writeObjDataList = CollectionProperty(type = ListItem)
	bpy.types.Scene.custom_index = IntProperty(name = "Index for writeObjDataList", default = 0)

	bpy.types.Object.writeObjDataTab = PointerProperty(type=ObjWriteDataOptionsPropertySettings)
	bpy.types.Object.writeObjDataOpt = PointerProperty(type=WriteObjDataOutputOptionsPropertySettings)


def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)

	if write_object_data in bpy.app.handlers.render_write:
		bpy.app.handlers.render_write.remove( write_object_data )
	if write_object_data in bpy.app.handlers.render_complete:
		bpy.app.handlers.render_complete.remove( write_object_data )
	if write_object_data in bpy.app.handlers.render_pre:
		bpy.app.handlers.render_pre.remove( write_object_data )
	if write_object_data in bpy.app.handlers.render_post:
		bpy.app.handlers.render_post.remove( write_object_data )
	if write_object_data in bpy.app.handlers.frame_change_pre:
		bpy.app.handlers.frame_change_pre.remove( write_object_data )

	del bpy.types.Object.writeObjDataTab

	del bpy.types.Scene.writeObjDataList
	del bpy.types.Scene.custom_index
	del bpy.types.Scene.writeObjDataTab


if __name__ == "__main__":
	register()
