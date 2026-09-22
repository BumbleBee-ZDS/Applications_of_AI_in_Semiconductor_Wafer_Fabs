# 第30章 晶圆厂AI平台工程——MLOps、模型治理与开发者体验

> **本章导读**
> 
> 第29章构建了算力底座，但裸金属和K8s集群只是基础设施。真正的AI工程化需要一套完整的平台能力：如何管理实验的可复现性？如何治理模型版本？如何构建从数据到部署的自动化流水线？如何让工艺工程师无需深度学习也能使用AI？本章将系统讲解AI平台工程的核心组件：实验管理、模型注册、CI/CD for ML、特征平台、LLM服务、开发者门户、多租户隔离、可观测性，以及平台演进路线。

## 30.1 AI平台定位与分层架构

### 平台在AI工程化中的位置

晶圆厂AI平台位于算力层（第29章）与业务应用之间，承担"承上启下"的关键角色：

```
┌─────────────────────────────────────────┐
│  业务应用层                              │
│  良率预测 / 缺陷检测 / R2R控制 / LLM问答  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  AI平台层（本章重点）                    │
│  实验管理 / 模型注册 / CI/CD / 特征平台   │
│  LLM服务 / 开发者门户 / 多租户 / 可观测性 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  算力层（第29章）                        │
│  GPU集群 / 推理服务 / 边缘节点 / 存储     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  数据层（第28章）                        │
│  数据治理 / 语义层 / 知识图谱 / 数据血缘   │
└─────────────────────────────────────────┘
```

### 平台四层架构

**工具链层**：

- 实验管理（MLflow/W&B）
- 模型注册（MLflow Model Registry）
- 数据版本（DVC）
- 特征存储（Feast）
- 工作流编排（Airflow/Prefect）

**运行时层**：

- 训练运行时（Kubeflow Training Operator）
- 推理运行时（Triton/Seldon）
- Notebook运行时（JupyterHub）
- 批处理运行时（Spark/Ray）

**治理层**：

- 多租户隔离
- 权限与审计
- 模型审批流
- 合规与追溯

**门户层**：

- 开发者门户（Backstage）
- 模型市场
- 数据集市场
- 文档与培训

### 平台选型：自建 vs 商业 vs 开源

| 方案 | 代表产品 | 优点 | 缺点 | 适用场景 |
|------|---------|------|------|---------|
| 商业平台 | Databricks、SageMaker | 开箱即用、企业支持 | 成本高、定制化受限 | 快速启动、预算充足 |
| 开源平台 | Kubeflow、MLflow | 灵活、无许可费 | 运维复杂、需工程投入 | 有工程团队、需定制 |
| 混合方案 | Kubeflow + 商业组件 | 平衡成本与能力 | 集成复杂 | 中大型晶圆厂 |

**推荐方案**：

- **小型晶圆厂**（<5个AI工程师）：MLflow + Kubeflow + JupyterHub
- **中型晶圆厂**（5-20个AI工程师）：Kubeflow + MLflow + Feast + Airflow
- **大型晶圆厂**（>20个AI工程师）：Databricks或自建平台

## 30.2 实验管理与可复现性

### 为什么需要实验管理

晶圆厂AI实验的典型痛点：

- **不可复现**：3个月前的实验结果无法重现
- **参数混乱**：超参数、数据版本、代码版本散落各处
- **知识流失**：工程师离职，实验经验随之消失
- **重复劳动**：不同团队重复做相同实验

### MLflow实验管理

**核心概念**：

- **Experiment**：一组相关运行的容器
- **Run**：单次实验执行
- **Parameter**：输入参数（超参数、配置）
- **Metric**：输出指标（准确率、loss）
- **Artifact**：产出物（模型、图表、日志）

**基础使用**：

```python
import mlflow

# 设置实验
mlflow.set_experiment("yield_prediction_v3")

with mlflow.start_run():
    # 记录参数
    mlflow.log_param("model_type", "transformer")
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("batch_size", 64)
    
    # 训练模型
    model = train_model(train_data, val_data)
    
    # 记录指标
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.93)
    
    # 保存模型
    mlflow.pytorch.log_model(model, "model")
```

**与MLflow Server集成**：

```bash
# 启动MLflow Server
mlflow server \
  --backend-store-uri postgresql://user:pass@db:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts/ \
  --host 0.0.0.0 --port 5000
```

### Weights & Biases (W&B)

**优势**：

