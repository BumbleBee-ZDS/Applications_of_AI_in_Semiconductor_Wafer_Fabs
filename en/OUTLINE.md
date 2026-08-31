# Detailed Table of Contents

## Part I: Foundations

### Chapter 1: Why AI × Semiconductor Wafer Fabs

- 1.1 The Twilight of Moore's Law and the Dawn of AI
- 1.2 The Fab's Dilemma: Complexity Explosion
  - Growth in layer count and step count at advanced nodes
  - Diminishing marginal returns on yield improvement costs
  - The ceiling of human expertise
- 1.3 AI's Value Proposition in the Fab
  - Cost reduction: Reducing equipment idle time and wafer scrap
  - Efficiency gains: Shortening process development cycles and accelerating yield ramp
  - Digitizing expertise: Converting senior engineers' tacit knowledge into reusable models
- 1.4 Global Landscape of AI Adoption in Wafer Fabs
  - Practices at TSMC, Samsung, Intel, SMIC, and other leading enterprises
- 1.5 This Book's Objectives and Organization

### Chapter 2: A Brief History of AI — From the 1956 Dartmouth Conference

- 2.1 The Dartmouth Conference: The Birth of AI
  - Summer 1956, Dartmouth College
  - McCarthy, Minsky, Shannon, Rochester
  - The formal introduction of the term "Artificial Intelligence"
- 2.2 The First Boom and Winter (1956–1974)
  - The golden age of Symbolism: Logic Theorist, GPS, ELIZA, SHRDLU
  - The 1973 Lighthill Report and the first AI winter
- 2.3 The Expert Systems Era (1974–1987)
  - Commercial success of DENDRAL and MYCIN
  - Japan's Fifth Generation Computer Project
  - The 1987 Lisp machine market collapse and the second AI winter
- 2.4 Statistical Learning and the Connectionist Revival (1987–2012)
  - The rediscovery of the backpropagation algorithm
  - The rise of SVM and Bayesian networks
  - Hinton's Deep Belief Networks in 2006
- 2.5 The Deep Learning Revolution (2012–2020)
  - ImageNet and AlexNet
  - AlphaGo defeats Lee Sedol
  - Deep learning's penetration into industrial domains
- 2.6 The Era of Large Models (2020–Present)
  - The GPT series and the Transformer architecture
  - The rise of the Agent concept
  - LLM exploration in industrial scenarios
- 2.7 The Divergence and Convergence of AI's Three Major Schools
  - The philosophical roots of Symbolism, Connectionism, and Behaviorism
  - The trend from opposition toward integration

---

## Part II: The Three Major Schools of AI

### Chapter 3: Symbolism — From Rules to Knowledge

- 3.1 Philosophical Roots: The Rationalist Tradition
  - From Leibniz's "calculus of thought" to Frege's formal logic
  - Core proposition: Thinking is symbol manipulation
- 3.2 The Physical Symbol System Hypothesis
  - Newell & Simon's classic assertion
  - The triad of Knowledge Representation → Reasoning → Problem Solving
- 3.3 Technological Evolution
  - Early: Logical reasoning (Logic Theorist, GPS)
  - Middle: Expert systems (MYCIN, DENDRAL)
  - Mature: Knowledge Graphs and Ontology
  - Contemporary: Neuro-Symbolic AI
- 3.4 Current Technical Frameworks
  - Knowledge representation: OWL, RDF, Knowledge Graph
  - Reasoning engines: Prolog, Datalog, SPARQL
  - Expert system shells: CLIPS, Jess
  - Knowledge graph platforms: Neo4j, Stardog
- 3.5 Strengths and Limitations
  - Strong interpretability, suitable for rule-explicit scenarios
  - Knowledge acquisition bottleneck, inability to handle ambiguity

### Chapter 4: Connectionism — From Perceptrons to Deep Learning

- 4.1 Philosophical Roots: Empiricism and Brain Science
  - Hebb's learning rule and the McCulloch-Pitts neuron model
  - Core proposition: Intelligence arises from the adjustment of neuronal connections
- 4.2 Core Ideas
  - Distributed representation
  - End-to-end learning from data
  - Emergent abilities
- 4.3 Technological Evolution
  - 1958 Perceptron (Rosenblatt)
  - 1969 Minsky's XOR critique
  - 1986 Backpropagation (Rumelhart, Hinton, Williams)
  - 2006 Deep Learning (Hinton)
  - 2012 AlexNet
  - 2017 Transformer (Attention is All You Need)
