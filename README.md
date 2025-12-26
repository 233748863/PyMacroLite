# PyMacroLite 使用文档

轻量级游戏自动化脚本工具，支持 OCR 文字识别、模板匹配、鼠标键盘控制。

## 安装依赖

```bash
pip install PySide6 pyautogui opencv-python pillow numpy rapidocr_onnxruntime psutil
```

GPU 加速（可选）：
```bash
pip install onnxruntime-gpu
```

## 启动方式

```bash
cd PyMacroLite
python gui.py
```

## GUI 界面说明

启动后有两个标签页：

### 🎮 运行标签页

用于执行脚本：

1. **选择窗口** - 点击 🔄 刷新按钮，从下拉框选择目标窗口，点击「连接」
2. **测试截图** - 点击「截图」验证 WGC 截图是否正常
3. **测试 OCR** - 选择 CPU/GPU，点击「OCR测试」验证文字识别
4. **加载脚本** - 点击「浏览」选择 JSON 脚本文件，或从编辑器自动加载
5. **运行脚本** - 选择入口模块，点击「▶ 运行」

### 📝 编辑标签页

可视化脚本编辑器：

1. **模块管理** - 左侧列表显示所有模块，可新增/删除
2. **步骤编辑** - 右侧编辑当前模块的步骤
   - 从下拉框选择指令类型，点击「➕ 添加」
   - 双击步骤可编辑参数
   - 使用 ⬆️⬇️ 调整顺序，🗑️ 删除
   - 支持拖拽排序
3. **文件操作** - 新建/打开/保存/另存为
4. **全局设置** - 点击「⚙️ 设置」配置误差、偏移、拟人化等

> 💡 切换到「运行」标签页时，会自动加载编辑器中的项目，无需手动保存再加载。

### 窗口操作

- 无边框深色主题窗口
- 拖拽标题栏移动窗口
- 双击标题栏最大化/还原
- 右上角按钮：最小化、最大化、关闭

---

## 脚本格式

脚本是 JSON 文件，结构如下：

```json
{
  "_settings": {
    "global_variance": 5,
    "global_offset_x": 0,
    "global_offset_y": 0,
    "human_move": true
  },
  "main": [
    {"action": "指令名", "params": {...}}
  ],
  "其他模块": [...]
}
```

- `_settings`: 全局设置（可选）
  - `global_variance`: 随机误差像素（防检测）
  - `global_offset_x/y`: 全局坐标偏移（窗口内偏移）
  - `human_move`: 默认启用贝塞尔曲线擬人化移动
- `main`: 默认入口模块
- 其他键名: 可调用的子模块

---

## 指令列表

### 流程控制

| 指令 | 参数 | 说明 |
|------|------|------|
| `label` | `name` | 定义标签（跳转目标） |
| `jump` | `target` | 无条件跳转到标签 |
| `jump_if_found` | `target`, `label`, `type`, `confidence`, `region` | 找到目标则跳转 |
| `check_value_jump` | `region`, `op`, `value`, `label` | OCR 数值比较跳转 |
| `call_script` | `name` | 调用其他模块 |
| `return` | - | 返回调用处 |
| `exit` | - | 结束脚本 |
| `wait` | `seconds` | 等待（秒） |

### 鼠标操作

| 指令 | 参数 | 说明 |
|------|------|------|
| `click` | `x`, `y`, `button`, `human` | 点击（button: left/right/middle） |
| `double_click` | `x`, `y`, `human` | 双击 |
| `move` | `x`, `y`, `human` | 移动鼠标 |
| `move_human` | `x`, `y`, `duration` | 贝塞尔曲线擬人化移动 |
| `drag` | `x1`, `y1`, `x2`, `y2`, `duration`, `human` | 拖拽 |
| `scroll` | `steps` | 滚轮（正数向上） |

> `human` 参数：`true` 启用贝塞尔曲线擬人化移动，`false` 直接移动。不填则使用全局设置。

### 键盘操作

