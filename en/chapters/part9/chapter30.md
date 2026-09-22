# Chapter 30: Wafer Fab AI Platform Engineering - MLOps, Model Governance, and Developer Experience

> **Chapter Guide**
> 
> Chapter 29 built the computing foundation, but bare metal and K8s clusters are just infrastructure. True AI engineering requires a complete set of platform capabilities: How to manage experiment reproducibility? How to govern model versions? How to build automated pipelines from data to deployment? How to enable process engineers to use AI without deep learning expertise? This chapter systematically covers the core components of AI platform engineering: experiment management, model registry, CI/CD for ML, feature platforms, LLM services, developer portals, multi-tenant isolation, observability, and platform evolution roadmap.

## 30.1 AI Platform Positioning and Layered Architecture

### Platform Position in AI Engineering

The wafer fab AI platform sits between the computing layer (Chapter 29) and business applications, playing a critical "connecting upper and lower layers" role:

```
┌─────────────────────────────────────────┐
│  Business Application Layer              │
│  Yield Prediction / Defect Detection / R2R Control / LLM Q&A │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  AI Platform Layer (Chapter Focus)       │
│  Experiment Mgmt / Model Registry / CI/CD / Feature Platform │
│  LLM Service / Developer Portal / Multi-tenant / Observability │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Computing Layer (Chapter 29)            │
│  GPU Cluster / Inference Service / Edge Node / Storage │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Data Layer (Chapter 28)                 │
│  Data Governance / Semantic Layer / Knowledge Graph / Data Lineage │
└─────────────────────────────────────────┘
```

### Platform Four-Layer Architecture

**Toolchain Layer**:

- Experiment management (MLflow/W&B)
- Model registry (MLflow Model Registry)
- Data versioning (DVC)
- Feature store (Feast)
- Workflow orchestration (Airflow/Prefect)

**Runtime Layer**:

- Training runtime (Kubeflow Training Operator)
- Inference runtime (Triton/Seldon)
- Notebook runtime (JupyterHub)
- Batch processing runtime (Spark/Ray)

**Governance Layer**:

- Multi-tenant isolation
- Permissions and auditing
- Model approval workflow
- Compliance and traceability

**Portal Layer**:

- Developer portal (Backstage)
- Model marketplace
- Dataset marketplace
- Documentation and training

### Platform Selection: Self-Built vs Commercial vs Open Source

| Solution | Representative Products | Advantages | Disadvantages | Use Case |
|----------|------------------------|------------|---------------|----------|
| Commercial platform | Databricks, SageMaker | Out-of-box, enterprise support | High cost, limited customization | Quick start, sufficient budget |
| Open source platform | Kubeflow, MLflow | Flexible, no license fees | Complex O&M, requires engineering investment | Has engineering team, needs customization |
| Hybrid solution | Kubeflow + commercial components | Balances cost and capability | Complex integration | Medium to large fabs |

**Recommended solutions**:

- **Small fabs** (<5 AI engineers): MLflow + Kubeflow + JupyterHub
- **Medium fabs** (5-20 AI engineers): Kubeflow + MLflow + Feast + Airflow
- **Large fabs** (>20 AI engineers): Databricks or self-built platform

## 30.2 Experiment Management and Reproducibility

### Why Experiment Management is Needed

Typical pain points in wafer fab AI experiments:

- **Not reproducible**: Experiment results from 3 months ago cannot be reproduced
- **Parameter chaos**: Hyperparameters, data versions, code versions scattered everywhere
- **Knowledge loss**: When engineers leave, experimental experience disappears with them
- **Duplicate work**: Different teams repeat the same experiments

### MLflow Experiment Management

**Core concepts**:

- **Experiment**: Container for a group of related runs
- **Run**: Single experiment execution
- **Parameter**: Input parameters (hyperparameters, configuration)
- **Metric**: Output metrics (accuracy, loss)
- **Artifact**: Outputs (models, charts, logs)

**Basic usage**:

```python
import mlflow

# Set experiment
mlflow.set_experiment("yield_prediction_v3")

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("model_type", "transformer")
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("batch_size", 64)
    
    # Train model
    model = train_model(train_data, val_data)
    
    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.93)
    
    # Save model
    mlflow.pytorch.log_model(model, "model")
```

