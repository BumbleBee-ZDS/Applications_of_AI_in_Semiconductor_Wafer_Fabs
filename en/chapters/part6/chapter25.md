# Chapter 25: Ontology Construction and Application in Semiconductor Wafer Fabs

## 25.1 Design Principles for Wafer Fab Ontology

The previous chapter told the story of how Palantir used Ontology to help Samsung improve yield. This chapter shifts perspective from "story" to "engineering" — specifically how to build an Ontology in a wafer fab and what intelligent applications it can drive.

### Business Entities as the Core

The first principle of wafer fab Ontology design is: center on business entities, not data tables.

Traditional data modeling starts from "what tables exist" — MES has a Lot table, Wafer table, and Operation table; FDC has a SensorData table; SPC has a Measurement table. This approach equates data structure with business semantics — but they are not the same thing. The Operation table in MES and the Step table in FDC may describe the same process step, just with different naming conventions across systems.

Ontology design starts from "what entities exist in the business" — Wafer, Tool, Recipe, Defect, ProcessStep. These entities are explicit expressions of business concepts, independent of any IT system. Data sources are merely data providers for entities — MES provides tracking data for Lot and Wafer, FDC provides sensor data for Tool, SPC provides Measurement results. The ontology defines "what is a Wafer"; the data source provides "W001 is a specific Wafer."

### Dynamically Evolvable

Wafer fab processes continuously evolve — introducing new process nodes, installing new equipment, and bringing in new products can all introduce new entity types and relationship types. The Ontology must be able to dynamically evolve — adding new object types and relationships without stopping the system.

This means Ontology design does not pursue "getting it right in one shot" but adopts incremental construction:

1. First define core entity types (Wafer, Tool, ProcessStep, etc.) and basic relationships
2. As applications deepen, gradually add new entity types (e.g., ConsumablePart, MaintenanceEvent)
3. Relationship types can also be added incrementally — initially maybe only `usesTool`, later adding `causesDefect`, `affectsYield`, and other semantic relationships

### Cross-System Semantic Unification

The Ontology's most fundamental responsibility is cross-system semantic unification. A wafer fab may have dozens of IT systems, each with its own data model. The Ontology does not replace these systems — it builds a semantic layer on top of them, allowing all systems' data to be understood under the same conceptual framework.

Achieving semantic unification requires three things:

**Concept alignment:** Determine which concepts across systems are equivalent. MES's "Operation" = FDC's "Step" = YMS's "Stage". These equivalence relationships are explicitly declared in the ontology — all three terms map to the same `ProcessStep` object type.

**Granularity alignment:** Different systems' data granularity may differ — MES records data by batch, FDC by second, SPC by batch or by wafer. The Ontology needs to define aggregation relationships between different granularity data — `Lot` contains multiple `Wafer`s, `Wafer` goes through multiple `ProcessStep`s, each `ProcessStep` corresponds to multiple `SensorDataPoint`s.

**Time alignment:** Different systems' timestamps may be based on different clocks or different time zones. The Ontology needs to define a unified time model — all timestamps converted to UTC, with their source system annotated.

## 25.2 Wafer Fab Core Ontology Models

### Product Ontology

The product ontology describes product entities in the wafer fab and their hierarchical relationships:

```
Object type hierarchy:

FabSite (Wafer Fab)
  └─ Product (Product)
       └─ Lot (Lot)
            └─ Wafer (Wafer)
                 └─ Die (Die)

Relationship types:
  FabSite -[PRODUCES]-> Product
  Product -[CONTAINS]-> Lot
  Lot -[CONTAINS]-> Wafer
  Wafer -[CONTAINS]-> Die

Property examples (Wafer):
  waferId: string (unique identifier)
  position: integer (position in lot)
  diameter: float (diameter, mm)
  thickness: float (thickness, μm)
  status: enum (IN_PROCESS, COMPLETED, SCRAPPED, ON_HOLD)
  startTime: datetime (start time)
  endTime: datetime (completion time, nullable)
```

The key design point of the product ontology is the hierarchical relationship — the five-layer structure from FabSite to Die covers all granularities from factory-level to chip-level. Queries can be performed at any level — viewing the entire factory's output, a product's yield, a lot's progress, a wafer's defect distribution, or a die's test results.

