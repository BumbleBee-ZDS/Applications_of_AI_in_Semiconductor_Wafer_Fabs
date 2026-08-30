# 第25章 Ontology 在半導體晶圓廠的構建與應用

## 25.1 晶圓廠 Ontology 的設計原則

上一章講述了Palantir如何用Ontology幫助三星提升良率。本章將視角從"故事"轉向"工程"——具體如何在晶圓廠中構建Ontology，以及它能驅動哪些智慧應用。

### 以業務實體為核心

晶圓廠Ontology設計的第一個原則是：以業務實體為核心，而非以資料表為核心。

傳統的資料建模從"有哪些表"出發——MES有Lot表、Wafer表、Operation表，FDC有SensorData表，SPC有Measurement表。這種方式將資料結構等同於業務語義——但它們不是同一回事。MES中的Operation表和FDC中的Step表可能描述同一個製程步驟，只是兩個系統的命名不同。

Ontology設計從"業務中有哪些實體"出發——Wafer、Tool、Recipe、Defect、ProcessStep。這些實體是業務概念的顯式表達，獨立於任何IT系統。資料源只是實體的資料提供者——MES提供Lot和Wafer的追蹤資料，FDC提供Tool的感測器資料，SPC提供Measurement結果。本體定義"什麼是Wafer"，資料源提供"W001是一片具體的Wafer"。

### 動態可演化

晶圓廠的製程在持續演進——新製程節點的引入、新設備的安裝、新產品的匯入都可能引入新的實體型別和關係型別。Ontology必須能夠動態演化——在不停止系統運行的情況下新增新的物件型別和關係。

這意味著Ontology的設計不追求"一步到位"，而是採用增量式構建：

1. 先定義核心實體型別（Wafer、Tool、ProcessStep等）和基礎關係
2. 隨著應用深化，逐步新增新的實體型別（如ConsumablePart、MaintenanceEvent）
3. 關係型別也可以增量新增——初期可能只有`usesTool`，後期新增`causesDefect`、`affectsYield`等語義關係

### 跨系統語義統一

Ontology最根本的職責是跨系統語義統一。一個晶圓廠可能有數十個IT系統，每個系統有自己的資料模型。Ontology不取代這些系統——它在這些系統之上建立一個語義層，讓所有系統的資料在同一套概念體系下被理解。

實現語義統一需要做三件事：

**概念對齊：** 確定不同系統中哪些概念是等價的。MES的"Operation"=FDC的"Step"=YMS的"Stage"。這些等價關係在本體中被顯式宣告——所有三個術語對映到同一個`ProcessStep`物件型別。

**粒度對齊：** 不同系統的資料粒度可能不同——MES按批次記錄資料，FDC按秒記錄，SPC按批次或按晶圓記錄。Ontology需要定義不同粒度資料之間的聚合關係——`Lot`包含多個`Wafer`，`Wafer`經過多個`ProcessStep`，每個`ProcessStep`對應多個`SensorDataPoint`。

**時間對齊：** 不同系統的時間戳可能基於不同時鐘或不同時區。Ontology需要定義統一的時間模型——所有時間戳轉換為UTC，並標註其來源系統。

## 25.2 晶圓廠核心本體模型

### 產品本體

產品本體描述晶圓廠中的產品實體及其層級關係：

```
对象类型层级:

FabSite (晶圆厂)
  └─ Product (产品)
       └─ Lot (批次)
            └─ Wafer (晶圆)
                 └─ Die (裸片)

关系类型:
  FabSite -[PRODUCES]-> Product
  Product -[CONTAINS]-> Lot
  Lot -[CONTAINS]-> Wafer
  Wafer -[CONTAINS]-> Die

属性示例 (Wafer):
  waferId: string (唯一标识)
  position: integer (在批次中的位置)
  diameter: float (直径, mm)
  thickness: float (厚度, μm)
  status: enum (IN_PROCESS, COMPLETED, SCRAPPED, ON_HOLD)
  startTime: datetime (投片时间)
  endTime: datetime (完成时间, nullable)
```

