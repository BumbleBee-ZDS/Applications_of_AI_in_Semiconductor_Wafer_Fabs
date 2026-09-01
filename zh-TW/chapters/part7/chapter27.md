# 第27章 動手實驗實驗室——把關鍵概念跑起來

## 27.1 為什麼需要動手實驗

前26章以概念、架構與產業案例為主線，配合的 Demo 腳本（`zh-CN/demos/` 下的 matplotlib 視覺化）負責「看一眼就懂」。但要把知識轉化為工程能力，還需要第二層：**可以本地執行的完整系統**——有真實的程式碼結構、可互動的介面、可修改的參數。

本章收錄 9 個動手實驗，全部來自作者在真實開發中積累並驗證過的 MVP 專案，按主題與正文章節的對應關係組織：

| 實驗 | 主題 | 對應章節 | 難度 |
| --- | --- | --- | --- |
| 27.3 Ontology 驅動的 Text2SQL | 本體語義層 + 受控 SQL 生成 | 第24/25章、第17章 | ★☆☆ |
| 27.4 晶圓廠 Ontology MVP（RCA Agent） | 本體圖 + GraphRAG + ReAct | 第24/25章、第2/14章 | ★★☆ |
| 27.5 FabGraph 雙圖譜知識平台 | Schema/Lineage 圖譜 + NL2SQL | 第14/13/17章 | ★★★ |
| 27.6 K8s 式宣告式排程 | 控制論迴圈 + 多 Agent 排程 | 第7/20章 | ★☆☆ |
| 27.7 產能規劃 PTA Agent | 感知-思考-行動 + What-If 模擬 | 第10章 | ★★☆ |
| 27.8 LoRA 微調兩階段查詢增強 | 資料合成 + 微調 + 評估 | 第15/17章 | ★★★ |
| 27.9 RTD 即時派工與人機協同 | 分級審批 + 稽核追溯 | 第8/11/22章 | ★★☆ |
| 27.10 CIM 可信系統紅藍對抗 | 規則+嵌入+LLM 混合驗證 | 第22/23章 | ★★☆ |
| 27.11 多 Agent 評估框架 | 評估品質/成本/韌性 | 第2/21章 | ★☆☆ |

> 所有實驗程式碼位於倉庫 `zh-CN/demos/experiments/` 目錄（各專案自帶 README）。除標註「需 API Key」的實驗外，其餘均可離線執行；需要 LLM 的實驗均提供 Mock/降級模式，無 Key 也能體驗核心流程。

## 27.2 實驗環境準備

- **Python**：3.10+（FabGraph 與微調實驗建議 3.11+）
- **通用依賴**：`pip install -r requirements.txt`（各專案目錄內）
- **API Key（可選）**：部分實驗使用 DeepSeek/通義千問等大語言模型，配置 `.env` 檔案中的 `API_KEY` 即可啟用真實 LLM；未配置時自動降級為規則引擎或 Mock
- **GPU（僅微調實驗建議）**：27.8 的 LoRA 訓練在 CPU 上可執行（速度較慢），有 NVIDIA GPU 可顯著加速

每個實驗小節給出「學什麼、怎麼跑、看什麼」三段式說明，建議先跑通再改參數，最後嘗試修改一處邏輯觀察系統行為的變化——這是理解架構設計意圖的最快路徑。

## 27.3 實驗一：Ontology 驅動的 Text2SQL（fab_ontology_text2sql）

**對應章節**：第24章（Palantir 與本體論）、第25章（Ontology 構建）、第17章（融合概論）

**學什麼**：這是理解「為什麼 LLM 不能自由寫 SQL」的最短路徑。實驗實現了 Palantir Ontology 思想的三段式 Text2SQL：

- **語義層**：本體字典定義晶圓廠的概念、實體與關係（Lot、Wafer、Equipment、Defect…）
- **動力層**：12 個預定義 SQL 範本，LLM 只負責「選範本 + 填參數」，絕不自由生成 SQL
- **動態層**：SQLite 執行引擎回傳結果並渲染圖表