- 4.4 Current Technical Frameworks
  - CNN, RNN/LSTM/GRU
  - Transformer and Attention mechanism
  - Self-supervised learning and the pre-training–fine-tuning paradigm
- 4.5 Strengths and Limitations
  - Powerful pattern recognition and generalization capabilities
  - Black-box nature, data hunger, lack of interpretability

### Chapter 5: Behaviorism — From Cybernetics to Reinforcement Learning

- 5.1 Philosophical Roots: Cybernetics and Evolutionary Theory
  - Wiener's cybernetics
  - Core proposition: Intelligence arises from interactive feedback with the environment
- 5.2 Core Ideas
  - The perception–action loop
  - Reward-driven learning
  - Trial-and-error and evolution
- 5.3 Technological Evolution
  - 1948 Cybernetics (Wiener)
  - 1950s Behaviorist psychology (Skinner)
  - 1989 Q-Learning (Watkins)
  - 2013 DQN (DeepMind)
  - 2016 AlphaGo
  - 2017 AlphaZero
- 5.4 Current Technical Frameworks
  - Q-Learning, Policy Gradient, PPO, SAC
  - Multi-Agent Reinforcement Learning (MARL)
  - Imitation Learning and Offline RL
- 5.5 Strengths and Limitations
  - Suited for sequential decision optimization
  - Low sample efficiency, difficult reward design

---

## Part III: The Three Core Departments of Semiconductor Wafer Fabs

### Chapter 6: Process Integration (PID) and Yield Engineering (YED)

- 6.1 Department Positioning and Responsibilities
  - PID: Process Integration, ensuring full-flow process consistency
  - YED: Yield Engineering, monitoring, analyzing, and improving yield
- 6.2 Core Business Processes
  - New Product Introduction (NPI) and process development
  - Process window definition and DOE
  - Yield Ramp
  - Yield management and defect analysis
- 6.3 Key Technologies and Methods
  - Electrical testing (WAT/CP/FT)
  - Defect detection (ADI/AEI)
  - FDC (Fault Detection & Classification)
  - Process window analysis
- 6.4 Challenges
  - Complex process parameter interaction effects
  - Difficulty in yield root cause localization
  - NPI cycle compression pressure
- 6.5 Practice Research: Real-World AI Deployment Cases in PID/YED
  - Intel: AI-driven GFA automated detection system
  - SK Hynix/Gauss Labs: Panoptes Virtual Metrology system
  - Micron: Smart Sight smart manufacturing system
  - Lam Research: Fabex Yield Optimizer
  - NVIDIA: Vision foundation models for wafer defect classification
  - Industry tool ecosystem

### Chapter 7: Manufacturing Division (MFG)

- 7.1 Department Positioning and Responsibilities
  - Production scheduling and dispatching
  - Capacity management and bottleneck optimization
  - Work-in-Process (WIP) management
- 7.2 Core Business Processes
  - Production planning and work order management
  - Dispatching rules and exception handling
  - Equipment maintenance scheduling
- 7.3 Key Technologies and Methods
  - MES (Manufacturing Execution System)
  - APS (Advanced Planning and Scheduling)
  - Bottleneck analysis (Theory of Constraints)
  - OEE (Overall Equipment Effectiveness)
- 7.4 Challenges
  - Scheduling complexity of reentrant flow lines
  - Multi-product mixed production
  - Balancing capacity utilization and delivery deadlines
  - Event-driven dynamic adjustment
- 7.5 Practice Research: Real-World AI Deployment Cases in MFG
  - TSMC: Intelligent Operations System
  - Samsung: AI Megafactory
  - GlobalFoundries: AI-driven AMHS health management
  - Goxel/Tongfang: Malaysia 12-inch fab AI-CIM system
  - Micron: Enterprise-grade AI manufacturing
  - Validation of reinforcement learning in production scheduling

### Chapter 8: Process Engineering (PE) and Equipment Engineering (EE)

- 8.1 Department Positioning and Responsibilities
  - PE: Process parameter development and optimization
  - EE: Equipment health monitoring and maintenance
- 8.2 Core Business Processes
  - Recipe development and validation
  - Equipment parameter tuning
  - Preventive Maintenance (PM) planning
  - Tool Matching
- 8.3 Key Technologies and Methods
  - SPC (Statistical Process Control)
  - FDC (Fault Detection and Classification)
  - R2R (Run-to-Run control)
  - Predictive Maintenance
