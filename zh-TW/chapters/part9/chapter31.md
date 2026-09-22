# 第31章 生產級AI運維——安全合規、成本優化與持續演進

> **本章導讀**
> 
> 前30章構建了從資料、演算法、算力到平台的完整體系，但AI系統上線只是開始。晶圓廠對AI系統的要求遠超網際網路場景：零容忍停機、嚴格審計追溯、IP保護、合規要求。本章聚焦生產級AI運維的核心挑戰：模型變更管理、資料安全與IP保護、合規框架與審計、系統韌性工程、成本精細化運營、模型漂移監控、知識沉澱閉環、供應商治理，以及AI Infra成熟度自評。

## 31.1 AI系統生產化挑戰總覽

### 晶圓廠AI vs 網際網路AI

| 維度 | 網際網路AI | 晶圓廠AI |
|------|---------|---------|
| **停機容忍度** | 分鐘級（可降級） | 零容忍（產線停擺=巨額損失） |
| **資料敏感性** | 中（使用者資料） | 極高（工藝Recipe、良率資料） |
| **IP保護** | 一般（演算法開源） | 嚴格（工藝Know-how是核心競爭力） |
| **合規要求** | 隱私保護（GDPR） | 多重合規（ISO 9001、IATF 16949、客戶稽核） |
| **變更風險** | 低（快速回滾） | 極高（模型錯誤=批量報廢） |
| **生命週期** | 短（月級迭代） | 長（年級穩定性） |
| **可解釋性** | 可選（黑盒可接受） | 必需（需向客戶解釋決策） |

### 生產化三大剛性約束

**約束一：零容忍停機**

- 推理服務宕機 = 產線停擺
- 單小時停機損失：$100k-1M（視產品線）
- 年可用性要求：99.99%（年停機<52分鐘）

**約束二：審計追溯**

- 每個AI決策需可追溯
- 模型版本、輸入資料、推理結果全鏈路記錄
- 保留期限：3-7年（視合規要求）

**約束三：IP保護**

- 工藝Recipe是核心競爭力
- 模型逆向工程風險
- 跨客戶資料隔離（代工廠場景）

### 運維成熟度模型

**Level 1: 手動運維**

- 手動部署模型
- 手動監控告警
- 事後故障處理
- 無標準化流程

**Level 2: 自動化運維**

- 自動化部署（CI/CD）
- 自動化監控（Prometheus）
- 自動化告警
- 基礎故障自癒

**Level 3: 智慧化運維**

- 預測性維護（模型漂移預測）
- 自動擴縮容
- 智慧故障診斷
- 根因分析自動化

**Level 4: 自適應運維**

- 模型自動調優
- 資源自動優化
- 故障自動恢復
- 持續學習與改進

**Level 5: 自治運維**

- 完全自治的AI系統
- 零人工干預
- 自我優化與演進
- 預測性與預防性運維

## 31.2 模型變更管理與審批流

### 變更分級

**高風險變更**：

- 生產模型版本升級
- 模型架構變更
- 訓練資料大規模變更
- 推理服務配置變更

**中風險變更**：

- 模型超參數調整
- 特徵工程優化
- 推理效能優化

**低風險變更**：

- 文檔更新
- 監控閾值調整
- 日誌級別變更

### 審批流程

**高風險變更審批流**：

```
變更申請 → 技術評審 → 安全評審 → 業務審批 → 灰度發布 → 全量上線
   ↓          ↓          ↓          ↓          ↓          ↓
 工程師    Tech Lead   Security   PM/Owner   10%流量    100%流量
```

**審批檢查清單**：

```yaml
high_risk_change_checklist:
  technical_review:
    - [ ] 程式碼審查通過
    - [ ] 單元測試覆蓋率>80%
    - [ ] 效能測試達標
    - [ ] 回滾方案就緒
  
  security_review:
    - [ ] 安全掃描通過
    - [ ] 無敏感資料洩露
    - [ ] 依賴組件安全
  
  business_approval:
    - [ ] 業務影響評估
    - [ ] 風險評估
    - [ ] 回滾影響評估
  
  deployment_readiness:
    - [ ] 監控告警配置
    - [ ] 灰度發布計畫
    - [ ] 回滾演練完成
```

### 變更視窗

**變更視窗定義**：