這套架構保證了**結果可控、可稽核、可解釋**——正是第24章所強調的「本體作為受控語義層」的工程體現。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/fab_ontology_text2sql
pip install -r requirements.txt
streamlit run app.py
```

依賴極輕（約 5 個套件），離線即可執行；配置 API Key 後切換為 LLM 模式，可對比「規則兜底」與「LLM 選範本」兩種路徑的輸出差異。

**看什麼**：在介面輸入「W80 批次最近的缺陷記錄」這類自然語言，觀察系統如何先匹配本體概念、再選擇範本、最後生成 SQL——注意全程沒有任何自由文字拼接的 SQL。

## 27.4 實驗二：晶圓廠 Ontology MVP——本體圖驅動的根因分析 Agent（wafer_ontology_mvp）

**對應章節**：第24/25章（Ontology）、第2章（Agent）、第14章（知識圖譜）

**學什麼**：把第24章「物件-連結-動作」的本體三層映射做成可執行的根因分析（RCA）系統：

- **本體層**：NetworkX + SQLite 構建 Lot/Wafer/Equipment/Defect 實體與關係圖，實現 Palantir 三層映射的資料底座
- **推理層**：LangGraph 驅動的 ReAct Agent，透過工具呼叫在本體圖上遍歷、檢索、歸因
- **服務層**：FastAPI 提供本體查詢 API，Flask 提供 Web 介面

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/wafer_ontology_mvp
pip install fastapi uvicorn sqlmodel networkx langchain langchain-openai langgraph python-dotenv
python src/main.py      # 啟動 API 服務（自動播種模擬資料）
python web/app.py       # 啟動 Web 介面
```

**看什麼**：向 Agent 提問「ETCH-A03 設備相關的批次為什麼良率下降」，觀察 ReAct 迴圈如何分解問題、呼叫本體查詢工具、沿「設備→批次→晶圓→缺陷」鏈路追溯，最後給出帶證據鏈的根因結論。這正是第14章知識圖譜輔助 RCA 的完整工程形態。

## 27.5 實驗三：FabGraph——雙圖譜驅動的資料資產平台（FabGraph_MVP）

**對應章節**：第14章（符號主義應用）、第13章（代工服務轉型期）、第17章（融合概論）

**學什麼**：這是 9 個實驗中工程化程度最高的專案，演示晶圓廠資料資產的「元資料治理 + 語義檢索」：

- **Schema Graph**：表/欄位/類型的結構圖譜，支援語義檢索與 JOIN 路徑推薦
- **Lineage Graph**：資料血緣圖譜，回答「這張表從哪來、被誰用」
- **NL2SQL**：基於雙圖譜上下文的自然語言查詢，含社群偵測等圖演算法應用

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/FabGraph_MVP
pip install -e ".[dev]"
python scripts/init_mock_data.py
uvicorn fabgraph.main:app --host 0.0.0.0 --port 8000 --reload   # API
streamlit run ui/streamlit_app/app.py                             # 介面
```

無 API Key 時自動降級為 Mock 模式；專案自帶 13 個 pytest 測試，可作為「如何為資料平台寫測試」的參考。

**看什麼**：先瀏覽 Schema Graph 頁面理解元資料組織，再用自然語言提問「蝕刻製程的良率趨勢」，觀察系統如何藉助圖譜推薦 JOIN 路徑、生成正確 SQL——體會第13章所說的「資料即服務」轉型的技術底座。

## 27.6 實驗四：K8s 式宣告式排程（C9S_agent）

**對應章節**：第7章（製造部/智慧排程）、第20章（SA 融合）

**學什麼**：把 Kubernetes 的控制論思想（宣告式調諧迴圈）搬進晶圓廠排程：使用者宣告目標（如「日產出 5000 片」），Supervisor/Scheduler/Worker/Monitor 四個 Agent 透過持續的「期望態-實際態」比對自動調諧，無需人工編寫排程腳本。這是第20章「符號+行為」融合（SA）的生動案例：規則系統定義目標與約束，行為系統負責逼近目標。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/C9S_agent
pip install -r requirements.txt   # 僅 2 個依賴
python app.py
```

純記憶體模擬，無任何外部依賴，秒級啟動。

**看什麼**：在儀表板下發一個產出目標，觀察調諧迴圈如何逐輪縮小偏差；再打開「傳統管道對比」頁面，對比宣告式與命令式兩種範式在應對擾動（設備故障注入）時的行為差異。

## 27.7 實驗五：產能規劃 PTA Agent（FabCapacityAgent）