- 8.4 Challenges
  - Parameter drift due to equipment aging
  - Inter-tool variability
  - Time-consuming recipe development
- 8.5 Practice Research: Real-World AI Deployment Cases in PE/EE
  - Intel: IIoT predictive maintenance system
  - Applied Materials: AIx platform and GPU-accelerated simulation
  - ASML: Generative AI for lithography optimization
  - MST NeuroBox: AI-driven R2R and chamber matching
  - Industry benchmark data for equipment predictive maintenance
  - KLA: AI-driven defect detection and process control

---
---

## Part III-B: Key Business Scenario Series

### Chapter 9: Yield Ramp — The "Valley of Death" of Semiconductor Manufacturing

- 9.1 Why Yield Ramp Is So Difficult
  - The S-shaped curve and the 12-24 month ramp cycle
  - Explosive growth in process step count (from ~300 steps at 28nm to 1,500+ at 3nm)
  - Device structure evolution (FinFET→GAA→CFET) and economic constraints on the learning rate
- 9.2 Defect Root Cause Analysis (RCA) — The Starting Point
  - Detection and analysis toolchain (KLA scan + SEM review / EDX / TEM / EFA)
  - The 5W1H principle of RCA
  - Systematic defects (70%) vs. random defects (30%)
- 9.3 Process Window Quantification
  - DOE and process window boundary, the PWI index
  - FEM for lithography and 3D DOE for etch, Cpk ≥ 1.67 (5σ)
- 9.4 Yield Models and Prediction
  - Poisson / Murphy / negative binomial models
  - Critical area and VSB/MCM correction
  - ML yield prediction (yieldHub platform, 85%+ accuracy)
- 9.5 Design-Technology Co-Optimization (DTCO)
  - Design rules and process windows, critical area minimization, the AI-ization of DTCO
- 9.6 Yield Learning Curve Management
  - Yield learning rate, Pareto analysis and prioritization, phase-based strategy
- 9.7 The Role of AI in Yield Ramp
  - Symbolism (RCA knowledge graphs), Connectionism (defect classification / yield prediction), Behaviorism (DOE optimization)
- 9.8 Practical Cases
- 9.9 Chapter Summary

### Chapter 10: Capacity Ramp and Capacity Planning — From "Doing It Right" to "Doing It in Volume"

- 10.1 What Is a Capacity Ramp
  - Capacity ramp vs. yield ramp
  - The three levels of capacity (tool capacity / utilization / wafer out)
- 10.2 The Levels of Capacity Planning
  - Strategic capacity planning and CAPEX
  - Bottleneck analysis and TOC, bottleneck shifting
- 10.3 Tool Qualification and Capacity Release
  - New tool acceptance and qualification, tool matching, phased release
- 10.4 Optimization Methods for Capacity Ramp
  - Scheduling and dispatch, AMHS logistics, virtual metrology and skip-lot inspection, PM optimization
- 10.5 AI in Capacity Ramp
  - Predictive maintenance, RL dynamic scheduling, capacity prediction models, digital twins
- 10.6 Practical Cases
- 10.7 Chapter Summary

---

## Part III-C: Construction and Ramp Phase

### Chapter 11: The Construction and Ramp Phase — From "Building the Fab" to "Ramping Output"

- 11.1 Phase Overview: Business Characteristics and Core Contradictions
  - The three-phase lifecycle of a wafer fab (construction / mature / transformation)
  - High investment, high uncertainty, high time pressure
- 11.2 Task 1: Yield Analysis
  - The particularity of construction-phase yield problems (few samples, unsettled physics, coupled root causes)
  - Wafer map analysis, defect Pareto, RCA, yield model calibration
  - AI roles: transfer learning, hybrid physics+data modeling, knowledge-graph-assisted RCA
- 11.3 Task 2: Virtual Metrology
  - Predicting metrology results from FDC signals, skip/sample decisions
  - Model cold start, process drift, trust building
- 11.4 Task 3: Defect Inspection
  - ADC auto defect classification, new-defect-class discovery
  - Deep-learning inspection, semi-supervised/unsupervised new-defect discovery
- 11.5 Key Points for AI Deployment in the Construction Phase
  - Data cold start, data-asset awareness, ramp-metric-driven
- 11.6 Chapter Summary

---

## Part III-D: Mature Mass Production

