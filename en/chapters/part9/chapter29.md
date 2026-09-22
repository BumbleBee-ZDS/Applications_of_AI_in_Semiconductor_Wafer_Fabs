# Chapter 29: Wafer Fab AI Computing Infrastructure - From GPU Clusters to Edge Inference Nodes

> **Chapter Guide**
> 
> Chapters 1-28 built a complete system from data governance to AI algorithms, but all AI systems ultimately need to run on physical infrastructure. This chapter focuses on the computing foundation for wafer fab AI: How to design GPU clusters for large-scale training? How to deploy low-latency inference services? How to achieve real-time control at edge nodes? Starting from computing demand analysis, we systematically cover cluster architecture, distributed training, model serving, edge deployment, resource scheduling, cost optimization, monitoring & operations, and acceptance benchmarks—providing directly implementable engineering solutions.

## 29.1 Wafer Fab AI Computing Demand Landscape

Wafer fab AI applications exhibit a distinct "three-peak" characteristic: training peaks, inference steady-state, and edge real-time. The computing demands of these three load types vary significantly and cannot be covered by a single architecture.

### Training Load: Intermittent, High Throughput, Long Duration

Training tasks focus on yield prediction models, defect detection CNNs, and large language model fine-tuning. Their characteristics include:

- **Large data scale**: A single wafer batch involves thousands of wafers, each containing FDC time-series data, defect images, and measurement results for hundreds of process steps. Training sets are often TB-scale
- **Compute intensive**: ResNet-50 training requires tens of GPU-hours; LLM fine-tuning (such as LoRA training in Chapter 27 Experiment 27.8) requires multi-GPU parallelism
- **Periodic execution**: New model development, quarterly retraining, and full training during process node migration show "pulse-like" computing consumption
- **High fault tolerance requirements**: Training tasks can be interrupted and resumed, but are sensitive to single-step iteration time (affecting experimental efficiency)

**Typical scenario**: A 3nm wafer fab conducts quarterly full retraining of yield models using a 128-A100 GPU cluster. Each training session takes approximately 72 hours, during which GPU utilization must be maintained above 85% to ensure return on investment.

### Inference Load: Continuous, Low Latency, High Concurrency

Inference tasks cover R2R control, online defect detection, and virtual metrology—core production line functions. Their characteristics include:

- **24/7 uninterrupted**: Production line doesn't stop, inference services don't stop
- **Latency sensitive**: R2R control requires end-to-end latency <50ms; defect detection requires single-frame inference <20ms
- **High concurrency**: Hundreds of devices perform inference simultaneously in a single fab, with peak QPS reaching thousands
- **Extremely high availability requirements**: Inference service downtime = production line stoppage; SLA requirement is 99.99% or above

**Typical scenario**: A fab's FDC real-time anomaly detection system connects to sensor streams from 500 devices, processing 100,000 time-series records per second, with inference latency P99 <30ms and annual availability >99.99%.

### Edge Load: Ultra-Low Latency, Offline Disaster Recovery, Resource Constrained

Edge tasks are deployed on the device side or production line edge, covering real-time process control, local quality inspection, and safety interlocks. Their characteristics include:

- **Extreme latency**: Some process control loops require <5ms response
- **Offline capability**: Must operate independently when the network is interrupted (production line cannot wait for the cloud)
- **Resource constrained**: Edge devices have limited computing power (typically <100 TOPS), requiring model compression
- **Harsh environment**: Cleanroom temperature, vibration, and electromagnetic interference constraints

**Typical scenario**: Endpoint detection for etching tools, using plasma spectroscopy to determine the etching completion time in real-time, requires latency <2ms, deployed on an industrial PC next to the tool.

### Computing Demand Matrix

| Load Type | Typical Scenario | Computing Scale | Latency Requirement | Availability | Deployment Location |
|-----------|------------------|-----------------|---------------------|--------------|---------------------|
| Training | Yield model retraining | Tens to hundreds of GPUs | Minutes to hours | 99% | Central data center/Cloud |
| Inference | R2R control, defect detection | Several to tens of GPUs | <50ms | 99.99% | Central data center |
| Edge | Endpoint detection, local inspection | <1 GPU | <5ms | 99.999% | Device side/Production line edge |

Understanding the differences among these three load types is the prerequisite for designing computing architecture. The next section will design a three-layer architecture of GPU clusters, inference services, and edge nodes to address these requirements.

## 29.2 GPU Cluster Architecture Design and Selection

Designing AI training clusters for wafer fabs requires finding a balance among performance, cost, and scalability. Unlike large internet companies, wafer fabs typically don't need ten-thousand-card clusters, but have higher requirements for stability, data security, and integration with production line systems.

### GPU Selection: A100/H100 vs L40S vs Edge GPUs

| GPU Model | Memory | FP16 Performance | Use Case | Single Card Price (Reference) |
|-----------|--------|------------------|----------|-------------------------------|
| A100 80GB | 80GB HBM2e | 312 TFLOPS | Large model training, large-scale parallelism | $10k-15k |
| H100 80GB | 80GB HBM3 | 989 TFLOPS | Ultra-large models, mixed-precision training | $25k-40k |
| L40S 48GB | 48GB GDDR6 | 362 TFLOPS | Medium-scale training, inference | $8k-12k |
| T4 16GB | 16GB GDDR6 | 65 TFLOPS | Inference, lightweight fine-tuning | $2k-3k |
| Jetson AGX Orin | 64GB LPDDR5 | 275 TOPS (INT8) | Edge inference | $1.5k-2k |