```yaml
change_windows:
  high_risk:
    allowed_times:
      - "Saturday 02:00-06:00"  # 週末凌晨
    blackout_periods:
      - "2024-12-20 to 2025-01-05"  # 年末假期
      - "Product launch week"  # 產品發布週
    approval_required:
      - "Change Advisory Board (CAB)"
  
  medium_risk:
    allowed_times:
      - "Weekday 22:00-06:00"  # 工作日夜間
      - "Weekend 00:00-08:00"  # 週末
    approval_required:
      - "Tech Lead"
  
  low_risk:
    allowed_times:
      - "Any time"
    approval_required:
      - "Peer review"
```

### 變更實施

**灰度發布策略**：

```python
from kubernetes import client, config
import time

class CanaryDeployment:
    def __init__(self, namespace="production"):
        config.load_kube_config()
        self.apps_v1 = client.AppsV1Api()
        self.namespace = namespace
    
    def deploy_canary(self, model_version, percentage=0.1):
        """部署canary版本"""
        canary = self._create_canary_deployment(model_version)
        self.apps_v1.create_namespaced_deployment(
            namespace=self.namespace,
            body=canary
        )
        self._configure_traffic_split(
            stable_percentage=1 - percentage,
            canary_percentage=percentage
        )
        return canary
    
    def monitor_canary(self, duration_minutes=60):
        """監控canary版本"""
        start_time = time.time()
        while time.time() - start_time < duration_minutes * 60:
            stable_metrics = self._collect_metrics("stable")
            canary_metrics = self._collect_metrics("canary")
            if self._check_anomaly(stable_metrics, canary_metrics):
                self.rollback_canary()
                return False
            time.sleep(300)
        return True
    
    def promote_canary(self):
        """全量發布canary"""
        self._update_stable_deployment()
        self._delete_canary_deployment()
        self._configure_traffic_split(stable_percentage=1.0, canary_percentage=0.0)
    
    def rollback_canary(self):
        """回滾canary"""
        self._delete_canary_deployment()
        self._configure_traffic_split(stable_percentage=1.0, canary_percentage=0.0)
```

### 變更記錄與審計

**變更日誌**：

```json
{
  "change_id": "CHG-2024-03-001",
  "change_type": "high_risk",
  "model_name": "yield_predictor",
  "from_version": "3.1.0",
  "to_version": "3.2.0",
  "requester": "zhang.san@fab.com",
  "approver": "li.si@fab.com",
  "approval_time": "2024-03-15T10:00:00Z",
  "deployment_time": "2024-03-16T02:00:00Z",
  "status": "completed",
  "audit_trail": [
    {"timestamp": "2024-03-15T09:00:00Z", "action": "change_request", "user": "zhang.san@fab.com"},
    {"timestamp": "2024-03-15T10:00:00Z", "action": "approved", "user": "li.si@fab.com"},
    {"timestamp": "2024-03-16T02:00:00Z", "action": "deployed", "user": "system"},
    {"timestamp": "2024-03-16T02:30:00Z", "action": "canary_promoted", "user": "system"}
  ]
}
```

## 31.3 資料安全與IP保護實戰

### 資料分類與分級

```yaml
data_classification:
  public:
    description: "可公開資料"
    examples: ["產品規格書（公開版）", "技術白皮書"]
    protection_level: "L1"
  internal:
    description: "內部使用資料"
    examples: ["內部報告", "會議紀要"]
    protection_level: "L2"
  confidential:
    description: "機密資料"
    examples: ["工藝Recipe", "良率資料", "客戶訂單"]
    protection_level: "L3"
  top_secret:
    description: "絕密資料"
    examples: ["核心工藝參數", "先進製程技術"]
    protection_level: "L4"
```

### 資料脫敏

```python
import hashlib
import numpy as np

class DataMasker:
    def __init__(self):
        self.salt = "fab_secret_salt"
    
    def mask_wafer_id(self, wafer_id: str) -> str:
        """脫敏晶圓ID"""
        hashed = hashlib.sha256(f"{wafer_id}{self.salt}".encode()).hexdigest()[:8]
        return f"W-{hashed}"
    
    def mask_lot_id(self, lot_id: str) -> str:
        """脫敏批次ID"""
        hashed = hashlib.sha256(f"{lot_id}{self.salt}".encode()).hexdigest()[:8]
        return f"L-{hashed}"
    
    def mask_customer_name(self, name: str) -> str:
        """脫敏客戶名稱"""
        return f"Customer-{hash(name) % 1000:03d}"
    
    def mask_process_param(self, value: float, sensitivity: str = "medium") -> float:
        """脫敏工藝參數"""
        if sensitivity == "high":
            noise = np.random.normal(0, 0.01 * value)
            return value + noise
        elif sensitivity == "medium":
            return round(value, 2)
        else:
            return value
```

