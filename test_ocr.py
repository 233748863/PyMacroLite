"""
OCR 引擎测试脚本
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ocr_engine import get_ocr_engine
from core.capture import ScreenCapture

def test_ocr():
    print("=" * 50)
    print("PyMacroLite OCR 测试")
    print("=" * 50)
    
    # 初始化截图 (WGC - 截取记事本)
    capture = ScreenCapture()
    if not capture.init(process_name="notepad.exe"):
        print("截图初始化失败! 请先打开记事本")
        return
    
    # 初始化 OCR (CPU + mobile 轻量模型)
    ocr = get_ocr_engine(use_gpu=False, model_type='mobile')
    ocr.initialize()
    
    if not ocr.enabled:
        print("OCR 初始化失败!")
        return
    
    # 截图
    print("\n[测试] 截取屏幕...")
    img = capture.capture()
    if img is None:
        print("截图失败!")
        return
    print(f"截图尺寸: {img.size}")
    
    # 测试 OCR
    print("\n[测试] 识别记事本内容...")
    start = time.time()
    results = ocr.detect(img)
    elapsed = time.time() - start
    
    print(f"耗时: {elapsed:.2f}s")
    print(f"识别到 {len(results)} 个文本块:")
    for r in results[:10]:
        print(f"  - '{r['text']}' (置信度: {r['conf']:.2f})")
    
    if len(results) > 10:
        print(f"  ... 还有 {len(results) - 10} 个")
    
    # 清理
    capture.release()
    print("\n测试完成!")

if __name__ == "__main__":
    test_ocr()
