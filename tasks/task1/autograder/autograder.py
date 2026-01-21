"""
Task 1: 线程包装类 - 自动测试
"""

import sys
import os

# 引用公共模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from utils import Autograder

import subprocess
import re
import time

# ==============================================================================
# 配置
# ==============================================================================

# Override ASSIGNMENT_DIR to point to the task1 directory
ASSIGNMENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXECUTABLE = os.path.join(ASSIGNMENT_DIR, "student_code")
SOURCE_FILE = os.path.join(ASSIGNMENT_DIR, "main.cpp")


# ==============================================================================
# 测试代码模板
# ==============================================================================

TEST_CODE = '''
#include <iostream>
#include <thread>
#include <vector>
#include <set>
#include <chrono>
#include <atomic>
#include <mutex>

// 前向声明 Thread 类
class Thread;

// 学生代码中的 Thread 类会被包含进来

// ==============================================================================
// 测试 1: 基本线程创建和执行
// ==============================================================================

std::atomic<bool> g_executed{false};
std::mutex g_output_mutex;

int test_basic_creation() {
    g_executed = false;

    Thread t([](int id) {
        std::lock_guard<std::mutex> lock(g_output_mutex);
        std::cout << "Thread " << id << " is running" << std::endl;
        g_executed = true;
    });

    int thread_id = t.getId();
    std::cout << "Created thread with ID: " << thread_id << std::endl;

    t.start();

    // 等待线程执行
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    if (g_executed) {
        std::cout << "PASS: 线程成功创建并执行" << std::endl;
        return 0;
    } else {
        std::cout << "FAIL: 线程未能执行" << std::endl;
        return 1;
    }
}

// ==============================================================================
// 测试 2: 多线程唯一 ID
// ==============================================================================

int test_unique_ids() {
    std::vector<Thread*> threads;
    std::set<int> ids;

    // 创建 5 个线程
    for (int i = 0; i < 5; ++i) {
        threads.push_back(new Thread([](int id) {
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }));
    }

    // 收集所有 ID
    for (auto* t : threads) {
        int id = t->getId();
        std::cout << "Thread ID: " << id << std::endl;
        ids.insert(id);
    }

    // 检查 ID 唯一性
    bool unique = (ids.size() == threads.size());

    // 启动所有线程
    for (auto* t : threads) {
        t->start();
    }

    // 等待线程完成
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // 清理
    for (auto* t : threads) {
        delete t;
    }

    if (unique) {
        std::cout << "PASS: 所有线程 ID 唯一" << std::endl;
        return 0;
    } else {
        std::cout << "FAIL: 发现重复的线程 ID" << std::endl;
        return 1;
    }
}

// ==============================================================================
// 测试 3: 不同函数类型
// ==============================================================================

std::atomic<int> g_func_count{0};

void standalone_func(int id) {
    std::lock_guard<std::mutex> lock(g_output_mutex);
    std::cout << "Standalone function thread " << id << std::endl;
    g_func_count++;
}

struct Functor {
    void operator()(int id) {
        std::lock_guard<std::mutex> lock(g_output_mutex);
        std::cout << "Functor thread " << id << std::endl;
        g_func_count++;
    }
};

int test_function_types() {
    g_func_count = 0;

    // Lambda
    Thread t1([](int id) {
        std::lock_guard<std::mutex> lock(g_output_mutex);
        std::cout << "Lambda thread " << id << std::endl;
        g_func_count++;
    });

    // 函数对象
    Thread t2(Functor{});

    // 普通函数
    Thread t3(standalone_func);

    t1.start();
    t2.start();
    t3.start();

    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    if (g_func_count == 3) {
        std::cout << "PASS: 支持不同类型的函数对象" << std::endl;
        return 0;
    } else {
        std::cout << "FAIL: 只有 " << g_func_count << "/3 个函数被执行" << std::endl;
        return 1;
    }
}

// ==============================================================================
// 测试 4: 线程 ID 传递正确性
// ==============================================================================

std::atomic<int> g_received_id{-1};

int test_id_passed_correctly() {
    g_received_id = -1;

    Thread t([](int id) {
        g_received_id = id;
    });

    int expected_id = t.getId();
    t.start();

    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    if (g_received_id == expected_id) {
        std::cout << "PASS: 线程 ID 正确传递给函数 (ID=" << expected_id << ")" << std::endl;
        return 0;
    } else {
        std::cout << "FAIL: 期望 ID=" << expected_id << ", 实际收到 ID=" << g_received_id << std::endl;
        return 1;
    }
}

// ==============================================================================
// 主函数 - 运行指定测试
// ==============================================================================

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <test_name>" << std::endl;
        return 1;
    }

    std::string test_name = argv[1];

    if (test_name == "basic_creation") {
        return test_basic_creation();
    } else if (test_name == "unique_ids") {
        return test_unique_ids();
    } else if (test_name == "function_types") {
        return test_function_types();
    } else if (test_name == "id_passed_correctly") {
        return test_id_passed_correctly();
    } else {
        std::cerr << "Unknown test: " << test_name << std::endl;
        return 1;
    }
}
'''


