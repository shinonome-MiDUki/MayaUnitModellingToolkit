from pathlib import Path
import json
import re

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
unit_modelling_toolkit_data_file = Path("/Users/shiinaayame/Downloads/test_mytool.json")

class MyCustomWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyCustomWindow, self).__init__(parent=parent)
        
        if not unit_modelling_toolkit_data_file.exists():
            self.tool_data = {"stored_items" : []}
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f)
        else:
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
        def naming_dialog() -> str | None:
            copy_name_dialog = cmds.promptDialog(
                title = "Copying Object Name",
                message = "Enter Object Name : ",
                button = ["Confirm", "Cancel"],
                defaultButton = "Confirm",
                cancelButton = "Cancel",
                dismissString = "Cancel"
            )
            if copy_name_dialog == "Confirm":
                copying_obj_name = str(cmds.promptDialog(q=True, text=True))
                return copying_obj_name
            else:
                return None
            
        copying_obj_name = naming_dialog() 
        while re.match(r"[a-zA-Z_][a-zA-Z0-9_]*$", copying_obj_name) is None:
            cmds.inViewMessage(amg='<span style="color:#FF0000;">Invalid Name !</span>', 
                   pos='botRight', 
                   fade=True)
            copying_obj_name = naming_dialog()
            if copying_obj_name is None:
                break
        if copying_obj_name is None:
            return
        c = 1
        root_name = copying_obj_name
        while cmds.objExists(f"UnitModellingToolkitGP|{copying_obj_name}"):
            copying_obj_name = f"{root_name}{c}"
            c += 1

        selected_obj_raw = cmds.ls(sl=True)
        if not selected_obj_raw:
            return
        selected_obj = cmds.duplicate(selected_obj_raw)
        selected_obj_w = cmds.parent(selected_obj, world=True)
        if selected_obj_w is not None:
            selected_obj = selected_obj_w
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
        cmds.parent(copying_obj_name, "UnitModellingToolkitGP")

        if "stored_items" in self.tool_data:
            self.tool_data["stored_items"].append(copying_obj_name)
            self.dropdown.clear()
            self.dropdown.addItems(self.tool_data["stored_items"])
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f)

    def on_delete(self):
        obj_to_delete = self.dropdown.currentText()
        obj_name = f"UnitModellingToolkitGP|{obj_to_delete.strip()}"
        if cmds.objExists(obj_name):
            cmds.delete(obj_name)
        current_stored = self.tool_data.get("stored_items",[])
        if obj_to_delete in current_stored:
            current_stored.remove(obj_to_delete)
            self.tool_data["stored_items"] = current_stored
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f)
        self.dropdown.clear()
        self.dropdown.addItems(current_stored)

    def on_place(self):
        selected_obj_ls = cmds.ls(sl=True)
        if not selected_obj_ls:
            return
        selected_obj = selected_obj_ls[0]
        selected_pos = cmds.xform(selected_obj, q=True, rotatePivot=True, worldSpace=True)
        using_obj = self.dropdown.currentText().strip()
        using_obj_name = f"UnitModellingToolkitGP|{using_obj}"
        if not cmds.objExists(using_obj_name):
            cmds.inViewMessage(amg='<span style="color:#FF0000;">Object not exist</span>', 
                   pos='botRight', 
                   fade=True)
            current_stored = self.tool_data.get("stored_items",[])
            if using_obj in current_stored:
                current_stored.remove(using_obj)
                self.tool_data["stored_items"] = current_stored
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f)
            self.dropdown.clear()
            self.dropdown.addItems(current_stored)
            return
        using_obj_duplicate = cmds.duplicate(using_obj_name)
        if len(using_obj_duplicate) > 1:
            using_obj_duplicate_real = []
            for obj in using_obj_duplicate:
                shape = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                if not shape:
                    using_obj_duplicate_real.append(obj)
                    break
            if not using_obj_duplicate_real:
                print("Group not found")
                return
            using_obj_duplicate = using_obj_duplicate_real
        using_obj_duplicate = cmds.parent(using_obj_duplicate, world=True)[0]
        cmds.setAttr(f"{using_obj_duplicate}.visibility", True)
        print(selected_pos)
        cmds.move(selected_pos[0], selected_pos[1], selected_pos[2], using_obj_duplicate, rotatePivotRelative=True)
        cmds.makeIdentity(using_obj_duplicate, apply=True, normal=False,
                          rotate=True, scale=True, translate=True,
                          preserveNormals=True)
        

def show_window():
    if cmds.window(unit_modelling_toolkit_obj_name, exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name)
    if cmds.workspaceControl(unit_modelling_toolkit_obj_name + "WorkspaceControl", exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name + "WorkspaceControl")

    global my_win
    my_win = MyCustomWindow()
    my_win.show(dockable=True)

show_window()