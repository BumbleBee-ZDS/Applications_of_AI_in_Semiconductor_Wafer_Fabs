# Chapter 28: Wafer-Fab Data Architecture — The Data Foundation for AI Applications

> This chapter is the data-infrastructure foundation of the entire book. The previous chapters introduced the three core departments and business scenarios of the fab; from this chapter on, we enter the substantive discussion of "how AI gets deployed." And the first step of AI deployment is answering one question: **what does fab data actually look like?**

Throughout the earlier chapters, we have repeatedly referenced FDC signals, metrology data, MES records, yield data, and similar concepts. This chapter systematically answers three questions: what data does a fab have, why is this data so difficult to manage, and how can it be organized into a form that AI can consume reliably. Understanding this chapter is a prerequisite for all subsequent AI applications — yield prediction, virtual metrology, predictive maintenance, root-cause analysis — because **the accuracy ceiling of any model is determined by the quality and semantic clarity of the data.**

The chapter has six sections: Section 28.1, the fab data landscape, builds an overall picture of the seven core data sources; Section 28.2, data lineage and tacit knowledge, examines where data comes from, where it goes, and who understands it; Section 28.3, the data governance system, discusses how to make data trustworthy, traceable, and reusable; Section 28.4, the industrial semantic layer and knowledge graph, introduces the key technology that lets AI "understand" the language of the fab; Section 28.5, LLM and Agent data-consumption patterns, explores how large language models consume these data safely; Section 28.6, implementation path and phased rollout, gives a pragmatic roadmap from data to value.

---

## 28.1 The Wafer-Fab Data Landscape: From MES to Equipment Logs

> **Core question of this section**: What are the core data sources in a fab? What are their characteristics? Why must they be used in conjunction across systems?

If you ask an IT engineer to draw a system map of the fab, he will draw a complex network of MES, EAP, FDC, SPC, YMS, ERP, and other systems; if you ask a process engineer to describe a day's work, he talks about "this lot of wafers ran a recipe on that etcher, and there's a yield problem." The gap between these two pictures is what this chapter aims to close. This section "dissects" the fab from the data perspective.

### 28.1.1 A Map of Core Data Sources

The data sources of a fab can be summarized as seven core systems. They sit at different levels of the IT/OT layered architecture and play different roles:

**MES (Manufacturing Execution System)** is the fab's "production dispatcher." It records the route of each lot, the execution status of each step, work-in-process (WIP) distribution, work-order information, and operator-equipment interactions. MES answers the questions "which wafers are where, what has been done, and what comes next." It is the primary source of lot-level, event-level data and serves as the "anchor" for data from other systems.

**FDC/EDA (Fault Detection and Classification / Equipment Data Acquisition)** is the "recorder" of equipment process parameters. EDA is responsible for collecting high-frequency time-series data from equipment (temperature, pressure, RF power, gas flow, etc.); FDC performs statistical monitoring and anomaly detection on top of the collected data — triggering alarms when a parameter deviates from the process window. FDC data answers "during the few minutes of processing this lot of wafers, was the equipment state normal?" This is the **highest-frequency, largest-volume** data stream in the fab.

**SPC (Statistical Process Control)** systems draw control charts based on metrology data (film thickness, CD, overlay, etc.) to monitor whether the process remains in control. The difference between SPC and FDC: SPC monitors **process results** (parameters obtained from metrology), while FDC monitors **process conditions** (equipment operating parameters). The two complement each other.

**YMS (Yield Management System)** aggregates electrical test (CP/FT) and defect-inspection data, generating wafer maps, yield trends, and defect-distribution analysis. YMS answers "did this lot ultimately turn out well, and where did it go wrong."

**ERP (Enterprise Resource Planning)** manages enterprise-resource-level data such as materials, purchasing, inventory, cost, and orders. It does not directly participate in processing, but is critical to capacity planning, cost analysis, and supply-chain decisions.

**SECS/GEM equipment logs (SEMI Equipment Communications Standard / Generic Equipment Model)** constitute the industrial protocol layer for equipment-host communication. Through SECS/GEM, equipment reports recipe-execution records, alarm events, and state transitions (such as Process End, Alarm). These logs are first-hand evidence of "what the equipment actually did" and are the original carrier of FDC data.

**Inspection/metrology systems (KLA defect scanning, CD-SEM, optical metrology, etc.)** produce defect coordinates, defect images, critical-dimension data, and more. They link with YMS, providing the most direct evidence for defect analysis and yield attribution.

**Architecture diagram of the data-source landscape (text description)**: from bottom to top, there are four layers. The **equipment layer** (bottom) includes etchers, lithography tools, film tools, etc., communicating upward via the SECS/GEM protocol, producing equipment logs and process data; the **control layer** includes EAP (Equipment Automation Program) and FDC/EDA, responsible for equipment automation control and process-data collection; the **execution layer** includes MES, SPC, and YMS, carrying the core business of production execution and quality monitoring; the **planning layer** (top) includes ERP and various analysis platforms, oriented toward enterprise resources and business decisions. Data flows upward: the equipment layer produces raw process data, the control layer collects and pre-filters, the execution layer organizes it into business records, and the planning layer performs global analysis.

Using one lot of wafers as a thread, the chain can be traced: after a wafer enters the line, **MES** assigns it a lot ID and plans the route; at a certain etch step, the equipment reports the process-start and process-end events via **SECS/GEM**, and **FDC/EDA** records chamber temperature, pressure, RF power, and other process parameters at millisecond frequency; after processing, metrology equipment produces **CD-SEM/optical metrology** data, and **SPC** determines whether the step is in control; finally, after electrical test, **YMS** generates the wafer map and yield statistics. A complete data chain is thus formed.

### 28.1.2 Comparing Data Characteristics: Time Granularity, Volume, and Update Frequency

Different types of data differ enormously in time granularity, data volume, and update frequency. Understanding these differences is a prerequisite for choosing storage solutions and AI modeling approaches.

We use **FDC trace data from a certain etch process** as the running example to illustrate time-series characteristics. While an etcher chamber processes one wafer, the FDC system typically collects dozens of parameter channels (chamber pressure, upper/lower electrode RF power, temperature, individual gas flows, ESC electrostatic-chuck current, etc.) at 1-10 Hz. At 20 channels, 5 Hz sampling, and 200 seconds per wafer, one wafer generates about 20,000 records; a chamber processes hundreds of wafers a day, so a single tool generates millions of FDC records per day. This is a typical **high-frequency time-series stream**.

In stark contrast: **MES lot events** are at the minute-to-hour level — a record is generated only when a lot completes a process step; YMS yield data is at the lot or daily level — typically summarized by lot or by day.

The following table compares the characteristics of the seven core data sources:

| Data source | Typical fields | Time granularity | Daily volume (reference) | Update method |
| --- | --- | --- | --- | --- |
| MES | Lot ID, Route, Step, status, timestamp | minute~hour | tens of thousands~hundreds of thousands of records | real-time event push |
| FDC/EDA | channel ID, pressure, temperature, RF power, timestamp | millisecond~second | millions~tens of millions of records | real-time streaming |
| SPC | parameter ID, measured value, UCL/LCL, judgment | lot-level | thousands~tens of thousands | batch + real-time alarm |
| YMS | lot ID, yield value, defect coordinates, wafer map | lot-level/daily | thousands of records + image files | batch |
| ERP | material number, work order, cost, inventory | minute~day | thousands | batch |
| SECS/GEM logs | event ID, recipe name, status code, timestamp | second~minute | tens of thousands~hundreds of thousands of events | real-time push |
| Inspection/metrology | defect coordinates, defect type, CD value, images | wafer/lot-level | thousands of records + many images | batch + real-time linkage |

