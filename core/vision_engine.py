"""
视觉引擎 - 模板匹配
"""

import os
import numpy as np
from cv2 import imread, matchTemplate, cvtColor, TM_CCOEFF_NORMED, COLOR_RGB2BGR
from .utils import find_file, get_resource_path

class VisionEngine:
    def __init__(self):
        self.template_cache = {}

    def find_template(self, screen_pil, template_path, threshold=0.8, region=None):
        """
        模板匹配
        :param screen_pil: PIL Image 截图
        :param template_path: 模板图片路径
        :param threshold: 匹配阈值
        :param region: 搜索区域 (x, y, w, h)
        :return: List[(x, y, w, h, confidence)]
        """
        # 使用工具函数查找模板文件
        found_path = find_file(template_path)
        if found_path:
            template_path = found_path
        else:
            # 尝试 assets 目录
            found_path = get_resource_path(os.path.join('assets', template_path))
            if os.path.exists(found_path):
                template_path = found_path
            else:
                print(f"[Vision] 找不到模板: {template_path}")
                return []

        # 加载模板 (带缓存)
        if template_path not in self.template_cache:
            tpl = imread(template_path)
            if tpl is None:
                return []
            self.template_cache[template_path] = tpl
        template = self.template_cache[template_path]

        # 转换截图
        screen_cv = cvtColor(np.array(screen_pil), COLOR_RGB2BGR)
        
        # 裁剪区域
        offset_x, offset_y = 0, 0
        if region:
            rx, ry, rw, rh = region
            screen_cv = screen_cv[ry:ry+rh, rx:rx+rw]
            offset_x, offset_y = rx, ry

        # 检查尺寸
        th, tw = template.shape[:2]
        sh, sw = screen_cv.shape[:2]
        if th > sh or tw > sw:
            return []

        # 匹配
        res = matchTemplate(screen_cv, template, TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        results = []
        for pt in zip(*loc[::-1]):
            score = res[pt[1], pt[0]]
            x = pt[0] + offset_x
            y = pt[1] + offset_y
            results.append((x, y, tw, th, float(score)))

        if not results:
            return []

        # 按置信度排序
        results.sort(key=lambda r: r[4], reverse=True)

        # NMS 去重
        filtered = []
        for r in results:
            overlap = False
            for f in filtered:
                dist = ((r[0] - f[0])**2 + (r[1] - f[1])**2)**0.5
                if dist < min(tw, th) / 2:
                    overlap = True
                    break
            if not overlap:
                filtered.append(r)

        return filtered

    def find_best(self, screen_pil, template_path, threshold=0.8, region=None):
        """返回最佳匹配的中心点"""
        results = self.find_template(screen_pil, template_path, threshold, region)
        if results:
            x, y, w, h, _ = results[0]
            return (x + w // 2, y + h // 2)
        return None

    def release(self):
        self.template_cache.clear()
