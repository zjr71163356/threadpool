/**
 * Task 0: 环境准备与多线程基础 - 实践练习
 *
 * 编译并运行测试:
 *   g++ -std=c++11 -pthread main.cpp -o main && ./main
 *
 * 说明:
 *   请在标记 "TODO" 的地方填写代码，完成后运行程序验证你的实现。
 */

#include "autograder/utils.cpp"
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>

// ============================================================
// 练习 1: 创建多个线程
//
// 任务: 实现 create_threads 函数
//   1. 创建 5 个线程
//   2. 每个线程打印 "Hello from thread X" (X 是 0-4)
//   3. 等待所有线程完成 (使用 join)
//
// 提示:
//   - 使用 std::vector<std::thread> 存储线程
//   - 可以使用 lambda 表达式或普通函数作为线程函数
//   - 记得对每个线程调用 join()
// ============================================================
std::mutex cout_mtx;
void create_threads()
{
    // TODO: 创建 5 个线程，每个打印 "Hello from thread X"
    // 然后等待所有线程完成
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; i++)
    {
        threads.emplace_back([](int pid)
                             {
                                 std::lock_guard<std::mutex> lock(cout_mtx);
                                 std::cout << "Hello from thread " << pid << std::endl; },
                             i);
    }

    for (auto &thread : threads)
    {
        thread.join();
    }
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

void compute_sum(int a, int b)
{
    std::lock_guard<std::mutex> lock(g_mutex);
    g_result = a + b;
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
void increment_unsafe(int iterations)
{
    for (int i = 0; i < iterations; ++i)
    {
        ++g_counter; // 数据竞争!
    }
}

void increment_safe(int iterations)
{
    // TODO: 使用 g_counter_mutex 保护对 g_counter 的访问
    // 循环 iterations 次，每次对 g_counter 加 1
    for (int i = 0; i < iterations; ++i)
    {
        std::lock_guard<std::mutex> lock(g_counter_mutex);
        ++g_counter; // 数据竞争!
    }
}

// ============================================================
// 主函数 - 运行自动测试
// ============================================================

int main()
{
    return run_autograder();
}