**Selection recommendations**:

- **Training clusters**: A100/H100 as the main force; 80GB memory can accommodate large batches and long sequences
- **Inference clusters**: L40S/T4 offers high cost-effectiveness and supports Multi-Instance GPU (MIG) partitioning
- **Edge nodes**: Jetson series has low power consumption and sufficient computing power, supporting TensorRT optimization

### Cluster Topology: Single Machine 8-GPU vs Multi-Machine Multi-GPU

**Single machine 8-GPU solution** (suitable for small to medium fabs):

```
┌─────────────────────────────────────┐
│  GPU Node (8×A100 80GB)             │
│  ├─ NVLink full interconnect (600GB/s)│
│  ├─ 2× AMD EPYC 7763 (128C)         │
│  ├─ 2TB DDR4 RAM                    │
│  └─ 8× NVMe 3.84TB (RAID0)          │
└─────────────────────────────────────┘
         │
         │ PCIe Gen4 x16
         │
┌────────┴────────┐
│  100GbE/IB Network│
└─────────────────┘
```

**Advantages**: NVLink provides high-speed inter-card communication, suitable for data parallelism within a single machine; simple deployment and low O&M costs.

**Disadvantages**: Single-machine computing power limit is approximately 2.5 PFLOPS (FP16), difficult to support ultra-large models.

**Multi-machine multi-GPU solution** (suitable for advanced process node fabs):

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

**Key components**:

- **Network**: InfiniBand HDR (200Gb/s) or RoCE v2 (100GbE), inter-card communication latency <1μs
- **Storage**: Parallel file system (Lustre/GPFS) or all-flash NAS, providing >10GB/s aggregate bandwidth
- **Scheduling**: Slurm or Kubernetes + GPU Operator, supporting job queuing and resource isolation

### Network Selection: InfiniBand vs RoCE

| Feature | InfiniBand HDR | RoCE v2 (100GbE) |
|---------|----------------|------------------|
| Bandwidth | 200 Gb/s | 100 Gb/s |
| Latency | <1 μs | 2-5 μs |
| Congestion control | Hardware-level, lossless | Requires DCQCN and other algorithm tuning |
| Cost | High (switch $5k-10k/port) | Low (reuses Ethernet) |
| Ecosystem | NVIDIA-dominated | Open standard |

**Recommendations**:

- **Sufficient budget, pursuing ultimate performance**: InfiniBand, suitable for large model training
- **Cost-sensitive, existing Ethernet foundation**: RoCE v2, suitable for small to medium-scale training and inference

### Storage Architecture: IO Bottleneck for Training Data

Training task IO patterns: large-scale small file reads (images), sequential reads (time-series data), random access (sample sampling).

**Recommended architecture**:

```
┌──────────────────────────────────────┐
│  Hot data layer (NVMe SSD)           │
│  ├─ Current training set (RAID0, >10GB/s)│
│  └─ Model checkpoints                │
└──────────────────────────────────────┘
              │
              │ Automatic tiering
              │
┌──────────────────────────────────────┐
│  Warm data layer (SATA SSD/HDD)      │
│  ├─ Historical training sets         │
│  └─ Validation sets                  │
└──────────────────────────────────────┘
              │
              │ Archival
              │
┌──────────────────────────────────────┐
│  Cold data layer (Object storage/Tape)│
│  └─ Raw data backup                  │
└──────────────────────────────────────┘
```

**Key optimizations**:

- **Prefetching and caching**: Load datasets into memory or NVMe cache before training to avoid runtime IO waits
- **Data format**: Use columnar formats such as TFRecord and WebDataset to reduce small file overhead
- **Parallel loading**: Multi-process DataLoader + prefetch to mask IO latency

### Practical Case: 3nm Wafer Fab Training Cluster Construction

**Background**: The fab needs to retrain 20+ yield/defect models monthly. The original 4-A100 cluster became a bottleneck, with each training session taking >1 week.

**Solution**:

- Build a 16-A100 cluster (2 nodes × 8 cards), InfiniBand interconnect
- Deploy Lustre parallel file system with 15GB/s aggregate bandwidth
- Introduce Slurm job scheduling to support multi-tenant queuing

**Results**:

- Training time reduced by 70% (from 7 days → 2 days)
- GPU utilization increased from 45% to 82%
- Supports 3 teams training in parallel without interference

**Investment**: Approximately $500k (including GPUs, network, storage, racks), ROI <18 months.

## 29.3 Distributed Training Engineering Practice

When a single card's memory cannot accommodate the model or batch, distributed training becomes necessary. Common distributed strategies in wafer fab scenarios include data parallelism, model parallelism, and mixed-precision training.

### Data Parallelism: DDP vs FSDP vs ZeRO

**DDP (Distributed Data Parallel)**:

- Each card holds a complete model copy, with data sharded
- Gradients synchronized via AllReduce
- Suitable for scenarios where the model fits on a single card

