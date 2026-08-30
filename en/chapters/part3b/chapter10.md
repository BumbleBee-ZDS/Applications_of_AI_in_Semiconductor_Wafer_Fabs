# Chapter 10: Capacity Ramp and Capacity Planning — From "Doing It Right" to "Doing It in Volume"

## 10.1 What Is a Capacity Ramp

The previous chapter discussed the yield ramp — solving "how to make chips right." This chapter discusses another equally critical ramp: the capacity ramp, solving "how to make chips in volume." An advanced fab costs more than $15 billion; every 1% drop in capacity utilization wastes tens of millions of dollars per year in depreciation and fixed costs. The goal of the capacity ramp is to raise output (wafer out) to design capacity as quickly as possible after a new line starts production, and to keep it stable.

### Capacity Ramp vs. Yield Ramp

The two appear independent but are deeply coupled:

| Dimension | Yield Ramp | Capacity Ramp |
| --- | --- | --- |
| Core metric | Yield (%): fraction of good chips | Output (wafers/month), capacity utilization |
| Question answered | How to do it right? | How to do it in volume? |
| Main constraints | Defects, process windows, learning rate | Equipment, logistics, bottlenecks, cycle time |
| Mutual influence | Low yield wastes capacity (many rejected wafers produced) | Overly fast capacity ramp dilutes experiment resources and slows yield learning |

In the early ramp, yield ramp and capacity ramp pull against each other: large numbers of experimental wafers consume capacity, but they are essential to yield learning. A good ramp strategy balances both — limiting capacity expansion while yield is unstable, and accelerating capacity release as yield approaches target.

### The Three Levels of Capacity

- **Tool capacity:** the rated capacity of machines, affected by equipment availability, process time, and maintenance cycles
- **Utilization:** actual output as a fraction of rated capacity; the equipment-level efficiency indicator
- **Wafer out:** the fab's overall output; the final result, constrained by bottleneck tools, logistics, and scheduling

These three are linked through metrics such as OEE (overall equipment effectiveness) — OEE = availability × performance × quality — the core dashboard of capacity management.

![Capacity ramp process and bottleneck management](../../images/flow_ch10_capacity_ramp_flow.png)

*Figure 10-1: Capacity ramp process and the bottleneck management loop*

## 10.2 The Levels of Capacity Planning

Capacity ramp is not simply "buy more equipment"; it is a multi-level planning problem from strategy to execution.

### Strategic Capacity Planning and CAPEX

Strategic capacity planning answers "how much capacity to build over the next few years." Fab construction takes 2–3 years, so capacity decisions must be made well in advance. Capacity planning models typically consider: market demand forecasts, process-node transition timing, equipment lead times (advanced lithography tools have lead times measured in years), and depreciation and capital costs. A new 3nm fab requires more than 15 EUV scanners at over $150 million each — there is almost no room for error in capacity decisions.

### Bottleneck Analysis and TOC

The theory of constraints (TOC) states that any system's capacity is determined by its bottleneck. In fabs, the bottleneck is usually a scarce tool class (e.g., EUV lithography, high-precision metrology) or a specific process layer (e.g., a particular etch step). When the bottleneck tool's utilization reaches 100%, fab output hits its ceiling; bottleneck shifting (the bottleneck moving from one tool to another) is a common phenomenon during capacity ramp that requires continuous monitoring.

### Capacity Balancing and Bottleneck Shifting

The essence of capacity ramp is a process of "bottleneck shifting": when a bottleneck is relieved (adding tools, optimizing process time), the bottleneck moves to the next link. Capacity planning must dynamically track the bottleneck location to avoid "over-investing in links that are no longer bottlenecks."

## 10.3 Tool Qualification and Capacity Release

Capacity release of a new line is not "equipment arrives, output begins"; every new tool must pass a strict qualification process before entering production.

### New Tool Acceptance and Qualification

After installation, a tool must pass installation acceptance testing (IAT), process qualification (PQ), and production validation (PV). In PV, the tool must reproduce process results consistent with existing tools — including consistency and stability of CD, film thickness, defect rate, and other parameters. The qualification cycle of an EUV scanner can take months, and qualification progress directly determines the capacity ramp tempo.

### Tool Matching

When multiple tools run in parallel, inter-tool parameter differences (tool drift, component aging differences) cause non-uniform output quality. Tool matching quantifies tool-to-tool differences through statistical methods and adjusts each tool's recipe parameters to align output. When matching is poor, yield differences between lots across tools can reach several percentage points — during capacity ramp, the influx of new tools makes matching problems more prominent.

### Phased Tool Release Strategy

