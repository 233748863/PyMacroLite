"""
OCR 引擎 - 基于 RapidOCR (ONNXRuntime 优化版)
支持 CPU/GPU 切换
"""

import os
import numpy as np

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPID = True
except ImportError:
    HAS_RAPID = False
    print("[OCR] 警告: rapidocr_onnxruntime 未安装")
    print("[OCR] 请运行: pip install rapidocr_onnxruntime")


class OCREngine:
    def __init__(self, use_gpu=False):
        """
        :param use_gpu: True 使用 GPU，False 使用 CPU
        """
        self.ocr = None
        self.enabled = False
        self.use_gpu = use_gpu
        self._current_device = None

    def initialize(self, use_gpu=None):
        """初始化 OCR 引擎"""
        if not HAS_RAPID:
            print("[OCR] rapidocr_onnxruntime 未安装")
            return False
            
        if use_gpu is not None:
            self.use_gpu = use_gpu
            
        # 配置相同则跳过
        if self.ocr is not None and self._current_device == self.use_gpu:
            return True
            
        try:
            device = "GPU" if self.use_gpu else "CPU"
            print(f"[OCR] 初始化 RapidOCR ({device})...")
            
            # RapidOCR 配置
            # use_cuda=True 需要 onnxruntime-gpu
            self.ocr = RapidOCR(use_cuda=self.use_gpu)
            
            self.enabled = True
            self._current_device = self.use_gpu
            print(f"[OCR] 初始化完成")
            return True
            
        except Exception as e:
            print(f"[OCR] 初始化失败: {e}")
            if self.use_gpu:
                print("[OCR] GPU 模式需要安装 onnxruntime-gpu")
            self.enabled = False
            return False

    def switch_device(self, use_gpu):
        """切换 CPU/GPU"""
        if use_gpu != self._current_device:
            print(f"[OCR] 切换设备: {'GPU' if use_gpu else 'CPU'}")
            self.ocr = None
            return self.initialize(use_gpu=use_gpu)
        return True

    def detect(self, image_pil, region=None):
        """
        识别图片中的文字
        :param image_pil: PIL Image
        :param region: 可选区域 (x, y, w, h)
        :return: List[dict] - {'text': str, 'conf': float, 'rect': (x,y,w,h)}
        """
        if not self.enabled or image_pil is None:
            return []

        try:
            img_np = np.array(image_pil)
            
            offset_x, offset_y = 0, 0
            if region:
                rx, ry, rw, rh = region
                img_np = img_np[ry:ry+rh, rx:rx+rw]
                offset_x, offset_y = rx, ry

            # RapidOCR 识别
            result, _ = self.ocr(img_np)
            
            if not result:
                return []

            results = []
            for item in result:
                # item: [box, text, score]
                box, text, score = item
                
                # box 是 4 个点的坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                box = np.array(box)
                x_min = int(box[:, 0].min())
                y_min = int(box[:, 1].min())
                x_max = int(box[:, 0].max())
                y_max = int(box[:, 1].max())
                
                results.append({
                    'text': text,
                    'conf': float(score),
                    'rect': (x_min + offset_x, y_min + offset_y, x_max - x_min, y_max - y_min)
                })

            return results

        except Exception as e:
            print(f"[OCR] 识别错误: {e}")
            return []

    def get_text(self, image_pil, region=None):
        """简化接口：返回拼接后的文字"""
        results = self.detect(image_pil, region)
        return " ".join([r['text'] for r in results])

    def release(self):
        """释放资源"""
        self.ocr = None
        self.enabled = False
        self._current_device = None
        print("[OCR] 资源已释放")


# 单例
_instance = None

def get_ocr_engine(use_gpu=False):
    """获取 OCR 引擎单例"""
    global _instance
    if _instance is None:
        _instance = OCREngine(use_gpu=use_gpu)
    return _instance