> **Practical tip:** A common mistake in fab data storage is "one size fits all." High-frequency time-series data such as FDC is best managed with columnar or time-series databases (e.g., InfluxDB, TimescaleDB); business data such as MES/YMS is suited to relational databases; inspection images and other unstructured data need object storage. Classify by the data-characteristics table first, then choose storage — this avoids the embarrassment of "a query over FDC history taking minutes."

In terms of volume, the annual incremental FDC history of an advanced fab (monthly output of tens of thousands of 12-inch wafers) can reach the TB level; adding inspection images and metrology data, the fab's annual data growth is typically in the tens of TB. This scale makes explicit demands on storage and query architecture: high-frequency process data must consider compression and tiered storage (hot data online, cold data archived).

### 28.1.3 Business Relationships Between Data

The data-source map answers "what data exists"; data linkage answers "how these data pieces form a complete story." A core feature of fab AI applications is that **most valuable analysis tasks require retrieving data across systems**.

Take a typical yield-drop root-cause analysis: when a lot's CP test yield drops sharply, the YED (Yield Engineering) engineer needs to simultaneously examine: the **YMS** wafer map to determine the spatial distribution of defects (edge or center?), the **MES** lot history to confirm which tools processed these wafers, the **FDC** data to see whether parameters drifted during processing on the corresponding tool, and the tool's **PM (Preventive Maintenance)** records to check whether it was approaching a maintenance cycle. No single system can answer "why did yield drop" — only by linking across systems can "result anomaly" be traced to "process anomaly" and then to "equipment anomaly."

A typical linkage chain can be expressed as:

```
Lot ID → Equipment ID → Chamber ID → FDC Trace → Corresponding Defect → Yield Loss
```

That is: starting from the yield loss, trace back to the processing equipment and chamber via the lot, descend to the FDC process data of that chamber, identify parameter anomalies, compare with the defect distribution, and finally confirm the source of the loss. This chain is exactly the data foundation for the yield-analysis and root-cause-analysis AI applications discussed from Chapter 9 onward.

Cross-system linkage is not easy in practice, with three main categories of difficulty:

**Inconsistent key systems.** The same physical object may be encoded differently across systems. For example, a lot number is `LOT-2026-001` in MES but may be truncated or prefixed in YMS; an equipment ID is `ETCH-03` in MES but `EQP-ETCH-003` in the FDC system. The first step of linkage is often "reconciliation" — building the mapping between each system's primary keys.

**Time-alignment problems.** FDC timestamps come from the equipment clock, while MES event timestamps come from the server clock, and the two may differ by seconds or even minutes. When doing "FDC parameters within the processing window" type linkage, directly joining by timestamp yields wrong results; clock calibration or alignment by event boundaries (such as Process Start/End events) is needed first.

**Multi-version states.** A lot may undergo rework, hold, splitting, or merging, and its process history can have multiple versions. Linkage must clarify "which version to take" — usually the final version, but root-cause analysis may need to review all historical versions.

> **Section summary:**
> - Fab data sources can be summarized as seven systems — MES, FDC/EDA, SPC, YMS, ERP, SECS/GEM logs, and inspection/metrology — distributed across four IT/OT layers with distinct roles.
> - Time granularity varies enormously: FDC is a millisecond-to-second high-frequency stream (millions of records per tool per day), MES events are minute-level, YMS summaries are lot/daily-level — "one size fits all" storage is a common error.
> - Valuable analysis almost always requires cross-system retrieval; the typical chain is "Lot→Equipment→Chamber→FDC Trace→Defect→Yield Loss."
> - The main difficulties of cross-system linkage are inconsistent keys, time alignment, and multi-version states; they must be addressed systematically during data governance.

---

## 28.2 Data Lineage and Tacit Knowledge: Where Data Comes From, Goes, and Who Understands It

> **Core question of this section**: Fab data often passes through complex processing chains. Where is this processing logic encapsulated? Why are these "invisible knowledge" the biggest obstacle to data governance?

In the previous section, we established a complete map of data sources. But in reality, what AI engineers receive is often not raw data but "report data" that has passed through many layers of processing. This processing logic — which source tables exist, what computations were done in between, how the definitions are set — constitutes **data lineage**. Understanding data lineage is the first step toward trustworthy data; and the tacit knowledge behind the lineage is the most intractable and most valuable part of fab data governance.

### 28.2.1 Sources of Complexity in Fab Data Lineage

Data lineage in fabs is far more complex than in the internet industry, rooted in **decades of IT system accumulation**.

Let us illustrate with a real processing chain. The "weekly yield" field in a fab's BI report may have the following lineage path:

```
Source table (YMS.WAFER_TEST_RESULT) → Oracle stored procedure (PKG_YIELD.CALC_WEEKLY)
→ PL/SQL business logic (filter rework lots, convert per-wafer) → ETL job (daily incremental load to warehouse)
→ Warehouse view (V_YIELD_WEEKLY) → BI report (weekly yield KPI)
```

In this chain, the loss of semantics at any link distorts the final number. For example, the stored procedure contains `WHERE lot_status != 'R'` — meaning it excludes rework lots. If an analyst does not know this filter and directly runs statistics on the report data, he will mistake "yield excluding rework" for "total yield."

The causes of complexity in fab data lineage can be summarized as three points:

**Decades-old legacy systems.** The IT systems of an advanced fab often span twenty or thirty years, having undergone multiple vendor switches and system upgrades. Early logic is encapsulated in Oracle stored procedures, views, and even COBOL programs; documentation has long been lost, but the code still runs.

**Vendor customization.** MES, YMS, and other systems are usually provided by multiple vendors, each having made extensive customization on top of the standard product — customization logic scattered across stored procedures, custom tables, and plugins. This logic is "part of the system" but not in any standard documentation.

**Personnel turnover and knowledge gaps.** IT and process teams in fabs experience frequent turnover; the veteran employee who understood why a certain stored procedure was written that way may have left. The system runs, but the "why" is known by no one.

The direct consequence of broken lineage is amplified in the AI era. Take virtual metrology (VM) modeling: an engineer receives a "yield table" to train a model but does not know whether the `YIELD_RATE` field is CP (circuit probing) yield or FT (final test) yield, whether it includes rework lots, or whether it is converted per wafer or per cassette — the labels the model learns are wrong from the start. **Label errors are the most insidious and most fatal source of AI model errors.** Unlike random noise, which can be suppressed by regularization, systematic bias makes the model learn wrong patterns — and the more complex the model, the more confidently it "remembers" these wrong patterns.

### 28.2.2 Three Forms of Tacit Knowledge

Data lineage records only "which links the data flowed through," but the **semantics** of each link — why it is computed this way, what this field represents, what this abnormal value means — is deeper knowledge. We call knowledge that cannot be directly obtained from system documentation **tacit knowledge**. In fabs, tacit knowledge exists in three forms:

**Knowledge in code: most reliable but hardest to read.** Stored procedures, view definitions, and ETL job scripts are the true "definers" of data semantics. They precisely record business logic — what is filtered, how conversion is done, what the defaults are. But this knowledge highly depends on the reader's technical ability and often has no comments. For example, this typical PL/SQL fragment:

```sql
-- Calculate weekly yield (excluding rework lots and engineering-experiment lots)
CREATE OR REPLACE PROCEDURE PKG_YIELD.CALC_WEEKLY (p_week IN VARCHAR2) IS
BEGIN
  INSERT INTO YIELD_WEEKLY (WEEK_ID, PRODUCT, YIELD_RATE)
  SELECT p_week, product_id,
         ROUND(SUM(pass_cnt) / NULLIF(SUM(total_cnt), 0) * 100, 2)
  FROM   WAFER_TEST_RESULT
  WHERE  test_week = p_week
    AND  lot_status != 'R'        -- exclude rework lots
    AND  lot_type != 'E'          -- exclude engineering-experiment lots
  GROUP BY product_id;
END;
```

The semantics of this code — "weekly yield = passed wafers / total wafers × 100, excluding rework and engineering lots" — hides in two `WHERE` conditions. An AI engineer who does not read the code will never know the definition.

**Knowledge in documents: most formal but most easily outdated.** SOPs (Standard Operating Procedures), engineering change notices (ECN/ECO), and process specifications record the "official version" of business rules. But their problem is **lag**: when the system code changes, the documentation is often forgotten; the definitions in the documents and the logic actually executed by the code may already be inconsistent. Documents are the "ought" of knowledge; code is the "is."

**Knowledge in people's heads: most valuable but most easily lost.** The experience of senior engineers is the most concentrated form of tacit knowledge. For example: "When this field shows -9999, it means the sensor is offline, not a real value"; "Tool 3's pressure runs high for the first two lots after PM, so exclude those in analysis"; "This yield formula only applies to products that did not go through wet cleaning" — this experience is written nowhere but directly affects the success of data analysis and model training.

A "three forms of knowledge" comparison table shows how the same knowledge appears in different carriers:

| Form | Carrier | Reliability | Readability | Timeliness | Loss risk |
| --- | --- | --- | --- | --- | --- |
| In code | stored procedures, views, ETL scripts | High (the "is") | Low (needs technical skill) | High (code is the current state) | Low (code still exists) |
| In documents | SOP, ECN/ECO, Spec | Medium (may lag) | High | Low (updates often forgotten) | Medium (documents get lost) |
| In people's heads | engineer experience | High but unpreserved | Low (oral transmission) | Unfixed | High (lost on departure) |

### 28.2.3 Business Risks of Tacit-Knowledge Loss

Tacit-knowledge loss is not a "might happen in the future" problem; it is a reality fabs face every day.

**Case**: After a senior YED engineer at a fab retired, the team found that no one could explain the origin of a "yield correction-factor table" — it had been manually calibrated years ago based on defect-distribution experience for a certain product and had been continuously referenced by the yield-analysis process. New engineers assumed it was the standard definition and used it in yield attribution for multiple projects, causing systematic bias in analysis conclusions for three consecutive months. Post-mortem review found that the factor applied only to an old, discontinued product and had never undergone formal review.

This case reveals three categories of typical risks from tacit-knowledge loss:

**Data misreading.** Not knowing field definitions or abnormal-value meanings leads to conclusions built on wrong understanding — the most direct risk.

**Reinventing the wheel.** Without accumulated tacit knowledge, every new team and every round of personnel turnover must rediscover everything; fabs spend enormous engineering effort each year on "re-understanding their own data."

**AI models learning wrong labels.** As discussed in Section 28.2.1, label/definition errors are systematically harmful to AI models. Tacit-knowledge loss directly undermines the data foundation of AI projects.

**Compliance and audit difficulties.** When asked "how was this number calculated," if the answer depends on one engineer's memory, the audit cannot pass.

At a deeper level, the essence of data governance is not "managing data" but **knowledge capture and transmission**. Lineage graphs capture knowledge in code, data dictionaries capture knowledge in documents, and expert interviews and knowledge accumulation capture knowledge in people's heads — all three are indispensable. This is the starting point of the next section on data governance, and the intellectual source of the "Ontology and knowledge graph" discussion in later chapters.

> **Practical tip:** Do not expect one-shot "big engineering" for tacit-knowledge capture. The pragmatic approach is **incidental accumulation**: every time a data problem is investigated, each RCA case, and each definition confirmation, casually record the "why" into the data dictionary or knowledge base. Field by field, this is more sustainable than planning a huge knowledge-engineering project. The key is to assign someone responsible for explaining each definition.

> **Section summary:**
> - The complexity of fab data lineage stems from decades of legacy systems, vendor customization, and personnel turnover; much business logic is encapsulated in stored procedures and views.
> - Tacit knowledge has three forms: in code (reliable but hard to read), in documents (formal but lagging), and in people's heads (valuable but easily lost).
> - The direct risks of tacit-knowledge loss are data misreading, redundant work, AI models learning wrong labels, and compliance/audit difficulties.
> - The essence of data governance is knowledge capture and transmission, covering all three carriers: code, documents, and people.

---

## 28.3 Data Governance: Making Data Trustworthy, Traceable, and Reusable

> **Core question of this section**: Faced with data of uneven quality, inconsistent definitions, and unclear lineage, how can a fab establish a governance system that makes data "trustworthy, traceable, and reusable"?

Section 28.2 identified the problems — complex lineage and dispersed tacit knowledge. This section provides the engineering solutions: data quality, standardization, metadata, lineage collection, and storage. The goal of this system is not "managing data" per se, but enabling AI engineers and analysts to **trust, trace, and reuse** the data they receive.

### 28.3.1 Data-Quality Challenges

The typical forms of fab data-quality problems can be grouped into four categories, each illustrated with a real scenario:

**Missing values.** FDC signals are reset after equipment PM (preventive maintenance); the first few lots after PM may lack complete FDC data; certain metrology points are only executed on sampled lots, so many lots miss specific fields. Handling missing values cannot simply "fill with zero" — the missing mechanism must be understood (random missing, or non-random missing correlated with equipment state).

**Outliers.** Sensor failures produce placeholder values such as -9999 or 0; after equipment parts are replaced, calibration drift shifts the entire parameter range of the same process. Outlier detection must be correlated with equipment events (replacement, PM, alarms) — the same numeric value may be an outlier before PM and normal after.

**Inconsistent definitions.** This is the most typical and most dangerous fab problem. Take "yield": the YED department defines it as CP test yield, the MFG department may use "line yield," finance uses "combined yield" — the three definitions are completely different. Similarly for "tool utilization": different systems define "available time" differently, producing numbers that can differ by over ten percentage points.

**Time-series alignment.** Different tools sample at different frequencies (some 1 Hz, some 10 Hz), and equipment clocks drift from server clocks. When correlating "FDC parameters with metrology results," alignment errors directly cause feature misplacement — correlating the pressure of the early process phase to the film thickness of the late phase.