- 实时可视化训练曲线
- 超参数搜索（Sweeps）
- 团队协作
- 报告生成

**使用示例**：

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

# 训练循环
for epoch in range(epochs):
    train_loss = train_epoch(model)
    val_loss = validate_epoch(model)
    
    # 记录指标
    wandb.log({
        "epoch": epoch,
        "train_loss": train_loss,
        "val_loss": val_loss
    })

# 保存模型
wandb.save("model.pt")
```

### 实验可复现性保障

**代码版本**：

```python
import mlflow
import subprocess

# 记录Git commit
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
mlflow.log_param("git_commit", commit)

# 记录代码差异
diff = subprocess.check_output(['git', 'diff']).decode()
with open("code_diff.patch", "w") as f:
    f.write(diff)
mlflow.log_artifact("code_diff.patch")
```

**环境版本**：

```python
import mlflow
import sys
import torch

# 记录Python版本
mlflow.log_param("python_version", sys.version)

# 记录PyTorch版本
mlflow.log_param("pytorch_version", torch.__version__)

# 记录CUDA版本
mlflow.log_param("cuda_version", torch.version.cuda)

# 导出conda环境
import subprocess
subprocess.run(["conda", "env", "export", ">", "environment.yml"])
mlflow.log_artifact("environment.yml")
```

**数据版本**：

```python
import mlflow
import dvc.api

# 记录数据版本
data_url = dvc.api.get_url("data/yield_train.parquet")
mlflow.log_param("data_url", data_url)

# 记录数据hash
import hashlib
with open("data/yield_train.parquet", "rb") as f:
    data_hash = hashlib.md5(f.read()).hexdigest()
mlflow.log_param("data_hash", data_hash)
```

### 实验元数据管理

**实验卡片模板**：

```yaml
experiment:
  name: "yield_prediction_v3"
  owner: "zhang.san@fab.com"
  team: "yield-engineering"
  date: "2024-03-15"
  
  objective: "提升良率预测准确率至95%以上"
  
  hypothesis: |
    使用Transformer架构替代LSTM，结合注意力机制
    捕捉长程时序依赖，预期提升准确率3-5%
  
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
    Transformer相比LSTM提升4.2%准确率，达到目标。
    但推理延迟增加50%，需优化以满足<20ms要求。
  
  next_steps:
    - "模型量化（INT8）降低推理延迟"
    - "增加数据增强提升泛化能力"
    - "A/B测试验证线上效果"
```

## 30.3 模型注册中心与版本治理

### 模型注册中心的作用

**核心功能**：

- **模型版本管理**：追踪模型的所有版本
- **生命周期管理**：Staging → Production → Archived
- **元数据管理**：模型卡片、训练参数、性能指标
- **审批流**：模型上线前的审核与批准
- **依赖追踪**：模型与数据、代码的关联

### MLflow Model Registry

**注册模型**：

```python
import mlflow

# 注册模型
mlflow.register_model(
    model_uri="runs:/abc123/model",
    name="yield_predictor"
)
```

**模型生命周期**：

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 转换到Staging
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Staging"
)

# 转换到Production
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Production"
)

# 归档
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Archived"
)
```

**加载生产模型**：

```python
import mlflow.pyfunc

# 加载生产版本
model = mlflow.pyfunc.load_model(
    model_uri="models:/yield_predictor/Production"
)

predictions = model.predict(input_data)
```

### 模型卡片（Model Card）

**模型卡片模板**：

```markdown
# 模型卡片：yield_predictor_v3

## 基本信息

- **模型名称**：yield_predictor_v3
- **版本**：3.2.1
- **所有者**：zhang.san@fab.com
- **团队**：Yield Engineering
- **创建日期**：2024-03-15
- **最后更新**：2024-03-20

## 模型描述

基于Transformer的良率预测模型，用于预测晶圆最终良率。

**输入**：
- 500维特征向量（工艺参数、设备状态、环境数据）
- 时序长度：100步

**输出**：
- 良率预测值（0-100%）
- 置信度（0-1）

## 训练数据

- **数据集**：yield_train_v3
- **样本数**：1,000,000
- **时间范围**：2023-01-01 至 2024-02-29
- **产品覆盖**：Product A, B, C
- **设备覆盖**：Tool 1-50

## 性能指标

| 指标 | 训练集 | 验证集 | 测试集 |
|------|--------|--------|--------|
| Accuracy | 95.2% | 94.8% | 94.5% |
| F1 Score | 93.1% | 92.7% | 92.3% |
| MAE | 2.3% | 2.5% | 2.7% |

## 限制与偏差

- **适用范围**：仅适用于Product A/B/C，不适用于新产品
- **已知偏差**：对低良率样本（<80%）预测准确率较低
- **数据依赖**：依赖FDC数据完整性，缺失值>10%时性能下降

## 推理性能

- **延迟**：P50=12ms, P99=25ms
- **吞吐**：单卡A100: 800 samples/s
- **显存占用**：2.3GB

## 伦理与合规

- **公平性**：已通过公平性审计，对不同产品批次无显著偏差
- **隐私**：不包含个人身份信息（PII）
- **安全**：已通过安全审查，无敏感信息泄露风险

## 使用说明

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/yield_predictor/Production")
predictions = model.predict(features)
```

