import sys
from PySide import QtCore, QtGui
import maya.cmds as cmds
import maya.mel as mel
 
class AnimCurveToolbox(QtGui.QMainWindow):
	def __init__(self):
		super(AnimCurveToolbox, self).__init__()
		self.__build_ui()
	#end
 
	def __get_curve_type(self):
		return self.cb_create_type.currentText()
	#end
 
	def __create_curve(self):
		desired_name = mel.eval('formValidObjectName(\"{0}\");'.format(self.txt_create_name.text()))
 
		# defaultObject is what formValidObjectName returns for empty strings
		if (desired_name == 'defaultObject') or cmds.objExists(desired_name):
			cmds.warning('Node already exists.')
			return
 
		cmds.createNode(self.__get_curve_type(), name=desired_name)
 
		self.txt_create_name.setText('')
	#end
 
	def __add_keyframe(self):
		curve_obj = self.cb_edit_curve.currentText()
		if (not len(curve_obj)) or (not cmds.objExists(curve_obj)):
			cmds.warning('Object does not exist.')
			return
 
		# get input value
		result = cmds.promptDialog(title='AnimCurveToolbox',
			message='Input (float/time):', button=['OK', 'Cancel'], defaultButton='OK',
			cancelButton='Cancel', dismissString='Cancel')
		if result == 'Cancel':
			cmds.warning('User canceled.')
			return
		input_value = cmds.promptDialog(query=True, text=True)
 
		# get value
		result = cmds.promptDialog(title='AnimCurveToolbox',
			message='Value (float):', button=['OK', 'Cancel'], defaultButton='OK',
			cancelButton='Cancel', dismissString='Cancel')
		if result == 'Cancel':
			cmds.warning('User canceled.')
			return
		value = cmds.promptDialog(query=True, text=True)
 
		try:
			curve_type = cmds.nodeType(curve_obj)
			if (curve_type == 'animCurveUL' or curve_type == 'animCurveUA' or curve_type == 'animCurveUT' or curve_type == 'animCurveUU'):
				cmds.setKeyframe(curve_obj, float=float(input_value), value=float(value))
			else:
				cmds.setKeyframe(curve_obj, time=input_value, value=float(value))
		except:
			cmds.warning('Failed to parse user-provided arguments.')
	#end
 
	def __refresh_curves(self):
		self.cb_edit_curve.clear()
		for curr in cmds.ls(type='animCurve'):
			self.cb_edit_curve.addItem(curr)
	#end
 
	def __select_curve(self):
		curve_obj = self.cb_edit_curve.currentText()
		if (not len(curve_obj)) or (not cmds.objExists(curve_obj)):
			cmds.warning('Object does not exist.')
			return False
 
		mods = cmds.getModifiers()
		shift_pressed = (mods & 1) > 0
		cmds.select(curve_obj, add=shift_pressed)
		return True
	#end
 
	def __open_graph_editor(self):
		if not self.__select_curve():
			return
		mel.eval("GraphEditor;");
	#end
 
	def __build_ui(self):
		self.setObjectName("self")
		self.setWindowTitle(" ")
		self.setFixedSize(196, 320)
		self.lbl_title = QtGui.QLabel(self)
		self.lbl_title.setGeometry(QtCore.QRect(10, 10, 181, 21))
		font = QtGui.QFont()
		font.setFamily("Arial")
		font.setPointSize(16)
		self.lbl_title.setFont(font)
		self.lbl_title.setObjectName("lbl_title")
		self.lbl_title.setText("AnimCurve Toolbox")
		self.gb_create = QtGui.QGroupBox(self)
		self.gb_create.setGeometry(QtCore.QRect(10, 40, 171, 111))
		self.gb_create.setObjectName("gb_create")
		self.cb_create_type = QtGui.QComboBox(self.gb_create)
		self.gb_create.setTitle("Create")
		self.cb_create_type.setGeometry(QtCore.QRect(40, 20, 121, 22))
		self.cb_create_type.setObjectName("cb_create_type")
		self.cb_create_type.addItem("animCurveUT")
		self.cb_create_type.addItem("animCurveUU")
		self.cb_create_type.addItem("animCurveUA")
		self.cb_create_type.addItem("animCurveTT")
		self.cb_create_type.addItem("animCurveTU")
		self.cb_create_type.addItem("animCurveUL")
		self.cb_create_type.addItem("animCurveTA")
		self.cb_create_type.addItem("animCurveTL")
		self.lbl_create_type = QtGui.QLabel(self.gb_create)
		self.lbl_create_type.setGeometry(QtCore.QRect(10, 20, 46, 21))
		self.lbl_create_type.setObjectName("lbl_create_type")
		self.lbl_create_type.setText("Type")
		self.txt_create_name = QtGui.QLineEdit(self.gb_create)
		self.txt_create_name.setGeometry(QtCore.QRect(40, 50, 121, 21))
		self.txt_create_name.setObjectName("txt_create_name")
		self.txt_create_name.setText("")
		self.lbl_create_name = QtGui.QLabel(self.gb_create)
		self.lbl_create_name.setGeometry(QtCore.QRect(10, 50, 46, 21))
		self.lbl_create_name.setObjectName("lbl_create_name")
		self.lbl_create_name.setText("Name")
		self.btn_create = QtGui.QPushButton(self.gb_create)
		self.btn_create.setGeometry(QtCore.QRect(10, 80, 151, 21))
		self.btn_create.setObjectName("btn_create")
		self.btn_create.setText("Create")
		self.btn_create.clicked.connect(self.__create_curve)
		self.gb_edit = QtGui.QGroupBox(self)
		self.gb_edit.setGeometry(QtCore.QRect(10, 160, 171, 141))
		self.gb_edit.setObjectName("gb_edit")
		self.gb_edit.setTitle("Edit")
		self.cb_edit_curve = QtGui.QComboBox(self.gb_edit)
		self.cb_edit_curve.setGeometry(QtCore.QRect(10, 20, 121, 22))
		self.cb_edit_curve.setObjectName("cb_edit_curve")
		self.btn_edit_add_keyframe = QtGui.QPushButton(self.gb_edit)
		self.btn_edit_add_keyframe.setGeometry(QtCore.QRect(10, 50, 151, 23))
		self.btn_edit_add_keyframe.setObjectName("btn_edit_add_keyframe")
		self.btn_edit_add_keyframe.setText("Add Keyframe")
		self.btn_edit_add_keyframe.clicked.connect(self.__add_keyframe)
		self.btn_edit_refresh = QtGui.QPushButton(self.gb_edit)
		self.btn_edit_refresh.setGeometry(QtCore.QRect(140, 20, 21, 23))
		self.btn_edit_refresh.setObjectName("btn_edit_refresh")
		self.btn_edit_refresh.setText("<")
		self.btn_edit_refresh.clicked.connect(self.__refresh_curves)
		self.btn_edit_select = QtGui.QPushButton(self.gb_edit)
		self.btn_edit_select.setGeometry(QtCore.QRect(10, 80, 151, 23))
		self.btn_edit_select.setObjectName("btn_edit_select")
		self.btn_edit_select.setText("Select")
		self.btn_edit_select.clicked.connect(self.__select_curve)
		self.btn_edit_graph = QtGui.QPushButton(self.gb_edit)
		self.btn_edit_graph.setGeometry(QtCore.QRect(10, 110, 151, 23))
		self.btn_edit_graph.setObjectName("btn_edit_graph")
		self.btn_edit_graph.setText("Graph Editor")
		self.btn_edit_graph.clicked.connect(self.__open_graph_editor)
		self.lbl_website = QtGui.QLabel(self)
		self.lbl_website.setGeometry(QtCore.QRect(90, 300, 91, 16))
		self.lbl_website.setObjectName("lbl_website")
		self.lbl_website.setText("www.ngreen.org")
 
		self.show()
		self.raise_()
	#end
#end
 
def main():
	app = QtGui.QApplication.instance()
	if not app:
		app = QtGui.QApplication(sys.argv)
		app.aboutToQuit.connect(app.deleteLater)
	global anim_curve_toolbox
	anim_curve_toolbox = AnimCurveToolbox()
	sys.exit(app.exec_())
#end
 
if __name__ == '__main__':
	main()
#end
