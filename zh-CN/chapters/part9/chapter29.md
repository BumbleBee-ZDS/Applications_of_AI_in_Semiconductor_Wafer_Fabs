# 第29章 晶圆厂AI算力底座——从GPU集群到边缘推理节点

> **本章导读**
> 
> 前28章构建了从数据治理到AI算法的完整体系，但所有AI系统最终都要落地到物理基础设施。本章聚焦晶圆厂AI的算力底座：如何设计GPU集群支撑大规模训练？如何部署低延迟推理服务？如何在边缘节点实现实时控制？我们将从算力需求分析出发，系统讲解集群架构、分布式训练、模型服务化、边缘部署、资源调度、成本优化、监控运维和验收基准，给出可直接落地的工程方案。

## 29.1 晶圆厂AI算力需求全景

晶圆厂的AI应用呈现明显的"三峰"特征：训练峰值、推理稳态、边缘实时。三类负载对算力的需求差异巨大，不能用一套架构简单覆盖。

### 训练负载：间歇性、高吞吐、长周期

训练类任务集中在良率预测模型、缺陷检测CNN、大语言模型微调等场景。其特点是：

- **数据规模大**：单批次晶圆涉及数千片，每片包含数百个工艺步骤的FDC时序数据、缺陷图像、量测结果，训练集动辄TB级
- **计算密集**：ResNet-50训练需要数十GPU·小时，LLM微调（如第27章实验27.8的LoRA训练）需要多卡并行
- **周期性执行**：新模型开发、季度重训练、工艺节点迁移时的全量训练，呈现"脉冲式"算力消耗
- **容错要求高**：训练任务可中断恢复，但对单步迭代时间敏感（影响实验效率）

**典型场景**：某3nm晶圆厂每季度进行良率模型全量重训练，使用128片A100 GPU集群，单次训练耗时约72小时，期间GPU利用率需保持在85%以上以确保投资回报。

### 推理负载：持续性、低延迟、高并发

推理类任务覆盖R2R控制、在线缺陷检测、虚拟量测等产线核心环节。其特点是：

- **7×24不间断**：产线不停，推理服务不停
- **延迟敏感**：R2R控制要求端到端延迟<50ms，缺陷检测要求单帧推理<20ms
- **并发量大**：单厂数百台设备同时推理，峰值QPS可达数千
- **可用性要求极高**：推理服务宕机=产线停摆，SLA要求99.99%以上

**典型场景**：某厂的FDC实时异常检测系统，接入500台设备的传感器流，每秒处理10万条时序记录，推理延迟P99<30ms，年可用性>99.99%。

### 边缘负载：超低延迟、离线容灾、资源受限

边缘类任务部署在设备侧或线边，覆盖实时工艺控制、本地质检、安全联锁等。其特点是：

- **极致延迟**：某些工艺控制环路要求<5ms响应
- **离线能力**：网络中断时必须能独立运行（产线不能等云端）
- **资源受限**：边缘设备算力有限（通常<100 TOPS），需模型压缩
- **环境苛刻**：洁净室温度、振动、电磁干扰约束

**典型场景**：刻蚀机台的终点检测（Endpoint Detection），基于等离子体光谱实时判断刻蚀完成时刻，要求延迟<2ms，部署在机台旁的工控机上。

### 算力需求矩阵

| 负载类型 | 典型场景 | 算力规模 | 延迟要求 | 可用性 | 部署位置 |
|---------|---------|---------|---------|--------|---------|
| 训练 | 良率模型重训练 | 数十~数百GPU | 分钟~小时级 | 99% | 中心机房/云 |
| 推理 | R2R控制、缺陷检测 | 数~数十GPU | <50ms | 99.99% | 中心机房 |
| 边缘 | 终点检测、本地质检 | <1 GPU | <5ms | 99.999% | 设备侧/线边 |

理解这三类负载的差异，是设计算力架构的前提。下一章将针对这些需求，设计GPU集群、推理服务、边缘节点的三层架构。

## 29.2 GPU集群架构设计与选型

晶圆厂AI训练集群的设计，需要在性能、成本、可扩展性之间找到平衡。与互联网大厂不同，晶圆厂通常不需要万卡集群，但对稳定性、数据安全、与产线系统的集成有更高要求。

### GPU选型：A100/H100 vs L40S vs 边缘GPU

| GPU型号 | 显存 | FP16算力 | 适用场景 | 单卡价格(参考) |
|---------|------|---------|---------|---------------|
| A100 80GB | 80GB HBM2e | 312 TFLOPS | 大模型训练、大规模并行 | $10k-15k |
| H100 80GB | 80GB HBM3 | 989 TFLOPS | 超大模型、混合精度训练 | $25k-40k |
| L40S 48GB | 48GB GDDR6 | 362 TFLOPS | 中等规模训练、推理 | $8k-12k |
| T4 16GB | 16GB GDDR6 | 65 TFLOPS | 推理、轻量微调 | $2k-3k |
| Jetson AGX Orin | 64GB LPDDR5 | 275 TOPS(INT8) | 边缘推理 | $1.5k-2k |

**选型建议**：

- **训练集群**：A100/H100为主力，80GB显存可容纳大batch和长序列
- **推理集群**：L40S/T4性价比高，支持多实例GPU(MIG)切分
- **边缘节点**：Jetson系列功耗低、算力足，支持TensorRT优化

### 集群拓扑：单机8卡 vs 多机多卡

**单机8卡方案**（适合中小厂）：