**Integration with MLflow Server**:

```bash
# Start MLflow Server
mlflow server \
  --backend-store-uri postgresql://user:pass@db:5432/mlflow \
  --default-artifact-root s3://mlflow-artifacts/ \
  --host 0.0.0.0 --port 5000
```

### Weights & Biases (W&B)

**Advantages**:

- Real-time visualization of training curves
- Hyperparameter search (Sweeps)
- Team collaboration
- Report generation

**Usage example**:

```python
import wandb

# Initialize
wandb.init(
    project="yield-prediction",
    config={
        "model_type": "transformer",
        "learning_rate": 0.001,
        "batch_size": 64
    }
)

# Training loop
for epoch in range(epochs):
    train_loss = train_epoch(model)
    val_loss = validate_epoch(model)
    
    # Log metrics
    wandb.log({
        "epoch": epoch,
        "train_loss": train_loss,
        "val_loss": val_loss
    })

# Save model
wandb.save("model.pt")
```

### Experiment Reproducibility Assurance

**Code versioning**:

```python
import mlflow
import subprocess

# Log Git commit
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
mlflow.log_param("git_commit", commit)

# Log code diff
diff = subprocess.check_output(['git', 'diff']).decode()
with open("code_diff.patch", "w") as f:
    f.write(diff)
mlflow.log_artifact("code_diff.patch")
```

**Environment versioning**:

```python
import mlflow
import sys
import torch

# Log Python version
mlflow.log_param("python_version", sys.version)

# Log PyTorch version
mlflow.log_param("pytorch_version", torch.__version__)

# Log CUDA version
mlflow.log_param("cuda_version", torch.version.cuda)

# Export conda environment
import subprocess
subprocess.run(["conda", "env", "export", ">", "environment.yml"])
mlflow.log_artifact("environment.yml")
```

**Data versioning**:

```python
import mlflow
import dvc.api

# Log data version
data_url = dvc.api.get_url("data/yield_train.parquet")
mlflow.log_param("data_url", data_url)

# Log data hash
import hashlib
with open("data/yield_train.parquet", "rb") as f:
    data_hash = hashlib.md5(f.read()).hexdigest()
mlflow.log_param("data_hash", data_hash)
```

### Experiment Metadata Management

**Experiment card template**:

```yaml
experiment:
  name: "yield_prediction_v3"
  owner: "zhang.san@fab.com"
  team: "yield-engineering"
  date: "2024-03-15"
  
  objective: "Improve yield prediction accuracy to above 95%"
  
  hypothesis: |
    Use Transformer architecture to replace LSTM, combined with attention mechanism
    to capture long-range temporal dependencies, expecting 3-5% accuracy improvement
  
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
    Transformer improves accuracy by 4.2% compared to LSTM, reaching target.
    However, inference latency increased by 50%, needs optimization to meet <20ms requirement.
  
  next_steps:
    - "Model quantization (INT8) to reduce inference latency"
    - "Add data augmentation to improve generalization"
    - "A/B test to verify online effects"
```

## 30.3 Model Registry and Version Governance

### Role of Model Registry

**Core functions**:

- **Model version management**: Track all versions of models
- **Lifecycle management**: Staging → Production → Archived
- **Metadata management**: Model cards, training parameters, performance metrics
- **Approval workflow**: Review and approval before model goes online
- **Dependency tracking**: Association between models, data, and code

### MLflow Model Registry

**Register model**:

```python
import mlflow

# Register model
mlflow.register_model(
    model_uri="runs:/abc123/model",
    name="yield_predictor"
)
```

**Model lifecycle**:

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Transition to Staging
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Staging"
)

# Transition to Production
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Production"
)

# Archive
client.transition_model_version_stage(
    name="yield_predictor",
    version=1,
    stage="Archived"
)
```

**Load production model**:

```python
import mlflow.pyfunc

# Load production version
model = mlflow.pyfunc.load_model(
    model_uri="models:/yield_predictor/Production"
)

