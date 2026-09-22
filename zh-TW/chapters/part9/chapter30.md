# 第30章 晶圓廠AI平台工程——MLOps、模型治理與開發者體驗

> **本章導讀**
> 
> 第29章構建了算力底座，但裸金屬和K8s集群只是基礎設施。真正的AI工程化需要一套完整的平台能力：如何管理實驗的可複現性？如何治理模型版本？如何構建從資料到部署的自動化流水線？如何讓工藝工程師無需深度學習也能使用AI？本章將系統講解AI平台工程的核心組件：實驗管理、模型註冊、CI/CD for ML、特徵平台、LLM服務、開發者門戶、多租戶隔離、可觀察性，以及平台演進路線。

## 30.1 AI平台定位與分層架構

### 平台在AI工程化中的位置

晶圓廠AI平台位於算力層（第29章）與業務應用之間，承擔「承上啟下」的關鍵角色：

```
┌─────────────────────────────────────────┐
│  業務應用層                              │
│  良率預測 / 缺陷檢測 / R2R控制 / LLM問答  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  AI平台層（本章重點）                    │
│  實驗管理 / 模型註冊 / CI/CD / 特徵平台   │
│  LLM服務 / 開發者門戶 / 多租戶 / 可觀察性 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  算力層（第29章）                        │
│  GPU集群 / 推理服務 / 邊緣節點 / 儲存     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  資料層（第28章）                        │
│  資料治理 / 語義層 / 知識圖譜 / 資料血緣   │
└─────────────────────────────────────────┘
```

### 平台四層架構

**工具鏈層**：

- 實驗管理（MLflow/W&B）
- 模型註冊（MLflow Model Registry）
- 資料版本（DVC）
- 特徵儲存（Feast）
- 工作流編排（Airflow/Prefect）

**運行時層**：

- 訓練運行時（Kubeflow Training Operator）
- 推理運行時（Triton/Seldon）
- Notebook運行時（JupyterHub）
- 批處理運行時（Spark/Ray）

**治理層**：

- 多租戶隔離
- 權限與審計
- 模型審批流
- 合規與追溯

**門戶層**：

- 開發者門戶（Backstage）
- 模型市場
- 資料集市場
- 文檔與培訓

### 平台選型：自建 vs 商業 vs 開源

| 方案 | 代表產品 | 優點 | 缺點 | 適用場景 |
|------|---------|------|------|---------|
| 商業平台 | Databricks、SageMaker | 開箱即用、企業支援 | 成本高、客製化受限 | 快速啟動、預算充足 |
| 開源平台 | Kubeflow、MLflow | 靈活、無許可費 | 運維複雜、需工程投入 | 有工程團隊、需客製 |
| 混合方案 | Kubeflow + 商業組件 | 平衡成本與能力 | 整合複雜 | 中大型晶圓廠 |

**推薦方案**：

- **小型晶圓廠**（<5個AI工程師）：MLflow + Kubeflow + JupyterHub
- **中型晶圓廠**（5-20個AI工程師）：Kubeflow + MLflow + Feast + Airflow
- **大型晶圓廠**（>20個AI工程師）：Databricks或自建平台

## 30.2 實驗管理與可複現性

### 為什麼需要實驗管理

晶圓廠AI實驗的典型痛點：

- **不可複現**：3個月前的實驗結果無法重現
- **參數混亂**：超參數、資料版本、程式碼版本散落各處
- **知識流失**：工程師離職，實驗經驗隨之消失
- **重複勞動**：不同團隊重複做相同實驗

### MLflow實驗管理

**核心概念**：

- **Experiment**：一組相關運行的容器
- **Run**：單次實驗執行
- **Parameter**：輸入參數（超參數、配置）
- **Metric**：輸出指標（準確率、loss）
- **Artifact**：產出物（模型、圖表、日誌）

**基礎使用**：

```python
import mlflow

# 設定實驗
mlflow.set_experiment("yield_prediction_v3")

with mlflow.start_run():
    # 記錄參數
    mlflow.log_param("model_type", "transformer")
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("batch_size", 64)
    
    # 訓練模型
    model = train_model(train_data, val_data)
    
    # 記錄指標
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.93)
    
    # 儲存模型
    mlflow.pytorch.log_model(model, "model")
```

**與MLflow Server整合**：

```bash
# 啟動MLflow Server
mlflow server \
  --backend-store-uri postgresql://user:pass@db:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts/ \
  --host 0.0.0.0 --port 5000
```

### Weights & Biases (W&B)

**優勢**：

- 即時視覺化訓練曲線
- 超參數搜尋（Sweeps）
- 團隊協作
- 報告生成

**使用範例**：

```python
import wandb

# 初始化
wandb.init(
    project="yield-prediction",
    config={
        "model_type": "transformer",
        "learning_rate": 0.001,
        "batch_size": 64
    }
)

# 訓練迴圈
for epoch in range(epochs):
    train_loss = train_epoch(model)
    val_loss = validate_epoch(model)
    
    # 記錄指標
    wandb.log({
        "epoch": epoch,
        "train_loss": train_loss,
        "val_loss": val_loss
    })

# 儲存模型
wandb.save("model.pt")
```