```
┌─────────────────────────────────────┐
│  GPU Node (8×A100 80GB)             │
│  ├─ NVLink全互联 (600GB/s)          │
│  ├─ 2× AMD EPYC 7763 (128C)        │
│  ├─ 2TB DDR4 RAM                    │
│  └─ 8× NVMe 3.84TB (RAID0)         │
└─────────────────────────────────────┘
         │
         │ PCIe Gen4 x16
         │
┌────────┴────────┐
│  100GbE/IB网络   │
└─────────────────┘
```

**优点**：NVLink提供卡间高速通信，适合单机内的数据并行；部署简单，运维成本低。

**缺点**：单机算力上限约2.5 PFLOPS(FP16)，难以支撑超大模型。

**多机多卡方案**（适合先进制程大厂）：

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Node 1   │  │ Node 2   │  │ Node 3   │
│ 8×A100   │  │ 8×A100   │  │ 8×A100   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │
     └──────────────┼──────────────┘
                    │
           ┌────────┴────────┐
           │ InfiniBand HDR  │
           │ (200Gb/s/port)  │
           └─────────────────┘
```

**关键组件**：

- **网络**：InfiniBand HDR(200Gb/s)或RoCE v2(100GbE)，卡间通信延迟<1μs
- **存储**：并行文件系统(Lustre/GPFS)或全闪存NAS，提供>10GB/s聚合带宽
- **调度**：Slurm或Kubernetes+GPU Operator，支持作业排队与资源隔离

### 网络选型：InfiniBand vs RoCE

| 特性 | InfiniBand HDR | RoCE v2 (100GbE) |
|------|---------------|------------------|
| 带宽 | 200 Gb/s | 100 Gb/s |
| 延迟 | <1 μs | 2-5 μs |
| 拥塞控制 | 硬件级，无损 | 需DCQCN等算法调优 |
| 成本 | 高（交换机$5k-10k/端口） | 低（复用以太网） |
| 生态 | NVIDIA主导 | 开放标准 |

**建议**：

- **预算充足、追求极致性能**：InfiniBand，适合大模型训练
- **成本敏感、已有以太网基础**：RoCE v2，适合中小规模训练与推理

### 存储架构：训练数据的IO瓶颈

训练任务的IO模式：大量小文件读取（图像）、顺序读取（时序数据）、随机访问（样本采样）。

**推荐架构**：

```
┌──────────────────────────────────────┐
│  热数据层 (NVMe SSD)                  │
│  ├─ 当前训练集 (RAID0, >10GB/s)       │
│  └─ 模型checkpoint                   │
└──────────────────────────────────────┘
              │
              │ 自动分层
              │
┌──────────────────────────────────────┐
│  温数据层 (SATA SSD/HDD)              │
│  ├─ 历史训练集                        │
│  └─ 验证集                           │
└──────────────────────────────────────┘
              │
              │ 归档
              │
┌──────────────────────────────────────┐
│  冷数据层 (对象存储/磁带)              │
│  └─ 原始数据备份                     │
└──────────────────────────────────────┘
```

**关键优化**：

- **预取与缓存**：训练前将数据集加载到内存或NVMe缓存，避免运行时IO等待
- **数据格式**：使用TFRecord、WebDataset等列式格式，减少小文件开销
- **并行加载**：多进程DataLoader + prefetch，掩盖IO延迟

### 实战案例：某3nm晶圆厂训练集群建设

**背景**：该厂每月需重训练20+个良率/缺陷模型，原有4卡A100集群成为瓶颈，单次训练耗时>1周。

**方案**：

- 建设16卡A100集群（2节点×8卡），InfiniBand互联
- 部署Lustre并行文件系统，聚合带宽15GB/s
- 引入Slurm作业调度，支持多租户排队

**效果**：

- 训练时间缩短70%（从7天→2天）
- GPU利用率从45%提升至82%
- 支持3个团队并行训练，互不干扰

**投资**：约$500k（含GPU、网络、存储、机柜），ROI<18个月。

## 29.3 分布式训练工程实践

当单卡显存不足以容纳模型或batch时，分布式训练成为必选项。晶圆厂场景常见的分布式策略包括数据并行、模型并行、混合精度训练。

### 数据并行：DDP vs FSDP vs ZeRO

**DDP (Distributed Data Parallel)**：

- 每张卡持有完整模型副本，数据分片
- 梯度通过AllReduce同步
- 适合模型可放入单卡的场景

```python
# PyTorch DDP示例
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group("nccl")
model = MyYieldModel().cuda()
model = DDP(model, device_ids=[local_rank])

for epoch in range(epochs):
    for batch in dataloader:
        loss = model(batch).loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

**FSDP (Fully Sharded Data Parallel)**：