### Chapter 12: Mature Mass Production — Efficiency and Resilience in Stable Operations

- 12.1 Phase Overview: Core Contradictions After Stable Production
  - Cost, efficiency, quality consistency
- 12.2 Task 1: Smart Scheduling
  - Mixed-product production and dynamic disturbances
  - Prediction layer + decision layer: RL dynamic scheduling (see Chapter 16)
- 12.3 Task 2: Predictive Maintenance
  - RUL prediction, failure early warning, maintenance decision optimization
- 12.4 Task 3: Energy Management
  - Energy monitoring / prediction / dynamic optimization
  - Off-peak production, tool standby strategies, green manufacturing
- 12.5 Key Points for AI Deployment in the Mature Phase
  - ROI orientation, deep integration with MES/APC, continuous iteration
- 12.6 Chapter Summary

---

## Part III-E: Foundry Service Transformation

### Chapter 13: Foundry Service Transformation — From "Manufacturing" to "Service"

- 13.1 Phase Overview: Business Characteristics of Foundry Services
  - Multi-customer multi-project parallelism, IP protection, trust as the core asset
- 13.2 Task 1: NPI Collaboration
  - Joint NPI scheduling, design-technology co-optimization (DTCO)
  - NPI knowledge base
- 13.3 Task 2: Data Security
  - Tenant isolation, access control, DLP, audit trail
  - Anomalous access detection, data masking, federated learning
- 13.4 Task 3: Supply Chain Transparency
  - End-to-end visibility, risk prediction, Clear-to-Build
  - Case: Palantir Foundry's three workflows
- 13.5 Key Points for AI Deployment in the Transformation Phase
  - Trust before technology, multi-party collaboration, service-metric orientation
- 13.6 Chapter Summary


## Part IV: Cross-Application of AI's Three Major Schools in Wafer Fabs

### Chapter 14: Applications of Symbolism in the Wafer Fab

- 14.1 Expert Systems in Process Diagnosis
  - PID/YED: Defect root cause analysis expert systems
  - PE/EE: Equipment fault diagnosis expert systems
- 14.2 Knowledge Graphs in Yield Management
  - Wafer fab process knowledge graph construction
  - Defect–process–equipment correlation reasoning
  - Knowledge-based traceability of yield issues
- 14.3 Rule Engines in Manufacturing Scheduling
  - MFG: Symbolic representation of dispatching rules
  - Explicit modeling of process constraints
- 14.4 Ontology in Process Integration
  - Ontological modeling of process flows
  - Cross-departmental knowledge sharing
- 14.5 Case Study: A 12-inch fab's knowledge graph–based yield analysis system
- 14.6 Practice Research: Symbolism tools and deployment cases
  - Samsung: Knowledge graph + LLM for sensor anomaly detection
  - yieldWerx: Root cause knowledge graphs
  - IKAS: Smart RCA platform
  - Historical perspective: Evolution of expert systems in semiconductor manufacturing (BIPS/GID3/CLIPS)
  - Frontiers of Neuro-Symbolic AI

### Chapter 15: Applications of Connectionism in the Wafer Fab

- 15.1 Deep Learning in Yield Prediction
  - PID/YED: CNN-based wafer map defect classification
  - Yield prediction models
  - Defect pattern recognition
- 15.2 Time-Series Models in Equipment Monitoring
  - PE/EE: LSTM for equipment parameter prediction
  - Anomaly detection in vibration signals
  - Predictive maintenance
- 15.3 Neural Networks in Manufacturing Scheduling
  - MFG: Deep learning–based intelligent scheduling
  - WIP flow prediction and bottleneck prediction
- 15.4 Computer Vision in Defect Detection
  - ADI/AEI deep learning detection
  - Electron microscopy image analysis
  - Automated Defect Classification (ADC)
- 15.5 Case Study: Leading fab's deep learning–based wafer map analysis
- 15.6 Practice Research: Connectionism in production-grade deployments
  - SK Hynix/Gauss Labs: Panoptes Virtual Metrology
  - Gauss Labs Universal Denoiser: AI-enhanced electron microscopy images
  - NVIDIA: Vision foundation models — from CNN to VLM
  - Intel: OpenVINO-driven inline inspection
  - Applied Materials: AIx real-time process visualization
  - Industry benchmark: Wafer map classification model comparison
- 15.7 Demo Visualization: CNN-driven wafer defect detection
- 15.8 Demo Visualization: Deep learning yield prediction and virtual metrology

