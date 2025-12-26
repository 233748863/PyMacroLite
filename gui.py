"""
PyMacroLite GUI - PySide6 界面（集成脚本编辑器）
"""

import sys
import os
import json

# 设置应用根目录
if "__compiled__" in dir():
    # Nuitka 打包后
    APP_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)  # 切换工作目录，确保相对路径正确

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QGroupBox, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog, QSplitter, 
    QListWidget, QListWidgetItem, QMessageBox, QStatusBar, QTabWidget,
    QDialog, QDialogButtonBox, QFormLayout, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage, QFont, QPalette, QColor

from core.capture import ScreenCapture
from core.ocr_engine import get_ocr_engine
from core.script_runner import ScriptRunner

# ==================== 指令定义 ====================
ACTIONS = {
    "wait": {"name": "⏱️ 等待", "params": [
        ("seconds", "float", "等待秒数", 1.0)
    ]},
    "click": {"name": "🖱️ 点击", "params": [
        ("x", "int", "X坐标", 0),
        ("y", "int", "Y坐标", 0),
        ("button", "choice", "按键", "left", ["left", "right", "middle"]),
        ("human", "bool", "拟人化", True)
    ]},
    "double_click": {"name": "🖱️ 双击", "params": [
        ("x", "int", "X坐标", 0),
        ("y", "int", "Y坐标", 0),
        ("human", "bool", "拟人化", True)
    ]},
    "drag": {"name": "✋ 拖拽", "params": [
        ("x1", "int", "起点X", 0), ("y1", "int", "起点Y", 0),
        ("x2", "int", "终点X", 0), ("y2", "int", "终点Y", 0),
        ("duration", "float", "时长", 0.5), ("human", "bool", "拟人化", True)
    ]},
    "scroll": {"name": "🖱️ 滚轮", "params": [("steps", "int", "格数(正上负下)", 3)]},
    "type": {"name": "⌨️ 输入文字", "params": [("text", "str", "文字", "")]},
    "key_hold": {"name": "⌨️ 按住按键", "params": [
        ("key", "str", "按键", ""), ("duration", "float", "时长", 0.1)
    ]},
    "key_combo": {"name": "⌨️ 组合键", "params": [("keys", "str", "如ctrl+c", "")]},
    "find_and_click": {"name": "🔍 找图点击", "params": [
        ("target", "str", "图片路径", "assets/"),
        ("confidence", "float", "匹配度", 0.8),
        ("button", "choice", "按键", "left", ["left", "right", "double"]),
        ("offset_x", "int", "X偏移", 0), ("offset_y", "int", "Y偏移", 0),
        ("human", "bool", "拟人化", True)
    ]},
    "click_text": {"name": "📝 找字点击", "params": [
        ("text", "str", "目标文字", ""), ("index", "int", "第几个", 1),
        ("button", "choice", "按键", "left", ["left", "right", "double"]),
        ("offset_x", "int", "X偏移", 0), ("offset_y", "int", "Y偏移", 0)
    ]},
    "label": {"name": "🏷️ 标签", "params": [("name", "str", "标签名", "")]},
    "jump": {"name": "↪️ 跳转", "params": [("target", "str", "目标标签", "")]},
    "jump_if_found": {"name": "❓ 条件跳转", "params": [
        ("target", "str", "图片/文字", ""),
        ("type", "choice", "类型", "image", ["image", "text"]),
        ("confidence", "float", "匹配度", 0.8),
        ("label", "str", "跳转标签", "")
    ]},
    "check_value_jump": {"name": "🔢 数值跳转", "params": [
        ("region", "region", "区域", [0, 0, 100, 30]),
        ("op", "choice", "比较", ">", [">", "<", ">=", "<=", "==", "!="]),
        ("value", "int", "比较值", 0), ("label", "str", "跳转标签", "")
    ]},
    "call_script": {"name": "📦 调用模块", "params": [("name", "str", "模块名", "")]},
    "return": {"name": "↩️ 返回", "params": []},
    "exit": {"name": "🛑 退出", "params": []},
    "run_python": {"name": "🐍 Python", "params": [
        ("code", "text", "代码", "api.log('Hello')\n")
    ]}
}