```python
# PyTorch DDP example
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

**FSDP (Fully Sharded Data Parallel)**:

- Model parameters, gradients, and optimizer states are all sharded
- Parameters pulled on demand, discarded after computation
- Suitable for large models (such as LLM fine-tuning)

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(
    MyLargeModel(),
    sharding_strategy=FULL_SHARD,
    cpu_offload=CPUOffload(offload_params=True),  # Optional CPU offloading
)
```

**ZeRO (Zero Redundancy Optimizer)**:

- Implemented in the DeepSpeed library, divided into ZeRO-1/2/3 stages
- ZeRO-3 is equivalent to FSDP, with parameters/gradients/optimizer all sharded
- Supports ultra-large models (>10B parameters)

### Model Parallelism: Tensor Parallel vs Pipeline Parallel

When the model is too large to fit on a single card, model parallelism is needed:

**Tensor Parallel (TP)**:

- Shards single-layer parameters (such as Attention matrices) across multiple cards
- Frequent inter-card communication, requiring high-speed interconnect (NVLink)
- Suitable for Transformer-type models

**Pipeline Parallel (PP)**:

- Cuts the model by layers, forming a pipeline
- Less inter-card communication, but has bubbles
- Suitable for deep models (such as ResNet-152)

### Mixed-Precision Training

Using FP16/BF16 for forward/backward computation while keeping FP32 master weights can save 50% memory and accelerate 2-3x.

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    with autocast(dtype=torch.bfloat16):  # BF16 is more stable
        loss = model(batch).loss
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### Practical Configuration: Yield Prediction Model Distributed Training

**Scenario**: A fab trains a Transformer-based yield prediction model (500M parameters) with a 100GB dataset.

**Configuration**:

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

**Launch command**:

```bash
deepspeed --num_nodes=2 --num_gpus=8 \
  train_yield_model.py \
  --deepspeed_config deepspeed_config.yaml \
  --data_path /lustre/data/yield_2024q3 \
  --output_dir /lustre/checkpoints/yield_model_v3
```

**Performance tuning points**:

1. **Data loading**: Use WebDataset format, 8-process DataLoader, prefetch=4
2. **Communication optimization**: Enable NCCL_DEBUG=INFO to monitor communication bottlenecks, adjust NCCL_ALGO
3. **Checkpoint**: Save every epoch, asynchronously write to parallel file system
4. **Fault recovery**: Enable elastic checkpoint, automatic restart on node failure

### Training Monitoring and Debugging

**Key metrics**:

- **GPU utilization**: `nvidia-smi` or DCGM Exporter, target >80%
- **Communication overhead**: AllReduce time proportion, target <20%
- **IO wait**: DataLoader idle time, target <10%
- **Memory peak**: Avoid OOM, reserve 10% margin

**Toolchain**:

- **TensorBoard/W&B**: Training curves, hyperparameter tracking
- **Nsight Systems**: GPU kernel-level performance analysis
- **PyTorch Profiler**: Operator-level bottleneck identification

## 29.4 High-Performance Data Processing Pipeline

Wafer fab AI data sources are diverse (FDC time-series, defect images, structured tables). How to efficiently load, preprocess, and feed data to models is a key bottleneck for training performance.

### Data Format Selection

| Data Type | Recommended Format | Advantages | Disadvantages |
|-----------|-------------------|------------|---------------|
| Defect images | WebDataset (tar) | Sequential reading, high throughput | Does not support random access |
| FDC time-series | Parquet | Columnar storage, good compression | Requires preprocessing to sequences |
| Structured tables | Parquet/CSV | Universal, easy to read | Poor performance for large files |
| Mixed data | TFRecord | Supports multimodal | Difficult to debug |

### Efficient Data Loader Design

**Problem**: Default DataLoader performs poorly in large-scale small file scenarios (file open overhead, metadata queries).

**Solution**: WebDataset + multi-process prefetching

```python
import webdataset as wds

dataset = (
    wds.WebDataset("s3://bucket/defect_data/{0000..0999}.tar")
    .decode("pil")                    # Decode images
    .to_tuple("jpg", "json")          # Extract fields
    .map(preprocess)                  # Custom preprocessing
    .batched(64)                      # Batching
)

dataloader = wds.WebLoader(
    dataset,
    batch_size=None,                  # Already batched in dataset
    num_workers=8,                    # Multi-process loading
    prefetch=4                        # Prefetch batches
)
```

**Performance comparison** (defect detection training):

| Solution | Throughput (img/s) | GPU Utilization |
|----------|-------------------|-----------------|
| Default DataLoader + small files | 120 | 45% |
| WebDataset + 8 workers | 850 | 92% |

### Data Preprocessing Pipeline

Typical workflow:

```
Raw data → Cleaning → Feature extraction → Normalization → Augmentation → Batching
```

**Key optimizations**:

1. **Offline preprocessing**: Complete time-consuming operations (such as image cropping, time-series alignment) in advance and store as intermediate format
2. **GPU-accelerated preprocessing**: Use DALI (NVIDIA) or TorchVision transforms to migrate CPU operations to GPU
3. **Cache hot data**: Establish memory cache for frequently accessed samples (such as typical defect patterns)

```python
# DALI-accelerated image preprocessing
from nvidia.dali.pipeline import pipeline_def
import nvidia.dali.fn as fn

@pipeline_def(batch_size=64, num_threads=8, device_id=0)
def defect_pipeline():
    images, labels = fn.readers.file(
        file_root="/data/defect",
        random_shuffle=True
    )
    images = fn.decoders.image(images, device="mixed")  # GPU decoding
    images = fn.resize(images, resize_x=224, resize_y=224)
    images = fn.normalize(images, mean=[0.485, 0.456, 0.406], 
                         std=[0.229, 0.224, 0.225])
    return images, labels
```