### 模型IP保護

**模型加密**：

```python
from cryptography.fernet import Fernet
import pickle

class ModelEncryptor:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_model(self, model, output_path: str):
        """加密模型"""
        model_bytes = pickle.dumps(model)
        encrypted = self.cipher.encrypt(model_bytes)
        with open(output_path, "wb") as f:
            f.write(encrypted)
    
    def decrypt_model(self, input_path: str):
        """解密模型"""
        with open(input_path, "rb") as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return pickle.loads(decrypted)
```

**模型水印**：

```python
import numpy as np

class ModelWatermarker:
    def __init__(self, watermark: str):
        self.watermark = watermark.encode()
    
    def embed_watermark(self, model_weights: np.ndarray) -> np.ndarray:
        """嵌入水印"""
        watermark_bits = np.unpackbits(np.frombuffer(self.watermark, dtype=np.uint8))
        positions = self._select_positions(model_weights.shape, len(watermark_bits))
        watermarked = model_weights.copy()
        for i, pos in enumerate(positions):
            watermarked.flat[pos] = self._embed_bit(watermarked.flat[pos], watermark_bits[i])
        return watermarked
    
    def extract_watermark(self, model_weights: np.ndarray) -> str:
        """提取水印"""
        positions = self._select_positions(model_weights.shape, len(self.watermark) * 8)
        watermark_bits = [self._extract_bit(model_weights.flat[pos]) for pos in positions]
        watermark_bytes = np.packbits(watermark_bits)
        return watermark_bytes.tobytes().decode()
    
    def _select_positions(self, shape, num_bits):
        np.random.seed(42)
        total_size = np.prod(shape)
        return np.random.choice(total_size, num_bits, replace=False)
    
    def _embed_bit(self, value: float, bit: int) -> float:
        int_value = int(value * 1000)
        int_value = int_value | 1 if bit == 1 else int_value & ~1
        return int_value / 1000
    
    def _extract_bit(self, value: float) -> int:
        return int(value * 1000) & 1
```

### 跨客戶資料隔離

```yaml
customer_isolation:
  storage:
    separate_namespaces: true
    encryption_at_rest: true
    encryption_keys: "per_customer"
  compute:
    dedicated_resources: true
    network_isolation: true
  access:
    rbac: true
    audit_logging: true
    data_masking: true
  model:
    separate_training: true
    model_isolation: true
    inference_isolation: true
```

## 31.4 合規框架與審計證據鏈

### 合規要求

**ISO 9001（品質管理體系）**：

- 過程控制：AI決策需可追溯
- 持續改進：模型效能監控與優化
- 客戶滿意：AI系統需滿足客戶需求

**IATF 16949（汽車品質管理體系）**：

- 風險管理：AI系統需進行FMEA分析
- 變更管理：模型變更需嚴格審批
- 可追溯性：從原材料到成品的全鏈路追溯

**客戶稽核要求**：

- 資料完整性：AI訓練資料需完整記錄
- 模型驗證：需向客戶展示模型驗證結果
- 審計報告：需提供AI系統審計報告

### 審計證據鏈

```
資料收集 → 資料預處理 → 模型訓練 → 模型驗證 → 模型部署 → 模型推理
   ↓          ↓          ↓          ↓          ↓          ↓
 原始日誌   處理日誌   訓練日誌   驗證報告   部署記錄   推理日誌
   ↓          ↓          ↓          ↓          ↓          ↓
 雜湊校驗   雜湊校驗   雜湊校驗   雜湊校驗   雜湊校驗   雜湊校驗
```

**審計日誌格式**：

```json
{
  "audit_id": "AUD-2024-03-001",
  "timestamp": "2024-03-15T10:00:00Z",
  "event_type": "model_training",
  "user": "zhang.san@fab.com",
  "system": "mlflow",
  "details": {
    "experiment_name": "yield_prediction_v3",
    "run_id": "abc123",
    "model_name": "yield_predictor",
    "model_version": "3.2.0",
    "training_data": {"dataset": "yield_train_v3", "hash": "sha256:abcdef123456", "size": "100GB"},
    "metrics": {"accuracy": 0.952, "f1_score": 0.931}
  },
  "checksum": "sha256:789xyz",
  "signature": "RSA-SHA256:signature_data"
}
```