- 模型参数、梯度、优化器状态全部分片
- 按需拉取参数，计算后丢弃
- 适合大模型（如LLM微调）

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(
    MyLargeModel(),
    sharding_strategy=FULL_SHARD,
    cpu_offload=CPUOffload(offload_params=True),  # 可选CPU卸载
)
```

**ZeRO (Zero Redundancy Optimizer)**：

- DeepSpeed库实现，分ZeRO-1/2/3三个阶段
- ZeRO-3等价于FSDP，参数/梯度/优化器全分片
- 支持超大模型（>10B参数）

### 模型并行：Tensor Parallel vs Pipeline Parallel

当模型过大无法放入单卡时，需要模型并行：

**Tensor Parallel (TP)**：

- 将单层参数（如Attention矩阵）切分到多卡
- 卡间通信频繁，需高速互联（NVLink）
- 适合Transformer类模型

**Pipeline Parallel (PP)**：

- 将模型按层切分，形成流水线
- 卡间通信较少，但存在气泡(bubble)
- 适合深层模型（如ResNet-152）

### 混合精度训练

使用FP16/BF16进行前向/反向计算，FP32保持主权重，可节省50%显存并加速2-3倍。

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    with autocast(dtype=torch.bfloat16):  # BF16更稳定
        loss = model(batch).loss
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 实战配置：良率预测模型分布式训练

**场景**：某厂训练基于Transformer的良率预测模型（500M参数），数据集100GB。

**配置**：

```yaml
# deepspeed_config.yaml
{
  "train_batch_size": 256,
  "gradient_accumulation_steps": 4,
  "fp16": {"enabled": true},
  "zero_optimization": {
    "stage": 2,
    "offload_optimizer": {"device": "cpu"}
  },
  "gradient_clipping": 1.0,
  "wall_clock_breakdown": false
}
```

**启动命令**：

```bash
deepspeed --num_nodes=2 --num_gpus=8 \
  train_yield_model.py \
  --deepspeed_config deepspeed_config.yaml \
  --data_path /lustre/data/yield_2024q3 \
  --output_dir /lustre/checkpoints/yield_model_v3
```

**性能调优要点**：

1. **数据加载**：使用WebDataset格式，8进程DataLoader，prefetch=4
2. **通信优化**：启用NCCL_DEBUG=INFO监控通信瓶颈，调整NCCL_ALGO
3. **Checkpoint**：每epoch保存，异步写入并行文件系统
4. **故障恢复**：启用elastic checkpoint，节点故障自动重启

### 训练监控与调试

**关键指标**：

- **GPU利用率**：`nvidia-smi`或DCGM Exporter，目标>80%
- **通信开销**：AllReduce时间占比，目标<20%
- **IO等待**：DataLoader空闲时间，目标<10%
- **显存峰值**：避免OOM，预留10%余量

**工具链**：

- **TensorBoard/W&B**：训练曲线、超参追踪
- **Nsight Systems**：GPU kernel级性能分析
- **PyTorch Profiler**：算子级瓶颈定位

## 29.4 高性能数据处理Pipeline

晶圆厂AI的数据来源多样（FDC时序、缺陷图像、结构化表格），如何高效加载、预处理、喂给模型，是训练性能的关键瓶颈。

### 数据格式选择

| 数据类型 | 推荐格式 | 优点 | 缺点 |
|---------|---------|------|------|
| 缺陷图像 | WebDataset (tar) | 顺序读取、高吞吐 | 不支持随机访问 |
| FDC时序 | Parquet | 列式存储、压缩好 | 需预处理为序列 |
| 结构化表格 | Parquet/CSV | 通用、易读 | 大文件性能差 |
| 混合数据 | TFRecord | 支持多模态 | 调试困难 |

### 高效数据加载器设计

**问题**：默认DataLoader在大量小文件场景下性能差（文件打开开销、元数据查询）。

**解决方案**：WebDataset + 多进程预取

```python
import webdataset as wds

dataset = (
    wds.WebDataset("s3://bucket/defect_data/{0000..0999}.tar")
    .decode("pil")                    # 解码图像
    .to_tuple("jpg", "json")          # 提取字段
    .map(preprocess)                  # 自定义预处理
    .batched(64)                      # 批处理
)

dataloader = wds.WebLoader(
    dataset,
    batch_size=None,                  # 已在dataset中batch
    num_workers=8,                    # 多进程加载
    prefetch=4                        # 预取batch
)
```

**性能对比**（缺陷检测训练）：

| 方案 | 吞吐量(img/s) | GPU利用率 |
|------|--------------|----------|
| 默认DataLoader + 小文件 | 120 | 45% |
| WebDataset + 8 workers | 850 | 92% |

### 数据预处理Pipeline

典型流程：

```
原始数据 → 清洗 → 特征提取 → 归一化 → 增强 → 批处理
```

**关键优化**：

1. **离线预处理**：将耗时操作（如图像裁剪、时序对齐）提前完成，存储为中间格式
2. **GPU加速预处理**：使用DALI(NVIDIA)或TorchVision transforms，将CPU操作迁移到GPU
3. **缓存热点数据**：对频繁访问的样本（如典型缺陷模式）建立内存缓存

```python
# DALI加速图像预处理
from nvidia.dali.pipeline import pipeline_def
import nvidia.dali.fn as fn

@pipeline_def(batch_size=64, num_threads=8, device_id=0)
def defect_pipeline():
    images, labels = fn.readers.file(
        file_root="/data/defect",
        random_shuffle=True
    )
    images = fn.decoders.image(images, device="mixed")  # GPU解码
    images = fn.resize(images, resize_x=224, resize_y=224)
    images = fn.normalize(images, mean=[0.485, 0.456, 0.406], 
                         std=[0.229, 0.224, 0.225])
    return images, labels
```

### 样本不均衡处理

晶圆厂数据普遍存在类别不均衡（如缺陷样本远少于正常样本）。

**策略**：

1. **过采样少数类**：SMOTE、数据增强（旋转、翻转、噪声）
2. **欠采样多数类**：随机丢弃、聚类中心保留
3. **类别权重**：在loss函数中为少数类赋予更高权重

```python
# 类别权重计算
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(labels),
    y=labels
)

# 在loss中使用
criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights).cuda())
```

### 数据版本管理

训练数据的版本追踪是可复现性的基础。

**工具**：DVC (Data Version Control)

```bash
# 初始化DVC
dvc init

# 追踪数据集
dvc add data/defect_dataset_v3/