predictions = model.predict(input_data)
```

### Model Card

**Model card template**:

```markdown
# Model Card: yield_predictor_v3

## Basic Information

- **Model Name**: yield_predictor_v3
- **Version**: 3.2.1
- **Owner**: zhang.san@fab.com
- **Team**: Yield Engineering
- **Created**: 2024-03-15
- **Last Updated**: 2024-03-20

## Model Description

Transformer-based yield prediction model for predicting final wafer yield.

**Input**:
- 500-dimensional feature vector (process parameters, equipment status, environmental data)
- Sequence length: 100 steps

**Output**:
- Yield prediction value (0-100%)
- Confidence (0-1)

## Training Data

- **Dataset**: yield_train_v3
- **Sample count**: 1,000,000
- **Time range**: 2023-01-01 to 2024-02-29
- **Product coverage**: Product A, B, C
- **Equipment coverage**: Tool 1-50

## Performance Metrics

| Metric | Training Set | Validation Set | Test Set |
|--------|--------------|----------------|----------|
| Accuracy | 95.2% | 94.8% | 94.5% |
| F1 Score | 93.1% | 92.7% | 92.3% |
| MAE | 2.3% | 2.5% | 2.7% |

## Limitations and Biases

- **Applicable scope**: Only applicable to Product A/B/C, not for new products
- **Known bias**: Lower prediction accuracy for low-yield samples (<80%)
- **Data dependency**: Relies on FDC data integrity, performance degrades when missing values >10%

## Inference Performance

- **Latency**: P50=12ms, P99=25ms
- **Throughput**: Single A100 card: 800 samples/s
- **Memory usage**: 2.3GB

## Ethics and Compliance

- **Fairness**: Passed fairness audit, no significant bias across different product batches
- **Privacy**: Does not contain personally identifiable information (PII)
- **Security**: Passed security review, no sensitive information leakage risk

## Usage Instructions

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/yield_predictor/Production")
predictions = model.predict(features)
```

## Maintenance Plan

- **Retraining frequency**: Quarterly
- **Monitoring metrics**: Accuracy, latency, data drift
- **Alert thresholds**: Accuracy <93% or latency >50ms
- **Responsible person**: zhang.san@fab.com

## Change History

| Version | Date | Changes | Responsible |
|---------|------|---------|-------------|
| 3.2.1 | 2024-03-20 | Fixed data preprocessing bug | zhang.san |
| 3.2.0 | 2024-03-15 | Upgraded to Transformer architecture | zhang.san |
| 3.1.0 | 2024-02-01 | Added Product C support | li.si |
```

### Model Approval Workflow

**Approval process**:

```
Model Development → Code Review → Performance Validation → Security Review → Business Approval → Deployment
       ↓                ↓              ↓                  ↓               ↓              ↓
    Engineer        Tech Lead      QA Engineer       Security        PM/Owner        MLOps
```

**Approval checklist**:

```yaml
approval_checklist:
  code_review:
    - [ ] Code meets coding standards
    - [ ] Unit test coverage >80%
    - [ ] No security vulnerabilities (SAST scan passed)
  
  performance_validation:
    - [ ] Test set accuracy >93%
    - [ ] Inference latency P99 <50ms
    - [ ] 72-hour stability test passed
  
  security_review:
    - [ ] No sensitive data leakage
    - [ ] Model input/output validation
    - [ ] Dependency component security scan
  
  business_approval:
    - [ ] Business impact assessment
    - [ ] ROI analysis
    - [ ] Risk assessment
  
  deployment_readiness:
    - [ ] Monitoring alerts configured
    - [ ] Rollback plan
    - [ ] Documentation complete
```

## 30.4 CI/CD for ML Pipeline

### ML Pipeline vs Traditional CI/CD

**Traditional CI/CD**:

```
Code commit → Build → Test → Deploy
```

**ML CI/CD**:

```
Data change → Data validation → Model training → Model validation → Model deployment
     ↓              ↓                ↓                ↓                  ↓
  Data pipeline   Data quality    Hyperparameter    Performance        Canary
                                     search          evaluation        release
```

### Data Change Triggered Retraining