### 實驗可複現性保障

**程式碼版本**：

```python
import mlflow
import subprocess

# 記錄Git commit
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
mlflow.log_param("git_commit", commit)

# 記錄程式碼差異
diff = subprocess.check_output(['git', 'diff']).decode()
with open("code_diff.patch", "w") as f:
    f.write(diff)
mlflow.log_artifact("code_diff.patch")
```

**環境版本**：

```python
import mlflow
import sys
import torch

# 記錄Python版本
mlflow.log_param("python_version", sys.version)

# 記錄PyTorch版本
mlflow.log_param("pytorch_version", torch.__version__)

# 記錄CUDA版本
mlflow.log_param("cuda_version", torch.version.cuda)

# 導出conda環境
import subprocess
subprocess.run(["conda", "env", "export", ">", "environment.yml"])
mlflow.log_artifact("environment.yml")
```

**資料版本**：

```python
import mlflow
import dvc.api

# 記錄資料版本
data_url = dvc.api.get_url("data/yield_train.parquet")
mlflow.log_param("data_url", data_url)

# 記錄資料hash
import hashlib
with open("data/yield_train.parquet", "rb") as f:
    data_hash = hashlib.md5(f.read()).hexdigest()
mlflow.log_param("data_hash", data_hash)
```

### 實驗中繼資料管理

**實驗卡片模板**：

```yaml
experiment:
  name: "yield_prediction_v3"
  owner: "zhang.san@fab.com"
  team: "yield-engineering"
  date: "2024-03-15"
  
  objective: "提升良率預測準確率至95%以上"
  
  hypothesis: |
    使用Transformer架構替代LSTM，結合注意力機制
    捕捉長程時序依賴，預期提升準確率3-5%
  
  dataset:
    name: "yield_train_v3"
    size: "100GB"
    samples: 1000000
    features: 500
    time_range: "2023-01-01 to 2024-02-29"
  
  model:
    architecture: "Transformer"
    parameters: 50000000
    input_dim: 500
    hidden_dim: 256
    num_layers: 6
  
  results:
    accuracy: 0.952
    f1_score: 0.931
    inference_latency_ms: 15
  
  conclusions: |
    Transformer相比LSTM提升4.2%準確率，達到目標。
    但推理延遲增加50%，需優化以滿足<20ms要求。
  
  next_steps:
    - "模型量化（INT8）降低推理延遲"
    - "增加資料增強提升泛化能力"
    - "A/B測試驗證線上效果"
```

## 30.3 模型註冊中心與版本治理

### 模型註冊中心的作用

**核心功能**：

- **模型版本管理**：追蹤模型的所有版本
- **生命週期管理**：Staging → Production → Archived
- **中繼資料管理**：模型卡片、訓練參數、效能指標
- **審批流**：模型上線前的審核與批准
- **依賴追蹤**：模型與資料、程式碼的關聯

### MLflow Model Registry

**註冊模型**：

```python
import mlflow

# 註冊模型
mlflow.register_model(
    model_uri="runs:/abc123/model",
    name="yield_predictor"
)
```

**模型生命週期**：

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 轉換到Staging
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Staging"
)

# 轉換到Production
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Production"
)

# 歸檔
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Archived"
)
```

**載入生產模型**：

```python
import mlflow.pyfunc

# 載入生產版本
model = mlflow.pyfunc.load_model(
    model_uri="models:/yield_predictor/Production"
)

predictions = model.predict(input_data)
```

### 模型卡片（Model Card）

**模型卡片模板**：

```markdown
# 模型卡片：yield_predictor_v3

## 基本資訊

- **模型名稱**：yield_predictor_v3
- **版本**：3.2.1
- **所有者**：zhang.san@fab.com
- **團隊**：Yield Engineering
- **建立日期**：2024-03-15
- **最後更新**：2024-03-20

## 模型描述

基於Transformer的良率預測模型，用於預測晶圓最終良率。

**輸入**：
- 500維特徵向量（工藝參數、設備狀態、環境資料）
- 時序長度：100步

**輸出**：
- 良率預測值（0-100%）
- 信賴度（0-1）

## 訓練資料

- **資料集**：yield_train_v3
- **樣本數**：1,000,000
- **時間範圍**：2023-01-01 至 2024-02-29
- **產品覆蓋**：Product A, B, C
- **設備覆蓋**：Tool 1-50

## 效能指標

| 指標 | 訓練集 | 驗證集 | 測試集 |
|------|--------|--------|--------|
| Accuracy | 95.2% | 94.8% | 94.5% |
| F1 Score | 93.1% | 92.7% | 92.3% |
| MAE | 2.3% | 2.5% | 2.7% |

## 限制與偏差