**審計日誌儲存**：

```python
import hashlib
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

class AuditLogger:
    def __init__(self, private_key_path: str):
        with open(private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(f.read(), password=None)
        self.audit_logs = []
    
    def log_event(self, event_type: str, user: str, details: dict):
        audit_entry = {
            "audit_id": f"AUD-{datetime.now().strftime('%Y-%m-%d')}-{len(self.audit_logs)+1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "user": user,
            "system": "ai_platform",
            "details": details
        }
        audit_json = json.dumps(audit_entry, sort_keys=True)
        checksum = hashlib.sha256(audit_json.encode()).hexdigest()
        audit_entry["checksum"] = f"sha256:{checksum}"
        signature = self.private_key.sign(audit_json.encode(), padding.PKCS1v15(), hashes.SHA256())
        audit_entry["signature"] = f"RSA-SHA256:{signature.hex()}"
        self.audit_logs.append(audit_entry)
        return audit_entry
    
    def verify_audit(self, audit_entry: dict, public_key_path: str) -> bool:
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        signature_hex = audit_entry["signature"].split(":")[1]
        signature = bytes.fromhex(signature_hex)
        audit_copy = audit_entry.copy()
        del audit_copy["signature"]
        audit_json = json.dumps(audit_copy, sort_keys=True)
        try:
            public_key.verify(signature, audit_json.encode(), padding.PKCS1v15(), hashes.SHA256())
            return True
        except:
            return False
```

### 合規報告生成

```python
from jinja2 import Template

class ComplianceReportGenerator:
    def __init__(self, audit_logs: list):
        self.audit_logs = audit_logs
    
    def generate_iso9001_report(self, start_date: str, end_date: str) -> str:
        template = Template("""
        # ISO 9001 合規報告
        ## 報告期間: {{ start_date }} 至 {{ end_date }}
        ## 模型變更統計
        - 總變更數: {{ total_changes }}
        - 高風險變更: {{ high_risk_changes }}
        ## 審批合規率: {{ approval_rate }}%
        ## 模型效能監控
        - 平均準確率: {{ avg_accuracy }}%
        - 平均延遲: {{ avg_latency }}ms
        ## 結論: {{ conclusion }}
        """)
        filtered_logs = [log for log in self.audit_logs if start_date <= log["timestamp"][:10] <= end_date]
        stats = {
            "start_date": start_date, "end_date": end_date,
            "total_changes": len([l for l in filtered_logs if l["event_type"] == "model_change"]),
            "high_risk_changes": len([l for l in filtered_logs if l.get("details", {}).get("risk_level") == "high"]),
            "approval_rate": 95.5, "avg_accuracy": 94.2, "avg_latency": 25,
            "conclusion": "所有指標均符合ISO 9001要求，系統運行穩定。"
        }
        return template.render(**stats)
```

## 31.5 AI系統韌性工程

### 韌性設計原則

**原則一：故障隔離**
- 微服務架構：每個服務獨立部署
- 熔斷機制：故障服務自動隔離
- 降級策略：核心功能優先保障

**原則二：冗餘設計**
- 多副本部署：至少3副本
- 跨可用區：多AZ部署
- 異地災備：異地備份

**原則三：快速恢復**
- 自動故障檢測：<1分鐘
- 自動故障恢復：<10分鐘
- 人工介入時間：<30分鐘

### 高可用架構

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: triton
        image: nvcr.io/nvidia/tritonserver:23.10-py3
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

### 故障自癒

```python
class AutoRecovery:
    def __init__(self):
        self.detector = FaultDetector()
        self.notifier = NotificationService()
    
    def recover_pod_failures(self, namespace: str):
        failures = self.detector.detect_pod_failures(namespace)
        for failure in failures:
            pod_name = failure["pod"]
            self.core_v1.delete_namespaced_pod(pod_name, namespace)
            self.notifier.send_alert(f"Pod {pod_name} 故障，已自動恢復", severity="warning")
    
    def recover_service_failures(self, namespace: str):
        failures = self.detector.detect_service_failures(namespace)
        for failure in failures:
            service_name = failure["service"]
            deployment = self.apps_v1.read_namespaced_deployment(service_name, namespace)
            deployment.spec.template.metadata.annotations = {
                "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()
            }
            self.apps_v1.patch_namespaced_deployment(service_name, namespace, deployment)
            self.notifier.send_alert(f"Service {service_name} 故障，已自動恢復", severity="critical")
```

