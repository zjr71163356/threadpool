# Task 2: 固定大小线程池（FIXED 模式）

**预计时间：** 3-5 小时
**难度：** ⭐⭐⭐ 中等

---

## 📖 学习目标

完成本任务后，你将：
- ✅ 理解生产者-消费者模式
- ✅ 掌握 `std::mutex` 和 `std::condition_variable`
- ✅ 理解线程同步的经典问题
- ✅ 实现线程池的核心功能
- ✅ 学会正确处理线程的启动和销毁

---

## 🎯 任务目标

实现一个固定大小的线程池 `ThreadPool`，支持以下功能：

1. 初始化指定数量的工作线程
2. 提交任务到任务队列
3. 工作线程自动从队列中取任务并执行
4. 析构时等待所有任务完成，优雅关闭所有线程

**核心接口：**

```cpp
class ThreadPool {
public:
    ThreadPool();
    ~ThreadPool();

    void start(int initThreadSize);
    void submitTask(Task task);  // Task = std::function<void()>

    // 禁止拷贝
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

private:
    void threadFunc(int threadid);  // 线程函数
    bool checkRunningState() const;

private:
    std::unordered_map<int, std::unique_ptr<Thread>> threads_;

    using Task = std::function<void()>;
    std::queue<Task> taskQue_;
    std::atomic_int taskSize_;

    std::mutex taskQueMtx_;
    std::condition_variable notEmpty_;
    std::condition_variable exitCond_;

    std::atomic_bool isPoolRunning_;
    int initThreadSize_;
};
```

---

## 📖 背景知识

### 1. 生产者-消费者模式

线程池是生产者-消费者模式的经典应用：

```
生产者（主线程）    →  [任务队列]  →  消费者（工作线程）
submitTask()                          threadFunc()
```

**关键问题：**
- 队列为空时，消费者如何等待？ → `condition_variable`
- 多个线程同时访问队列如何保证安全？ → `mutex`
- 如何通知等待的线程？ → `notify_all()` / `notify_one()`

### 2. std::condition_variable 详解

条件变量用于线程间的同步：

```cpp
std::mutex mtx;
std::condition_variable cv;
std::queue<int> queue;

// 生产者
void producer() {
    std::unique_lock<std::mutex> lock(mtx);
    queue.push(42);
    cv.notify_one();  // 通知一个等待的线程
}

// 消费者
void consumer() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, []{ return !queue.empty(); });  // 等待队列非空
    int value = queue.front();
    queue.pop();
}
```

**重要概念：**

#### 虚假唤醒（Spurious Wakeup）
线程可能在没有 `notify` 的情况下醒来，因此必须使用循环检查条件：

```cpp
// ❌ 错误：只检查一次
cv.wait(lock);
if (!queue.empty()) { /* ... */ }

// ✅ 正确：使用 lambda 会自动循环检查
cv.wait(lock, []{ return !queue.empty(); });

// 等价于：
while (queue.empty()) {
    cv.wait(lock);
}
```

#### wait() 的工作流程
```cpp
cv.wait(lock, predicate);
```
1. 原子地释放 `lock` 并进入等待状态
2. 被唤醒后重新获取 `lock`
3. 检查 `predicate`，如果为 `true` 返回，否则继续等待

### 3. 线程池的生命周期

```
[创建] → [配置] → [启动] → [运行] → [关闭] → [销毁]
   ↓        ↓        ↓        ↓        ↓        ↓
构造函数  setXXX   start   submitTask  析构   清理资源
```

**关键状态：**
- `isPoolRunning_`：线程池是否在运行
- 用于在析构时通知所有线程退出

### 4. 线程函数的设计

工作线程的核心逻辑：

```cpp
void threadFunc(int threadid) {
    for (;;) {  // 无限循环
        Task task;
        {
            std::unique_lock<std::mutex> lock(taskQueMtx_);

            // 等待任务或退出信号
            while (taskQue_.empty()) {
                if (!isPoolRunning_) {
                    // 线程池关闭，退出
                    return;
                }
                notEmpty_.wait(lock);
            }

            // 取出任务
            task = taskQue_.front();
            taskQue_.pop();
        }  // 释放锁

        // 执行任务（在锁外执行）
        if (task != nullptr) {
            task();
        }
    }
}
```

**为什么在锁外执行任务？**
- 任务执行可能很耗时
- 持有锁会阻塞其他线程提交任务
- 减少锁的持有时间，提高并发性能

---

## 💡 实现提示

### 步骤 1：定义 ThreadPool 类

```cpp
// threadpool.h
#ifndef THREADPOOL_H
#define THREADPOOL_H

#include <vector>
#include <queue>
#include <memory>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <unordered_map>
#include "thread_wrapper.h"  // 使用 Task 1 的 Thread 类

class ThreadPool {
public:
    ThreadPool();
    ~ThreadPool();

    void start(int initThreadSize);
    void submitTask(std::function<void()> task);

    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

private:
    void threadFunc(int threadid);
    bool checkRunningState() const;

private:
    std::unordered_map<int, std::unique_ptr<Thread>> threads_;

    using Task = std::function<void()>;
    std::queue<Task> taskQue_;
    std::atomic_int taskSize_;

    std::mutex taskQueMtx_;
    std::condition_variable notEmpty_;
    std::condition_variable exitCond_;

    std::atomic_bool isPoolRunning_;
    int initThreadSize_;
};

#endif
```