- **適用範圍**：僅適用於Product A/B/C，不適用於新產品
- **已知偏差**：對低良率樣本（<80%）預測準確率較低
- **資料依賴**：依賴FDC資料完整性，缺失值>10%時效能下降

## 推理效能

- **延遲**：P50=12ms, P99=25ms
- **吞吐**：單卡A100: 800 samples/s
- **記憶體佔用**：2.3GB

## 倫理與合規

- **公平性**：已通過公平性審計，對不同產品批次無顯著偏差
- **隱私**：不包含個人身份資訊（PII）
- **安全**：已通過安全審查，無敏感資訊洩露風險

## 使用說明

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/yield_predictor/Production")
predictions = model.predict(features)
```

## 維護計畫

- **重訓練頻率**：每季度
- **監控指標**：準確率、延遲、資料漂移
- **告警閾值**：準確率<93%或延遲>50ms
- **負責人**：zhang.san@fab.com

## 變更歷史

| 版本 | 日期 | 變更內容 | 負責人 |
|------|------|---------|--------|
| 3.2.1 | 2024-03-20 | 修復資料預處理bug | zhang.san |
| 3.2.0 | 2024-03-15 | 升級到Transformer架構 | zhang.san |
| 3.1.0 | 2024-02-01 | 增加Product C支援 | li.si |
```

### 模型審批流

**審批流程**：

```
模型開發 → 程式碼審查 → 效能驗證 → 安全審查 → 業務審批 → 上線部署
   ↓          ↓          ↓          ↓          ↓          ↓
 工程師    Tech Lead   QA Engineer  Security   PM/Owner   MLOps
```

**審批檢查清單**：

```yaml
approval_checklist:
  code_review:
    - [ ] 程式碼符合編碼規範
    - [ ] 單元測試覆蓋率>80%
    - [ ] 無安全漏洞（SAST掃描通過）
  
  performance_validation:
    - [ ] 測試集準確率>93%
    - [ ] 推理延遲P99<50ms
    - [ ] 72小時穩定性測試通過
  
  security_review:
    - [ ] 無敏感資料洩露
    - [ ] 模型輸入輸出驗證
    - [ ] 依賴組件安全掃描
  
  business_approval:
    - [ ] 業務價值評估
    - [ ] ROI分析
    - [ ] 風險評估
  
  deployment_readiness:
    - [ ] 監控告警配置
    - [ ] 回滾方案
    - [ ] 文檔完整
```

## 30.4 CI/CD for ML流水線

### ML流水線 vs 傳統CI/CD

**傳統CI/CD**：

```
程式碼提交 → 構建 → 測試 → 部署
```

**ML CI/CD**：

```
資料變更 → 資料驗證 → 模型訓練 → 模型驗證 → 模型部署
   ↓          ↓          ↓          ↓          ↓
 資料管道   資料品質    超參搜尋    效能評估    灰度發布
```

### 資料變更觸發重訓練

**使用Airflow編排**：

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_data_drift():
    """檢查資料漂移"""
    # 比較當前資料與訓練資料的分佈
    drift_score = calculate_drift()
    return drift_score > threshold

def retrain_model():
    """重訓練模型"""
    # 載入最新資料
    data = load_latest_data()
    
    # 訓練模型
    model = train_model(data)
    
    # 評估效能
    metrics = evaluate_model(model)
    
    # 註冊模型
    register_model(model, metrics)

def validate_model():
    """驗證模型效能"""
    # 載入最新模型
    model = load_latest_model()
    
    # 運行測試套件
    test_results = run_test_suite(model)
    
    # 檢查是否滿足SLA
    assert test_results['accuracy'] > 0.93
    assert test_results['latency_p99'] < 0.05

def deploy_model():
    """部署模型"""
    # 灰度發布
    deploy_to_staging(model_version="latest")
    
    # A/B測試
    run_ab_test(staging_percentage=0.1)

with DAG('ml_pipeline', schedule_interval='@daily') as dag:
    check_drift = PythonOperator(
        task_id='check_data_drift',
        python_callable=check_data_drift
    )
    
    retrain = PythonOperator(
        task_id='retrain_model',
        python_callable=retrain_model
    )
    
    validate = PythonOperator(
        task_id='validate_model',
        python_callable=validate_model
    )
    
    deploy = PythonOperator(
        task_id='deploy_model',
        python_callable=deploy_model
    )
    
    check_drift >> retrain >> validate >> deploy