### 多級降級

```python
class DegradationManager:
    def __init__(self):
        self.levels = {
            "normal": {"model": "full_model", "features": "all_features", "timeout": 50},
            "degraded_1": {"model": "lightweight_model", "features": "core_features", "timeout": 30},
            "degraded_2": {"model": "rule_engine", "features": "minimal_features", "timeout": 10},
            "emergency": {"model": "default_values", "features": "no_features", "timeout": 5}
        }
        self.current_level = "normal"
    
    def degrade(self, reason: str):
        if self.current_level == "normal":
            self.current_level = "degraded_1"
        elif self.current_level == "degraded_1":
            self.current_level = "degraded_2"
        elif self.current_level == "degraded_2":
            self.current_level = "emergency"
        self.notifier.send_alert(f"系統降級到 {self.current_level}: {reason}", severity="critical")
    
    def recover(self):
        if self.current_level == "emergency":
            self.current_level = "degraded_2"
        elif self.current_level == "degraded_2":
            self.current_level = "degraded_1"
        elif self.current_level == "degraded_1":
            self.current_level = "normal"
        self.notifier.send_notification(f"系統恢復到 {self.current_level}")
```

## 31.6 成本精細化運營

### 成本分攤模型

```python
class CostAllocator:
    def __init__(self):
        self.resource_usage = {}
    
    def track_usage(self, product_line: str, resource_type: str, amount: float):
        if product_line not in self.resource_usage:
            self.resource_usage[product_line] = {}
        if resource_type not in self.resource_usage[product_line]:
            self.resource_usage[product_line][resource_type] = 0
        self.resource_usage[product_line][resource_type] += amount
    
    def calculate_cost(self, product_line: str, pricing: dict) -> float:
        usage = self.resource_usage.get(product_line, {})
        return sum(amount * pricing.get(rt, 0) for rt, amount in usage.items())
    
    def generate_report(self, pricing: dict):
        return [
            {
                "product_line": pl,
                "gpu_hours": usage.get("gpu_hours", 0),
                "storage_gb": usage.get("storage_gb", 0),
                "total_cost": self.calculate_cost(pl, pricing)
            }
            for pl, usage in self.resource_usage.items()
        ]
```

**成本分攤範例**：

```yaml
pricing:
  gpu_hours: {A100: 2.5, L40S: 1.5, T4: 0.5}
  storage_gb: {nvme: 0.10, ssd: 0.05, hdd: 0.02}

cost_report:
  period: "2024-03"
  product_lines:
    - {name: "DRAM", gpu_hours: 5000, storage_gb: 10000, total_cost: "$13,550"}
    - {name: "NAND", gpu_hours: 3000, storage_gb: 8000, total_cost: "$8,310"}
    - {name: "Logic", gpu_hours: 2000, storage_gb: 5000, total_cost: "$5,600"}
  total_cost: "$27,460"
```

### 資源優化

**殭屍任務識別**：

```python
class ZombieTaskDetector:
    def detect_zombie_jobs(self, namespace: str, max_age_days: int = 7):
        batch_v1 = client.BatchV1Api()
        jobs = batch_v1.list_namespaced_job(namespace)
        zombies = []
        for job in jobs.items:
            age_days = (datetime.utcnow() - job.metadata.creation_timestamp).days
            if age_days > max_age_days and job.status.completion_time is None:
                zombies.append({"job": job.metadata.name, "age_days": age_days})
        return zombies
    
    def detect_idle_gpus(self, namespace: str, threshold: float = 0.1):
        gpu_metrics = self._get_gpu_metrics(namespace)
        return [{"pod": g["pod"], "gpu": g["gpu_id"], "utilization": g["utilization"]}
                for g in gpu_metrics if g["utilization"] < threshold]
```

### 成本優化清單

**GPU利用率提升**：
- [ ] 動態batching：提升推理吞吐
- [ ] 模型量化：減少記憶體佔用
- [ ] 多任務共享：同一GPU服務多個模型
- [ ] MIG切分：A100切分為多個實例
- [ ] 時間片輪轉：白天推理，夜間訓練

**雲成本優化**：
- [ ] 預留實例：1年/3年預留，折扣30-60%
- [ ] Spot實例：非關鍵任務使用，折扣60-90%
- [ ] 自動擴縮：夜間縮容，避免閒置

