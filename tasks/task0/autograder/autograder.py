"""
Task 0: 多线程基础 - 自动测试
"""

from utils import Autograder, ASSIGNMENT_DIR

import os
import subprocess
import re

# ==============================================================================
# 配置
# ==============================================================================

EXECUTABLE = os.path.join(ASSIGNMENT_DIR, "student_code")
SOURCE_FILE = os.path.join(ASSIGNMENT_DIR, "main.cpp")


# ==============================================================================
# 测试代码模板
# ==============================================================================

TEST_CODE = '''
#include <iostream>
#include <thread>
#include <vector>
#include <mutex>
#include <sstream>
#include <algorithm>
#include <cstring>

// 学生代码中的声明
extern std::mutex g_mutex;
extern int g_result;
extern std::mutex g_counter_mutex;
extern int g_counter;

void create_threads();
void compute_sum(int a, int b);
void increment_safe(int iterations);
void increment_unsafe(int iterations);

// ==============================================================================
// 测试 1: create_threads
// ==============================================================================

int test_create_threads() {
    // 重定向 cout 捕获输出
    std::ostringstream captured;
    std::streambuf* old_cout = std::cout.rdbuf(captured.rdbuf());

    create_threads();

    std::cout.rdbuf(old_cout);

    std::string output = captured.str();

    // 检查是否包含所有 5 个线程的输出
    std::vector<bool> found(5, false);
    for (int i = 0; i < 5; ++i) {
        std::string expected = "Hello from thread " + std::to_string(i);
        if (output.find(expected) != std::string::npos) {
            found[i] = true;
        }
    }

    int count = std::count(found.begin(), found.end(), true);

    if (count == 5) {
        std::cout << "PASS: 成功创建 5 个线程并正确打印消息" << std::endl;
        return 0;
    } else {
        std::cout << "FAIL: 只找到 " << count << "/5 个正确的线程输出" << std::endl;
        std::cout << "期望输出包含: Hello from thread 0, Hello from thread 1, ..., Hello from thread 4" << std::endl;
        std::cout << "实际输出:\\n" << output << std::endl;
        return 1;
    }
}

// ==============================================================================
// 测试 2: compute_sum
// ==============================================================================

int test_compute_sum() {
    int failures = 0;

    // 测试 1: 基本加法
    g_result = 0;
    {
        std::thread t(compute_sum, 10, 20);
        t.join();
    }
    if (g_result != 30) {
        std::cout << "FAIL: compute_sum(10, 20) 应该等于 30, 实际得到 " << g_result << std::endl;
        failures++;
    }

    // 测试 2: 负数
    g_result = 0;
    {
        std::thread t(compute_sum, -5, 15);
        t.join();
    }
    if (g_result != 10) {
        std::cout << "FAIL: compute_sum(-5, 15) 应该等于 10, 实际得到 " << g_result << std::endl;
        failures++;
    }

    // 测试 3: 零
    g_result = 999;
    {
        std::thread t(compute_sum, 0, 0);
        t.join();
    }
    if (g_result != 0) {
        std::cout << "FAIL: compute_sum(0, 0) 应该等于 0, 实际得到 " << g_result << std::endl;
        failures++;
    }

    if (failures == 0) {
        std::cout << "PASS: compute_sum 所有测试通过" << std::endl;
        return 0;
    }
    return 1;
}

// ==============================================================================
// 测试 3: increment_safe
// ==============================================================================

int test_increment_safe() {
    const int num_threads = 10;
    const int iterations = 10000;
    const int expected = num_threads * iterations;

    // 多次测试以确保稳定性
    for (int run = 0; run < 3; ++run) {
        g_counter = 0;

        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back(increment_safe, iterations);
        }
        for (auto& t : threads) {
            t.join();
        }

        if (g_counter != expected) {
            std::cout << "FAIL: 第 " << (run + 1) << " 次运行, 期望 " << expected
                      << ", 实际得到 " << g_counter << std::endl;
            std::cout << "提示: 请确保使用 mutex 保护对 g_counter 的访问" << std::endl;
            return 1;
        }
    }

    std::cout << "PASS: increment_safe 所有测试通过 (3 次运行结果稳定)" << std::endl;
    return 0;
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

    if (test_name == "create_threads") {
        return test_create_threads();
    } else if (test_name == "compute_sum") {
        return test_compute_sum();
    } else if (test_name == "increment_safe") {
        return test_increment_safe();
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

    # 移除 main 函数和 autograder include
    student_code = re.sub(r'#include\s+"autograder/utils\.cpp"', '', student_code)
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

def test_create_threads():
    """测试练习 1: create_threads 函数"""
    output, returncode = run_test_binary("create_threads")
    if returncode != 0:
        raise AssertionError(output.strip())
    return True


def test_compute_sum():
    """测试练习 2: compute_sum 函数"""
    output, returncode = run_test_binary("compute_sum")
    if returncode != 0:
        raise AssertionError(output.strip())
    return True


def test_increment_safe():
    """测试练习 3: increment_safe 函数"""
    output, returncode = run_test_binary("increment_safe")
    if returncode != 0:
        raise AssertionError(output.strip())
    return True


# ==============================================================================
# 主入口
# ==============================================================================

if __name__ == "__main__":
    grader = Autograder()
    grader.setup = setup_test_environment
    grader.teardown = cleanup_test_environment

    grader.add_part("练习 1: 创建多个线程 (create_threads)", test_create_threads)
    grader.add_part("练习 2: 参数传递 (compute_sum)", test_compute_sum)
    grader.add_part("练习 3: 修复数据竞争 (increment_safe)", test_increment_safe)

    exit(grader.run())