```

### 自動化評估門禁

**評估指標門禁**：

```python
def model_quality_gate(model_version):
    """模型品質門禁"""
    model = load_model(model_version)
    
    # 1. 效能指標
    metrics = evaluate_model(model)
    
    if metrics['accuracy'] < 0.93:
        raise ValueError(f"Accuracy {metrics['accuracy']} < 0.93")
    
    if metrics['latency_p99'] > 0.05:
        raise ValueError(f"Latency P99 {metrics['latency_p99']} > 50ms")
    
    # 2. 公平性檢查
    fairness_metrics = check_fairness(model)
    if fairness_metrics['max_diff'] > 0.05:
        raise ValueError(f"Fairness violation: {fairness_metrics}")
    
    # 3. 魯棒性測試
    robustness = adversarial_test(model)
    if robustness['attack_success_rate'] > 0.01:
        raise ValueError(f"Robustness issue: {robustness}")
    
    # 4. 資料漂移檢查
    drift = check_drift(model)
    if drift['score'] > 0.1:
        raise Warning(f"Data drift detected: {drift}")
    
    return True
```

### 灰度發布與A/B測試

**灰度發布策略**：

```python
from kubernetes import client, config

def deploy_canary(model_version, percentage=0.1):
    """灰度發布"""
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    
    # 部署canary版本
    canary_deployment = create_deployment(
        name=f"model-canary-{model_version}",
        image=f"model-registry:{model_version}",
        replicas=1
    )
    
    apps_v1.create_namespaced_deployment(
        namespace="production",
        body=canary_deployment
    )
    
    # 配置流量分割
    configure_traffic_split(
        stable_percentage=1 - percentage,
        canary_percentage=percentage
    )
```

**A/B測試監控**：

```python
def monitor_ab_test(duration_hours=24):
    """監控A/B測試結果"""
    start_time = time.time()
    
    while time.time() - start_time < duration_hours * 3600:
        # 收集指標
        stable_metrics = collect_metrics("stable")
        canary_metrics = collect_metrics("canary")
        
        # 統計顯著性檢驗
        p_value = statistical_test(stable_metrics, canary_metrics)
        
        if p_value < 0.05:
            # 顯著差異
            if canary_metrics['accuracy'] > stable_metrics['accuracy']:
                # Canary更優，全量發布
                promote_canary()
                break
            else:
                # Canary更差，回滾
                rollback_canary()
                break
        
        time.sleep(3600)  # 每小時檢查一次
```

## 30.5 特徵平台與線上特徵服務

### 特徵平台的作用

**核心問題**：Training-Serving Skew（訓練-服務偏差）

- 訓練時使用的特徵與推理時不一致
- 特徵計算邏輯分散在不同程式碼中
- 特徵複用困難，重複開發

**特徵平台解決**：

- 統一特徵定義
- 離線/線上一致性
- 特徵複用與共享

### Feast特徵儲存

**架構**：

```
┌─────────────────────────────────────────┐
│  特徵定義（Feature Repository）          │
│  feature_repo/                          │
│  ├─ features/                           │
│  │  ├─ yield_features.py                │
│  │  └─ defect_features.py               │
│  └─ feature_store.yaml                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  離線儲存（Offline Store）               │
│  Parquet / BigQuery / Snowflake         │
│  用於訓練                               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  線上儲存（Online Store）                │
│  Redis / DynamoDB / Cassandra           │
│  用於推理                               │
└─────────────────────────────────────────┘
```

**特徵定義範例**：

```python
# feature_repo/features/yield_features.py
from feast import Feature, Entity, FeatureView, FileSource
from datetime import timedelta

# 定義實體
wafer = Entity(
    name="wafer",
    description="晶圓實體",
    tags={"team": "yield"}
)