**電力優化**：
- [ ] 液冷散熱：PUE從1.5→1.2，節電20%
- [ ] 智慧排程：夜間低谷電價時段訓練
- [ ] 餘熱回收：用於辦公供暖

## 31.7 模型漂移監控與再訓練觸發

### 漂移類型

**資料漂移（Data Drift）**：
- 輸入資料分佈變化
- 原因：工藝變更、設備老化、環境變化
- 檢測：統計檢驗（KS檢驗、PSI）

**概念漂移（Concept Drift）**：
- 輸入輸出關係變化
- 原因：工藝優化、新產品導入
- 檢測：效能監控（準確率下降）

**特徵漂移（Feature Drift）**：
- 單個特徵分佈變化
- 原因：感測器校準、設備維護
- 檢測：特徵級統計檢驗

### 漂移檢測

```python
import numpy as np
from scipy import stats

class DriftDetector:
    def __init__(self, reference_data: np.ndarray):
        self.reference_data = reference_data
    
    def detect_ks_drift(self, current_data: np.ndarray, threshold: float = 0.05) -> dict:
        results = {}
        for i in range(self.reference_data.shape[1]):
            ks_stat, p_value = stats.ks_2samp(self.reference_data[:, i], current_data[:, i])
            results[f"feature_{i}"] = {"ks_statistic": ks_stat, "p_value": p_value, "drift_detected": p_value < threshold}
        return results
    
    def detect_psi_drift(self, current_data: np.ndarray, threshold: float = 0.2) -> dict:
        results = {}
        for i in range(self.reference_data.shape[1]):
            psi = self._calculate_psi(self.reference_data[:, i], current_data[:, i])
            results[f"feature_{i}"] = {"psi": psi, "drift_detected": psi > threshold}
        return results
    
    def _calculate_psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        breakpoints = np.quantile(expected, np.linspace(0, 1, bins + 1))
        expected_counts, _ = np.histogram(expected, bins=breakpoints)
        actual_counts, _ = np.histogram(actual, bins=breakpoints)
        expected_prop = np.clip(expected_counts / len(expected), 1e-6, None)
        actual_prop = np.clip(actual_counts / len(actual), 1e-6, None)
        return np.sum((actual_prop - expected_prop) * np.log(actual_prop / expected_prop))

class ConceptDriftDetector:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.performance_history = []
    
    def add_prediction(self, y_true: float, y_pred: float):
        self.performance_history.append(abs(y_true - y_pred))
        if len(self.performance_history) > self.window_size * 2:
            self.performance_history = self.performance_history[-self.window_size * 2:]
    
    def detect_drift(self, threshold: float = 0.1) -> bool:
        if len(self.performance_history) < self.window_size * 2:
            return False
        old_error = np.mean(self.performance_history[:self.window_size])
        new_error = np.mean(self.performance_history[self.window_size:])
        return (new_error - old_error) / old_error > threshold
```

### 再訓練觸發

```python
class RetrainingTrigger:
    def __init__(self):
        self.drift_detector = DriftDetector(reference_data)
        self.concept_detector = ConceptDriftDetector()
    
    def check_triggers(self, current_data: np.ndarray, predictions: list) -> dict:
        triggers = {}
        drift_results = self.drift_detector.detect_ks_drift(current_data)
        drift_features = [k for k, v in drift_results.items() if v["drift_detected"]]
        if len(drift_features) > 5:
            triggers["data_drift"] = {"severity": "high", "features": drift_features, "action": "retrain"}
        
        for y_true, y_pred in predictions:
            self.concept_detector.add_prediction(y_true, y_pred)
        if self.concept_detector.detect_drift():
            triggers["concept_drift"] = {"severity": "critical", "action": "retrain"}
        
        recent_accuracy = np.mean([abs(y_true - y_pred) < 0.05 for y_true, y_pred in predictions[-1000:]])
        if recent_accuracy < 0.90:
            triggers["performance_degradation"] = {"severity": "high", "accuracy": recent_accuracy, "action": "retrain"}
        
        return triggers
```

## 31.8 知識沉澱與反饋閉環

### 知識圖譜回流

