"""
PyMacroLite - 轻量级自动化脚本工具
仅保留核心功能：OCR识别 + 模板匹配 + 脚本执行
"""

import sys
import os
import json
import argparse

# 确保可以导入 core 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.script_runner import ScriptRunner

def main():
    parser = argparse.ArgumentParser(description='PyMacroLite - 轻量级自动化脚本')
    parser.add_argument('script', nargs='?', default='project.json', help='脚本文件路径')
    parser.add_argument('--entry', '-e', default='main', help='入口模块名称')
    parser.add_argument('--debug', '-d', action='store_true', help='调试模式')
    args = parser.parse_args()

    print(f"[PyMacroLite] 加载脚本: {args.script}")
    
    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            project = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到脚本文件 {args.script}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 - {e}")
        sys.exit(1)

    runner = ScriptRunner(debug=args.debug)
    runner.load_project(project)
    
    print(f"[PyMacroLite] 开始执行模块: {args.entry}")
    print("按 Ctrl+C 停止执行")
    print("-" * 40)
    
    try:
        runner.run(args.entry)
    except KeyboardInterrupt:
        print("\n[PyMacroLite] 用户中断执行")
    finally:
        runner.cleanup()
        print("[PyMacroLite] 执行结束")

if __name__ == "__main__":
    main()
