# 第29章 晶圓廠AI算力底座——從GPU集群到邊緣推理節點

> **本章導讀**
> 
> 前28章構建了從資料治理到AI演算法的完整體系，但所有AI系統最終都要落地到實體基礎設施。本章聚焦晶圓廠AI的算力底座：如何設計GPU集群支撐大規模訓練？如何部署低延遲推理服務？如何在邊緣節點實現即時控制？我們將從算力需求分析出發，系統講解集群架構、分散式訓練、模型服務化、邊緣部署、資源排程、成本優化、監控運維和驗收基準，給出可直接落地的工程方案。

## 29.1 晶圓廠AI算力需求全景

晶圓廠的AI應用呈現明顯的「三峰」特徵：訓練峰值、推理穩態、邊緣即時。三類負載對算力的需求差異巨大，不能用一套架構簡單覆蓋。

### 訓練負載：間歇性、高吞吐、長週期

訓練類任務集中在良率預測模型、缺陷檢測CNN、大語言模型微調等場景。其特點是：

- **資料規模大**：單批次晶圓涉及數千片，每片包含數百個工藝步驟的FDC時序資料、缺陷圖像、量測結果，訓練集動輒TB級
- **計算密集**：ResNet-50訓練需要數十GPU·小時，LLM微調（如第27章實驗27.8的LoRA訓練）需要多卡並行
- **週期性執行**：新模型開發、季度重訓練、工藝節點遷移時的全量訓練，呈現「脈衝式」算力消耗
- **容錯要求高**：訓練任務可中斷恢復，但對單步迭代時間敏感（影響實驗效率）

**典型場景**：某3nm晶圓廠每季度進行良率模型全量重訓練，使用128片A100 GPU集群，單次訓練耗時約72小時，期間GPU利用率需保持在85%以上以確保投資回報。

### 推理負載：持續性、低延遲、高並發

推理類任務覆蓋R2R控制、線上缺陷檢測、虛擬量測等產線核心環節。其特點是：

- **7×24不間斷**：產線不停，推理服務不停
- **延遲敏感**：R2R控制要求端到端延遲<50ms，缺陷檢測要求單幀推理<20ms
- **並發量大**：單廠數百台設備同時推理，峰值QPS可達數千
- **可用性要求極高**：推理服務宕機=產線停擺，SLA要求99.99%以上

**典型場景**：某廠的FDC即時異常檢測系統，接入500台設備的感測器流，每秒處理10萬條時序記錄，推理延遲P99<30ms，年可用性>99.99%。

### 邊緣負載：超低延遲、離線容災、資源受限

邊緣類任務部署在設備側或線邊，覆蓋即時工藝控制、本地質檢、安全聯鎖等。其特點是：

- **極致延遲**：某些工藝控制環路要求<5ms響應
- **離線能力**：網路中斷時必須能獨立運行（產線不能等雲端）
- **資源受限**：邊緣設備算力有限（通常<100 TOPS），需模型壓縮
- **環境苛刻**：無塵室温度的限制

**典型場景**：蝕刻機台的終點檢測（Endpoint Detection），基於電漿光譜即時判斷蝕刻完成時刻，要求延遲<2ms，部署在機台旁的工控機上。

### 算力需求矩陣

| 負載類型 | 典型場景 | 算力規模 | 延遲要求 | 可用性 | 部署位置 |
|---------|---------|---------|---------|--------|---------|
| 訓練 | 良率模型重訓練 | 數十~數百GPU | 分鐘~小時級 | 99% | 中心機房/雲 |
| 推理 | R2R控制、缺陷檢測 | 數~數十GPU | <50ms | 99.99% | 中心機房 |
| 邊緣 | 終點檢測、本地質檢 | <1 GPU | <5ms | 99.999% | 設備側/線邊 |

理解這三類負載的差異，是設計算力架構的前提。下一章將針對這些需求，設計GPU集群、推理服務、邊緣節點的三層架構。

## 29.2 GPU集群架構設計與選型

晶圓廠AI訓練集群的設計，需要在效能、成本、可擴展性之間找到平衡。與網際網路大廠不同，晶圓廠通常不需要萬卡集群，但對穩定性、資料安全、與產線系統的整合有更高要求。

### GPU選型：A100/H100 vs L40S vs 邊緣GPU

| GPU型號 | 記憶體 | FP16算力 | 適用場景 | 單卡價格(參考) |
|---------|------|---------|---------|---------------|
| A100 80GB | 80GB HBM2e | 312 TFLOPS | 大模型訓練、大規模並行 | $10k-15k |
| H100 80GB | 80GB HBM3 | 989 TFLOPS | 超大模型、混合精度訓練 | $25k-40k |
| L40S 48GB | 48GB GDDR6 | 362 TFLOPS | 中等規模訓練、推理 | $8k-12k |
| T4 16GB | 16GB GDDR6 | 65 TFLOPS | 推理、輕量微調 | $2k-3k |
| Jetson AGX Orin | 64GB LPDDR5 | 275 TOPS(INT8) | 邊緣推理 | $1.5k-2k |