From the AI perspective, the impact of data quality on models deserves special emphasis: **models are far more sensitive to systematic bias (such as label-definition errors) than to random noise.** Random noise can be suppressed by loss-function regularization, but systematic bias makes models learn wrong patterns — and the more complex the model, the more easily it "memorizes" these wrong patterns. Therefore, data-quality governance must take priority over model tuning; this is the first principle of AI projects.

> **Practical tip:** For fab data-quality troubleshooting, start with a "definition list": register the precise definitions, source systems, and calculation logic of the 50-100 most commonly used business definitions (yield, utilization, cycle time, defect density, etc.). Most AI project data problems ultimately trace back to "definitions not aligned" rather than "data missing."

### 28.3.2 Standardization and Metadata Management

The goal of data standardization is to make different systems and teams use the same name, unit, and code for the same thing.

**Naming conventions.** Unify the encoding rules for equipment IDs, step IDs, and product IDs. For example, equipment IDs are unified as "process-category-sequence" (ETCH-03), step IDs as "process-category-step-number-version." Seemingly simple, this is the foundation of cross-system linkage — most of the inconsistent-key problems in Section 28.1.3 can be alleviated at the source through naming conventions.

**Unit unification.** The same physical quantity may use different units in different systems (pressure in mTorr or Pa; temperature in Celsius or Kelvin). Data entering the data platform should be uniformly converted, with the original unit recorded in metadata.

**Dictionary/code-table management.** Enumerated values such as defect codes, alarm codes, and status codes need a unified dictionary table subject to change management — adding a new defect code must not change only one system but synchronize all consumers.

**Three types of metadata management.** Metadata is "data about data," divided into three categories:

- **Technical metadata**: table structures, field types, primary/foreign keys, storage locations — answers "where does the data exist and what does it look like."
- **Business metadata**: business meaning of fields, definition notes, owners, source systems — answers "what does this field mean"; this is what AI engineers need most.
- **Operational metadata**: ETL run logs, data update times, lineage records — answers "is the data current, and where did it come from."

Business metadata is the core output of data governance. A "field dictionary entry" example:

| Metadata item | Content |
| --- | --- |
| Field name | YIELD_RATE |
| Business meaning | Product yield (percentage) |
| Precise definition | CP passed chips / total chips × 100, excluding rework lots |
| Calculation logic | Source table YMS.WAFER_TEST_RESULT, stored procedure PKG_YIELD.CALC_WEEKLY |
| Data granularity | Lot × product |
| Unit | % (0~100) |
| Abnormal-value convention | -9999 means the lot was not tested; exclude it |
| Source system | YMS |
| Business owner | YED-Zhang San |
| Update frequency | Daily batch, 2:00 AM |

### 28.3.3 Technical Paths for Automated Lineage Collection

Lineage collection has three main technical paths, with clearly different degrees of automation and limitations:

**Static SQL parsing.** Parse the source code of stored procedures, views, and ETL scripts to automatically extract "table→table" and "field→field" dependencies. Advantage: no runtime environment intrusion and batch processing. Disadvantage: limited coverage — it often fails on dynamic SQL (concatenated query statements), nested PL/SQL logic, and external calls. For the `EXECUTE IMMEDIATE` dynamic SQL common in Oracle stored procedures, static parsing is almost helpless.

```sql
-- Dynamic SQL example: static parsing cannot determine the actual table and fields queried
v_sql := 'SELECT ' || v_dynamic_columns || 
         ' FROM ' || v_dynamic_table || 
         ' WHERE week_id = :w';
EXECUTE IMMEDIATE v_sql INTO v_result USING p_week;
```

**Runtime auditing.** Enable auditing at the database layer (e.g., Oracle Fine-Grained Auditing) or intercept SQL actually executed at the application layer to capture real data read/write relationships. Advantage: accurate (actual executed logic, not guesswork). Disadvantage: depends on database auditing capabilities, has performance overhead, and only covers "paths that have been triggered" — some stored-procedure branches may not have executed for months, leaving lineage incomplete.

**Manual annotation.** For key definitions that automation cannot cover, business/IT personnel manually register lineage relationships. Advantage: accurate and can supplement semantic information (not just "who depends on whom," but "why"). Data dictionaries and definition lists are essentially manual-annotation outputs. Disadvantage: depends on process discipline and requires long-term maintenance.

**The "90-9-1" rule of thumb**: in mature fabs, automation tools typically resolve about 90% of **table-level lineage** (which table depends on which table); about 9% requires manual annotation (dynamic SQL, cross-system data flows); and the final ~1% of **field-level semantic lineage** (why this field is computed this way) relies almost entirely on humans. **Table-level lineage answers "where the data came from"; field-level semantic lineage answers "what the data means"** — the latter is what AI applications truly need, and this part requires human involvement.

### 28.3.4 Graph Storage for Lineage

Data lineage is naturally a graph structure: tables, fields, stored procedures, and reports are nodes; dependency relationships are edges. Two mainstream storage choices exist:

| Dimension | Relational database | Graph database (Neo4j/NebulaGraph) |
| --- | --- | --- |
| Data model | lineage table (edge table) | native node+edge graph model |
| Multi-hop queries | multiple JOINs, SQL complex, performance degrades with hops | native traversal, excellent multi-hop performance and readability |
| Team familiarity | high (everyone knows SQL) | low (requires learning Cypher/GQL) |
| Operations cost | low (reuse existing DB) | medium (new component, cluster operations) |
| Suitable scale | up to a few thousand nodes | tens of thousands of nodes and above |

**Pragmatic advice**: lineage evolves in three phases — start with a relational database (two tables: `node` table and `edge` table), sufficient for single-hop queries like "field→upstream field"; migrate to a graph database when the graph reaches tens of thousands of nodes and frequent multi-hop traversal such as "find all downstream reports from a field" is needed; a transitional option is "relational storage + in-memory graph traversal" — building the graph in memory with Python's networkx, combining the reliable storage of relational databases with graph traversal capability, suitable for medium-scale scenarios.

> **Practical tip:** The key to phased lineage evolution is **data model first**: regardless of storage, the node/edge/attribute model of lineage (node types: table/field/process/report; edge types: read/write/derived; attributes: source system, definition note, owner) should be designed from the start. Storage can change; changing the data model later is costly.

> **Section summary:**
> - The four typical fab data-quality problems are missing values, outliers, inconsistent definitions, and time-series alignment; inconsistent definitions cause the most harm to AI models.
> - Standardization (naming, units, dictionaries) is the foundation of cross-system linkage; among the three metadata types, business metadata (field dictionaries) is the governance output AI engineers need most.
> - Lineage collection has three paths: static SQL parsing (automated, table-level), runtime auditing (accurate but costly), and manual annotation (the "last mile" of field-level semantics must involve humans).
> - Lineage storage can evolve by scale: relational → in-memory graph traversal → graph database, but the lineage data model should be designed from the beginning.

---

## 28.4 Industrial Semantic Layer and Knowledge Graph: Teaching AI the Language of the Fab

> **Core question of this section**: After solving data quality and lineage, a deeper question remains — how can AI "understand" the business semantics of fab data rather than treating it as a collection of isolated tables?