### Sample Imbalance Handling

Wafer fab data generally exhibits class imbalance (defect samples are far fewer than normal samples).

**Strategies**:

1. **Oversample minority class**: SMOTE, data augmentation (rotation, flipping, noise)
2. **Undersample majority class**: Random discard, cluster center retention
3. **Class weights**: Assign higher weights to minority classes in the loss function

```python
# Class weight calculation
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(labels),
    y=labels
)

# Use in loss
criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights).cuda())
```

### Data Version Management

Version tracking of training data is the foundation of reproducibility.

**Tool**: DVC (Data Version Control)

```bash
# Initialize DVC
dvc init

# Track dataset
dvc add data/defect_dataset_v3/

# Commit to Git
git add data/defect_dataset_v3.dvc
git commit -m "Add defect dataset v3"

# Switch to historical version
dvc checkout data/defect_dataset_v3.dvc@v2
```

**Integration with MLflow**:

```python
import mlflow

with mlflow.start_run():
    mlflow.log_param("data_version", "defect_v3")
    mlflow.log_param("data_hash", dvc.api.get_url("data/defect_dataset_v3/"))
    # ... training logic
```

## 29.5 Model Serving and Inference Gateway

Trained models need to be deployed as highly available, low-latency inference services for production line systems to call.

### Inference Engine Selection

| Engine | Use Case | Advantages | Disadvantages |
|--------|----------|------------|---------------|
| TensorRT | NVIDIA GPU inference | Ultimate performance, INT8 quantization | NVIDIA only, slow compilation |
| Triton Inference Server | Multi-framework, multi-model | Supports dynamic batching, model management | Complex deployment |
| vLLM | LLM inference | PagedAttention, high throughput | LLM only |
| ONNX Runtime | Cross-platform | Universal, CPU/GPU support | Performance not as good as dedicated engines |
| TorchScript | PyTorch models | Native support, easy deployment | Average performance |

### Triton Inference Service Architecture

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
         │ Load balancing
         │
┌────────┴────────┐
│  API Gateway    │
│  (Kong/Nginx)   │
└─────────────────┘
```

**Model configuration example** (config.pbtxt):

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

### Dynamic Batching

Merge multiple requests into a single batch for processing to improve GPU utilization.

**Principle**:

- Requests enter a queue upon arrival, waiting for at most `max_queue_delay_microseconds`
- After accumulating to `preferred_batch_size` or timeout, merge into a batch and send to the model
- After inference completion, split results and return to each request

**Effect** (defect detection):

| Strategy | Throughput (img/s) | P99 Latency (ms) |
|----------|-------------------|------------------|
| Single request processing | 200 | 15 |
| Dynamic batching (max_delay=5ms) | 850 | 22 |

### Model Version Management and Canary Release

**Model repository structure**:

```
/models/defect_cnn/
├── config.pbtxt
├── 1/              # v1 (production)
│   └── model.plan
├── 2/              # v2 (canary 10%)
│   └── model.plan
└── 3/              # v3 (testing)
    └── model.plan
```

**Canary release strategy**:

```python
# Implement canary through Triton model routing
# 90% traffic goes to v1, 10% traffic goes to v2

import random

def route_model():
    if random.random() < 0.1:
        return "defect_cnn_v2"
    return "defect_cnn_v1"
```

**Rollback mechanism**:

```bash
# Unload problematic version
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/2/unload

# Load stable version
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/1/load
```

### Inference Service High Availability

**Multi-replica deployment**:

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

**Load balancing**:

```nginx
# nginx configuration
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

### Monitoring and Alerting

**Key metrics**:

- **Inference latency**: P50/P95/P99, alert threshold >50ms
- **Throughput**: QPS, alert threshold <80% of target
- **GPU utilization**: Target >70%, alert <50%
- **Error rate**: Target <0.1%, alert >1%
- **Queue depth**: Dynamic batch queue length, alert >100

**Prometheus + Grafana monitoring stack**:

```python
# Triton metrics export
# Exposes Prometheus format metrics at /metrics endpoint by default

# Custom business metrics
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

## 29.6 Edge Deployment and Real-Time Inference

Edge inference is the "last mile" of wafer fab AI, directly serving production line real-time control.

### Edge Scenario Classification

| Scenario | Latency Requirement | Computing Demand | Deployment Location |
|----------|---------------------|------------------|---------------------|
| Endpoint detection | <2ms | <10 TOPS | Embedded in tool |
| Local quality inspection | <20ms | <50 TOPS | Line-side industrial PC |
| Safety interlock | <1ms | <5 TOPS | PLC/Safety controller |
| Data preprocessing | <10ms | <20 TOPS | Edge gateway |

### Edge Hardware Selection

**NVIDIA Jetson series**:

| Model | Performance (INT8) | Memory | Power Consumption | Price |
|-------|-------------------|--------|-------------------|-------|
| Jetson Nano | 472 GFLOPS | 4GB | 5-10W | $99 |
| Jetson Xavier NX | 21 TOPS | 8GB | 10-15W | $399 |
| Jetson AGX Orin | 275 TOPS | 64GB | 15-60W | $1,999 |

**Recommendations**:

- **Lightweight tasks** (endpoint detection): Jetson Xavier NX, best cost-effectiveness
- **Complex tasks** (multi-model inference): Jetson AGX Orin, sufficient computing power
- **Ultra-low latency** (safety interlock): FPGA or dedicated ASIC

### Model Compression and Optimization

**Quantization**:

Convert FP32 models to INT8, increasing computing power 2-4x with <1% accuracy loss.

```python
# TensorRT quantization
import tensorrt as trt

logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
parser = trt.OnnxParser(network, logger)

with open("model.onnx", "rb") as f:
    parser.parse(f.read())

# INT8 quantization configuration
config = builder.create_builder_config()
config.set_flag(trt.BuilderFlag.INT8)
config.int8_calibrator = MyCalibrator(calibration_data)

engine = builder.build_engine(network, config)
with open("model_int8.engine", "wb") as f:
    f.write(engine.serialize())
```

**Pruning**:

Remove unimportant weights or channels to reduce computation.

```python
# Structured pruning (channel-level)
from torch.nn.utils import prune

for name, module in model.named_modules():
    if isinstance(module, nn.Conv2d):
        prune.ln_structured(module, name='weight', amount=0.3, dim=0, n=2)
        prune.remove(module, 'weight')
```

**Knowledge distillation**:

Use a large model (teacher) to guide small model (student) training.

```python
# Distillation loss
def distillation_loss(student_logits, teacher_logits, temperature=4.0):
    student_log_softmax = F.log_softmax(student_logits / temperature, dim=1)
    teacher_softmax = F.softmax(teacher_logits / temperature, dim=1)
    return F.kl_div(student_log_softmax, teacher_softmax, reduction='batchmean')
```

### Edge Inference Framework

**TensorRT**:

NVIDIA GPU-dedicated inference engine with optimal performance.

```python
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

# Load engine
with open("model.engine", "rb") as f:
    runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
    engine = runtime.deserialize_cuda_engine(f.read())

# Inference
context = engine.create_execution_context()
input_host = np.random.randn(1, 3, 224, 224).astype(np.float32)
output_host = np.empty((1, 1000), dtype=np.float32)

# Allocate GPU memory
input_device = cuda.mem_alloc(input_host.nbytes)
output_device = cuda.mem_alloc(output_host.nbytes)

# Copy data
cuda.memcpy_htod(input_device, input_host)
context.execute(1, [int(input_device), int(output_device)])
cuda.memcpy_dtoh(output_host, output_device)
```

**ONNX Runtime**:

Cross-platform inference engine supporting CPU/GPU/NPU.

```python
import onnxruntime as ort

session = ort.InferenceSession("model.onnx")
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

result = session.run([output_name], {input_name: input_data})
```

### Offline Disaster Recovery Design

Edge nodes must operate independently when the network is interrupted.

**Strategies**:

1. **Local model caching**: Edge nodes store the latest model version, periodically synchronizing from the center
2. **Local data storage**: Inference results stored locally first, uploaded after network recovery
3. **Degradation mode**: Switch to rule engine or default values when model is abnormal

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
            # Model abnormal, degrade to rule engine
            return self.fallback.predict(input_data)
    
    def sync_to_cloud(self):
        if self.is_network_available():
            self.local_buffer.upload_pending()
```

### Practical Case: Etching Endpoint Detection Edge Deployment

**Background**: A fab's etching tools require real-time endpoint detection. The original solution relied on cloud inference with latency >100ms, causing over-etching.

**Solution**:

- Deploy Jetson AGX Orin next to the tool
- Model compression: FP32→INT8 quantization, inference time from 15ms→3ms
- Offline disaster recovery: Local storage of models from the last 7 days, independent operation during network interruption

**Results**:

- End-to-end latency from 100ms→8ms (including data collection)
- Over-etching rate from 2.3%→0.4%
- Annual wafer scrap cost savings >$500k

## 29.7 Computing Scheduling and Resource Isolation

Wafer fab AI computing power needs to serve multiple teams (process, equipment, yield) and multiple tasks (training, inference, experiments). How to allocate resources fairly and efficiently is a key challenge.

### Scheduling Strategy

**Priority queue**:

```
Priority 1: Production line inference services (non-interruptible)
Priority 2: Emergency training tasks (such as yield anomaly investigation)
Priority 3: Regular training tasks
Priority 4: Development experiments
```

**Resource quota**:

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

**Time-slice rotation**:

Prioritize inference services during the day, release GPUs for training tasks at night.

```python
# Time-based scheduling strategy
from datetime import datetime

def get_priority():
    hour = datetime.now().hour
    if 8 <= hour < 20:  # Daytime
        return "inference"
    else:  # Nighttime
        return "training"
```

### Multi-Tenant Isolation

**Namespace isolation**:

```yaml
# Each team has an independent namespace
apiVersion: v1
kind: Namespace
metadata:
  name: yield-team
  labels:
    team: yield
    cost-center: CC1234
```

**GPU partitioning (MIG)**:

A100 supports MIG (Multi-Instance GPU), partitioning a single card into up to 7 instances.

```bash
# Enable MIG
nvidia-smi -i 0 -mig 1

# Create GPU instance (1g.10gb = 1/7 A100)
nvidia-smi mig -cgi 1g.10gb -C
```