**選型建議**：

- **訓練集群**：A100/H100為主力，80GB記憶體可容納大batch和長序列
- **推理集群**：L40S/T4性價比高，支援多實例GPU(MIG)切分
- **邊緣節點**：Jetson系列功耗低、算力足，支援TensorRT優化

### 集群拓撲：單機8卡 vs 多機多卡

**單機8卡方案**（適合中小廠）：

```
┌─────────────────────────────────────┐
│  GPU Node (8×A100 80GB)             │
│  ├─ NVLink全互聯 (600GB/s)          │
│  ├─ 2× AMD EPYC 7763 (128C)        │
│  ├─ 2TB DDR4 RAM                    │
│  └─ 8× NVMe 3.84TB (RAID0)         │
└─────────────────────────────────────┘
         │
         │ PCIe Gen4 x16
         │
┌────────┴────────┐
│  100GbE/IB網路   │
└─────────────────┘
```

**優點**：NVLink提供卡間高速通訊，適合單機內的資料並行；部署簡單，運維成本低。

**缺點**：單機算力上限約2.5 PFLOPS(FP16)，難以支撐超大模型。

**多機多卡方案**（適合先進製程大廠）：

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

**關鍵組件**：

- **網路**：InfiniBand HDR(200Gb/s)或RoCE v2(100GbE)，卡間通訊延遲<1μs
- **儲存**：並行檔案系統(Lustre/GPFS)或全快閃記憶體NAS，提供>10GB/s聚合頻寬
- **排程**：Slurm或Kubernetes+GPU Operator，支援作業排隊與資源隔離

### 網路選型：InfiniBand vs RoCE

| 特性 | InfiniBand HDR | RoCE v2 (100GbE) |
|------|---------------|------------------|
| 頻寬 | 200 Gb/s | 100 Gb/s |
| 延遲 | <1 μs | 2-5 μs |
| 擁塞控制 | 硬體級，無損 | 需DCQCN等演算法調優 |
| 成本 | 高（交換器$5k-10k/埠） | 低（複用乙太網路） |
| 生態 | NVIDIA主導 | 開放標準 |

**建議**：

- **預算充足、追求極致效能**：InfiniBand，適合大模型訓練
- **成本敏感、已有乙太網路基礎**：RoCE v2，適合中小規模訓練與推理

### 儲存架構：訓練資料的IO瓶頸

訓練任務的IO模式：大量小檔案讀取（圖像）、順序讀取（時序資料）、隨機存取（樣本取樣）。

**推薦架構**：

```
┌──────────────────────────────────────┐
│  熱資料層 (NVMe SSD)                  │
│  ├─ 當前訓練集 (RAID0, >10GB/s)       │
│  └─ 模型checkpoint                   │
└──────────────────────────────────────┘
              │
              │ 自動分層
              │
┌──────────────────────────────────────┐
│  溫資料層 (SATA SSD/HDD)              │
│  ├─ 歷史訓練集                        │
│  └─ 驗證集                           │
└──────────────────────────────────────┘
              │
              │ 歸檔
              │
┌──────────────────────────────────────┐
│  冷資料層 (物件儲存/磁帶)              │
│  └─ 原始資料備份                     │
└──────────────────────────────────────┘
```

**關鍵優化**：

- **預取與快取**：訓練前將資料集載入到記憶體或NVMe快取，避免運行時IO等待
- **資料格式**：使用TFRecord、WebDataset等列式格式，減少小檔案開銷
- **並行載入**：多行程DataLoader + prefetch，掩蓋IO延遲

### 實戰案例：某3nm晶圓廠訓練集群建設

**背景**：該廠每月需重訓練20+個良率/缺陷模型，原有4卡A100集群成為瓶頸，單次訓練耗時>1週。

**方案**：

- 建設16卡A100集群（2節點×8卡），InfiniBand互聯
- 部署Lustre並行檔案系統，聚合頻寬15GB/s
- 引入Slurm作業排程，支援多租戶排隊

**效果**：

- 訓練時間縮短70%（從7天→2天）
- GPU利用率從45%提升至82%
- 支援3個團隊並行訓練，互不干擾

**投資**：約$500k（含GPU、網路、儲存、機櫃），ROI<18個月。

## 29.3 分散式訓練工程實踐

當單卡記憶體不足以容納模型或batch時，分散式訓練成為必選項。晶圓廠場景常見的分散式策略包括資料並行、模型並行、混合精度訓練。

### 資料並行：DDP vs FSDP vs ZeRO

**DDP (Distributed Data Parallel)**：

- 每張卡持有完整模型副本，資料分片
- 梯度透過AllReduce同步
- 適合模型可放入單卡的場景

```python
# PyTorch DDP範例
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

- 模型參數、梯度、最佳化器狀態全部分片
- 按需拉取參數，計算後丟棄
- 適合大模型（如LLM微調）

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(
    MyLargeModel(),
    sharding_strategy=FULL_SHARD,
    cpu_offload=CPUOffload(offload_params=True),  # 可選CPU卸載
)
```

**ZeRO (Zero Redundancy Optimizer)**：