## 维护计划

- **重训练频率**：每季度
- **监控指标**：准确率、延迟、数据漂移
- **告警阈值**：准确率<93%或延迟>50ms
- **负责人**：zhang.san@fab.com

## 变更历史

| 版本 | 日期 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 3.2.1 | 2024-03-20 | 修复数据预处理bug | zhang.san |
| 3.2.0 | 2024-03-15 | 升级到Transformer架构 | zhang.san |
| 3.1.0 | 2024-02-01 | 增加Product C支持 | li.si |
```

### 模型审批流

**审批流程**：

```
模型开发 → 代码审查 → 性能验证 → 安全审查 → 业务审批 → 上线部署
   ↓          ↓          ↓          ↓          ↓          ↓
 工程师    Tech Lead   QA Engineer  Security   PM/Owner   MLOps
```

**审批检查清单**：

```yaml
approval_checklist:
  code_review:
    - [ ] 代码符合编码规范
    - [ ] 单元测试覆盖率>80%
    - [ ] 无安全漏洞（SAST扫描通过）
  
  performance_validation:
    - [ ] 测试集准确率>93%
    - [ ] 推理延迟P99<50ms
    - [ ] 72小时稳定性测试通过
  
  security_review:
    - [ ] 无敏感数据泄露
    - [ ] 模型输入输出验证
    - [ ] 依赖组件安全扫描
  
  business_approval:
    - [ ] 业务价值评估
    - [ ] ROI分析
    - [ ] 风险评估
  
  deployment_readiness:
    - [ ] 监控告警配置
    - [ ] 回滚方案
    - [ ] 文档完整
```

## 30.4 CI/CD for ML流水线

### ML流水线 vs 传统CI/CD

**传统CI/CD**：

```
代码提交 → 构建 → 测试 → 部署
```

**ML CI/CD**：

```
数据变更 → 数据验证 → 模型训练 → 模型验证 → 模型部署
   ↓          ↓          ↓          ↓          ↓
 数据管道   数据质量    超参搜索    性能评估    灰度发布
```

### 数据变更触发重训练

**使用Airflow编排**：

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_data_drift():
    """检查数据漂移"""
    # 比较当前数据与训练数据的分布
    drift_score = calculate_drift()
    return drift_score > threshold

def retrain_model():
    """重训练模型"""
    # 加载最新数据
    data = load_latest_data()
    
    # 训练模型
    model = train_model(data)
    
    # 评估性能
    metrics = evaluate_model(model)
    
    # 注册模型
    register_model(model, metrics)

def validate_model():
    """验证模型性能"""
    # 加载最新模型
    model = load_latest_model()
    
    # 运行测试套件
    test_results = run_test_suite(model)
    
    # 检查是否满足SLA
    assert test_results['accuracy'] > 0.93
    assert test_results['latency_p99'] < 0.05

def deploy_model():
    """部署模型"""
    # 灰度发布
    deploy_to_staging(model_version="latest")
    
    # A/B测试
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

### 自动化评估门禁

**评估指标门禁**：

```python
def model_quality_gate(model_version):
    """模型质量门禁"""
    model = load_model(model_version)
    
    # 1. 性能指标
    metrics = evaluate_model(model)
    
    if metrics['accuracy'] < 0.93:
        raise ValueError(f"Accuracy {metrics['accuracy']} < 0.93")
    
    if metrics['latency_p99'] > 0.05:
        raise ValueError(f"Latency P99 {metrics['latency_p99']} > 50ms")
    
    # 2. 公平性检查
    fairness_metrics = check_fairness(model)
    if fairness_metrics['max_diff'] > 0.05:
        raise ValueError(f"Fairness violation: {fairness_metrics}")
    
    # 3. 鲁棒性测试
    robustness = adversarial_test(model)
    if robustness['attack_success_rate'] > 0.01:
        raise ValueError(f"Robustness issue: {robustness}")
    
    # 4. 数据漂移检查
    drift = check_drift(model)
    if drift['score'] > 0.1:
        raise Warning(f"Data drift detected: {drift}")
    
    return True