### 步骤 2：实现构造函数

```cpp
ThreadPool::ThreadPool()
    : initThreadSize_(0)
    , taskSize_(0)
    , isPoolRunning_(false)
{
}
```

### 步骤 3：实现 start() 方法

**需要做什么：**
1. 设置运行状态
2. 记录初始线程数
3. 创建工作线程
4. 启动所有线程

```cpp
void ThreadPool::start(int initThreadSize) {
    // TODO: 设置 isPoolRunning_ = true
    // TODO: 保存 initThreadSize_

    // 创建线程
    for (int i = 0; i < initThreadSize; i++) {
        // TODO: 创建 Thread 对象，传入 threadFunc
        // 提示：使用 std::bind 绑定成员函数
        auto ptr = std::make_unique<Thread>(
            std::bind(&ThreadPool::threadFunc, this, std::placeholders::_1)
        );
        int threadId = ptr->getId();
        threads_.emplace(threadId, std::move(ptr));
    }

    // 启动所有线程
    for (int i = 0; i < initThreadSize; i++) {
        threads_[i]->start();
    }
}
```

### 步骤 4：实现 submitTask() 方法

**需要做什么：**
1. 获取锁
2. 将任务加入队列
3. 通知等待的线程

```cpp
void ThreadPool::submitTask(Task task) {
    // TODO: 获取锁 std::unique_lock<std::mutex> lock(taskQueMtx_);

    // TODO: 任务入队 taskQue_.push(task);
    // TODO: 增加任务计数 taskSize_++;

    // TODO: 通知等待的线程 notEmpty_.notify_all();
}
```

### 步骤 5：实现 threadFunc() 方法

这是最核心的部分！

```cpp
void ThreadPool::threadFunc(int threadid) {
    std::cout << "Thread " << threadid << " start!" << std::endl;

    for (;;) {
        Task task;
        {
            std::unique_lock<std::mutex> lock(taskQueMtx_);

            std::cout << "tid:" << threadid << " trying to get task..." << std::endl;

            // 等待任务队列非空
            while (taskQue_.empty()) {
                // 检查线程池是否关闭
                if (!isPoolRunning_) {
                    threads_.erase(threadid);
                    std::cout << "threadid:" << threadid << " exit!" << std::endl;
                    exitCond_.notify_all();
                    return;
                }

                // 等待任务
                notEmpty_.wait(lock);
            }

            std::cout << "tid:" << threadid << " get task success..." << std::endl;

            // 取出任务
            task = taskQue_.front();
            taskQue_.pop();
            taskSize_--;

            // 如果还有任务，通知其他线程
            if (taskQue_.size() > 0) {
                notEmpty_.notify_all();
            }
        }  // 释放锁

        // 执行任务
        if (task != nullptr) {
            task();
        }
    }
}
```

### 步骤 6：实现析构函数

**需要做什么：**
1. 设置关闭标志
2. 唤醒所有等待的线程
3. 等待所有线程退出

```cpp
ThreadPool::~ThreadPool() {
    isPoolRunning_ = false;

    // 唤醒所有等待的线程
    {
        std::unique_lock<std::mutex> lock(taskQueMtx_);
        notEmpty_.notify_all();
    }

    // 等待所有线程退出
    std::unique_lock<std::mutex> lock(taskQueMtx_);
    exitCond_.wait(lock, [&]() { return threads_.size() == 0; });
}
```

---

## ✅ 测试代码

```cpp
#include <iostream>
#include <chrono>
#include <thread>
#include "threadpool.h"

void test1_BasicExecution() {
    std::cout << "=== Test 1: Basic task execution ===" << std::endl;

    ThreadPool pool;
    pool.start(2);

    std::atomic<int> counter(0);

    for (int i = 0; i < 5; ++i) {
        pool.submitTask([&counter, i]() {
            std::cout << "Task " << i << " executing" << std::endl;
            counter++;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        });
    }

    std::this_thread::sleep_for(std::chrono::seconds(1));
    std::cout << "Counter: " << counter << " (expected: 5)" << std::endl;
}

void test2_ManyTasks() {
    std::cout << "\n=== Test 2: Many tasks ===" << std::endl;

    ThreadPool pool;
    pool.start(4);

    std::atomic<int> sum(0);

    for (int i = 0; i < 100; ++i) {
        pool.submitTask([&sum, i]() {
            sum += i;
        });
    }

    std::this_thread::sleep_for(std::chrono::seconds(1));
    int expected = 100 * 99 / 2;
    std::cout << "Sum: " << sum << " (expected: " << expected << ")" << std::endl;
}

void test3_Destruction() {
    std::cout << "\n=== Test 3: Graceful destruction ===" << std::endl;

    {
        ThreadPool pool;
        pool.start(2);

        for (int i = 0; i < 10; ++i) {
            pool.submitTask([i]() {
                std::cout << "Task " << i << " executing" << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
            });
        }

        std::cout << "Destroying pool..." << std::endl;
    }  // 析构函数应该等待所有任务完成

    std::cout << "Pool destroyed successfully" << std::endl;
}

int main() {
    test1_BasicExecution();
    test2_ManyTasks();
    test3_Destruction();

    std::cout << "\n✅ All tests completed!" << std::endl;
    return 0;
}
```