- DeepSpeed庫實現，分ZeRO-1/2/3三個階段
- ZeRO-3等價於FSDP，參數/梯度/最佳化器全分片
- 支援超大模型（>10B參數）

### 模型並行：Tensor Parallel vs Pipeline Parallel

當模型過大無法放入單卡時，需要模型並行：

**Tensor Parallel (TP)**：

- 將單層參數（如Attention矩陣）切分到多卡
- 卡間通訊頻繁，需高速互聯（NVLink）
- 適合Transformer類模型

**Pipeline Parallel (PP)**：

- 將模型按層切分，形成流水線
- 卡間通訊較少，但存在氣泡(bubble)
- 適合深層模型（如ResNet-152）

### 混合精度訓練

使用FP16/BF16進行前向/反向計算，FP32保持主權重，可節省50%記憶體並加速2-3倍。

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    with autocast(dtype=torch.bfloat16):  # BF16更穩定
        loss = model(batch).loss
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 實戰配置：良率預測模型分散式訓練

**場景**：某廠訓練基於Transformer的良率預測模型（500M參數），資料集100GB。

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

**啟動命令**：

```bash
deepspeed --num_nodes=2 --num_gpus=8 \
  train_yield_model.py \
  --deepspeed_config deepspeed_config.yaml \
  --data_path /lustre/data/yield_2024q3 \
  --output_dir /lustre/checkpoints/yield_model_v3
```

**效能調優要點**：

1. **資料載入**：使用WebDataset格式，8行程DataLoader，prefetch=4
2. **通訊優化**：啟用NCCL_DEBUG=INFO監控通訊瓶頸，調整NCCL_ALGO
3. **Checkpoint**：每epoch儲存，異步寫入並行檔案系統
4. **故障恢復**：啟用elastic checkpoint，節點故障自動重啟

### 訓練監控與除錯

**關鍵指標**：

- **GPU利用率**：`nvidia-smi`或DCGM Exporter，目標>80%
- **通訊開銷**：AllReduce時間佔比，目標<20%
- **IO等待**：DataLoader空閒時間，目標<10%
- **記憶體峰值**：避免OOM，預留10%餘量

**工具鏈**：

- **TensorBoard/W&B**：訓練曲線、超參追蹤
- **Nsight Systems**：GPU kernel級效能分析
- **PyTorch Profiler**：算子級瓶頸定位

## 29.4 高效能資料處理Pipeline

晶圓廠AI的資料來源多樣（FDC時序、缺陷圖像、結構化表格），如何高效載入、預處理、餵給模型，是訓練效能的關鍵瓶頸。

### 資料格式選擇

| 資料類型 | 推薦格式 | 優點 | 缺點 |
|---------|---------|------|------|
| 缺陷圖像 | WebDataset (tar) | 順序讀取、高吞吐 | 不支援隨機存取 |
| FDC時序 | Parquet | 列式儲存、壓縮好 | 需預處理為序列 |
| 結構化表格 | Parquet/CSV | 通用、易讀 | 大檔案效能差 |
| 混合資料 | TFRecord | 支援多模態 | 除錯困難 |

### 高效資料載入器設計

**問題**：預設DataLoader在大量小檔案場景下效能差（檔案開啟開銷、中繼資料查詢）。

**解決方案**：WebDataset + 多行程預取

```python
import webdataset as wds

dataset = (
    wds.WebDataset("s3://bucket/defect_data/{0000..0999}.tar")
    .decode("pil")                    # 解碼圖像
    .to_tuple("jpg", "json")          # 提取欄位
    .map(preprocess)                  # 自訂預處理
    .batched(64)                      # 批處理
)

dataloader = wds.WebLoader(
    dataset,
    batch_size=None,                  # 已在dataset中batch
    num_workers=8,                    # 多行程載入
    prefetch=4                        # 預取batch
)
```

**效能對比**（缺陷檢測訓練）：

| 方案 | 吞吐量(img/s) | GPU利用率 |
|------|--------------|----------|
| 預設DataLoader + 小檔案 | 120 | 45% |
| WebDataset + 8 workers | 850 | 92% |

### 資料預處理Pipeline

典型流程：

```
原始資料 → 清洗 → 特徵提取 → 正規化 → 增強 → 批處理
```

**關鍵優化**：

1. **離線預處理**：將耗時操作（如圖像裁剪、時序對齊）提前完成，儲存為中間格式
2. **GPU加速預處理**：使用DALI(NVIDIA)或TorchVision transforms，將CPU操作遷移到GPU
3. **快取熱點資料**：對頻繁存取的樣本（如典型缺陷模式）建立記憶體快取

```python
# DALI加速圖像預處理
from nvidia.dali.pipeline import pipeline_def
import nvidia.dali.fn as fn

@pipeline_def(batch_size=64, num_threads=8, device_id=0)
def defect_pipeline():
    images, labels = fn.readers.file(
        file_root="/data/defect",
        random_shuffle=True
    )
    images = fn.decoders.image(images, device="mixed")  # GPU解碼
    images = fn.resize(images, resize_x=224, resize_y=224)
    images = fn.normalize(images, mean=[0.485, 0.456, 0.406], 
                         std=[0.229, 0.224, 0.225])
    return images, labels
```