產品本體的設計要點是層級關係——從FabSite到Die的五層結構覆蓋了從工廠級到晶片級的所有粒度。查詢可以在任意層級進行——檢視整個工廠的產出、某個產品的良率、某個批次的進度、某片晶圓的缺陷分佈、某顆晶片的測試結果。

### 製程本體

製程本體描述製程流程的結構：

```
对象类型:

Route (工艺路线)
  └─ ProcessStep (工艺步骤)
       ├─ Module (工艺模块)
       └─ Recipe (配方)
            └─ Parameter (参数)

关系类型:
  Route -[HAS_STEP]-> ProcessStep
  ProcessStep -[BELONGS_TO]-> Module
  ProcessStep -[USES_RECIPE]-> Recipe
  Recipe -[HAS_PARAMETER]-> Parameter
  ProcessStep -[PRECEDES]-> ProcessStep  (步骤顺序)
  ProcessStep -[REQUIRES_TOOL_TYPE]-> ToolType

属性示例 (ProcessStep):
  stepId: string
  stepOrder: integer (在路线中的序号)
  stepType: enum (LITHO, ETCH, CVD, PVD, CMP, IMP, CLEAN, MEASURE)
  targetCD: float (目标关键尺寸, nm)
  cdTolerance: float (CD允差, nm)
  cycleTime: float (标准加工时间, min)
```

製程本體的關鍵設計是步驟間的順序關係（`PRECEDES`）和步驟與設備的型別約束（`REQUIRES_TOOL_TYPE`）。順序關係支援正向和反向遍歷——給定某個步驟，可以查詢其前序步驟（"這個步驟之前發生了什麼"）或後序步驟（"這個步驟之後會做什麼"）。設備型別約束使得派工系統可以在本體層面檢查"某個步驟是否可以在某臺設備上執行"。

### 設備本體

設備本體描述設備的層級結構和狀態：

```
对象类型层级:

ToolType (设备类型)
  └─ Tool (设备)
       └─ Chamber (腔体)
            └─ Component (部件)
                 └─ ConsumablePart (消耗件)

关系类型:
  ToolType -[INSTANCE]-> Tool
  Tool -[HAS_CHAMBER]-> Chamber
  Chamber -[HAS_COMPONENT]-> Component
  Component -[USES_CONSUMABLE]-> ConsumablePart
  Tool -[LOCATED_AT]-> Bay (设备位于哪个厂区)
  Tool -[CURRENT_STATUS]-> ToolStatus

动作:
  Tool.schedulePM(maintenanceType, scheduledTime)
  Tool.takeOffline(reason)
  Tool.bringOnline()
  Tool.calibrate(parameters)

函数:
  Tool.getOEE(timeRange) -> float
  Tool.getHealthScore() -> float
  Tool.getYieldHistory(timeRange) -> YieldResult
```

設備本體引入了動作和函式——這是從靜態知識表示到"可執行本體"的關鍵一步。`schedulePM`動作封裝了設備維護排程的完整邏輯——檢查設備當前狀態、驗證維護視窗、建立維護工單、通知相關人員。AI Agent可以透過呼叫這個動作來執行設備維護安排，而不需要知道底層MES系統的API細節。

### 缺陷本體

缺陷本體描述缺陷的型別、成因和影響：

```
对象类型:

Defect (缺陷)
  ├─ DefectType (缺陷类型)
  ├─ DefectPattern (缺陷模式)
  └─ RootCause (根因)

关系类型:
  Wafer -[HAS_DEFECT]-> Defect
  Defect -[CLASSIFIED_AS]-> DefectType
  Defect -[EXHIBITS_PATTERN]-> DefectPattern
  Defect -[CAUSED_BY]-> RootCause
  RootCause -[RELATED_TO]-> ProcessStep
  RootCause -[RELATED_TO]-> Tool
  Defect -[IMPACTS]-> Die
  Defect -[DETECTED_BY]-> InspectionTool

属性示例 (Defect):
  defectId: string
  location: (x: float, y: float)  (晶圆上的坐标)
  size: float (尺寸, nm)
  severity: enum (CRITICAL, MAJOR, MINOR, INFO)
  detectionLayer: string (在哪一层检测到)
  timestamp: datetime
```