During ramp, teams face a trade-off between "release more tools to accelerate ramp" and "insufficiently validated tools affecting quality." A mature strategy is phased release: first run qualification wafers to stabilize the tool and match the reference tool, then gradually increase the production-wafer ratio, while continuously monitoring new-tool stability with SPC and FDC.

## 10.4 Optimization Methods for Capacity Ramp

### Scheduling and Dispatching

During ramp, the WIP (work-in-process) distribution changes rapidly, and traditional static dispatch rules (FIFO, due-date priority) cannot cope. Dynamic dispatch strategies adjust dispatch decisions in real time based on current tool status, WIP distribution, and due-date pressure — "which tool does this lot go to, which lot runs first." Optimization targets include shortening cycle time, raising bottleneck utilization, and balancing tool loads. See Chapter 7 for detailed discussion of scheduling and dispatch.

### AMHS Logistics and Automation

Wafers in the fab are moved automatically by the overhead hoist transport (AMHS) system. During ramp, logistics bottlenecks (hoist congestion, rail scheduling) can become hidden capacity bottlenecks — tools idle waiting for transport while transport is congested. AMHS health management and intelligent scheduling directly affect actual fab output.

### Virtual Metrology and Skip-Lot Inspection

Metrology tools are expensive capacity consumers: key-step metrology of every wafer occupies metrology-tool capacity. Virtual metrology (VM) predicts metrology results from equipment sensor data and allows "skip inspection" or "sampled inspection" for lots on stable tools, freeing metrology capacity — highly effective in ramp phases when metrology is the bottleneck.

### PM Optimization

Preventive maintenance (PM) occupies tool time: too-frequent PM wastes capacity; too-little PM increases breakdown risk. Predictive maintenance dynamically schedules PM timing based on equipment condition data, balancing breakdown risk against capacity loss. See Chapter 8 for the detailed technology.

## 10.5 AI in Capacity Ramp

Every link of the capacity ramp has a role for AI:

| Link | AI Application | Goal |
| --- | --- | --- |
| Equipment maintenance | Predictive maintenance (failure prediction, RUL estimation) | Reduce unscheduled downtime, raise availability |
| Scheduling and dispatch | RL-based dynamic scheduling (DQN/MARL) | Shorten cycle time, raise bottleneck utilization (see Chapter 13) |
| Metrology capacity | Virtual metrology, skip-lot decisions | Free up metrology-tool capacity |
| Bottleneck management | Capacity prediction models, WIP flow prediction | Identify bottleneck shifts early, guide capacity investment |
| Fab-wide simulation | Digital twins (line simulation) | Validate capacity decisions in a virtual fab first |

### From Experience-Based to Data-Driven Capacity Management

Traditional capacity management relies on the judgment of senior production engineers — "where is the bottleneck, when will it shift, how many tools should be released." AI is making this process data-driven: capacity prediction models forecast the output curve for the coming weeks from historical output and tool status; WIP flow prediction models identify bottlenecks before they form; RL schedulers train in simulation and deploy to the line for dynamic optimization. Together these technologies form the closed loop of "digital capacity management" — ramp decisions move from gut feel to data-driven.

## 10.6 Practical Cases

- **AMHS health management:** GlobalFoundries deployed AI-driven AMHS health management, detecting anomalies early from hoist-system operating data and reducing the impact of logistics congestion on output
- **Intelligent scheduling validation:** the AISSI project validated deep RL scheduling (DQN, MARL) on real industrial datasets — achieving about 9% output improvement in simulation and line validation, confirming that RL scheduling can move from research to the production line (see Chapter 13)
- **Digital capacity planning:** several leading fabs use digital-twin platforms (e.g., NVIDIA Omniverse) to simulate the entire line, validating capacity-expansion plans in a virtual environment before executing them in reality, significantly reducing the risk of capacity decisions (see Chapter 18)
- **Virtual metrology freeing capacity:** SK hynix's Panoptes virtual metrology shortened metrology cycles while freeing metrology-tool capacity, indirectly supporting line output improvement (see Chapter 12)

## 10.7 Chapter Summary

The capacity ramp and the yield ramp are the two main lines of a fab's ramp phase: yield solves "doing it right," capacity solves "doing it in volume," and the two constrain each other, jointly determining the return on investment of a new line. The essence of a capacity ramp is systematic bottleneck management — from tool qualification and tool matching to scheduling, dispatch, and logistics optimization, every link can be a hidden bottleneck. AI's role in capacity ramp is to upgrade "experience-driven capacity management" to "data-driven capacity management": predictive maintenance protects availability, RL optimizes scheduling and dispatch, virtual metrology frees metrology capacity, and digital twins reduce decision risk. For fabs, the speed of the capacity ramp is shifting from "stacking equipment" to "intelligent operations capability."