```

### 灰度发布与A/B测试

**灰度发布策略**：

```python
from kubernetes import client, config

def deploy_canary(model_version, percentage=0.1):
    """灰度发布"""
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

**A/B测试监控**：

```python
def monitor_ab_test(duration_hours=24):
    """监控A/B测试结果"""
    start_time = time.time()
    
    while time.time() - start_time < duration_hours * 3600:
        # 收集指标
        stable_metrics = collect_metrics("stable")
        canary_metrics = collect_metrics("canary")
        
        # 统计显著性检验
        p_value = statistical_test(stable_metrics, canary_metrics)
        
        if p_value < 0.05:
            # 显著差异
            if canary_metrics['accuracy'] > stable_metrics['accuracy']:
                # Canary更优，全量发布
                promote_canary()
                break
            else:
                # Canary更差，回滚
                rollback_canary()
                break
        
        time.sleep(3600)  # 每小时检查一次
```

## 30.5 特征平台与在线特征服务

### 特征平台的作用

**核心问题**：Training-Serving Skew（训练-服务偏差）

- 训练时使用的特征与推理时不一致
- 特征计算逻辑分散在不同代码中
- 特征复用困难，重复开发

**特征平台解决**：

- 统一特征定义
- 离线/在线一致性
- 特征复用与共享

### Feast特征存储

**架构**：

```
┌─────────────────────────────────────────┐
│  特征定义（Feature Repository）          │
│  feature_repo/                          │
│  ├─ features/                           │
│  │  ├─ yield_features.py                │
│  │  └─ defect_features.py               │
│  └─ feature_store.yaml                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  离线存储（Offline Store）               │
│  Parquet / BigQuery / Snowflake         │
│  用于训练                               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  在线存储（Online Store）                │
│  Redis / DynamoDB / Cassandra           │
│  用于推理                               │
└─────────────────────────────────────────┘
```

**特征定义示例**：

```python
# feature_repo/features/yield_features.py
from feast import Feature, Entity, FeatureView, FileSource
from datetime import timedelta

# 定义实体
wafer = Entity(
    name="wafer",
    description="晶圆实体",
    tags={"team": "yield"}
)

# 定义数据源
yield_source = FileSource(
    path="data/yield_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# 定义特征视图
yield_features = FeatureView(
    name="yield_features",
    entities=[wafer],
    ttl=timedelta(days=1),
    features=[
        Feature(
            name="avg_temperature",
            description="平均温度",
            dtype=Float32
        ),
        Feature(
            name="max_pressure",
            description="最大压力",
            dtype=Float32
        ),
        Feature(
            name="defect_count",
            description="缺陷数量",
            dtype=Int32
        ),
    ],
    source=yield_source,
    tags={"team": "yield", "version": "v3"}
)
```

**特征注册**：

```bash
# 应用特征定义
feast apply

# 物化特征到在线存储
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

**训练时获取特征**：

```python
from feast import FeatureStore

# 初始化Feature Store
store = FeatureStore(repo_path="feature_repo")

# 获取训练数据
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

# 训练模型
model.train(training_df)
```

**推理时获取特征**：

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")

# 在线获取特征
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

### 特征服务化

**低延迟特征服务**：

```python
from fastapi import FastAPI
from feast import FeatureStore
import redis

app = FastAPI()
store = FeatureStore(repo_path="feature_repo")
cache = redis.Redis(host='localhost', port=6379)

@app.get("/features/{wafer_id}")
async def get_features(wafer_id: str):
    # 先查缓存
    cached = cache.get(f"features:{wafer_id}")
    if cached:
        return json.loads(cached)
    
    # 从Feature Store获取
    features = store.get_online_features(
        features=[
            "yield_features:avg_temperature",
            "yield_features:max_pressure",
            "yield_features:defect_count"
        ],
        entity_rows=[{"wafer": wafer_id}]
    ).to_dict()
    
    # 写入缓存（TTL 5分钟）
    cache.setex(
        f"features:{wafer_id}",
        300,
        json.dumps(features)
    )
    
    return features