# 定義資料來源
yield_source = FileSource(
    path="data/yield_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# 定義特徵視圖
yield_features = FeatureView(
    name="yield_features",
    entities=[wafer],
    ttl=timedelta(days=1),
    features=[
        Feature(
            name="avg_temperature",
            description="平均溫度",
            dtype=Float32
        ),
        Feature(
            name="max_pressure",
            description="最大壓力",
            dtype=Float32
        ),
        Feature(
            name="defect_count",
            description="缺陷數量",
            dtype=Int32
        ),
    ],
    source=yield_source,
    tags={"team": "yield", "version": "v3"}
)
```

**特徵註冊**：

```bash
# 應用特徵定義
feast apply

# 物化特徵到線上儲存
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

**訓練時獲取特徵**：

```python
from feast import FeatureStore

# 初始化Feature Store
store = FeatureStore(repo_path="feature_repo")

# 獲取訓練資料
entity_df = pd.DataFrame({
    "wafer_id": ["W001", "W002", "W003"],
    "event_timestamp": [pd.Timestamp.now()] * 3
})

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "yield_features:avg_temperature",
        "yield_features:max_pressure",
        "yield_features:defect_count"
    ]
).to_df()

# 訓練模型
model.train(training_df)
```

**推理時獲取特徵**：

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")

# 線上獲取特徵
feature_vector = store.get_online_features(
    features=[
        "yield_features:avg_temperature",
        "yield_features:max_pressure",
        "yield_features:defect_count"
    ],
    entity_rows=[{"wafer": "W001"}]
).to_dict()

# 推理
prediction = model.predict(feature_vector)
```

### 特徵服務化

**低延遲特徵服務**：

```python
from fastapi import FastAPI
from feast import FeatureStore
import redis

app = FastAPI()
store = FeatureStore(repo_path="feature_repo")
cache = redis.Redis(host='localhost', port=6379)

@app.get("/features/{wafer_id}")
async def get_features(wafer_id: str):
    # 先查快取
    cached = cache.get(f"features:{wafer_id}")
    if cached:
        return json.loads(cached)
    
    # 從Feature Store獲取
    features = store.get_online_features(
        features=[
            "yield_features:avg_temperature",
            "yield_features:max_pressure",
            "yield_features:defect_count"
        ],
        entity_rows=[{"wafer": wafer_id}]
    ).to_dict()
    
    # 寫入快取（TTL 5分鐘）
    cache.setex(
        f"features:{wafer_id}",
        300,
        json.dumps(features)
    )
    
    return features
```

## 30.6 LLM/Agent服務平台

### LLM服務架構

**核心組件**：

```
┌─────────────────────────────────────────┐
│  LLM Gateway                            │
│  ├─ 請求路由（多模型負載均衡）            │
│  ├─ 限流與配額（Rate Limiting）           │
│  ├─ 審計日誌（請求/響應記錄）             │
│  └─ 成本追蹤（Token使用統計）             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  模型服務層                              │
│  ├─ 本地模型（vLLM/TGI）                │
│  ├─ 雲API（OpenAI/Claude/千問）          │
│  └─ 專用模型（Embedding/Reranker）       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  RAG/Agent層                            │
│  ├─ GraphRAG（第28章知識圖譜）           │
│  ├─ Vector RAG（向量檢索）               │
│  ├─ Prompt模板管理                      │
│  └─ Agent工具鏈                         │
└─────────────────────────────────────────┘
```

### LLM Gateway實現

**請求路由與負載均衡**：

```python
from fastapi import FastAPI, Request
import httpx
import asyncio

app = FastAPI()

# 模型配置
MODELS = {
    "gpt-4": {
        "provider": "openai",
        "endpoints": ["https://api.openai.com/v1/chat/completions"],
        "rate_limit": 100  # requests/min
    },
    "qwen-72b": {
        "provider": "local",
        "endpoints": [
            "http://vllm-1:8000/v1/chat/completions",
            "http://vllm-2:8000/v1/chat/completions"
        ],
        "rate_limit": 50
    }
}

# 負載均衡器
class LoadBalancer:
    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.current = 0
        self.lock = asyncio.Lock()
    
    async def get_endpoint(self):
        async with self.lock:
            endpoint = self.endpoints[self.current]
            self.current = (self.current + 1) % len(self.endpoints)
            return endpoint

load_balancers = {
    name: LoadBalancer(config["endpoints"])
    for name, config in MODELS.items()
}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "gpt-4")
    
    # 獲取負載均衡器
    lb = load_balancers.get(model)
    if not lb:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")
    
    # 選擇endpoint
    endpoint = await lb.get_endpoint()
    
    # 轉發請求
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json=body,
            headers={"Authorization": f"Bearer {get_api_key(model)}"}
        )
        
        # 記錄審計日誌
        log_request(request, response, model)
        
        return response.json()
```

### Prompt模板管理

**模板儲存**：

```python
# prompt_templates/yield_analysis.yaml
templates:
  yield_root_cause:
    system: |
      你是晶圓廠良率分析專家。根據提供的資料，分析良率下降的根本原因。
      
      分析框架：
      1. 資料概覽：良率趨勢、異常批次
      2. 設備關聯：哪些設備與良率下降相關
      3. 工藝參數：關鍵參數的偏移
      4. 環境因素：溫濕度、潔淨度等
      5. 根本原因：綜合分析結論
      6. 建議措施：改進建議
    
    user: |
      請分析以下良率資料：
      
      產品：{product}
      時間範圍：{time_range}
      良率趨勢：{yield_trend}
      
      設備資料：
      {equipment_data}
      
      工藝參數：
      {process_params}
      
      請給出詳細的根因分析和改進建議。
    
    variables:
      - product
      - time_range
      - yield_trend
      - equipment_data
      - process_params
```

**模板服務**：

```python
from fastapi import FastAPI
import yaml

app = FastAPI()

class PromptTemplateManager:
    def __init__(self, template_dir="prompt_templates"):
        self.template_dir = template_dir
        self.templates = self.load_templates()
    
    def load_templates(self):
        templates = {}
        for file in Path(self.template_dir).glob("*.yaml"):
            with open(file) as f:
                data = yaml.safe_load(f)
                templates.update(data["templates"])
        return templates
    
    def render(self, template_name, **kwargs):
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return {
            "system": template["system"],
            "user": template["user"].format(**kwargs)
        }

template_manager = PromptTemplateManager()

@app.post("/prompt/render")
async def render_prompt(template_name: str, variables: dict):
    return template_manager.render(template_name, **variables)