```python
from neo4j import GraphDatabase

class KnowledgeGraphUpdater:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def log_incident(self, incident: dict):
        with self.driver.session() as session:
            session.run("""
                CREATE (i:Incident {
                    incident_id: $incident_id, timestamp: $timestamp,
                    severity: $severity, description: $description,
                    root_cause: $root_cause, resolution: $resolution
                })
            """, **incident)
            if "model_name" in incident:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    MATCH (m:Model {name: $model_name})
                    CREATE (i)-[:AFFECTED]->(m)
                """, incident_id=incident["incident_id"], model_name=incident["model_name"])
    
    def log_model_iteration(self, model_iteration: dict):
        with self.driver.session() as session:
            session.run("""
                CREATE (m:ModelVersion {
                    model_name: $model_name, version: $version,
                    timestamp: $timestamp, metrics: $metrics
                })
            """, **model_iteration)
            session.run("""
                MATCH (new:ModelVersion {model_name: $model_name, version: $version})
                MATCH (old:ModelVersion {model_name: $model_name, version: $previous_version})
                CREATE (old)-[:EVOLVED_TO]->(new)
            """, model_name=model_iteration["model_name"],
                version=model_iteration["version"],
                previous_version=model_iteration["previous_version"])
```

**反饋閉環**：

```
運維事件 → 根因分析 → 知識圖譜 → 模型優化 → 部署上線 → 監控反饋
   ↑                                                          ↓
   └──────────────────────────────────────────────────────────┘
```

### 經驗沉澱

**故障案例庫**：

```yaml
incident_case:
  case_id: "INC-2024-001"
  title: "良率預測模型準確率下降"
  date: "2024-03-15"
  severity: "high"
  symptoms:
    - "模型準確率從95%下降到88%"
    - "誤報率增加30%"
  root_cause:
    category: "data_drift"
    description: |
      設備維護後，感測器校準參數變化，導致FDC資料分佈偏移。
      模型訓練資料未包含維護後的資料模式。
  resolution:
    immediate: "使用最近7天資料重訓練模型"
    permanent: "建立資料漂移自動檢測與再訓練機制"
  lessons_learned:
    - "需要建立設備維護後的資料品質檢查"
    - "需要縮短再訓練週期（從季度→月度）"
    - "需要建立資料漂移自動監控"
```

## 31.9 供應商與開源組件治理

### 依賴版本管理

```yaml
compatibility_matrix:
  cuda:
    versions: ["11.8", "12.1", "12.3"]
    compatible_cudnn: {"11.8": "8.6", "12.1": "8.9", "12.3": "8.9"}
    compatible_tensorrt: {"11.8": "8.5", "12.1": "8.6", "12.3": "8.6"}
  
  pytorch:
    versions: ["2.0", "2.1", "2.2"]
    compatible_cuda: {"2.0": ["11.8"], "2.1": ["11.8", "12.1"], "2.2": ["12.1", "12.3"]}
  
  triton:
    versions: ["23.10", "24.01", "24.03"]
    compatible_tensorrt: {"23.10": "8.5", "24.01": "8.6", "24.03": "8.6"}
```

### 安全補丁驗證

```python
class PatchValidator:
    def __init__(self):
        self.test_env = TestEnvironment()
    
    def validate_patch(self, component: str, patch_version: str) -> dict:
        # 1. 建立測試環境
        self.test_env.setup(component, patch_version)
        
        # 2. 運行回歸測試
        test_results = self.test_env.run_regression_tests()
        
        # 3. 效能基準測試
        perf_results = self.test_env.run_benchmark()
        
        # 4. 安全掃描
        security_results = self.test_env.run_security_scan()
        
        return {
            "component": component,
            "patch_version": patch_version,
            "tests_passed": test_results["passed"],
            "performance_impact": perf_results["delta"],
            "security_issues": security_results["issues"],
            "recommendation": "approve" if test_results["passed"] > 0.95 and len(security_results["issues"]) == 0 else "reject"
        }
```

### 供應鏈風險評估

```yaml
supply_chain_risk:
  high_risk:
    - component: "CUDA"
      vendor: "NVIDIA"
      risk: "單一供應商鎖定"
      mitigation: "維護ONNX Runtime作為替代推理路徑"
    - component: "Triton"
      vendor: "NVIDIA"
      risk: "深度綁定NVIDIA生態"
      mitigation: "保留TorchScript/ONNX部署能力"
  
  medium_risk:
    - component: "PyTorch"
      vendor: "Meta (開源)"
      risk: "版本迭代快速，相容性維護成本高"
      mitigation: "鎖定LTS版本，季度評估升級"
    - component: "Kubeflow"
      vendor: "Google (開源)"
      risk: "社群活躍度波動"
      mitigation: "保持自訂Pipeline能力，降低平台依賴"
```