| 指令 | 参数 | 说明 |
|------|------|------|
| `type` | `text` | 输入文字 |
| `key_hold` | `key`, `duration` | 按住按键 |
| `key_down` | `key` | 按下不放 |
| `key_up` | `key` | 释放按键 |
| `key_combo` | `keys` | 组合键（如 "Ctrl+C"） |

### 视觉操作

| 指令 | 参数 | 说明 |
|------|------|------|
| `find_and_click` | `target`, `confidence`, `button`, `region`, `offset_x`, `offset_y` | 找图并点击 |
| `click_text` | `text`, `index`, `region`, `button`, `offset_x`, `offset_y` | 找文字并点击 |
| `click_text_sequence` | `text`, `interval`, `region` | 依次点击多个文字（逗号分隔） |

### Python 代码块

| 指令 | 参数 | 说明 |
|------|------|------|
| `run_python` | `code` | 执行 Python 代码 |

---

## 示例脚本

### 基础示例：自动登录

```json
{
  "main": [
    {"action": "wait", "params": {"seconds": 2}},
    {"action": "click_text", "params": {"text": "登录", "button": "left"}},
    {"action": "wait", "params": {"seconds": 1}},
    {"action": "click", "params": {"x": 500, "y": 300}},
    {"action": "type", "params": {"text": "username"}},
    {"action": "key_combo", "params": {"keys": "Tab"}},
    {"action": "type", "params": {"text": "password"}},
    {"action": "click_text", "params": {"text": "确定"}}
  ]
}
```

### 循环示例：自动刷怪

```json
{
  "main": [
    {"action": "label", "params": {"name": "loop_start"}},
    
    {"action": "find_and_click", "params": {
      "target": "monster.png",
      "confidence": 0.8
    }},
    {"action": "wait", "params": {"seconds": 0.5}},
    
    {"action": "key_hold", "params": {"key": "1", "duration": 0.1}},
    {"action": "wait", "params": {"seconds": 2}},
    
    {"action": "jump", "params": {"target": "loop_start"}}
  ]
}
```

### 条件跳转示例

```json
{
  "main": [
    {"action": "label", "params": {"name": "check"}},
    
    {"action": "jump_if_found", "params": {
      "target": "boss.png",
      "type": "image",
      "confidence": 0.85,
      "label": "fight_boss"
    }},
    
    {"action": "jump_if_found", "params": {
      "target": "回城",
      "type": "text",
      "label": "go_home"
    }},
    
    {"action": "wait", "params": {"seconds": 1}},
    {"action": "jump", "params": {"target": "check"}},
    
    {"action": "label", "params": {"name": "fight_boss"}},
    {"action": "call_script", "params": {"name": "boss_fight"}},
    {"action": "jump", "params": {"target": "check"}},
    
    {"action": "label", "params": {"name": "go_home"}},
    {"action": "click_text", "params": {"text": "回城"}},
    {"action": "exit"}
  ],
  
  "boss_fight": [
    {"action": "key_hold", "params": {"key": "r", "duration": 0.1}},
    {"action": "wait", "params": {"seconds": 5}},
    {"action": "return"}
  ]
}
```

### Python 代码块示例

```json
{
  "main": [
    {"action": "run_python", "params": {"code": "
# 可以使用 api 对象访问所有功能
text = api.ocr()
api.log(f'识别到: {text}')

if '背包已满' in text:
    api.click(100, 200)
    api.sleep(0.5)
    api.jump('sell_items')
else:
    api.click(300, 400)
"}}
  ]
}
```

---

## Python API 参考

在 `run_python` 代码块中可用的 API：

### 系统与调试
```python
api.log("消息")           # 输出日志
api.sleep(1.5)            # 暂停（秒）
api.jump("label_name")    # 跳转到标签
api.stop()                # 停止脚本
```

### 变量存取
```python
api.set_var("count", 10)              # 设置变量
count = api.get_var("count", 0)       # 获取变量（带默认值）
api.variables["key"] = "value"        # 直接访问变量字典
```

