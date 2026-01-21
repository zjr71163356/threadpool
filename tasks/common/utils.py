"""
Task 0: 多线程基础 - 自动测试工具
"""

_AUTOGRADER_PACKAGES = [
    "colorama==0.4.6"
]

# ==============================================================================
# Virtual Environment Setup
# ==============================================================================

def _check_virtualenv():
    import sys
    import os
    import subprocess

    venv_path = os.path.dirname(os.path.abspath(__file__))

    if os.environ.get("VIRTUAL_ENV", None) != venv_path or "VIRTUAL_ENV_BIN" not in os.environ:
        config_path = os.path.join(venv_path, "pyvenv.cfg")
        if not os.path.isfile(config_path):
            print("🔍 创建虚拟环境...")
            subprocess.check_call([sys.executable, "-m", "venv", venv_path])
            print("✅ 虚拟环境创建完成")

        bin_dir = next((bd for bd in ["Scripts", "bin"] if os.path.isdir(os.path.join(venv_path, bd))), None)
        if bin_dir is None:
            raise RuntimeError("找不到虚拟环境的 bin 目录")
        bin_dir = os.path.join(venv_path, bin_dir)

        env = os.environ.copy()
        env["PATH"] = os.pathsep.join([bin_dir, *env.get("PATH", "").split(os.pathsep)])
        env["VIRTUAL_ENV"] = venv_path
        env["VIRTUAL_ENV_BIN"] = bin_dir
        env["VIRTUAL_ENV_PROMPT"] = os.path.basename(venv_path)
        env["PYTHONIOENCODING"] = "utf-8"

        interpreter_path = os.path.join(bin_dir, "python")
        result = subprocess.run([interpreter_path] + sys.argv, env=env)
        sys.exit(result.returncode)

_check_virtualenv()


# ==============================================================================
# Pip Package Installation
# ==============================================================================

def _install_requirement(package: str):
    import subprocess
    import sys
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def _install_requirements():
    import sys
    import subprocess
    import os

    print("⏳ 安装测试依赖...")

    subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for package in _AUTOGRADER_PACKAGES:
        _install_requirement(package)

    REQUIREMENTS = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.isfile(REQUIREMENTS):
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print("✅ 依赖安装完成")

_install_requirements()


# ==============================================================================
# Imports
# ==============================================================================

import os
import subprocess
from dataclasses import dataclass
from typing import Callable, List, Optional, Union
from colorama import Fore, init, Style, Back

init()

# ==============================================================================
# Autograder Core
# ==============================================================================

ASSIGNMENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
AUTOGRADER_DIR = os.path.join(ASSIGNMENT_DIR, "autograder")

TestFunction = Callable[[], Union[bool, None]]

@dataclass(frozen=True)
class TestPart:
    name: str
    func: TestFunction
    special: bool = False

class Autograder:
    def __init__(self):
        self.parts: List[TestPart] = []
        self.setup: Optional[TestFunction] = None
        self.teardown: Optional[TestFunction] = None

    def add_part(self, name: str, func: Callable[[], bool]) -> None:
        self.parts.append(TestPart(name, func))

    def run(self) -> int:
        parts = self.parts.copy()
        if self.setup:
            parts.insert(0, TestPart("测试环境准备", self.setup, True))
        if self.teardown:
            parts.append(TestPart("测试环境清理", self.teardown, True))

        failures = 0
        passed = 0

        for part in parts:
            header = f"🧪 测试: {part.name}".ljust(60)
            print(f"\n{Back.CYAN}{Fore.LIGHTWHITE_EX}{header}{Style.RESET_ALL}")

            result = None
            error = None

            try:
                result = part.func()
            except Exception as e:
                error = e
                result = False

            if result is None or result:
                if not part.special:
                    print(f"{Fore.GREEN}✅ {part.name} 通过!{Fore.RESET}")
                    passed += 1
            else:
                print(f"{Fore.RED}❌ {part.name} 失败!{Fore.RESET}")
                if error:
                    print(f"{Style.BRIGHT}原因:{Style.DIM} {error}{Style.RESET_ALL}")
                failures += 1

                if part.special:
                    break

        # Summary
        total = passed + failures
        print(f"\n{'='*60}")
        print(f"测试结果: {Fore.GREEN}{passed} 通过{Fore.RESET}, {Fore.RED}{failures} 失败{Fore.RESET} (共 {total} 项)")

        if failures == 0:
            message = "🚀🚀🚀 恭喜! 所有测试通过! 🚀🚀🚀"
            print(f"\n{Back.LIGHTGREEN_EX}{Fore.LIGHTWHITE_EX}{message.center(60)}{Style.RESET_ALL}")
            return 0
        else:
            print(f"\n{Fore.YELLOW}请检查失败的测试，修复后重新运行。{Fore.RESET}")
            return 1