缺陷本體的核心價值在於因果鏈路的顯式表達——`Defect → CAUSED_BY → RootCause → RELATED_TO → ProcessStep/Tool`。這條鏈路將"晶圓上某個位置有一個缺陷"與"某個製程步驟的某臺設備導致了這個缺陷"顯式關聯。當YED工程師查詢一個缺陷時，系統可以自動沿這條鏈路展示完整的因果資訊。

### 時間本體

時間本體將時間維度整合到所有實體中：

```
对象类型:

TimePeriod (时间段)
  ├─ Shift (班次)
  ├─ Day (日)
  ├─ Week (周)
  └─ Month (月)

ProcessPeriod (工艺周期)
  ├─ PMCycle (PM周期: 两次PM之间的运行期)
  ├─ RecipeCycle (配方周期: 同一配方连续运行期)
  └─ LotProcessing (批次加工期)

关系类型:
  Wafer -[ENTERED_STEP_AT]-> ProcessStep (with timestamp)
  Wafer -[EXITED_STEP_AT]-> ProcessStep (with timestamp)
  Tool -[RAN_PM_AT]-> PMCycle (with start/end time)
  Defect -[OCCURRED_DURING]-> ProcessPeriod

函数:
  TimePeriod.getYield(product, tool?) -> YieldResult
  PMCycle.getBatchCount() -> integer
  PMCycle.getDegradationTrend() -> TimeSeries
```

時間本體的設計使得"時間維度查詢"變得自然——"上週3號機臺在第3個PM週期內的良率趨勢"是一個沿本體關係鏈路的複合查詢：`TimePeriod(Week) → Tool → PMCycle → YieldResult`。

## 25.3 Ontology 驅動的資料融合

### MES + FDC + SPC + YMS 的資料整合

將四大核心系統的資料融合到統一本體中是Ontology工程的核心任務。每個系統的資料對映方式不同：

**MES → 本體：** MES資料是"骨架"——定義了Lot、Wafer、ProcessStep的存在和它們之間的層級關係。MES中的每條記錄直接對映為本體中的物件例項。MES的批次追蹤資料是本體的時間軸基礎——每個Wafer在每個ProcessStep的進出時間定義了它在時間維度上的完整歷史。

**FDC → 本體：** FDC資料是"血肉"——提供了設備運行的詳細感測器時序資料。FDC資料對映為Tool物件的屬性——具體來說是Tool在某個ProcessStep處理某個Wafer時的SensorData。FDC資料的對映需要處理時間對齊——FDC的時間戳需要與MES的批次進出時間對齊，確定某段感測器資料對應哪個批次的哪個步驟。

**SPC → 本體：** SPC資料是"量尺"——提供了製程參數的量測結果。SPC資料對映為Measurement物件，關聯到對應的ProcessStep和Wafer。SPC資料還包含控制圖狀態——當參數超出控制限時，觸發一個Defect或Alert事件。

**YMS → 本體：** YMS資料是"裁判"——提供了缺陷檢測結果和測試良率。YMS資料對映為Defect物件（缺陷例項）和TestResult物件（測試結果）。YMS的晶圓圖資料可以對映為Wafer物件的屬性——一個二維陣列表示每顆Die的透過/失敗狀態。

### 跨系統語義對齊

將四個系統的資料對映到本體時，語義對齊是最關鍵的工程挑戰。以下是幾個典型的對齊場景：

**步驟對齊：** MES中一個Lot的製程路線包含1200步，每步有一個stepId。FDC中也記錄了設備運行的步驟資訊，但stepId的命名規則可能不同——MES用"OP_045"表示第45步，FDC可能用"STEP_45"表示。本體需要定義對映規則：`MES.OP_045 ≡ FDC.STEP_45 ≡ Ontology.ProcessStep(stepOrder=45)`。

**時間對齊：** MES記錄批次進出設備的時間（批次級粒度），FDC記錄感測器資料的時間戳（秒級粒度）。對齊方式是：FDC中時間戳落在MES記錄的某批進出時間區間內的感測器資料，屬於該批次在該步驟的運行資料。