### Process Ontology

The process ontology describes the structure of process flows:

```
Object types:

Route (Process Route)
  └─ ProcessStep (Process Step)
       ├─ Module (Process Module)
       └─ Recipe (Recipe)
            └─ Parameter (Parameter)

Relationship types:
  Route -[HAS_STEP]-> ProcessStep
  ProcessStep -[BELONGS_TO]-> Module
  ProcessStep -[USES_RECIPE]-> Recipe
  Recipe -[HAS_PARAMETER]-> Parameter
  ProcessStep -[PRECEDES]-> ProcessStep  (step sequence)
  ProcessStep -[REQUIRES_TOOL_TYPE]-> ToolType

Property examples (ProcessStep):
  stepId: string
  stepOrder: integer (sequence number in route)
  stepType: enum (LITHO, ETCH, CVD, PVD, CMP, IMP, CLEAN, MEASURE)
  targetCD: float (target critical dimension, nm)
  cdTolerance: float (CD tolerance, nm)
  cycleTime: float (standard processing time, min)
```

The key design of the process ontology is the sequential relationship between steps (`PRECEDES`) and the type constraint between steps and equipment (`REQUIRES_TOOL_TYPE`). The sequential relationship supports forward and backward traversal — given a certain step, you can query its preceding steps ("what happened before this step") or following steps ("what happens after this step"). The equipment type constraint enables the dispatching system to check at the ontology level "whether a certain step can be executed on a certain piece of equipment."

### Equipment Ontology

The equipment ontology describes the hierarchical structure and status of equipment:

```
Object type hierarchy:

ToolType (Equipment Type)
  └─ Tool (Equipment)
       └─ Chamber (Chamber)
            └─ Component (Component)
                 └─ ConsumablePart (Consumable Part)

Relationship types:
  ToolType -[INSTANCE]-> Tool
  Tool -[HAS_CHAMBER]-> Chamber
  Chamber -[HAS_COMPONENT]-> Component
  Component -[USES_CONSUMABLE]-> ConsumablePart
  Tool -[LOCATED_AT]-> Bay (equipment location in bay)
  Tool -[CURRENT_STATUS]-> ToolStatus

Actions:
  Tool.schedulePM(maintenanceType, scheduledTime)
  Tool.takeOffline(reason)
  Tool.bringOnline()
  Tool.calibrate(parameters)

Functions:
  Tool.getOEE(timeRange) -> float
  Tool.getHealthScore() -> float
  Tool.getYieldHistory(timeRange) -> YieldResult
```

The equipment ontology introduces actions and functions — this is a key step from static knowledge representation to "executable ontology." The `schedulePM` action encapsulates the complete logic of equipment maintenance scheduling — checking the equipment's current status, verifying the maintenance window, creating a maintenance work order, and notifying relevant personnel. An AI Agent can execute equipment maintenance arrangements by calling this action without needing to know the underlying MES system's API details.

### Defect Ontology

The defect ontology describes defect types, causes, and impacts:

```
Object types:

Defect (Defect)
  ├─ DefectType (Defect Type)
  ├─ DefectPattern (Defect Pattern)
  └─ RootCause (Root Cause)

Relationship types:
  Wafer -[HAS_DEFECT]-> Defect
  Defect -[CLASSIFIED_AS]-> DefectType
  Defect -[EXHIBITS_PATTERN]-> DefectPattern
  Defect -[CAUSED_BY]-> RootCause
  RootCause -[RELATED_TO]-> ProcessStep
  RootCause -[RELATED_TO]-> Tool
  Defect -[IMPACTS]-> Die
  Defect -[DETECTED_BY]-> InspectionTool

Property examples (Defect):
  defectId: string
  location: (x: float, y: float)  (coordinates on wafer)
  size: float (size, nm)
  severity: enum (CRITICAL, MAJOR, MINOR, INFO)
  detectionLayer: string (at which layer detected)
  timestamp: datetime
```