### 樣本不均衡處理

晶圓廠資料普遍存在類別不均衡（如缺陷樣本遠少於正常樣本）。

**策略**：

1. **過採樣少數類**：SMOTE、資料增強（旋轉、翻轉、雜訊）
2. **欠採樣多數類**：隨機丟棄、聚类中心保留
3. **類別權重**：在loss函數中為少數類賦予更高權重

```python
# 類別權重計算
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(labels),
    y=labels
)

# 在loss中使用
criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights).cuda())
```

### 資料版本管理

訓練資料的版本追蹤是可複現性的基礎。

**工具**：DVC (Data Version Control)

```bash
# 初始化DVC
dvc init

# 追蹤資料集
dvc add data/defect_dataset_v3/

# 提交到Git
git add data/defect_dataset_v3.dvc
git commit -m "Add defect dataset v3"

# 切換到歷史版本
dvc checkout data/defect_dataset_v3.dvc@v2
```

**與MLflow整合**：

```python
import mlflow

with mlflow.start_run():
    mlflow.log_param("data_version", "defect_v3")
    mlflow.log_param("data_hash", dvc.api.get_url("data/defect_dataset_v3/"))
    # ... 訓練邏輯
```

## 29.5 模型服務化與推理網關

訓練好的模型需要部署為高可用、低延遲的推理服務，供產線系統呼叫。

### 推理引擎選型

| 引擎 | 適用場景 | 優點 | 缺點 |
|------|---------|------|------|
| TensorRT | NVIDIA GPU推理 | 極致效能、INT8量化 | 僅NVIDIA、編譯慢 |
| Triton Inference Server | 多框架、多模型 | 支援動態batching、模型管理 | 部署複雜 |
| vLLM | LLM推理 | PagedAttention、高吞吐 | 僅LLM |
| ONNX Runtime | 跨平台 | 通用、CPU/GPU支援 | 效能不如專用引擎 |
| TorchScript | PyTorch模型 | 原生支援、易部署 | 效能一般 |

### Triton推理服務架構

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
         │ 負載均衡
         │
┌────────┴────────┐
│  API Gateway    │
│  (Kong/Nginx)   │
└─────────────────┘
```

**模型配置範例** (config.pbtxt)：

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

### 動態Batching

將多個請求合併為一個batch處理，提升GPU利用率。

**原理**：

- 請求到達後進入佇列，等待最多`max_queue_delay_microseconds`
- 累積到`preferred_batch_size`或超時後，合併為一個batch送入模型
- 推理完成後拆分結果返回各請求

**效果**（缺陷檢測）：

| 策略 | 吞吐量(img/s) | P99延遲(ms) |
|------|--------------|------------|
| 單請求處理 | 200 | 15 |
| 動態batching (max_delay=5ms) | 850 | 22 |

### 模型版本管理與灰度發布

**模型倉庫結構**：

```
/models/defect_cnn/
├── config.pbtxt
├── 1/              # v1 (生產)
│   └── model.plan
├── 2/              # v2 (灰度10%)
│   └── model.plan
└── 3/              # v3 (測試)
    └── model.plan
```

**灰度發布策略**：

```python
# 透過Triton模型路由實現灰度
# 90%流量走v1，10%流量走v2

import random

def route_model():
    if random.random() < 0.1:
        return "defect_cnn_v2"
    return "defect_cnn_v1"
```

**回滾機制**：

```bash
# 卸載問題版本
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/2/unload

# 載入穩定版本
curl -X POST http://triton:8000/v2/repository/models/defect_cnn/versions/1/load
```

### 推理服務高可用

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

**負載均衡**：

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

### 監控與告警

**關鍵指標**：

- **推理延遲**：P50/P95/P99，告警閾值>50ms
- **吞吐量**：QPS，告警閾值<目標80%
- **GPU利用率**：目標>70%，告警<50%
- **錯誤率**：目標<0.1%，告警>1%
- **佇列深度**：動態batch佇列長度，告警>100

**Prometheus + Grafana監控棧**：

```python
# Triton指標導出
# 預設在/metrics端點暴露Prometheus格式指標

# 自訂業務指標
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

## 29.6 邊緣部署與即時推理

邊緣推理是晶圓廠AI的「最後一公里」，直接服務於產線即時控制。

### 邊緣場景分類

| 場景 | 延遲要求 | 算力需求 | 部署位置 |
|------|---------|---------|---------|
| 終點檢測 | <2ms | <10 TOPS | 機台內嵌 |
| 本地質檢 | <20ms | <50 TOPS | 線邊工控機 |
| 安全聯鎖 | <1ms | <5 TOPS | PLC/安全控制器 |
| 資料預處理 | <10ms | <20 TOPS | 邊緣網關 |

### 邊緣硬體選型

**NVIDIA Jetson系列**：