```

### RAG服務整合

**GraphRAG + Vector RAG混合檢索**：

```python
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings

class HybridRAGService:
    def __init__(self):
        self.graph_retriever = GraphRAGRetriever()  # 第28章知識圖譜
        self.vector_retriever = VectorRetriever()   # 向量檢索
        self.llm = ChatOpenAI(model="gpt-4")
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. GraphRAG檢索（結構化知識）
        graph_docs = self.graph_retriever.retrieve(query, top_k=top_k)
        
        # 2. Vector RAG檢索（非結構化文檔）
        vector_docs = self.vector_retriever.retrieve(query, top_k=top_k)
        
        # 3. 融合排序
        combined = self.rerank(graph_docs + vector_docs, query)
        
        return combined[:top_k]
    
    def query(self, query: str):
        # 檢索相關文檔
        docs = self.retrieve(query)
        
        # 構建prompt
        context = "\n\n".join([doc.content for doc in docs])
        prompt = f"""
        根據以下上下文回答問題：
        
        {context}
        
        問題：{query}
        
        答案：
        """
        
        # 呼叫LLM
        response = self.llm.invoke(prompt)
        
        return {
            "answer": response.content,
            "sources": [doc.metadata for doc in docs]
        }
```

## 30.7 開發者門戶與自助服務

### 開發者門戶的作用

**核心目標**：降低AI使用門檻，讓工藝工程師無需深度學習也能使用AI。

**關鍵功能**：

- **模型市場**：瀏覽、試用、部署模型
- **資料集市場**：發現、申請、使用資料集
- **Notebook環境**：一鍵啟動Jupyter環境
- **文檔與培訓**：教程、最佳實踐、API文檔
- **社區與協作**：問答、程式碼分享、經驗交流

### Backstage開發者門戶

**架構**：

```
┌─────────────────────────────────────────┐
│  Backstage Portal                       │
│  ├─ 模型市場插件                        │
│  ├─ 資料集市場插件                      │
│  ├─ Notebook啟動器                      │
│  ├─ 文檔站點                            │
│  └─ 社區論壇                            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  後端服務                               │
│  ├─ MLflow API（模型/實驗）              │
│  ├─ Feast API（特徵）                   │
│  ├─ DVC API（資料）                     │
│  └─ JupyterHub API（Notebook）          │
└─────────────────────────────────────────┘
```

**模型市場頁面**：

```tsx
// src/components/ModelMarket.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button } from '@material-ui/core';