**Network isolation**:

```yaml
# NetworkPolicy restricts cross-namespace access
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

### Elastic Scaling

**Load-based auto-scaling**:

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

**Time-based scheduled scaling**:

```yaml
# Scale up training cluster at night
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
  - schedule: "0 22 * * *"  # Every night at 22:00
    replicas: 8
  - schedule: "0 8 * * *"   # Every morning at 8:00
    replicas: 2
```

### Job Scheduling System

**Slurm**:

Traditional HPC job scheduler, suitable for batch training tasks.

```bash
# Submit training job
sbatch --gres=gpu:8 --time=24:00:00 train_yield.sh

# View job status
squeue

# Cancel job
scancel <job_id>
```

**Volcano**:

Kubernetes-native batch scheduler supporting Gang Scheduling.

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

### Practical Case: Multi-Team Computing Sharing Platform

**Background**: Three AI teams (yield, defect, equipment) in a fab share a 16-A100 cluster with severe resource contention.

**Solution**:

- Kubernetes + Volcano scheduling
- Each team has an independent namespace with a quota of 8 GPUs
- Inference services have the highest priority, training tasks queue
- Automatically scale up training cluster at night

**Results**:

- Resource contention complaints reduced by 90%
- GPU utilization increased from 55% to 78%
- Training task wait time from 3 days→4 hours

## 29.8 Computing Cost Modeling and TCO Analysis

AI computing investment is huge, requiring refined cost modeling and ROI analysis.

### TCO Composition

**Hardware costs**:

- GPU servers: $10k-50k/node
- Network equipment: InfiniBand switches $5k-10k/port
- Storage systems: All-flash NAS $50k-200k
- Racks, power, cooling: $5k-10k/year/rack

**Software costs**:

- GPU drivers, CUDA: Free
- Container platform (K8s): Free
- MLOps platform (Kubeflow): Free
- Commercial software (such as Weights & Biases): $50-200/user/month

**Labor costs**:

- AI platform engineer: $150k-250k/year
- MLOps engineer: $120k-200k/year
- GPU operations engineer: $100k-150k/year

**Power costs**:

- Single A100 card power consumption: 300W
- 8-card node power consumption: ~3kW
- Electricity cost: $0.1/kWh → $2,600/year/node

### TCO Comparison: Self-Built vs Cloud vs Hybrid

**Scenario**: 16-A100 cluster, 5-year TCO

| Solution | Hardware | Power | Labor | Cloud Cost | 5-Year TCO |
|----------|----------|-------|-------|------------|------------|
| Self-built | $400k | $50k | $500k | - | $950k |
| Pure cloud (AWS) | - | - | $200k | $1.2M | $1.4M |
| Hybrid (8-card self-built + 8-card cloud) | $200k | $25k | $350k | $600k | $1.175M |

**Conclusion**:

- **Long-term stable load**: Self-built is more economical (TCO 30-40% lower)
- **Volatile load**: Cloud is more flexible (pay-as-you-go)
- **Hybrid solution**: Balances cost and elasticity

### ROI Calculation Framework

**Benefits**:

- Yield improvement: Every 1% improvement → $10M-50M/year (depending on capacity and product value)
- Efficiency improvement: Training time reduction → Engineer productivity improvement
- Cost savings: Automation replacing manual labor → Labor cost savings

**Costs**:

- Computing investment: Hardware + software + labor
- O&M costs: Power + maintenance + upgrades

**ROI formula**:

```
ROI = (Annualized benefits - Annualized costs) / Annualized costs × 100%
```

**Case**:

- Investment: $200k (computing) + $100k/year (O&M) = $300k/year
- Benefits: Yield improvement 0.5% → $25M/year
- ROI = ($25M - $0.3M) / $0.3M × 100% = 8233%

### Cost Optimization Strategies

**GPU utilization improvement**:

- Dynamic batching: Improve inference throughput
- Model quantization: Reduce memory usage
- Multi-task sharing: Same GPU serving multiple models
- MIG partitioning: A100 partitioned into multiple instances
- Time-slice rotation: Inference during the day, training at night

**Cloud cost optimization**:

- Reserved instances: 1-year/3-year reservation, 30-60% discount
- Spot instances: For non-critical tasks, 60-90% discount
- Auto-scaling: Scale down at night to avoid idleness

**Power optimization**:

- Liquid cooling: PUE from 1.5→1.2, 20% power savings
- Intelligent scheduling: Train during off-peak electricity price periods at night
- Waste heat recovery: Used for office heating

### Practical Case: Computing Investment ROI Analysis

**Background**: A fab invested $500k to build an AI training cluster and needs to evaluate ROI.

**Costs**:

- Hardware: $500k (one-time)
- O&M: $50k/year (labor + power)
- 5-year TCO: $750k

**Benefits**:

- Yield improvement 0.3%: $15M/year
- Training efficiency improvement 50%: Engineer time savings $100k/year
- Annualized benefits: $15.1M

**ROI**:

- Annualized cost: $150k ($750k/5 years)
- ROI = ($15.1M - $0.15M) / $0.15M × 100% = 9967%
- Payback period: <1 month

## 29.9 Infrastructure Monitoring and Self-Healing

GPU cluster stability directly affects AI task continuity, requiring comprehensive monitoring and self-healing mechanisms.

### Monitoring Metrics System

**Hardware layer**:

- GPU temperature, power consumption, fan speed
- Memory ECC error count
- NVLink/PCIe bandwidth and error rate
- CPU/memory/disk usage

**Software layer**:

- GPU utilization, memory usage
- Training task progress, loss curves
- Inference service latency, throughput, error rate
- Network bandwidth, latency, packet loss rate

**Business layer**:

- Model accuracy, drift metrics
- Data pipeline latency, failure rate
- SLA achievement rate

### DCGM Exporter + Prometheus

NVIDIA DCGM (Data Center GPU Manager) provides GPU monitoring APIs.

```bash
# Deploy DCGM Exporter
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/dcgm-exporter/main/deployment/dcgm-exporter.yaml