The core value of the defect ontology lies in the explicit expression of causal chains — `Defect → CAUSED_BY → RootCause → RELATED_TO → ProcessStep/Tool`. This chain explicitly links "there is a defect at a certain position on the wafer" with "a certain process step's certain equipment caused this defect." When a YED engineer queries a defect, the system can automatically display the complete causal information along this chain.

### Time Ontology

The time ontology integrates the time dimension into all entities:

```
Object types:

TimePeriod (Time Period)
  ├─ Shift (Shift)
  ├─ Day (Day)
  ├─ Week (Week)
  └─ Month (Month)

ProcessPeriod (Process Period)
  ├─ PMCycle (PM Cycle: operating period between two PMs)
  ├─ RecipeCycle (Recipe Cycle: continuous running period of same recipe)
  └─ LotProcessing (Lot Processing Period)

Relationship types:
  Wafer -[ENTERED_STEP_AT]-> ProcessStep (with timestamp)
  Wafer -[EXITED_STEP_AT]-> ProcessStep (with timestamp)
  Tool -[RAN_PM_AT]-> PMCycle (with start/end time)
  Defect -[OCCURRED_DURING]-> ProcessPeriod

Functions:
  TimePeriod.getYield(product, tool?) -> YieldResult
  PMCycle.getBatchCount() -> integer
  PMCycle.getDegradationTrend() -> TimeSeries
```

The time ontology's design makes "time-dimensional queries" natural — "last week's yield trend for Tool No. 3 during the 3rd PM cycle" is a composite query along the ontology's relationship chain: `TimePeriod(Week) → Tool → PMCycle → YieldResult`.

## 25.3 Ontology-Driven Data Fusion

### Data Integration of MES + FDC + SPC + YMS

Fusing the four core systems' data into a unified ontology is the core task of Ontology engineering. Each system's data mapping approach differs:

**MES → Ontology:** MES data is the "skeleton" — defining the existence of Lot, Wafer, ProcessStep and their hierarchical relationships. Each record in MES directly maps to an object instance in the ontology. MES's batch tracking data is the time axis foundation of the ontology — each Wafer's entry/exit time at each ProcessStep defines its complete history in the time dimension.

**FDC → Ontology:** FDC data is the "flesh and blood" — providing detailed sensor time-series data of equipment operation. FDC data maps to properties of the Tool object — specifically, the SensorData when the Tool processes a certain Wafer at a certain ProcessStep. FDC data mapping requires time alignment — FDC timestamps need to be aligned with MES's batch entry/exit times to determine which batch's which step a segment of sensor data corresponds to.

**SPC → Ontology:** SPC data is the "measuring stick" — providing process parameter measurement results. SPC data maps to Measurement objects, associated with the corresponding ProcessStep and Wafer. SPC data also contains control chart status — when a parameter exceeds control limits, it triggers a Defect or Alert event.

**YMS → Ontology:** YMS data is the "judge" — providing defect inspection results and test yield. YMS data maps to Defect objects (defect instances) and TestResult objects (test results). YMS's wafer map data can map to a property of the Wafer object — a two-dimensional array representing each Die's pass/fail status.

### Cross-System Semantic Alignment

When mapping data from the four systems to the ontology, semantic alignment is the most critical engineering challenge. Here are several typical alignment scenarios:

**Step alignment:** A Lot's process route in MES contains 1200 steps, each with a stepId. FDC also records step information during equipment operation, but the stepId naming convention may differ — MES uses "OP_045" for step 45, while FDC may use "STEP_45." The ontology needs to define mapping rules: `MES.OP_045 ≡ FDC.STEP_45 ≡ Ontology.ProcessStep(stepOrder=45)`.

**Time alignment:** MES records batch entry/exit times at the equipment level (batch-level granularity), while FDC records sensor data timestamps at the second-level granularity. The alignment method: sensor data in FDC whose timestamp falls within the entry/exit time interval of a batch recorded in MES belongs to that batch's operation data for that step.

**Equipment alignment:** Equipment IDs in MES (e.g., "ETC-03") and equipment identifiers in FDC (e.g., "ETCHER_003") need unified mapping. When equipment has components replaced after PM, the old and new component IDs also need to be associated in the ontology — `Component(replaced_by: Component)`.

## 25.4 Ontology-Driven Intelligent Applications