```

## 30.6 LLM/Agent服务平台

### LLM服务架构

**核心组件**：

```
┌─────────────────────────────────────────┐
│  LLM Gateway                            │
│  ├─ 请求路由（多模型负载均衡）            │
│  ├─ 限流与配额（Rate Limiting）           │
│  ├─ 审计日志（请求/响应记录）             │
│  └─ 成本追踪（Token使用统计）             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  模型服务层                              │
│  ├─ 本地模型（vLLM/TGI）                │
│  ├─ 云API（OpenAI/Claude/千问）          │
│  └─ 专用模型（Embedding/Reranker）       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  RAG/Agent层                            │
│  ├─ GraphRAG（第28章知识图谱）           │
│  ├─ Vector RAG（向量检索）               │
│  ├─ Prompt模板管理                      │
│  └─ Agent工具链                         │
└─────────────────────────────────────────┘
```

### LLM Gateway实现

**请求路由与负载均衡**：

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

# 负载均衡器
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
    
    # 获取负载均衡器
    lb = load_balancers.get(model)
    if not lb:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")
    
    # 选择endpoint
    endpoint = await lb.get_endpoint()
    
    # 转发请求
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json=body,
            headers={"Authorization": f"Bearer {get_api_key(model)}"}
        )
        
        # 记录审计日志
        log_request(request, response, model)
        
        return response.json()
```

### Prompt模板管理

**模板存储**：

```python
# prompt_templates/yield_analysis.yaml
templates:
  yield_root_cause:
    system: |
      你是晶圆厂良率分析专家。根据提供的数据，分析良率下降的根本原因。
      
      分析框架：
      1. 数据概览：良率趋势、异常批次
      2. 设备关联：哪些设备与良率下降相关
      3. 工艺参数：关键参数的偏移
      4. 环境因素：温湿度、洁净度等
      5. 根本原因：综合分析结论
      6. 建议措施：改进建议
    
    user: |
      请分析以下良率数据：
      
      产品：{product}
      时间范围：{time_range}
      良率趋势：{yield_trend}
      
      设备数据：
      {equipment_data}
      
      工艺参数：
      {process_params}
      
      请给出详细的根因分析和改进建议。
    
    variables:
      - product
      - time_range
      - yield_trend
      - equipment_data
      - process_params
```

**模板服务**：

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

### RAG服务集成

**GraphRAG + Vector RAG混合检索**：

```python
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings

class HybridRAGService:
    def __init__(self):
        self.graph_retriever = GraphRAGRetriever()  # 第28章知识图谱
        self.vector_retriever = VectorRetriever()   # 向量检索
        self.llm = ChatOpenAI(model="gpt-4")
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. GraphRAG检索（结构化知识）
        graph_docs = self.graph_retriever.retrieve(query, top_k=top_k)
        
        # 2. Vector RAG检索（非结构化文档）
        vector_docs = self.vector_retriever.retrieve(query, top_k=top_k)
        
        # 3. 融合排序
        combined = self.rerank(graph_docs + vector_docs, query)
        
        return combined[:top_k]
    
    def query(self, query: str):
        # 检索相关文档
        docs = self.retrieve(query)
        
        # 构建prompt
        context = "\n\n".join([doc.content for doc in docs])
        prompt = f"""
        根据以下上下文回答问题：
        
        {context}
        
        问题：{query}
        
        答案：
        """
        
        # 调用LLM
        response = self.llm.invoke(prompt)
        
        return {
            "answer": response.content,
            "sources": [doc.metadata for doc in docs]
        }
```

## 30.7 开发者门户与自助服务

### 开发者门户的作用

**核心目标**：降低AI使用门槛，让工艺工程师无需深度学习也能使用AI。

**关键功能**：

- **模型市场**：浏览、试用、部署模型
- **数据集市场**：发现、申请、使用数据集
- **Notebook环境**：一键启动Jupyter环境
- **文档与培训**：教程、最佳实践、API文档
- **社区与协作**：问答、代码分享、经验交流

### Backstage开发者门户

**架构**：