**對應章節**：第10章（產能爬坡與產能規劃）

**學什麼**：9 個實驗中文檔、測試與降級策略最完整的專案，演示「感知（Perception）-思考（Thinking）-行動（Action）」四 Agent 編排的產能分析：

- **即時監控**：OEE、UPH 等指標看板（首次執行自動生成 90 天/120 台設備的模擬 MES 資料）
- **瓶頸偵測**：基於排隊論與利用率的瓶頸定位
- **What-If 模擬**：蒙地卡羅模擬加機/提速/擴班等方案的產能影響
- **Agent 工作台**：全鏈路執行或單 Agent 除錯，自動生成分析報告

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/FabCapacityAgent/fab_capacity_agent
pip install -r requirements.txt
streamlit run app.py
```

首次啟動需 30–60 秒生成模擬資料；無 API Key 時 LLM 相關功能自動降級，核心計算功能不受影響。附帶 23 個單元測試（`pytest tests/`）。

**看什麼**：在 What-If 頁面分別模擬「瓶頸設備 +1 台」與「瓶頸製程提速 10%」，對比兩者對月產出的影響——直觀感受第10章「先找瓶頸、再定投資」的產能規劃方法論。

## 27.8 實驗六：LoRA 微調——小模型輔助大語言模型的兩階段查詢增強（fab_llm_fine_tuning）

**對應章節**：第15章（連接主義應用）、第17章（融合概論）

**學什麼**：微調章節的最佳配套實驗，完整走通「資料合成 → LoRA 訓練 → 推理 → 量化評估」全鏈路。核心思路是**兩階段分工**：先用 LoRA 微調 Qwen2-0.5B 小模型做領域查詢預處理（補全術語、澄清意圖），再交給通用大語言模型生成最終 SQL——以極低成本獲得領域適配能力。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/fab_llm_fine_tuning
pip install -r requirements.txt
python -m fab_mvp.data_generation              # 生成/檢視訓練資料
python -m fab_mvp.train_lora --smoke --epochs 1   # 冒煙測試（快速驗證流程）
python -m fab_mvp.train_lora --epochs 3        # 完整訓練
```

倉庫已附帶訓練資料與評估結果（`fab_mvp/outputs/`），不訓練也可直接檢視評估報告；完整訓練需下載 Qwen2-0.5B 基座模型（約 1 GB），CPU 可執行但較慢。

**看什麼**：對比 `outputs/eval_summary.json` 中微調前後的指標差異，理解「小模型做預處理」為何能提升端到端準確率——這是第15章「資料稀缺場景下的 AI 加速」主題在 LLM 時代的延伸。

## 27.9 實驗七：RTD 即時派工與人機協同（fab_ai_rtd_mvp）

**對應章節**：第8章（製程/設備工程）、第11章（建設期與爬坡期）、第22章（LLM 應用）

**學什麼**：唯一完整演示「人工審批 + 稽核追溯」的實驗，覆蓋 RTD（Real-Time Dispatching）派工全鏈路：

感知（異常偵測）→ RAG 診斷（檢索歷史處置方案）→ 排程建議 → 模擬驗證 → **L1–L4 分級人工審批** → 執行與稽核日誌

分級審批是落地關鍵：低風險動作自動放行，高風險動作必須人工確認——這正是第11章「建設期人機協同」與第22章「LLM 進廠的信任門檻」兩個主題的工程答案。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/fab_ai_rtd_mvp
pip install -r requirements.txt
streamlit run app.py
```

配置 DeepSeek/通義千問 API Key 可啟用真實 LLM 診斷；無 Key 時全鏈路以規則降級執行，審批與稽核流程完整可體驗。

**看什麼**：觸發一次設備異常，跟隨介面向下走完整條鏈路，特別注意審批節點——不同風險等級的派工建議會停在不同層級等待人工決策，所有決策留痕可追溯。

## 27.10 實驗八：CIM 可信系統紅藍對抗（wafer-trust-guard）

**對應章節**：第22章（LLM 應用）、第23章（Agent 系統）

**學什麼**：用「紅藍對抗」的對抗式演練回答「如何驗證 AI 系統可信」：

- **紅隊**：生成試圖繞過管控的違規 Recipe（模擬攻擊與誤用）
- **藍隊**：四層驗證防線——靜態規則校驗 → Embedding 語義對齊 → LLM Judge 評審 → FA 記憶閉環（歷史案例召回）

四層防線恰好對應第18章神經符號思想的「規則 + 向量 + 大語言模型」混合驗證，是治理與信任主題的稀缺配套實驗。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/wafer-trust-guard
pip install -r requirements.txt
streamlit run app.py
```

