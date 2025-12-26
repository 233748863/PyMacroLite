"""
工具函数 - 路径处理等
"""

import os
import sys


def get_app_path():
    """
    获取应用程序根目录
    - 开发环境: 返回项目目录
    - Nuitka 打包后: 返回 exe 所在目录
    """
    # Nuitka 打包后会设置 __compiled__ 属性
    if "__compiled__" in dir():
        # 打包后，使用 exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，使用 core 的上级目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    :param relative_path: 相对于应用根目录的路径，如 'libs/WGC.dll' 或 'assets/target.png'
    :return: 绝对路径
    """
    base = get_app_path()
    return os.path.join(base, relative_path)


def find_file(filename, search_dirs=None):
    """
    在多个目录中查找文件
    :param filename: 文件名或相对路径
    :param search_dirs: 额外搜索目录列表
    :return: 找到的绝对路径，或 None
    """
    # 如果是绝对路径且存在，直接返回
    if os.path.isabs(filename) and os.path.exists(filename):
        return filename
    
    # 搜索目录列表
    base = get_app_path()
    dirs = [
        base,                           # 应用根目录
        os.path.join(base, 'assets'),   # assets 目录
        os.path.join(base, 'libs'),     # libs 目录
        os.getcwd(),                    # 当前工作目录
    ]
    
    if search_dirs:
        dirs.extend(search_dirs)
    
    # 在各目录中查找
    for d in dirs:
        full_path = os.path.join(d, filename)
        if os.path.exists(full_path):
            return full_path
    
    return None