# ==================== 工作线程 ====================
class OCRWorker(QThread):
    finished = Signal(list)
    error = Signal(str)
    def __init__(self, ocr, image):
        super().__init__()
        self.ocr, self.image = ocr, image
    def run(self):
        try: self.finished.emit(self.ocr.detect(self.image))
        except Exception as e: self.error.emit(str(e))

class ScriptWorker(QThread):
    log = Signal(str)
    finished = Signal()
    def __init__(self, runner, entry):
        super().__init__()
        self.runner, self.entry = runner, entry
    def run(self):
        try:
            import builtins
            orig = print
            builtins.print = lambda *a, **k: (self.log.emit(' '.join(str(x) for x in a)), orig(*a, **k))
            self.runner.run(self.entry)
            builtins.print = orig
        except Exception as e: self.log.emit(f"错误: {e}")
        finally: self.finished.emit()

# ==================== 参数编辑对话框 ====================
class ParamDialog(QDialog):
    def __init__(self, action_type, params=None, parent=None):
        super().__init__(parent)
        self.action_type = action_type
        self.widgets = {}
        self._init_ui(params or {})
    
    def _init_ui(self, params):
        action_def = ACTIONS.get(self.action_type, {})
        self.setWindowTitle(f"编辑: {action_def.get('name', self.action_type)}")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        for p in action_def.get("params", []):
            name, ptype, label = p[0], p[1], p[2]
            default = p[3] if len(p) > 3 else ""
            value = params.get(name, default)
            widget = self._make_widget(ptype, p, value)
            self.widgets[name] = (ptype, widget)
            form.addRow(f"{label}:", widget)
        
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
    
    def _make_widget(self, ptype, p, value):
        if ptype == "int":
            w = QSpinBox(); w.setRange(-9999, 9999); w.setValue(int(value or 0))
        elif ptype == "float":
            w = QDoubleSpinBox(); w.setRange(-9999, 9999); w.setDecimals(2); w.setValue(float(value or 0))
        elif ptype == "bool":
            w = QCheckBox(); w.setChecked(bool(value))
        elif ptype == "choice":
            w = QComboBox(); w.addItems(p[4] if len(p) > 4 else [])
            if value in (p[4] if len(p) > 4 else []): w.setCurrentText(str(value))
        elif ptype == "text":
            w = QTextEdit(); w.setPlainText(str(value or "")); w.setMinimumHeight(120)
        elif ptype == "region":
            w = QLineEdit()
            w.setText(f"{value[0]}, {value[1]}, {value[2]}, {value[3]}" if isinstance(value, list) else "0, 0, 100, 30")
        else:
            w = QLineEdit(); w.setText(str(value or ""))
        return w
    
    def get_params(self):
        result = {}
        for name, (ptype, w) in self.widgets.items():
            if ptype == "int": result[name] = w.value()
            elif ptype == "float": result[name] = w.value()
            elif ptype == "bool": result[name] = w.isChecked()
            elif ptype == "choice": result[name] = w.currentText()
            elif ptype == "text": result[name] = w.toPlainText()
            elif ptype == "region":
                try: result[name] = [int(x.strip()) for x in w.text().split(",")][:4]
                except: result[name] = [0, 0, 100, 30]
            else: result[name] = w.text()
        return result