全鏈路帶 Mock 兜底，無 Key 可完整執行。

**看什麼**：觀察同一違規 Recipe 在四層防線中的攔截位置——有的被靜態規則直接攔下，有的穿透到 LLM Judge 才被識別。思考：如果只保留其中一層，系統會在哪裡失守？

## 27.11 實驗九：多 Agent 評估框架（fab_agent_test）

**對應章節**：第2章（AI 簡史/Agent 概念）、第21章（NSA 全融合）

**學什麼**：回答「怎麼評估一個 Agent 系統好不好」。手寫 Planner/ToolSet/Reflector/Orchestrator 四模組協作完成缺陷 RCA，同時**即時評估**三類指標：

- **過程品質**：任務分解合理性、工具呼叫正確率
- **資源成本**：呼叫輪次、時延
- **系統韌性**：注入 30% 逾時故障，觀察系統能否恢復並完成任務

零外部 AI 依賴（純 Mock），白盒實現，是理解 Agent 評估方法論的最佳起點。

**怎麼跑**：

```bash
cd zh-CN/demos/experiments/fab_agent_test
pip install streamlit
streamlit run app.py
```

**看什麼**：執行一次完整評估，重點看韌性測試段——當工具呼叫逾時時，Orchestrator 的重試與降級策略如何生效，評估指標如何即時反映系統狀態。

## 27.12 實驗十：良率模型與爬坡模擬（yield_modeling_ramp）

對應**第9章（良率爬坡）**與**第11章（建設期/爬坡期）**。純 Python 實作三大概念：Poisson / 負二項式 / Murphy 良率模型對比、S 形爬坡曲線與學習率、基於 FDC 訊號的虛擬量測入門預測。執行後生成三張圖並輸出模型對比結論，直觀理解 `Y = exp(-D₀A)` 的數學含義與「死亡之谷」的成因。程式與說明均為中英雙語。

```bash
cd experiments/yield_modeling_ramp
pip install numpy matplotlib scikit-learn
python yield_modeling_ramp.py
```

## 27.13 實驗十一：預測性維護 RUL 預測（predictive_maintenance_rul）

對應**第12章（成熟量產期·預測性維護）**。用合成設備退化數據實作剩餘壽命（RUL）預測，並對比「定期 PM」與「預測性維護」兩種策略的維護成本——回答「維護時機到底怎麼定」這一成熟期核心問題。程式與說明均為中英雙語。

```bash
cd experiments/predictive_maintenance_rul
pip install numpy matplotlib scikit-learn
python predictive_maintenance_rul.py
```

## 27.14 實驗十二：LLM RAG 製程文件問答（llm_rag_spec_qa）

對應**第22章（LLM在晶圓廠的應用）**。實作一個精簡 RAG 系統：從製程規範（SPEC）文件庫檢索相關內容，再呼叫 LLM 生成帶來源引用的回答。預設呼叫 DeepSeek API；未設定 API Key 時自動降級為 Mock LLM，可離線執行。程式與說明均為中英雙語。

```bash
cd experiments/llm_rag_spec_qa
pip install requests
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可選，不設定則用 Mock LLM
python llm_rag_spec_qa.py
```

## 27.15 實驗十三：CNN 晶圓缺陷分類（wafer_defect_cnn）

對應**第15章（連接主義在晶圓廠的應用）**。生成四種缺陷模式（中心/邊緣環形/簇狀/無缺陷）的模擬晶圓圖，用神經網路（MLP 模擬 CNN 分類思想，零 GPU 依賴）自動分類，視覺化樣本、混淆矩陣與預測。配套 Web 介面可互動「生成並預測」。程式與說明均為中英雙語。

```bash
cd experiments/wafer_defect_cnn
pip install numpy matplotlib scikit-learn flask
python wafer_defect_cnn.py        # 命令列 / CLI
python web_app.py                 # Web 介面 http://127.0.0.1:5003
```

## 27.16 實驗十四：Q-Learning 智慧派工（rl_dispatch_basic）