```
┌─────────────────────────────────────────┐
│  Backstage Portal                       │
│  ├─ 模型市场插件                        │
│  ├─ 数据集市场插件                      │
│  ├─ Notebook启动器                      │
│  ├─ 文档站点                            │
│  └─ 社区论坛                            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  后端服务                               │
│  ├─ MLflow API（模型/实验）              │
│  ├─ Feast API（特征）                   │
│  ├─ DVC API（数据）                     │
│  └─ JupyterHub API（Notebook）          │
└─────────────────────────────────────────┘
```

**模型市场页面**：

```tsx
// src/components/ModelMarket.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button } from '@material-ui/core';

export const ModelMarket = () => {
  const [models, setModels] = useState([]);
  
  useEffect(() => {
    // 从MLflow获取模型列表
    fetch('/api/mlflow/models')
      .then(res => res.json())
      .then(data => setModels(data));
  }, []);
  
  return (
    <div>
      <Typography variant="h4">模型市场</Typography>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {models.map(model => (
          <Card key={model.name}>
            <CardContent>
              <Typography variant="h6">{model.name}</Typography>
              <Typography variant="body2" color="textSecondary">
                版本: {model.version}
              </Typography>
              <Typography variant="body2">
                准确率: {(model.metrics.accuracy * 100).toFixed(2)}%
              </Typography>
              <Typography variant="body2">
                所有者: {model.owner}
              </Typography>
              <Button variant="contained" color="primary">
                试用
              </Button>
              <Button variant="outlined">
                详情
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
```

### Notebook环境

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

**一键启动Notebook**：

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
        "本Notebook提供良率分析的标准流程。"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# 导入库\n",
        "import pandas as pd\n",
        "import mlflow\n",
        "from feast import FeatureStore\n",
        "\n",
        "# 连接MLflow\n",
        "mlflow.set_tracking_uri('https://mlflow.fab.com')\n",
        "\n",
        "# 连接Feature Store\n",
        "store = FeatureStore(repo_path='/home/jovyan/feature_repo')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# 加载数据\n",
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

## 30.8 多租户隔离与权限体系

### 多租户隔离的必要性

**晶圆厂场景**：

- **代工厂（Foundry）**：多个客户共享算力，需严格隔离
- **大型IDM**：不同产品线（DRAM、NAND、Logic）独立管理
- **研发团队**：不同项目组资源独立

**隔离维度**：

- **计算资源**：GPU、CPU、内存配额
- **数据存储**：数据集、模型、特征
- **网络访问**：命名空间隔离
- **权限控制**：RBAC（基于角色的访问控制）

### Kubernetes多租户

**命名空间隔离**：

```yaml
# 客户A命名空间
apiVersion: v1
kind: Namespace
metadata:
  name: customer-a
  labels:
    customer: customer-a
    tier: premium

---
# 资源配额
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
# 网络策略
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

### RBAC权限控制

**角色定义**：

```yaml
# 数据科学家角色
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
# 角色绑定
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

**MLflow权限**：

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 创建实验（仅所有者可写）
experiment_id = client.create_experiment(
    name="customer_a_yield_model",
    artifact_location="s3://mlflow-artifacts/customer-a"
)

# 设置权限标签
client.set_experiment_tag(experiment_id, "owner", "zhang.san@fab.com")
client.set_experiment_tag(experiment_id, "team", "yield-engineering")
client.set_experiment_tag(experiment_id, "access", "private")
```

## 30.9 平台可观测性与SLO管理

### 可观测性三大支柱

**指标（Metrics）**：

- 系统指标：CPU、内存、GPU利用率
- 应用指标：请求延迟、错误率、吞吐量
- 业务指标：模型准确率、数据漂移、SLA达成率

**日志（Logs）**：

- 应用日志：训练日志、推理日志
- 审计日志：用户操作、模型变更
- 安全日志：访问记录、异常行为

**追踪（Traces）**：

- 请求链路：从API到模型推理的完整路径
- 性能分析：各阶段耗时、瓶颈定位

### SLO定义

**服务等级目标（SLO）**：

```yaml
# slo_definitions.yaml
services:
  inference_service:
    slo:
      availability: 99.99%  # 年停机<52分钟
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
      availability: 99.9%  # 年停机<8.76小时
      throughput: ">80% of baseline"
      job_completion: ">99% within SLA"
    
    slo_rules:
      - name: "job_completion"
        expr: "training_job_success_rate"
        threshold: 0.99
        duration: "7d"