**Using Airflow orchestration**:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_data_drift():
    """Check data drift"""
    # Compare current data with training data distribution
    drift_score = calculate_drift()
    return drift_score > threshold

def retrain_model():
    """Retrain model"""
    # Load latest data
    data = load_latest_data()
    
    # Train model
    model = train_model(data)
    
    # Evaluate performance
    metrics = evaluate_model(model)
    
    # Register model
    register_model(model, metrics)

def validate_model():
    """Validate model performance"""
    # Load latest model
    model = load_latest_model()
    
    # Run test suite
    test_results = run_test_suite(model)
    
    # Check if meets SLA
    assert test_results['accuracy'] > 0.93
    assert test_results['latency_p99'] < 0.05

def deploy_model():
    """Deploy model"""
    # Canary release
    deploy_to_staging(model_version="latest")
    
    # A/B test
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

### Automated Evaluation Gates

**Evaluation metric gates**:

```python
def model_quality_gate(model_version):
    """Model quality gate"""
    model = load_model(model_version)
    
    # 1. Performance metrics
    metrics = evaluate_model(model)
    
    if metrics['accuracy'] < 0.93:
        raise ValueError(f"Accuracy {metrics['accuracy']} < 0.93")
    
    if metrics['latency_p99'] > 0.05:
        raise ValueError(f"Latency P99 {metrics['latency_p99']} > 50ms")
    
    # 2. Fairness check
    fairness_metrics = check_fairness(model)
    if fairness_metrics['max_diff'] > 0.05:
        raise ValueError(f"Fairness violation: {fairness_metrics}")
    
    # 3. Robustness test
    robustness = adversarial_test(model)
    if robustness['attack_success_rate'] > 0.01:
        raise ValueError(f"Robustness issue: {robustness}")
    
    # 4. Data drift check
    drift = check_drift(model)
    if drift['score'] > 0.1:
        raise Warning(f"Data drift detected: {drift}")
    
    return True
```

### Canary Release and A/B Testing

**Canary release strategy**:

```python
from kubernetes import client, config

def deploy_canary(model_version, percentage=0.1):
    """Canary release"""
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    
    # Deploy canary version
    canary_deployment = create_deployment(
        name=f"model-canary-{model_version}",
        image=f"model-registry:{model_version}",
        replicas=1
    )
    
    apps_v1.create_namespaced_deployment(
        namespace="production",
        body=canary_deployment
    )
    
    # Configure traffic split
    configure_traffic_split(
        stable_percentage=1 - percentage,
        canary_percentage=percentage
    )
```

**A/B test monitoring**:

```python
def monitor_ab_test(duration_hours=24):
    """Monitor A/B test results"""
    start_time = time.time()
    
    while time.time() - start_time < duration_hours * 3600:
        # Collect metrics
        stable_metrics = collect_metrics("stable")
        canary_metrics = collect_metrics("canary")
        
        # Statistical significance test
        p_value = statistical_test(stable_metrics, canary_metrics)
        
        if p_value < 0.05:
            # Significant difference
            if canary_metrics['accuracy'] > stable_metrics['accuracy']:
                # Canary is better, full release
                promote_canary()
                break
            else:
                # Canary is worse, rollback
                rollback_canary()
                break
        
        time.sleep(3600)  # Check every hour
```

## 30.5 Feature Platform and Online Feature Service

### Role of Feature Platform

**Core problem**: Training-Serving Skew

- Features used during training are inconsistent with inference
- Feature calculation logic scattered across different code
- Feature reuse is difficult, leading to duplicate development

**Feature platform solves**:

- Unified feature definition
- Offline/online consistency
- Feature reuse and sharing

### Feast Feature Store

**Architecture**:

```
┌─────────────────────────────────────────┐
│  Feature Definition (Feature Repository) │
│  feature_repo/                          │
│  ├─ features/                           │
│  │  ├─ yield_features.py                │
│  │  └─ defect_features.py               │
│  └─ feature_store.yaml                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Offline Store                          │
│  Parquet / BigQuery / Snowflake         │
│  For training                           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Online Store                           │
│  Redis / DynamoDB / Cassandra           │
│  For inference                          │
└─────────────────────────────────────────┘
```