# 提交到Git
git add data/defect_dataset_v3.dvc
git commit -m "Add defect dataset v3"

# 切换到历史版本
dvc checkout data/defect_dataset_v3.dvc@v2
```

**与MLflow集成**：

```python
import mlflow

with mlflow.start_run():
    mlflow.log_param("data_version", "defect_v3")
    mlflow.log_param("data_hash", dvc.api.get_url("data/defect_dataset_v3/"))
    # ... 训练逻辑
```

## 29.5 模型服务化与推理网关

训练好的模型需要部署为高可用、低延迟的推理服务，供产线系统调用。

### 推理引擎选型

| 引擎 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| TensorRT | NVIDIA GPU推理 | 极致性能、INT8量化 | 仅NVIDIA、编译慢 |
| Triton Inference Server | 多框架、多模型 | 支持动态batching、模型管理 | 部署复杂 |
| vLLM | LLM推理 | PagedAttention、高吞吐 | 仅LLM |
| ONNX Runtime | 跨平台 | 通用、CPU/GPU支持 | 性能不如专用引擎 |
| TorchScript | PyTorch模型 | 原生支持、易部署 | 性能一般 |

### Triton推理服务架构

```
┌─────────────────────────────────────────┐
│  Triton Inference Server                 │
│  ├─ Model Repository (/models)           │
│  │   ├─ defect_cnn/                      │
│  │   │   ├─ config.pbtxt                 │
│  │   │   └─ 1/model.plan (TensorRT)      │
│  │   └─ yield_predictor/                 │
│  │       ├─ config.pbtxt                 │
│  │       └─ 1/model.pt (PyTorch)         │
│  ├─ HTTP/gRPC Endpoint                   │
│  └─ Dynamic Batching                     │
└─────────────────────────────────────────┘
         │
         │ 负载均衡
         │
┌────────┴────────┐
│  API Gateway    │
│  (Kong/Nginx)   │
└─────────────────┘
```

**模型配置示例** (config.pbtxt)：

```protobuf
name: "defect_cnn"
platform: "tensorrt_plan"
max_batch_size: 64
input [
  {
    name: "image"
    data_type: TYPE_FP32
    dims: [3, 224, 224]
  }
]
output [
  {
    name: "defect_class"
    data_type: TYPE_INT32
    dims: [1]
  }
]
dynamic_batching {
  preferred_batch_size: [8, 16, 32]
  max_queue_delay_microseconds: 5000
}
instance_group [
  {
    count: 2
    kind: KIND_GPU
    gpus: [0, 1]
  }
]
```

### 动态Batching

将多个请求合并为一个batch处理，提升GPU利用率。

**原理**：

- 请求到达后进入队列，等待最多`max_queue_delay_microseconds`
- 累积到`preferred_batch_size`或超时后，合并为一个batch送入模型
- 推理完成后拆分结果返回各请求

**效果**（缺陷检测）：

| 策略 | 吞吐量(img/s) | P99延迟(ms) |
|------|--------------|------------|
| 单请求处理 | 200 | 15 |
| 动态batching (max_delay=5ms) | 850 | 22 |

### 模型版本管理与灰度发布

**模型仓库结构**：

```
/models/defect_cnn/
├── config.pbtxt
├── 1/              # v1 (生产)
│   └── model.plan
├── 2/              # v2 (灰度10%)
│   └── model.plan
└── 3/              # v3 (测试)
    └── model.plan
```

**灰度发布策略**：

```python
# 通过Triton模型路由实现灰度
# 90%流量走v1，10%流量走v2

import random

def route_model():
    if random.random() < 0.1:
        return "defect_cnn_v2"
    return "defect_cnn_v1"
```

**回滚机制**：

```bash
# 卸载问题版本
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/2/unload

# 加载稳定版本
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/1/load
```

### 推理服务高可用

**多副本部署**：

```yaml
# k8s deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: triton-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: triton
  template:
    spec:
      containers:
      - name: triton
        image: nvcr.io/nvidia/tritonserver:23.10-py3
        args: ["tritonserver", "--model-repository=/models"]
        resources:
          limits:
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /v2/health/live
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /v2/health/ready
            port: 8000
          initialDelaySeconds: 10
```

**负载均衡**：

```nginx
# nginx配置
upstream triton_backend {
    least_conn;
    server triton-0.triton:8000;
    server triton-1.triton:8000;
    server triton-2.triton:8000;
}

server {
    listen 80;
    location /inference {
        proxy_pass http://triton_backend;
        proxy_next_upstream error timeout http_502;
    }
}
```

### 监控与告警

**关键指标**：

- **推理延迟**：P50/P95/P99，告警阈值>50ms
- **吞吐量**：QPS，告警阈值<目标80%
- **GPU利用率**：目标>70%，告警<50%
- **错误率**：目标<0.1%，告警>1%
- **队列深度**：动态batch队列长度，告警>100

**Prometheus + Grafana监控栈**：

```python
# Triton指标导出
# 默认在/metrics端点暴露Prometheus格式指标

# 自定义业务指标
from prometheus_client import Counter, Histogram

INFERENCE_LATENCY = Histogram(
    'inference_latency_seconds',
    'Time spent on model inference',
    ['model_name']
)