# ==============================================================================
# 测试环境
# ==============================================================================

def setup_test_environment():
    """准备测试环境: 编译学生代码和测试代码"""
    # 写入测试代码
    test_file = os.path.join(ASSIGNMENT_DIR, "autograder", "test_runner.cpp")
    with open(test_file, "w") as f:
        f.write(TEST_CODE)

    # 读取学生代码
    with open(SOURCE_FILE, "r") as f:
        student_code = f.read()

    # 移除 main 函数和 common/utils.cpp include
    student_code = re.sub(r'#include\s+"\.\./common/utils\.cpp"', '', student_code)
    student_code = re.sub(
        r'int\s+main\s*\(\s*\)\s*\{[^}]*return\s+run_autograder\s*\(\s*\)\s*;[^}]*\}',
        '',
        student_code
    )

    # 写入处理后的学生代码
    student_file = os.path.join(ASSIGNMENT_DIR, "autograder", "student_impl.cpp")
    with open(student_file, "w") as f:
        f.write(student_code)

    # 编译
    combined_source = os.path.join(ASSIGNMENT_DIR, "autograder", "combined_test.cpp")
    with open(combined_source, "w") as f:
        f.write('#include "student_impl.cpp"\n')
        f.write('#include "test_runner.cpp"\n')

    result = subprocess.run(
        ["g++", "-std=c++11", "-pthread", "-o", EXECUTABLE, combined_source],
        capture_output=True,
        text=True,
        cwd=ASSIGNMENT_DIR
    )

    if result.returncode != 0:
        raise AssertionError(f"编译失败:\n{result.stderr}")

    return True


def cleanup_test_environment():
    """清理测试环境"""
    files_to_remove = [
        os.path.join(ASSIGNMENT_DIR, "student_code"),
        os.path.join(ASSIGNMENT_DIR, "autograder", "test_runner.cpp"),
        os.path.join(ASSIGNMENT_DIR, "autograder", "student_impl.cpp"),
        os.path.join(ASSIGNMENT_DIR, "autograder", "combined_test.cpp"),
    ]
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
    return True


def run_test_binary(test_name: str, timeout: int = 30) -> tuple:
    """运行测试二进制文件并返回输出"""
    result = subprocess.run(
        [EXECUTABLE, test_name],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=ASSIGNMENT_DIR
    )
    return result.stdout + result.stderr, result.returncode


# ==============================================================================
# 测试函数
# ==============================================================================

def test_basic_creation():
    """测试练习 1: 基本线程创建和执行"""
    output, returncode = run_test_binary("basic_creation")
    print(output)
    if returncode != 0:
        raise AssertionError("线程创建或执行失败")
    return True


def test_unique_ids():
    """测试练习 2: 多线程唯一 ID"""
    output, returncode = run_test_binary("unique_ids")
    print(output)
    if returncode != 0:
        raise AssertionError("线程 ID 不唯一")
    return True


def test_function_types():
    """测试练习 3: 支持不同函数类型"""
    output, returncode = run_test_binary("function_types")
    print(output)
    if returncode != 0:
        raise AssertionError("不支持某些函数类型")
    return True


def test_id_passed_correctly():
    """测试练习 4: 线程 ID 正确传递"""
    output, returncode = run_test_binary("id_passed_correctly")
    print(output)
    if returncode != 0:
        raise AssertionError("线程 ID 未正确传递给函数")
    return True


# ==============================================================================
# 主入口
# ==============================================================================

if __name__ == "__main__":
    grader = Autograder()
    grader.setup = setup_test_environment
    grader.teardown = cleanup_test_environment

    grader.add_part("练习 1: 基本线程创建和执行", test_basic_creation)
    grader.add_part("练习 2: 多线程唯一 ID", test_unique_ids)
    grader.add_part("练习 3: 支持不同函数类型", test_function_types)
    grader.add_part("练习 4: 线程 ID 正确传递", test_id_passed_correctly)

    exit(grader.run())