### Chapter 16: Applications of Behaviorism in the Wafer Fab

- 16.1 Reinforcement Learning in Process Optimization
  - PID/YED: RL-based DOE parameter space search
  - Reinforcement learning approaches to R2R control
- 16.2 Reinforcement Learning in Manufacturing Scheduling
  - MFG: RL-based intelligent dispatching
  - Multi-tool collaborative scheduling and dynamic bottleneck mitigation
- 16.3 Reinforcement Learning in Equipment Control
  - PE/EE: RL-based adaptive equipment parameter adjustment
  - Predictive maintenance decision optimization
- 16.4 Multi-Agent Systems in the Wafer Fab
  - Cross-departmental collaborative MARL
  - Fab-wide optimization
- 16.5 Case Study: RL-based R2R control system
- 16.6 Practice Research: Reinforcement learning from research to production-line validation
  - Google DeepMind AlphaChip: Production-grade deployment of RL in chip design
  - AISSI project: Deep RL validated on the factory floor for scheduling
  - RL scheduling benchmarks on real industrial datasets
  - Samsung: Autonomous fault maintenance system — fusion of RL and graph analysis
  - Synopsys DSO.ai: Commercial validation of RL in chip design optimization
  - Industry practice summary: Deployment stages of Behaviorism in semiconductors
- 16.7 Demo Visualization: RL-driven process parameter optimization
- 16.8 Demo Visualization: Multi-agent reinforcement learning scheduling

### Chapter 17: Overview of Integration — The Crossroads and Unification of the Three Schools

- 17.1 Why Integration Is the Inevitable Trend
  - Limitations of any single school
  - The composite nature of real fab problems
- 17.2 Three Integration Directions and Full Integration
  - NB (Neural + Symbolic): Combining intuition and reason
  - NA (Neural + Action): Combining perception and decision-making
  - SA (Symbolic + Action): Combining planning and execution
  - NSA Full Integration: The perception–cognition–action closed loop
- 17.3 Mapping Integration Directions to the Three Core Departments
  - NB/NA/SA/NSA × PID/YED, MFG, PE/EE
- 17.4 The Inevitability of Integration from an AGI Perspective
  - AGI's "threshold" theory
  - The fog beyond the threshold
  - The current main theme: Unification of technical pathways

### Chapter 18: NB (Neural + Symbolic) — Neuro-Symbolic Integration in the Wafer Fab

- 18.1 Core Idea: Combining Intuition and Reason
  - Kahneman's dual-system theory (System 1 fast thinking vs. System 2 slow thinking)
- 18.2 Technical Pathways
  - Path 1: LLM + Knowledge Graph (RAG and Tool Use)
  - Path 2: Chain-of-Thought (CoT)
  - Path 3: Neuro-symbolic constrained learning
- 18.3 Applications in PID/YED
  - Verifiable yield root cause analysis
  - Defect classification with domain knowledge constraints
  - Automated generation and verification of yield reports
- 18.4 Applications in MFG
  - Cross-system data Q&A
  - Production report automation and compliance verification
  - Fusion of dispatching rules and ML predictions
- 18.5 Applications in PE/EE
  - Equipment fault "perception + diagnosis"
  - Recipe optimization with knowledge constraints
  - Intelligent retrieval and compliance checking of SPEC documents
- 18.6 Practice Cases
  - Samsung: Knowledge graph + LLM sensor anomaly detection
  - yieldWerx: Root cause knowledge graphs
  - IKAS: Smart RCA platform
  - Palantir AIP: NB-integrated industrial-grade architecture

### Chapter 19: NA (Neural + Action) — Neuro-Behavioral Integration in the Wafer Fab

- 19.1 Core Idea: Combining Perception and Decision-Making
  - Deep learning for perception, reinforcement learning for decision-making
- 19.2 Technical Pathways
  - Path 1: Deep RL (Deep Reinforcement Learning)
  - Path 2: RLHF (Reinforcement Learning from Human Feedback)
  - Path 3: End-to-end perception–decision systems
- 19.3 Applications in PID/YED
  - Yield prediction + parameter optimization
  - Perception-based adaptive DOE search
  - Automated response decisions for yield anomalies
- 19.4 Applications in MFG
  - End-to-end intelligent dispatching
  - Vision-based WIP management
  - Dynamic adjustment of production plans