**Feature definition example**:

```python
# feature_repo/features/yield_features.py
from feast import Feature, Entity, FeatureView, FileSource
from datetime import timedelta

# Define entity
wafer = Entity(
    name="wafer",
    description="Wafer entity",
    tags={"team": "yield"}
)

# Define data source
yield_source = FileSource(
    path="data/yield_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# Define feature view
yield_features = FeatureView(
    name="yield_features",
    entities=[wafer],
    ttl=timedelta(days=1),
    features=[
        Feature(
            name="avg_temperature",
            description="Average temperature",
            dtype=Float32
        ),
        Feature(
            name="max_pressure",
            description="Maximum pressure",
            dtype=Float32
        ),
        Feature(
            name="defect_count",
            description="Defect count",
            dtype=Int32
        ),
    ],
    source=yield_source,
    tags={"team": "yield", "version": "v3"}
)
```

**Feature registration**:

```bash
# Apply feature definitions
feast apply

# Materialize features to online store
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

**Get features during training**:

```python
from feast import FeatureStore

# Initialize Feature Store
store = FeatureStore(repo_path="feature_repo")

# Get training data
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

# Train model
model.train(training_df)
```

**Get features during inference**:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")

# Get online features
feature_vector = store.get_online_features(
    features=[
        "yield_features:avg_temperature",
        "yield_features:max_pressure",
        "yield_features:defect_count"
    ],
    entity_rows=[{"wafer": "W001"}]
).to_dict()

# Inference
prediction = model.predict(feature_vector)
```

### Feature Serving

**Low-latency feature service**:

```python
from fastapi import FastAPI
from feast import FeatureStore
import redis

app = FastAPI()
store = FeatureStore(repo_path="feature_repo")
cache = redis.Redis(host='localhost', port=6379)

@app.get("/features/{wafer_id}")
async def get_features(wafer_id: str):
    # Check cache first
    cached = cache.get(f"features:{wafer_id}")
    if cached:
        return json.loads(cached)
    
    # Get from Feature Store
    features = store.get_online_features(
        features=[
            "yield_features:avg_temperature",
            "yield_features:max_pressure",
            "yield_features:defect_count"
        ],
        entity_rows=[{"wafer": wafer_id}]
    ).to_dict()
    
    # Write to cache (TTL 5 minutes)
    cache.setex(
        f"features:{wafer_id}",
        300,
        json.dumps(features)
    )
    
    return features
```

## 30.6 LLM/Agent Service Platform

### LLM Service Architecture

**Core components**:

```
┌─────────────────────────────────────────┐
│  LLM Gateway                            │
│  ├─ Request routing (multi-model load balancing) │
│  ├─ Rate limiting and quotas            │
│  ├─ Audit logs (request/response records)│
│  └─ Cost tracking (token usage statistics)│
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Model Service Layer                    │
│  ├─ Local models (vLLM/TGI)             │
│  ├─ Cloud APIs (OpenAI/Claude/Qwen)     │
│  └─ Specialized models (Embedding/Reranker)│
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  RAG/Agent Layer                        │
│  ├─ GraphRAG (Chapter 28 knowledge graph)│
│  ├─ Vector RAG (vector retrieval)       │
│  ├─ Prompt template management          │
│  └─ Agent toolchain                     │
└─────────────────────────────────────────┘
```

### LLM Gateway Implementation

**Request routing and load balancing**:

```python
from fastapi import FastAPI, Request
import httpx
import asyncio

app = FastAPI()

# Model configuration
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

# Load balancer
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
    
    # Get load balancer
    lb = load_balancers.get(model)
    if not lb:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")
    
    # Select endpoint
    endpoint = await lb.get_endpoint()
    
    # Forward request
    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json=body,
            headers={"Authorization": f"Bearer {get_api_key(model)}"}
        )
        
        # Log audit
        log_request(request, response, model)
        
        return response.json()
```

### Prompt Template Management

**Template storage**:

```python
# prompt_templates/yield_analysis.yaml
templates:
  yield_root_cause:
    system: |
      You are a wafer fab yield analysis expert. Based on the provided data, analyze the root cause of yield decline.
      
      Analysis framework:
      1. Data overview: Yield trends, abnormal batches
      2. Equipment correlation: Which equipment is related to yield decline
      3. Process parameters: Deviations in key parameters
      4. Environmental factors: Temperature, humidity, cleanliness, etc.
      5. Root cause: Comprehensive analysis conclusion
      6. Recommended measures: Improvement suggestions
    
    user: |
      Please analyze the following yield data:
      
      Product: {product}
      Time range: {time_range}
      Yield trend: {yield_trend}
      
      Equipment data:
      {equipment_data}
      
      Process parameters:
      {process_params}
      
      Please provide detailed root cause analysis and improvement suggestions.
    
    variables:
      - product
      - time_range
      - yield_trend
      - equipment_data
      - process_params
```

**Template service**:

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

### RAG Service Integration

**GraphRAG + Vector RAG hybrid retrieval**:

```python
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings

class HybridRAGService:
    def __init__(self):
        self.graph_retriever = GraphRAGRetriever()  # Chapter 28 knowledge graph
        self.vector_retriever = VectorRetriever()   # Vector retrieval
        self.llm = ChatOpenAI(model="gpt-4")
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. GraphRAG retrieval (structured knowledge)
        graph_docs = self.graph_retriever.retrieve(query, top_k=top_k)
        
        # 2. Vector RAG retrieval (unstructured documents)
        vector_docs = self.vector_retriever.retrieve(query, top_k=top_k)
        
        # 3. Fusion ranking
        combined = self.rerank(graph_docs + vector_docs, query)
        
        return combined[:top_k]
    
    def query(self, query: str):
        # Retrieve relevant documents
        docs = self.retrieve(query)
        
        # Build prompt
        context = "\n\n".join([doc.content for doc in docs])
        prompt = f"""
        Answer the question based on the following context:
        
        {context}
        
        Question: {query}
        
        Answer:
        """
        
        # Call LLM
        response = self.llm.invoke(prompt)
        
        return {
            "answer": response.content,
            "sources": [doc.metadata for doc in docs]
        }
```

## 30.7 Developer Portal and Self-Service

### Role of Developer Portal

**Core goal**: Lower AI usage barriers, enabling process engineers to use AI without deep learning expertise.

**Key features**:

- **Model marketplace**: Browse, trial, deploy models
- **Dataset marketplace**: Discover, request, use datasets
- **Notebook environment**: One-click Jupyter environment launch
- **Documentation and training**: Tutorials, best practices, API documentation
- **Community and collaboration**: Q&A, code sharing, experience exchange

### Backstage Developer Portal

**Architecture**:

```
┌─────────────────────────────────────────┐
│  Backstage Portal                       │
│  ├─ Model marketplace plugin            │
│  ├─ Dataset marketplace plugin          │
│  ├─ Notebook launcher                   │
│  ├─ Documentation site                  │
│  └─ Community forum                     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Backend services                       │
│  ├─ MLflow API (models/experiments)     │
│  ├─ Feast API (features)                │
│  ├─ DVC API (data)                      │
│  └─ JupyterHub API (Notebook)           │
└─────────────────────────────────────────┘
```

**Model marketplace page**:

```tsx
// src/components/ModelMarket.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Button } from '@material-ui/core';

export const ModelMarket = () => {
  const [models, setModels] = useState([]);
  
  useEffect(() => {
    // Get model list from MLflow
    fetch('/api/mlflow/models')
      .then(res => res.json())
      .then(data => setModels(data));
  }, []);
  
  return (
    <div>
      <Typography variant="h4">Model Marketplace</Typography>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {models.map(model => (
          <Card key={model.name}>
            <CardContent>
              <Typography variant="h6">{model.name}</Typography>
              <Typography variant="body2" color="textSecondary">
                Version: {model.version}
              </Typography>
              <Typography variant="body2">
                Accuracy: {(model.metrics.accuracy * 100).toFixed(2)}%
              </Typography>
              <Typography variant="body2">
                Owner: {model.owner}
              </Typography>
              <Button variant="contained" color="primary">
                Try
              </Button>
              <Button variant="outlined">
                Details
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
```