| 型號 | 算力(INT8) | 記憶體 | 功耗 | 價格 |
|------|-----------|------|------|------|
| Jetson Nano | 472 GFLOPS | 4GB | 5-10W | $99 |
| Jetson Xavier NX | 21 TOPS | 8GB | 10-15W | $399 |
| Jetson AGX Orin | 275 TOPS | 64GB | 15-60W | $1,999 |

**推薦**：

- **輕量任務**（終點檢測）：Jetson Xavier NX，性價比最優
- **複雜任務**（多模型推理）：Jetson AGX Orin，算力充足
- **超低延遲**（安全聯鎖）：FPGA或專用ASIC

### 模型壓縮與優化

**量化**：

將FP32模型轉換為INT8，算力提升2-4倍，精度損失<1%。

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

移除不重要的權重或通道，減少計算量。

```python
# 結構化剪枝（通道級）
from torch.nn.utils import prune

for name, module in model.named_modules():
    if isinstance(module, nn.Conv2d):
        prune.ln_structured(module, name='weight', amount=0.3, dim=0, n=2)
        prune.remove(module, 'weight')
```

**知識蒸餾**：

用大模型(teacher)指導小模型(student)訓練。

```python
# 蒸餾loss
def distillation_loss(student_logits, teacher_logits, temperature=4.0):
    student_log_softmax = F.log_softmax(student_logits / temperature, dim=1)
    teacher_softmax = F.softmax(teacher_logits / temperature, dim=1)
    return F.kl_div(student_log_softmax, teacher_softmax, reduction='batchmean')
```

### 邊緣推理框架

**TensorRT**：

NVIDIA GPU專用推理引擎，效能最優。

```python
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

# 載入engine
with open("model.engine", "rb") as f:
    runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
    engine = runtime.deserialize_cuda_engine(f.read())

# 推理
context = engine.create_execution_context()
input_host = np.random.randn(1, 3, 224, 224).astype(np.float32)
output_host = np.empty((1, 1000), dtype=np.float32)

# 分配GPU記憶體
input_device = cuda.mem_alloc(input_host.nbytes)
output_device = cuda.mem_alloc(output_host.nbytes)

# 拷貝資料
cuda.memcpy_htod(input_device, input_host)
context.execute(1, [int(input_device), int(output_device)])
cuda.memcpy_dtoh(output_host, output_device)
```

**ONNX Runtime**：

跨平台推理引擎，支援CPU/GPU/NPU。

```python
import onnxruntime as ort

session = ort.InferenceSession("model.onnx")
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

result = session.run([output_name], {input_name: input_data})
```

### 離線容災設計

邊緣節點必須在網路中斷時獨立運行。

**策略**：

1. **本地模型快取**：邊緣節點儲存最新模型版本，定期從中心同步
2. **本地資料儲存**：推理結果先存本地，網路恢復後上傳
3. **降級模式**：模型異常時切換到規則引擎或預設值

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
            # 模型異常，降級到規則引擎
            return self.fallback.predict(input_data)
    
    def sync_to_cloud(self):
        if self.is_network_available():
            self.local_buffer.upload_pending()
```

### 實戰案例：蝕刻終點檢測邊緣部署

**背景**：某廠蝕刻機需要即時檢測蝕刻終點，原方案依賴雲端推理，延遲>100ms，導致過蝕刻。

**方案**：

- 部署Jetson AGX Orin在機台旁
- 模型壓縮：FP32→INT8量化，推理時間從15ms→3ms
- 離線容災：本地儲存最近7天模型，網路中斷時獨立運行

**效果**：

- 端到端延遲從100ms→8ms（含資料採集）
- 過蝕刻率從2.3%→0.4%
- 年節省晶圓報廢成本>$500k

## 29.7 算力排程與資源隔離

晶圓廠AI算力需要服務多個團隊（工藝、設備、良率）、多種任務（訓練、推理、實驗），如何公平、高效地分配資源是關鍵挑戰。

### 排程策略

**優先順序佇列**：

```
優先順序1: 產線推理服務（不可中斷）
優先順序2: 緊急訓練任務（如良率異常排查）
優先順序3: 常規訓練任務
優先順序4: 開發實驗
```

**資源配額**：

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

**時間片輪轉**：

白天優先推理服務，夜間釋放GPU給訓練任務。

```python
# 基於時間的排程策略
from datetime import datetime

def get_priority():
    hour = datetime.now().hour
    if 8 <= hour < 20:  # 白天
        return "inference"
    else:  # 夜間
        return "training"
```

### 多租戶隔離

**命名空間隔離**：

```yaml
# 每個團隊獨立命名空間
apiVersion: v1
kind: Namespace
metadata:
  name: yield-team
  labels:
    team: yield
    cost-center: CC1234
```

**GPU切分（MIG）**：

A100支援MIG（Multi-Instance GPU），將單卡切分為最多7個實例。

```bash
# 啟用MIG
nvidia-smi -i 0 -mig 1

# 建立GPU實例（1g.10gb = 1/7 A100）
nvidia-smi mig -cgi 1g.10gb -C
```

**網路隔離**：

```yaml
# NetworkPolicy限制跨命名空間存取
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

### 彈性伸縮

