"""
Generate all flowchart images with English labels for the English version of the book.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

EN_IMAGE_DIR = r'h:\code\traework\AI在半导体晶圆厂的应用\en\images'
os.makedirs(EN_IMAGE_DIR, exist_ok=True)


def save_fig(fig, name):
    path = os.path.join(EN_IMAGE_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {name}")


# ============================================================
# Flowcharts Batch 1: Ch1-5
# ============================================================

def flow_ch1_value():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('AI Value Positioning in Wafer Fabs: Three-Layer Architecture', fontsize=14, fontweight='bold')
    layers = [
        (6, 'Cost Reduction\n- Equipment idle reduction\n- Wafer scrap reduction\n- Predictive maintenance', '#E3F2FD', '#2196F3'),
        (3.5, 'Efficiency Enhancement\n- NPI cycle compression\n- Yield ramp acceleration\n- Process optimization', '#E8F5E9', '#4CAF50'),
        (1, 'Experience Digitalization\n- Tacit knowledge capture\n- Model-based replication\n- Cross-fab deployment', '#FFF3E0', '#FF9800'),
    ]
    for y, label, face, edge in layers:
        box = FancyBboxPatch((1.5, y-0.8), 11, 1.6, boxstyle='round,pad=0.15',
                             facecolor=face, edgecolor=edge, linewidth=2)
        ax.add_patch(box)
        ax.text(7, y, label, ha='center', va='center', fontsize=11, fontweight='bold')
    ax.annotate('', xy=(7, 3), xytext=(7, 4.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(7, 5.5), xytext=(7, 7),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(0.3, 6, 'Layer 1\n(Tactical)', fontsize=10, fontweight='bold', color='#2196F3', va='center')
    ax.text(0.3, 3.5, 'Layer 2\n(Operational)', fontsize=10, fontweight='bold', color='#4CAF50', va='center')
    ax.text(0.3, 1, 'Layer 3\n(Strategic)', fontsize=10, fontweight='bold', color='#FF9800', va='center')
    save_fig(fig, 'flow_ch1_value.png')


def flow_ch2_timeline():
    fig, ax = plt.subplots(figsize=(18, 8))
    ax.set_xlim(0, 18); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Evolution Timeline of Three AI Schools', fontsize=14, fontweight='bold')
    streams = [
        (6.5, 'Symbolism', '#2196F3', [
            (1, '1956\nDartmouth'), (4, '1960s\nGPS'), (7, '1970s\nMYCIN'),
            (10, '1980s\nExpert Sys.'), (13, '2000s\nKG'), (16, '2020s\nNeuro-Symbolic')
        ]),
        (4, 'Connectionism', '#4CAF50', [
            (1, '1943\nM-P Model'), (4, '1958\nPerceptron'), (7, '1969\nXOR Critique'),
            (10, '1986\nBackprop'), (13, '2012\nAlexNet'), (16, '2017+\nTransformer')
        ]),
        (1.5, 'Behaviorism', '#FF9800', [
            (1, '1948\nCybernetics'), (4, '1950s\nSkinner'), (7, '1989\nQ-Learning'),
            (10, '2013\nDQN'), (13, '2016\nAlphaGo'), (16, '2020s\nRLHF')
        ]),
    ]
    for y, name, color, milestones in streams:
        ax.plot([0.5, 17], [y, y], color=color, linewidth=3, alpha=0.5)
        ax.text(-0.3, y, name, fontsize=12, fontweight='bold', color=color, ha='right', va='center')
        for x, label in milestones:
            ax.plot(x, y, 'o', color=color, markersize=10, zorder=5)
            ax.text(x, y + 0.7, label, ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    ax.annotate('', xy=(17.5, 4), xytext=(0, 4),
                arrowprops=dict(arrowstyle='->', color='#333', lw=2))
    ax.text(9, -0.3, 'Convergence: Neuro-Symbolic AI, LLM+Agent, Embodied Intelligence',
            ha='center', fontsize=11, fontweight='bold', color='#9C27B0',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E5F5', edgecolor='#9C27B0'))
    save_fig(fig, 'flow_ch2_timeline.png')


def flow_ch3_symbolism():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Symbolism: Technology Evolution', fontsize=14, fontweight='bold')
    stages = [
        (2, '1956-1970\nEarly Era\nLogic Theorist\nGPS', '#2196F3'),
        (5.5, '1970-1987\nExpert Systems\nMYCIN\nDENDRAL', '#4CAF50'),
        (9, '2000s\nKnowledge\nGraphs\nGoogle KG', '#FF9800'),
        (12.5, '2020s\nNeuro-Symbolic\nLLM+KG\nRAG', '#9C27B0'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.3, 3), 2.6, 3, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 4.5, label, ha='center', va='center', fontsize=9, fontweight='bold')
    for i in range(3):
        ax.annotate('', xy=(stages[i+1][0]-1.3, 4.5), xytext=(stages[i][0]+1.3, 4.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(8, 1, 'Knowledge Representation: Logic -> Rules -> Ontology -> Neural-Symbolic',
            ha='center', fontsize=10, fontweight='bold', color='#333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9C4', edgecolor='#FBC02D'))
    save_fig(fig, 'flow_ch3_symbolism.png')


def flow_ch4_connectionism():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Connectionism: From Perceptron to Transformer', fontsize=14, fontweight='bold')
    stages = [
        (2, '1958\nPerceptron\n(Rosenblatt)', '#2196F3'),
        (5.5, '1986\nBackpropagation\n(Rumelhart et al.)', '#4CAF50'),
        (9, '2012\nAlexNet\n(ImageNet)', '#FF9800'),
        (12.5, '2017+\nTransformer\n(Attention)', '#9C27B0'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.3, 3), 2.6, 3, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 4.5, label, ha='center', va='center', fontsize=9, fontweight='bold')
    for i in range(3):
        ax.annotate('', xy=(stages[i+1][0]-1.3, 4.5), xytext=(stages[i][0]+1.3, 4.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(8, 1, 'Learning Paradigm: Supervised -> Self-supervised -> Pretrain+Fine-tune -> Prompt',
            ha='center', fontsize=10, fontweight='bold', color='#333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9C4', edgecolor='#FBC02D'))
    save_fig(fig, 'flow_ch4_connectionism.png')


def flow_ch5_behaviorism():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Behaviorism: From Cybernetics to RLHF', fontsize=14, fontweight='bold')
    stages = [
        (2, '1948\nCybernetics\n(Wiener)', '#2196F3'),
        (5.5, '1989\nQ-Learning\n(Watkins)', '#4CAF50'),
        (9, '2013-2016\nDQN -> AlphaGo\n(DeepMind)', '#FF9800'),
        (12.5, '2020s\nRLHF + MARL\n(PPO, SAC)', '#9C27B0'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.3, 3), 2.6, 3, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 4.5, label, ha='center', va='center', fontsize=9, fontweight='bold')
    for i in range(3):
        ax.annotate('', xy=(stages[i+1][0]-1.3, 4.5), xytext=(stages[i][0]+1.3, 4.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(8, 1, 'Decision Paradigm: Single-agent -> Multi-agent -> Offline RL -> LLM Alignment',
            ha='center', fontsize=10, fontweight='bold', color='#333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9C4', edgecolor='#FBC02D'))
    save_fig(fig, 'flow_ch5_behaviorism.png')


# ============================================================
# Flowcharts Batch 2: Ch6-12
# ============================================================

def flow_ch6_npi():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('PID/YED: New Product Introduction (NPI) Process Flow', fontsize=13, fontweight='bold')
    stages = [
        (2, 'Process\nDesign', '#2196F3'),
        (5, 'DOE & Recipe\nDevelopment', '#4CAF50'),
        (8, 'Pilot Run &\nYield Ramp', '#FF9800'),
        (11, 'Mass Production\n& Monitoring', '#F44336'),
        (14, 'Yield\nOptimization', '#9C27B0'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.2, 2), 2.4, 2, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 3, label, ha='center', va='center', fontsize=9, fontweight='bold')
    for i in range(4):
        ax.annotate('', xy=(stages[i+1][0]-1.2, 3), xytext=(stages[i][0]+1.2, 3),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(8, 0.8, 'AI Integration Points: ML yield prediction | KG root cause analysis | RL parameter optimization',
            ha='center', fontsize=9, fontweight='bold', color='#333')
    save_fig(fig, 'flow_ch6_npi.png')


def flow_ch7_dispatch():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('MFG: Smart Dispatching System Architecture', fontsize=13, fontweight='bold')
    layers = [
        (5, 'Data Layer\nMES + FDC + SPC', '#E3F2FD', '#2196F3'),
        (3.5, 'Decision Layer\nRL Agent + Rule Engine', '#FFF3E0', '#FF9800'),
        (2, 'Execution Layer\nAMHS + Tool Control', '#E8F5E9', '#4CAF50'),
    ]
    for y, label, face, edge in layers:
        box = FancyBboxPatch((2, y-0.5), 12, 1, boxstyle='round,pad=0.1',
                             facecolor=face, edgecolor=edge, linewidth=2)
        ax.add_patch(box)
        ax.text(8, y, label, ha='center', va='center', fontsize=10, fontweight='bold')
    ax.annotate('', xy=(8, 4), xytext=(8, 4.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(8, 2.5), xytext=(8, 3),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    save_fig(fig, 'flow_ch7_dispatch.png')


def flow_ch8_pm():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('PE/EE: Predictive Maintenance Workflow', fontsize=13, fontweight='bold')
    stages = [
        (2, 'Sensor Data\nCollection', '#2196F3'),
        (5, 'Feature\nExtraction\n(LSTM)', '#4CAF50'),
        (8, 'Anomaly\nDetection\n(ML)', '#FF9800'),
        (11, 'Remaining\nUseful Life\nPrediction', '#F44336'),
        (14, 'Maintenance\nDecision', '#9C27B0'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.2, 2), 2.4, 2, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 3, label, ha='center', va='center', fontsize=8.5, fontweight='bold')
    for i in range(4):
        ax.annotate('', xy=(stages[i+1][0]-1.2, 3), xytext=(stages[i][0]+1.2, 3),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    save_fig(fig, 'flow_ch8_pm.png')


def flow_ch14_expert_system():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Symbolism in Wafer Fabs: Expert System Architecture', fontsize=13, fontweight='bold')
    components = [
        (3, 6, 'Knowledge Base\n(Rules + Facts)', '#2196F3'),
        (7, 6, 'Inference Engine\n(Forward/Backward)', '#4CAF50'),
        (11, 6, 'User Interface\n(Query + Explanation)', '#FF9800'),
        (3, 2.5, 'Knowledge\nAcquisition', '#9C27B0'),
        (7, 2.5, 'Working Memory\n(Facts + Conclusions)', '#F44336'),
        (11, 2.5, 'Explanation\nModule', '#795548'),
    ]
    for x, y, label, color in components:
        box = FancyBboxPatch((x-1.5, y-0.6), 3, 1.2, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')
    ax.annotate('', xy=(5.5, 6), xytext=(4.5, 6), arrowprops=dict(arrowstyle='<->', color='#666', lw=2))
    ax.annotate('', xy=(9.5, 6), xytext=(8.5, 6), arrowprops=dict(arrowstyle='<->', color='#666', lw=2))
    ax.annotate('', xy=(7, 5.4), xytext=(7, 3.1), arrowprops=dict(arrowstyle='<->', color='#666', lw=2))
    ax.annotate('', xy=(3, 5.4), xytext=(3, 3.1), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(11, 5.4), xytext=(11, 3.1), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    save_fig(fig, 'flow_ch14_expert_system.png')


def flow_ch15_training_pipeline():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('Deep Learning Model Training Pipeline', fontsize=13, fontweight='bold')
    stages = [
        (2, 'Data\nCollection', '#2196F3'),
        (4.5, 'Data\nPreprocessing', '#4CAF50'),
        (7, 'Model\nTraining\n(CNN/LSTM)', '#FF9800'),
        (9.5, 'Validation\n& Testing', '#F44336'),
        (12, 'Deployment\n(Edge/Cloud)', '#9C27B0'),
        (14.5, 'Monitoring\n& Retraining', '#795548'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-0.9, 2), 1.8, 2, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 3, label, ha='center', va='center', fontsize=8, fontweight='bold')
    for i in range(5):
        ax.annotate('', xy=(stages[i+1][0]-0.9, 3), xytext=(stages[i][0]+0.9, 3),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(14.5, 2), xytext=(14.5, 0.8),
                arrowprops=dict(arrowstyle='->', color='#F44336', lw=2,
                                connectionstyle='arc3,rad=-0.3'))
    ax.text(15.5, 1.2, 'Feedback\nLoop', fontsize=8, color='#F44336', fontweight='bold')
    save_fig(fig, 'flow_ch15_training_pipeline.png')


def flow_ch16_mdp_loop():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Reinforcement Learning: MDP Decision Loop', fontsize=13, fontweight='bold')
    agent = FancyBboxPatch((3, 5), 4, 1.5, boxstyle='round,pad=0.2',
                           facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=2)
    ax.add_patch(agent)
    ax.text(5, 5.75, 'RL Agent\n(Policy Network)', ha='center', va='center', fontsize=11, fontweight='bold')
    env = FancyBboxPatch((3, 1.5), 4, 1.5, boxstyle='round,pad=0.2',
                         facecolor='#4CAF50', alpha=0.2, edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(env)
    ax.text(5, 2.25, 'Wafer Fab Environment\n(MES + FDC + Equipment)', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.annotate('', xy=(7, 3), xytext=(7, 5),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2.5))
    ax.text(7.3, 4, 'State\nObservation', fontsize=9, color='#FF9800', fontweight='bold')
    ax.annotate('', xy=(3, 5), xytext=(3, 3),
                arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2.5))
    ax.text(1.5, 4, 'Action\n(Dispatch/\nParameter)', fontsize=9, color='#9C27B0', fontweight='bold')
    ax.annotate('', xy=(5, 3), xytext=(5, 5),
                arrowprops=dict(arrowstyle='->', color='#F44336', lw=1.5,
                                connectionstyle='arc3,rad=0.3'))
    ax.text(5.3, 4, 'Reward\nSignal', fontsize=8, color='#F44336', fontweight='bold')
    save_fig(fig, 'flow_ch16_mdp_loop.png')


def flow_ch17_fusion_map():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Three Fusion Directions Mapping', fontsize=14, fontweight='bold')
    c1 = Circle((3, 6), 1.5, facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=2)
    c2 = Circle((7, 6), 1.5, facecolor='#4CAF50', alpha=0.2, edgecolor='#4CAF50', linewidth=2)
    c3 = Circle((11, 6), 1.5, facecolor='#FF9800', alpha=0.2, edgecolor='#FF9800', linewidth=2)
    ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)
    ax.text(3, 6, 'Symbolism\n(Reasoning)', ha='center', va='center', fontsize=10, fontweight='bold', color='#2196F3')
    ax.text(7, 6, 'Connectionism\n(Perception)', ha='center', va='center', fontsize=10, fontweight='bold', color='#4CAF50')
    ax.text(11, 6, 'Behaviorism\n(Action)', ha='center', va='center', fontsize=10, fontweight='bold', color='#FF9800')
    # Fusion zones
    ax.text(5, 7.5, 'NB\n(Neural+Symbolic)', ha='center', fontsize=9, fontweight='bold', color='#9C27B0')
    ax.text(9, 7.5, 'NA\n(Neural+Action)', ha='center', fontsize=9, fontweight='bold', color='#FF6B6B')
    ax.text(7, 3.5, 'SA\n(Symbolic+Action)', ha='center', fontsize=9, fontweight='bold', color='#4CAF50')
    ax.text(7, 1.5, 'NSA Full Fusion\n(Perception-Cognition-Action Loop)', ha='center', fontsize=10, fontweight='bold', color='#9C27B0',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E5F5', edgecolor='#9C27B0'))
    save_fig(fig, 'flow_ch17_fusion_map.png')


# ============================================================
# Flowcharts Batch 3: Ch18-19
# ============================================================

def flow_ch18_nb_rca():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('NB Fusion: LLM + Knowledge Graph Root Cause Analysis', fontsize=13, fontweight='bold')
    steps = [
        (3, 6.5, 'CNN Defect\nDetection\n(Neural)', '#2196F3'),
        (7, 6.5, 'KG Retrieval\n(Symbolic)', '#4CAF50'),
        (11, 6.5, 'LLM Reasoning\n+ Verification', '#9C27B0'),
        (3, 3, 'SPC Rule\nCheck', '#FF9800'),
        (7, 3, 'Verified\nRoot Cause', '#F44336'),
        (11, 3, 'Actionable\nReport', '#4CAF50'),
    ]
    for x, y, label, color in steps:
        box = FancyBboxPatch((x-1.3, y-0.6), 2.6, 1.2, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')
    ax.annotate('', xy=(5.7, 6.5), xytext=(4.3, 6.5), arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(9.7, 6.5), xytext=(8.3, 6.5), arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(3, 3.6), xytext=(3, 5.9), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(7, 3.6), xytext=(7, 5.9), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(11, 3.6), xytext=(11, 5.9), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    save_fig(fig, 'flow_ch18_nb_rca.png')


def flow_ch19_na_loop():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('NA Fusion: Perception-Decision Closed Loop', fontsize=13, fontweight='bold')
    ax.text(2, 6, 'Neural\n(Perception)', fontsize=12, fontweight='bold', color='#2196F3', ha='center')
    ax.text(6, 6, 'Fusion\nLayer', fontsize=12, fontweight='bold', color='#9C27B0', ha='center')
    ax.text(10, 6, 'Action\n(Decision)', fontsize=12, fontweight='bold', color='#FF9800', ha='center')
    ax.text(6, 2, 'Environment\n(Wafer Fab)', fontsize=11, fontweight='bold', color='#4CAF50', ha='center')
    ax.annotate('', xy=(4.5, 6), xytext=(3, 6), arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2.5))
    ax.annotate('', xy=(8.5, 6), xytext=(7.5, 6), arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2.5))
    ax.annotate('', xy=(6, 3), xytext=(10, 5), arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2,
                                                                connectionstyle='arc3,rad=0.3'))
    ax.annotate('', xy=(2, 5), xytext=(6, 3), arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2,
                                                              connectionstyle='arc3,rad=0.3'))
    save_fig(fig, 'flow_ch19_na_loop.png')


def flow_ch19_rlhf():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('RLHF: Reinforcement Learning from Human Feedback', fontsize=13, fontweight='bold')
    steps = [
        (2, 'SFT\nSupervised\nFine-tuning', '#2196F3'),
        (5.5, 'RM\nReward Model\nTraining', '#4CAF50'),
        (9, 'PPO\nPolicy\nOptimization', '#FF9800'),
        (12.5, 'Aligned\nLLM Output', '#9C27B0'),
    ]
    for x, label, color in steps:
        box = FancyBboxPatch((x-1.3, 2), 2.6, 2.5, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, 3.25, label, ha='center', va='center', fontsize=10, fontweight='bold')
    for i in range(3):
        ax.annotate('', xy=(steps[i+1][0]-1.3, 3.25), xytext=(steps[i][0]+1.3, 3.25),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.text(5.5, 0.8, 'Human Feedback Loop', fontsize=10, fontweight='bold', color='#F44336',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFEBEE', edgecolor='#F44336'))
    save_fig(fig, 'flow_ch19_rlhf.png')


def flow_ch20_sa_architecture():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('SA Fusion: Symbolic Planning + RL Execution Architecture', fontsize=13, fontweight='bold')
    ax.text(3, 6, 'Symbolic Planner\n(HTN/Ontology)\nDirection & Constraints', fontsize=10, fontweight='bold',
            color='#2196F3', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#2196F3'))
    ax.text(7, 6, 'Task Decomposition\n& Constraint Propagation', fontsize=10, fontweight='bold',
            color='#9C27B0', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E5F5', edgecolor='#9C27B0'))
    ax.text(11, 6, 'RL Executor\nFlexible Execution\nwithin Constraints', fontsize=10, fontweight='bold',
            color='#FF9800', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#FF9800'))
    ax.text(7, 2, 'Wafer Fab Environment\n(MES + Equipment + WIP)', fontsize=10, fontweight='bold',
            color='#4CAF50', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9', edgecolor='#4CAF50'))
    ax.annotate('', xy=(5.5, 6), xytext=(4.2, 6), arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(9.5, 6), xytext=(8.5, 6), arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(7, 3), xytext=(11, 5), arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2,
                                                                connectionstyle='arc3,rad=0.3'))
    ax.annotate('', xy=(3, 5), xytext=(7, 3), arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2,
                                                              connectionstyle='arc3,rad=0.3'))
    save_fig(fig, 'flow_ch20_sa_architecture.png')


def flow_ch20_multiagent():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Multi-Agent Symbolic-Action Architecture', fontsize=13, fontweight='bold')
    center = FancyBboxPatch((5, 5.5), 4, 1.2, boxstyle='round,pad=0.15',
                             facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
    ax.add_patch(center)
    ax.text(7, 6.1, 'Symbolic Coordinator\n(Task Allocation + Constraints)', ha='center', va='center', fontsize=9, fontweight='bold')
    agents = [
        (2, 3, 'PID Agent\n(RL)', '#2196F3'),
        (5, 3, 'MFG Agent\n(RL)', '#4CAF50'),
        (8, 3, 'PE Agent\n(RL)', '#FF9800'),
        (11, 3, 'EE Agent\n(RL)', '#F44336'),
    ]
    for x, y, label, color in agents:
        box = FancyBboxPatch((x-1.2, y-0.5), 2.4, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.annotate('', xy=(x, 3.5), xytext=(7, 5.5), arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))
    save_fig(fig, 'flow_ch20_multiagent.png')


def flow_ch21_nsa_loop():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('NSA Full Fusion: Perception-Cognition-Action Loop', fontsize=13, fontweight='bold')
    c1 = Circle((2.5, 5.5), 1.2, facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=2)
    c2 = Circle((6, 5.5), 1.2, facecolor='#4CAF50', alpha=0.2, edgecolor='#4CAF50', linewidth=2)
    c3 = Circle((9.5, 5.5), 1.2, facecolor='#FF9800', alpha=0.2, edgecolor='#FF9800', linewidth=2)
    ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)
    ax.text(2.5, 5.5, 'Perception\n(Neural)', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(6, 5.5, 'Cognition\n(Symbolic)', ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(9.5, 5.5, 'Action\n(Behavior)', ha='center', va='center', fontsize=9, fontweight='bold')
    center = Circle((6, 2.5), 1.3, facecolor='#9C27B0', alpha=0.3, edgecolor='#9C27B0', linewidth=3)
    ax.add_patch(center)
    ax.text(6, 2.5, 'NSA\nFull Fusion', ha='center', va='center', fontsize=10, fontweight='bold', color='#9C27B0')
    for cx, cy in [(2.5, 5.5), (6, 5.5), (9.5, 5.5)]:
        ax.annotate('', xy=(6, 3.5), xytext=(cx, 4.5),
                    arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=1.5))
    save_fig(fig, 'flow_ch21_nsa_loop.png')


def flow_ch21_evolution():
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
    ax.set_title('NSA Four-Stage Evolution Path', fontsize=13, fontweight='bold')
    stages = [
        (2, 'Stage 1: AI-Assisted\n(Current)\nAI provides analysis\nHumans make decisions', '#81C784'),
        (5.5, 'Stage 2: AI-Augmented\n(1-2 years)\nSemi-autonomous decisions\nHuman oversight', '#FFB74D'),
        (9, 'Stage 3: AI-Autonomous\n(3-5 years)\nAutonomous in bounded scope\nHumans set goals', '#E57373'),
        (12.5, 'Stage 4: Embodied AI\n(5-10+ years)\nPhysical closed loop\nHuman-robot collaboration', '#BA68C8'),
    ]
    for x, label, color in stages:
        box = FancyBboxPatch((x-1.5, 1), 3, 3.5, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2.5)
        ax.add_patch(box)
        lines = label.split('\n')
        ax.text(x, 3.8, lines[0], ha='center', va='center', fontsize=10, fontweight='bold', color=color)
        for j, line in enumerate(lines[1:]):
            ax.text(x, 3.2 - j*0.4, line, ha='center', va='center', fontsize=7.5)
    for i in range(3):
        ax.annotate('', xy=(stages[i+1][0]-1.5, 2.5), xytext=(stages[i][0]+1.5, 2.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2.5))
    save_fig(fig, 'flow_ch21_evolution.png')


def flow_ch22_rag():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('RAG Architecture: LLM + Domain Knowledge Retrieval', fontsize=13, fontweight='bold')
    steps = [
        (7, 7, 'User Query: "Step23 overlay accuracy issue?"', '#E3F2FD', '#2196F3'),
        (3, 5, 'Query Embedding', '#FFF3E0', '#FF9800'),
        (7, 5, 'Knowledge Base\n(SPEC + Defect DB + KG)', '#E8F5E9', '#4CAF50'),
        (11, 5, 'Top-K Relevant\nDocuments', '#F3E5F5', '#9C27B0'),
        (7, 3, 'Prompt Assembly\n(Query + Retrieved Context)', '#FFFDE7', '#FBC02D'),
        (7, 1, 'LLM Generation\n(Answer + Citations)', '#E8F5E9', '#4CAF50'),
    ]
    for x, y, label, face, edge in steps:
        box = FancyBboxPatch((x-2, y-0.5), 4, 1, boxstyle='round,pad=0.1',
                             facecolor=face, edgecolor=edge, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
    ax.annotate('', xy=(7, 5.5), xytext=(7, 6.5), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(7, 3.5), xytext=(7, 4.5), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(7, 1.5), xytext=(7, 2.5), arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    save_fig(fig, 'flow_ch22_rag.png')


def flow_ch23_agent():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Agent System Architecture in Wafer Fabs', fontsize=13, fontweight='bold')
    center = FancyBboxPatch((4.5, 5.5), 5, 1.2, boxstyle='round,pad=0.15',
                             facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
    ax.add_patch(center)
    ax.text(7, 6.1, 'Coordinator Agent\n(Perception - Planning - Dispatch)', ha='center', va='center', fontsize=9, fontweight='bold')
    agents = [
        (2, 3, 'PID Agent\n(Process Analysis)', '#2196F3'),
        (5.5, 3, 'YED Agent\n(Yield Monitoring)', '#4CAF50'),
        (8.5, 3, 'MFG Agent\n(Scheduling)', '#FF9800'),
        (12, 3, 'EE Agent\n(Equipment Health)', '#F44336'),
    ]
    for x, y, label, color in agents:
        box = FancyBboxPatch((x-1.5, y-0.5), 3, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.annotate('', xy=(x, 3.5), xytext=(7, 5.5), arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))
    mem = FancyBboxPatch((2, 0.5), 10, 1, boxstyle='round,pad=0.1',
                         facecolor='#607D8B', alpha=0.1, edgecolor='#607D8B', linewidth=1.5)
    ax.add_patch(mem)
    ax.text(7, 1, 'Shared Memory (Short-term + Long-term, Vector Database)', ha='center', va='center', fontsize=9, fontweight='bold')
    save_fig(fig, 'flow_ch23_agent.png')


def flow_ch24_ontology():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Palantir Ontology: Technical Architecture in Semiconductor', fontsize=13, fontweight='bold')
    layers = [
        (7, 'Ontology Layer\n(Objects + Actions + Relations)', '#9C27B0'),
        (4.5, 'Data Integration Layer\n(Foundry: ETL + Pipeline)', '#2196F3'),
        (2, 'Source Systems\n(MES + FDC + SPC + SPEC + KG)', '#4CAF50'),
    ]
    for y, label, color in layers:
        box = FancyBboxPatch((2, y-0.5), 12, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(8, y, label, ha='center', va='center', fontsize=10, fontweight='bold')
    ax.annotate('', xy=(8, 5), xytext=(8, 6.5), arrowprops=dict(arrowstyle='<->', color='#666', lw=2))
    ax.annotate('', xy=(8, 2.5), xytext=(8, 4), arrowprops=dict(arrowstyle='<->', color='#666', lw=2))
    # Applications
    apps = ['Yield\nAnalysis', 'Root Cause\nDiagnosis', 'Smart\nDispatch', 'Predictive\nMaintenance', 'Supply Chain\nVisibility']
    for i, app in enumerate(apps):
        x = 2 + i * 2.8
        box = FancyBboxPatch((x-1, 6.5), 2, 1, boxstyle='round,pad=0.1',
                             facecolor='#FF9800', alpha=0.15, edgecolor='#FF9800', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, 7, app, ha='center', va='center', fontsize=7.5, fontweight='bold')
        ax.annotate('', xy=(x, 6.5), xytext=(x, 7.5), arrowprops=dict(arrowstyle='->', color='#FF9800', lw=1))
    save_fig(fig, 'flow_ch24_ontology.png')


# ============================================================
# Demo images with English labels
# ============================================================

def demo_ch2_three_schools():
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    # Radar chart
    schools = ['Symbolism', 'Connectionism', 'Behaviorism']
    colors = ['#2196F3', '#4CAF50', '#FF9800']
    metrics = ['Knowledge Repr.', 'Learning Ability', 'Perception', 'Reasoning', 'Decision Opt.', 'Explainability']
    data = {
        'Symbolism': [0.9, 0.2, 0.3, 0.85, 0.5, 0.95],
        'Connectionism': [0.4, 0.9, 0.95, 0.3, 0.4, 0.2],
        'Behaviorism': [0.3, 0.7, 0.6, 0.4, 0.9, 0.5],
    }
    N = len(metrics)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    ax = axes[0, 0]
    for school, color in zip(schools, colors):
        vals = data[school] + data[school][:1]
        ax.plot(angles, vals, 'o-', linewidth=2, label=school, color=color)
        ax.fill(angles, vals, alpha=0.15, color=color)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=8)
    ax.set_title('Three AI Schools: Capability Comparison', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)

    # Maturity
    ax = axes[0, 1]
    dims = ['Data\nEfficiency', 'Explain-\nability', 'General-\nization', 'Real-time\nAdaptability', 'Scalability']
    sym = [0.9, 0.95, 0.3, 0.4, 0.5]
    con = [0.3, 0.2, 0.9, 0.7, 0.9]
    beh = [0.5, 0.5, 0.6, 0.95, 0.7]
    x = np.arange(len(dims))
    w = 0.25
    ax.bar(x - w, sym, w, label='Symbolism', color='#2196F3', alpha=0.8)
    ax.bar(x, con, w, label='Connectionism', color='#4CAF50', alpha=0.8)
    ax.bar(x + w, beh, w, label='Behaviorism', color='#FF9800', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(dims, fontsize=8)
    ax.set_title('Technology Maturity Dimensions', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)

    # Application suitability
    ax = axes[1, 0]
    apps = ['Defect\nDetection', 'Yield\nPrediction', 'Scheduling', 'Root Cause\nAnalysis', 'R2R\nControl', 'Predictive\nMaint.']
    cnn = [0.95, 0.88, 0.6, 0.3, 0.7, 0.75]
    kg = [0.3, 0.5, 0.7, 0.92, 0.5, 0.4]
    rl = [0.4, 0.6, 0.92, 0.5, 0.88, 0.7]
    x = np.arange(len(apps))
    ax.bar(x - w, kg, w, label='Symbolism (KG)', color='#2196F3', alpha=0.8)
    ax.bar(x, cnn, w, label='Connectionism (DL)', color='#4CAF50', alpha=0.8)
    ax.bar(x + w, rl, w, label='Behaviorism (RL)', color='#FF9800', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(apps, fontsize=8)
    ax.set_title('Application Suitability by School', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)

    # Timeline
    ax = axes[1, 1]
    ax.set_title('AI Development & Semiconductor Intersection', fontsize=12, fontweight='bold')
    ax.set_xlim(1950, 2030); ax.set_ylim(0, 10)
    ax.axhspan(0, 3, facecolor='#E3F2FD', alpha=0.5)
    ax.text(1990, 1.5, 'Semiconductor Industry Uses AI', fontsize=10, ha='center', fontweight='bold', color='#2196F3')
    events = [(1956, 'Dartmouth'), (1986, 'Backprop'), (2012, 'AlexNet'), (2017, 'Transformer'), (2022, 'ChatGPT')]
    for year, label in events:
        ax.plot(year, 5, 'o', color='#9C27B0', markersize=10)
        ax.text(year, 6, label, ha='center', fontsize=9, fontweight='bold')
    ax.set_xlabel('Year', fontsize=10)
    ax.set_yticks([])
    save_fig(fig, 'demo_ch2_three_schools.png')


def demo_ch6_wafer_defect():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    np.random.seed(42)
    # Wafer defect patterns
    patterns = ['Center', 'Edge Ring', 'Scratch', 'Cluster', 'Random', 'Normal']
    for idx, (pattern, ax) in enumerate(zip(patterns, axes.flat)):
        ax.set_title(f'Pattern: {pattern}', fontsize=11, fontweight='bold')
        x, y = np.meshgrid(np.linspace(-1, 1, 20), np.linspace(-1, 1, 20))
        r = np.sqrt(x**2 + y**2)
        if pattern == 'Center':
            defect = r < 0.3
        elif pattern == 'Edge Ring':
            defect = (r > 0.7) & (r < 0.9)
        elif pattern == 'Scratch':
            defect = (np.abs(y - 0.3) < 0.05) & (x > -0.5)
        elif pattern == 'Cluster':
            defect = (x - 0.3)**2 + (y + 0.2)**2 < 0.15
        elif pattern == 'Random':
            defect = np.random.rand(20, 20) > 0.92
        else:
            defect = np.random.rand(20, 20) > 0.99
        colors = np.where(defect, 1, 0)
        ax.scatter(x, y, c=colors, cmap='RdYlGn_r', s=30, edgecolors='gray', linewidths=0.3)
        circle = plt.Circle((0, 0), 1, fill=False, color='black', linewidth=2)
        ax.add_patch(circle)
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal'); ax.axis('off')
    fig.suptitle('Chapter 6 Demo: Wafer Defect Pattern Classification (CNN)', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch6_wafer_defect.png')


def demo_ch7_smart_scheduling():
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    # WIP comparison
    ax = axes[0, 0]
    t = np.arange(24)
    fifo = 200 + 30*np.sin(t*0.3) + np.random.randn(24)*10
    smart = 180 + 8*np.sin(t*0.2) + np.random.randn(24)*3
    ax.plot(t, fifo, 'o-', color='#FF6B6B', label='FIFO', markersize=4)
    ax.plot(t, smart, 's-', color='#4CAF50', label='AI Scheduling', markersize=4)
    ax.set_title('WIP Level: FIFO vs AI Scheduling', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10); ax.set_xlabel('Time (h)'); ax.grid(alpha=0.3)

    # Utilization
    ax = axes[0, 1]
    tools = ['Tool-A01', 'Tool-A02', 'Tool-B01', 'Tool-B02', 'Tool-C01']
    fifo_util = [65, 78, 72, 80, 68]
    smart_util = [88, 92, 90, 91, 87]
    x = np.arange(len(tools))
    ax.bar(x - 0.15, fifo_util, 0.3, label='FIFO', color='#FF6B6B', alpha=0.8)
    ax.bar(x + 0.15, smart_util, 0.3, label='AI Scheduling', color='#4CAF50', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(tools, fontsize=8, rotation=15)
    ax.set_title('Equipment Utilization Comparison', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_ylabel('Utilization (%)')

    # Gantt
    ax = axes[1, 0]
    tasks = [('Lot-001', 0, 4, '#2196F3'), ('Lot-002', 2, 3, '#4CAF50'),
             ('Lot-003', 1, 5, '#FF9800'), ('Lot-004', 4, 3, '#F44336'),
             ('Lot-005', 3, 4, '#9C27B0'), ('Lot-006', 5, 3, '#795548')]
    for i, (name, start, dur, color) in enumerate(tasks):
        ax.barh(i, dur, left=start, height=0.6, color=color, alpha=0.7)
        ax.text(start + dur/2, i, name, ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t[0] for t in tasks], fontsize=8)
    ax.set_xlabel('Time (h)'); ax.set_title('AI Scheduling Gantt Chart', fontsize=12, fontweight='bold')

    # Metrics
    ax = axes[1, 1]
    metrics = ['Cycle Time\n(h)', 'Utilization\n(%)', 'On-time\nDelivery (%)', 'Throughput\n(lots/day)']
    fifo_vals = [18.5, 72, 80, 45]
    smart_vals = [13.2, 88, 94, 58]
    x = np.arange(len(metrics))
    ax.bar(x - 0.15, fifo_vals, 0.3, label='FIFO', color='#FF6B6B', alpha=0.8)
    ax.bar(x + 0.15, smart_vals, 0.3, label='AI', color='#4CAF50', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=8)
    ax.set_title('Key Metrics Comparison', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 7 Demo: Smart Scheduling System', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch7_smart_scheduling.png')


def demo_ch8_predictive_maintenance():
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    np.random.seed(42)
    # Vibration signal
    ax = axes[0, 0]
    t = np.linspace(0, 100, 1000)
    normal = np.sin(t * 0.5) + np.random.randn(1000) * 0.1
    degrading = np.sin(t * 0.5) + 0.02 * t + np.random.randn(1000) * 0.15
    ax.plot(t, normal, color='#4CAF50', alpha=0.7, label='Normal')
    ax.plot(t, degrading, color='#F44336', alpha=0.7, label='Degrading')
    ax.set_title('Vibration Signal: Normal vs Degrading', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Time (min)')

    # Health score
    ax = axes[0, 1]
    days = np.arange(0, 90)
    health = 100 - 0.8 * days + 5 * np.sin(days * 0.1) + np.random.randn(90) * 1.5
    health = np.clip(health, 20, 100)
    ax.plot(days, health, 'o-', color='#2196F3', markersize=3)
    ax.axhline(y=60, color='#FF9800', linestyle='--', label='Warning Threshold')
    ax.axhline(y=30, color='#F44336', linestyle='--', label='Critical Threshold')
    ax.fill_between(days, 0, 60, where=health < 60, alpha=0.1, color='#FF9800')
    ax.set_title('Equipment Health Score Trend', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Day'); ax.set_ylabel('Health Score')

    # RUL prediction
    ax = axes[1, 0]
    actual_rul = np.arange(50, 0, -1)
    predicted_rul = actual_rul + np.random.randn(50) * 3 + 2 * np.exp(-actual_rul / 20)
    ax.scatter(actual_rul, predicted_rul, color='#2196F3', alpha=0.6, s=20)
    ax.plot([0, 50], [0, 50], 'k--', alpha=0.5, label='Ideal')
    ax.set_title('RUL Prediction: Actual vs Predicted', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Actual RUL (days)'); ax.set_ylabel('Predicted RUL (days)')

    # Comparison
    ax = axes[1, 1]
    metrics = ['Downtime\n(h/month)', 'MTBF\n(days)', 'Maintenance\nCost (k$)', 'OEE (%)']
    traditional = [24, 45, 80, 72]
    predictive = [8, 85, 45, 88]
    x = np.arange(len(metrics))
    ax.bar(x - 0.15, traditional, 0.3, label='Time-based PM', color='#FF6B6B', alpha=0.8)
    ax.bar(x + 0.15, predictive, 0.3, label='Predictive Maint.', color='#4CAF50', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=8)
    ax.set_title('Time-based vs Predictive Maintenance', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 8 Demo: Predictive Maintenance System', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch8_predictive_maintenance.png')


def demo_ch14_kg_rca():
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    # KG visualization (simplified)
    ax = axes[0, 0]
    ax.set_title('Knowledge Graph: Yield Root Cause Analysis', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    nodes = {
        'Yield Drop': (5, 8, '#F44336'),
        'Edge Ring Defect': (5, 6, '#FF9800'),
        'Overlay Error': (2, 4, '#2196F3'),
        'Etch Non-uniformity': (5, 4, '#4CAF50'),
        'CMP Over-polish': (8, 4, '#9C27B0'),
        'Step23: Litho': (2, 2, '#F44336'),
        'Step47: Etch': (5, 2, '#4CAF50'),
        'Step89: CMP': (8, 2, '#9C27B0'),
    }
    for name, (x, y, color) in nodes.items():
        ax.scatter(x, y, s=500, c=color, alpha=0.7, edgecolors='white', linewidths=2, zorder=5)
        ax.text(x, y, name, ha='center', va='center', fontsize=6, fontweight='bold', color='white', zorder=6)
    edges = [(5,8,5,6), (5,6,2,4), (5,6,5,4), (5,6,8,4), (2,4,2,2), (5,4,5,2), (8,4,8,2)]
    for x1,y1,x2,y2 in edges:
        ax.plot([x1,x2], [y1,y2], 'k-', alpha=0.3, linewidth=1)

    # Inference chain
    ax = axes[0, 1]
    ax.set_title('Inference Chain (Rule Engine)', fontsize=12, fontweight='bold')
    chain = ['CNN: Edge Ring\n(94% confidence)', 'KG: Edge Ring ->\n{Litho, Etch, CMP}',
             'SPC: Step23 = 3.2 sigma\n(EXCEEDS limit)', 'CONCLUSION:\nOverlay error at Step23']
    for i, step in enumerate(chain):
        y = 3.5 - i * 1.5
        ax.barh(y, 1, height=0.8, color=['#2196F3','#4CAF50','#FF9800','#F44336'][i], alpha=0.7)
        ax.text(0.5, y, step, ha='center', va='center', fontsize=7, fontweight='bold', color='white')
        if i < 3:
            ax.annotate('', xy=(0.5, y-0.4), xytext=(0.5, y-0.6),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.set_xlim(0, 1); ax.axis('off')

    # Timeline
    ax = axes[1, 0]
    methods = ['Manual\nAnalysis', 'Expert\nSystem', 'Knowledge\nGraph', 'KG + LLM\n(NB Fusion)']
    times = [120, 45, 15, 3.8]
    ax.bar(methods, times, color=['#FF6B6B','#FF9800','#4CAF50','#9C27B0'], alpha=0.8)
    ax.set_title('Analysis Time: Method Evolution', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (min)')

    # Accuracy
    ax = axes[1, 1]
    methods2 = ['Manual', 'Expert Sys.', 'KG', 'KG + LLM']
    accuracy = [75, 82, 88, 94]
    ax.bar(methods2, accuracy, color=['#FF6B6B','#FF9800','#4CAF50','#9C27B0'], alpha=0.8)
    ax.set_title('Analysis Accuracy: Method Evolution', fontsize=12, fontweight='bold')
    ax.set_ylabel('Accuracy (%)')
    fig.suptitle('Chapter 14 Demo: Knowledge Graph Root Cause Analysis', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch14_kg_rca.png')


def demo_ch15_cnn_detection():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    np.random.seed(42)
    # Layer 1 features
    for idx in range(3):
        ax = axes[0, idx]
        feature = np.random.randn(10, 10)
        ax.imshow(feature, cmap='viridis', interpolation='nearest')
        ax.set_title(f'Conv Layer {idx+1} Feature Map', fontsize=10, fontweight='bold')
        ax.axis('off')

    # Filter activations
    ax = axes[1, 0]
    filters = np.random.rand(4, 4)
    ax.imshow(filters, cmap='hot', interpolation='nearest')
    ax.set_title('Filter Activation Heatmap', fontsize=10, fontweight='bold')
    ax.set_xticks([]); ax.set_yticks([])

    # Classification probabilities
    ax = axes[1, 1]
    classes = ['Center', 'Edge Ring', 'Scratch', 'Cluster', 'Random', 'Normal']
    probs = [0.02, 0.94, 0.01, 0.02, 0.005, 0.005]
    colors = ['#4CAF50' if p < 0.5 else '#F44336' for p in probs]
    ax.barh(classes, probs, color=colors, alpha=0.8)
    ax.set_title('Classifier Output Probabilities', fontsize=10, fontweight='bold')
    ax.set_xlabel('Probability')

    # Training curve
    ax = axes[1, 2]
    epochs = np.arange(100)
    train_acc = 0.95 * (1 - np.exp(-epochs / 20)) + np.random.randn(100) * 0.02
    val_acc = 0.92 * (1 - np.exp(-epochs / 25)) + np.random.randn(100) * 0.02
    ax.plot(epochs, train_acc, color='#2196F3', label='Train Acc')
    ax.plot(epochs, val_acc, color='#FF9800', label='Val Acc')
    ax.set_title('Training Curve', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8); ax.set_xlabel('Epoch')
    fig.suptitle('Chapter 15 Demo: CNN-Driven Wafer Defect Detection', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch15_cnn_detection.png')


def demo_ch15_yield_prediction():
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    np.random.seed(42)
    # DNN architecture
    ax = axes[0, 0]
    ax.set_title('DNN Model Architecture', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
    layers = [(1, 4, 'Input\n(12 params)'), (3.5, 4, 'Hidden 1\n(64 neurons)'), (6, 4, 'Hidden 2\n(32 neurons)'), (8.5, 4, 'Output\n(Yield %)')]
    for x, y, label in layers:
        rect = FancyBboxPatch((x-0.6, y-1), 1.2, 2, boxstyle='round,pad=0.1',
                               facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold')
    for i in range(3):
        ax.annotate('', xy=(layers[i+1][0]-0.6, 4), xytext=(layers[i][0]+0.6, 4),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # Scatter prediction
    ax = axes[0, 1]
    n = 100
    y_test = 75 + np.random.rand(n) * 23
    y_pred_lr = y_test - np.random.rand(n) * 10 + 3
    y_pred_dnn = y_test + np.random.randn(n) * 2
    ax.scatter(y_test, y_pred_lr, color='#FF9800', alpha=0.6, label=f'Linear Reg. (R2=0.78)')
    ax.scatter(y_test, y_pred_dnn, color='#2196F3', alpha=0.6, label=f'DNN (R2=0.94)')
    ax.plot([75, 98], [75, 98], 'k--', alpha=0.5, label='Ideal')
    ax.set_title('Yield Prediction: Actual vs Predicted', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Actual Yield (%)'); ax.set_ylabel('Predicted Yield (%)')

    # Virtual metrology
    ax = axes[1, 0]
    t = np.arange(50)
    actual = 200 + 10 * np.sin(t * 0.2) + np.random.randn(50) * 2
    vm = 200 + 10 * np.sin(t * 0.2) + np.random.randn(50) * 1
    ax.plot(t, actual, 'o-', color='#333', linewidth=2, markersize=3, label='Actual Measurement')
    ax.plot(t, vm, 's-', color='#2196F3', linewidth=1.5, markersize=3, label='Virtual Metrology')
    ax.set_title('Virtual Metrology: Actual vs Predicted', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Wafer Index'); ax.set_ylabel('Film Thickness (nm)')

    # Feature importance
    ax = axes[1, 1]
    features = ['Temp', 'Pressure', 'RF Power', 'Etch Rate', 'Gas Flow', 'Time', 'Uniformity', 'Particle']
    importance = [0.28, 0.22, 0.18, 0.12, 0.08, 0.05, 0.04, 0.03]
    ax.barh(features, importance, color='#4CAF50', alpha=0.8)
    ax.set_title('Feature Importance Ranking', fontsize=12, fontweight='bold')
    ax.set_xlabel('Importance')
    fig.suptitle('Chapter 15 Demo: Deep Learning Yield Prediction & Virtual Metrology', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch15_yield_prediction.png')


def demo_ch16_rl_optimization():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    np.random.seed(42)
    # Parameter space search
    ax = axes[0, 0]
    x = np.linspace(0, 10, 50)
    y = np.linspace(0, 10, 50)
    X, Y = np.meshgrid(x, y)
    Z = 80 + 15 * np.exp(-((X-5)**2 + (Y-5)**2) / 8)
    contour = ax.contourf(X, Y, Z, levels=15, cmap='RdYlGn')
    rl_path_x = [2, 3, 4, 4.5, 5, 5.2, 5]
    rl_path_y = [2, 3, 4, 4.5, 5, 5.2, 5]
    ax.plot(rl_path_x, rl_path_y, 'o-', color='white', linewidth=2, markersize=6, label='RL Search Path')
    ax.plot(5, 5, '*', color='red', markersize=20, label='Optimum')
    ax.set_title('RL Parameter Space Search', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)

    # Convergence
    ax = axes[0, 1]
    episodes = np.arange(200)
    reward = -20 + 0.1 * episodes * (1 - np.exp(-episodes / 50)) + np.random.randn(200) * 2
    ax.plot(episodes, reward, color='#9C27B0', linewidth=1.5)
    window = 10
    smooth = np.convolve(reward, np.ones(window)/window, mode='valid')
    ax.plot(episodes[window-1:], smooth, color='#2196F3', linewidth=2.5, label='Smoothed')
    ax.set_title('RL Optimization Convergence', fontsize=11, fontweight='bold')
    ax.set_xlabel('Episode'); ax.set_ylabel('Cumulative Reward')
    ax.legend(fontsize=9)

    # DOE comparison
    ax = axes[0, 2]
    methods = ['Full\nFactorial', 'Taguchi', 'Bayesian\nOpt.', 'RL-guided']
    experiments = [256, 64, 20, 12]
    ax.bar(methods, experiments, color=['#FF6B6B','#FF9800','#4CAF50','#9C27B0'], alpha=0.8)
    ax.set_title('DOE Efficiency Comparison', fontsize=11, fontweight='bold')
    ax.set_ylabel('Experiments Needed')

    # R2R control
    ax = axes[1, 0]
    t = np.arange(100)
    drift = 0.05 * t + 0.3 * np.sin(t * 0.15)
    r2r = drift.copy()
    for i in range(10, 100, 20):
        r2r[i:i+20] -= r2r[i] * 0.7
    rl_control = drift * 0.2 + np.random.randn(100) * 0.05
    ax.plot(t, drift, color='#F44336', label='No Control (Drift)')
    ax.plot(t, r2r, color='#FF9800', label='Traditional R2R')
    ax.plot(t, rl_control, color='#9C27B0', linewidth=2, label='RL Control')
    ax.set_title('R2R Control: Parameter Drift Compensation', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)

    # Improvement
    ax = axes[1, 1]
    params = ['Etch\nRate', 'Uniformity', 'CD\nControl', 'Overlay\nAccuracy', 'Particle\nCount']
    before = [72, 68, 75, 70, 65]
    after = [92, 88, 94, 90, 85]
    x = np.arange(len(params))
    ax.bar(x - 0.15, before, 0.3, label='Before RL', color='#FF6B6B', alpha=0.8)
    ax.bar(x + 0.15, after, 0.3, label='After RL', color='#4CAF50', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(params, fontsize=8)
    ax.set_title('Parameter Improvement: Before vs After RL', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)

    # Policy heatmap
    ax = axes[1, 2]
    policy = np.random.rand(10, 10)
    ax.imshow(policy, cmap='YlOrRd', interpolation='nearest')
    ax.set_title('RL Policy Decision Map', fontsize=11, fontweight='bold')
    ax.set_xlabel('State: Equipment Load'); ax.set_ylabel('State: WIP Level')
    fig.suptitle('Chapter 16 Demo: RL-Driven Process Parameter Optimization', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch16_rl_optimization.png')


def demo_ch16_marl():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    np.random.seed(42)
    # Multi-agent topology
    ax = axes[0, 0]
    ax.set_title('Multi-Agent Fab Topology', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    agents = [(5, 8, 'Coordinator', '#9C27B0'), (2, 5, 'PID Agent', '#2196F3'),
              (5, 5, 'MFG Agent', '#4CAF50'), (8, 5, 'PE Agent', '#FF9800'),
              (3, 2, 'Tool-A', '#F44336'), (7, 2, 'Tool-B', '#795548')]
    for x, y, name, color in agents:
        ax.scatter(x, y, s=300, c=color, alpha=0.7, edgecolors='white', linewidths=2, zorder=5)
        ax.text(x, y, name, ha='center', va='center', fontsize=7, fontweight='bold', color='white', zorder=6)
    for x1, y1, _, _ in agents[1:4]:
        ax.plot([5, x1], [8, y1], 'k-', alpha=0.3)
    for x1, y1, _, _ in agents[4:]:
        ax.plot([5, x1], [5, y1], 'k-', alpha=0.3)

    # Coordination vs independent
    ax = axes[0, 1]
    metrics = ['Cycle Time\n(h)', 'Utilization\n(%)', 'On-time\n(%)', 'Yield\n(%)', 'Conflicts\n(/day)']
    independent = [18.5, 72, 80, 88, 12]
    coordinated = [13.2, 88, 94, 92, 2]
    x = np.arange(len(metrics))
    w = 0.35
    ax.bar(x - w/2, independent, w, label='Independent', color='#FF6B6B', alpha=0.8)
    ax.bar(x + w/2, coordinated, w, label='Coordinated MARL', color='#4CAF50', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=8)
    ax.set_title('Independent vs Coordinated Decisions', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)

    # WIP flow
    ax = axes[1, 0]
    t = np.arange(48)
    fifo = 200 + 30 * np.sin(t * 0.3) + np.random.randn(48) * 10
    marl = 180 + 10 * np.sin(t * 0.2) + np.random.randn(48) * 3
    ax.plot(t, fifo, color='#FF6B6B', label='FIFO')
    ax.plot(t, marl, color='#4CAF50', label='MARL')
    ax.set_title('WIP Flow: FIFO vs MARL', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9); ax.set_xlabel('Time (h)')

    # Gantt
    ax = axes[1, 1]
    tasks = [('Lot-1', 0, 4), ('Lot-2', 1, 3), ('Lot-3', 2, 5), ('Lot-4', 4, 3), ('Lot-5', 3, 4)]
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']
    for i, (name, s, d) in enumerate(tasks):
        ax.barh(i, d, left=s, height=0.6, color=colors[i], alpha=0.7)
    ax.set_title('MARL Scheduling Gantt Chart', fontsize=11, fontweight='bold')
    ax.set_xlabel('Time (h)')

    # Communication
    ax = axes[1, 2]
    episodes = np.arange(100)
    comm_freq = 50 * np.exp(-episodes / 50) + 5 + np.random.randn(100) * 2
    ax.plot(episodes, comm_freq, color='#9C27B0', linewidth=1.5)
    ax.set_title('Agent Communication Frequency\n(Decreases with Learning)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Episode'); ax.set_ylabel('Messages/Step')
    fig.suptitle('Chapter 16 Demo: Multi-Agent Reinforcement Learning for Scheduling', fontsize=14, fontweight='bold')
    save_fig(fig, 'demo_ch16_marl.png')


def demo_ch18_nb_fusion():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    # LLM hypotheses
    ax = axes[0, 0]
    hypotheses = [('H1: Overlay Error', 0.65, '#FF6B6B'), ('H2: Etch Non-uniformity', 0.55, '#FF9800'),
                 ('H3: CMP Over-polish', 0.30, '#FFC107'), ('H4: Deposition Anomaly', 0.15, '#FFD54F')]
    for i, (h, score, color) in enumerate(hypotheses):
        y = 0.85 - i * 0.22
        ax.barh(y, score, height=0.12, color=color, alpha=0.8)
        ax.text(score + 0.02, y, f'{score:.0%}', va='center', fontsize=9, fontweight='bold')
        ax.text(0.01, y, h, va='center', fontsize=9)
    ax.set_title('Step 1: LLM Hypothesis Generation\n(Neural - Intuition)', fontsize=10, fontweight='bold', color='#2196F3')
    ax.set_xlim(0, 0.9)

    # KG verification
    ax = axes[0, 1]
    kg_data = {'Step 23 Litho': ('3.2 sigma', '#F44336'), 'Step 47 Etch': ('1.1 sigma', '#4CAF50'),
               'Step 89 CMP': ('0.8 sigma', '#4CAF50'), 'Step 12 Dep': ('1.5 sigma', '#4CAF50')}
    for i, (step, (spc, color)) in enumerate(kg_data.items()):
        y = 0.85 - i * 0.22
        ax.barh(y, 1, height=0.12, color=color, alpha=0.7)
        ax.text(0.5, y, f'{step} SPC: {spc}', ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    ax.set_title('Step 2: KG Fact Verification\n(Symbolic - Retrieval)', fontsize=10, fontweight='bold', color='#4CAF50')
    ax.set_xlim(0, 1); ax.axis('off')

    # Verified results
    ax = axes[0, 2]
    results = [('Overlay Error', 0.94, '#F44336'), ('Etch Non-uniformity', 0.12, '#4CAF50'),
               ('CMP Over-polish', 0.05, '#4CAF50'), ('Deposition Anomaly', 0.03, '#4CAF50')]
    for i, (cause, prob, color) in enumerate(results):
        y = 0.85 - i * 0.22
        ax.barh(y, prob, height=0.12, color=color, alpha=0.8)
        ax.text(prob + 0.02, y, f'{prob:.0%}', va='center', fontsize=9, fontweight='bold')
        ax.text(0.01, y, cause, va='center', fontsize=9)
    ax.set_title('Step 3: LLM+KG Reasoning\n(NB Fusion - Verifiable)', fontsize=10, fontweight='bold', color='#9C27B0')
    ax.set_xlim(0, 1.15)

    # Inference chain
    ax = axes[1, 0]
    ax.set_title('NB Fusion Inference Chain', fontsize=10, fontweight='bold')
    chain = [('CNN: Edge Ring\n(94% confidence)', '#2196F3'),
             ('KG: Edge->\n{Litho,Etch,CMP}', '#4CAF50'),
             ('Rules: SPC Step23\n=3.2 sigma EXCEEDS', '#FF9800'),
             ('LLM: Overlay Error\n94% confidence', '#9C27B0'),
             ('VERIFIED: Complete\ntrace, no hallucination', '#4CAF50')]
    for i, (text, color) in enumerate(chain):
        y = 4 - i
        ax.barh(y, 1, height=0.7, color=color, alpha=0.7, edgecolor='white')
        ax.text(0.5, y, text, ha='center', va='center', fontsize=7.5, fontweight='bold', color='white')
        if i < 4:
            ax.annotate('', xy=(0.5, y - 0.35), xytext=(0.5, y - 0.5),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.set_xlim(0, 1); ax.set_ylim(-0.5, 4.5); ax.axis('off')

    # Report
    ax = axes[1, 1]
    report = (
        "[Yield Analysis Report - Auto-Generated]\n"
        "========================================\n"
        "Lot: B12345 | Product: Product-X (3nm)\n"
        "Yield: 85% (Target: 92%, Down 7pp)\n"
        "========================================\n"
        "[Root Cause Analysis]\n"
        "  - CNN: Edge Ring Defect (94% conf.)\n"
        "  - KG: Linked 3 edge-related steps\n"
        "  - SPC: Step 23 overlay 3.2 sigma\n"
        "    -> Exceeds 2 sigma limit (Tool-A03)\n"
        "  - Other steps within control limits\n"
        "========================================\n"
        "[Conclusion] Primary cause = Tool-A03 overlay error\n"
        "[Traceability] 5 steps, fully traceable\n"
        "[Hallucination Risk] None (KG-backed)\n"
        "[Recommendation] Calibrate Tool-A03 alignment\n"
        "========================================\n"
        "Generation: 3.8s | Verification: PASSED"
    )
    ax.text(0.05, 0.95, report, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='#2196F3', alpha=0.9))
    ax.set_title('Auto-Generated Yield Report (KG-Verified)', fontsize=10, fontweight='bold', color='#9C27B0')
    ax.axis('off')

    # Comparison
    ax = axes[1, 2]
    metrics = ['Analysis Time\n(min)', 'Accuracy\n(%)', 'Traceability\n(1-10)', 'Hallucination\nRisk (1-10)', 'Engineer\nAcceptance (%)']
    traditional = [120, 75, 3, 8, 60]
    nb = [3.8, 94, 10, 1, 88]
    x = np.arange(len(metrics))
    w = 0.35
    ax.bar(x - w/2, traditional, w, label='Manual', color='#FF6B6B', alpha=0.8)
    ax.bar(x + w/2, nb, w, label='NB Fusion', color='#9C27B0', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=8)
    ax.set_title('Manual vs NB Fusion Analysis', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 18 Demo: NB Fusion (LLM+KG) Driven Verifiable Yield Root Cause Analysis',
                 fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch18_nb_fusion.png')


def demo_ch19_na_fusion():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    np.random.seed(42)
    # Architecture
    ax = axes[0, 0]
    ax.set_title('NA Fusion: E2E Perception-Decision Architecture', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    boxes = [(2, 8, 'Wafer Image\n(CNN)', '#2196F3'), (5, 8, 'Sensor\n(LSTM)', '#2196F3'), (8, 8, 'MES Data\n(MLP)', '#2196F3')]
    for x, y, label, color in boxes:
        box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
    fuse = FancyBboxPatch((2.5, 5), 5, 1, boxstyle='round,pad=0.1', facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
    ax.add_patch(fuse)
    ax.text(5, 5.5, 'Feature Fusion (Concat + Attention)', ha='center', va='center', fontsize=8, fontweight='bold', color='#9C27B0')
    rl_boxes = [(2, 2, 'RL Agent\n(PPO)', '#FF9800'), (5, 2, 'Policy\nNetwork', '#FF9800'), (8, 2, 'Reward\nFeedback', '#FF9800')]
    for x, y, label, color in rl_boxes:
        box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
    ax.text(0.2, 8, 'Neural\n(Perception)', fontsize=8, fontweight='bold', color='#2196F3', va='center')
    ax.text(0.2, 2, 'Action\n(Decision)', fontsize=8, fontweight='bold', color='#FF9800', va='center')

    # RL training
    ax = axes[0, 1]
    episodes = np.arange(500)
    na_reward = -50 + 0.25 * episodes * (1 - np.exp(-episodes / 100)) + np.random.randn(500) * 2
    rl_reward = -50 + 0.12 * episodes + 15 * np.sin(episodes * 0.03) + np.random.randn(500) * 4
    w = 20
    na_smooth = np.convolve(na_reward, np.ones(w)/w, mode='valid')
    rl_smooth = np.convolve(rl_reward, np.ones(w)/w, mode='valid')
    ax.plot(episodes[w-1:], na_smooth, color='#9C27B0', linewidth=2.5, label='NA Fusion (Perception-enhanced RL)')
    ax.plot(episodes[w-1:], rl_smooth, color='#FF9800', linewidth=2, linestyle='--', label='Pure RL')
    ax.set_title('RL Training: NA vs Pure RL', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8); ax.set_xlabel('Episode')

    # DOE search
    ax = axes[0, 2]
    np.random.seed(123)
    param_space = np.random.randn(200, 2) * 2
    param_space[:, 0] = param_space[:, 0] * 5 + 25
    param_space[:, 1] = param_space[:, 1] * 3 + 15
    yield_vals = 80 + 5 * np.exp(-((param_space[:, 0]-22)**2 + (param_space[:, 1]-14)**2) / 8) + np.random.randn(200) * 2
    sc = ax.scatter(param_space[:, 0], param_space[:, 1], c=yield_vals, cmap='RdYlGn', s=20, alpha=0.6)
    ax.plot([28,26,24,22.5,22,21.8,22,22.1,22], [17,16,15,14.2,14,14.1,13.9,14,14], 'o-', color='#9C27B0', linewidth=2, label='RL Path')
    ax.plot(22, 14, '*', color='red', markersize=20, label='Optimum')
    ax.set_title('DOE Parameter Space Search', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # WIP
    ax = axes[1, 0]
    t = np.arange(24)
    fifo = 200 + 30*np.sin(t*0.3) + np.random.randn(24)*10
    na = 180 + 15*np.sin(t*0.3) + np.random.randn(24)*5
    ax.plot(t, fifo, 'o-', color='#F44336', label='FIFO')
    ax.plot(t, na, 's-', color='#9C27B0', label='NA Fusion')
    ax.set_title('WIP Level Comparison', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)

    # Equipment drift
    ax = axes[1, 1]
    tf = np.linspace(0, 100, 500)
    drift = 0.05 * tf + 0.3 * np.sin(tf * 0.15)
    r2r = drift.copy()
    for i in range(10, 500, 50):
        r2r[i:i+50] -= r2r[i] * 0.6
    na_ctrl = drift * 0.3 + 0.05 * np.sin(tf * 0.2) * 0.3
    ax.plot(tf, drift, color='#F44336', label='No Control')
    ax.plot(tf, r2r, color='#FF9800', label='Traditional R2R')
    ax.plot(tf, na_ctrl, color='#9C27B0', linewidth=2, label='NA Fusion Control')
    ax.set_title('Equipment Drift Control', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # Summary
    ax = axes[1, 2]
    depts = ['PID/YED\nYield', 'PID/YED\nDOE', 'MFG\nWIP', 'MFG\nDispatch', 'PE/EE\nControl', 'PE/EE\nMaint.']
    trad = [82, 75, 65, 70, 72, 68]
    na_vals = [94, 91, 88, 92, 95, 89]
    x = np.arange(len(depts))
    w = 0.35
    ax.bar(x - w/2, trad, w, label='Traditional', color='#FF6B6B', alpha=0.8)
    ax.bar(x + w/2, na_vals, w, label='NA Fusion', color='#9C27B0', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(depts, fontsize=7)
    ax.set_title('NA Fusion: Quantified Results', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 19 Demo: NA Fusion (Neural+Action) - E2E Optimization', fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch19_na_fusion.png')


def demo_ch20_sa_fusion():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    # HTN tree
    ax = axes[0, 0]
    ax.set_title('SA Fusion: HTN Task Decomposition', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis('off')
    root = FancyBboxPatch((5, 8.5), 4, 1.2, boxstyle='round,pad=0.1',
                           facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=2)
    ax.add_patch(root)
    ax.text(7, 9.1, 'NPI Process Dev\n(Root Goal)', ha='center', va='center', fontsize=8, fontweight='bold')
    layer2 = [(1.5, 6, 'Process\nDesign'), (5, 6, 'Equipment\nSetup'), (8.5, 6, 'Pilot Run\nVerification'), (12, 6, 'Yield\nImprovement')]
    for x, y, label in layer2:
        box = FancyBboxPatch((x-1.2, y-0.5), 2.4, 1, boxstyle='round,pad=0.1',
                             facecolor='#2196F3', alpha=0.15, edgecolor='#2196F3', linewidth=1.5)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
        ax.annotate('', xy=(x, 6.5), xytext=(7, 8.5), arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5))
    ax.text(0.2, 6, 'Symbolic\n(Planning)', fontsize=8, fontweight='bold', color='#2196F3', va='center')
    ax.text(0.2, 2.5, 'Action\n(RL Exec)', fontsize=8, fontweight='bold', color='#FF9800', va='center')

    # Comparison
    ax = axes[0, 1]
    tasks = ['NPI Cycle\n(weeks)', 'Task\nCompletion (%)', 'Resource\nUtil. (%)', 'Response\nTime (h)', 'Plan\nDeviation (%)']
    pure_rl = [12, 78, 72, 4.5, 15]
    pure_sym = [16, 85, 68, 6.0, 8]
    sa = [9, 93, 88, 1.5, 3]
    x = np.arange(len(tasks))
    w = 0.25
    ax.bar(x - w, pure_rl, w, label='Pure RL', color='#FF9800', alpha=0.8)
    ax.bar(x, pure_sym, w, label='Pure Symbolic', color='#2196F3', alpha=0.8)
    ax.bar(x + w, sa, w, label='SA Fusion', color='#9C27B0', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(tasks, fontsize=7)
    ax.set_title('Pure RL vs Symbolic vs SA', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # Anomaly response
    ax = axes[0, 2]
    ax.set_title('MFG: Anomaly Response Automation', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    steps = [(5, 9, 'Equipment Down Alert', '#F44336'), (5, 7, 'Symbolic: Match Response Rules', '#2196F3'),
             (5, 5, 'RL: WIP Transfer + PM Scheduling', '#FF9800'), (5, 3, 'Execution: Auto-adjusted', '#4CAF50'),
             (5, 1, 'Total: 38 min (Traditional: 4h+)', '#9C27B0')]
    for x, y, label, color in steps:
        box = FancyBboxPatch((x-2.5, y-0.5), 5, 1, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
    for i in range(4):
        ax.annotate('', xy=(5, steps[i+1][1]+0.5), xytext=(5, steps[i][1]-0.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # PM Gantt
    ax = axes[1, 0]
    tasks_g = [('PM-ToolA (Plan)', 0, 4, '#2196F3'), ('PM-ToolA (RL)', 4, 3, '#FF9800'),
               ('PM-ToolB (Plan)', 1, 3, '#2196F3'), ('PM-ToolB (RL)', 3.5, 2.5, '#FF9800'),
               ('PM-ToolC (Plan)', 5, 4, '#2196F3'), ('PM-ToolC (RL)', 9, 2, '#FF9800')]
    for i, (name, s, d, c) in enumerate(tasks_g):
        ax.barh(len(tasks_g)-i-1, d, left=s, height=0.6, color=c, alpha=0.7)
    ax.set_title('PM Plan (Symbolic) + Execution (RL)', fontsize=10, fontweight='bold')
    ax.set_xlabel('Time (h)')

    # Multi-agent
    ax = axes[1, 1]
    ax.set_title('Multi-Agent Symbolic-Action Architecture', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    center = FancyBboxPatch((3, 7), 4, 1.2, boxstyle='round,pad=0.15',
                             facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
    ax.add_patch(center)
    ax.text(5, 7.6, 'Symbolic Coordinator\n(Planner)', ha='center', va='center', fontsize=8, fontweight='bold')
    agents = [(1.5, 4, 'PID Agent\n(RL)'), (4, 4, 'MFG Agent\n(RL)'), (6.5, 4, 'PE Agent\n(RL)'), (8.5, 4, 'EE Agent\n(RL)')]
    for x, y, label in agents:
        box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1, boxstyle='round,pad=0.1',
                             facecolor='#FF9800', alpha=0.15, edgecolor='#FF9800', linewidth=1.5)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
        ax.annotate('', xy=(x, 4.5), xytext=(5, 7), arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))

    # Symbolic constraint benefit
    ax = axes[1, 2]
    episodes = np.arange(300)
    pure_rl_r = -30 + 0.1 * episodes + 10 * np.sin(episodes * 0.1) + np.random.randn(300) * 5
    pure_rl_r = np.cumsum(pure_rl_r) / np.arange(1, 301) * 10
    sa_r = -30 + 0.2 * episodes * (1 - np.exp(-episodes / 50)) + np.random.randn(300) * 2
    sa_r = np.cumsum(sa_r) / np.arange(1, 301) * 10
    w = 15
    rl_s = np.convolve(pure_rl_r, np.ones(w)/w, mode='valid')
    sa_s = np.convolve(sa_r, np.ones(w)/w, mode='valid')
    ax.plot(episodes[w-1:], rl_s, color='#FF9800', linewidth=2, linestyle='--', label='Pure RL')
    ax.plot(episodes[w-1:], sa_s, color='#9C27B0', linewidth=2.5, label='SA Fusion')
    ax.set_title('Symbolic Constraints Accelerate RL', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 20 Demo: SA Fusion (Symbolic+Action)', fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch20_sa_fusion.png')


def demo_ch21_nsa_fusion():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    # NSA loop
    ax = axes[0, 0]
    ax.set_title('NSA Full Fusion: Perception-Cognition-Action Loop', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    c1 = Circle((2, 7), 1.2, facecolor='#2196F3', alpha=0.2, edgecolor='#2196F3', linewidth=2)
    c2 = Circle((5, 7), 1.2, facecolor='#4CAF50', alpha=0.2, edgecolor='#4CAF50', linewidth=2)
    c3 = Circle((8, 7), 1.2, facecolor='#FF9800', alpha=0.2, edgecolor='#FF9800', linewidth=2)
    ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)
    ax.text(2, 7, 'Neural\n(Perception)', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(5, 7, 'Symbolic\n(Cognition)', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(8, 7, 'Action\n(Behavior)', ha='center', va='center', fontsize=8, fontweight='bold')
    cc = Circle((5, 3), 1.3, facecolor='#9C27B0', alpha=0.3, edgecolor='#9C27B0', linewidth=3)
    ax.add_patch(cc)
    ax.text(5, 3, 'NSA\nFull Fusion', ha='center', va='center', fontsize=9, fontweight='bold', color='#9C27B0')

    # Four stages
    ax = axes[0, 1]
    ax.set_title('NSA Four-Stage Evolution', fontsize=10, fontweight='bold')
    stages = ['AI-Assisted\n(Current)', 'AI-Augmented\n(1-2 yrs)', 'AI-Autonomous\n(3-5 yrs)', 'Embodied AI\n(5-10+ yrs)']
    colors_s = ['#81C784', '#FFB74D', '#E57373', '#BA68C8']
    for i, (s, c) in enumerate(zip(stages, colors_s)):
        box = FancyBboxPatch((i*2.5+0.2, 3), 2, 2, boxstyle='round,pad=0.1',
                             facecolor=c, alpha=0.2, edgecolor=c, linewidth=2)
        ax.add_patch(box)
        ax.text(i*2.5+1.2, 4, s, ha='center', va='center', fontsize=7, fontweight='bold')
    ax.set_xlim(0, 10.5); ax.set_ylim(2, 6); ax.axis('off')

    # Digital twin precision
    ax = axes[0, 2]
    t = np.linspace(0, 100, 200)
    real = 200 + 20*np.sin(t*0.1) + np.random.randn(200)*1.5
    twin_v1 = 200 + 20*np.sin(t*0.1-0.3) + np.random.randn(200)*3
    twin_v2 = 200 + 20*np.sin(t*0.1-0.05) + np.random.randn(200)*0.8
    ax.plot(t[:100], real[:100], color='#333', linewidth=2, label='Real Equipment')
    ax.plot(t[:100], twin_v1[:100], color='#FF9800', alpha=0.7, label='Twin v1 (RMSE=4.2)')
    ax.plot(t[:100], twin_v2[:100], color='#2196F3', alpha=0.7, label='Twin v2 (RMSE=1.1)')
    ax.set_title('Digital Twin Precision Evolution', fontsize=10, fontweight='bold')
    ax.legend(fontsize=7)

    # Self-healing
    ax = axes[1, 0]
    days = np.arange(50)
    trad = np.clip(100 - 1.2*days + 3*np.sin(days*0.3), 20, 100)
    sa = np.clip(100 - 0.3*days + 2*np.sin(days*0.3), 30, 100)
    nsa = np.clip(100 - 0.5*days + 2*np.sin(days*0.3), 50, 100)
    nsa[15:] = nsa[15:] + np.cumsum(np.exp(-np.abs(days[15:]-15)*0.5)*3)
    nsa = np.clip(nsa, 50, 100)
    ax.plot(days, trad, color='#F44336', label='Traditional PM')
    ax.plot(days, sa, color='#FF9800', label='SA Fusion')
    ax.plot(days, nsa, color='#9C27B0', linewidth=2.5, label='NSA Self-healing')
    ax.set_title('PE/EE: Self-healing Equipment System', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # Full-stack yield
    ax = axes[1, 1]
    stages_y = ['Design', 'NPI', 'Pilot', 'Ramp', 'Volume', 'Decline']
    trad_y = [85, 70, 75, 82, 88, 84]
    nsa_y = [92, 85, 90, 94, 96, 95]
    x = np.arange(len(stages_y))
    ax.bar(x - 0.15, trad_y, 0.3, label='Traditional', color='#FF6B6B', alpha=0.8)
    ax.bar(x + 0.15, nsa_y, 0.3, label='NSA Full Stack', color='#9C27B0', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(stages_y, fontsize=8)
    ax.set_title('PID/YED: Full-Stack Yield Intelligence', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)

    # Comparison matrix
    ax = axes[1, 2]
    depts = ['PID\nYield', 'PID\nRoot Cause', 'MFG\nDispatch', 'MFG\nWIP', 'PE\nPredict', 'PE\nControl']
    nb = [88, 92, 72, 70, 78, 72]
    na = [85, 70, 90, 82, 85, 90]
    sa = [70, 80, 85, 78, 82, 75]
    nsa = [95, 96, 97, 93, 94, 96]
    x = np.arange(len(depts))
    w = 0.2
    ax.bar(x - 1.5*w, nb, w, label='NB', color='#2196F3', alpha=0.7)
    ax.bar(x - 0.5*w, na, w, label='NA', color='#FF9800', alpha=0.7)
    ax.bar(x + 0.5*w, sa, w, label='SA', color='#4CAF50', alpha=0.7)
    ax.bar(x + 1.5*w, nsa, w, label='NSA', color='#9C27B0', alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels(depts, fontsize=7)
    ax.set_title('NB vs NA vs SA vs NSA', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)
    fig.suptitle('Chapter 21 Demo: NSA Full Fusion - Embodied Intelligence', fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch21_nsa_fusion.png')


def demo_ch22_llm_fab():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    # RAG architecture
    ax = axes[0, 0]
    ax.set_title('RAG Architecture Flow', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    steps = [(5, 9, 'User Query', '#E3F2FD'), (5, 7, 'Query Embedding', '#FFF3E0'),
             (5, 5, 'Knowledge Base Retrieval\n(SPEC + Manuals + KG)', '#E8F5E9'),
             (5, 3, 'Prompt Assembly\n(Query + Context)', '#FFFDE7'),
             (5, 1, 'LLM Generation\n(Answer + Citations)', '#E8F5E9')]
    for x, y, label, face in steps:
        box = FancyBboxPatch((x-2.5, y-0.5), 5, 1, boxstyle='round,pad=0.1',
                             facecolor=face, edgecolor='#666', linewidth=1.5)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold')
    for i in range(4):
        ax.annotate('', xy=(5, steps[i+1][1]+0.5), xytext=(5, steps[i][1]-0.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # Retrieval accuracy
    ax = axes[0, 1]
    qtypes = ['SPEC\nSearch', 'Manual\nQA', 'Process\nQuery', 'Report\nGen', 'Cross-doc\nReasoning']
    keyword = [65, 60, 58, 45, 30]
    vector = [78, 75, 72, 65, 55]
    rag = [94, 91, 93, 88, 85]
    x = np.arange(len(qtypes))
    w = 0.25
    ax.bar(x - w, keyword, w, label='Keyword', color='#FF6B6B', alpha=0.8)
    ax.bar(x, vector, w, label='Vector', color='#FF9800', alpha=0.8)
    ax.bar(x + w, rag, w, label='RAG', color='#2196F3', alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels(qtypes, fontsize=7)
    ax.set_title('Retrieval Accuracy Comparison', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # Hallucination rate
    ax = axes[0, 2]
    methods = ['Pure\nLLM', 'LLM+\nRetrieval', 'LLM+KG+\nRAG', 'LLM+KG+RAG\n+Self-verify']
    halluc = [22, 12, 4, 0.8]
    ax.bar(methods, halluc, color=['#F44336','#FF9800','#FFC107','#4CAF50'], alpha=0.8)
    ax.set_title('Hallucination Rate Comparison', fontsize=10, fontweight='bold')
    ax.set_ylabel('Hallucination Rate (%)')

    # Report generation speedup
    ax = axes[1, 0]
    sections = ['Data\nSummary', 'Statistical\nAnalysis', 'Anomaly\nDetection', 'Root Cause\nInference', 'Recommend.\nGeneration', 'Formatting\n& Output']
    manual = [45, 60, 40, 90, 30, 25]
    llm = [3, 5, 2, 8, 3, 1]
    x = np.arange(len(sections))
    ax.barh(x - 0.15, manual, 0.3, label='Manual', color='#FF6B6B', alpha=0.8)
    ax.barh(x + 0.15, llm, 0.3, label='LLM', color='#2196F3', alpha=0.9)
    ax.set_yticks(x); ax.set_yticklabels(sections, fontsize=7)
    ax.set_title('Report Generation: Manual vs LLM', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)

    # NL interaction
    ax = axes[1, 1]
    ax.set_title('Natural Language Data Interaction', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    q = FancyBboxPatch((0.3, 7.5), 5, 1.5, boxstyle='round,pad=0.15', facecolor='#E3F2FD', edgecolor='#2196F3', linewidth=1.5)
    ax.add_patch(q)
    ax.text(0.5, 8.6, '[User]', fontsize=8, fontweight='bold', color='#2196F3')
    ax.text(0.5, 8.0, '"What is the yield trend\nfor Tool-A03 Step23 last week?"', fontsize=8.5, va='center')
    p = FancyBboxPatch((0.3, 4), 9.4, 2.5, boxstyle='round,pad=0.15', facecolor='#FFF3E0', edgecolor='#FF9800', linewidth=1.5)
    ax.add_patch(p)
    ax.text(0.5, 6.1, '[LLM Processing]', fontsize=8, fontweight='bold', color='#FF9800')
    ax.text(0.5, 5.5, '1. Entity: Tool=A03, Step=23, Time=last 7 days', fontsize=8)
    ax.text(0.5, 5.0, '2. SQL: SELECT yield FROM lot_data WHERE...', fontsize=8)
    ax.text(0.5, 4.5, '3. Context: SPC data + KG relations', fontsize=8)
    a = FancyBboxPatch((0.3, 0.5), 9.4, 3, boxstyle='round,pad=0.15', facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=1.5)
    ax.add_patch(a)
    ax.text(0.5, 3.1, '[LLM Answer]', fontsize=8, fontweight='bold', color='#4CAF50')
    lines = ['Tool-A03 Step23 yield (last 7 days):', '- Mean: 91.3% (Target: 92%)',
             '- Trend: Stable 5 days, dropped to 87% on day 6', '- Anomaly: SPC 2.8 sigma on day 6',
             '- Root cause: Alignment temp +2.3C | Rec: Check cooling']
    for i, line in enumerate(lines):
        ax.text(0.5, 2.7 - i*0.4, line, fontsize=8)

    # Application summary
    ax = axes[1, 2]
    apps = ['SPEC\nSearch', 'Manual\nQA', 'Report\nAuto-gen', 'Cross-sys\nQuery', 'Work\nOrder', 'Production\nReport', 'Change\nEval']
    manual_t = [30, 25, 60, 90, 45, 60, 180]
    llm_t = [2, 3, 5, 5, 3, 4, 15]
    x = np.arange(len(apps))
    ax.bar(x - 0.15, manual_t, 0.3, label='Manual (min)', color='#FF6B6B', alpha=0.7)
    ax.bar(x + 0.15, llm_t, 0.3, label='LLM (min)', color='#2196F3', alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels(apps, fontsize=7)
    ax.set_title('LLM Application: Efficiency Comparison', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)
    fig.suptitle('Chapter 22 Demo: LLM Applications in Wafer Fabs', fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch22_llm_fab.png')


def demo_ch23_agent_system():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    # Multi-agent architecture
    ax = axes[0, 0]
    ax.set_title('Multi-Agent Collaborative Architecture', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    center = FancyBboxPatch((3, 7.5), 4, 1.2, boxstyle='round,pad=0.15',
                             facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
    ax.add_patch(center)
    ax.text(5, 8.1, 'Coordinator Agent\n(Perception-Planning-Dispatch)', ha='center', va='center', fontsize=8, fontweight='bold')
    agents = [(1.2, 5, 'PID Agent\n(RAG+Reasoning)', '#2196F3'), (4, 5, 'YED Agent\n(ML+KG)', '#4CAF50'),
              (6.8, 5, 'MFG Agent\n(RL+MILP)', '#FF9800'), (9, 5, 'EE Agent\n(Time-series+RL)', '#F44336')]
    for x, y, label, color in agents:
        box = FancyBboxPatch((x-1, y-0.7), 2, 1.4, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box); ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')
        ax.annotate('', xy=(x, 5.7), xytext=(5, 7.5), arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))
    mem = FancyBboxPatch((1, 2.5), 8, 1, boxstyle='round,pad=0.1',
                         facecolor='#607D8B', alpha=0.1, edgecolor='#607D8B', linewidth=1.5)
    ax.add_patch(mem)
    ax.text(5, 3, 'Shared Memory (Short+Long-term, Vector DB)', ha='center', va='center', fontsize=8, fontweight='bold')

    # Response timeline
    ax = axes[0, 1]
    ax.set_title('Agent Response Timeline: Yield Anomaly', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 20); ax.set_ylim(0, 6); ax.axis('off')
    steps = [(1.5, 'T+0min\nYED Agent\ndetects -7pp', '#4CAF50'),
             (5, 'T+2min\nCoordinator\ndistributes tasks', '#9C27B0'),
             (8.5, 'T+5min\nPID Agent\nroot cause (RAG+KG)', '#2196F3'),
             (12, 'T+8min\nMFG Agent\nWIP adjust (RL)', '#FF9800'),
             (15.5, 'T+12min\nEE Agent\nequipment check', '#F44336'),
             (19, 'T+18min\nResolved\nyield restored', '#4CAF50')]
    for x, label, color in steps:
        box = FancyBboxPatch((x-1.3, 1.5), 2.6, 2.5, boxstyle='round,pad=0.1',
                             facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            ax.text(x, 3.5 - j*0.5, line, ha='center', va='center', fontsize=7, fontweight='bold')
    for i in range(5):
        ax.annotate('', xy=(steps[i+1][0]-1.3, 2.75), xytext=(steps[i][0]+1.3, 2.75),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))

    # Agent vs Traditional
    ax = axes[0, 2]
    metrics = ['Detection\n(min)', 'Root Cause\n(min)', 'Execution\n(min)', 'Total Time\n(h)', 'Accuracy\n(%)']
    trad = [30, 120, 60, 3.5, 75]
    agent = [0.2, 5, 3, 0.3, 94]
    x = np.arange(len(metrics))
    w = 0.35
    ax.bar(x - w/2, trad, w, label='Traditional', color='#FF6B6B', alpha=0.8)
    ax.bar(x + w/2, agent, w, label='Agent System', color='#9C27B0', alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=7)
    ax.set_title('Traditional vs Agent System', fontsize=10, fontweight='bold')
    ax.legend(fontsize=9)

    # Learning curve
    ax = axes[1, 0]
    episodes = np.arange(100)
    res_time = 20 * np.exp(-episodes / 25) + 2 + np.random.randn(100) * 0.5
    accuracy = np.clip(70 + 25 * (1 - np.exp(-episodes / 30)) + np.random.randn(100) * 2, 70, 97)
    ax.plot(episodes, res_time, 'o-', color='#FF9800', linewidth=2, markersize=3, label='Resolution Time (min)')
    ax_twin = ax.twinx()
    ax_twin.plot(episodes, accuracy, 's-', color='#4CAF50', linewidth=2, markersize=3, label='Accuracy (%)')
    ax.set_title('Agent Learning Curve', fontsize=10, fontweight='bold')
    ax.set_xlabel('Cases Processed')
    ax.legend(fontsize=8, loc='upper right'); ax_twin.legend(fontsize=8, loc='center right')

    # Dynamic scheduling
    ax = axes[1, 1]
    t = np.arange(48)
    fifo = np.clip(65 + 20*np.sin(t*0.3) + np.random.randn(48)*8, 50, 95)
    agent_u = np.clip(85 + 6*np.sin(t*0.2) + np.random.randn(48)*3, 78, 95)
    ax.plot(t, fifo, 'o-', color='#FF6B6B', linewidth=1.5, markersize=3, label='FIFO')
    ax.plot(t, agent_u, 's-', color='#9C27B0', linewidth=2, markersize=3, label='Agent Dynamic')
    ax.axhline(y=90, color='#4CAF50', linestyle=':', alpha=0.5, label='Target (90%)')
    ax.set_title('MFG Agent: Dynamic Scheduling (48h)', fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)

    # Digital twin + Agent
    ax = axes[1, 2]
    ax.set_title('Digital Twin + Agent Closed Loop', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    layers = [(6.5, 'Digital Twin Layer (Real-time Mirror)', '#2196F3'),
              (3.5, 'Agent Decision Layer (Reasoning+Opt+Verify)', '#9C27B0'),
              (0.5, 'Physical Factory (Equipment+WIP+Process)', '#4CAF50')]
    for y, label, color in layers:
        box = FancyBboxPatch((1, y), 8, 1.5, boxstyle='round,pad=0.15',
                             facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(box); ax.text(5, y+0.75, label, ha='center', va='center', fontsize=8, fontweight='bold')
    ax.annotate('', xy=(5, 5), xytext=(5, 6.5), arrowprops=dict(arrowstyle='<->', color='#2196F3', lw=2))
    ax.annotate('', xy=(5, 2), xytext=(5, 3.5), arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=2))
    fig.suptitle('Chapter 23 Demo: Agent Systems in Wafer Fabs - Multi-Agent Collaboration', fontsize=13, fontweight='bold')
    save_fig(fig, 'demo_ch23_agent_system.png')


# ============================================================
# Generate all images
# ============================================================

if __name__ == '__main__':
    print("=== Generating English flowcharts ===")
    flow_ch1_value()
    flow_ch2_timeline()
    flow_ch3_symbolism()
    flow_ch4_connectionism()
    flow_ch5_behaviorism()
    flow_ch6_npi()
    flow_ch7_dispatch()
    flow_ch8_pm()
    flow_ch14_expert_system()
    flow_ch15_training_pipeline()
    flow_ch16_mdp_loop()
    flow_ch17_fusion_map()
    flow_ch18_nb_rca()
    flow_ch19_na_loop()
    flow_ch19_rlhf()
    flow_ch20_sa_architecture()
    flow_ch20_multiagent()
    flow_ch21_nsa_loop()
    flow_ch21_evolution()
    flow_ch22_rag()
    flow_ch23_agent()
    flow_ch24_ontology()

    print("\n=== Generating English demo images ===")
    demo_ch2_three_schools()
    demo_ch6_wafer_defect()
    demo_ch7_smart_scheduling()
    demo_ch8_predictive_maintenance()
    demo_ch14_kg_rca()
    demo_ch15_cnn_detection()
    demo_ch15_yield_prediction()
    demo_ch16_rl_optimization()
    demo_ch16_marl()
    demo_ch18_nb_fusion()
    demo_ch19_na_fusion()
    demo_ch20_sa_fusion()
    demo_ch21_nsa_fusion()
    demo_ch22_llm_fab()
    demo_ch23_agent_system()

    print(f"\nAll English images generated in: {EN_IMAGE_DIR}")
    print(f"Total files: {len(os.listdir(EN_IMAGE_DIR))}")