# ==================== 步骤列表项 ====================
class StepItem(QListWidgetItem):
    def __init__(self, action, params):
        self.action, self.params = action, params
        name = ACTIONS.get(action, {}).get("name", action)
        p = params
        if action == "label": text = f"🏷️ [{p.get('name','')}]"
        elif action == "jump": text = f"↪️ → [{p.get('target','')}]"
        elif action == "wait": text = f"⏱️ {p.get('seconds',1)}秒"
        elif action == "click": text = f"🖱️ ({p.get('x',0)}, {p.get('y',0)})"
        elif action == "find_and_click": text = f"🔍 [{p.get('target','')}]"
        elif action == "click_text": text = f"📝 [{p.get('text','')}]"
        elif action == "jump_if_found": text = f"❓ [{p.get('target','')}] → [{p.get('label','')}]"
        elif action == "call_script": text = f"📦 [{p.get('name','')}]"
        elif action == "key_hold": text = f"⌨️ [{p.get('key','')}] {p.get('duration',0.1)}s"
        elif action == "type": text = f"⌨️ [{p.get('text','')[:15]}]"
        elif action == "run_python": text = f"🐍 {p.get('code','')[:25].replace(chr(10),' ')}..."
        elif action == "return": text = "↩️ 返回"
        elif action == "exit": text = "🛑 退出"
        else: text = name
        super().__init__(text)
    def to_dict(self): return {"action": self.action, "params": self.params}

# ==================== 模块编辑器 ====================
class ModuleEditor(QWidget):
    changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = QHBoxLayout()
        self.action_combo = QComboBox()
        for a, info in ACTIONS.items(): self.action_combo.addItem(info['name'], a)
        toolbar.addWidget(self.action_combo)
        
        btn_add = QPushButton("➕ 添加"); btn_add.clicked.connect(self.add_step)
        toolbar.addWidget(btn_add)
        toolbar.addStretch()
        
        for txt, fn in [("⬆️", self.move_up), ("⬇️", self.move_down), ("🗑️", self.delete_step)]:
            b = QPushButton(txt); b.setFixedWidth(36); b.clicked.connect(fn); toolbar.addWidget(b)
        layout.addLayout(toolbar)
        
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QListWidget.InternalMove)
        self.step_list.itemDoubleClicked.connect(self.edit_step)
        layout.addWidget(self.step_list)
    
    def add_step(self):
        action = self.action_combo.currentData()
        dlg = ParamDialog(action, {}, self)
        if dlg.exec() == QDialog.Accepted:
            self.step_list.addItem(StepItem(action, dlg.get_params()))
            self.changed.emit()
    
    def edit_step(self, item):
        if isinstance(item, StepItem):
            dlg = ParamDialog(item.action, item.params, self)
            if dlg.exec() == QDialog.Accepted:
                item.params = dlg.get_params()
                item.setText(StepItem(item.action, item.params).text())
                self.changed.emit()
    
    def delete_step(self):
        r = self.step_list.currentRow()
        if r >= 0: self.step_list.takeItem(r); self.changed.emit()
    
    def move_up(self):
        r = self.step_list.currentRow()
        if r > 0:
            item = self.step_list.takeItem(r)
            self.step_list.insertItem(r-1, item)
            self.step_list.setCurrentRow(r-1)
            self.changed.emit()
    
    def move_down(self):
        r = self.step_list.currentRow()
        if r < self.step_list.count()-1:
            item = self.step_list.takeItem(r)
            self.step_list.insertItem(r+1, item)
            self.step_list.setCurrentRow(r+1)
            self.changed.emit()
    
    def load_steps(self, steps):
        self.step_list.clear()
        for s in steps: self.step_list.addItem(StepItem(s.get("action",""), s.get("params",{})))
    
    def get_steps(self):
        return [self.step_list.item(i).to_dict() for i in range(self.step_list.count()) if isinstance(self.step_list.item(i), StepItem)]