**設備對齊：** MES中的設備ID（如"ETC-03"）與FDC中的設備標識（如"ETCHER_003"）需要統一對映。當設備被PM後更換了部件，新舊部件的ID也需要在本體中關聯——`Component(replaced_by: Component)`。

## 25.4 Ontology 驅動的智慧應用

### 基於本體的根因分析

當所有資料被融合到本體後，根因分析從"工程師在多個系統中手動查詢"變為"在本體圖上自動推理"。

一次典型的本體驅動RCA流程：

```
触发: CP良率低于控制限

Step 1: 获取异常批次的完整工艺历史
  查询: Lot(B67890).getProcessHistory()
  结果: 1200个ProcessStep，使用23台Tool

Step 2: 对比正常批次，识别异常参数
  查询: 比较B67890与normal_b67800/normal_b67850的所有Measurement
  结果: Step 623的CD偏差+4%（正常±1%），Step 624的膜厚偏差-3%（正常±1.5%）

Step 3: 沿因果链路搜索关联设备
  查询: Step 623 → USES_TOOL → Tool(ETC-03)
  查询: ETC-03在B67890的SensorData
  结果: RF功率波动2.8%（正常<1%）

Step 4: 检查设备历史趋势
  查询: ETC-03在过去7天的健康度趋势
  结果: RF功率波动过去3天逐步增大

Step 5: 在知识图谱中搜索类似历史案例
  查询: 搜索"RF功率波动→CD偏差→良率下降"的历史案例
  结果: 3个月前ETC-05出现过类似模式，根因为匹配器老化

Step 6: 生成根因假设
  假设: ETC-03匹配器老化导致RF功率波动
  置信度: 82%
  推理路径: [Step2→Step3→Step4→Step5的完整链路]
  建议措施: 检查ETC-03匹配器，安排维护
```

這個過程的每一步都是沿本體中的關係鏈路進行的圖查詢——不需要跨系統跳轉，不需要人工判斷"MES中的step是否對應FDC中的operation"。本體已經將這些語義關係顯式定義了。

### 本體驅動的知識推理

本體不僅儲存已知事實，還可以透過推理規則發現隱含知識。幾個推理示例：

**傳遞性推理：** 如果`Wafer W001`屬於`Lot L123`，且`Lot L123`屬於`Product P005`，那麼可以推理出`Wafer W001`是`Product P005`的例項。這個推理在本體中是自動的——使用者查詢Product P005的所有Wafer時，系統自動透過傳遞性關係返回所有屬於該Product的Lot中的所有Wafer。

**一致性檢查：** 本體可以定義約束——如"每個Wafer必須屬於且僅屬於一個Lot"。當資料對映過程中出現一個Wafer被關聯到兩個Lot的情況時，本體推理引擎自動檢測到不一致並報警。這種資料品質校驗在傳統資料湖中很難實現——因為沒有統一的語義模型來定義"什麼是合法的資料關係"。

**隱含關聯發現：** 本體推理可以發現人類未顯式標註的關聯。如果`DefectType A`通常`CAUSED_BY` `RootCause X`，而當前分析中`Defect D123`被`CLASSIFIED_AS` `DefectType A`，那麼推理引擎可以推匯出`Defect D123`的可能根因是`RootCause X`——即使沒有人顯式標註這個關聯。

### 本體 + LLM 的智慧問答

Ontology與LLM的結合是當前最前沿的方向。LLM的自然語言理解能力+本體的結構化知識=真正的"工業智慧助手"。

在這個架構中，LLM的角色是"自然語言介面"，本體的角色是"知識引擎"：

