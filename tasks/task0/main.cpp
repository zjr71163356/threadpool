/**
 * Task 0: 环境准备与多线程基础 - 实践练习
 *
 * 编译并运行测试:
 *   g++ -std=c++11 -pthread main.cpp -o main && ./main
 *
 * 说明:
 *   请在标记 "TODO" 的地方填写代码，完成后运行程序验证你的实现。
 */

#include <iostream>
#include <thread>
#include <vector>
#include <mutex>
#include "autograder/utils.cpp"

// ============================================================
// 练习 1: 创建多个线程
//
// 任务: 编写函数 thread_hello，让每个线程打印 "Hello from thread X"
//       其中 X 是传入的线程编号 (0-4)
//
// 提示: 使用 std::cout 打印，格式: "Hello from thread 0"
// ============================================================

void thread_hello(int thread_id) {
    // TODO: 打印 "Hello from thread X"，X 是 thread_id
    // 格式必须是: "Hello from thread 0" (含换行)

}

// ============================================================
// 练习 2: 参数传递与结果存储
//
// 任务: 编写函数 compute_sum，计算 a + b 并存储到 g_result 中
//       注意: g_result 是共享变量，需要使用 mutex 保护
//
// 提示: 使用 std::lock_guard<std::mutex> 进行 RAII 风格加锁
// ============================================================

std::mutex g_mutex;
int g_result = 0;

void compute_sum(int a, int b) {
    // TODO: 计算 a + b，并将结果存储到 g_result 中
    // 注意: 必须使用 g_mutex 保护对 g_result 的访问

}

// ============================================================
// 练习 3: 修复数据竞争
//
// 任务: increment_unsafe 函数存在数据竞争
//       请编写 increment_safe 函数，使用 mutex 修复这个问题
//
// 要求: 循环 iterations 次，每次对 g_counter 加 1
// ============================================================

std::mutex g_counter_mutex;
int g_counter = 0;

// 不安全版本 (仅供参考，不要修改)
void increment_unsafe(int iterations) {
    for (int i = 0; i < iterations; ++i) {
        ++g_counter;  // 数据竞争!
    }
}

void increment_safe(int iterations) {
    // TODO: 使用 g_counter_mutex 保护对 g_counter 的访问
    // 循环 iterations 次，每次对 g_counter 加 1

}

// ============================================================
// 主函数 - 运行自动测试
// ============================================================

int main() {
    return run_autograder();
}