**基於負載的自動擴縮**：

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

**基於時間的定時擴縮**：

```yaml
# 夜間擴容訓練集群
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

### 作業排程系統

**Slurm**：

傳統HPC作業排程器，適合批處理訓練任務。

```bash
# 提交訓練作業
sbatch --gres=gpu:8 --time=24:00:00 train_yield.sh

# 查看作業狀態
squeue

# 取消作業
scancel <job_id>
```

**Volcano**：

Kubernetes原生的批處理排程器，支援Gang Scheduling。

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

### 實戰案例：多團隊算力共享平台

**背景**：某廠3個AI團隊（良率、缺陷、設備）共享16卡A100集群，資源爭搶嚴重。

**方案**：

- Kubernetes + Volcano排程
- 每團隊獨立命名空間，配額8 GPU
- 推理服務優先順序最高，訓練任務排隊
- 夜間自動擴容訓練集群

**效果**：

- 資源爭搶投訴減少90%
- GPU利用率從55%提升至78%
- 訓練任務等待時間從3天→4小時

## 29.8 算力成本建模與TCO分析

AI算力投資巨大，需要精細化的成本建模與ROI分析。

### TCO構成

**硬體成本**：

- GPU伺服器：$10k-50k/節點
- 網路設備：InfiniBand交換器$5k-10k/埠
- 儲存系統：全快閃記憶體NAS $50k-200k
- 機櫃、電力、散熱：$5k-10k/年/機櫃

**軟體成本**：

- GPU驅動、CUDA：免費
- 容器平台（K8s）：免費
- MLOps平台（Kubeflow）：免費
- 商業軟體（如Weights & Biases）：$50-200/user/月

**人力成本**：

- AI平台工程師：$150k-250k/年
- MLOps工程師：$120k-200k/年
- GPU運維工程師：$100k-150k/年

**電力成本**：

- 單卡A100功耗：300W
- 8卡節點功耗：~3kW
- 電費：$0.1/kWh → $2,600/年/節點

### TCO對比：自建 vs 雲 vs 混合

**場景**：16卡A100集群，5年TCO

| 方案 | 硬體 | 電力 | 人力 | 雲費用 | 5年TCO |
|------|------|------|------|--------|--------|
| 自建 | $400k | $50k | $500k | - | $950k |
| 純雲(AWS) | - | - | $200k | $1.2M | $1.4M |
| 混合(8卡自建+8卡雲) | $200k | $25k | $350k | $600k | $1.175M |

**結論**：

- **長期穩定負載**：自建更經濟（TCO低30-40%）
- **波動性負載**：雲更靈活（按需付費）
- **混合方案**：平衡成本與彈性

### ROI計算框架

**收益項**：

- 良率提升：每1%提升 → $10M-50M/年（視產能與產品價值）
- 效率提升：訓練時間縮短 → 工程師生產力提升
- 成本節省：自動化替代人工 → 人力成本節省

**成本項**：

- 算力投資：硬體+軟體+人力
- 運維成本：電力+維護+升級

**ROI公式**：

```
ROI = (年化收益 - 年化成本) / 年化成本 × 100%
```

**案例**：

- 投資：$200k（算力）+ $100k/年（運維）= $300k/年
- 收益：良率提升0.5% → $25M/年
- ROI = ($25M - $0.3M) / $0.3M × 100% = 8233%

### 成本優化策略

**GPU利用率提升**：

- 動態batching：提升推理吞吐
- 模型量化：減少記憶體佔用
- 多任務共享：同一GPU服務多個模型

**雲成本優化**：

- 預留實例：1年/3年預留，折扣30-60%
- Spot實例：非關鍵任務使用，折扣60-90%
- 自動擴縮：夜間縮容，避免閒置

**電力優化**：

- 液冷散熱：PUE從1.5→1.2，節電20%
- 智慧排程：夜間低谷電價時段訓練
- 餘熱回收：用於辦公供暖

### 實戰案例：算力投資ROI分析

**背景**：某廠投資$500k建設AI訓練集群，需評估ROI。

**成本**：

- 硬體：$500k（一次性）
- 運維：$50k/年（人力+電力）
- 5年TCO：$750k

**收益**：

- 良率提升0.3%：$15M/年
- 訓練效率提升50%：工程師時間節省$100k/年
- 年化收益：$15.1M

**ROI**：

- 年化成本：$150k（$750k/5年）
- ROI = ($15.1M - $0.15M) / $0.15M × 100% = 9967%
- 回收期：<1個月

## 29.9 基礎設施監控與故障自癒

GPU集群的穩定性直接影響AI任務的連續性，需要全面的監控與自癒機制。

### 監控指標體系

**硬體層**：

- GPU溫度、功耗、風扇轉速
- 記憶體ECC錯誤計數
- NVLink/PCIe頻寬與錯誤率
- CPU/記憶體/磁碟使用率

**軟體層**：

- GPU利用率、記憶體佔用
- 訓練任務進度、loss曲線
- 推理服務延遲、吞吐量、錯誤率
- 網路頻寬、延遲、丟包率

**業務層**：

- 模型準確率、漂移指標
- 資料管道延遲、失敗率
- SLA達成率

### DCGM Exporter + Prometheus

NVIDIA DCGM (Data Center GPU Manager) 提供GPU監控API。

```bash
# 部署DCGM Exporter
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/dcgm-exporter/main/deployment/dcgm-exporter.yaml