```
工程师: "最近一周哪台设备的参数波动最大？对良率有什么影响？"
  │
  ├─ LLM解析意图:
  │    查询: 过去7天所有Tool的SensorData波动
  │    分析: 波动最大的Tool
  │    关联: 波动Tool对良率的影响
  │
  ├─ LLM生成本体查询:
  │    Tool.getAll().filter(timeRange=last7days)
  │      .map(t => t.getSensorDataVariance())
  │      .sortBy(variance).top(1)
  │    → 结果: ETC-03, RF功率波动3.2%
  │
  ├─ LLM生成本体关联查询:
  │    ETC-03 → USED_AT → ProcessStep 623
  │    ProcessStep 623 → AFFECTS → CD
  │    CD deviation → IMPACTS → Yield
  │    → 结果: ETC-03的RF波动影响Step 623的CD均匀性，
  │      预计导致良率下降2-3%
  │
  └─ LLM生成自然语言回答:
       "过去7天参数波动最大的设备是ETC-03（刻蚀机），
        其RF功率波动达3.2%，远超正常水平（<1%）。
        该设备用于第623步刻蚀工艺，RF功率波动直接影响
        刻蚀CD的均匀性。根据历史关联分析，类似的RF波动
        通常导致CP良率下降2-3%。
        建议检查ETC-03的匹配器状态并评估是否需要维护。"
```

這個過程展示了LLM+Ontology的三個獨特能力：

**LLM理解使用者的自然語言意圖**——工程師不需要知道本體的schema或查詢語言，只需用自然語言提問。

**本體提供結構化的知識和推理能力**——LLM不需要"記住"所有製程知識（這會導致幻覺），本體作為外部知識庫提供準確的事實和關係。

**LLM將結構化查詢結果轉化為人類可理解的自然語言**——工程師不需要解讀表格或圖表，LLM直接用語言解釋分析結果。

### 本體驅動的數字孿生

當Ontology包含動作和函式時，它本身就構成了一個"可執行的數字孿生"。這個數字孿生不僅對映了晶圓廠的靜態結構（有哪些設備、產品、製程），還對映了動態行為（設備如何運行、製程如何影響良率、維護如何影響產能）。

數字孿生與Ontology的結合在三個層面發揮作用：

**模擬：** 在本體上模擬"what-if"場景——"如果ETC-03明天停機維護，未來72小時的產能影響是什麼？"本體中的函式可以計算這個影響——查詢ETC-03上排隊的批次、估算路由到備用設備的時間、模擬對交期的影響。

**最佳化：** 基於本體的最佳化演算法可以找到全域最優策略。因為本體統一了所有資料，最佳化演算法可以在完整的資訊空間上搜尋——而不像傳統方法那樣只在單個系統的資料上做區域性最佳化。

**閉環控制：** 本體支援雙向資料流——不僅從源系統讀取資料到本體，還可以將本體中的決策寫回源系統執行。當Agent在本體上呼叫`Tool.schedulePM()`動作時，這個動作可以自動觸發MES中的維護工單建立和排程調整。

## 25.5 實施路徑與挑戰

### 從哪些本體開始構建

不要試圖一次構建完整的晶圓廠本體——這是不現實的。應該從最高價值的業務場景出發，構建該場景所需的最小本體，然後逐步擴充套件。

推薦的構建順序：

**第一階段：良率分析本體。** 這是最能體現價值的起點。構建Wafer、Lot、ProcessStep、Tool、Defect、TestResult六類核心實體及其基礎關係。這個本體支援第六章描述的根因分析場景——從良率異常出發，沿關係鏈路定位根因。

**第二階段：設備健康本體。** 擴充套件Tool、Chamber、Component的層級結構，新增SensorData、MaintenanceEvent、PMCycle等實體。這個本體支援預測性維護和設備健康監控場景。

**第三階段：生產排程本體。** 新增Route、DispatchingRule、WIP、Capacity等實體。這個本體支援智慧排程和瓶頸分析場景。

**第四階段：全廠整合本體。** 將前三個階段的本體整合，新增跨領域的關係——如"設備健康度影響製程品質影響良率影響產能"的完整因果鏈路。這個本體支援整廠級Agent架構和數字孿生。

### 與現有 IT 系統的整合

Ontology不取代現有的IT系統——MES、FDC、SPC、YMS繼續運行，各自執行自己的功能。Ontology在它們之上提供一個語義層。

整合方式有三種：

**批次ETL：** 每日從源系統批次匯出資料到本體的資料儲存。適用於不需要即時性的分析場景（如日級良率報告）。優點是簡單可靠，缺點是資料有時延。