- 19.5 Applications in PE/EE
  - Real-time adaptive equipment control
  - Perception-based predictive maintenance decisions
  - End-to-end optimization of R2R control
- 19.6 Practice Cases
  - AISSI project: Deep RL validated on the factory floor for scheduling
  - Google DeepMind AlphaChip: Perception–decision chip design
  - Samsung: Autonomous fault maintenance system
  - NVIDIA: cuLitho + Metropolis perception–decision closed loop
  - Lam Research: Equipment AI perception–control fusion
- 19.7 Demo Visualization: NA integration end-to-end optimization

### Chapter 20: SA (Symbolic + Action) — Symbolic-Behavioral Integration in the Wafer Fab

- 20.1 Core Idea: Combining Planning and Execution
  - Symbolic planning for "direction," behavioral execution for "flexibility"
- 20.2 Technical Pathways
  - Path 1: Symbolic planning + RL execution
  - Path 2: HTN + adaptive execution
  - Path 3: Multi-agent symbolic-behavioral architecture
- 20.3 Applications in PID/YED
  - NPI project management and task decomposition
  - Symbolic orchestration of process development workflows
  - Automated planning and execution of yield improvement projects
- 20.4 Applications in MFG
  - Exception response workflow automation
  - Hierarchical decomposition and execution of production plans
  - Cross-departmental symbolic-behavioral scheduling
- 20.5 Applications in PE/EE
  - PM planning + adaptive execution
  - Symbolic planning of equipment repair workflows
  - Task decomposition and optimization for tool matching
- 20.6 Practice Cases
  - Samsung: Autonomous manufacturing system planning–execution architecture
  - Palantir AIP: Ontology-driven task orchestration
  - L3Harris (Palantir Warp Speed): Symbolic-behavioral architecture for complex manufacturing
  - Flexciton: Mixed-integer programming + RL scheduling system
  - Multi-agent systems in NPI collaboration exploration
- 20.7 Demo Visualization: SA integration task orchestration and collaboration

### Chapter 21: NSA Full Integration — Embodied Intelligence and the Future of the Wafer Fab

- 21.1 Core Idea: The Perception–Cognition–Action Closed Loop
  - The progressive relationship from NB/NA/SA to NSA
- 21.2 Technical Pathways
  - Path 1: World models and digital twins
  - Path 2: Multimodal embodied intelligence
  - Path 3: End-to-end agent architecture
- 21.3 Applications in PID/YED
  - Full-stack yield intelligence (perception → reasoning → optimization → verification)
  - Autonomous process development systems
- 21.4 Applications in MFG
  - Autonomous manufacturing operations
  - Fab-wide autonomous decision-making
- 21.5 Applications in PE/EE
  - Self-healing equipment systems
  - Autonomous equipment tuning and maintenance
- 21.6 The Evolution Path from Point AI to Embodied Intelligence
  - Four stages: AI-assisted → AI-augmented → AI-autonomous → Embodied Intelligence
- 21.7 Practice Cases
  - Samsung: NSA prototype of the autonomous manufacturing system
  - Palantir + NVIDIA: AIOS-RA's NSA architecture
  - NVIDIA Omniverse: Wafer fab digital twin platform
  - Micron: NSA exploration of predictive manufacturing
- 21.8 Outlook and Challenges
  - Technical challenges (world model accuracy, closed-loop latency, safety)
  - Organizational challenges (trust building, human-machine collaboration models)
  - Ethics and governance
  - A gradual path from vision to reality
- 21.9 Demo Visualization: NSA full-integration perception–cognition–action closed loop

---

## Part V: LLM and Agents

### Chapter 22: Large Language Models (LLM) in the Wafer Fab

- 22.1 LLM Technology Overview
  - Transformer architecture review
  - Pre-training–fine-tuning–alignment paradigm
  - Overview of mainstream LLMs (GPT-4, Claude, Llama, ERNIE, etc.)
- 22.2 LLM Applications in Process Document Management
  - Intelligent retrieval and Q&A for process specifications (SPEC)
  - Automated interpretation of equipment manuals
  - Automated generation of anomaly reports
- 22.3 LLM Applications in Yield Analysis
  - Automated generation of yield reports
  - Natural language interaction with process data
  - LLM-assisted multi-source data analysis
- 22.4 LLM Applications in Manufacturing Operations
  - Intelligent work order management
  - Production report automation
  - Cross-system data Q&A