# ==================== 脚本编辑器标签页 ====================
class ScriptEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = {"_settings": {"global_variance": 5, "human_move": True}, "main": []}
        self.current_file = None
        self.modified = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        
        # 左侧模块列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("模块列表"))
        self.module_list = QListWidget()
        self.module_list.currentRowChanged.connect(self._on_module_changed)
        left_layout.addWidget(self.module_list)
        
        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕"); btn_add.clicked.connect(self._add_module)
        btn_del = QPushButton("🗑️"); btn_del.clicked.connect(self._del_module)
        btn_row.addWidget(btn_add); btn_row.addWidget(btn_del)
        left_layout.addLayout(btn_row)
        
        # 右侧编辑区
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        toolbar = QHBoxLayout()
        for txt, fn in [("📄 新建", self._new), ("📂 打开", self._open), ("💾 保存", self._save), ("📥 另存", self._save_as)]:
            b = QPushButton(txt); b.clicked.connect(fn); toolbar.addWidget(b)
        toolbar.addStretch()
        btn_settings = QPushButton("⚙️ 设置"); btn_settings.clicked.connect(self._edit_settings)
        toolbar.addWidget(btn_settings)
        right_layout.addLayout(toolbar)
        
        self.editor = ModuleEditor()
        self.editor.changed.connect(self._on_changed)
        right_layout.addWidget(self.editor)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setSizes([150, 550])
        layout.addWidget(splitter)
        
        self._refresh_modules()
    
    def _refresh_modules(self):
        self.module_list.clear()
        for k in self.project.keys():
            if not k.startswith("_"): self.module_list.addItem(k)
        if self.module_list.count() > 0: self.module_list.setCurrentRow(0)
    
    def _on_module_changed(self, row):
        if row >= 0:
            name = self.module_list.item(row).text()
            self.editor.load_steps(self.project.get(name, []))
    
    def _on_changed(self):
        row = self.module_list.currentRow()
        if row >= 0:
            name = self.module_list.item(row).text()
            self.project[name] = self.editor.get_steps()
            self.modified = True
    
    def _add_module(self):
        name, ok = QInputDialog.getText(self, "新建模块", "名称:")
        if ok and name and name not in self.project:
            self.project[name] = []
            self._refresh_modules()
            self.modified = True
    
    def _del_module(self):
        row = self.module_list.currentRow()
        if row >= 0:
            name = self.module_list.item(row).text()
            if name == "main": QMessageBox.warning(self, "错误", "不能删除main"); return
            if QMessageBox.question(self, "确认", f"删除 [{name}]?") == QMessageBox.Yes:
                del self.project[name]
                self._refresh_modules()
                self.modified = True
    
    def _edit_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("全局设置"); dlg.setMinimumWidth(300)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        s = self.project.get("_settings", {})
        
        var_spin = QSpinBox(); var_spin.setRange(0, 50); var_spin.setValue(s.get("global_variance", 5))
        ox_spin = QSpinBox(); ox_spin.setRange(-9999, 9999); ox_spin.setValue(s.get("global_offset_x", 0))
        oy_spin = QSpinBox(); oy_spin.setRange(-9999, 9999); oy_spin.setValue(s.get("global_offset_y", 0))
        human_chk = QCheckBox(); human_chk.setChecked(s.get("human_move", True))
        
        form.addRow("随机误差:", var_spin)
        form.addRow("X偏移:", ox_spin)
        form.addRow("Y偏移:", oy_spin)
        form.addRow("拟人化:", human_chk)
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if dlg.exec() == QDialog.Accepted:
            self.project["_settings"] = {
                "global_variance": var_spin.value(), "global_offset_x": ox_spin.value(),
                "global_offset_y": oy_spin.value(), "human_move": human_chk.isChecked()
            }
            self.modified = True
    
    def _new(self):
        self.project = {"_settings": {"global_variance": 5, "human_move": True}, "main": []}
        self.current_file = None; self.modified = False
        self._refresh_modules()
    
    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f: self.project = json.load(f)
                self.current_file = path; self.modified = False
                self._refresh_modules()
            except Exception as e: QMessageBox.critical(self, "错误", str(e))
    
    def _save(self):
        if not self.current_file: self._save_as(); return
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.project, f, ensure_ascii=False, indent=4)
            self.modified = False
            QMessageBox.information(self, "保存", "保存成功")
        except Exception as e: QMessageBox.critical(self, "错误", str(e))
    
    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "另存为", "project.json", "JSON (*.json)")
        if path: self.current_file = path; self._save()
    
    def get_project(self): return self.project