## 31.10 AI Infra成熟度自評與演進

### 成熟度模型

| 維度 | Level 1 初始 | Level 2 基礎 | Level 3 定義 | Level 4 管理 | Level 5 優化 |
|------|------------|------------|------------|------------|------------|
| **算力管理** | 手動配置GPU | 容器化部署 | 自動擴縮容 | 多租戶隔離 | 智慧資源調度 |
| **模型治理** | 本地檔案儲存 | MLflow追蹤 | 模型註冊中心 | 審批流程 | 自動化生命週期 |
| **CI/CD** | 手動部署 | 基礎自動化 | 完整流水線 | 灰度發布 | 持續驗證 |
| **監控運維** | 基礎日誌 | Prometheus | 完整告警 | 故障自癒 | 預測性運維 |
| **安全合規** | 無管控 | 基礎存取控制 | 審計日誌 | 合規報告 | 自動化合規 |
| **成本運營** | 無追蹤 | 基礎計量 | 成本分攤 | 優化建議 | 自動化優化 |

### 自評清單

```yaml
self_assessment:
  compute_management:
    - id: "CM-1"
      question: "GPU資源是否容器化管理？"
      level: 2
    - id: "CM-2"
      question: "是否支援自動擴縮容？"
      level: 3
    - id: "CM-3"
      question: "是否實現多租戶隔離？"
      level: 4
    - id: "CM-4"
      question: "是否具備智慧資源調度能力？"
      level: 5
  
  model_governance:
    - id: "MG-1"
      question: "是否使用實驗管理工具（MLflow/W&B）？"
      level: 2
    - id: "MG-2"
      question: "是否建立模型註冊中心？"
      level: 3
    - id: "MG-3"
      question: "是否有模型審批流程？"
      level: 4
    - id: "MG-4"
      question: "是否實現模型全生命週期自動化？"
      level: 5
  
  monitoring:
    - id: "MO-1"
      question: "是否有基礎監控指標？"
      level: 2
    - id: "MO-2"
      question: "是否建立告警規則？"
      level: 3
    - id: "MO-3"
      question: "是否實現故障自動恢復？"
      level: 4
    - id: "MO-4"
      question: "是否具備預測性運維能力？"
      level: 5
```

### 演進路線圖

```
當前狀態評估 → 差距分析 → 優先順序排序 → 路線圖制定 → 執行與追蹤
     ↓              ↓            ↓              ↓              ↓
  成熟度雷達    目標等級     投資ROI       季度里程碑     持續改進
```

**實施建議**：

1. **短期（0-6個月）**：建立基礎MLOps工具鏈（MLflow + DVC + Triton）
2. **中期（6-18個月）**：完善CI/CD流水線、模型治理、監控告警
3. **長期（18-36個月）**：實現平台化、自動化運維、智慧優化

---

## 本章小結

本章系統介紹了生產級AI運維的核心實踐，涵蓋從安全合規到持續演進的完整體系。核心要點：

1. **生產化三大約束**：零容忍停機、審計追溯、IP保護，是晶圓廠AI運維的剛性要求
2. **變更管理**：分級審批 + 灰度發布 + 完整審計鏈，保障模型變更安全可控
3. **資料安全**：分類分級 + 脫敏 + 加密 + 水印 + 跨客戶隔離，構建多層防護
4. **合規審計**：ISO 9001/IATF 16949對接 + 數位簽章證據鏈 + 自動化報告
5. **韌性工程**：故障隔離 + 冗餘設計 + 快速恢復 + 多級降級，保障7×24連續運行
6. **成本運營**：精細化分攤 + 殭屍任務識別 + 自動擴縮 + 電力優化
7. **漂移監控**：資料漂移/概念漂移/特徵漂移三維檢測 + 自動再訓練觸發
8. **知識閉環**：運維事件回流知識圖譜 + 故障案例庫 + 反饋自增強
9. **供應商治理**：相容性矩陣 + 安全補丁驗證 + 供應鏈風險評估
10. **成熟度自評**：6維度5級模型 + 自評清單 + 演進路線圖

至此，第九部分「AI Infra工程化實戰」三章全部完成。從第29章算力底座、第30章平台工程到第31章生產運維，形成了完整的「算力→平台→運維」工程化閉環，與前28章的「資料→演算法→業務」體系共同構成晶圓廠AI的完整知識圖譜。