### Ontology-Based Root Cause Analysis

When all data is fused into the ontology, root cause analysis transforms from "engineers manually querying across multiple systems" to "automated reasoning on the ontology graph."

A typical ontology-driven RCA process:

```
Trigger: CP yield below control limit

Step 1: Get anomalous batch's complete process history
  Query: Lot(B67890).getProcessHistory()
  Result: 1200 ProcessSteps, using 23 Tools

Step 2: Compare with normal batches, identify anomalous parameters
  Query: Compare all Measurements of B67890 with normal_b67800/normal_b67850
  Result: Step 623 CD deviation +4% (normal ±1%), Step 624 film thickness deviation -3% (normal ±1.5%)

Step 3: Search associated equipment along causal chain
  Query: Step 623 → USES_TOOL → Tool(ETC-03)
  Query: ETC-03's SensorData during B67890
  Result: RF power fluctuation 2.8% (normal <1%)

Step 4: Check equipment historical trend
  Query: ETC-03's health score trend over past 7 days
  Result: RF power fluctuation gradually increased over past 3 days

Step 5: Search for similar historical cases in knowledge graph
  Query: Search for historical cases of "RF power fluctuation → CD deviation → yield drop"
  Result: ETC-05 had similar pattern 3 months ago, root cause was matcher aging

Step 6: Generate root cause hypothesis
  Hypothesis: ETC-03 matcher aging causing RF power fluctuation
  Confidence: 82%
  Reasoning path: [Complete chain of Step2→Step3→Step4→Step5]
  Recommended action: Check ETC-03 matcher, schedule maintenance
```

Every step of this process is a graph query along the ontology's relationship chains — no cross-system jumping, no manual judgment of "whether the step in MES corresponds to the operation in FDC." The ontology has already explicitly defined these semantic relationships.

### Ontology-Driven Knowledge Reasoning

The ontology not only stores known facts but can also discover implicit knowledge through reasoning rules. Several reasoning examples:

**Transitive reasoning:** If `Wafer W001` belongs to `Lot L123`, and `Lot L123` belongs to `Product P005`, then it can be inferred that `Wafer W001` is an instance of `Product P005`. This reasoning is automatic in the ontology — when a user queries all Wafers of Product P005, the system automatically returns all Wafers from all Lots belonging to that Product through transitive relationships.

**Consistency checking:** The ontology can define constraints — e.g., "each Wafer must belong to exactly one Lot." When a Wafer is associated with two Lots during data mapping, the ontology reasoning engine automatically detects the inconsistency and alerts. This kind of data quality validation is difficult to achieve in traditional data lakes — because there is no unified semantic model to define "what constitutes a valid data relationship."

**Implicit association discovery:** Ontology reasoning can discover associations that humans have not explicitly labeled. If `DefectType A` is typically `CAUSED_BY` `RootCause X`, and in the current analysis `Defect D123` is `CLASSIFIED_AS` `DefectType A`, then the reasoning engine can infer that the possible root cause of `Defect D123` is `RootCause X` — even if no one explicitly labeled this association.

### Ontology + LLM Intelligent Q&A

The combination of Ontology and LLM is currently the most frontier direction. LLM's natural language understanding capability + Ontology's structured knowledge = a true "industrial intelligent assistant."

In this architecture, the LLM's role is the "natural language interface," and the ontology's role is the "knowledge engine":

```
Engineer: "Which equipment had the largest parameter fluctuation in the past week? What's the impact on yield?"
  │
  ├─ LLM parses intent:
  │    Query: All Tool SensorData fluctuation over past 7 days
  │    Analyze: Tool with largest fluctuation
  │    Correlate: Impact of fluctuating Tool on yield
  │
  ├─ LLM generates ontology query:
  │    Tool.getAll().filter(timeRange=last7days)
  │      .map(t => t.getSensorDataVariance())
  │      .sortBy(variance).top(1)
  │    → Result: ETC-03, RF power fluctuation 3.2%
  │
  ├─ LLM generates ontology associative query:
  │    ETC-03 → USED_AT → ProcessStep 623
  │    ProcessStep 623 → AFFECTS → CD
  │    CD deviation → IMPACTS → Yield
  │    → Result: ETC-03's RF fluctuation affects Step 623's CD uniformity,
  │      estimated yield drop of 2-3%
  │
  └─ LLM generates natural language answer:
       "The equipment with the largest parameter fluctuation in the past 7 days is
        ETC-03 (etcher), with RF power fluctuation of 3.2%, far exceeding the normal
        level (<1%). This equipment is used for Step 623 etch process, and RF power
        fluctuation directly affects etch CD uniformity. Based on historical association
        analysis, similar RF fluctuations typically cause CP yield drops of 2-3%.
        Recommendation: Check ETC-03's matcher status and assess whether maintenance
        is needed."
```