INFERENCE_ERRORS = Counter(
    'inference_errors_total',
    'Number of inference errors',
    ['model_name', 'error_type']
)
```

## 29.6 边缘部署与实时推理

边缘推理是晶圆厂AI的"最后一公里"，直接服务于产线实时控制。

### 边缘场景分类

| 场景 | 延迟要求 | 算力需求 | 部署位置 |
|------|---------|---------|---------|
| 终点检测 | <2ms | <10 TOPS | 机台内嵌 |
| 本地质检 | <20ms | <50 TOPS | 线边工控机 |
| 安全联锁 | <1ms | <5 TOPS | PLC/安全控制器 |
| 数据预处理 | <10ms | <20 TOPS | 边缘网关 |

### 边缘硬件选型

**NVIDIA Jetson系列**：

| 型号 | 算力(INT8) | 显存 | 功耗 | 价格 |
|------|-----------|------|------|------|
| Jetson Nano | 472 GFLOPS | 4GB | 5-10W | $99 |
| Jetson Xavier NX | 21 TOPS | 8GB | 10-15W | $399 |
| Jetson AGX Orin | 275 TOPS | 64GB | 15-60W | $1,999 |

**推荐**：

- **轻量任务**（终点检测）：Jetson Xavier NX，性价比最优
- **复杂任务**（多模型推理）：Jetson AGX Orin，算力充足
- **超低延迟**（安全联锁）：FPGA或专用ASIC

### 模型压缩与优化

**量化**：

将FP32模型转换为INT8，算力提升2-4倍，精度损失<1%。

```python
# TensorRT量化
import tensorrt as trt

logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
parser = trt.OnnxParser(network, logger)

with open("model.onnx", "rb") as f:
    parser.parse(f.read())

# INT8量化配置
config = builder.create_builder_config()
config.set_flag(trt.BuilderFlag.INT8)
config.int8_calibrator = MyCalibrator(calibration_data)

engine = builder.build_engine(network, config)
with open("model_int8.engine", "wb") as f:
    f.write(engine.serialize())
```

**剪枝**：

移除不重要的权重或通道，减少计算量。

```python
# 结构化剪枝（通道级）
from torch.nn.utils import prune

for name, module in model.named_modules():
    if isinstance(module, nn.Conv2d):
        prune.ln_structured(module, name='weight', amount=0.3, dim=0, n=2)
        prune.remove(module, 'weight')
```

**知识蒸馏**：

用大模型(teacher)指导小模型(student)训练。

```python
# 蒸馏loss
def distillation_loss(student_logits, teacher_logits, temperature=4.0):
    student_log_softmax = F.log_softmax(student_logits / temperature, dim=1)
    teacher_softmax = F.softmax(teacher_logits / temperature, dim=1)
    return F.kl_div(student_log_softmax, teacher_softmax, reduction='batchmean')
```

### 边缘推理框架

**TensorRT**：

NVIDIA GPU专用推理引擎，性能最优。

```python
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

# 加载engine
with open("model.engine", "rb") as f:
    runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
    engine = runtime.deserialize_cuda_engine(f.read())

# 推理
context = engine.create_execution_context()
input_host = np.random.randn(1, 3, 224, 224).astype(np.float32)
output_host = np.empty((1, 1000), dtype=np.float32)

# 分配GPU内存
input_device = cuda.mem_alloc(input_host.nbytes)
output_device = cuda.mem_alloc(output_host.nbytes)

# 拷贝数据
cuda.memcpy_htod(input_device, input_host)
context.execute(1, [int(input_device), int(output_device)])
cuda.memcpy_dtoh(output_host, output_device)
```

**ONNX Runtime**：

跨平台推理引擎，支持CPU/GPU/NPU。

```python
import onnxruntime as ort

session = ort.InferenceSession("model.onnx")
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

result = session.run([output_name], {input_name: input_data})
```

### 离线容灾设计

边缘节点必须在网络中断时独立运行。

**策略**：

1. **本地模型缓存**：边缘节点存储最新模型版本，定期从中心同步
2. **本地数据存储**：推理结果先存本地，网络恢复后上传
3. **降级模式**：模型异常时切换到规则引擎或默认值

```python
class EdgeInferenceService:
    def __init__(self):
        self.model = self.load_local_model()
        self.fallback = RuleBasedFallback()
        self.local_buffer = LocalBuffer()
    
    def infer(self, input_data):
        try:
            result = self.model.predict(input_data)
            self.local_buffer.save(input_data, result)
            return result
        except ModelError:
            # 模型异常，降级到规则引擎
            return self.fallback.predict(input_data)
    
    def sync_to_cloud(self):
        if self.is_network_available():
            self.local_buffer.upload_pending()
```

### 实战案例：刻蚀终点检测边缘部署

**背景**：某厂刻蚀机需要实时检测刻蚀终点，原方案依赖云端推理，延迟>100ms，导致过刻蚀。

**方案**：

- 部署Jetson AGX Orin在机台旁
- 模型压缩：FP32→INT8量化，推理时间从15ms→3ms
- 离线容灾：本地存储最近7天模型，网络中断时独立运行

**效果**：

- 端到端延迟从100ms→8ms（含数据采集）
- 过刻蚀率从2.3%→0.4%
- 年节省晶圆报废成本>$500k

## 29.7 算力调度与资源隔离

晶圆厂AI算力需要服务多个团队（工艺、设备、良率）、多种任务（训练、推理、实验），如何公平、高效地分配资源是关键挑战。

### 调度策略

**优先级队列**：

```
优先级1: 产线推理服务（不可中断）
优先级2: 紧急训练任务（如良率异常排查）
优先级3: 常规训练任务
优先级4: 开发实验
```

**资源配额**：

```yaml
# Kubernetes ResourceQuota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: yield-team-quota
spec:
  hard:
    requests.nvidia.com/gpu: 8
    limits.nvidia.com/gpu: 16
    cpu: "64"
    memory: 256Gi
