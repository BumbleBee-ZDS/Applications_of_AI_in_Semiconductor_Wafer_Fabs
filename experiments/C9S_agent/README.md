# WaferFab-Agent-K8s

> 基于 Kubernetes 控制论思想的半导体晶圆厂（FAB）生产调度模拟系统

## 🌟 技术亮点：过程控制论（源自 Kubernetes）

### 核心思想：声明式期望状态 + 调谐循环自动收敛

本项目将 Kubernetes 的控制论（Cybernetics）思想引入半导体制造调度领域，用"**观察-决策-执行**"的闭环控制取代传统的"命令式管道"模式。

```
┌─────────────────────────────────────────────────────────┐
│                    调谐循环 (Reconcile Loop)              │
│                                                          │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│   │  观察     │ ───▶ │  决策     │ ───▶ │  执行     │       │
│   │  Observe │      │  Decide  │      │  Act     │       │
│   └──────────┘      └──────────┘      └──────────┘       │
│        │                                            │     │
│        └────────────────────────────────────────────┘     │
│                     持续循环，永不停止                       │
└─────────────────────────────────────────────────────────┘
```

### K8s 控制论映射关系

| K8s 概念 | 本项目实现 | 说明 |
|---------|-----------|------|
| Pod | `WaferLot`（晶圆批次） | 核心调度单元，包含完整生命周期状态 |
| Container | `ProcessStep`（工艺步骤） | Pod 内的执行单元，对应晶圆加工的每一步 |
| Node | `ToolGroup`（设备组） | 提供计算/加工资源的物理实体 |
| etcd | `self.lots` 内存存储 | 集群状态的唯一真实来源 |
| Controller Manager | `FabController` | 运行调谐循环，驱动系统收敛 |
| Scheduler | `SchedulerAgent` | 将 Pod（批次）调度到 Node（设备）上 |
| Kubelet | Worker 逻辑 | 在 Node 上实际执行任务 |
| Declarative Spec | `steps` / `status: completed` | 声明期望状态，而非命令执行步骤 |
| Self-Healing | 自动重试机制（最多3次） | 失败后自动重试，而非直接终止 |
| Events | `add_log()` 日志系统 | 记录系统状态变化事件 |

### 为什么过程控制论更优？

| 维度 | 传统命令式管道 | K8s 声明式调谐循环 |
|-----|-------------|------------------|
| **控制模式** | 一次性、线性执行 | 持续闭环控制 |
| **失败处理** | 失败即终止，无重试 | 自动重试（自愈），最多3次 |
| **资源调度** | 不考虑资源限制，顺序排队 | 基于负载的动态调度，资源利用率更高 |
| **并发能力** | 串行执行，批次间相互等待 | 并行执行，充分利用设备资源 |
| **状态管理** | 无状态，失败后无法恢复 | 有状态，可从任意失败点继续 |
| **系统韧性** | 单点故障导致整体失败 | 故障隔离，单个批次失败不影响全局 |

---

## 📋 项目概述

WaferFab-Agent-K8s 是一个模拟半导体晶圆厂生产调度的 Web 应用，演示了如何将 Kubernetes 的控制论思想应用于复杂制造系统。

系统包含 5 个示例晶圆批次，经过光刻（Photolithography）、刻蚀（Etch）、沉积（Deposition）、清洗（Cleaning）等工艺步骤，通过调谐循环自动调度到对应设备组上执行。

---

## 🏗️ 系统架构

### 多智能体协作

```
                    ┌───────────────────┐
                    │  Supervisor Agent │
                    │  (Controller Mgr) │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌─────▼────────┐ ┌───▼───────────┐
     │ Scheduler     │ │  Worker      │ │  Monitor      │
     │ Agent         │ │  Agent       │ │  Agent        │
     │ (K8s Scheduler)│ │ (Kubelet)   │ │ (Observability)│
     └────────┬──────┘ └─────┬────────┘ └───────────────┘
              │              │
     ┌────────▼──────────────▼────────┐
     │      ToolGroups (设备组)        │
     │  Photolithography / Etch / ... │
     └────────────────────────────────┘
```