```

### 监控告警

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
        summary: "推理延迟P99超过50ms"
        description: "当前P99延迟: {{ $value }}s"
    
    - alert: LowModelAccuracy
      expr: model_accuracy < 0.93
      for: 1h
      labels:
        severity: critical
      annotations:
        summary: "模型准确率低于93%"
        description: "当前准确率: {{ $value }}"
    
    - alert: DataDriftDetected
      expr: data_drift_score > 0.1
      for: 30m
      labels:
        severity: warning
      annotations:
        summary: "检测到数据漂移"
        description: "漂移分数: {{ $value }}"
```

**Grafana仪表板**：

```json
{
  "dashboard": {
    "title": "AI Platform Overview",
    "panels": [
      {
        "title": "推理延迟分布",
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
        "title": "模型准确率趋势",
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

## 30.10 平台演进路线与组织配套

### 三阶段演进路线

**阶段一：脚本化（0-6个月）**

- **特征**：
  - 手动执行训练脚本
  - 模型存储在本地文件系统
  - 无版本管理
  - 无自动化流水线

- **工具**：
  - Python脚本
  - Git（代码版本）
  - 本地Jupyter

- **适用场景**：
  - AI团队<3人
  - 模型数量<5个
  - 快速验证阶段

**阶段二：工具化（6-18个月）**

- **特征**：
  - MLflow实验管理
  - 模型注册中心
  - 基础CI/CD
  - 特征存储

- **工具**：
  - MLflow
  - DVC
  - Feast
  - Airflow
  - Triton

- **适用场景**：
  - AI团队3-10人
  - 模型数量5-20个
  - 生产环境部署

**阶段三：平台化（18-36个月）**

- **特征**：
  - 统一开发者门户
  - 自助服务
  - 完整MLOps流水线
  - 多租户隔离
  - 完善的可观测性

- **工具**：
  - Kubeflow
  - Backstage
  - 完整监控栈
  - 自动化审批流

- **适用场景**：
  - AI团队>10人
  - 模型数量>20个
  - 大规模生产环境

### 组织配套

**团队结构**：

```
AI平台团队
├─ 平台工程师（3-5人）
│  ├─ 基础设施（K8s、GPU集群）
│  ├─ MLOps工具链（MLflow、Feast）
│  └─ 开发者体验（门户、文档）
│
├─ ML工程师（5-10人）
│  ├─ 模型开发
│  ├─ 特征工程
│  └─ 实验优化
│
└─ 数据工程师（2-3人）
   ├─ 数据管道
   ├─ 数据质量
   └─ 数据治理
```

**关键角色**：

- **平台负责人**：整体架构、技术选型、团队管理
- **MLOps工程师**：CI/CD流水线、自动化部署、监控告警
- **基础设施工程师**：K8s集群、GPU管理、存储网络
- **开发者体验工程师**：门户开发、文档编写、培训支持

### 能力建设重点

**技术能力**：

- Kubernetes与容器编排
- GPU集群管理
- MLOps工具链（MLflow、Feast、Kubeflow）
- 监控与可观测性（Prometheus、Grafana）
- 安全与合规（RBAC、审计、加密）

**流程能力**：

- 实验管理最佳实践
- 模型版本治理
- CI/CD for ML
- 数据质量管理
- 故障响应与复盘

**组织能力**：

- 跨团队协作（AI团队、IT团队、业务团队）
- 知识沉淀与分享
- 培训与赋能
- 持续改进机制

---

## 本章小结

本章系统介绍了晶圆厂AI平台工程的核心组件与实施路径。核心要点：

1. **平台定位**：AI平台位于算力层与业务应用之间，承担"承上启下"的关键角色
2. **实验管理**：MLflow/W&B保障实验可复现性，避免知识流失
3. **模型治理**：模型注册中心 + 模型卡片 + 审批流，确保模型质量与合规
4. **CI/CD for ML**：数据变更触发重训练、自动化评估门禁、灰度发布
5. **特征平台**：Feast解决Training-Serving Skew，实现特征复用
6. **LLM服务**：LLM Gateway + Prompt管理 + RAG集成，支撑大模型应用
7. **开发者门户**：降低AI使用门槛，让工艺工程师也能使用AI
8. **多租户隔离**：命名空间 + 资源配额 + RBAC，保障资源公平与安全
9. **可观测性**：Metrics + Logs + Traces，SLO管理保障服务质量
10. **演进路线**：脚本化→工具化→平台化，匹配团队规模与业务需求

AI平台是AI工程化的核心载体，下一章将聚焦生产级AI运维，保障AI系统在晶圆厂的稳定、安全、高效运行。
