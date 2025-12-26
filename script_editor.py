"""
PyMacroLite 脚本可视化编辑器
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
    QDialog, QDialogButtonBox, QFormLayout, QTabWidget, QSplitter,
    QMessageBox, QFileDialog, QMenu, QInputDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPalette, QColor, QFont

# 指令定义
ACTIONS = {
    "wait": {"name": "等待", "params": [
        ("seconds", "float", "等待秒数", 1.0)
    ]},
    "click": {"name": "点击", "params": [
        ("x", "int", "X坐标", 0),
        ("y", "int", "Y坐标", 0),
        ("button", "choice", "按键", "left", ["left", "right", "middle"]),
        ("human", "bool", "拟人化", True)
    ]},
    "double_click": {"name": "双击", "params": [
        ("x", "int", "X坐标", 0),
        ("y", "int", "Y坐标", 0),
        ("human", "bool", "拟人化", True)
    ]},
    "drag": {"name": "拖拽", "params": [
        ("x1", "int", "起点X", 0),
        ("y1", "int", "起点Y", 0),
        ("x2", "int", "终点X", 0),
        ("y2", "int", "终点Y", 0),
        ("duration", "float", "时长(秒)", 0.5),
        ("human", "bool", "拟人化", True)
    ]},
    "scroll": {"name": "滚轮", "params": [
        ("steps", "int", "滚动格数(正上负下)", 3)
    ]},
    "type": {"name": "输入文字", "params": [
        ("text", "str", "文字内容", "")
    ]},
    "key_hold": {"name": "按住按键", "params": [
        ("key", "str", "按键名", ""),
        ("duration", "float", "时长(秒)", 0.1)
    ]},
    "key_combo": {"name": "组合键", "params": [
        ("keys", "str", "组合键(如ctrl+c)", "")
    ]},
    "find_and_click": {"name": "找图点击", "params": [
        ("target", "str", "图片路径", "assets/"),
        ("confidence", "float", "匹配度(0-1)", 0.8),
        ("button", "choice", "按键", "left", ["left", "right", "double"]),
        ("offset_x", "int", "X偏移", 0),
        ("offset_y", "int", "Y偏移", 0),
        ("human", "bool", "拟人化", True)
    ]},
    "click_text": {"name": "找字点击", "params": [
        ("text", "str", "目标文字", ""),
        ("index", "int", "第几个(从1开始)", 1),
        ("button", "choice", "按键", "left", ["left", "right", "double"]),
        ("offset_x", "int", "X偏移", 0),
        ("offset_y", "int", "Y偏移", 0)
    ]},
    "label": {"name": "标签", "params": [
        ("name", "str", "标签名", "")
    ]},
    "jump": {"name": "跳转", "params": [
        ("target", "str", "目标标签", "")
    ]},
    "jump_if_found": {"name": "条件跳转(找到)", "params": [
        ("target", "str", "图片路径或文字", ""),
        ("type", "choice", "类型", "image", ["image", "text"]),
        ("confidence", "float", "匹配度", 0.8),
        ("label", "str", "跳转标签", "")
    ]},
    "check_value_jump": {"name": "条件跳转(数值)", "params": [
        ("region", "region", "识别区域", [0, 0, 100, 30]),
        ("op", "choice", "比较", ">", [">", "<", ">=", "<=", "==", "!="]),
        ("value", "int", "比较值", 0),
        ("label", "str", "跳转标签", "")
    ]},
    "call_script": {"name": "调用模块", "params": [
        ("name", "str", "模块名", "")
    ]},
    "return": {"name": "返回", "params": []},
    "exit": {"name": "退出", "params": []},
    "run_python": {"name": "Python代码", "params": [
        ("code", "text", "代码", "# 在这里写Python代码\napi.log('Hello')\n")
    ]}
}


class ParamDialog(QDialog):
    """参数编辑对话框"""
    def __init__(self, action_type, params=None, parent=None):
        super().__init__(parent)
        self.action_type = action_type
        self.param_widgets = {}
        self.init_ui(params or {})
    
    def init_ui(self, params):
        action_def = ACTIONS.get(self.action_type, {})
        self.setWindowTitle(f"编辑: {action_def.get('name', self.action_type)}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        for param_def in action_def.get("params", []):
            name = param_def[0]
            ptype = param_def[1]
            label = param_def[2]
            default = param_def[3] if len(param_def) > 3 else ""
            
            value = params.get(name, default)
            widget = self._create_widget(ptype, param_def, value)
            self.param_widgets[name] = (ptype, widget)
            form.addRow(f"{label}:", widget)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create_widget(self, ptype, param_def, value):
        if ptype == "int":
            w = QSpinBox()
            w.setRange(-9999, 9999)
            w.setValue(int(value) if value else 0)
            return w
        elif ptype == "float":
            w = QDoubleSpinBox()
            w.setRange(-9999, 9999)
            w.setDecimals(2)
            w.setValue(float(value) if value else 0)
            return w
        elif ptype == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            return w
        elif ptype == "choice":
            w = QComboBox()
            choices = param_def[4] if len(param_def) > 4 else []
            w.addItems(choices)
            if value in choices:
                w.setCurrentText(str(value))
            return w
        elif ptype == "text":
            w = QTextEdit()
            w.setPlainText(str(value) if value else "")
            w.setMinimumHeight(150)
            return w
        elif ptype == "region":
            w = QLineEdit()
            if isinstance(value, list):
                w.setText(f"{value[0]}, {value[1]}, {value[2]}, {value[3]}")
            else:
                w.setText("0, 0, 100, 30")
            w.setPlaceholderText("x, y, 宽, 高")
            return w
        else:
            w = QLineEdit()
            w.setText(str(value) if value else "")
            return w
    
    def get_params(self):
        result = {}
        for name, (ptype, widget) in self.param_widgets.items():
            if ptype == "int":
                result[name] = widget.value()
            elif ptype == "float":
                result[name] = widget.value()
            elif ptype == "bool":
                result[name] = widget.isChecked()
            elif ptype == "choice":
                result[name] = widget.currentText()
            elif ptype == "text":
                result[name] = widget.toPlainText()
            elif ptype == "region":
                try:
                    parts = [int(x.strip()) for x in widget.text().split(",")]
                    result[name] = parts[:4]
                except:
                    result[name] = [0, 0, 100, 30]
            else:
                result[name] = widget.text()
        return result


class StepItem(QListWidgetItem):
    """步骤列表项"""
    def __init__(self, action, params):
        self.action = action
        self.params = params
        action_def = ACTIONS.get(action, {})
        name = action_def.get("name", action)
        
        # 生成显示文本
        if action == "label":
            text = f"🏷️ [{params.get('name', '')}]"
        elif action == "jump":
            text = f"↪️ 跳转到 [{params.get('target', '')}]"
        elif action == "wait":
            text = f"⏱️ 等待 {params.get('seconds', 1)} 秒"
        elif action == "click":
            text = f"🖱️ 点击 ({params.get('x', 0)}, {params.get('y', 0)})"
        elif action == "find_and_click":
            text = f"🔍 找图点击 [{params.get('target', '')}]"
        elif action == "click_text":
            text = f"📝 找字点击 [{params.get('text', '')}]"
        elif action == "jump_if_found":
            text = f"❓ 找到 [{params.get('target', '')}] 则跳转"
        elif action == "call_script":
            text = f"📦 调用 [{params.get('name', '')}]"
        elif action == "key_hold":
            text = f"⌨️ 按键 [{params.get('key', '')}] {params.get('duration', 0.1)}秒"
        elif action == "type":
            text = f"⌨️ 输入 [{params.get('text', '')[:20]}]"
        elif action == "run_python":
            code = params.get('code', '')[:30].replace('\n', ' ')
            text = f"🐍 Python: {code}..."
        elif action == "return":
            text = "↩️ 返回"
        elif action == "exit":
            text = "🛑 退出"
        else:
            text = f"{name}"
        
        super().__init__(text)
    
    def to_dict(self):
        return {"action": self.action, "params": self.params}


class ModuleEditor(QWidget):
    """模块编辑器"""
    changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.action_combo = QComboBox()
        for action, info in ACTIONS.items():
            self.action_combo.addItem(f"{info['name']}", action)
        toolbar.addWidget(self.action_combo)
        
        btn_add = QPushButton("➕ 添加")
        btn_add.clicked.connect(self.add_step)
        toolbar.addWidget(btn_add)
        
        toolbar.addStretch()
        
        btn_up = QPushButton("⬆️")
        btn_up.setFixedWidth(40)
        btn_up.clicked.connect(self.move_up)
        toolbar.addWidget(btn_up)
        
        btn_down = QPushButton("⬇️")
        btn_down.setFixedWidth(40)
        btn_down.clicked.connect(self.move_down)
        toolbar.addWidget(btn_down)
        
        btn_del = QPushButton("🗑️")
        btn_del.setFixedWidth(40)
        btn_del.clicked.connect(self.delete_step)
        toolbar.addWidget(btn_del)
        
        layout.addLayout(toolbar)
        
        # 步骤列表
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QListWidget.InternalMove)
        self.step_list.itemDoubleClicked.connect(self.edit_step)
        layout.addWidget(self.step_list)
    
    def add_step(self):
        action = self.action_combo.currentData()
        dialog = ParamDialog(action, {}, self)
        if dialog.exec() == QDialog.Accepted:
            params = dialog.get_params()
            item = StepItem(action, params)
            self.step_list.addItem(item)
            self.changed.emit()
    
    def edit_step(self, item):
        if isinstance(item, StepItem):
            dialog = ParamDialog(item.action, item.params, self)
            if dialog.exec() == QDialog.Accepted:
                item.params = dialog.get_params()
                # 更新显示
                new_item = StepItem(item.action, item.params)
                item.setText(new_item.text())
                self.changed.emit()
    
    def delete_step(self):
        row = self.step_list.currentRow()
        if row >= 0:
            self.step_list.takeItem(row)
            self.changed.emit()
    
    def move_up(self):
        row = self.step_list.currentRow()
        if row > 0:
            item = self.step_list.takeItem(row)
            self.step_list.insertItem(row - 1, item)
            self.step_list.setCurrentRow(row - 1)
            self.changed.emit()
    
    def move_down(self):
        row = self.step_list.currentRow()
        if row < self.step_list.count() - 1:
            item = self.step_list.takeItem(row)
            self.step_list.insertItem(row + 1, item)
            self.step_list.setCurrentRow(row + 1)
            self.changed.emit()
    
    def load_steps(self, steps):
        self.step_list.clear()
        for step in steps:
            action = step.get("action", "")
            params = step.get("params", {})
            item = StepItem(action, params)
            self.step_list.addItem(item)
    
    def get_steps(self):
        steps = []
        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            if isinstance(item, StepItem):
                steps.append(item.to_dict())
        return steps


class ScriptEditor(QMainWindow):
    """脚本编辑器主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyMacroLite 脚本编辑器")
        self.setMinimumSize(900, 600)
        
        self.project = {"_settings": {"global_variance": 5, "human_move": True}, "main": []}
        self.current_file = None
        self.modified = False
        
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # 左侧：模块列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        left_layout.addWidget(QLabel("模块列表"))
        
        self.module_list = QListWidget()
        self.module_list.currentRowChanged.connect(self.on_module_changed)
        left_layout.addWidget(self.module_list)
        
        btn_layout = QHBoxLayout()
        btn_add_module = QPushButton("➕ 新建")
        btn_add_module.clicked.connect(self.add_module)
        btn_del_module = QPushButton("🗑️ 删除")
        btn_del_module.clicked.connect(self.delete_module)
        btn_layout.addWidget(btn_add_module)
        btn_layout.addWidget(btn_del_module)
        left_layout.addLayout(btn_layout)
        
        # 右侧：编辑区
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 工具栏
        toolbar = QHBoxLayout()
        btn_new = QPushButton("📄 新建")
        btn_new.clicked.connect(self.new_project)
        btn_open = QPushButton("📂 打开")
        btn_open.clicked.connect(self.open_project)
        btn_save = QPushButton("💾 保存")
        btn_save.clicked.connect(self.save_project)
        btn_saveas = QPushButton("📥 另存为")
        btn_saveas.clicked.connect(self.save_project_as)
        
        toolbar.addWidget(btn_new)
        toolbar.addWidget(btn_open)
        toolbar.addWidget(btn_save)
        toolbar.addWidget(btn_saveas)
        toolbar.addStretch()
        
        btn_settings = QPushButton("⚙️ 全局设置")
        btn_settings.clicked.connect(self.edit_settings)
        toolbar.addWidget(btn_settings)
        
        right_layout.addLayout(toolbar)
        
        # 模块编辑器
        self.module_editor = ModuleEditor()
        self.module_editor.changed.connect(self.on_content_changed)
        right_layout.addWidget(self.module_editor)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 700])
        layout.addWidget(splitter)
        
        # 初始化
        self.refresh_module_list()
    
    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.instance().setPalette(palette)
    
    def refresh_module_list(self):
        self.module_list.clear()
        for name in self.project.keys():
            if not name.startswith("_"):
                self.module_list.addItem(name)
        if self.module_list.count() > 0:
            self.module_list.setCurrentRow(0)
    
    def on_module_changed(self, row):
        if row >= 0:
            name = self.module_list.item(row).text()
            steps = self.project.get(name, [])
            self.module_editor.load_steps(steps)
    
    def on_content_changed(self):
        row = self.module_list.currentRow()
        if row >= 0:
            name = self.module_list.item(row).text()
            self.project[name] = self.module_editor.get_steps()
            self.modified = True
            self.update_title()
    
    def update_title(self):
        title = "PyMacroLite 脚本编辑器"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.modified:
            title += " *"
        self.setWindowTitle(title)
    
    def add_module(self):
        name, ok = QInputDialog.getText(self, "新建模块", "模块名称:")
        if ok and name:
            if name in self.project:
                QMessageBox.warning(self, "错误", "模块已存在")
                return
            self.project[name] = []
            self.refresh_module_list()
            # 选中新模块
            for i in range(self.module_list.count()):
                if self.module_list.item(i).text() == name:
                    self.module_list.setCurrentRow(i)
                    break
            self.modified = True
            self.update_title()
    
    def delete_module(self):
        row = self.module_list.currentRow()
        if row >= 0:
            name = self.module_list.item(row).text()
            if name == "main":
                QMessageBox.warning(self, "错误", "不能删除 main 模块")
                return
            reply = QMessageBox.question(self, "确认", f"确定删除模块 [{name}]?")
            if reply == QMessageBox.Yes:
                del self.project[name]
                self.refresh_module_list()
                self.modified = True
                self.update_title()
    
    def edit_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("全局设置")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        settings = self.project.get("_settings", {})
        
        variance_spin = QSpinBox()
        variance_spin.setRange(0, 50)
        variance_spin.setValue(settings.get("global_variance", 5))
        form.addRow("随机误差(像素):", variance_spin)
        
        offset_x_spin = QSpinBox()
        offset_x_spin.setRange(-9999, 9999)
        offset_x_spin.setValue(settings.get("global_offset_x", 0))
        form.addRow("X轴偏移:", offset_x_spin)
        
        offset_y_spin = QSpinBox()
        offset_y_spin.setRange(-9999, 9999)
        offset_y_spin.setValue(settings.get("global_offset_y", 0))
        form.addRow("Y轴偏移:", offset_y_spin)
        
        human_check = QCheckBox()
        human_check.setChecked(settings.get("human_move", True))
        form.addRow("拟人化移动:", human_check)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            self.project["_settings"] = {
                "global_variance": variance_spin.value(),
                "global_offset_x": offset_x_spin.value(),
                "global_offset_y": offset_y_spin.value(),
                "human_move": human_check.isChecked()
            }
            self.modified = True
            self.update_title()
    
    def new_project(self):
        if self.modified:
            reply = QMessageBox.question(self, "保存", "是否保存当前项目?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_project()
            elif reply == QMessageBox.Cancel:
                return
        
        self.project = {"_settings": {"global_variance": 5, "human_move": True}, "main": []}
        self.current_file = None
        self.modified = False
        self.refresh_module_list()
        self.update_title()
    
    def open_project(self):
        if self.modified:
            reply = QMessageBox.question(self, "保存", "是否保存当前项目?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_project()
            elif reply == QMessageBox.Cancel:
                return
        
        path, _ = QFileDialog.getOpenFileName(self, "打开脚本", "", "JSON文件 (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.project = json.load(f)
                self.current_file = path
                self.modified = False
                self.refresh_module_list()
                self.update_title()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开失败: {e}")
    
    def save_project(self):
        if not self.current_file:
            self.save_project_as()
            return
        
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.project, f, ensure_ascii=False, indent=4)
            self.modified = False
            self.update_title()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存脚本", "project.json", "JSON文件 (*.json)")
        if path:
            self.current_file = path
            self.save_project()
    
    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, "保存", "是否保存当前项目?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_project()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    editor = ScriptEditor()
    editor.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