對應**第16章（行為主義在晶圓廠的應用）**與第12章智慧排程。實作微型派工環境（快/慢兩台設備、隨機到達批次），用 Q-Learning 學習派工策略，與隨機派工對比總獎勵，視覺化學習曲線與排程甘特圖。程式與說明均為中英雙語。

```bash
cd experiments/rl_dispatch_basic
pip install numpy matplotlib flask
python rl_dispatch_basic.py       # 命令列 / CLI
python web_app.py                 # Web 介面 http://127.0.0.1:5004
```

## 27.17 實驗十五：專家系統缺陷診斷（expert_system_rca）

對應**第14章（符號主義在晶圓廠的應用）**。實作前向推理專家系統：將工程師的缺陷-根因經驗編碼為 IF-THEN 規則，輸入觀察事實自動推理出帶置信度的診斷與建議，並視覺化推理鏈。配套 Web 介面可勾選事實互動診斷。程式與說明均為中英雙語。

```bash
cd experiments/expert_system_rca
pip install numpy matplotlib flask
python expert_system_rca.py       # 命令列 / CLI
python web_app.py                 # Web 介面 http://127.0.0.1:5005
```

## 27.18 實驗十六：LLM Agent 工具呼叫（llm_agent_tool_use）

對應**第23章（Agent 系統在晶圓廠的實踐）**。實作 ReAct（推理+行動）Agent：LLM 自主決定呼叫工具（查WIP/設備狀態/利用率/製程規格），根據工具結果繼續推理直到給出最終回答，完整演示「感知→規劃→行動→觀察」循環。支援 DeepSeek API 與離線 Mock。程式與說明均為中英雙語。

```bash
cd experiments/llm_agent_tool_use
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可選
python llm_agent_tool_use.py       # 命令列 / CLI
python web_app.py                  # Web 介面 http://127.0.0.1:5006
```

## 27.19 實驗十七：思維鏈良率根因分析（llm_chain_of_thought_rca）

對應**第18章（NB 神經符號融合）**。用思維鏈（Chain-of-Thought）讓 LLM 按「觀察→假設→驗證→結論」分步推理良率根因，並用 IF-THEN 符號規則校驗 LLM 結論——演示神經與符號的結合與仲裁。支援 DeepSeek API 與離線 Mock。程式與說明均為中英雙語。

```bash
cd experiments/llm_chain_of_thought_rca
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可選
python llm_chain_of_thought_rca.py  # 命令列 / CLI
python web_app.py                  # Web 介面 http://127.0.0.1:5007
```

## 27.20 實驗十八：LLM 良率週報自動生成（llm_report_automation）

對應**第22章（LLM在晶圓廠的應用·良率報告生成）**。把結構化良率數據（週趨勢、缺陷TOP、設備狀態）交給 LLM，自動生成專業良率週報（數據→文本），並視覺化數據圖表。支援 DeepSeek API 與離線 Mock。程式與說明均為中英雙語。

```bash
cd experiments/llm_report_automation
pip install requests matplotlib flask
echo "DEEPSEEK_API_KEY=你的key" > .env   # 可選
python llm_report_automation.py    # 命令列 / CLI
python web_app.py                  # Web 介面 http://127.0.0.1:5008
```

## 27.21 從實驗到生產：改造指引

本章實驗均為 MVP 形態，走向生產環境通常還需要以下改造（各實驗的完整設計文件見其目錄內 README）：

1. **資料接入**：把模擬資料生成器替換為 MES/EAP/SPC 真實資料介面，注意保持本體/圖譜 Schema 穩定
2. **金鑰管理**：將 `.env` 中的 API Key 遷移至企業金鑰管理系統，按最小權限分配
3. **評估閉環**：參考 27.11 的三維評估框架，為每個上線的 Agent 建立持續評估
4. **審批與稽核**：涉及生產動作的系統，照搬 27.9 的分級審批與稽核日誌設計
5. **信任驗證**：對外提供決策建議的系統，用 27.10 的紅藍對抗思路做上線前演練

> 實驗是理解的捷徑，也是質疑的起點。跑通之後，不妨問自己：如果晶圓廠的真實資料分佈與模擬資料不同，這個系統的哪個環節會最先失效？——這正是從 Demo 走向落地的第一道門檻。
