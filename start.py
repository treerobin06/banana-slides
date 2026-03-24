#!/usr/bin/env python3
"""
Banana Slides 一键启动脚本
同时启动后端 (Flask) 和前端 (Vite) 服务

使用方法:
    python start.py          # 启动所有服务
    python start.py --backend   # 仅启动后端
    python start.py --frontend  # 仅启动前端
    python start.py --install   # 安装依赖后启动
"""

import subprocess
import sys
import os
import signal
import time
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 服务配置
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# 全局进程列表
processes = []


def print_banner():
    """打印启动横幅"""
    print("\n" + "=" * 50)
    print("🍌 Banana Slides 一键启动脚本 🍌")
    print("=" * 50)
    print(f"📁 项目目录: {PROJECT_ROOT}")
    print("=" * 50 + "\n")


def check_requirements():
    """检查必要的工具是否安装（宽松检查，只检查是否存在）"""
    warnings = []
    
    # 检查 Python
    print("🔍 检查 Python...", end=" ")
    if sys.version_info < (3, 10):
        warnings.append("Python 版本建议 >= 3.10")
        print(f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} (建议 3.10+)")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # 检查 uv（仅检查是否存在，不检查版本）
    print("🔍 检查 uv...", end=" ")
    try:
        result = subprocess.run(
            ["uv", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            warnings.append("uv 未安装，请运行: pip install uv 或 curl -LsSf https://astral.sh/uv/install.sh | sh")
            print("❌")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        warnings.append("uv 未安装，请运行: pip install uv 或 curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("❌")
    
    # 检查 Node.js（仅检查是否存在）
    print("🔍 检查 Node.js...", end=" ")
    try:
        result = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            warnings.append("Node.js 未安装")
            print("❌")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        warnings.append("Node.js 未安装，请从 https://nodejs.org 下载安装")
        print("❌")
    
    # 检查 npm（仅检查是否存在）
    print("🔍 检查 npm...", end=" ")
    try:
        result = subprocess.run(
            ["npm", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            warnings.append("npm 未安装")
            print("❌")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        warnings.append("npm 未安装")
        print("❌")
    
    print()
    
    if warnings:
        print("⚠️  环境检查警告（如果依赖已安装，可忽略）:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
        response = input("是否继续? (Y/n): ").strip().lower()
        if response and response != 'y':
            return False
    
    print("✅ 环境检查通过\n")
    return True


def check_env_file():
    """检查 .env 文件是否存在"""
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env 文件不存在，从 .env.example 复制...")
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env 文件已创建，请编辑填入 API 密钥\n")
        else:
            print("⚠️  .env 和 .env.example 都不存在")
            print("   请创建 .env 文件并配置必要的环境变量\n")
            return False
    else:
        print("✅ .env 文件存在\n")
    
    return True


def check_and_install_dependencies():
    """检查并安装依赖（如果未安装）"""
    # 检查后端依赖（检查 .venv 或 uv.lock）
    print("🔍 检查后端依赖...", end=" ", flush=True)
    venv_exists = (PROJECT_ROOT / ".venv").exists()
    uv_lock_exists = (PROJECT_ROOT / "uv.lock").exists()
    
    if venv_exists or uv_lock_exists:
        print("✅ (依赖已存在)")
        print("   如需重新安装，请手动运行: uv sync\n")
    else:
        print("⚠️  (未检测到依赖)")
        response = input("   是否现在安装后端依赖? (Y/n): ").strip().lower()
        if not response or response == 'y':
            print("📦 安装后端依赖...")
            result = subprocess.run(
                ["uv", "sync"],
                cwd=PROJECT_ROOT,
                shell=(os.name == 'nt'),
                timeout=300
            )
            if result.returncode != 0:
                print("❌ 后端依赖安装失败")
                return False
            print("✅ 后端依赖安装完成\n")
        else:
            print("⚠️  跳过后端依赖安装\n")
    
    # 检查前端依赖（检查 node_modules）
    print("🔍 检查前端依赖...", end=" ", flush=True)
    node_modules_exists = (FRONTEND_DIR / "node_modules").exists()
    
    if node_modules_exists:
        print("✅ (依赖已存在)")
        print("   如需重新安装，请手动运行: cd frontend && npm install\n")
    else:
        print("⚠️  (未检测到依赖)")
        response = input("   是否现在安装前端依赖? (Y/n): ").strip().lower()
        if not response or response == 'y':
            print("📦 安装前端依赖...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=FRONTEND_DIR,
                shell=(os.name == 'nt'),
                timeout=300
            )
            if result.returncode != 0:
                print("❌ 前端依赖安装失败")
                return False
            print("✅ 前端依赖安装完成\n")
        else:
            print("⚠️  跳过前端依赖安装\n")
    
    return True


def install_dependencies():
    """强制安装依赖（用于 --install 参数）"""
    print("📦 安装后端依赖...")
    result = subprocess.run(
        ["uv", "sync"],
        cwd=PROJECT_ROOT,
        shell=(os.name == 'nt'),
        timeout=300
    )
    if result.returncode != 0:
        print("❌ 后端依赖安装失败")
        return False
    print("✅ 后端依赖安装完成\n")
    
    print("📦 安装前端依赖...")
    result = subprocess.run(
        ["npm", "install"],
        cwd=FRONTEND_DIR,
        shell=(os.name == 'nt'),
        timeout=300
    )
    if result.returncode != 0:
        print("❌ 前端依赖安装失败")
        return False
    print("✅ 前端依赖安装完成\n")
    
    return True


def start_backend():
    """启动后端服务"""
    print(f"🚀 启动后端服务 (端口 {BACKEND_PORT})...")
    
    # 确保目录存在
    (BACKEND_DIR / "instance").mkdir(exist_ok=True)
    (PROJECT_ROOT / "uploads").mkdir(exist_ok=True)
    
    # 启动后端服务（uv run python app.py）
    if os.name == 'nt':
        cmd = "uv run python app.py"
        process = subprocess.Popen(
            cmd,
            cwd=BACKEND_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            ["uv", "run", "python", "app.py"],
            cwd=BACKEND_DIR,
            preexec_fn=os.setsid
        )
    
    processes.append(("backend", process))
    print(f"✅ 后端服务已启动 (PID: {process.pid})")
    print(f"   📍 API 地址: http://localhost:{BACKEND_PORT}")
    print(f"   📍 健康检查: http://localhost:{BACKEND_PORT}/health\n")
    
    return process


def start_frontend():
    """启动前端服务"""
    print(f"🚀 启动前端服务 (端口 {FRONTEND_PORT})...")
    
    # Windows 使用 shell=True
    if os.name == 'nt':
        cmd = "npm run dev"
        process = subprocess.Popen(
            cmd,
            cwd=FRONTEND_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            preexec_fn=os.setsid
        )
    
    processes.append(("frontend", process))
    print(f"✅ 前端服务已启动 (PID: {process.pid})")
    print(f"   📍 访问地址: http://localhost:{FRONTEND_PORT}\n")
    
    return process


def cleanup(signum=None, frame=None):
    """清理并关闭所有进程"""
    print("\n\n🛑 正在关闭服务...")
    
    for name, process in processes:
        try:
            if process.poll() is None:  # 进程仍在运行
                print(f"   关闭 {name} (PID: {process.pid})...")
                if os.name == 'nt':
                    # Windows
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        capture_output=True
                    )
                else:
                    # Linux/Mac
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            print(f"   ⚠️ 关闭 {name} 时出错: {e}")
    
    print("✅ 所有服务已关闭\n")
    sys.exit(0)


def wait_for_backend(timeout=30):
    """等待后端服务启动"""
    import urllib.request
    import urllib.error
    
    print("⏳ 等待后端服务就绪...", end=" ", flush=True)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(f"http://localhost:{BACKEND_PORT}/health", timeout=2)
            if response.status == 200:
                print("✅")
                return True
        except (urllib.error.URLError, ConnectionRefusedError):
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    
    print(" ❌ 超时")
    return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Banana Slides 一键启动脚本")
    parser.add_argument("--backend", action="store_true", help="仅启动后端")
    parser.add_argument("--frontend", action="store_true", help="仅启动前端")
    parser.add_argument("--install", action="store_true", help="安装依赖后启动")
    parser.add_argument("--no-check", action="store_true", help="跳过环境检查")
    args = parser.parse_args()
    
    # 如果没有指定任何选项，则启动所有服务
    start_all = not args.backend and not args.frontend
    
    print_banner()
    
    # 环境检查
    if not args.no_check:
        if not check_requirements():
            sys.exit(1)
    
    # 检查 .env 文件
    if not check_env_file():
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # 安装依赖
    if args.install:
        if not install_dependencies():
            sys.exit(1)
    else:
        # 检查依赖（不强制安装）
        check_and_install_dependencies()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    if os.name == 'nt':
        signal.signal(signal.SIGBREAK, cleanup)
    
    # 启动服务
    try:
        if args.backend or start_all:
            start_backend()
            time.sleep(2)  # 给后端一点启动时间
        
        if args.frontend or start_all:
            if start_all:
                # 等待后端就绪
                wait_for_backend()
            start_frontend()
        
        print("=" * 50)
        print("🎉 所有服务已启动!")
        print("=" * 50)
        if start_all or args.backend:
            print(f"📍 后端 API: http://localhost:{BACKEND_PORT}")
        if start_all or args.frontend:
            print(f"📍 前端界面: http://localhost:{FRONTEND_PORT}")
        print("=" * 50)
        print("\n按 Ctrl+C 停止所有服务\n")
        
        # 等待进程
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} 服务已退出 (返回码: {process.returncode})")
                    cleanup()
            time.sleep(1)
            
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()