### Notebook Environment

**JupyterHub deployment**:

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

**One-click Notebook launch**:

```python
# notebooks/yield_analysis_template.ipynb
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# Yield Analysis Template\n",
        "\n",
        "This Notebook provides a standard workflow for yield analysis."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# Import libraries\n",
        "import pandas as pd\n",
        "import mlflow\n",
        "from feast import FeatureStore\n",
        "\n",
        "# Connect to MLflow\n",
        "mlflow.set_tracking_uri('https://mlflow.fab.com')\n",
        "\n",
        "# Connect to Feature Store\n",
        "store = FeatureStore(repo_path='/home/jovyan/feature_repo')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "source": [
        "# Load data\n",
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

## 30.8 Multi-Tenant Isolation and Permission System

### Necessity of Multi-Tenant Isolation

**Wafer fab scenarios**:

- **Foundry**: Multiple customers share computing power, requiring strict isolation
- **Large IDM**: Different product lines (DRAM, NAND, Logic) managed independently
- **R&D teams**: Different project teams have independent resources

**Isolation dimensions**:

- **Computing resources**: GPU, CPU, memory quotas
- **Data storage**: Datasets, models, features
- **Network access**: Namespace isolation
- **Permission control**: RBAC (Role-Based Access Control)

### Kubernetes Multi-Tenancy

**Namespace isolation**:

```yaml
# Customer A namespace
apiVersion: v1
kind: Namespace
metadata:
  name: customer-a
  labels:
    customer: customer-a
    tier: premium

---
# Resource quota
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
# Network policy
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

### RBAC Permission Control

**Role definition**:

```yaml
# Data scientist role
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
# Role binding
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

**MLflow permissions**:

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Create experiment (only owner can write)
experiment_id = client.create_experiment(
    name="customer_a_yield_model",
    artifact_location="s3://mlflow-artifacts/customer-a"
)

# Set permission tags
client.set_experiment_tag(experiment_id, "owner", "zhang.san@fab.com")
client.set_experiment_tag(experiment_id, "team", "yield-engineering")
client.set_experiment_tag(experiment_id, "access", "private")
```

## 30.9 Platform Observability and SLO Management

### Three Pillars of Observability

**Metrics**:

- System metrics: CPU, memory, GPU utilization
- Application metrics: Request latency, error rate, throughput
- Business metrics: Model accuracy, data drift, SLA achievement rate

**Logs**:

- Application logs: Training logs, inference logs
- Audit logs: User operations, model changes
- Security logs: Access records, abnormal behavior

**Traces**:

- Request traces: Complete path from API to model inference
- Performance analysis: Time spent in each stage, bottleneck identification

### SLO Definition

**Service Level Objectives (SLO)**:

```yaml
# slo_definitions.yaml
services:
  inference_service:
    slo:
      availability: 99.99%  # Annual downtime <52 minutes
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
      availability: 99.9%  # Annual downtime <8.76 hours
      throughput: ">80% of baseline"
      job_completion: ">99% within SLA"
    
    slo_rules:
      - name: "job_completion"
        expr: "training_job_success_rate"
        threshold: 0.99
        duration: "7d"
```

### Monitoring Alerts

**Prometheus + Grafana**:

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
        summary: "Inference latency P99 exceeds 50ms"
        description: "Current P99 latency: {{ $value }}s"
    
    - alert: LowModelAccuracy
      expr: model_accuracy < 0.93
      for: 1h
      labels:
        severity: critical
      annotations:
        summary: "Model accuracy below 93%"
        description: "Current accuracy: {{ $value }}"
    
    - alert: DataDriftDetected
      expr: data_drift_score > 0.1
      for: 30m
      labels:
        severity: warning
      annotations:
        summary: "Data drift detected"
        description: "Drift score: {{ $value }}"