- 22.5 Challenges and Outlook
  - Data security and privacy
  - Addressing the hallucination problem
  - Domain knowledge injection and RAG technology
- 22.6 Demo Visualization: LLM applications in the wafer fab

### Chapter 23: Agent Systems in Practice at the Wafer Fab

- 23.1 Agent Technology Overview
  - Evolution from LLM to Agent
  - Agent core components: Perception, Planning, Memory, Action
  - Multi-Agent system architecture
- 23.2 Process Integration Agent
  - Automated process analysis Agent
  - Cross-departmental collaboration Agent
- 23.3 Yield Analysis Agent
  - Automated root cause analysis Agent
  - Yield anomaly response Agent
- 23.4 Manufacturing Scheduling Agent
  - Dynamic scheduling Agent
  - Exception handling Agent
- 23.5 Equipment Maintenance Agent
  - Predictive maintenance decision Agent
  - Equipment health monitoring Agent
- 23.6 Fab-Level Agent Architecture
  - Multi-Agent collaboration framework
  - Combining digital twins with Agents
  - From point AI to fab-wide intelligence
- 23.7 Demo Visualization: Multi-Agent collaboration framework

---

## Part VI: Ontology Special Chapter

### Chapter 24: Palantir and Ontology — From Bin Laden to Samsung's Yield Leap

- 24.1 What Is Ontology
  - From philosophy to computer science
  - The role of Ontology in AI
  - Relationship and distinction with Knowledge Graphs
- 24.2 The Palantir Story
  - Founding: Peter Thiel and Alex Karp
  - Bin Laden: How Palantir helped the CIA locate the target
  - Tracking Khamenei: Palantir's role in monitoring Iran's nuclear facilities
  - From defense to industry transformation
- 24.3 Palantir's Technical Architecture
  - Gotham platform (defense and intelligence)
  - Foundry platform (commercial and industrial)
  - Ontology as the core engine
- 24.4 Palantir Enters Semiconductors
  - Background of Samsung Semiconductor adopting Palantir Foundry
  - The specific story of yield improvement
  - Why traditional data platforms couldn't do it
- 24.5 Athinia — Palantir and Merck's Semiconductor Data Joint Venture
  - The birth of the joint venture
  - Collaboration with Micron on CMP predictive manufacturing
  - Athinia ecosystem (ASNA, TEL)
- 24.6 European IDM Case — Supply Chain Visibility and Capacity Planning
  - Multi-fab capacity visibility
  - End-to-end supply chain visibility
  - Clear-to-Build (constructability check)
- 24.7 Palantir's Three Semiconductor Workflows
  - Workflow 1: Production Optimization
  - Workflow 2: Disruptions and Yield
  - Workflow 3: Strategic CAPEX Simulation
- 24.8 AIP Applications in Semiconductor R&D
  - Dual-pillar architecture (knowledge tree + ML)
  - Fusion of LLM and Ontology
  - Data access control and anti-hallucination mechanisms
- 24.9 Industry Ecosystem and Competitive Landscape
  - Sphere of influence
  - Competitor comparison (Snowflake, Databricks, EDA giants, equipment vendor AI, NVIDIA Omniverse)
  - Palantir's moat
- 24.10 Samsung's ChatGPT Data Leak Incident and Palantir's "Data Sovereignty" Advantage
  - The ChatGPT leak incident
  - Abandoning Microsoft and Google
  - Palantir's "data sovereignty" promise
- 24.11 From Syntropy to Athinia — The Cross-Domain Evolution Story
  - Syntropy: Starting point in cancer research
  - Technology transfer from cancer to semiconductors
- 24.12 Qualcomm and Palantir — Ontology Extending to the Edge
  - Collaboration details
  - Semiconductor value of edge Ontology
  - Ontology sinking from fab-level to equipment-level
- 24.13 FDE Model — Palantir's "Special Forces" Deployed in Wafer Fabs
  - What is an FDE
  - Echo-Delta dual-role collaboration
  - AI FDE: The latest evolution
- 24.14 Ursa Major Case — Ontology-Driven Manufacturing System
  - Background
  - A "digital nervous system" rather than a "static data platform"
- 24.15 Athinia and SEMI Strategic Collaboration — Industry-Level Supply Chain Digital Twin
  - From enterprise-level to industry-level
  - Industry-level digital twin (demand change simulation, supply disruption assessment, traceability)
  - Appearance at SEMICON West 2024
  - Significance for wafer fabs