### 核心组件

- **Supervisor Agent**：全局控制器，运行调谐循环，监控系统状态
- **Scheduler Agent**：调度器，基于最少负载策略将批次分配到设备
- **Worker Agent**：执行者，管理单个批次的步骤执行和状态转换
- **Monitor Agent**：监控者，记录日志、收集指标、生成事件

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Flask 2.x

### 安装依赖

```bash
cd waferfab-agent
pip install -r requirements.txt
```

### 启动服务

```bash
python app.py
```

服务启动后访问：
- 仪表盘：http://localhost:5000
- 架构对比：http://localhost:5000/compare

---

## 📁 项目结构

```
waferfab-agent/
├── app.py              # Flask 应用主入口，路由定义
├── controller.py       # 核心控制器（调谐循环 + Kubelet 逻辑）
├── scheduler.py        # 调度器 Agent（K8s Scheduler）
├── models.py           # 数据模型（WaferLot / ProcessStep / ToolGroup）
├── traditional.py      # 传统命令式管道实现（对比用）
├── requirements.txt    # Python 依赖
├── static/
│   └── style.css       # 前端样式
└── templates/
    ├── dashboard.html  # 实时仪表盘
    └── compare.html    # 架构对比页面
```

---

## 🔧 核心 API

| 方法 | 端点 | 说明 |
|-----|------|------|
| GET | `/api/lots` | 获取所有批次状态 |
| POST | `/api/lots` | 创建新批次 |
| GET | `/api/lots/<id>` | 获取单个批次详情 |
| DELETE | `/api/lots/<id>` | 删除批次 |
| GET | `/api/tools` | 获取设备组利用率 |
| GET | `/api/logs` | 获取调谐循环日志 |
| GET | `/api/metrics` | 获取系统指标 |
| POST | `/api/compare` | 运行架构对比测试 |

---

## 🎯 调谐循环详解

调谐循环（Reconcile Loop）是 K8s 控制论的核心，本项目每 2 秒执行一次：

```python
def reconcile(self):
    # 1. 观察：扫描所有活跃批次
    active_lots = [lot for lot in self.lots.values() 
                   if lot.status not in ["completed", "failed"]]
    
    # 2. 决策：对每个批次判断应执行的操作
    for lot in active_lots:
        if lot.status == "pending":
            # 需要调度分配设备
            self._handle_pending(lot)
        elif lot.status == "running":
            # 检查步骤是否完成
            self._handle_running(lot)
    
    # 3. 执行：触发状态转换
    # ...（在 handle 函数中执行）
```

### 批次状态机

```
     pending
        │
        ▼  调度分配设备
     running
     │     │
     │     └─── 步骤失败（<3次）───► running（重试）
     │
     ▼  步骤完成 ──► 还有步骤？──┐
     │                          │是
     │否                        │
     ▼                          │
  completed ◄───────────────────┘

  running
     │
     └─── 失败次数 ≥ 3 ───► failed
```

---

## 📊 仪表盘功能

- **批次状态表格**：实时显示所有批次的当前步骤、状态、进度、耗时
- **设备利用率图表**：使用 Chart.js 展示各设备组的繁忙/空闲比例
- **调谐循环日志**：实时输出系统事件日志，包括调度、执行、失败、重试等
- **系统指标**：总批次数、完成数、进行中、失败率、平均耗时

---

## 💡 设计要点

1. **声明式 API**：用户只需声明"我要完成这些步骤"，系统自动找方法达成
2. **最终一致性**：系统不断调谐，最终所有批次都会收敛到 completed 或 failed 状态
3. **容错设计**：随机模拟设备故障，验证自愈能力（自动重试）
4. **资源约束**：设备数量有限，调度器需要优化分配策略
5. **并发安全**：使用 RLock 保护共享状态，支持多线程安全访问

---

## 📚 延伸阅读

- [Kubernetes 控制器模式](https://kubernetes.io/zh-cn/docs/concepts/architecture/controller/)
- [Kubernetes 调度器](https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/kube-scheduler/)
- [控制论与分布式系统](https://en.wikipedia.org/wiki/Cybernetics)