The previous two sections solved the "data trustworthiness" problem, but the "data comprehensibility" problem remains. AI engineers face physical tables such as `EQP_TBL` and `RECIPE_HDR`, while business problems are expressed in business language such as "this tool," "this lot of wafers," "this process step." The gap between the two needs an **industrial semantic layer** to bridge.

### 28.4.1 Why the Internet Data-Middle-Platform Model Cannot Be Copied Directly

Over the past decade, the internet industry's data-middle-platform model was widely promoted: a data lake consolidates all-domain data, wide tables unify definitions, and BI reports serve decisions. This model succeeded in internet scenarios, but fabs cannot copy it directly, because industrial data differs fundamentally from internet data:

**Physical anchoring of industrial data.** An internet click record is still a meaningful log out of context; but a pressure reading in industrial data is meaningless unless it maps to "which tool, which chamber, which moment, which process step." Physical anchoring requires the data model to preserve the complete tool-chamber-time-process dimensions, imposing extra requirements on the "data lake + wide table" model — if wide tables do not preserve these dimensions, the data loses its industrial value.

**High domain-semantic density.** Internet data field semantics are relatively simple (user ID, time, behavior type); in fab data, the same field `PRESSURE` has completely different meanings and value ranges across different tools, processes, and recipes; the same business concept (such as "yield") has different definitions in different departments. This "context determines semantics" characteristic is rarely seen in internet data-middle-platform scenarios.

**Real-time requirements and closed-loop feedback.** Internet middle platforms mainly serve post-hoc analysis (reports, recommendations); fab data must support real-time control (R2R control, FDC alarms) and decision closed loops. The chain from "being analyzed" to "being used" to "feedback to the line" must be closed, exceeding the "extract-analyze-report" scope of middle platforms.

**Conclusion**: the internet middle-platform model solved the "data retrieval" problem (centralizing data) but cannot solve the "semantic understanding" problem (letting users know what the data means) — this is exactly what the industrial semantic layer must add. The middle platform is the "porter of data"; the semantic layer is the "translator of data."

### 28.4.2 Concept and Positioning of the Industrial Semantic Layer

**Definition of the industrial semantic layer**: between the physical data layer (databases, files, equipment data) and the AI application layer, establish a layer of "business-object semantic abstraction" so that applications face business concepts such as "lot," "wafer," "equipment," "process step," "defect," and "parameter" rather than physical tables such as `EQP_TBL` and `RECIPE_HDR`.

Use an analogy to understand it: the semantic layer is the **"translation layer" of the fab** — translating table structures readable by IT engineers into business language understandable by process and AI engineers. In the traditional mode, an AI engineer asking "check the yield of Tool 3" must write SQL to JOIN four or five tables and know which equipment ID corresponds to Tool 3; with the semantic layer, he simply says "query equipment=ETCH-03, metric=yield," and the semantic layer handles the translation into the underlying query.

The three values of the industrial semantic layer:

- **Shielding underlying complexity**: applications no longer care about physical table structures, key mappings, or cross-system linkage — all encapsulated by the semantic layer.
- **Unifying definitions**: all consumers retrieve data through the same semantic layer, naturally using the same definitions — the definition list governed in Section 28.3 is solidified into unified business-object definitions through the semantic layer.
- **Controlled data-consumption interface**: AI applications (especially LLM/Agent) do not directly access underlying databases but consume data through the controlled interface provided by the semantic layer — this is both the security boundary and the locus of permission control (see Section 28.5.3).

**Architecture diagram of the semantic layer (text description)**: a three-layer structure. The bottom layer is the **physical data layer**, containing MES databases, YMS databases, FDC time-series stores, and inspection-image storage; the middle layer is the **industrial semantic layer**, composed of the ontology model and semantic services — the ontology defines business objects and relationships, and semantic services provide three capabilities: object queries, relationship traversal, and definition computation; the top layer is the **AI application layer**, including yield analysis, virtual metrology, root-cause analysis, and LLM/Agent applications. Data flows upward: applications query through semantic APIs, the semantic layer translates into physical queries and performs permission filtering, returning business-object-level results. The permission-control point sits between the semantic layer and the physical layer — all physical access passes through the semantic layer's authentication and filtering.

### 28.4.3 Designing a Semiconductor Domain Ontology

The core of the semantic layer is the **ontology** — an explicit, formalized description of business entities, relationships, and rules. A fab semantic layer can start from a minimal core ontology: six entities and a few relationship groups.

**Six core entities**:

| Entity | Meaning | Key attributes (example) |
| --- | --- | --- |
| Lot | batch, the basic management unit of wafer processing | LotID, product, route, status |
| Wafer | wafer, the physical processing object | WaferID, owning Lot, current step |
| Equipment | tool (including chamber) | EquipmentID, process category, status |
| ProcessStep | process step (recipe execution) | StepID, recipe name, parameter version |
| Defect | defect | DefectID, type, coordinates, size |
| Parameter | process parameter (metrology or FDC) | parameter name, value, timestamp |

**Core relationships between entities**:

```
Wafer -BELONGS_TO-> Lot           (wafer belongs to a lot)
Wafer -PROCESSED_ON-> Equipment   (wafer processed on a tool)
Equipment -EXECUTES-> ProcessStep (tool executes a process step)
Defect -OBSERVED_ON-> Wafer       (defect observed on a wafer)
ProcessStep -HAS_PARAMETER-> Parameter (process step has parameters)
Lot -HAS_TEST_RESULT-> yield data  (lot has test results)
```

**RCA scenario walkthrough**: use a concrete root-cause-analysis scenario to show the difference between "thinking at the semantic layer" and "joining tables." Question: "a lot's yield dropped sharply; find possible root causes." In the traditional table mode, the engineer must know the table structures of YMS, MES, and FDC and manually JOIN. In the semantic-layer mode, the query path is:

1. Locate the "yield anomaly" object at the semantic layer: query the lot's yield data and confirm the anomaly;
2. Follow `Defect -OBSERVED_ON-> Wafer` to find defects corresponding to the abnormal yield and their spatial distribution (wafer map);
3. Follow `Wafer -PROCESSED_ON-> Equipment` to find the tools and chambers that processed these wafers;
4. Follow `Equipment -EXECUTES-> ProcessStep` to locate the specific process step;
5. Follow `ProcessStep -HAS_PARAMETER-> Parameter` to compare the step's parameters with normal lots and identify deviations.

No physical table is touched throughout — the semantic layer translates "business queries" into "graph traversal + attribute queries." More importantly, this query path is **explainable**: each step corresponds to a clear business relationship, and AI applications' conclusions can be traced to specific ontology paths (this is the foundation of the GraphRAG in Section 28.5).

**Choice of formalization level**: the ontology does not need to adopt W3C standards such as OWL/RDF from the start. A pragmatic path starts from lightweight forms: define entities and relationships with property graphs or JSON Schema to satisfy application needs; upgrade to RDF/OWL when cross-organization sharing and reasoning capabilities (such as consistency checks) are needed. **Do not fetishize standards; evolve as needed** — the value of an ontology lies in "explicitly expressing business semantics," not in "using a certain standard."

### 28.4.4 Layered Knowledge-Graph Architecture

The ontology answers "what business objects look like," while a complete fab knowledge system requires three layers of graphs working together:

- **L1 data lineage graph**: dependencies among tables, fields, stored procedures, ETL jobs, and reports. Answers "where the data came from." It is the output of data governance (see Section 28.3) and the foundation of the entire knowledge system.
- **L2 business knowledge graph**: a relationship network of business entities, business rules, SOPs, historical cases, and defect knowledge. Answers "how the business operates." For example, the business rule "edge-ring defect → litho focus shift → check FEM window" is one piece of knowledge in the L2 graph.
- **L3 operational ontology**: with the semantic layer at its core, entities, relationships, and actions are invocable by the system. Answers "what AI can do." For example, the `hold_lot` action in the ontology can be executed by agents — the critical leap from "knowledge" to "action."

**Relationships among the three layers**: L1 is the foundation (L3 depends on L2, L2 depends on L1); L2 grows on top of L1, "translating" technical lineage into business semantics; L3 adds operability on top of L2. Architecturally, LLM/Agent interact only with L3, which references L2 knowledge and L1 lineage downward — ensuring AI does not touch raw data directly, with all access passing through the semantic layer's controlled interface (echoing the security design in Section 28.5.3).

**Architecture diagram of the layered knowledge graph (text description)**: three layers from bottom to top. The L1 layer has tables, fields, and stored procedures as nodes, with read/write/derived edges — the lineage graph collected automatically and manually; the L2 layer has business entities (Lot, Wafer, Equipment, Defect, Rule, SOP, Case) as nodes, with business edges (BELONGS_TO, PROCESSED_ON, RULE_OF, CITED_BY), jointly built by business experts and knowledge engineering; the L3 layer sits on top, with core ontology objects as nodes and added Action edges (hold_lot, create_workorder, release_lot); agents consume knowledge and execute actions through L3's API. Data flows: Agent request → L3 action/query → L2 business semantics → L1 physical data.

### 28.4.5 Comparison with Industry Approaches

Fab semantic layers and knowledge graphs are not new concepts; industry approaches exist for reference:

**Google One Knowledge Federation (OKF)**. OKF's philosophy is "federating knowledge from dispersed systems into a unified semantic view." It is conceptually aligned with the "unified semantic view across MES/FDC/YMS" goal — both emphasize not moving data but establishing cross-source semantic mappings. The difference: OKF targets internet-scale knowledge organization, while fabs need industrial physical semantics (tool-chamber-time anchoring), beyond OKF's general scenario.

**Palantir Ontology**. Palantir has mature industrial (especially semiconductor) deployments: its "Object-Link-Action" model directly corresponds to this book's L3 operational ontology — objects are business entities, links are entity relationships, actions are executable operations. Palantir's yield-improvement case with Samsung (see Chapter 21) is an industrial-grade validation of "semantic layer + AI" in fabs. Its core ideas are worth borrowing: object-oriented abstraction, unified semantics, executable actions.

| Approach | Core idea | Relationship to this chapter |
| --- | --- | --- |
| Google OKF | cross-source unified semantic view, knowledge federation | same goal as cross-system unified semantics, but not industry-specific |
| Palantir Ontology | Object-Link-Action, mature industrial deployment | direct reference for L3 operational ontology (Samsung/Merck Athinia cases) |
| This chapter's approach | three-layer graph + semantic layer, evolving to fab reality | borrows "object-oriented, semantically unified, actionable" ideas |

**Pragmatic attitude**: no need to copy any single approach. A fab should start from a minimal core ontology (six entities, a few relationship groups), first supporting one or two high-value scenarios (such as yield RCA), then expanding gradually — an ontology "grows," it is not "designed" once. Absorb the three ideas of "object-oriented, semantically unified, actionable," and advance according to the current system state and team capability, which is more reliable than pursuing a "one-step" solution.

> **Practical tip:** How to define the "minimum viable" boundary of the ontology? A practical criterion: **sufficient to support the query path of your next AI application.** If the next application is yield RCA, the ontology covering the six entities — Lot/Wafer/Equipment/ProcessStep/Defect/Parameter — and their associations is enough; do not model SOPs, personnel, and cost "completely" — that stalls ontology building at the "model-building" stage, failing to generate business value for a long time.

> **Section summary:**
> - The internet data-middle-platform solves "data retrieval"; the industrial semantic layer solves "semantic understanding"; the physical anchoring and high domain-semantic density of industrial data determine that the middle-platform model cannot be copied directly.
> - The industrial semantic layer is the "translation layer" between physical data and AI applications, with three values: shielding complexity, unifying definitions, and controlled consumption.
> - A fab core ontology starts from six entities (Lot/Wafer/Equipment/ProcessStep/Defect/Parameter); ontology query paths are themselves explainable, forming the basis of RCA and GraphRAG.
> - The knowledge graph has three layers: L1 lineage (where data comes from), L2 business knowledge (how business operates), L3 operational ontology (what AI can do); agents interact only with L3.
> - Reference the ideas of OKF and Palantir Ontology, but start minimal-viable to fab reality; do not fetishize standards or pursue one-step completeness.

---

## 28.5 LLM and Agent Data-Consumption Patterns: From "Querying Data" to "Deciding with Data"

> **Core question of this section**: With the semantic layer and knowledge graph in place, how can LLMs and Agents consume these data safely and effectively? What are the trade-offs of different retrieval and collaboration patterns?

Section 28.4 established the semantic layer and the three-layer knowledge graph — the infrastructure for AI data consumption. This section discusses the "last mile": how large language models (LLMs) and agents actually use this infrastructure. Three key questions: which retrieval method (vector RAG or GraphRAG), how multi-agent collaboration works, and how data-access permissions are controlled.

### 28.5.1 GraphRAG vs Traditional Vector RAG

RAG (Retrieval-Augmented Generation) is the mainstream technology for "attaching external knowledge" to LLMs. Two routes exist in fab scenarios:

**Traditional vector RAG.** Chunk documents or data, vectorize with an embedding model, retrieve by semantic similarity at query time, and stuff the most similar text chunks into the prompt for the LLM. Advantages: simple to implement and friendly to open-ended Q&A (e.g., "what are the requirements for the cleaning process in the SOP"). Limitation: **no multi-hop reasoning** — it can only retrieve "textually similar" content and cannot answer questions requiring cross-entity correlation. For example, "this lot's yield dropped — is it related to parameter drift on ETCH-03 over the past three days?" requires correlating four dimensions — lot, tool, FDC parameters, and defects — which vector-similarity retrieval cannot do.

**GraphRAG (Graph-based RAG)**. Retrieve over the knowledge graph (the three-layer graph in Section 28.4): first locate the relevant subgraph based on the question (which entities, along which relationships), then provide the entities, relationships, and attributes within the subgraph as structured context to the LLM. Advantages:

- **Answers multi-hop questions**: traversal along ontology paths naturally supports cross-entity reasoning such as "lot→tool→parameter→defect";
- **Explainable**: the LLM's answer can be traced to specific graph paths (which entity, which relationship), so engineers can verify "why it said that";
- **More precise answers**: structured context has higher information density than text chunks, with lower hallucination rates.

The cost: the knowledge graph must be built first (high cost, long cycle), and the retrieval chain is more complex (locating the subgraph + assembling context).

**Selection conclusion for industrial scenarios**:

| Dimension | Vector RAG | GraphRAG |
| --- | --- | --- |
| Applicable questions | document/spec Q&A (SOP, Spec, mechanisms) | data query and correlation analysis (yield, tools, lots) |
| Multi-hop reasoning | not supported | supported (along graph paths) |
| Explainability | low (text source only) | high (traceable to graph paths) |
| Build cost | low (documents + embedding only) | high (knowledge graph required) |
| Hallucination risk | higher | lower (structured context) |

**In practice the two are often combined**: GraphRAG answers structured-data questions (query yield, query correlations), while vector RAG answers knowledge-document questions (query SOP, query specs). In a "yield-anomaly diagnosis" session, GraphRAG first locates data evidence, then vector RAG supplements process-mechanism knowledge.

**Comparison case**: a user asks "a lot's yield dropped — which chamber parameter is abnormal?" Vector RAG returns several semantically similar text fragments (possibly irrelevant equipment-manual paragraphs), unable to give a structured answer; GraphRAG traverses the ontology path: locate the lot's yield data → find the processing tools and chambers → retrieve the FDC parameters for the corresponding period → compare with the normal baseline, outputting "ETCH-03 chamber pressure deviated 12% from baseline during period X, consistent with the yield-drop time window" — with the graph path attached for engineer verification.

### 28.5.2 Multi-Agent Collaboration Architecture

A single LLM call cannot accomplish complex industrial tasks; fab practice often adopts multi-agent collaboration. A typical four-agent division of labor:

- **Perception Agent**: monitors data changes — SPC alarms, FDC anomalies, YMS yield fluctuations — converting signals into structured events (e.g., "ETCH-03 chamber pressure exceeded limits for three consecutive lots").
- **Diagnosis Agent**: based on perception events, performs root-cause analysis along the knowledge graph (using the GraphRAG of Section 28.5.1), outputting candidate root causes and evidence chains.
- **Knowledge QA Agent**: answers engineers' natural-language questions, retrieving SOPs, specs, and historical reports (using vector RAG), supplementing process-mechanism knowledge.
- **Execution Agent**: executes actions under approval and permission constraints — hold lots, generate work orders, recommend recipe adjustments; execution requires human approval.

**Collaboration flow (using "a lot yield anomaly" as an example)**:

```
Perception Agent triggered (SPC alarm: yield below control limit)
  → Diagnosis Agent reasons along the ontology (GraphRAG locates defect→tool→parameter evidence)
  → Knowledge QA Agent supplements context (vector RAG retrieves similar cases and SOPs)
  → Execution Agent gives recommendations (candidate root causes + suggested actions)
  → Human approval (engineer confirms or rejects)
  → Execute action (hold lot / generate work order) and record audit log
```

**Human-in-the-Loop design** is an important difference between industrial and internet scenarios: agents are only "advisers"; critical actions (hold lots, change recipes, release lots) require human approval. The reason: the cost of actions in fabs is extremely high — wrongly holding a lot can lose hundreds of thousands of dollars; wrongly releasing may cause batch scrap. Agents can accelerate analysis and provide recommendations, but final decision authority must remain with engineers. This is both a technical constraint and a compliance/accountability requirement.

> **Practical tip:** The most common mistake in multi-agent deployment is going straight for a "fully automatic closed loop." The pragmatic path is **first "analysis enhancement," then "execution automation"**: phase one, agents only output diagnosis reports and recommendations, engineers execute manually; phase two, open automatic execution for low-risk actions (such as generating reports and querying data); phase three, consider executing high-risk actions (such as holding lots) under strict approval. Let engineers first "trust" the agent's analysis capability, then "authorize" its execution capability.

### 28.5.3 Data Permissions and Security Control

After LLMs and agents connect to data, security becomes the primary concern. Core principle: **LLMs do not directly access underlying databases**; all data consumption goes through the semantic layer, which implements row-level, column-level, and field-level permission filtering.

**Why design it this way**:

- **Prompt-injection risk**: data may contain malicious instructions (e.g., an SOP document says "ignore previous instructions"); an LLM reading the database directly may be induced to execute dangerous operations. The semantic layer, as an intermediate layer, limits what the LLM can see and which queries it can execute.
- **Unauthorized-query risk**: the LLM may generate queries beyond the user's permissions (e.g., cross-customer queries, accessing sensitive fields). The semantic layer performs permission checks when translating queries, rejecting unauthorized requests.
- **Minimum-data-exposure principle**: models should not touch sensitive data they do not need — customer-product information, IP-related recipe details, payroll and cost data. The semantic layer exposes only necessary fields by role.

**Three elements of security control**:

- **Access control**: the semantic layer implements role-permission mapping (process engineers can query FDC and metrology; equipment engineers can query equipment logs; management can query cost KPIs), with permission filtering before query execution.
- **Audit logs**: record "who (user/agent) queried what data through which interface and executed what action," supporting post-hoc tracing — the foundation of compliance audits.
- **Sensitive-field masking**: customer IDs, product codes, and similar fields are masked or generalized before being returned to the LLM, preventing the model from "remembering" sensitive information.

**Linkage with foundry-service transformation**: Chapter 13's foundry-service transformation phase has data security and multi-customer isolation as core tasks. The semantic-layer security design of this section is precisely the technical foundation for this requirement — implementing tenant-level isolation through the semantic layer (Customer A's agents cannot see Customer B's data), echoing Chapter 13's "data security" and Chapter 21's Palantir "Object-Link-Action" model.

> **Section summary:**
> - Data-query/correlation questions favor GraphRAG (multi-hop, explainable); document/spec questions are served well by vector RAG; the two are often combined.
> - Multi-agent collaboration adopts a perception-diagnosis-knowledge-QA-execution four-role division, with "human-in-the-loop" at the core — agents advise, humans decide.
> - The security principle is that LLMs do not directly access underlying databases; all access goes through the semantic layer for permission filtering, auditing, and masking.
> - The semantic-layer security design provides the technical foundation for multi-customer data isolation in foundry services.

---

## 28.6 Implementation Path and Phased Rollout: From Data to Value

> **Core question of this section**: The first five sections established a complete technical framework from data sources to the semantic layer — but where does rollout start? How can we avoid "building a lot of infrastructure without generating business value"?

Once the technical framework is clear, the rollout path determines success or failure. The biggest risk in fab data-architecture construction is not technical difficulty but **tempo out of control** — either pursuing perfection from the start (an ontology built for three months without being used once) or skipping governance and going straight to AI (models learning wrong labels). This section gives a validated four-phase roadmap, with clear milestones and acceptance criteria for each phase.

### 28.6.1 Overview of the Four-Phase Roadmap

**Phase 1: Data detox and lineage baseline (1-3 months)**. Goal: figure out "where the data is, what it looks like, and who depends on whom." Specific work:

- Inventory all core data sources and build a data-source list (against the seven sources of Section 28.1);
- Build business metadata for top key fields (against the field dictionary of Section 28.3.2);
- Establish a lineage baseline (static parsing + manual annotation, against Section 28.3.3);
- Establish basic data-quality rules (missing, anomaly, definitions) with automated alerts.

**Phase 2: Semantic-layer construction and single-point PoC (3-6 months)**. Goal: prove the value of "semantic layer + AI" with one high-value scenario. Specific work:

- Design and implement a minimal core ontology (six entities, against Section 28.4.3);
- Build a semantic-layer MVP (three capabilities: object queries, relationship traversal, definition computation);
- Choose a high-value scenario (usually yield RCA or virtual metrology) and complete the "query→analysis→conclusion" loop;
- Produce quantifiable value proof (e.g., RCA time reduced from X days to Y hours).

**Phase 3: Multi-agent collaboration and closed-loop validation (6-12 months)**. Goal: from "single-point analysis" to "collaborative closed loop." Specific work:

- Build four types of agents on the semantic layer (against Section 28.5.2);
- Complete the "perception→diagnosis→recommendation" chain, starting with analysis enhancement (agents produce reports, humans execute);
- Pilot in a small scope (single department, single product line) to validate stability and value;
- Establish the human-approval flow and audit mechanism.

**Phase 4: Ontology deepening and scaled rollout (12-24 months)**. Goal: from "pilot" to "scale." Specific work:

- Expand the ontology (add actions, rules, historical cases; upgrade to L3 operational ontology);
- Roll out to multiple departments (process, equipment, manufacturing, quality);
- Establish a continuous governance and operations mechanism (definition change management, ontology version management, knowledge-annotation process);
- Form a "data-knowledge-decision" self-reinforcing closed loop — each RCA result is deposited into the graph as new knowledge, improving the quality of the next diagnosis.

### 28.6.2 Milestones and Acceptance Criteria per Phase

Each phase requires "measurable business value" as the acceptance criterion, not "technical functionality completed":

| Phase | Key milestones | Example acceptance criteria |
| --- | --- | --- |
| Phase 1 | data-source list, field dictionary, lineage baseline, quality rules | 100% of core data sources in the list; Top-20 key definitions have business metadata; table-level lineage coverage ≥80%; quality rules live with automated alerts |
| Phase 2 | core ontology, semantic-layer MVP, PoC closed loop | ontology covers six entities; semantic layer supports at least 3 types of typical queries; PoC end-to-end runs with ≥90% agreement with manual conclusions |
| Phase 3 | four agent types, collaboration chain, pilot | all 4 agent types runnable; end-to-end example (anomaly→diagnosis→recommendation) stable in the pilot scope; human-approval flow closed loop; latency and throughput meet targets |
| Phase 4 | ontology expansion, multi-department rollout, governance mechanism | ontology covers new entities and actions; ≥2 departments use at scale; supports ≥N real decisions within six months; continuous governance mechanism established |

> **Practical tip:** Three criteria for selecting the Phase-2 PoC scenario: first, **data readiness** (the data needed by the scenario is governed and definitions are clear); second, **quantifiable value** (you can state clearly "current time X, target Y"); third, **controlled failure cost** (getting it wrong does not affect the line). Yield RCA is the first choice — the data exists, the value is intuitive, and it is read-only analysis that does not touch the line. Avoid high-risk scenarios such as "real-time tool control" as the first PoC.

### 28.6.3 Common Pitfalls and How to Avoid Them

**Pitfall 1: Pursuing a perfect ontology from the start.** An ontology "grows"; it is not "designed." Pursuing complete coverage of all entities and relationships leads to "an ontology built for three months without being used once." Start from a minimal viable ontology (six entities) and expand as you use it — each ontology expansion should come from a real query requirement.

**Pitfall 2: Data quality killing AI projects.** Most AI model errors come from "label/definition errors," not "bad algorithms." Skipping Phase 1 and going straight to AI means the model may learn wrong patterns. **Data governance must take priority over model tuning** — first use the field dictionary and lineage to solve "whether the labels are correct," then discuss "whether the model is accurate."

**Pitfall 3: Ignoring the "people" in tacit knowledge.** Lineage and dictionaries can only record knowledge that is "already known"; they cannot capture "in-people's-heads" experience. Key knowledge must be supplemented through expert interviews and RCA retrospectives, and must be **institutionalized** — establish a data-steward role so that "every key definition has someone responsible for explaining it" becomes an organizational rule, not individual self-discipline.

**Pitfall 4: LLM permissions out of control.** Establish security boundaries first (semantic-layer permissions + approval flows), then open agent capabilities. Do not "open first, fix later" — after an LLM connects to data, the cost of one unauthorized query or one prompt-injection attack can far exceed the development time saved.

**Pitfall 5: Organizational collaboration absent.** Data governance must be jointly built by IT, process, equipment, and quality departments. Single-department leadership easily produces an "IT data dictionary" — technically correct but divorced from business. Recommend a cross-department data-governance working group: business departments define definitions, IT handles technical implementation, quality handles acceptance.

> **Section summary:**
> - Rollout has four phases: data detox and lineage baseline → semantic layer and single-point PoC → multi-agent collaboration closed loop → ontology scale-out, from 1-3 months to 12-24 months per phase.
> - Acceptance criteria must be "value quantifiable" (e.g., RCA time from X days to Y hours), not "technical functionality completed."
> - Five common pitfalls: perfect ontology, data quality killing AI, ignoring the people in tacit knowledge, LLM permissions out of control, and organizational collaboration absent.
> - Core tempo principles: data governance before model tuning, minimal-viable start, security boundaries before capability opening.

---

> **Chapter experiment**: Experiment 22 in Chapter 27 (`experiments/fabwiki`) compiles warehouse tacit knowledge (magic codes / prefix codes / field-type traps / definition-timing traps) into OKF knowledge packages and a navigable knowledge graph that drives deterministic Text2SQL — a runnable implementation of this chapter's "data governance and semantic layer" ideas, fully demonstrable offline without a key.

## Chapter Summary

The wafer-fab data architecture is the foundation of all AI applications in this book. This chapter follows the logic of "what data is → is the data trustworthy → is the data understandable → how AI uses it → how to implement it" and gives a complete answer:

**What data is**: fabs have seven core data sources, with time granularity spanning six orders of magnitude (from millisecond FDC to daily ERP); any valuable analysis requires cross-system retrieval.

**Is the data trustworthy**: lineage is complex and tacit knowledge is dispersed; data governance (quality, standardization, metadata, lineage) makes data trustworthy, traceable, and reusable — the essence of data governance is knowledge capture and transmission.

**Is the data understandable**: the internet middle-platform cannot solve industrial semantic understanding; fabs need an industrial semantic layer and a three-layer knowledge graph (L1 lineage → L2 business knowledge → L3 operational ontology), letting AI understand data as business objects rather than physical tables.

**How AI uses it**: data-query questions use GraphRAG, document questions use vector RAG; multi-agent collaboration adopts perception-diagnosis-QA-execution roles with human-in-the-loop; for security, LLMs do not directly access databases — all consumption goes through the semantic layer.

**How to implement**: a four-phase roadmap — data detox and lineage baseline → semantic layer and single-point PoC → multi-agent collaboration closed loop → ontology scale-out — with measurable business value at each phase.

For fabs, the real goal of data-architecture construction is not "building a data platform" but **making data a trustworthy, understandable, and actionable organizational asset**. When engineers and AI systems both think based on the same trustworthy semantics, the AI applications discussed in later chapters — yield prediction, virtual metrology, predictive maintenance, root-cause analysis — have a solid foundation on which to stand.

F and Palantir Ontology, but start minimal-viable to fab reality; do not fetishize standards or pursue one-step completeness.