# ==================== 运行器标签页 ====================
class RunnerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capture = None
        self.ocr = None
        self.runner = None
        self.project = {}
        self.script_worker = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        
        # 左侧控制面板
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        # 截图设置
        cap_grp = QGroupBox("截图设置")
        cap_layout = QVBoxLayout(cap_grp)
        row = QHBoxLayout()
        row.addWidget(QLabel("窗口:"))
        self.proc_combo = QComboBox(); self.proc_combo.setMinimumWidth(180)
        row.addWidget(self.proc_combo, 1)
        self.btn_refresh = QPushButton("🔄"); self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self._refresh_windows)
        row.addWidget(self.btn_refresh)
        cap_layout.addLayout(row)
        
        row2 = QHBoxLayout()
        self.btn_connect = QPushButton("连接"); self.btn_connect.clicked.connect(self._connect)
        self.btn_capture = QPushButton("截图"); self.btn_capture.clicked.connect(self._capture)
        self.btn_capture.setEnabled(False)
        row2.addWidget(self.btn_connect); row2.addWidget(self.btn_capture)
        cap_layout.addLayout(row2)
        left_layout.addWidget(cap_grp)
        
        # 输入驱动设置
        input_grp = QGroupBox("输入驱动")
        input_layout = QVBoxLayout(input_grp)
        row = QHBoxLayout()
        row.addWidget(QLabel("驱动:"))
        self.input_driver_combo = QComboBox()
        self.input_driver_combo.addItem("Win32 (通用)", "win32")
        self.input_driver_combo.addItem("Logitech (防检测)", "logitech")
        self.input_driver_combo.setToolTip("Logitech 需要罗技鼠标/键盘 + G HUB 软件")
        row.addWidget(self.input_driver_combo)
        input_layout.addLayout(row)
        left_layout.addWidget(input_grp)
        
        # OCR 设置
        ocr_grp = QGroupBox("OCR")
        ocr_layout = QVBoxLayout(ocr_grp)
        row = QHBoxLayout()
        row.addWidget(QLabel("设备:"))
        self.device_combo = QComboBox(); self.device_combo.addItems(["CPU", "GPU"])
        row.addWidget(self.device_combo)
        ocr_layout.addLayout(row)
        self.btn_ocr = QPushButton("OCR测试"); self.btn_ocr.clicked.connect(self._test_ocr)
        ocr_layout.addWidget(self.btn_ocr)
        left_layout.addWidget(ocr_grp)
        
        # 脚本执行
        script_grp = QGroupBox("脚本执行")
        script_layout = QVBoxLayout(script_grp)
        row = QHBoxLayout()
        self.script_path = QLineEdit(); self.script_path.setPlaceholderText("脚本路径")
        self.btn_browse = QPushButton("浏览"); self.btn_browse.clicked.connect(self._browse)
        row.addWidget(self.script_path); row.addWidget(self.btn_browse)
        script_layout.addLayout(row)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("入口:"))
        self.entry_combo = QComboBox()
        row.addWidget(self.entry_combo)
        script_layout.addLayout(row)
        
        row = QHBoxLayout()
        self.btn_run = QPushButton("▶ 运行"); self.btn_run.clicked.connect(self._run)
        self.btn_run.setEnabled(False)
        self.btn_stop = QPushButton("■ 停止"); self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        row.addWidget(self.btn_run); row.addWidget(self.btn_stop)
        script_layout.addLayout(row)
        left_layout.addWidget(script_grp)
        left_layout.addStretch()
        
        # 右侧预览和日志
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        prev_grp = QGroupBox("预览")
        prev_layout = QVBoxLayout(prev_grp)
        self.preview = QLabel("未截图")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(350, 250)
        self.preview.setStyleSheet("background:#2a2a2a; border:1px solid #555;")
        prev_layout.addWidget(self.preview)
        right_layout.addWidget(prev_grp)
        
        log_grp = QGroupBox("日志")
        log_layout = QVBoxLayout(log_grp)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        btn_clear = QPushButton("清空"); btn_clear.clicked.connect(self.log_text.clear)
        log_layout.addWidget(btn_clear)
        right_layout.addWidget(log_grp)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setSizes([280, 520])
        layout.addWidget(splitter)
        
        QTimer.singleShot(100, self._refresh_windows)
    
    def log(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def _refresh_windows(self):
        self.proc_combo.clear()
        import ctypes
        from ctypes import wintypes
        windows = []
        def cb(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    if title.strip():
                        rect = wintypes.RECT()
                        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        w, h = rect.right - rect.left, rect.bottom - rect.top
                        if w > 100 and h > 100: windows.append((title, hwnd, w, h))
            return True
        ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
        windows.sort(key=lambda x: x[0].lower())
        for t, h, w, ht in windows:
            self.proc_combo.addItem(f"{t[:35]}... ({w}x{ht})" if len(t)>35 else f"{t} ({w}x{ht})", h)
        self.log(f"[窗口] 找到 {len(windows)} 个")
    
    def _connect(self):
        hwnd = self.proc_combo.currentData()
        if not hwnd: QMessageBox.warning(self, "警告", "请选择窗口"); return
        self.capture = ScreenCapture()
        if self.capture.init(hwnd=hwnd):
            self.log(f"[截图] 已连接")
            self.btn_capture.setEnabled(True)
        else: self.log("[截图] 连接失败")
    
    def _capture(self):
        if self.capture:
            img = self.capture.capture()
            if img: self.log(f"[截图] {img.size}"); self._show_preview(img)
            else: self.log("[截图] 失败")
    
    def _show_preview(self, pil_img):
        img = pil_img.convert("RGBA")
        qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format_RGBA8888)
        pm = QPixmap.fromImage(qimg).scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(pm)
        self._last_img = pil_img
    
    def _ensure_ocr(self):
        use_gpu = self.device_combo.currentText() == "GPU"
        if self.ocr is None:
            self.ocr = get_ocr_engine(use_gpu=use_gpu)
            self.ocr.initialize()
        elif self.ocr._current_device != use_gpu:
            self.ocr.switch_device(use_gpu)
        return self.ocr.enabled
    
    def _test_ocr(self):
        if not self.capture: QMessageBox.warning(self, "警告", "请先连接窗口"); return
        img = self.capture.capture()
        if not img: self.log("[OCR] 截图失败"); return
        self._show_preview(img)
        self.log("[OCR] 识别中...")
        if not self._ensure_ocr(): self.log("[OCR] 初始化失败"); return
        self.ocr_worker = OCRWorker(self.ocr, img)
        self.ocr_worker.finished.connect(self._on_ocr_result)
        self.ocr_worker.error.connect(lambda e: self.log(f"[OCR] 错误: {e}"))
        self.ocr_worker.start()
    
    def _on_ocr_result(self, results):
        self.log(f"[OCR] 识别到 {len(results)} 个文字:")
        for r in results[:10]:  # 显示前10个
            text = r.get('text', '')
            conf = r.get('conf', 0)
            rect = r.get('rect', (0, 0, 0, 0))
            self.log(f"  [{conf:.0%}] {text} @ ({rect[0]},{rect[1]})")
    
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择脚本", "", "JSON (*.json)")
        if path: self.script_path.setText(path); self._load_script(path)
    
    def _load_script(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f: self.project = json.load(f)
            self.entry_combo.clear()
            self.entry_combo.addItems([k for k in self.project.keys() if not k.startswith('_')])
            self.log(f"[脚本] 已加载: {os.path.basename(path)}")
            self.btn_run.setEnabled(True)
        except Exception as e: self.log(f"[脚本] 加载失败: {e}")
    
    def load_project(self, project):
        """从编辑器加载项目"""
        self.project = project
        self.entry_combo.clear()
        self.entry_combo.addItems([k for k in project.keys() if not k.startswith('_')])
        self.btn_run.setEnabled(True)
        self.log("[脚本] 从编辑器加载")
    
    def _run(self):
        if not self.project or not self.capture: 
            QMessageBox.warning(self, "警告", "请先连接窗口并加载脚本"); return
        entry = self.entry_combo.currentText()
        if not entry: return
        
        # 获取选择的输入驱动
        driver = self.input_driver_combo.currentData()
        self.log(f"[脚本] 执行: {entry} (驱动: {driver})")
        
        self.btn_run.setEnabled(False); self.btn_stop.setEnabled(True)
        self.runner = ScriptRunner(input_driver=driver)
        self.runner.capture = self.capture
        if self.ocr: self.runner.ocr = self.ocr
        self.runner.load_project(self.project)
        self.script_worker = ScriptWorker(self.runner, entry)
        self.script_worker.log.connect(self.log)
        self.script_worker.finished.connect(self._on_finished)
        self.script_worker.start()
    
    def _stop(self):
        if self.runner: self.runner.running = False; self.log("[脚本] 停止中...")
    
    def _on_finished(self):
        self.log("[脚本] 完成")
        self.btn_run.setEnabled(True); self.btn_stop.setEnabled(False)
        self.script_worker = None

# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyMacroLite")
        self.setMinimumSize(950, 650)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._init_ui()
    
    def _init_ui(self):
        container = QWidget()
        container.setObjectName("main")
        container.setStyleSheet("#main{background:#353535;border-radius:8px;}")
        self.setCentralWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet("background:#2d2d2d;border-top-left-radius:8px;border-top-right-radius:8px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)
        
        title = QLabel("PyMacroLite")
        title.setStyleSheet("color:#ddd;font-weight:bold;font-size:13px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        for txt, fn, style in [("─", self.showMinimized, ""), ("□", self._toggle_max, ""), ("✕", self.close, ":hover{background:#e81123;color:white;}")]:
            b = QPushButton(txt)
            b.setStyleSheet(f"QPushButton{{border:none;background:transparent;color:#aaa;font-size:14px;padding:4px 10px;}}QPushButton:hover{{background:#444;}}{style}")
            b.clicked.connect(fn)
            title_layout.addWidget(b)
            if txt == "□": self.btn_max = b
        
        main_layout.addWidget(title_bar)
        
        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane{border:none;} QTabBar::tab{padding:8px 20px;}")
        
        self.editor_tab = ScriptEditorTab()
        self.runner_tab = RunnerTab()
        
        self.tabs.addTab(self.runner_tab, "🎮 运行")
        self.tabs.addTab(self.editor_tab, "📝 编辑")
        
        # 添加"加载到运行"按钮
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # 状态栏
        self.status = QStatusBar()
        self.status.setStyleSheet("background:#2d2d2d;color:#aaa;border-bottom-left-radius:8px;border-bottom-right-radius:8px;")
        self.status.showMessage("就绪")
        main_layout.addWidget(self.status)
    
    def _on_tab_changed(self, idx):
        if idx == 0:  # 切换到运行标签页
            # 自动加载编辑器中的项目
            self.runner_tab.load_project(self.editor_tab.get_project())
    
    def _toggle_max(self):
        if self.isMaximized(): self.showNormal(); self.btn_max.setText("□")
        else: self.showMaximized(); self.btn_max.setText("❐")
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 36:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
    def mouseReleaseEvent(self, e): self._drag_pos = None
    def mouseDoubleClickEvent(self, e):
        if e.position().y() < 36: self._toggle_max()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 深色主题
    p = QPalette()
    p.setColor(QPalette.Window, QColor(53, 53, 53))
    p.setColor(QPalette.WindowText, Qt.white)
    p.setColor(QPalette.Base, QColor(35, 35, 35))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.Text, Qt.white)
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, Qt.white)
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(p)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