```

**时间片轮转**：

白天优先推理服务，夜间释放GPU给训练任务。

```python
# 基于时间的调度策略
from datetime import datetime

def get_priority():
    hour = datetime.now().hour
    if 8 <= hour < 20:  # 白天
        return "inference"
    else:  # 夜间
        return "training"
```

### 多租户隔离

**命名空间隔离**：

```yaml
# 每个团队独立命名空间
apiVersion: v1
kind: Namespace
metadata:
  name: yield-team
  labels:
    team: yield
    cost-center: CC1234
```

**GPU切分（MIG）**：

A100支持MIG（Multi-Instance GPU），将单卡切分为最多7个实例。

```bash
# 启用MIG
nvidia-smi -i 0 -mig 1

# 创建GPU实例（1g.10gb = 1/7 A100）
nvidia-smi mig -cgi 1g.10gb -C
```

**网络隔离**：

```yaml
# NetworkPolicy限制跨命名空间访问
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: yield-team-isolation
  namespace: yield-team
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: yield-team
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: yield-team
```

### 弹性伸缩

**基于负载的自动扩缩**：

```yaml
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: triton-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: gpu_utilization
      target:
        type: AverageValue
        averageValue: "70"
```

**基于时间的定时扩缩**：

```yaml
# 夜间扩容训练集群
apiVersion: autoscaling/v1
kind: ScheduledScale
metadata:
  name: training-night-scale
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: training-cluster
  schedules:
  - schedule: "0 22 * * *"  # 每晚22:00
    replicas: 8
  - schedule: "0 8 * * *"   # 每早8:00
    replicas: 2
```

### 作业调度系统

**Slurm**：

传统HPC作业调度器，适合批处理训练任务。

```bash
# 提交训练作业
sbatch --gres=gpu:8 --time=24:00:00 train_yield.sh

# 查看作业状态
squeue

# 取消作业
scancel <job_id>
```

**Volcano**：

Kubernetes原生的批处理调度器，支持Gang Scheduling。

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: distributed-training
spec:
  minAvailable: 4
  schedulerName: volcano
  plugins:
    env: []
    svc: []
  tasks:
  - replicas: 4
    name: worker
    template:
      spec:
        containers:
        - name: worker
          image: training-image:latest
          resources:
            limits:
              nvidia.com/gpu: 8
```

### 实战案例：多团队算力共享平台

**背景**：某厂3个AI团队（良率、缺陷、设备）共享16卡A100集群，资源争抢严重。

**方案**：

- Kubernetes + Volcano调度
- 每团队独立命名空间，配额8 GPU
- 推理服务优先级最高，训练任务排队
- 夜间自动扩容训练集群

**效果**：

- 资源争抢投诉减少90%
- GPU利用率从55%提升至78%
- 训练任务等待时间从3天→4小时

## 29.8 算力成本建模与TCO分析

AI算力投资巨大，需要精细化的成本建模与ROI分析。

### TCO构成

**硬件成本**：

- GPU服务器：$10k-50k/节点
- 网络设备：InfiniBand交换机$5k-10k/端口
- 存储系统：全闪存NAS $50k-200k
- 机柜、电力、散热：$5k-10k/年/机柜

**软件成本**：

- GPU驱动、CUDA：免费
- 容器平台（K8s）：免费
- MLOps平台（Kubeflow）：免费
- 商业软件（如Weights & Biases）：$50-200/user/月

**人力成本**：

- AI平台工程师：$150k-250k/年
- MLOps工程师：$120k-200k/年
- GPU运维工程师：$100k-150k/年

**电力成本**：

- 单卡A100功耗：300W
- 8卡节点功耗：~3kW
- 电费：$0.1/kWh → $2,600/年/节点

### TCO对比：自建 vs 云 vs 混合

**场景**：16卡A100集群，5年TCO

| 方案 | 硬件 | 电力 | 人力 | 云费用 | 5年TCO |
|------|------|------|------|--------|--------|
| 自建 | $400k | $50k | $500k | - | $950k |
| 纯云(AWS) | - | - | $200k | $1.2M | $1.4M |
| 混合(8卡自建+8卡云) | $200k | $25k | $350k | $600k | $1.175M |

**结论**：

- **长期稳定负载**：自建更经济（TCO低30-40%）
- **波动性负载**：云更灵活（按需付费）
- **混合方案**：平衡成本与弹性

### ROI计算框架

**收益项**：

- 良率提升：每1%提升 → $10M-50M/年（视产能与产品价值）
- 效率提升：训练时间缩短 → 工程师生产力提升
- 成本节省：自动化替代人工 → 人力成本节省

**成本项**：

- 算力投资：硬件+软件+人力
- 运维成本：电力+维护+升级

**ROI公式**：

```
ROI = (年化收益 - 年化成本) / 年化成本 × 100%
```

**案例**：

- 投资：$200k（算力）+ $100k/年（运维）= $300k/年
- 收益：良率提升0.5% → $25M/年
- ROI = ($25M - $0.3M) / $0.3M × 100% = 8233%

### 成本优化策略

**GPU利用率提升**：

- 动态batching：提升推理吞吐
- 模型量化：减少显存占用
- 多任务共享：同一GPU服务多个模型

**云成本优化**：

- 预留实例：1年/3年预留，折扣30-60%
- Spot实例：非关键任务使用，折扣60-90%
- 自动扩缩：夜间缩容，避免闲置

**电力优化**：

- 液冷散热：PUE从1.5→1.2，节电20%
- 智能调度：夜间低谷电价时段训练
- 余热回收：用于办公供暖