This process demonstrates three unique capabilities of LLM + Ontology:

**The LLM understands the user's natural language intent** — engineers don't need to know the ontology's schema or query language; they simply ask in natural language.

**The ontology provides structured knowledge and reasoning capability** — the LLM doesn't need to "remember" all process knowledge (which would cause hallucinations); the ontology serves as an external knowledge base providing accurate facts and relationships.

**The LLM transforms structured query results into human-understandable natural language** — engineers don't need to interpret tables or charts; the LLM directly explains the analysis results in language.

### Ontology-Driven Digital Twin

When the Ontology contains actions and functions, it itself constitutes an "executable digital twin." This digital twin not only maps the wafer fab's static structure (what equipment, products, and processes exist) but also dynamic behavior (how equipment operates, how processes affect yield, how maintenance affects capacity).

The combination of digital twin and Ontology operates at three levels:

**Simulation:** Simulating "what-if" scenarios on the ontology — "If ETC-03 goes down for maintenance tomorrow, what is the capacity impact over the next 72 hours?" Functions in the ontology can calculate this impact — querying batches queued on ETC-03, estimating routing time to backup equipment, simulating delivery impact.

**Optimization:** Optimization algorithms based on the ontology can find globally optimal strategies. Because the ontology unifies all data, optimization algorithms can search in the complete information space — rather than only doing local optimization on a single system's data like traditional methods.

**Closed-loop control:** The ontology supports bidirectional data flow — not only reading data from source systems into the ontology but also writing decisions from the ontology back to source systems for execution. When an Agent calls the `Tool.schedulePM()` action on the ontology, this action can automatically trigger maintenance work order creation and schedule adjustment in MES.

## 25.5 Implementation Path and Challenges

### Where to Start Building the Ontology

Don't attempt to build a complete wafer fab ontology all at once — this is unrealistic. Start from the highest-value business scenario, build the minimal ontology needed for that scenario, then gradually expand.

Recommended construction order:

**Phase 1: Yield analysis ontology.** This is the starting point that best demonstrates value. Build six core entity types — Wafer, Lot, ProcessStep, Tool, Defect, TestResult — and their basic relationships. This ontology supports the root cause analysis scenario described in Chapter 6 — starting from a yield anomaly, locating the root cause along relationship chains.

**Phase 2: Equipment health ontology.** Expand the Tool, Chamber, and Component hierarchical structure; add SensorData, MaintenanceEvent, PMCycle, and other entities. This ontology supports predictive maintenance and equipment health monitoring scenarios.

**Phase 3: Production scheduling ontology.** Add Route, DispatchingRule, WIP, Capacity, and other entities. This ontology supports intelligent scheduling and bottleneck analysis scenarios.

**Phase 4: Fab-wide integration ontology.** Integrate the ontologies from the previous three phases; add cross-domain relationships — such as the complete causal chain of "equipment health affects process quality affects yield affects capacity." This ontology supports fab-wide Agent architecture and digital twins.

### Integration with Existing IT Systems

The Ontology does not replace existing IT systems — MES, FDC, SPC, and YMS continue to operate, each performing its own functions. The Ontology provides a semantic layer on top of them.

There are three integration approaches:

**Batch ETL:** Daily batch export of data from source systems to the ontology's data store. Suitable for analysis scenarios that don't require real-time (e.g., daily yield reports). Advantage is simplicity and reliability; disadvantage is data latency.