```

**Grafana dashboard**:

```json
{
  "dashboard": {
    "title": "AI Platform Overview",
    "panels": [
      {
        "title": "Inference Latency Distribution",
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
        "title": "Model Accuracy Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "model_accuracy",
            "legendFormat": "{{model_name}}"
          }
        ]
      },
      {
        "title": "GPU Utilization",
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

## 30.10 Platform Evolution Roadmap and Organizational Support

### Three-Stage Evolution Roadmap

**Stage 1: Script-based (0-6 months)**

- **Characteristics**:
  - Manual execution of training scripts
  - Models stored in local file system
  - No version management
  - No automated pipelines

- **Tools**:
  - Python scripts
  - Git (code versioning)
  - Local Jupyter

- **Use cases**:
  - AI team <3 people
  - Model count <5
  - Rapid validation stage

**Stage 2: Tool-based (6-18 months)**

- **Characteristics**:
  - MLflow experiment management
  - Model registry
  - Basic CI/CD
  - Feature store

- **Tools**:
  - MLflow
  - DVC
  - Feast
  - Airflow
  - Triton

- **Use cases**:
  - AI team 3-10 people
  - Model count 5-20
  - Production environment deployment

**Stage 3: Platform-based (18-36 months)**

- **Characteristics**:
  - Unified developer portal
  - Self-service
  - Complete MLOps pipeline
  - Multi-tenant isolation
  - Comprehensive observability

- **Tools**:
  - Kubeflow
  - Backstage
  - Complete monitoring stack
  - Automated approval workflows

- **Use cases**:
  - AI team >10 people
  - Model count >20
  - Large-scale production environment

### Organizational Support

**Team structure**:

```
AI Platform Team
├─ Platform Engineers (3-5 people)
│  ├─ Infrastructure (K8s, GPU clusters)
│  ├─ MLOps toolchain (MLflow, Feast)
│  └─ Developer experience (portal, documentation)
│
├─ ML Engineers (5-10 people)
│  ├─ Model development
│  ├─ Feature engineering
│  └─ Experiment optimization
│
└─ Data Engineers (2-3 people)
   ├─ Data pipelines
   ├─ Data quality
   └─ Data governance
```

**Key roles**:

- **Platform lead**: Overall architecture, technology selection, team management
- **MLOps engineer**: CI/CD pipelines, automated deployment, monitoring alerts
- **Infrastructure engineer**: K8s clusters, GPU management, storage networking
- **Developer experience engineer**: Portal development, documentation writing, training support

### Capability Building Focus

**Technical capabilities**:

- Kubernetes and container orchestration
- GPU cluster management
- MLOps toolchain (MLflow, Feast, Kubeflow)
- Monitoring and observability (Prometheus, Grafana)
- Security and compliance (RBAC, auditing, encryption)

**Process capabilities**:

- Experiment management best practices
- Model version governance
- CI/CD for ML
- Data quality management
- Incident response and post-mortem

**Organizational capabilities**:

- Cross-team collaboration (AI team, IT team, business team)
- Knowledge accumulation and sharing
- Training and enablement
- Continuous improvement mechanisms

---

## Chapter Summary

This chapter systematically introduced the core components and implementation paths of wafer fab AI platform engineering. Key points:

1. **Platform positioning**: AI platform sits between computing layer and business applications, playing a critical "connecting upper and lower layers" role
2. **Experiment management**: MLflow/W&B ensures experiment reproducibility, preventing knowledge loss
3. **Model governance**: Model registry + model cards + approval workflow ensures model quality and compliance
4. **CI/CD for ML**: Data change triggers retraining, automated evaluation gates, canary release
5. **Feature platform**: Feast solves Training-Serving Skew, enabling feature reuse
6. **LLM service**: LLM Gateway + Prompt management + RAG integration supports large model applications
7. **Developer portal**: Lowers AI usage barriers, enabling process engineers to use AI
8. **Multi-tenant isolation**: Namespace + resource quotas + RBAC ensures fair and secure resource allocation
9. **Observability**: Metrics + Logs + Traces, SLO management ensures service quality
10. **Evolution roadmap**: Script-based → Tool-based → Platform-based, matching team size and business needs

AI platform is the core carrier of AI engineering. The next chapter will focus on production-grade AI operations, ensuring stable, secure, and efficient operation of AI systems in wafer fabs.