export const ModelMarket = () => {
  const [models, setModels] = useState([]);
  
  useEffect(() => {
    // 從MLflow獲取模型列表
    fetch('/api/mlflow/models')
      .then(res => res.json())
      .then(data => setModels(data));
  }, []);
  
  return (
    <div>
      <Typography variant="h4">模型市場</Typography>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {models.map(model => (
          <Card key={model.name}>
            <CardContent>
              <Typography variant="h6">{model.name}</Typography>
              <Typography variant="body2" color="textSecondary">
                版本: {model.version}
              </Typography>
              <Typography variant="body2">
                準確率: {(model.metrics.accuracy * 100).toFixed(2)}%
              </Typography>
              <Typography variant="body2">
                所有者: {model.owner}
              </Typography>
              <Button variant="contained" color="primary">
                試用
              </Button>
              <Button variant="outlined">
                詳情
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
```

### Notebook環境

**JupyterHub部署**：

```yaml
# jupyterhub-config.yaml
hub:
  config:
    JupyterHub:
      authenticator_class: generic-oauth
    GenericOAuthenticator:
      oauth_callback_url: https://jupyter.fab.com/hub/oauth_callback
      client_id: jupyterhub
      client_secret: ${OAUTH_SECRET}
      authorize_url: https://auth.fab.com/oauth/authorize
      token_url: https://auth.fab.com/oauth/token
      userdata_url: https://auth.fab.com/oauth/userinfo

singleuser:
  image:
    name: jupyter-scipy
    tag: latest
  storage:
    type: dynamic
    capacity: 10Gi
  cpu:
    limit: 4
    guarantee: 2
  memory:
    limit: 8G
    guarantee: 4G
  extraEnv:
    MLFLOW_TRACKING_URI: https://mlflow.fab.com
    FEAST_REPO_PATH: /home/jovyan/feature_repo
```

**一鍵啟動Notebook**：

```python
# notebooks/yield_analysis_template.ipynb
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 良率分析模板\n",
        "\n",
        "本Notebook提供良率分析的標準流程。"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# 導入庫\n",
        "import pandas as pd\n",
        "import mlflow\n",
        "from feast import FeatureStore\n",
        "\n",
        "# 連接MLflow\n",
        "mlflow.set_tracking_uri('https://mlflow.fab.com')\n",
        "\n",
        "# 連接Feature Store\n",
        "store = FeatureStore(repo_path='/home/jovyan/feature_repo')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# 載入資料\n",
        "entity_df = pd.DataFrame({\n",
        "    'wafer_id': ['W001', 'W002', 'W003'],\n",
        "    'event_timestamp': [pd.Timestamp.now()] * 3\n",
        "})\n",
        "\n",
        "features = store.get_historical_features(\n",
        "    entity_df=entity_df,\n",
        "    features=[\n",
        "        'yield_features:avg_temperature',\n",
        "        'yield_features:max_pressure'\n",
        "    ]\n",
        ").to_df()"
      ]
    }
  ]
}
```

## 30.8 多租戶隔離與權限體系

### 多租戶隔離的必要性

**晶圓廠場景**：

- **代工廠（Foundry）**：多個客戶共享算力，需嚴格隔離
- **大型IDM**：不同產品線（DRAM、NAND、Logic）獨立管理
- **研發團隊**：不同專案組資源獨立

**隔離維度**：

- **計算資源**：GPU、CPU、記憶體配額
- **資料儲存**：資料集、模型、特徵
- **網路存取**：命名空間隔離
- **權限控制**：RBAC（基於角色的存取控制）

### Kubernetes多租戶

**命名空間隔離**：

```yaml
# 客戶A命名空間
apiVersion: v1
kind: Namespace
metadata:
  name: customer-a
  labels:
    customer: customer-a
    tier: premium

---
# 資源配額
apiVersion: v1
kind: ResourceQuota
metadata:
  name: customer-a-quota
  namespace: customer-a
spec:
  hard:
    requests.cpu: "64"
    requests.memory: 256Gi
    requests.nvidia.com/gpu: 8
    limits.cpu: "128"
    limits.memory: 512Gi
    limits.nvidia.com/gpu: 16
    persistentvolumeclaims: 20
    services: 10

---
# 網路策略
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: customer-a-isolation
  namespace: customer-a
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: customer-a
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: customer-a
```

### RBAC權限控制

**角色定義**：

```yaml
# 資料科學家角色
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: customer-a
  name: data-scientist
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch", "create", "delete"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "watch", "create", "delete"]
- apiGroups: ["kubeflow.org"]
  resources: ["tfjobs", "pytorchjobs"]
  verbs: ["get", "list", "watch", "create", "delete"]

---
# 角色綁定
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: zhang-san-data-scientist
  namespace: customer-a
subjects:
- kind: User
  name: zhang.san@fab.com
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: data-scientist
  apiGroup: rbac.authorization.k8s.io
```

**MLflow權限**：

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 建立實驗（僅所有者可寫）
experiment_id = client.create_experiment(
    name="customer_a_yield_model",
    artifact_location="s3://mlflow-artifacts/customer-a"
)

# 設定權限標籤
client.set_experiment_tag(experiment_id, "owner", "zhang.san@fab.com")
client.set_experiment_tag(experiment_id, "team", "yield-engineering")
client.set_experiment_tag(experiment_id, "access", "private")
```

## 30.9 平台可觀察性與SLO管理

### 可觀察性三大支柱

**指標（Metrics）**：

- 系統指標：CPU、記憶體、GPU利用率
- 應用指標：請求延遲、錯誤率、吞吐量
- 業務指標：模型準確率、資料漂移、SLA達成率

**日誌（Logs）**：

- 應用日誌：訓練日誌、推理日誌
- 審計日誌：使用者操作、模型變更
- 安全日誌：存取記錄、異常行為

**追蹤（Traces）**：

- 請求鏈路：從API到模型推理的完整路徑
- 效能分析：各階段耗時、瓶頸定位

### SLO定義

**服務等級目標（SLO）**：

```yaml
# slo_definitions.yaml
services:
  inference_service:
    slo:
      availability: 99.99%  # 年停機<52分鐘
      latency:
        p50: 20ms
        p95: 40ms
        p99: 50ms
      error_rate: <0.1%
    
    slo_rules:
      - name: "high_availability"
        expr: "up{job='inference'} == 1"
        threshold: 0.9999
        duration: "30d"
      
      - name: "low_latency"
        expr: "histogram_quantile(0.99, inference_latency_seconds)"
        threshold: 0.05
        duration: "5m"
  
  training_service:
    slo:
      availability: 99.9%  # 年停機<8.76小時
      throughput: ">80% of baseline"
      job_completion: ">99% within SLA"
    
    slo_rules:
      - name: "job_completion"
        expr: "training_job_success_rate"
        threshold: 0.99
        duration: "7d"
```

### 監控告警

**Prometheus + Grafana**：

```yaml
# prometheus-rules.yaml
groups:
  - name: ai_platform_alerts
    rules:
    - alert: HighInferenceLatency
      expr: histogram_quantile(0.99, inference_latency_seconds) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "推理延遲P99超過50ms"
        description: "當前P99延遲: {{ $value }}s"
    
    - alert: LowModelAccuracy
      expr: model_accuracy < 0.93
      for: 1h
      labels:
        severity: critical
      annotations:
        summary: "模型準確率低於93%"
        description: "當前準確率: {{ $value }}"
    
    - alert: DataDriftDetected
      expr: data_drift_score > 0.1
      for: 30m
      labels:
        severity: warning
      annotations:
        summary: "檢測到資料漂移"
        description: "漂移分數: {{ $value }}"
```

**Grafana儀表板**：

```json
{
  "dashboard": {
    "title": "AI Platform Overview",
    "panels": [
      {
        "title": "推理延遲分佈",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, inference_latency_seconds)",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.99, inference_latency_seconds)",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "模型準確率趨勢",
        "type": "graph",
        "targets": [
          {
            "expr": "model_accuracy",
            "legendFormat": "{{model_name}}"
          }
        ]
      },
      {
        "title": "GPU利用率",
        "type": "gauge",
        "targets": [
          {
            "expr": "DCGM_FI_DEV_GPU_UTIL",
            "legendFormat": "GPU {{gpu}}"
          }
        ]
      }
    ]
  }
}
```

## 30.10 平台演進路線與組織配套

### 三階段演進路線

**階段一：腳本化（0-6個月）**

- **特徵**：
  - 手動執行訓練腳本
  - 模型儲存在本地檔案系統
  - 無版本管理
  - 無自動化流水線

- **工具**：
  - Python腳本
  - Git（程式碼版本）
  - 本地Jupyter

- **適用場景**：
  - AI團隊<3人
  - 模型數量<5個
  - 快速驗證階段

**階段二：工具化（6-18個月）**

- **特徵**：
  - MLflow實驗管理
  - 模型註冊中心
  - 基礎CI/CD
  - 特徵儲存

- **工具**：
  - MLflow
  - DVC
  - Feast
  - Airflow
  - Triton

- **適用場景**：
  - AI團隊3-10人
  - 模型數量5-20個
  - 生產環境部署

**階段三：平台化（18-36個月）**

- **特徵**：
  - 統一開發者門戶
  - 自助服務
  - 完整MLOps流水線
  - 多租戶隔離
  - 完善的可觀察性

- **工具**：
  - Kubeflow
  - Backstage
  - 完整監控棧
  - 自動化審批流

- **適用場景**：
  - AI團隊>10人
  - 模型數量>20個
  - 大規模生產環境

### 組織配套

**團隊結構**：

```
AI平台團隊
├─ 平台工程師（3-5人）
│  ├─ 基礎設施（K8s、GPU集群）
│  ├─ MLOps工具鏈（MLflow、Feast）
│  └─ 開發者體驗（門戶、文檔）
│
├─ ML工程師（5-10人）
│  ├─ 模型開發
│  ├─ 特徵工程
│  └─ 實驗優化
│
└─ 資料工程師（2-3人）
   ├─ 資料管道
   ├─ 資料品質
   └─ 資料治理
```

**關鍵角色**：

- **平台負責人**：整體架構、技術選型、團隊管理
- **MLOps工程師**：CI/CD流水線、自動化部署、監控告警
- **基礎設施工程師**：K8s集群、GPU管理、儲存網路
- **開發者體驗工程師**：門戶開發、文檔編寫、培訓支援

### 能力建設重點

**技術能力**：

- Kubernetes與容器編排
- GPU集群管理
- MLOps工具鏈（MLflow、Feast、Kubeflow）
- 監控與可觀察性（Prometheus、Grafana）
- 安全與合規（RBAC、審計、加密）

**流程能力**：

- 實驗管理最佳實踐
- 模型版本治理
- CI/CD for ML
- 資料品質管理
- 故障響應與復盤

**組織能力**：

- 跨團隊協作（AI團隊、IT團隊、業務團隊）
- 知識沉澱與分享
- 培訓與賦能
- 持續改進機制

---

## 本章小結

本章系統介紹了晶圓廠AI平台工程的核心組件與實施路徑。核心要點：

1. **平台定位**：AI平台位於算力層與業務應用之間，承擔「承上啟下」的關鍵角色
2. **實驗管理**：MLflow/W&B保障實驗可複現性，避免知識流失
3. **模型治理**：模型註冊中心 + 模型卡片 + 審批流，確保模型品質與合規
4. **CI/CD for ML**：資料變更觸發重訓練、自動化評估門禁、灰度發布
5. **特徵平台**：Feast解決Training-Serving Skew，實現特徵複用
6. **LLM服務**：LLM Gateway + Prompt管理 + RAG整合，支撐大模型應用
7. **開發者門戶**：降低AI使用門檻，讓工藝工程師也能使用AI
8. **多租戶隔離**：命名空間 + 資源配額 + RBAC，保障資源公平與安全
9. **可觀察性**：Metrics + Logs + Traces，SLO管理保障服務品質
10. **演進路線**：腳本化→工具化→平台化，匹配團隊規模與業務需求

AI平台是AI工程化的核心載體，下一章將聚焦生產級AI運維，保障AI系統在晶圓廠的穩定、安全、高效運行。