**Streaming data pipelines:** Map source systems' real-time data streams to the ontology through message queues like Kafka. Suitable for scenarios requiring near-real-time (e.g., equipment anomaly monitoring, real-time yield tracking). FDC's sensor data is suitable for this approach — data generated every second is mapped to SensorData objects in the ontology through streaming pipelines.

**Federated queries:** Don't physically move data to the ontology store; access source systems directly at query time. Suitable for scenarios with extremely large data volumes or extremely high data security requirements. Disadvantage is higher query latency.

In practice, all three approaches are typically used in combination — MES data via batch ETL (daily updates are sufficient), FDC data via streaming pipelines (near-real-time needed), and certain sensitive data via federated queries (not leaving the source system).

### Organizational and Cultural Change

The technical challenges of Ontology are solvable — OWL, knowledge graphs, data pipelines, and other technologies are already mature. The greater challenge is at the organizational and cultural level.

**Cross-department collaboration.** Ontology definition requires consensus across PID, YED, MFG, PE, and EE departments — "what is a ProcessStep," a seemingly simple question, may have different understandings across departments. Driving this cross-department consensus requires support from senior management and a professional ontology engineering team.

**Data ownership.** When all data is integrated into a unified ontology, data ownership becomes blurred — does MES data "belong to" the IT department or "belong to" PID? How are data modification permissions allocated in the ontology? These questions require a clear governance framework.

**Return on investment timeline.** Ontology project ROI is not immediate — the ontology's value materializes gradually as data accumulates and applications expand. Management needs to understand this and provide sufficient patience and sustained investment. Samsung's case shows that from introducing Palantir to significant yield improvement took about a year and a half.

### ROI Assessment

ROI assessment for Ontology projects needs to consider both direct and indirect benefits:

**Direct benefits:**
- Root cause analysis time reduction (from hours to tens of minutes)
- Yield improvement (faster root cause localization → faster process correction → shorter yield ramp cycle)
- Reduced unplanned equipment downtime (advance warning from predictive maintenance)
- Capacity utilization improvement (intelligent scheduling reduces bottleneck idle time)

**Indirect benefits:**
- Engineer experience digitization (tacit knowledge converted into reusable ontology knowledge)
- Cross-department collaboration efficiency improvement (unified semantics reduces communication costs)
- AI model development acceleration (ontology-provided data infrastructure accelerates model training and deployment)
- New employee training acceleration (ontology as a training tool, helping newcomers quickly understand the full process picture)

---

## Conclusion

This book started from the 1956 Dartmouth Conference, traversed seventy years of AI development history, followed the three major schools of symbolism, connectionism, and behaviorism, entered the three core departments of semiconductor wafer fabs, and finally converged on Ontology — the technology brought from military intelligence to industrial manufacturing by Palantir.

This journey revealed a core viewpoint: **AI deployment in wafer fabs is not the victory of any single algorithm, but the victory of technology fusion.** Deep learning can identify defect patterns but cannot explain "why this defect caused the yield drop." Reinforcement learning can optimize process parameters but cannot automatically discover associations from massive heterogeneous data. LLMs can understand engineers' questions but, without accurate knowledge base support, will only produce hallucinations.

Ontology provides the semantic infrastructure for all these technologies to work collaboratively — it is the wafer fab's "universal language," enabling data from different systems, AI models from different domains, and engineers from different departments to communicate and collaborate under the same knowledge framework.

Palantir's story — from helping the CIA track bin Laden, to helping the IAEA monitor Iran's nuclear facilities, to helping Samsung climb out of the 30% yield quagmire — is not a company's business story, but a proof of a technological paradigm: when data is properly organized, semantics are explicitly defined, and relationships are structurally expressed, the power of AI can truly be unleashed.

Semiconductor manufacturing is the frontier of human industrial civilization. Each generation of technology node advancement challenges the limits of physics and engineering. AI is not an optional add-on for wafer fabs — when process complexity exceeds human engineers' cognitive bandwidth, AI becomes a necessity. And Ontology is the infrastructure that enables this necessity to work effectively.

This book reaching this point is only the beginning. Semiconductor technology is evolving, AI technology is exploding, and the intersection of the two generates new practices and stories every day. This book will continue to be updated with industry development — on GitHub, with the participation of every reader.