### 实战案例：算力投资ROI分析

**背景**：某厂投资$500k建设AI训练集群，需评估ROI。

**成本**：

- 硬件：$500k（一次性）
- 运维：$50k/年（人力+电力）
- 5年TCO：$750k

**收益**：

- 良率提升0.3%：$15M/年
- 训练效率提升50%：工程师时间节省$100k/年
- 年化收益：$15.1M

**ROI**：

- 年化成本：$150k（$750k/5年）
- ROI = ($15.1M - $0.15M) / $0.15M × 100% = 9967%
- 回收期：<1个月

## 29.9 基础设施监控与故障自愈

GPU集群的稳定性直接影响AI任务的连续性，需要全面的监控与自愈机制。

### 监控指标体系

**硬件层**：

- GPU温度、功耗、风扇转速
- 显存ECC错误计数
- NVLink/PCIe带宽与错误率
- CPU/内存/磁盘使用率

**软件层**：

- GPU利用率、显存占用
- 训练任务进度、loss曲线
- 推理服务延迟、吞吐量、错误率
- 网络带宽、延迟、丢包率

**业务层**：

- 模型准确率、漂移指标
- 数据管道延迟、失败率
- SLA达成率

### DCGM Exporter + Prometheus

NVIDIA DCGM (Data Center GPU Manager) 提供GPU监控API。

```bash
# 部署DCGM Exporter
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/dcgm-exporter/main/deployment/dcgm-exporter.yaml

# Prometheus配置
scrape_configs:
  - job_name: 'dcgm'
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

**关键指标**：

```
DCGM_FI_DEV_GPU_TEMP          # GPU温度
DCGM_FI_DEV_POWER_USAGE       # 功耗
DCGM_FI_DEV_FB_FREE           # 显存空闲
DCGM_FI_DEV_GPU_UTIL          # GPU利用率
DCGM_FI_DEV_ECC_DBE_VOL_TOTAL # 双位ECC错误（严重）
```

### 告警规则

```yaml
# Prometheus告警规则
groups:
  - name: gpu_alerts
    rules:
    - alert: GPUTemperatureHigh
      expr: DCGM_FI_DEV_GPU_TEMP > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "GPU温度过高: {{ $labels.gpu }}"
    
    - alert: GPUECCError
      expr: increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[5m]) > 0
      labels:
        severity: critical
      annotations:
        summary: "GPU发生ECC错误: {{ $labels.gpu }}"
    
    - alert: InferenceLatencyHigh
      expr: histogram_quantile(0.99, inference_latency_seconds) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "推理延迟P99>50ms"
```

### 故障自愈机制

**GPU故障自动隔离**：

```python
import subprocess
import time

def check_gpu_health(gpu_id):
    """检查GPU健康状态"""
    result = subprocess.run(
        ["nvidia-smi", "-i", str(gpu_id), "--query-gpu=ecc.errors.uncorrected.volatile.total", "--format=csv,noheader"],
        capture_output=True, text=True
    )
    ecc_errors = int(result.stdout.strip())
    return ecc_errors == 0

def isolate_faulty_gpu(gpu_id):
    """隔离故障GPU"""
    # 从调度池中移除
    subprocess.run(["nvidia-smi", "-i", str(gpu_id), "-mig", "0"])
    # 发送告警
    send_alert(f"GPU {gpu_id} 已隔离，存在ECC错误")
    # 记录日志
    log_event(f"GPU {gpu_id} isolated due to ECC errors")

# 定期检查
while True:
    for gpu_id in range(8):
        if not check_gpu_health(gpu_id):
            isolate_faulty_gpu(gpu_id)
    time.sleep(60)
```

**训练任务容错**：

```python
# PyTorch Elastic（自动恢复）
import torch.distributed.elastic as etcd

