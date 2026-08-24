#!/usr/bin/env python3
"""
测试运行脚本
用于运行用户模块的接口测试
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """主函数"""
    # 设置环境变量
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    # 构建pytest命令
    pytest_args = [
        "python", "-m", "pytest",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误跟踪
        "--color=yes",  # 彩色输出
        "--disable-warnings",  # 禁用警告
        "test/api/test_api_users.py",  # 用户模块测试
        "test/api/test_api_auth.py",  # 认证模块测试
    ]
    
    # 如果有命令行参数，添加到pytest参数中
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    
    print("运行用户模块接口测试...")
    print(f"命令: {' '.join(pytest_args)}")
    print("-" * 50)
    
    try:
        # 运行测试
        result = subprocess.run(pytest_args, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    pytest_args = [
        "python", "-m", "pytest",
        "-v",
        "--tb=short",
        "--color=yes",
        f"test/api/{test_file}",
    ]
    
    print(f"运行测试文件: {test_file}")
    print(f"命令: {' '.join(pytest_args)}")
    print("-" * 50)
    
    result = subprocess.run(pytest_args)
    return result.returncode


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    pytest_args = [
        "python", "-m", "pytest",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v",
        "test/api/test_api_users.py",
        "test/api/test_api_auth.py",
    ]
    
    print("运行测试并生成覆盖率报告...")
    print(f"命令: {' '.join(pytest_args)}")
    print("-" * 50)
    
    result = subprocess.run(pytest_args)
    return result.returncode


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--coverage":
            sys.exit(run_with_coverage())
        elif sys.argv[1].endswith(".py"):
            sys.exit(run_specific_test(sys.argv[1]))
    
    # 运行默认测试
    sys.exit(main())
