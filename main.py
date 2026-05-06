from pathlib import Path
import json
import re

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QCheckBox,
    QStackedWidget, QWidget
    )
from PySide6 import QtWidgets
from PySide6 import QtCore

from maya import cmds as cmds
from maya import mel as mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

unit_modelling_toolkit_obj_name = "UnitModellingToolkitWindow"
unit_modelling_toolkit_data_file = Path(cmds.workspace(q=True, directory=True) + "UnitModellingToolkit.json")

class MyCustomWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyCustomWindow, self).__init__(parent=parent)
        
        self.current_file_name = cmds.file(q=True, sceneName=True, shortName=True)
        if self.current_file_name == "":
            self.current_file_name = "Untitled"
        if not unit_modelling_toolkit_data_file.exists():
            self.tool_data = {
                self.current_file_name: {
                    "stored_items" : [], 
                    "stored_components" : {}
                }
            }
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
        else:
            with open(unit_modelling_toolkit_data_file, "r", encoding="utf-8") as f:
                self.tool_data = json.load(f)
            if self.current_file_name not in self.tool_data:
                self.tool_data[self.current_file_name] = {
                        "stored_items" : [], 
                        "stored_components" : {}
                    }
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
        self.setWindowTitle("Unit Modelling Toolkits")
        self.setObjectName(unit_modelling_toolkit_obj_name)
        self.setMinimumSize(300, 150)

        self.layout = QVBoxLayout(self)
        self.mode_select_box = QCheckBox("Mesh-Mode")
        self.mode_select_box.setChecked(True)
        self.mode_select_box.toggled.connect(self.toggle_mode)
        self.layout.addWidget(self.mode_select_box)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        self.setup_mesh_mode_ui()
        self.setup_component_mode_ui()
        self.stacked_widget.setCurrentIndex(0)

    def setup_mesh_mode_ui(self): 
        mesh_mode_widget = QWidget()
        mesh_layout = QVBoxLayout(mesh_mode_widget)
        mesh_label = QLabel("Copied Assets : ")
        mesh_layout.addWidget(mesh_label)
        self.mesh_dropdown = QComboBox()
        self.mesh_dropdown.clear()
        self.mesh_dropdown.addItems(self.tool_data[self.current_file_name].get("stored_items", []))
        mesh_layout.addWidget(self.mesh_dropdown)
        
        sublayout1 = QHBoxLayout()
        mesh_copy_btn = QPushButton("Store")
        mesh_copy_btn.clicked.connect(self.on_copy_mesh)
        sublayout1.addWidget(mesh_copy_btn)
        mesh_delete_btn = QPushButton("Delete")
        mesh_delete_btn.clicked.connect(self.on_delete_mesh)
        sublayout1.addWidget(mesh_delete_btn)
        mesh_place_btn = QPushButton("Place")
        mesh_place_btn.clicked.connect(self.on_place_mesh)
        sublayout1.addWidget(mesh_place_btn)
        mesh_layout.addLayout(sublayout1)

        self.stacked_widget.addWidget(mesh_mode_widget)

    def setup_component_mode_ui(self): 
        component_mode_widget = QWidget()
        component_layout = QVBoxLayout(component_mode_widget)
        component_label = QLabel("Copied Component : ")
        component_layout.addWidget(component_label)
        self.component_dropdown = QComboBox()
        self.component_dropdown.clear()
        self.component_dropdown.addItems([i for i in self.tool_data[self.current_file_name].get("stored_components", {})])
        component_layout.addWidget(self.component_dropdown)
        
        sublayout1 = QHBoxLayout()
        component_copy_btn = QPushButton("Store")
        component_copy_btn.clicked.connect(self.on_copy_component)
        sublayout1.addWidget(component_copy_btn)
        component_delete_btn = QPushButton("Delete")
        component_delete_btn.clicked.connect(self.on_delete_component)
        sublayout1.addWidget(component_delete_btn)
        component_place_btn = QPushButton("Select")
        component_place_btn.clicked.connect(self.on_select_component)
        sublayout1.addWidget(component_place_btn)
        component_layout.addLayout(sublayout1)

        self.stacked_widget.addWidget(component_mode_widget)

    def on_copy_mesh(self):
        selected_obj_raw = cmds.ls(sl=True)
        for obj_raw in selected_obj_raw:
            if cmds.objectType(obj_raw) != "transform":
                cmds.inViewMessage(amg='<span style="color:#FF0000;">Invalid Component Type !</span>', 
                   pos='botRight', 
                   fade=True)
                return

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
                copying_obj_name = str(cmds.promptDialog(q=True, text=True)).strip()
                return copying_obj_name
            else:
                return None
            
        copying_obj_name = naming_dialog() 
        while copying_obj_name != "" and re.match(r"[a-zA-Z_][a-zA-Z0-9_]*$", copying_obj_name) is None:
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
        cmds.xform(copying_obj_name, centerPivots=True)
        if not cmds.objExists("UnitModellingToolkitGP"):
            cmds.group(empty=True, name="UnitModellingToolkitGP")
        cmds.setAttr("UnitModellingToolkitGP.visibility", False)
        cmds.parent(copying_obj_name, "UnitModellingToolkitGP")

        if "stored_items" in self.tool_data[self.current_file_name]:
            self.tool_data[self.current_file_name]["stored_items"].append(copying_obj_name)
            self.mesh_dropdown.clear()
            self.mesh_dropdown.addItems(self.tool_data[self.current_file_name]["stored_items"])
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f, ensure_ascii=False, indent=3)

    def on_delete_mesh(self):
        obj_to_delete = self.mesh_dropdown.currentText().strip()
        obj_name = f"UnitModellingToolkitGP|{obj_to_delete.strip()}"
        if cmds.objExists(obj_name):
            cmds.delete(obj_name)
        current_stored = self.tool_data[self.current_file_name].get("stored_items",[])
        if obj_to_delete in current_stored:
            current_stored.remove(obj_to_delete)
            self.tool_data[self.current_file_name]["stored_items"] = current_stored
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
        self.mesh_dropdown.clear()
        self.mesh_dropdown.addItems(current_stored)

    def on_place_mesh(self):
        selected_obj_ls = cmds.ls(sl=True)
        if not selected_obj_ls:
            return
        selected_obj = selected_obj_ls[0]
        using_obj = self.mesh_dropdown.currentText().strip()
        using_obj_name = f"UnitModellingToolkitGP|{using_obj}"
        if not cmds.objExists(using_obj_name):
            cmds.inViewMessage(amg='<span style="color:#FF0000;">Object not exist</span>', 
                   pos='botRight', 
                   fade=True)
            current_stored = self.tool_data[self.current_file_name].get("stored_items",[])
            if using_obj in current_stored:
                current_stored.remove(using_obj)
                self.tool_data[self.current_file_name]["stored_items"] = current_stored
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
            self.mesh_dropdown.clear()
            self.mesh_dropdown.addItems(current_stored)
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
        cmds.matchTransform(using_obj_duplicate, selected_obj)
        cmds.makeIdentity(using_obj_duplicate, apply=True, normal=False,
                          rotate=True, scale=True, translate=True,
                          preserveNormals=True)
        
    def on_copy_component(self):
        selected_component = cmds.ls(sl=True)
        copy_name_dialog = cmds.promptDialog(
            title = "Copying Object Name",
            message = "Enter Object Name : ",
            button = ["Confirm", "Cancel"],
            defaultButton = "Confirm",
            cancelButton = "Cancel",
            dismissString = "Cancel"
        )
        if copy_name_dialog == "Confirm":
            copying_component_name = str(cmds.promptDialog(q=True, text=True)).strip()
        else:
            return
        copying_component_name = copying_component_name if copying_component_name != "" else selected_component[0]
        if "stored_components" in self.tool_data[self.current_file_name]:
            self.tool_data[self.current_file_name]["stored_components"][copying_component_name] = selected_component
        else:
            self.tool_data[self.current_file_name]["stored_components"] = {}
        with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
            json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
        self.component_dropdown.clear()
        self.component_dropdown.addItems([i for i in self.tool_data[self.current_file_name].get("stored_components", {})])
    
    def on_delete_component(self):
        component_to_delete = self.component_dropdown.currentText().strip()
        if ("stored_components" in self.tool_data[self.current_file_name] 
            and component_to_delete in self.tool_data[self.current_file_name]["stored_components"]):
            del self.tool_data[self.current_file_name]["stored_components"][component_to_delete]
        with open(unit_modelling_toolkit_data_file, "w",  encoding="utf-8") as f:
            json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
        self.component_dropdown.clear()
        self.component_dropdown.addItems([i for i in self.tool_data[self.current_file_name]["stored_components"]])

    def on_select_component(self):
        cmds.select(cl=True)
        selected_component_gp = self.component_dropdown.currentText().strip()
        components_to_select = self.tool_data[self.current_file_name].get("stored_components", {}).get(selected_component_gp, None)
        if components_to_select is None:
            return
        print(components_to_select)
        try:
            cmds.select(components_to_select)
        except:
            cmds.inViewMessage(amg='<span style="color:#FF0000;">Selection failed</span>', 
                    pos='botRight', 
                    fade=True)
            del self.tool_data[self.current_file_name]["stored_components"][selected_component_gp]
            with open(unit_modelling_toolkit_data_file, "w", encoding="utf-8") as f:
                json.dump(self.tool_data, f, ensure_ascii=False, indent=3)
            self.component_dropdown.clear()
            self.component_dropdown.addItems([i for i in self.tool_data[self.current_file_name]["stored_components"]])
        
    def toggle_mode(self):
        if self.mode_select_box.isChecked():
            self.stacked_widget.setCurrentIndex(0)
        else:
            self.stacked_widget.setCurrentIndex(1)
        

def show_window():
    if cmds.window(unit_modelling_toolkit_obj_name, exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name)
    if cmds.workspaceControl(unit_modelling_toolkit_obj_name + "WorkspaceControl", exists=True):
        cmds.deleteUI(unit_modelling_toolkit_obj_name + "WorkspaceControl")

    global my_win
    my_win = MyCustomWindow()
    my_win.show(dockable=True)

show_window()