# 配置checkpoint
def save_checkpoint(model, optimizer, epoch, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

# 故障恢复
def load_checkpoint(path):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return checkpoint['epoch']

# Elastic训练
etcd.run(
    train_func,
    min_nodes=2,
    max_nodes=4,
    rdzv_backend="etcd",
    rdzv_endpoint="etcd:2379"
)
```

**推理服务降级**：

```python
class InferenceService:
    def __init__(self):
        self.primary_model = load_model("primary")
        self.fallback_model = load_model("fallback")  # 轻量版模型
        self.rule_engine = RuleEngine()
    
    def predict(self, input_data):
        try:
            # 尝试主模型
            return self.primary_model.predict(input_data)
        except ModelError:
            try:
                # 降级到轻量模型
                return self.fallback_model.predict(input_data)
            except ModelError:
                # 降级到规则引擎
                return self.rule_engine.predict(input_data)
```

### 实战案例：GPU集群故障自愈系统

**背景**：某厂16卡A100集群，月均发生2-3次GPU故障，导致训练任务中断。

**方案**：

- DCGM Exporter + Prometheus监控
- ECC错误自动检测与GPU隔离
- 训练任务Elastic Checkpoint，故障自动恢复
- 推理服务多级降级

**效果**：

- 训练任务中断时间从8小时/月→30分钟/月
- 推理服务可用性从99.5%→99.99%
- 运维人力节省50%

## 29.10 算力底座验收基准与压测

新建或升级算力底座后，需要进行严格的验收测试，确保满足生产要求。

### 验收维度

**性能基准**：

- 训练吞吐：tokens/s（LLM）、images/s（CV）
- 推理延迟：P50/P95/P99
- 网络带宽：AllReduce吞吐、延迟
- 存储IO：顺序/随机读写带宽

**稳定性基准**：

- 长时间运行：72小时连续训练无故障
- 故障恢复：节点故障后自动恢复时间<10分钟
- 内存泄漏：显存/内存占用稳定

**功能基准**：

- 多租户隔离：资源配额、网络隔离
- 弹性伸缩：自动扩缩容响应时间<2分钟
- 监控告警：指标采集完整率>99%

### 训练性能压测

**MLPerf Training**：

业界标准训练基准，覆盖ResNet、BERT、GPT等模型。

```bash
# 运行MLPerf Training
cd mlperf/training
make run MODEL=bert DATA_DIR=/data/bpho

# 结果解读
# BERT训练时间：< 3.5小时（8×A100）为合格
```

**自定义基准**：

```python
# 晶圆厂典型模型训练基准
import time
import torch

def benchmark_training(model, dataloader, epochs=3):
    """训练性能基准测试"""
    optimizer = torch.optim.Adam(model.parameters())
    
    start = time.time()
    for epoch in range(epochs):
        for batch in dataloader:
            loss = model(batch).loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
    
    elapsed = time.time() - start
    throughput = len(dataloader) * epochs / elapsed
    print(f"Throughput: {throughput:.2f} batches/s")
    return throughput

# 基准要求
# 良率预测模型(ResNet-50): >500 images/s (8×A100)
# 缺陷检测模型(ResNet-101): >300 images/s (8×A100)
```

### 推理性能压测

**工具**：Triton Perf Analyzer

```bash
# 推理性能测试
perf_analyzer -m defect_cnn -b 32 --service-triton triton:8001

# 结果解读
# 吞吐量: >1000 inferencing/s (单卡A100)
# P99延迟: <30ms
```

**并发测试**：

```python
import asyncio
import aiohttp

async def inference_request(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def benchmark_concurrent(url, data, concurrency=100):
    """并发推理压测"""
    async with aiohttp.ClientSession() as session:
        tasks = [inference_request(session, url, data) for _ in range(concurrency)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"Throughput: {concurrency / elapsed:.2f} req/s")
        print(f"P99 Latency: {sorted([r['latency'] for r in results])[int(concurrency*0.99)]:.2f}ms")
```

### 稳定性压测

**72小时连续训练**：

```bash
# 启动长时间训练任务
nohup python train_yield_model.py --epochs 100 > train.log 2>&1 &

# 监控脚本
while true; do
    # 检查GPU状态
    nvidia-smi --query-gpu=temperature,memory.used,utilization.gpu --format=csv >> gpu_monitor.log
    
    # 检查训练进度
    tail -n 1 train.log >> progress.log
    
    sleep 60
done
```

**故障注入测试**：

```bash
# 模拟GPU故障
nvidia-smi -i 0 --gpu-lock=1  # 锁定GPU

# 验证训练任务自动恢复
# 预期：任务在10分钟内自动迁移到其他节点继续训练
```

### 验收清单

**硬件验收**：

- [ ] GPU型号、数量符合设计
- [ ] 网络带宽达到设计指标（InfiniBand 200Gb/s）
- [ ] 存储IO满足训练需求（>10GB/s）
- [ ] 电力、散热满足满载运行

**软件验收**：

- [ ] GPU驱动、CUDA版本正确
- [ ] 容器平台（K8s）部署成功
- [ ] 调度系统（Slurm/Volcano）配置完成
- [ ] 监控告警系统上线

**性能验收**：

- [ ] 训练吞吐达到基准要求
- [ ] 推理延迟满足SLA
- [ ] 72小时稳定性测试通过
- [ ] 故障恢复时间<10分钟

**功能验收**：

- [ ] 多租户隔离有效
- [ ] 弹性伸缩正常工作
- [ ] 监控指标采集完整
- [ ] 告警规则触发正确

### 实战案例：算力底座验收

**背景**：某厂新建16卡A100集群，需验收后上线。

**验收过程**：

1. **硬件检查**：GPU型号、网络带宽、存储IO均达标
2. **性能压测**：
   - MLPerf BERT训练：3.2小时（要求<3.5小时）✓
   - 推理吞吐：1200 inferencing/s（要求>1000）✓
   - P99延迟：25ms（要求<30ms）✓
3. **稳定性测试**：72小时连续训练无故障 ✓
4. **故障注入**：模拟GPU故障，任务8分钟内恢复 ✓

**结果**：验收通过，正式上线。

---

## 本章小结

本章系统介绍了晶圆厂AI算力底座的设计与实施，覆盖从GPU集群到边缘推理节点的完整架构。核心要点：

1. **三类负载差异化设计**：训练（高吞吐）、推理（低延迟）、边缘（实时性）需要不同的硬件与架构方案
2. **集群选型关键**：GPU型号、网络拓扑、存储架构直接影响训练性能与成本
3. **分布式训练工程**：DDP/FSDP/ZeRO策略选择、混合精度、数据Pipeline优化是训练效率的关键
4. **推理服务化**：Triton + 动态batching + 灰度发布构建高可用推理服务
5. **边缘部署**：模型压缩 + TensorRT优化 + 离线容灾实现产线实时推理
6. **资源调度**：多租户隔离、优先级队列、弹性伸缩保障资源公平与高效利用
7. **成本与TCO**：自建vs云vs混合方案需要精细化ROI分析
8. **监控与自愈**：DCGM + Prometheus + 自动故障隔离保障集群稳定性
9. **验收基准**：性能、稳定性、功能三维度的严格验收确保生产就绪

算力底座是AI工程化的物理基础，下一章将在此基础上构建AI平台，提供模型开发、部署、运维的工具链与开发者体验。
