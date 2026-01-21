# Task 1: 线程包装类

**预计时间：** 1-2 小时
**难度：** ⭐⭐ 简单

---

## 📖 学习目标

完成本任务后，你将：
- ✅ 理解为什么要封装 `std::thread`
- ✅ 掌握 `std::function` 的使用
- ✅ 理解静态成员变量的用法
- ✅ 实现简单的 RAII 风格类
- ✅ 理解线程 ID 管理机制

---

## 🎯 任务目标

实现一个 `Thread` 类，封装 `std::thread`，提供以下功能：

1. 接受一个函数对象（接受 int 参数的函数）
2. 为每个线程分配唯一的 ID
3. 提供 `start()` 方法启动线程
4. 提供 `getId()` 获取线程 ID

**接口定义：**

```cpp
class Thread {
public:
    using ThreadFunc = std::function<void(int)>;

    Thread(ThreadFunc func);
    ~Thread() = default;

    void start();
    int getId() const;

private:
    ThreadFunc func_;
    static int generateId_;
    int threadId_;
};
```

---

## 📖 背景知识

### 1. 为什么要封装 std::thread？

虽然 `std::thread` 已经很好用，但在线程池场景中：

**原始方式的问题：**
```cpp
std::thread t([]() { /* do work */ });
// 问题1：如何管理多个线程？
// 问题2：如何给线程分配ID？
// 问题3：如何统一启动方式（join/detach）？
```

**封装的好处：**
- ✅ 统一的线程创建接口
- ✅ 自动分配唯一 ID
- ✅ 灵活控制线程的启动方式
- ✅ 方便扩展（如线程名称、优先级等）

### 2. std::function 详解

`std::function` 是一个通用的函数包装器：

```cpp
#include <functional>

// 可以包装普通函数
int add(int a, int b) { return a + b; }
std::function<int(int, int)> f1 = add;

// 可以包装 lambda
std::function<int(int, int)> f2 = [](int a, int b) { return a + b; };

// 可以包装成员函数
class Calculator {
public:
    int multiply(int a, int b) { return a * b; }
};
Calculator calc;
std::function<int(int, int)> f3 = std::bind(&Calculator::multiply, &calc,
                                             std::placeholders::_1,
                                             std::placeholders::_2);
```

**本任务中的使用：**
```cpp
using ThreadFunc = std::function<void(int)>;
// 接受一个 int 参数（线程ID），无返回值的函数
```

### 3. 静态成员变量

静态成员变量属于类，而非某个对象：

```cpp
class Thread {
private:
    static int generateId_;  // 声明
    int threadId_;
};

// 类外定义并初始化
int Thread::generateId_ = 0;
```

**特点：**
- 所有对象共享同一个静态变量
- 可以用作计数器、ID 生成器等

**线程安全问题：**
```cpp
// ⚠️ 不是线程安全的
threadId_ = generateId_++;

// 如果多线程同时创建 Thread 对象，可能分配相同的 ID
// 但在我们的场景中，Thread 对象在单线程中创建，所以没问题
```

### 4. detach 的使用场景

在线程池中，我们使用 `detach()`：

```cpp
void Thread::start() {
    std::thread t(func_, threadId_);
    t.detach();  // 让线程在后台运行
}
```

**为什么使用 detach？**
- 线程池中的工作线程是长期运行的
- 不需要主线程等待它们完成
- 线程的生命周期由线程池管理

**注意事项：**
- 必须确保线程访问的资源（如 `func_`）在线程运行期间有效
- 这就是为什么使用 `std::function` —— 它会复制或移动捕获的数据

---

## 💡 实现提示

### 步骤 1：定义 Thread 类

```cpp
// thread_wrapper.h
#ifndef THREAD_WRAPPER_H
#define THREAD_WRAPPER_H

#include <functional>
#include <thread>

class Thread {
public:
    using ThreadFunc = std::function<void(int)>;

    // TODO: 实现构造函数
    Thread(ThreadFunc func);

    ~Thread() = default;

    // TODO: 实现 start 方法
    void start();

    // TODO: 实现 getId 方法
    int getId() const;

private:
    ThreadFunc func_;
    static int generateId_;
    int threadId_;
};

#endif
```

### 步骤 2：实现构造函数

**需要做什么：**
1. 保存传入的函数对象
2. 生成唯一的线程 ID

**提示：**
```cpp
Thread::Thread(ThreadFunc func)
    : func_(/* TODO */)
    , threadId_(/* TODO: 使用 generateId_ 生成唯一 ID */)
{
}
```

### 步骤 3：实现 start 方法

**需要做什么：**
1. 创建 `std::thread` 对象
2. 传递函数和线程 ID
3. detach 线程

**提示：**
```cpp
void Thread::start() {
    std::thread t(/* TODO: 调用 func_，传入 threadId_ */);
    /* TODO: detach 线程 */
}
```

### 步骤 4：实现 getId 方法

这个很简单，返回 `threadId_` 即可。

### 步骤 5：定义静态成员变量