**流式資料管道：** 透過Kafka等訊息佇列將源系統的即時資料流對映到本體。適用於需要近即時性的場景（如設備異常監控、即時良率追蹤）。FDC的感測器資料適合這種方式——每秒產生的資料透過流式管道對映到本體中的SensorData物件。

**聯邦查詢：** 不將資料物理移動到本體儲存，而是在查詢時直接訪問源系統。適用於資料量極大或資料安全要求極高的場景。缺點是查詢延遲較高。

實踐中三種方式通常混合使用——MES資料用批次ETL（每天更新一次足夠），FDC資料用流式管道（需要近即時），某些敏感資料用聯邦查詢（不離開源系統）。

### 組織與文化變革

Ontology的技術挑戰是可解決的——OWL、知識圖譜、資料管道等技術已經成熟。更大的挑戰在組織和文化層面。

**跨部門協作。** 本體的定義需要PID、YED、MFG、PE、EE多個部門達成共識——"什麼是ProcessStep"這個看似簡單的問題，不同部門可能有不同的理解。推動這種跨部門共識需要高層管理者的支援和專業的本體工程團隊。

**資料所有權。** 當所有資料被整合到統一本體後，資料的所有權變得模糊——MES資料"屬於"IT部門還是"屬於"PID？本體中的資料修改權限如何分配？這些問題需要明確的治理框架。

**投資回報週期。** Ontology專案的ROI不是即時的——本體的價值隨著資料積累和應用擴充套件逐步體現。管理層需要理解這一點，給予足夠的耐心和持續投入。三星的案例表明，從引入Palantir到良率顯著改善經歷了約一年半的時間。

### ROI 評估

Ontology專案的ROI評估需要考慮直接收益和間接收益：

**直接收益：**
- 根因分析時間縮短（從數小時到數十分鐘）
- 良率提升（更快的根因定位→更快的製程修正→更短的良率爬坡週期）
- 設備非計畫停機減少（預測性維護的提前預警）
- 產能利用率提升（智慧排程減少瓶頸空閒時間）

**間接收益：**
- 工程師經驗數位化（隱性知識轉化為可複用的本體知識）
- 跨部門協作效率提升（統一語義減少溝通成本）
- AI模型開發加速（本體提供的資料基礎設施加速模型訓練和部署）
- 新員工培訓加速（本體作為培訓工具，幫助新人快速理解製程全貌）

---

## 結語

本書從1956年達特茅斯會議出發，穿越AI七十年的發展歷程，沿著符號主義、連接主義、行為主義三大流派，進入了半導體晶圓廠的三大核心部門，最終收束於Ontology——這個被Palantir從軍事情報帶到工業製造的技術。

這趟旅程揭示了一個核心觀點：**AI在晶圓廠的落地，不是某個演算法的勝利，而是技術融合的勝利。** 深度學習可以辨識缺陷模式，但它不能解釋"為什麼這個缺陷導致了良率下降"。強化學習可以最佳化製程參數，但它不能從海量異構資料中自動發現關聯。LLM可以理解工程師的問題，但如果沒有準確的知識庫支撐，它只會產生幻覺。

Ontology提供了所有這些技術協同工作的語義基礎設施——它是晶圓廠的"通用語言"，讓不同系統中的資料、不同領域的AI模型、不同部門的工程師能夠在同一個知識框架下溝通和協作。

Palantir的故事——從幫助CIA追蹤本拉登，到幫助IAEA監控伊朗核設施，再到幫助三星從30%的良率泥潭中爬出來——不是某個公司的商業故事，而是一個技術正規化的證明：當資料被正確地組織、語義被顯式地定義、關係被結構化地表達時，AI的力量才能真正釋放。

半導體製造是人類工業文明的最前沿。每一代技術節點的推進都在挑戰物理極限和工程極限。AI不是晶圓廠的附加選項——當製程複雜性超過人類工程師的認知頻寬時，AI成為必需品。而Ontology是讓這個必需品能夠有效工作的基礎設施。

這本書寫到此處只是開始。半導體技術在演進，AI技術在爆發，兩者的交叉每天都在產生新的實踐和故事。本書將隨產業發展持續更新——在GitHub上，在每一位讀者的參與中。