# Prometheus configuration
scrape_configs:
  - job_name: 'dcgm'
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

**Key metrics**:

```
DCGM_FI_DEV_GPU_TEMP          # GPU temperature
DCGM_FI_DEV_POWER_USAGE       # Power consumption
DCGM_FI_DEV_FB_FREE           # Memory free
DCGM_FI_DEV_GPU_UTIL          # GPU utilization
DCGM_FI_DEV_ECC_DBE_VOL_TOTAL # Double-bit ECC errors (critical)
```

### Alert Rules

```yaml
# Prometheus alert rules
groups:
  - name: gpu_alerts
    rules:
    - alert: GPUTemperatureHigh
      expr: DCGM_FI_DEV_GPU_TEMP > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "GPU temperature too high: {{ $labels.gpu }}"
    
    - alert: GPUECCError
      expr: increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[5m]) > 0
      labels:
        severity: critical
      annotations:
        summary: "GPU ECC error occurred: {{ $labels.gpu }}"
    
    - alert: InferenceLatencyHigh
      expr: histogram_quantile(0.99, inference_latency_seconds) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Inference latency P99 >50ms"
```

### Self-Healing Mechanisms

**GPU fault automatic isolation**:

```python
import subprocess
import time

def check_gpu_health(gpu_id):
    """Check GPU health status"""
    result = subprocess.run(
        ["nvidia-smi", "-i", str(gpu_id), "--query-gpu=ecc.errors.uncorrected.volatile.total", "--format=csv,noheader"],
        capture_output=True, text=True
    )
    ecc_errors = int(result.stdout.strip())
    return ecc_errors == 0

def isolate_faulty_gpu(gpu_id):
    """Isolate faulty GPU"""
    # Remove from scheduling pool
    subprocess.run(["nvidia-smi", "-i", str(gpu_id), "-mig", "0"])
    # Send alert
    send_alert(f"GPU {gpu_id} has been isolated, ECC errors exist")
    # Log event
    log_event(f"GPU {gpu_id} isolated due to ECC errors")

# Periodic check
while True:
    for gpu_id in range(8):
        if not check_gpu_health(gpu_id):
            isolate_faulty_gpu(gpu_id)
    time.sleep(60)
```

**Training task fault tolerance**:

```python
# PyTorch Elastic (automatic recovery)
import torch.distributed.elastic as etcd

# Configure checkpoint
def save_checkpoint(model, optimizer, epoch, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

# Fault recovery
def load_checkpoint(path):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return checkpoint['epoch']

# Elastic training
etcd.run(
    train_func,
    min_nodes=2,
    max_nodes=4,
    rdzv_backend="etcd",
    rdzv_endpoint="etcd:2379"
)
```

**Inference service degradation**:

```python
class InferenceService:
    def __init__(self):
        self.primary_model = load_model("primary")
        self.fallback_model = load_model("fallback")  # Lightweight model
        self.rule_engine = RuleEngine()
    
    def predict(self, input_data):
        try:
            # Try primary model
            return self.primary_model.predict(input_data)
        except ModelError:
            try:
                # Degrade to lightweight model
                return self.fallback_model.predict(input_data)
            except ModelError:
                # Degrade to rule engine
                return self.rule_engine.predict(input_data)
```

### Practical Case: GPU Cluster Self-Healing System

**Background**: A fab's 16-A100 cluster experiences 2-3 GPU failures monthly, causing training task interruptions.

**Solution**:

- DCGM Exporter + Prometheus monitoring
- ECC error automatic detection and GPU isolation
- Training task Elastic Checkpoint, automatic fault recovery
- Multi-level inference service degradation

**Results**:

- Training task interruption time from 8 hours/month→30 minutes/month
- Inference service availability from 99.5%→99.99%
- O&M labor savings 50%

## 29.10 Computing Infrastructure Acceptance Benchmarks and Stress Testing

After building or upgrading computing infrastructure, strict acceptance testing is needed to ensure production requirements are met.

### Acceptance Dimensions

**Performance benchmarks**:

- Training throughput: tokens/s (LLM), images/s (CV)
- Inference latency: P50/P95/P99
- Network bandwidth: AllReduce throughput, latency
- Storage IO: Sequential/random read/write bandwidth

**Stability benchmarks**:

- Long-term operation: 72-hour continuous training without failure
- Fault recovery: Automatic recovery time after node failure <10 minutes
- Memory leak: Memory/memory usage stable

**Functional benchmarks**:

- Multi-tenant isolation: Resource quotas, network isolation
- Elastic scaling: Auto-scaling response time <2 minutes
- Monitoring alerts: Metric collection completeness >99%

### Training Performance Stress Testing

**MLPerf Training**:

Industry-standard training benchmark covering ResNet, BERT, GPT and other models.

```bash
# Run MLPerf Training
cd mlperf/training
make run MODEL=bert DATA_DIR=/data/bpho

# Result interpretation
# BERT training time: <3.5 hours (8×A100) is qualified
```

**Custom benchmarks**:

```python
# Wafer fab typical model training benchmark
import time
import torch

def benchmark_training(model, dataloader, epochs=3):
    """Training performance benchmark test"""
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

# Benchmark requirements
# Yield prediction model (ResNet-50): >500 images/s (8×A100)
# Defect detection model (ResNet-101): >300 images/s (8×A100)
```

### Inference Performance Stress Testing

**Tool**: Triton Perf Analyzer

```bash
# Inference performance test
perf_analyzer -m defect_cnn -b 32 --service-triton triton:8001

# Result interpretation
# Throughput: >1000 inferencing/s (single A100 card)
# P99 latency: <30ms
```

**Concurrency testing**:

```python
import asyncio
import aiohttp

async def inference_request(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def benchmark_concurrent(url, data, concurrency=100):
    """Concurrent inference stress test"""
    async with aiohttp.ClientSession() as session:
        tasks = [inference_request(session, url, data) for _ in range(concurrency)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"Throughput: {concurrency / elapsed:.2f} req/s")
        print(f"P99 Latency: {sorted([r['latency'] for r in results])[int(concurrency*0.99)]:.2f}ms")
```

### Stability Stress Testing

**72-hour continuous training**:

```bash
# Start long-term training task
nohup python train_yield_model.py --epochs 100 > train.log 2>&1 &

# Monitoring script
while true; do
    # Check GPU status
    nvidia-smi --query-gpu=temperature,memory.used,utilization.gpu --format=csv >> gpu_monitor.log
    
    # Check training progress
    tail -n 1 train.log >> progress.log
    
    sleep 60
done
```

**Fault injection testing**:

```bash
# Simulate GPU failure
nvidia-smi -i 0 --gpu-lock=1  # Lock GPU

# Verify training task automatic recovery
# Expected: Task automatically migrates to other nodes within 10 minutes and continues training
```

### Acceptance Checklist

**Hardware acceptance**:

- [ ] GPU model and quantity match design
- [ ] Network bandwidth meets design metrics (InfiniBand 200Gb/s)
- [ ] Storage IO meets training requirements (>10GB/s)
- [ ] Power and cooling meet full-load operation

**Software acceptance**:

- [ ] GPU driver and CUDA versions correct
- [ ] Container platform (K8s) deployed successfully
- [ ] Scheduling system (Slurm/Volcano) configured
- [ ] Monitoring alert system online

**Performance acceptance**:

- [ ] Training throughput meets benchmark requirements
- [ ] Inference latency meets SLA
- [ ] 72-hour stability test passed
- [ ] Fault recovery time <10 minutes

**Functional acceptance**:

- [ ] Multi-tenant isolation effective
- [ ] Elastic scaling works normally
- [ ] Monitoring metrics collection complete
- [ ] Alert rules trigger correctly

### Practical Case: Computing Infrastructure Acceptance

**Background**: A fab built a new 16-A100 cluster and needs to go online after acceptance.

**Acceptance process**:

1. **Hardware check**: GPU model, network bandwidth, storage IO all meet standards
2. **Performance stress testing**:
   - MLPerf BERT training: 3.2 hours (requirement <3.5 hours) ✓
   - Inference throughput: 1200 inferencing/s (requirement >1000) ✓
   - P99 latency: 25ms (requirement <30ms) ✓
3. **Stability testing**: 72-hour continuous training without failure ✓
4. **Fault injection**: Simulate GPU failure, task recovers within 8 minutes ✓

**Result**: Acceptance passed, officially online.

---

## Chapter Summary

This chapter systematically introduced the design and implementation of wafer fab AI computing infrastructure, covering the complete architecture from GPU clusters to edge inference nodes. Key points:

1. **Three-type load differentiated design**: Training (high throughput), inference (low latency), and edge (real-time) require different hardware and architecture solutions
2. **Cluster selection key points**: GPU model, network topology, and storage architecture directly affect training performance and cost
3. **Distributed training engineering**: DDP/FSDP/ZeRO strategy selection, mixed precision, and data pipeline optimization are key to training efficiency
4. **Inference serving**: Triton + dynamic batching + canary release builds highly available inference services
5. **Edge deployment**: Model compression + TensorRT optimization + offline disaster recovery achieves production line real-time inference
6. **Resource scheduling**: Multi-tenant isolation, priority queues, and elastic scaling ensure fair and efficient resource utilization
7. **Cost and TCO**: Self-built vs cloud vs hybrid solutions require refined ROI analysis
8. **Monitoring and self-healing**: DCGM + Prometheus + automatic fault isolation ensures cluster stability
9. **Acceptance benchmarks**: Strict acceptance across performance, stability, and functionality dimensions ensures production readiness

Computing infrastructure is the physical foundation of AI engineering. The next chapter will build AI platforms on this foundation, providing toolchains and developer experiences for model development, deployment, and operations.