- 24.16 Palantir and NVIDIA's Sovereign AI Operating System — The Ultimate Architecture for Semiconductor Data Sovereignty
  - From "data sovereignty" to "AI sovereignty"
  - AIOS-RA architecture (NVIDIA layer, Palantir layer, Rubix layer)
  - Value for semiconductor wafer fabs
  - From the perspective of the Samsung case
- 24.17 Samsung's HBM4 Yield Breakthrough — From 2nm to Advanced Packaging
  - HBM4: A harder yield challenge than 2nm
  - The data story behind the yield breakthrough
  - The 4nm yield breakthrough
- 24.18 Palantir Warp Speed — OS Evolution from Wafer Fab to All Manufacturing
  - Warp Speed: Ontology-driven manufacturing execution system
  - L3Harris case — A reference for complex manufacturing
  - Boeing case — Closing the digital thread loop
  - Implications for semiconductor wafer fabs
- 24.19 From Case to Paradigm
  - Three-stage evolution: Intra-enterprise → Supply chain → Industry-level
  - Three value tiers of Ontology technology

### Chapter 25: Building and Applying Ontology in Semiconductor Wafer Fabs

- 25.1 Design Principles for Fab Ontology
  - Business entities as the core
  - Dynamically evolvable
  - Cross-system semantic unification
- 25.2 Core Ontology Models for the Fab
  - Product ontology: Wafer, Die, Device, Layer
  - Process ontology: Recipe, Step, Parameter
  - Equipment ontology: Tool, Chamber, Component
  - Defect ontology: Defect, Root Cause, Yield Impact
  - Time ontology: Lot, Wafer, Operation
- 25.3 Ontology-Driven Data Fusion
  - MES + FDC + YMS data integration
  - Cross-system semantic alignment
  - Mapping real-time data to the ontology
- 25.4 Ontology-Driven Intelligent Applications
  - Ontology-based root cause analysis
  - Ontology-driven knowledge reasoning
  - Ontology + LLM intelligent Q&A
  - Ontology-driven digital twins
- 25.5 Implementation Path and Challenges
  - Which ontologies to build first
  - Integration with existing IT systems
  - Organizational and cultural transformation
  - ROI evaluation

---

### Chapter 26: Applications of Embodied AI — When AI Steps into the Physical World of the Fab

- 26.1 From "Thinking" to "Acting"
  - Definition of embodied AI and the fab's strong demand
  - Relationship to NSA full fusion (Ch. 21): the physical manifestation of the intelligent loop
- 26.2 The Embodied AI Technology Stack
  - Multimodal perception, world models, cognitive planning, action execution, learning and feedback
  - VLA (Vision-Language-Action) models
- 26.3 Embodied AI Scenarios in the Fab
  - Intelligent AMHS overhead hoists and AGVs
  - Cleanroom robotic arms and EFEM auto load/unload
  - Mobile manipulation robots for inspection and maintenance
  - Humanoid robots (exploratory)
- 26.4 The Fusion of Embodied AI and Ontology
  - Ontology as the world model: verifiability and orchestratability
- 26.5 Current Practice and Cases
- 26.6 Challenges and Outlook
  - Technical, cost, and organizational challenges and the evolution path
- 26.7 Chapter Summary

## References

See [references.md](computer://references.md), comprising 77 academic references organized into the following seven categories:

1. **AI Foundations and Three Major Schools** — Classic literature and textbooks on Symbolism, Connectionism, and Behaviorism (Russell & Norvig, McCarthy, Newell & Simon, Hinton, LeCun, Sutton & Barto, Silver, etc.)
2. **AI Integration Directions** — NB neuro-symbolic integration (RAG, CoT, Toolformer, ReAct), NA neuro-behavioral integration (Deep RL, SAC), SA symbolic-behavioral integration (HTN planning), NSA full integration (World Models, RT-2, Free Energy Principle)
3. **AI Applications in Semiconductor Wafer Fabs** — Defect detection, virtual metrology, intelligent scheduling, predictive maintenance, R2R control, yield analysis, digital twins (IEEE TSM, IEEE TASE, JIM, and other journal papers)
4. **Chip Design and RL** — AlphaChip (Nature 2021)
5. **AI Surveys for Semiconductor Manufacturing**
6. **Ontology and Industrial AI** — Gruber, Uschold, and other classic ontology literature
7. **Cognitive Science and AI Philosophy** — Turing, Brooks, Marcus & Davis