### 鼠标控制
```python
api.click(x, y, button='left', human=False)    # 点击
api.double_click(x, y, human=False)            # 双击
api.triple_click(x, y, human=False)            # 三连击
api.right_click(x, y, human=False)             # 右键
api.middle_click(x, y, human=False)            # 中键
api.move(x, y, human=False)                    # 移动
api.move_human(x, y, duration=None)            # 贝塞尔曲线擬人化移动
api.drag(x1, y1, x2, y2, duration=0.5, human=False)  # 拖拽
api.mouse_down(button='left')                  # 按下鼠标
api.mouse_up(button='left')                    # 释放鼠标
api.scroll(steps)                              # 滚轮（正数向上）
pos = api.get_mouse_pos()                      # 获取鼠标位置
```

### 键盘控制
```python
api.key("enter")                  # 按键
api.type("text")                  # 输入文字
api.key_down("shift")             # 按下
api.key_up("shift")               # 释放
api.key_hold("w", 2.0)            # 按住2秒
api.hotkey("ctrl", "c")           # 组合键
```

### 视觉识别
```python
# OCR
text = api.ocr(region=[x, y, w, h])           # OCR 返回文字
results = api.ocr_detect(region)               # OCR 返回详细列表

# 找图
pos = api.find_image("target.png", confidence=0.8, region=None)
# 返回 (center_x, center_y) 或 None

all_pos = api.find_all_images("target.png", confidence=0.8)
# 返回 [(x, y, w, h, score), ...]

# 找文字
pos = api.find_text("确定", index=1, region=None)
# 返回 (center_x, center_y) 或 None

# 找图并点击
found = api.find_and_click("btn.png", confidence=0.8, button='left', 
                           region=None, offset_x=0, offset_y=0, human=False)
# 返回 True/False

# 找文字并点击
found = api.click_text("确定", index=1, button='left', 
                       region=None, offset_x=0, offset_y=0, human=False)
# 返回 True/False

# 取色
r, g, b = api.get_color(x, y)

# 截图
img = api.screenshot(region=[x, y, w, h])  # 返回 PIL Image
```

---

## 参数说明

### region 区域参数

格式：`[x, y, width, height]`

限制搜索/识别范围，提高速度和准确性。

```json
{"action": "click_text", "params": {
  "text": "确定",
  "region": [100, 200, 300, 100]
}}
```

### confidence 置信度

范围：0.0 ~ 1.0，默认 0.8

值越高匹配越严格，建议：
- 精确匹配：0.9+
- 一般匹配：0.8
- 模糊匹配：0.6~0.7

### button 按钮类型

- `left`: 左键（默认）
- `right`: 右键
- `middle`: 中键
- `double`: 双击
- `drag`: 拖拽（需配合 `drag_dx`, `drag_dy`）

---

## 图片资源

模板图片放在 `assets/` 目录，脚本中可直接使用文件名：

```json
{"action": "find_and_click", "params": {"target": "button.png"}}
```

或使用完整路径：

```json
{"action": "find_and_click", "params": {"target": "assets/button.png"}}
```

---

## 注意事项

1. **WGC 截图**需要 Windows 10 1903+ 版本
2. **管理员权限**可能需要以管理员身份运行才能控制某些游戏
3. **PyAutoGUI 安全机制**：鼠标移到屏幕左上角可紧急中断
4. **坐标系**：所有坐标相对于目标窗口左上角，会自动加上 `global_offset`
5. **擬人化移动**：使用三阶贝塞尔曲线模拟人类鼠标轨迹，带随机控制点和速度变化

---

## 贝塞尔曲线擬人化移动原理

```
起点 -----> 控制点1
                 \
                  \
                   > 控制点2 -----> 终点
```

- 三阶贝塞尔曲线生成平滑弧线路径
- 控制点随机偏移，每次轨迹不同
- 移动速度根据距离自动调整
- 每步添加微小随机延迟