---

## 🤔 思考题

1. **为什么使用 while 而不是 if 检查队列？**
   ```cpp
   while (taskQue_.empty()) {  // 为什么不是 if？
       notEmpty_.wait(lock);
   }
   ```

2. **为什么任务执行要在锁外？**
   - 如果在锁内执行会怎样？
   - 对性能有什么影响？

3. **notify_one() vs notify_all()**
   - 什么时候用 `notify_one()`？
   - 什么时候用 `notify_all()`？
   - 本实现中为什么用 `notify_all()`？

4. **析构函数的设计**
   - 为什么要等待所有线程退出？
   - 如果不等待会有什么问题？
   - 如何测试析构函数是否正确？

5. **线程数的选择**
   - 应该创建多少个线程？
   - CPU 密集型 vs IO 密集型任务有什么不同？
   - `std::thread::hardware_concurrency()` 返回什么？

6. **死锁的可能性**
   - 当前实现会死锁吗？
   - 什么情况下可能死锁？
   - 如何检测死锁？

---

## 🐛 常见错误

### 错误 1：忘记使用 while 循环

```cpp
// ❌ 错误
if (taskQue_.empty()) {
    notEmpty_.wait(lock);
}
// 可能虚假唤醒，队列仍然为空！

// ✅ 正确
while (taskQue_.empty()) {
    notEmpty_.wait(lock);
}
```

### 错误 2：在持有锁时执行任务

```cpp
// ❌ 错误：在锁内执行
{
    std::unique_lock<std::mutex> lock(taskQueMtx_);
    task = taskQue_.front();
    taskQue_.pop();
    task();  // 其他线程无法提交任务！
}

// ✅ 正确：在锁外执行
{
    std::unique_lock<std::mutex> lock(taskQueMtx_);
    task = taskQue_.front();
    taskQue_.pop();
}
task();  // 锁已释放
```

### 错误 3：析构时不等待线程退出

```cpp
// ❌ 错误
~ThreadPool() {
    isPoolRunning_ = false;
    // 没有等待！线程可能还在访问成员变量
}

// ✅ 正确
~ThreadPool() {
    isPoolRunning_ = false;
    notEmpty_.notify_all();
    exitCond_.wait(lock, [&]() { return threads_.size() == 0; });
}
```

### 错误 4：忘记通知条件变量

```cpp
// ❌ 错误
void submitTask(Task task) {
    std::unique_lock<std::mutex> lock(taskQueMtx_);
    taskQue_.push(task);
    // 忘记 notify，线程可能永远等待！
}
```

---

## 🔍 调试技巧

### 1. 添加日志
```cpp
#define DEBUG_LOG
#ifdef DEBUG_LOG
    #define LOG(msg) std::cout << "[" << std::this_thread::get_id() << "] " << msg << std::endl
#else
    #define LOG(msg)
#endif
```

### 2. 使用 ThreadSanitizer
```bash
g++ -std=c++11 -pthread -fsanitize=thread -g test_task2.cpp -o test
./test
```

### 3. 使用 gdb 调试
```bash
gdb ./test
(gdb) break ThreadPool::threadFunc
(gdb) run
(gdb) info threads
```

---

## ✅ 检查清单

完成本任务前，请确认：

- [ ] 线程池能够创建并启动指定数量的线程
- [ ] 能够提交任务并正确执行
- [ ] 多个任务能够并发执行
- [ ] 析构时等待所有任务完成
- [ ] 析构时所有线程正确退出
- [ ] 没有死锁
- [ ] 没有数据竞争（ThreadSanitizer 检查）
- [ ] 没有内存泄漏（valgrind 检查）
- [ ] 理解生产者-消费者模式
- [ ] 理解条件变量的工作原理
- [ ] 回答所有思考题

---

## 📚 扩展阅读

- [C++ Concurrency in Action - Chapter 4: Synchronizing concurrent operations](https://www.manning.com/books/c-plus-plus-concurrency-in-action-second-edition)
- [Producer-Consumer Problem](https://en.wikipedia.org/wiki/Producer%E2%80%93consumer_problem)
- [Spurious Wakeup](https://en.wikipedia.org/wiki/Spurious_wakeup)

---

## 下一步

完成本任务后，继续 [Task 3: 任务返回值](task3_task_result.md)

在 Task 3 中，你将学习如何使用 `std::future` 获取任务的返回值！
