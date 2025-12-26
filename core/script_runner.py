"""
脚本运行器 - 核心执行引擎
"""

import time
import re
import random
from .capture import ScreenCapture
from .input_controller import InputController
from .ocr_engine import get_ocr_engine
from .vision_engine import VisionEngine

class ScriptAPI:
    """注入到 Python 代码块的 API"""
    
    def __init__(self, runner):
        self.runner = runner
        self._pending_jump = None

    # ============================
    # 1. 系统与调试
    # ============================
    def log(self, msg):
        """输出日志"""
        print(f"[Script] {msg}")

    def sleep(self, seconds):
        """暂停（秒）"""
        time.sleep(seconds)

    def jump(self, label):
        """跳转到标签"""
        self._pending_jump = label

    def stop(self):
        """停止脚本"""
        self.runner.running = False

    # ============================
    # 2. 变量存取
    # ============================
    def set_var(self, name, value):
        """设置全局变量"""
        self.runner.variables[name] = value

    def get_var(self, name, default=None):
        """获取全局变量"""
        return self.runner.variables.get(name, default)

    # ============================
    # 3. 鼠标控制
    # ============================
    def click(self, x, y, button='left', human=False):
        """点击"""
        self.runner.input.click(x, y, button, human=human)

    def double_click(self, x, y, human=False):
        """双击"""
        self.runner.input.double_click(x, y, human=human)

    def triple_click(self, x, y, human=False):
        """三连击"""
        self.runner.input.click(x, y, 'left', clicks=3, human=human)

    def right_click(self, x, y, human=False):
        """右键点击"""
        self.runner.input.click(x, y, 'right', human=human)

    def middle_click(self, x, y, human=False):
        """中键点击"""
        self.runner.input.click(x, y, 'middle', human=human)

    def move(self, x, y, human=False):
        """移动鼠标"""
        self.runner.input.move(x, y, human=human)

    def move_human(self, x, y, duration=None):
        """贝塞尔曲线擬人化移动"""
        self.runner.input.move_human(x, y, duration)

    def drag(self, x1, y1, x2, y2, duration=0.5, human=False):
        """拖拽"""
        self.runner.input.drag(x1, y1, x2, y2, duration, human=human)

    def mouse_down(self, button='left'):
        """按下鼠标"""
        self.runner.input.mouse_down(button)

    def mouse_up(self, button='left'):
        """释放鼠标"""
        self.runner.input.mouse_up(button)

    def scroll(self, steps):
        """滚轮（正数向上）"""
        self.runner.input.scroll(steps)

    def get_mouse_pos(self):
        """获取当前鼠标位置"""
        return self.runner.input.get_position()

    # ============================
    # 4. 键盘控制
    # ============================
    def key(self, key):
        """按键"""
        self.runner.input.key_press(key)

    def type(self, text):
        """输入文字"""
        self.runner.input.type_text(text)

    def key_down(self, key):
        """按下按键"""
        self.runner.input.key_down(key)

    def key_up(self, key):
        """释放按键"""
        self.runner.input.key_up(key)

    def key_hold(self, key, duration):
        """按住按键一段时间"""
        self.runner.input.key_hold(key, duration)

    def hotkey(self, *keys):
        """组合键"""
        self.runner.input.hotkey(*keys)

    # ============================
    # 5. 视觉识别
    # ============================
    def ocr(self, region=None):
        """OCR 识别，返回完整文字"""
        img = self.runner.capture.capture()
        if img:
            return self.runner.ocr.get_text(img, region)
        return ""

    def ocr_detect(self, region=None):
        """OCR 识别，返回详细结果列表"""
        img = self.runner.capture.capture()
        if img:
            return self.runner.ocr.detect(img, region)
        return []

    def find_image(self, target, confidence=0.8, region=None):
        """
        找图
        :return: (center_x, center_y) 或 None
        """
        img = self.runner.capture.capture()
        if img:
            return self.runner.vision.find_best(img, target, confidence, region)
        return None

    def find_all_images(self, target, confidence=0.8, region=None):
        """
        找所有匹配的图
        :return: [(x, y, w, h, score), ...]
        """
        img = self.runner.capture.capture()
        if img:
            return self.runner.vision.find_template(img, target, confidence, region)
        return []

    def find_text(self, text, index=1, region=None):
        """
        找文字坐标
        :param text: 目标文字
        :param index: 第几个匹配（从1开始）
        :return: (center_x, center_y) 或 None
        """
        img = self.runner.capture.capture()
        if not img:
            return None
        
        results = self.runner.ocr.detect(img, region)
        count = 0
        for r in results:
            if text in r['text']:
                count += 1
                if count == index:
                    x, y, w, h = r['rect']
                    return (x + w // 2, y + h // 2)
        return None

    def find_and_click(self, target, confidence=0.8, button='left', region=None, 
                       offset_x=0, offset_y=0, human=False):
        """
        找图并点击
        :return: True 找到并点击，False 未找到
        """
        pos = self.find_image(target, confidence, region)
        if pos:
            x, y = pos[0] + offset_x, pos[1] + offset_y
            if button == 'double':
                self.double_click(x, y, human=human)
            elif button == 'right':
                self.right_click(x, y, human=human)
            else:
                self.click(x, y, button, human=human)
            return True
        return False

    def click_text(self, text, index=1, button='left', region=None,
                   offset_x=0, offset_y=0, human=False):
        """
        找文字并点击
        :return: True 找到并点击，False 未找到
        """
        pos = self.find_text(text, index, region)
        if pos:
            x, y = pos[0] + offset_x, pos[1] + offset_y
            if button == 'double':
                self.double_click(x, y, human=human)
            elif button == 'right':
                self.right_click(x, y, human=human)
            else:
                self.click(x, y, button, human=human)
            return True
        return False

    def get_color(self, x, y):
        """
        获取某点颜色
        :return: (r, g, b) 或 None
        """
        img = self.runner.capture.capture()
        if not img:
            return None
        x = max(0, min(x, img.width - 1))
        y = max(0, min(y, img.height - 1))
        pixel = img.getpixel((x, y))
        # 处理 RGBA
        if len(pixel) == 4:
            return pixel[:3]
        return pixel

    def screenshot(self, region=None):
        """
        截图
        :return: PIL Image 或 None
        """
        img = self.runner.capture.capture()
        if img and region:
            x, y, w, h = region
            img = img.crop((x, y, x + w, y + h))
        return img

    @property
    def engine(self):
        """兼容原项目的 api.engine 访问"""
        return self.runner

    @property
    def variables(self):
        """直接访问变量字典"""
        return self.runner.variables


class ScriptRunner:
    def __init__(self, debug=False, input_driver='win32'):
        self.debug = debug
        self.project = {}
        self.current_module = ""
        self.script = []
        self.step_index = 0
        self.call_stack = []
        self.running = False
        self.variables = {}
        
        # 引擎
        self.capture = ScreenCapture()
        self.input = InputController(driver=input_driver)
        self.ocr = get_ocr_engine()
        self.vision = VisionEngine()

    def load_project(self, project_data):
        self.project = project_data.copy()
        
        # 读取设置
        settings = self.project.get('_settings', {})
        
        # 误差设置
        variance = settings.get('global_variance', 0)
        self.input.set_variance(variance)
        
        # 全局偏移
        offset_x = settings.get('global_offset_x', 0)
        offset_y = settings.get('global_offset_y', 0)
        self.input.set_global_offset(offset_x, offset_y)
        
        # 擬人化移动默认开关
        self.human_move = settings.get('human_move', False)
        
        print(f"[Runner] 项目加载完成，共 {len(self.project)} 个模块")
        print(f"[Runner] 误差: {variance}, 偏移: ({offset_x}, {offset_y}), 擬人化: {self.human_move}")

    def run(self, entry='main'):
        """运行脚本"""
        if entry not in self.project:
            print(f"[Runner] 找不到入口模块: {entry}")
            return

        # 初始化
        self.capture.init()
        self.ocr.initialize()
        
        self.current_module = entry
        self.script = self.project[entry]
        self.step_index = 0
        self.call_stack = []
        self.running = True

        # 构建标签映射
        label_map = self._build_label_map(self.script)

        while self.running and self.step_index < len(self.script):
            cmd = self.script[self.step_index]
            action = cmd.get('action')
            params = cmd.get('params', {})

            if self.debug:
                print(f"[DEBUG] #{self.step_index} {action}: {params}")

            # 流程控制
            if action == 'label':
                self.step_index += 1
                continue

            elif action == 'jump':
                target = params.get('target')
                if target in label_map:
                    self.step_index = label_map[target]
                    continue
                else:
                    print(f"[Runner] 找不到标签: {target}")

            elif action == 'exit':
                print("[Runner] 执行 exit")
                break

            elif action == 'call_script':
                target_module = params.get('name')
                if target_module in self.project:
                    self.call_stack.append((self.current_module, self.step_index + 1))
                    self.current_module = target_module
                    self.script = self.project[target_module]
                    self.step_index = 0
                    label_map = self._build_label_map(self.script)
                    continue

            elif action == 'return':
                if self.call_stack:
                    prev_module, prev_index = self.call_stack.pop()
                    self.current_module = prev_module
                    self.script = self.project[prev_module]
                    self.step_index = prev_index
                    label_map = self._build_label_map(self.script)
                    continue
                else:
                    break

            # 条件跳转
            elif action == 'jump_if_found':
                target = params.get('target')
                label = params.get('label')
                threshold = params.get('confidence', 0.8)
                target_type = params.get('type', 'image')
                region = params.get('region')

                found = self._check_found(target, target_type, threshold, region)
                if found and label in label_map:
                    self.step_index = label_map[label]
                    continue

            elif action == 'check_value_jump':
                if self._check_value(params):
                    label = params.get('label')
                    if label in label_map:
                        self.step_index = label_map[label]
                        continue

            # 执行普通指令
            else:
                result = self._execute_action(action, params)
                
                # 处理 Python 代码块的跳转
                if isinstance(result, tuple) and result[0] == 'JUMP':
                    jump_label = result[1]
                    if jump_label in label_map:
                        self.step_index = label_map[jump_label]
                        continue

            self.step_index += 1

        # 脚本结束，检查调用栈
        if self.call_stack:
            prev_module, prev_index = self.call_stack.pop()
            self.current_module = prev_module
            self.script = self.project[prev_module]
            self.step_index = prev_index
            label_map = self._build_label_map(self.script)
            self.run(self.current_module)

    def _build_label_map(self, script):
        """构建标签索引"""
        labels = {}
        for i, cmd in enumerate(script):
            if cmd.get('action') == 'label':
                name = cmd.get('params', {}).get('name')
                if name:
                    labels[name] = i
        return labels

    def _check_found(self, target, target_type, threshold, region):
        """检查目标是否存在"""
        img = self.capture.capture()
        if not img:
            return False

        if target_type == 'text':
            results = self.ocr.detect(img, region)
            for r in results:
                if target in r['text']:
                    return True
            return False
        else:
            # 图片匹配
            result = self.vision.find_best(img, target, threshold, region)
            return result is not None

    def _check_value(self, params):
        """检查数值条件"""
        region = params.get('region')
        op = params.get('op', '>')
        value = params.get('value', 0)

        img = self.capture.capture()
        if not img:
            return False

        text = self.ocr.get_text(img, region)
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return False

        num = int(numbers[0])
        
        if op == '>':
            return num > value
        elif op == '<':
            return num < value
        elif op == '>=':
            return num >= value
        elif op == '<=':
            return num <= value
        elif op == '==':
            return num == value
        elif op == '!=':
            return num != value
        return False

    def _execute_action(self, action, params):
        """执行单个指令"""
        
        # 是否使用擬人化移动（指令级别可覆盖全局设置）
        human = params.get('human', self.human_move)
        
        # ===== 等待 =====
        if action == 'wait':
            time.sleep(params.get('seconds', 1.0))

        # ===== 鼠标操作 =====
        elif action == 'click':
            x, y = params.get('x'), params.get('y')
            button = params.get('button', 'left')
            if x is not None and y is not None:
                self.input.click(x, y, button, human=human)
                print(f"[Action] 点击 ({x}, {y}){' [擬人化]' if human else ''}")

        elif action == 'double_click':
            x, y = params.get('x'), params.get('y')
            if x is not None and y is not None:
                self.input.double_click(x, y, human=human)
                print(f"[Action] 双击 ({x}, {y})")

        elif action == 'move':
            x, y = params.get('x'), params.get('y')
            if x is not None and y is not None:
                self.input.move(x, y, human=human)

        elif action == 'move_human':
            x, y = params.get('x'), params.get('y')
            duration = params.get('duration')
            if x is not None and y is not None:
                self.input.move_human(x, y, duration)
                print(f"[Action] 擬人化移动到 ({x}, {y})")

        elif action == 'drag':
            x1, y1 = params.get('x1'), params.get('y1')
            x2, y2 = params.get('x2'), params.get('y2')
            dur = params.get('duration', 0.5)
            self.input.drag(x1, y1, x2, y2, dur, human=human)

        elif action == 'scroll':
            self.input.scroll(params.get('steps', 0))

        # ===== 键盘操作 =====
        elif action == 'type':
            self.input.type_text(params.get('text', ''))
            print(f"[Action] 输入: {params.get('text', '')}")

        elif action == 'key_hold':
            key = params.get('key')
            dur = params.get('duration', 0.1)
            self.input.key_hold(key, dur)
            print(f"[Action] 按住 {key} {dur}s")

        elif action == 'key_down':
            self.input.key_down(params.get('key'))

        elif action == 'key_up':
            self.input.key_up(params.get('key'))

        elif action == 'key_combo':
            keys = params.get('keys', '').replace(',', '+').split('+')
            keys = [k.strip() for k in keys if k.strip()]
            if keys:
                self.input.hotkey(*keys)

        # ===== 视觉操作 =====
        elif action == 'find_and_click':
            target = params.get('target')
            threshold = params.get('confidence', 0.8)
            button = params.get('button', 'left')
            region = params.get('region')
            offset_x = params.get('offset_x', 0)
            offset_y = params.get('offset_y', 0)

            img = self.capture.capture()
            if img:
                pos = self.vision.find_best(img, target, threshold, region)
                if pos:
                    x, y = pos[0] + offset_x, pos[1] + offset_y
                    if button == 'double':
                        self.input.double_click(x, y, human=human)
                    else:
                        self.input.click(x, y, button, human=human)
                    print(f"[Action] 找到 {target} 并点击 ({x}, {y})")

        elif action == 'click_text':
            text = params.get('text')
            index = params.get('index', 1)
            region = params.get('region')
            offset_x = params.get('offset_x', 0)
            offset_y = params.get('offset_y', 0)
            button = params.get('button', 'left')

            img = self.capture.capture()
            if img:
                results = self.ocr.detect(img, region)
                count = 0
                for r in results:
                    if text in r['text']:
                        count += 1
                        if count == index:
                            rx, ry, rw, rh = r['rect']
                            x = rx + rw // 2 + offset_x
                            y = ry + rh // 2 + offset_y
                            
                            if button == 'drag':
                                dx = params.get('drag_dx', 0)
                                dy = params.get('drag_dy', 0)
                                self.input.drag(x, y, x + dx, y + dy, human=human)
                            elif button == 'double':
                                self.input.double_click(x, y, human=human)
                            else:
                                self.input.click(x, y, button, human=human)
                            print(f"[Action] 找到文字 '{text}' 并点击 ({x}, {y})")
                            break

        elif action == 'click_text_sequence':
            texts = params.get('text', '').split(',')
            interval = params.get('interval', 0.2)
            region = params.get('region')

            for t in texts:
                t = t.strip()
                if not t:
                    continue
                img = self.capture.capture()
                if img:
                    results = self.ocr.detect(img, region)
                    for r in results:
                        if t in r['text']:
                            rx, ry, rw, rh = r['rect']
                            x, y = rx + rw // 2, ry + rh // 2
                            self.input.click(x, y)
                            print(f"[Action] 点击文字序列: {t}")
                            break
                time.sleep(interval)

        # ===== Python 代码块 =====
        elif action == 'run_python':
            code = params.get('code', '')
            return self._run_python(code)

        return None

    def _run_python(self, code):
        """执行内嵌 Python 代码"""
        api = ScriptAPI(self)
        
        # 构建执行环境
        exec_globals = {
            'api': api,
            're': re,
            'time': time,
            'random': random,
        }
        
        # 尝试导入 PIL
        try:
            from PIL import Image, ImageDraw
            exec_globals['Image'] = Image
            exec_globals['ImageDraw'] = ImageDraw
        except:
            pass

        try:
            exec(code, exec_globals)
            
            # 检查是否有跳转请求
            if api._pending_jump:
                return ('JUMP', api._pending_jump)
                
        except Exception as e:
            print(f"[Python] 执行错误: {e}")
            import traceback
            traceback.print_exc()

        return None

    def stop(self):
        """停止执行"""
        self.running = False

    def cleanup(self):
        """清理资源"""
        self.input.release_all()
        self.capture.release()
        self.vision.release()
