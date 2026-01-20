# C++ 线程池学习文档

## 目录
1. [项目概述](#项目概述)
2. [核心类设计](#核心类设计)
3. [工作模式](#工作模式)
4. [关键特性](#关键特性)
5. [使用示例](#使用示例)
6. [核心机制详解](#核心机制详解)
7. [线程安全机制](#线程安全机制)
8. [代码流程图](#代码流程图)

---

## 项目概述

这是一个基于 **C++11** 标准实现的高性能线程池，支持两种工作模式，并使用现代 C++ 特性（如 `std::future`、可变参数模板、智能指针等）实现任务的异步执行。

### 核心文件
- `threadpool.h` - 线程池核心实现
- `threadpool.cpp` - 测试示例代码

### 技术栈
- C++11/14 标准库
- `std::thread` - 线程管理
- `std::future` / `std::packaged_task` - 异步任务与结果获取
- `std::mutex` / `std::condition_variable` - 线程同步
- 可变参数模板 - 灵活的任务提交接口

---

## 核心类设计

### 1. Thread 类
封装线程对象，负责线程的创建和管理。

```cpp
class Thread {
public:
    using ThreadFunc = std::function<void(int)>;

    Thread(ThreadFunc func);  // 构造函数，接收线程执行函数
    void start();              // 启动线程
    int getId() const;         // 获取线程ID

private:
    ThreadFunc func_;          // 线程执行的函数
    static int generateId_;    // 静态ID生成器
    int threadId_;             // 线程唯一标识
};
```

**关键点：**
- 使用 `std::function` 作为线程函数类型，支持任意可调用对象
- 使用 `detach()` 分离线程，让线程在后台运行
- 静态成员 `generateId_` 确保每个线程有唯一ID

---

### 2. ThreadPool 类
线程池核心类，负责任务调度和线程管理。

#### 主要成员变量

```cpp
// 线程管理
std::unordered_map<int, std::unique_ptr<Thread>> threads_;  // 线程容器
int initThreadSize_;            // 初始线程数量
int threadSizeThreshHold_;      // 线程数量上限（cached模式）
std::atomic_int curThreadSize_; // 当前线程总数
std::atomic_int idleThreadSize_;// 空闲线程数

// 任务队列
std::queue<Task> taskQue_;      // 任务队列
std::atomic_int taskSize_;      // 任务数量
int taskQueMaxThreshHold_;      // 任务队列容量上限

// 同步机制
std::mutex taskQueMtx_;                  // 任务队列互斥锁
std::condition_variable notFull_;        // 队列未满条件变量
std::condition_variable notEmpty_;       // 队列非空条件变量
std::condition_variable exitCond_;       // 线程退出条件变量

// 状态标识
PoolMode poolMode_;              // 工作模式
std::atomic_bool isPoolRunning_; // 运行状态
```

#### 核心方法

| 方法 | 功能说明 |
|------|---------|
| `start(int size)` | 启动线程池，创建指定数量的工作线程 |
| `submitTask(Func&&, Args&&...)` | 提交任务到线程池（使用可变参数模板） |
| `setMode(PoolMode)` | 设置工作模式（FIXED/CACHED） |
| `setTaskQueMaxThreshHold(int)` | 设置任务队列容量上限 |
| `setThreadSizeThreshHold(int)` | 设置线程数量上限（仅cached模式） |
| `threadFunc(int)` | 工作线程执行函数（私有方法） |

---

## 工作模式

### MODE_FIXED (固定模式)
- 线程数量在启动时确定，运行期间保持不变
- 适用于任务负载稳定的场景
- 优点：资源消耗可控，性能稳定
- 缺点：无法应对突发高负载

### MODE_CACHED (缓存模式)
- 线程数量动态调整，根据任务负载自动扩缩容
- 核心机制：
  - **自动扩容**：当 `任务数 > 空闲线程数` 且未达上限时，创建新线程
  - **自动回收**：线程空闲超过 60 秒后自动销毁（保留初始线程）
- 适用于任务负载波动较大的场景
- 优点：灵活应对负载变化
- 缺点：线程创建/销毁有一定开销

---

## 关键特性

### 1. 可变参数模板实现灵活任务提交

使用 C++11 的可变参数模板和完美转发，支持任意函数签名的任务：

```cpp
template<typename Func, typename... Args>
auto submitTask(Func&& func, Args&&... args)
    -> std::future<decltype(func(args...))>
{
    // 推导返回类型
    using RType = decltype(func(args...));

    // 使用 packaged_task 包装任务
    auto task = std::make_shared<std::packaged_task<RType()>>(
        std::bind(std::forward<Func>(func), std::forward<Args>(args)...)
    );

    // 获取 future 对象以获取结果
    std::future<RType> result = task->get_future();

    // ... 任务入队逻辑 ...

    return result;
}
```

**优势：**
- 支持任意返回类型
- 支持任意数量和类型的参数
- 编译期类型安全
- 自动推导返回类型

---

### 2. 基于 future 的结果获取

摒弃自定义 `Result` 类，直接使用 C++11 标准库的 `std::future`：

```cpp
// 提交任务
future<int> result = pool.submitTask(sum, 10, 20);

// 阻塞等待并获取结果
int value = result.get();
```

---

### 3. 任务队列容量控制

提交任务时会检查队列是否已满：

```cpp
// 等待最多 1 秒，如果队列仍然满则提交失败
if (!notFull_.wait_for(lock, std::chrono::seconds(1),
    [&]()->bool { return taskQue_.size() < taskQueMaxThreshHold_; }))
{
    std::cerr << "task queue is full, submit task fail." << std::endl;
    // 返回默认值的 future
    auto task = std::make_shared<std::packaged_task<RType()>>(
        []()->RType { return RType(); }
    );
    (*task)();
    return task->get_future();
}
```

---

## 使用示例

### 基本用法

```cpp
#include "threadpool.h"

// 定义任务函数
int sum(int a, int b) {
    return a + b;
}

int main() {
    // 1. 创建线程池
    ThreadPool pool;

    // 2. 启动线程池（2个工作线程）
    pool.start(2);

    // 3. 提交普通函数任务
    future<int> r1 = pool.submitTask(sum, 10, 20);

    // 4. 提交 Lambda 表达式任务
    future<int> r2 = pool.submitTask([](int a, int b) {
        return a * b;
    }, 5, 6);

    // 5. 获取结果
    cout << "10 + 20 = " << r1.get() << endl;  // 输出: 30
    cout << "5 * 6 = " << r2.get() << endl;    // 输出: 30

    return 0;
}
```

### 设置 CACHED 模式

```cpp
ThreadPool pool;
pool.setMode(PoolMode::MODE_CACHED);  // 设置为动态模式
pool.setThreadSizeThreshHold(10);     // 最多创建10个线程
pool.start(2);                         // 初始2个线程
```

### 批量提交任务

```cpp
ThreadPool pool;
pool.start(4);

vector<future<int>> results;

// 提交100个任务
for (int i = 0; i < 100; i++) {
    results.push_back(pool.submitTask([](int n) {
        return n * n;
    }, i));
}

// 获取所有结果
for (auto& f : results) {
    cout << f.get() << " ";
}
```

---

## 核心机制详解

### 1. 线程池启动流程

```cpp
void start(int initThreadSize) {
    // 1. 设置运行状态
    isPoolRunning_ = true;

    // 2. 记录初始线程数
    initThreadSize_ = initThreadSize;
    curThreadSize_ = initThreadSize;

    // 3. 创建线程对象
    for (int i = 0; i < initThreadSize_; i++) {
        auto ptr = std::make_unique<Thread>(
            std::bind(&ThreadPool::threadFunc, this, std::placeholders::_1)
        );
        int threadId = ptr->getId();
        threads_.emplace(threadId, std::move(ptr));
    }

    // 4. 启动所有线程
    for (int i = 0; i < initThreadSize_; i++) {
        threads_[i]->start();
        idleThreadSize_++;
    }
}
```

**关键点：**
- 使用 `std::unique_ptr` 管理线程对象，自动释放资源
- 使用 `std::bind` 将成员函数绑定为线程执行函数
- `unordered_map` 以线程ID为键，方便后续查找和删除

---

### 2. 工作线程执行逻辑

```cpp
void threadFunc(int threadid) {
    auto lastTime = std::chrono::high_resolution_clock().now();

    for (;;) {  // 无限循环
        Task task;
        {
            std::unique_lock<std::mutex> lock(taskQueMtx_);

            // 等待任务（带超时检测）
            while (taskQue_.size() == 0) {
                // 检查线程池是否结束
                if (!isPoolRunning_) {
                    threads_.erase(threadid);
                    exitCond_.notify_all();
                    return;
                }

                // CACHED 模式：检查空闲超时
                if (poolMode_ == PoolMode::MODE_CACHED) {
                    if (notEmpty_.wait_for(lock, std::chrono::seconds(1))
                        == std::cv_status::timeout) {
                        auto now = std::chrono::high_resolution_clock().now();
                        auto dur = std::chrono::duration_cast<std::chrono::seconds>(now - lastTime);

                        // 空闲超过60秒且线程数大于初始值，回收线程
                        if (dur.count() >= THREAD_MAX_IDLE_TIME
                            && curThreadSize_ > initThreadSize_) {
                            threads_.erase(threadid);
                            curThreadSize_--;
                            idleThreadSize_--;
                            return;
                        }
                    }
                } else {
                    // FIXED 模式：无限等待
                    notEmpty_.wait(lock);
                }
            }

            idleThreadSize_--;

            // 从队列取出任务
            task = taskQue_.front();
            taskQue_.pop();
            taskSize_--;

            // 通知其他线程和生产者
            if (taskQue_.size() > 0) {
                notEmpty_.notify_all();
            }
            notFull_.notify_all();
        }

        // 执行任务（锁外执行，避免阻塞其他线程）
        if (task != nullptr) {
            task();
        }

        idleThreadSize_++;
        lastTime = std::chrono::high_resolution_clock().now();
    }
}
```

**核心逻辑：**
1. **等待任务**：通过条件变量 `notEmpty_` 等待任务到来
2. **超时机制**：CACHED 模式下，等待超时后检查是否需要回收线程
3. **取出任务**：从队列头部取出任务（FIFO）
4. **执行任务**：在锁外执行，避免阻塞其他线程
5. **更新状态**：更新空闲线程计数和时间戳

---

### 3. 任务提交流程

```cpp
template<typename Func, typename... Args>
auto submitTask(Func&& func, Args&&... args)
    -> std::future<decltype(func(args...))>
{
    using RType = decltype(func(args...));

    // 1. 包装任务
    auto task = std::make_shared<std::packaged_task<RType()>>(
        std::bind(std::forward<Func>(func), std::forward<Args>(args)...)
    );
    std::future<RType> result = task->get_future();

    // 2. 等待队列有空位
    std::unique_lock<std::mutex> lock(taskQueMtx_);
    if (!notFull_.wait_for(lock, std::chrono::seconds(1),
        [&]()->bool { return taskQue_.size() < taskQueMaxThreshHold_; }))
    {
        // 队列满，返回默认值
        // ...
    }

    // 3. 任务入队
    taskQue_.emplace([task]() { (*task)(); });
    taskSize_++;

    // 4. 通知工作线程
    notEmpty_.notify_all();

    // 5. CACHED 模式：动态创建线程
    if (poolMode_ == PoolMode::MODE_CACHED
        && taskSize_ > idleThreadSize_
        && curThreadSize_ < threadSizeThreshHold_)
    {
        auto ptr = std::make_unique<Thread>(
            std::bind(&ThreadPool::threadFunc, this, std::placeholders::_1)
        );
        int threadId = ptr->getId();
        threads_.emplace(threadId, std::move(ptr));
        threads_[threadId]->start();
        curThreadSize_++;
        idleThreadSize_++;
    }

    return result;
}
```

**关键设计：**
- 使用 `packaged_task` 包装任务，自动处理返回值
- 使用 Lambda 捕获 `shared_ptr<packaged_task>`，延长生命周期
- 条件变量 `notFull_` 实现生产者阻塞
- 动态扩容判断：`任务数 > 空闲线程数`

---

## 线程安全机制

### 1. 互斥锁保护共享资源

```cpp
std::mutex taskQueMtx_;  // 保护任务队列和计数器
```

**受保护的资源：**
- `taskQue_` - 任务队列
- `taskSize_` - 任务计数
- `threads_` - 线程容器
- `idleThreadSize_` / `curThreadSize_` - 线程计数

---

### 2. 条件变量实现等待/通知

| 条件变量 | 作用 | 等待条件 | 唤醒时机 |
|---------|------|---------|---------|
| `notEmpty_` | 任务队列非空 | 队列为空时工作线程等待 | 任务入队后唤醒 |
| `notFull_` | 任务队列未满 | 队列满时生产者等待 | 任务出队后唤醒 |
| `exitCond_` | 线程退出 | 析构函数等待所有线程退出 | 线程退出时唤醒 |

---

### 3. 原子变量避免锁竞争

```cpp
std::atomic_int taskSize_;       // 任务数量
std::atomic_int curThreadSize_;  // 当前线程数
std::atomic_int idleThreadSize_; // 空闲线程数
std::atomic_bool isPoolRunning_; // 运行状态
```

**优势：**
- 无锁读取，减少性能开销
- 保证多线程环境下的可见性和原子性

---

## 代码流程图

### 任务提交流程

```
用户提交任务
    ↓
获取互斥锁
    ↓
等待队列有空位（最多1秒）
    ↓
    ├── 超时 → 返回默认值 future
    │
    └── 成功 → 任务入队
                ↓
            唤醒工作线程（notEmpty_）
                ↓
            检查是否需要创建新线程（CACHED模式）
                ↓
            返回 future 对象
```

### 工作线程执行流程

```
线程启动
    ↓
进入无限循环
    ↓
获取互斥锁
    ↓
等待任务到来（notEmpty_）
    ↓
    ├── 线程池结束 → 清理并退出
    │
    ├── 超时（CACHED模式）→ 检查是否回收
    │
    └── 任务到来 → 取出任务
                     ↓
                释放互斥锁
                     ↓
                执行任务
                     ↓
                更新空闲线程计数
                     ↓
                回到循环开始
```

---

## 设计亮点

### 1. 使用智能指针管理资源
- `std::unique_ptr<Thread>` - 自动管理线程对象生命周期
- `std::shared_ptr<packaged_task>` - 延长任务对象生命周期至执行完成

### 2. 类型推导与完美转发
```cpp
template<typename Func, typename... Args>
auto submitTask(Func&& func, Args&&... args)
    -> std::future<decltype(func(args...))>
```
- 尾置返回类型 + `decltype` 实现自动类型推导
- 完美转发保留参数的值类别（左值/右值）

### 3. RAII 原则
- 析构函数自动清理资源
- 使用 `std::unique_lock` 自动管理锁

### 4. 双重检查优化
```cpp
while (taskQue_.size() == 0) {
    if (!isPoolRunning_) return;  // 先检查状态
    // 再进入等待
}
```

---

## 性能优化建议

### 1. 减少锁粒度
当前实现在任务执行时已释放锁，这是正确的做法。继续保持"锁外执行任务"的原则。

### 2. 任务窃取（Work Stealing）
可以为每个线程维护独立的任务队列，空闲线程从其他线程"窃取"任务，减少锁竞争。

### 3. 批量通知优化
```cpp
// 当前实现
notEmpty_.notify_all();

// 优化建议：精确唤醒一个线程
notEmpty_.notify_one();
```

### 4. 内存池优化
对于高频创建/销毁的任务对象，可以使用内存池减少分配开销。

---

## 常见问题

### Q1: 为什么使用 `detach()` 而不是 `join()`?
**A:** 使用 `detach()` 让线程在后台独立运行，不阻塞主线程。线程池析构时通过条件变量 `exitCond_` 确保所有线程退出。

### Q2: 任务队列满时如何处理?
**A:** 当前实现会等待最多 1 秒，超时后返回一个包含默认值的 `future` 对象，并输出错误信息。

### Q3: CACHED 模式的线程回收机制是什么?
**A:** 线程空闲超过 60 秒（`THREAD_MAX_IDLE_TIME`）且线程总数大于初始值时，线程会自动退出。

### Q4: 如何处理任务执行异常?
**A:** `packaged_task` 会自动捕获异常并存储在 `future` 对象中，调用 `future.get()` 时会重新抛出异常。

---

## 学习路径建议

1. **基础阶段**
   - 理解线程同步原语（mutex、condition_variable）
   - 掌握 C++11 多线程基础（thread、future）

2. **进阶阶段**
   - 研究生产者-消费者模式
   - 理解 RAII 和智能指针

3. **高级阶段**
   - 分析性能瓶颈（使用性能分析工具）
   - 尝试改进（任务窃取、无锁队列等）

4. **实践项目**
   - 将线程池应用于实际项目（Web 服务器、图像处理等）
   - 对比不同场景下的性能表现

---

## 参考资料

- [C++ Concurrency in Action](https://www.manning.com/books/c-plus-plus-concurrency-in-action-second-edition)
- [Effective Modern C++](https://www.oreilly.com/library/view/effective-modern-c/9781491908419/)
- [cppreference - thread support library](https://en.cppreference.com/w/cpp/thread)

---

## 总结

这个线程池实现展示了现代 C++ 的优秀实践：
- ✅ 使用标准库而非手动管理（future vs 自定义Result）
- ✅ 智能指针管理资源，避免内存泄漏
- ✅ 模板编程提供灵活接口
- ✅ 原子变量减少锁开销
- ✅ RAII 原则确保资源正确释放

通过学习这个项目，你可以掌握 C++ 并发编程的核心概念和最佳实践！
