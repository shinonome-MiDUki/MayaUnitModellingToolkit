from pathlib import Path
import json

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton
    )
from PySide6 import QtWidgets
from PySide6 import QtCore

from maya import cmds as cmds
from maya import mel as mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

unit_modelling_toolkit_obj_name = "UnitModellingToolkitWindow"
unit_modelling_toolkit_data_file = Path("")

class MyCustomWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyCustomWindow, self).__init__(parent=parent)
        
        if not unit_modelling_toolkit_data_file.exists():
            print("Data file not exist")
            return
        with open(unit_modelling_toolkit_data_file, "r", encoding="utf-8") as f:
            self.tool_data = json.load(f)
        self.setWindowTitle("Unit Modelling Toolkits")
        self.setObjectName(unit_modelling_toolkit_obj_name)
        self.setMinimumSize(300, 100)
       
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Copied Assets : ")
        layout.addWidget(self.label)
        self.dropdown = QComboBox()
        self.dropdown.clear()
        self.dropdown.addItems(self.tool_data.get("stored_items", []))
        layout.addWidget(self.dropdown)
        
        sublayout1 = QHBoxLayout()
        self.copy_btn = QPushButton("Store")
        self.copy_btn.clicked.connect(self.on_copy)
        sublayout1.addWidget(self.copy_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete)
        sublayout1.addWidget(self.delete_btn)
        self.place_btn = QPushButton("Place")
        self.place_btn.clicked.connect(self.on_place)
        sublayout1.addWidget(self.place_btn)
        layout.addLayout(sublayout1)

    def on_copy(self):
        copy_name_dialog = cmds.promptDialog(
            title = "Copying Object Name",
            message = "Enter Object Name : ",
            button = ["Confirm", "Cancel"],
            defaultButton = "Confirm",
            cancelButton = "Cancel",
            dismissButton = "Cancel"
        )
        if copy_name_dialog == "Confirm":
            copying_obj_name = str(cmds.promptDialog(q=True, text=True))
            c = 1
            root_name = copying_obj_name
            while cmds.objExists(f"UnitModellingToolkitGP|{copying_obj_name}"):
                copying_obj_name = f"{root_name}{c}"
                c += 1
        else:
            return
        selected_obj_raw = cmds.ls(sl=True)
        if not selected_obj:
            return
        selected_obj = cmds.duplicate(selected_obj_raw)
        selected_obj = cmds.group(selected_obj, world=True)
        if len(selected_obj) > 1:
            copying_obj_name = copying_obj_name if copying_obj_name != "" else f"{copying_obj_name[0]}sGroup"
            cmds.group(selected_obj, name=copying_obj_name)
        else:
            if copying_obj_name != "":
                copying_obj_name = copying_obj_name
                cmds.rename(selected_obj[0], copying_obj_name)
            else:
                copying_obj_name = selected_obj[0]
        cmds.move(0, 0, 0, copying_obj_name, rotatePivotRelative=True)
        cmds.makeIdentity(copying_obj_name, apply=True, normal=False,
                          rotate=True, scale=True, translate=True,
                          preserveNormals=True)
        if not cmds.objExists("UnitModellingToolkitGP"):
            cmds.group(empty=True, name="UnitModellingToolkitGP")
        cmds.setAttr("UnitModellingToolkitGP.visibility", False)
        cmds.parent(copying_obj_name, "UnitModellingToolkitGP", relative=True)

        if "stored_items" in self.tool_data:
            self.tool_data["stored_items"].append(copying_obj_name)
            self.dropdown.clear()
            self.dropdown.addItems(self.tool_data["stored_items"])
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f)

    def on_delete(self):
        pass

    def on_place(self):
        pass

def show_window():
    if cmds.window(unit_modelling_toolkit_obj_name, exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name)
    if cmds.workspaceControl(unit_modelling_toolkit_obj_name + "WorkspaceControl", exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name + "WorkspaceControl")

    global my_win
    my_win = MyCustomWindow()
    my_win.show(dockable=True)

show_window()