# WaferFab-Agent-K8s

> A semiconductor fab (FAB) production scheduling simulation system based on Kubernetes cybernetics

## 🌟 Technical Highlight: Process Cybernetics (from Kubernetes)

### Core Idea: Declarative Desired State + Reconcile Loop that Converges Automatically

This project brings Kubernetes' cybernetics ideas into semiconductor manufacturing scheduling, replacing the traditional "imperative pipeline" mode with an "**Observe-Decide-Act**" closed-loop control.

```
┌─────────────────────────────────────────────────────────┐
│                     Reconcile Loop                       │
│                                                          │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│   │  Observe │ ───▶ │  Decide  │ ───▶ │   Act    │       │
│   └──────────┘      └──────────┘      └──────────┘       │
│        │                                            │     │
│        └────────────────────────────────────────────┘     │
│                continuous loop, never stops               │
└─────────────────────────────────────────────────────────┘
```

### K8s Cybernetics Mapping

| K8s concept | This project's implementation | Description |
|---------|-----------|------|
| Pod | `WaferLot` (wafer lot) | Core scheduling unit with the full lifecycle state |
| Container | `ProcessStep` (process step) | Execution unit inside a Pod, corresponds to each wafer-processing step |
| Node | `ToolGroup` (tool group) | Physical entity providing compute/processing resources |
| etcd | `self.lots` in-memory store | Single source of truth for cluster state |
| Controller Manager | `FabController` | Runs the reconcile loop, drives the system to convergence |
| Scheduler | `SchedulerAgent` | Schedules Pods (lots) onto Nodes (tools) |
| Kubelet | Worker logic | Actually executes tasks on Nodes |
| Declarative Spec | `steps` / `status: completed` | Declares the desired state, not imperative execution steps |
| Self-Healing | Auto-retry mechanism (up to 3 times) | Automatically retries after failure instead of terminating |
| Events | `add_log()` logging system | Records system state-change events |

### Why is Process Cybernetics Better?

| Dimension | Traditional imperative pipeline | K8s declarative reconcile loop |
|-----|-------------|------------------|
| **Control mode** | One-shot, linear execution | Continuous closed-loop control |
| **Failure handling** | Terminates on failure, no retry | Auto-retry (self-healing), up to 3 times |
| **Resource scheduling** | Ignores resource limits, sequential queueing | Dynamic load-based scheduling, higher utilization |
| **Concurrency** | Serial execution, lots wait for each other | Parallel execution, full use of tool resources |
| **State management** | Stateless, cannot recover after failure | Stateful, can resume from any failure point |
| **System resilience** | Single point of failure brings everything down | Failure isolation, one lot's failure doesn't affect the whole |

---

## 📋 Project Overview

WaferFab-Agent-K8s is a web application that simulates semiconductor fab production scheduling, demonstrating how Kubernetes cybernetics can be applied to complex manufacturing systems.

The system contains 5 sample wafer lots that pass through process steps including Photolithography, Etch, Deposition, and Cleaning, automatically scheduled onto the corresponding tool groups by the reconcile loop.

---

## 🏗️ System Architecture

### Multi-Agent Collaboration

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
     │      ToolGroups                │
     │  Photolithography / Etch / ... │
     └────────────────────────────────┘
```

### Core Components

- **Supervisor Agent**: the global controller that runs the reconcile loop and monitors system state
- **Scheduler Agent**: the scheduler that assigns lots to tools using the least-load policy
- **Worker Agent**: the executor that manages step execution and state transitions for a single lot
- **Monitor Agent**: the monitor that records logs, collects metrics, and generates events

---

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Flask 2.x

### Install Dependencies

```bash
cd waferfab-agent
pip install -r requirements.txt
```

### Launch the Service

```bash
python app.py
```

After startup, visit:
- Dashboard: http://localhost:5000
- Architecture comparison: http://localhost:5000/compare

---

## 📁 Project Structure

```
waferfab-agent/
├── app.py              # Flask application entry, route definitions
├── controller.py       # Core controller (reconcile loop + Kubelet logic)
├── scheduler.py        # Scheduler Agent (K8s Scheduler)
├── models.py           # Data models (WaferLot / ProcessStep / ToolGroup)
├── traditional.py      # Traditional imperative pipeline implementation (for comparison)
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css       # Frontend styles
└── templates/
    ├── dashboard.html  # Real-time dashboard
    └── compare.html    # Architecture comparison page
```

---

## 🔧 Core API

| Method | Endpoint | Description |
|-----|------|------|
| GET | `/api/lots` | Get all lot statuses |
| POST | `/api/lots` | Create a new lot |
| GET | `/api/lots/<id>` | Get a single lot's details |
| DELETE | `/api/lots/<id>` | Delete a lot |
| GET | `/api/tools` | Get tool-group utilization |
| GET | `/api/logs` | Get reconcile-loop logs |
| GET | `/api/metrics` | Get system metrics |
| POST | `/api/compare` | Run the architecture comparison test |

---

## 🎯 Reconcile Loop in Detail

The reconcile loop is the core of K8s cybernetics; this project runs it every 2 seconds:

```python
def reconcile(self):
    # 1. Observe: scan all active lots
    active_lots = [lot for lot in self.lots.values() 
                   if lot.status not in ["completed", "failed"]]
    
    # 2. Decide: for each lot, determine the action to take
    for lot in active_lots:
        if lot.status == "pending":
            # needs to be scheduled to a tool
            self._handle_pending(lot)
        elif lot.status == "running":
            # check whether the step is complete
            self._handle_running(lot)
    
    # 3. Act: trigger state transitions
    # ...(executed in the handle functions)
```

### Lot State Machine

```
     pending
        │
        ▼  schedule to a tool
     running
     │     │
     │     └─── step failed (<3 times) ───► running (retry)
     │
     ▼  step completed ──► more steps? ──┐
     │                                  │ yes
     │ no                               │
     ▼                                  │
  completed ◄───────────────────────────┘

  running
     │
     └─── failure count ≥ 3 ───► failed
```

---

## 📊 Dashboard Features

- **Lot status table**: real-time display of all lots' current step, status, progress, and duration
- **Tool utilization chart**: Chart.js visualizes each tool group's busy/idle ratio
- **Reconcile-loop log**: real-time system event log output, including scheduling, execution, failure, retry, etc.
- **System metrics**: total lots, completed, in-progress, failure rate, average duration

---

## 💡 Design Points

1. **Declarative API**: users only declare "I want to complete these steps"; the system automatically finds a way to achieve it
2. **Eventual consistency**: the system keeps reconciling until all lots converge to `completed` or `failed`
3. **Fault tolerance**: randomly simulates tool failures to verify self-healing (auto-retry)
4. **Resource constraints**: the number of tools is limited, so the scheduler must optimize its allocation strategy
5. **Concurrency safety**: uses RLock to protect shared state, supporting thread-safe access

---

## 📚 Further Reading

- [Kubernetes Controller pattern](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Kubernetes Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)
- [Cybernetics and distributed systems](https://en.wikipedia.org/wiki/Cybernetics)