在 `.cpp` 文件或头文件中定义：

```cpp
int Thread::generateId_ = 0;
```

---

## ✅ 测试代码

创建 `test_task1.cpp`：

```cpp
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include "thread_wrapper.h"

void testBasic() {
    std::cout << "Test 1: Basic thread creation and execution" << std::endl;

    bool executed = false;
    Thread t([&executed](int id) {
        std::cout << "Thread " << id << " is running" << std::endl;
        executed = true;
    });

    std::cout << "Thread ID: " << t.getId() << std::endl;
    t.start();

    // 等待线程执行
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    if (executed) {
        std::cout << "✅ Test 1 passed" << std::endl;
    } else {
        std::cout << "❌ Test 1 failed" << std::endl;
    }
}

void testMultipleThreads() {
    std::cout << "\nTest 2: Multiple threads with unique IDs" << std::endl;

    std::vector<Thread*> threads;
    for (int i = 0; i < 5; ++i) {
        threads.push_back(new Thread([](int id) {
            std::cout << "Thread " << id << " is running" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }));
    }

    // 检查 ID 唯一性
    std::set<int> ids;
    for (auto* t : threads) {
        ids.insert(t->getId());
        std::cout << "Thread ID: " << t->getId() << std::endl;
    }

    if (ids.size() == threads.size()) {
        std::cout << "✅ All thread IDs are unique" << std::endl;
    } else {
        std::cout << "❌ Duplicate thread IDs found" << std::endl;
    }

    // 启动所有线程
    for (auto* t : threads) {
        t->start();
    }

    // 等待所有线程完成
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // 清理
    for (auto* t : threads) {
        delete t;
    }

    std::cout << "✅ Test 2 passed" << std::endl;
}

void testFunctionTypes() {
    std::cout << "\nTest 3: Different function types" << std::endl;

    // Lambda
    Thread t1([](int id) {
        std::cout << "Lambda thread " << id << std::endl;
    });

    // 函数对象
    struct Functor {
        void operator()(int id) {
            std::cout << "Functor thread " << id << std::endl;
        }
    };
    Thread t2(Functor());

    t1.start();
    t2.start();

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    std::cout << "✅ Test 3 passed" << std::endl;
}

int main() {
    testBasic();
    testMultipleThreads();
    testFunctionTypes();

    std::cout << "\n✅ All tests passed!" << std::endl;
    return 0;
}
```

---

## 🤔 思考题

1. **为什么使用 `std::function` 而不是函数指针？**
   - `std::function` 的优势是什么？
   - 性能上有什么代价？

2. **静态变量的线程安全**
   - `generateId_++` 是线程安全的吗？
   - 如果多个线程同时创建 `Thread` 对象会怎样？
   - 如何修复？（提示：`std::atomic<int>`）

3. **detach vs join 的选择**
   - 为什么线程池使用 detach？
   - 使用 detach 有什么风险？
   - 如何确保 `func_` 在线程运行期间有效？

4. **RAII 原则**
   - 当前的 `Thread` 类符合 RAII 吗？
   - 如果在析构函数中添加 `join()`，会有什么问题？

5. **扩展思考**
   - 如何给线程添加名称？
   - 如何获取线程的运行状态？
   - 如何实现线程的暂停和恢复？

---

## 🐛 常见错误

### 错误 1：忘记定义静态成员变量

```cpp
// ❌ 只声明，未定义
class Thread {
    static int generateId_;
};

// 链接错误：undefined reference to `Thread::generateId_'
```

**修复：**
```cpp
// ✅ 在类外定义
int Thread::generateId_ = 0;
```

### 错误 2：线程对象立即析构

```cpp
// ❌
void bug() {
    Thread t([](int id) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    });
    t.start();
}  // t 被销毁，但线程还在运行！
```

虽然使用了 detach，但 `func_` 可能引用了局部变量，导致未定义行为。

### 错误 3：编译时缺少 -pthread

```bash
# ❌
g++ -std=c++11 test_task1.cpp -o test

# ✅
g++ -std=c++11 -pthread test_task1.cpp -o test
```


---

## ✅ 检查清单

完成本任务前，请确认：

- [ ] `Thread` 类能够成功编译
- [ ] 能够创建和启动线程
- [ ] 每个线程都有唯一的 ID
- [ ] 支持不同类型的函数对象（lambda、函数、仿函数）
- [ ] 所有测试通过
- [ ] 理解 `std::function` 的作用
- [ ] 理解静态成员变量的用法
- [ ] 思考并回答思考题

---

## 📚 参考代码结构

```
starter/task1/
├── thread_wrapper.h      # 你的实现
├── test_task1.cpp        # 测试代码
└── CMakeLists.txt        # 构建配置
```

**编译运行：**
```bash
cd starter/task1
mkdir build && cd build
cmake ..
make
./test_task1
```

---

## 下一步

完成本任务后，继续 [Task 2: 固定大小线程池](task2_fixed_pool.md)

在 Task 2 中，你将学习生产者-消费者模式，实现真正的线程池！