# Prometheus配置
scrape_configs:
  - job_name: 'dcgm'
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

**關鍵指標**：

```
DCGM_FI_DEV_GPU_TEMP          # GPU溫度
DCGM_FI_DEV_POWER_USAGE       # 功耗
DCGM_FI_DEV_FB_FREE           # 記憶體空閒
DCGM_FI_DEV_GPU_UTIL          # GPU利用率
DCGM_FI_DEV_ECC_DBE_VOL_TOTAL # 雙位ECC錯誤（嚴重）
```

### 告警規則

```yaml
# Prometheus告警規則
groups:
  - name: gpu_alerts
    rules:
    - alert: GPUTemperatureHigh
      expr: DCGM_FI_DEV_GPU_TEMP > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "GPU溫度過高: {{ $labels.gpu }}"
    
    - alert: GPUECCError
      expr: increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[5m]) > 0
      labels:
        severity: critical
      annotations:
        summary: "GPU發生ECC錯誤: {{ $labels.gpu }}"
    
    - alert: InferenceLatencyHigh
      expr: histogram_quantile(0.99, inference_latency_seconds) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "推理延遲P99>50ms"
```

### 故障自癒機制

**GPU故障自動隔離**：

```python
import subprocess
import time

def check_gpu_health(gpu_id):
    """檢查GPU健康狀態"""
    result = subprocess.run(
        ["nvidia-smi", "-i", str(gpu_id), "--query-gpu=ecc.errors.uncorrected.volatile.total", "--format=csv,noheader"],
        capture_output=True, text=True
    )
    ecc_errors = int(result.stdout.strip())
    return ecc_errors == 0

def isolate_faulty_gpu(gpu_id):
    """隔離故障GPU"""
    # 從排程池中移除
    subprocess.run(["nvidia-smi", "-i", str(gpu_id), "-mig", "0"])
    # 發送告警
    send_alert(f"GPU {gpu_id} 已隔離，存在ECC錯誤")
    # 記錄日誌
    log_event(f"GPU {gpu_id} isolated due to ECC errors")

# 定期檢查
while True:
    for gpu_id in range(8):
        if not check_gpu_health(gpu_id):
            isolate_faulty_gpu(gpu_id)
    time.sleep(60)
```

**訓練任務容錯**：

```python
# PyTorch Elastic（自動恢復）
import torch.distributed.elastic as etcd

# 配置checkpoint
def save_checkpoint(model, optimizer, epoch, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

# 故障恢復
def load_checkpoint(path):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return checkpoint['epoch']

# Elastic訓練
etcd.run(
    train_func,
    min_nodes=2,
    max_nodes=4,
    rdzv_backend="etcd",
    rdzv_endpoint="etcd:2379"
)
```

**推理服務降級**：

```python
class InferenceService:
    def __init__(self):
        self.primary_model = load_model("primary")
        self.fallback_model = load_model("fallback")  # 輕量版模型
        self.rule_engine = RuleEngine()
    
    def predict(self, input_data):
        try:
            # 嘗試主模型
            return self.primary_model.predict(input_data)
        except ModelError:
            try:
                # 降級到輕量模型
                return self.fallback_model.predict(input_data)
            except ModelError:
                # 降級到規則引擎
                return self.rule_engine.predict(input_data)
```

### 實戰案例：GPU集群故障自癒系統

**背景**：某廠16卡A100集群，月均發生2-3次GPU故障，導致訓練任務中斷。

**方案**：

- DCGM Exporter + Prometheus監控
- ECC錯誤自動檢測與GPU隔離
- 訓練任務Elastic Checkpoint，故障自動恢復
- 推理服務多級降級

**效果**：

- 訓練任務中斷時間從8小時/月→30分鐘/月
- 推理服務可用性從99.5%→99.99%
- 運維人力節省50%

## 29.10 算力底座驗收基準與壓測

新建或升級算力底座後，需要進行嚴格的驗收測試，確保滿足生產要求。

### 驗收維度

**效能基準**：

- 訓練吞吐：tokens/s（LLM）、images/s（CV）
- 推理延遲：P50/P95/P99
- 網路頻寬：AllReduce吞吐、延遲
- 儲存IO：順序/隨機讀寫頻寬

**穩定性基準**：

- 長時間運行：72小時連續訓練無故障
- 故障恢復：節點故障後自動恢復時間<10分鐘
- 記憶體洩漏：記憶體/記憶體佔用穩定

**功能基準**：

- 多租戶隔離：資源配額、網路隔離
- 彈性伸縮：自動擴縮容響應時間<2分鐘
- 監控告警：指標採集完整率>99%

### 訓練效能壓測

**MLPerf Training**：

業界標準訓練基準，覆蓋ResNet、BERT、GPT等模型。

```bash
# 運行MLPerf Training
cd mlperf/training
make run MODEL=bert DATA_DIR=/data/bpho

# 結果解讀
# BERT訓練時間：< 3.5小時（8×A100）為合格
```

**自訂基準**：

```python
# 晶圓廠典型模型訓練基準
import time
import torch

def benchmark_training(model, dataloader, epochs=3):
    """訓練效能基準測試"""
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

# 基準要求
# 良率預測模型(ResNet-50): >500 images/s (8×A100)
# 缺陷檢測模型(ResNet-101): >300 images/s (8×A100)
```

### 推理效能壓測

**工具**：Triton Perf Analyzer

```bash
# 推理效能測試
perf_analyzer -m defect_cnn -b 32 --service-triton triton:8001

# 結果解讀
# 吞吐量: >1000 inferencing/s (單卡A100)
# P99延遲: <30ms
```

**並發測試**：

```python
import asyncio
import aiohttp

async def inference_request(session, url, data):
    async with session.post(url, json=data) as response:
        return await response.json()

async def benchmark_concurrent(url, data, concurrency=100):
    """並發推理壓測"""
    async with aiohttp.ClientSession() as session:
        tasks = [inference_request(session, url, data) for _ in range(concurrency)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"Throughput: {concurrency / elapsed:.2f} req/s")
        print(f"P99 Latency: {sorted([r['latency'] for r in results])[int(concurrency*0.99)]:.2f}ms")
```

### 穩定性壓測

**72小時連續訓練**：

```bash
# 啟動長時間訓練任務
nohup python train_yield_model.py --epochs 100 > train.log 2>&1 &

# 監控腳本
while true; do
    # 檢查GPU狀態
    nvidia-smi --query-gpu=temperature,memory.used,utilization.gpu --format=csv >> gpu_monitor.log
    
    # 檢查訓練進度
    tail -n 1 train.log >> progress.log
    
    sleep 60
done
```

**故障注入測試**：

```bash
# 模擬GPU故障
nvidia-smi -i 0 --gpu-lock=1  # 鎖定GPU

# 驗證訓練任務自動恢復
# 預期：任務在10分鐘內自動遷移到其他節點繼續訓練
```

### 驗收清單

**硬體驗收**：

- [ ] GPU型號、數量符合設計
- [ ] 網路頻寬達到設計指標（InfiniBand 200Gb/s）
- [ ] 儲存IO滿足訓練需求（>10GB/s）
- [ ] 電力、散熱滿足滿載運行

**軟體驗收**：

- [ ] GPU驅動、CUDA版本正確
- [ ] 容器平台（K8s）部署成功
- [ ] 排程系統（Slurm/Volcano）配置完成
- [ ] 監控告警系統上線

**效能驗收**：

- [ ] 訓練吞吐達到基準要求
- [ ] 推理延遲滿足SLA
- [ ] 72小時穩定性測試通過
- [ ] 故障恢復時間<10分鐘

**功能驗收**：

- [ ] 多租戶隔離有效
- [ ] 彈性伸縮正常工作
- [ ] 監控指標採集完整
- [ ] 告警規則觸發正確

### 實戰案例：算力底座驗收

**背景**：某廠新建16卡A100集群，需驗收後上線。

**驗收過程**：

1. **硬體檢查**：GPU型號、網路頻寬、儲存IO均達標
2. **效能壓測**：
   - MLPerf BERT訓練：3.2小時（要求<3.5小時）✓
   - 推理吞吐：1200 inferencing/s（要求>1000）✓
   - P99延遲：25ms（要求<30ms）✓
3. **穩定性測試**：72小時連續訓練無故障 ✓
4. **故障注入**：模擬GPU故障，任務8分鐘內恢復 ✓

**結果**：驗收通過，正式上線。

---

## 本章小結

本章系統介紹了晶圓廠AI算力底座的設計與實施，覆蓋從GPU集群到邊緣推理節點的完整架構。核心要點：

1. **三類負載差異化設計**：訓練（高吞吐）、推理（低延遲）、邊緣（即時性）需要不同的硬體與架構方案
2. **集群選型關鍵**：GPU型號、網路拓撲、儲存架構直接影響訓練效能與成本
3. **分散式訓練工程**：DDP/FSDP/ZeRO策略選擇、混合精度、資料Pipeline優化是訓練效率的關鍵
4. **推理服務化**：Triton + 動態batching + 灰度發布構建高可用推理服務
5. **邊緣部署**：模型壓縮 + TensorRT優化 + 離線容災實現產線即時推理
6. **資源排程**：多租戶隔離、優先順序佇列、彈性伸縮保障資源公平與高效利用
7. **成本與TCO**：自建vs雲vs混合方案需要精細化ROI分析
8. **監控與自癒**：DCGM + Prometheus + 自動故障隔離保障集群穩定性
9. **驗收基準**：效能、穩定性、功能三維度的嚴格驗收確保生產就緒

算力底座是AI工程化的實體基礎，下一章將在此基礎上構建AI平台，提供模型開發、部署、運維的工具鏈與開發者體驗。
