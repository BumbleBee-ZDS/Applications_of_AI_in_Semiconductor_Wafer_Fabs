# -*- coding: utf-8 -*-
"""
Generate the 7 missing flowcharts with Traditional Chinese labels.
Uses OpenCC to dynamically convert Simplified Chinese to Traditional Chinese.
"""
import os
import sys
import re
import numpy as np
import opencc

ORIGINAL_DEMOS = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\demos'
sys.path.insert(0, ORIGINAL_DEMOS)

cc = opencc.OpenCC('s2twp')

TERM_OVERRIDES = {
    '光刻': '微影',
    '刻蚀': '蝕刻',
    '蚀刻': '蝕刻',
    '离子注入': '離子佈植',
    '光刻胶': '光阻',
    '光阻剂': '光阻',
    '工艺': '製程',
    '制程': '製程',
    '调度': '排程',
    '派工': '派工',
    '良率': '良率',
    '晶圆': '晶圓',
    '芯片': '晶片',
    '半导体': '半導體',
    '晶圆厂': '晶圓廠',
    '软件': '軟體',
    '硬件': '硬體',
    '数据': '資料',
    '信息': '資訊',
    '质量': '品質',
    '算法': '演算法',
    '应用': '應用',
    '优化': '最佳化',
    '网络': '網路',
    '系统': '系統',
    '开发': '開發',
    '技术': '技術',
    '设备': '設備',
    '设计': '設計',
    '人工智能': '人工智慧',
    '深度学习': '深度學習',
    '机器学习': '機器學習',
    '强化学习': '強化學習',
    '神经网络': '類神經網路',
    '沉积': '沉積',
    '英特尔': '英特爾',
    '中芯国际': '中芯國際',
    '台积电': '台積電',
    '应用材料': '應用材料',
    '制造': '製造',
    '生产': '生產',
    '研发': '研發',
    '维护': '維護',
    '集成': '整合',
    '测试': '測試',
    '检测': '檢測',
    '监控': '監控',
    '监测': '監測',
    '瓶颈': '瓶頸',
    '参数': '參數',
    '架构': '架構',
    '知识': '知識',
    '符号': '符號',
    '连接': '連接',
    '行为': '行為',
    '认知': '認知',
    '决策': '決策',
    '学习': '學習',
    '训练': '訓練',
    '预测': '預測',
    '识别': '辨識',
    '特征': '特徵',
    '反馈': '回饋',
    '奖励': '獎勵',
    '价值': '價值',
    '经验': '經驗',
    '实验': '實驗',
    '验证': '驗證',
    '部署': '部署',
    '场景': '場景',
    '领域': '領域',
    '行业': '產業',
    '企业': '企業',
    '问题': '問題',
    '挑战': '挑戰',
    '机遇': '機遇',
    '趋势': '趨勢',
    '时代': '時代',
    '创新': '創新',
    '转型': '轉型',
    '升级': '升級',
    '数字化': '數位化',
    '智能化': '智慧化',
    '自动化': '自動化',
    '可视化': '視覺化',
    '标准化': '標準化',
    '周期': '週期',
    '步骤': '步驟',
    '阶段': '階段',
    '层次': '層次',
    '结构': '結構',
    '体系': '體系',
    '机制': '機制',
    '规则': '規則',
    '策略': '策略',
    '路径': '路徑',
    '性能': '效能',
    '效率': '效率',
    '成本': '成本',
    '风险': '風險',
    '稳定': '穩定',
    '灵活': '靈活',
    '精准': '精準',
    '实时': '即時',
    '动态': '動態',
    '全局': '全域',
    '关键': '關鍵',
    '基础': '基礎',
    '本质': '本質',
    '现象': '現象',
    '规律': '規律',
    '理论': '理論',
    '实践': '實踐',
    '实现': '實現',
    '实施': '實施',
    '执行': '執行',
    '运行': '運行',
    '项目': '專案',
    '计划': '計畫',
    '目标': '目標',
    '指标': '指標',
    '标准': '標準',
    '规范': '規範',
    '需求': '需求',
    '资源': '資源',
    '市场': '市場',
    '客户': '客戶',
    '用户': '使用者',
    '产品': '產品',
    '服务': '服務',
    '业务': '業務',
    '运营': '營運',
    '经营': '經營',
    '组织': '組織',
    '团队': '團隊',
    '部门': '部門',
    '职责': '職責',
    '权限': '權限',
    '责任': '責任',
    '增长': '成長',
    '发展': '發展',
    '提升': '提升',
    '改善': '改善',
    '减少': '減少',
    '扩大': '擴大',
    '改变': '改變',
    '转变': '轉變',
    '转化': '轉化',
    '转换': '轉換',
    '传输': '傳輸',
    '传递': '傳遞',
    '传播': '傳播',
    '沟通': '溝通',
    '协作': '協作',
    '竞争': '競爭',
    '对比': '對比',
    '分析': '分析',
    '综合': '綜合',
    '总结': '總結',
    '归纳': '歸納',
    '演绎': '演繹',
    '判断': '判斷',
    '理解': '理解',
    '认识': '認識',
    '意识': '意識',
    '关注': '關注',
    '重视': '重視',
    '强调': '強調',
    '表明': '表明',
    '显示': '顯示',
    '说明': '說明',
    '证明': '證明',
    '发现': '發現',
    '发明': '發明',
    '创造': '創造',
    '探索': '探索',
    '研究': '研究',
    '调查': '調查',
    '观察': '觀察',
    '试验': '試驗',
    '检验': '檢驗',
    '确认': '確認',
    '评估': '評估',
    '评价': '評價',
    '计算': '計算',
    '估算': '估算',
    '预警': '預警',
    '诊断': '診斷',
    '修复': '修復',
    '保养': '保養',
    '维修': '維修',
    '替换': '替換',
    '改进': '改進',
    '完善': '完善',
    '英伟达': '輝達',
    '格罗方德': '格羅方德',
    '高通': '高通',
    '互联': '互聯',
    '互通': '互通',
    '落地': '落地',
    '弯道超车': '彎道超車',
    '根因': '根因',
    '缺陷': '缺陷',
    '在制品': '在製品',
    '预维护': '預防性維護',
    '预测性维护': '預測性維護',
    '预防性维护': '預防性維護',
    '新品导入': '新產品導入',
    '新产品导入': '新產品導入',
    '爬坡': '爬坡',
    '良率爬坡': '良率爬坡',
    '异常检测': '異常檢測',
    '故障检测': '故障檢測',
    '故障分类': '故障分類',
    '统计过程控制': '統計過程控制',
    '先进过程控制': '先進製程控制',
    ' Run-to-Run': ' Run-to-Run',
    '虚拟量测': '虛擬量測',
    '自动光学检测': '自動光學檢測',
    '扫描电镜': '掃描電子顯微鏡',
    '透射电镜': '穿透式電子顯微鏡',
    '原子力显微镜': '原子力顯微鏡',
    '聚焦离子束': '聚焦離子束',
    '化学机械抛光': '化學機械拋光',
    '化学气相沉积': '化學氣相沉積',
    '物理气相沉积': '物理氣相沉積',
    '原子层沉积': '原子層沉積',
    '等离子体刻蚀': '電漿蝕刻',
    '反应离子刻蚀': '反應式離子蝕刻',
    '湿法刻蚀': '濕式蝕刻',
    '干法刻蚀': '乾式蝕刻',
    '快速热退火': '快速熱退火',
    '炉管': '爐管',
    '扩散': '擴散',
    '薄膜沉积': '薄膜沉積',
    '清洗': '清洗',
    '研磨': '研磨',
    'CMP': 'CMP',
    'CVD': 'CVD',
    'PVD': 'PVD',
    'ALD': 'ALD',
    'RIE': 'RIE',
    'ICP': 'ICP',
    'PVD': 'PVD',
    'RTP': 'RTP',
    'FIB': 'FIB',
    'SEM': 'SEM',
    'TEM': 'TEM',
    'AFM': 'AFM',
    'AOI': 'AOI',
    'VM': 'VM',
    'APC': 'APC',
    'SPC': 'SPC',
    'FDC': 'FDC',
    'R2R': 'R2R',
    'EHS': 'EHS',
    'OEE': 'OEE',
    'MES': 'MES',
    'ERP': 'ERP',
    'APS': 'APS',
    'AMHS': 'AMHS',
    'WIP': 'WIP',
    'NPI': 'NPI',
    'DOE': 'DOE',
    'PID': 'PID',
    'YED': 'YED',
    'MFG': 'MFG',
    'PE': 'PE',
    'EE': 'EE',
    'PM': 'PM',
    'CM': 'CM',
    'PdM': 'PdM',
    'RUL': 'RUL',
    'MTBF': 'MTBF',
    'MTTR': 'MTTR',
    'KPI': 'KPI',
    'ROC': 'ROC',
    'AUC': 'AUC',
    'mAP': 'mAP',
    'IoU': 'IoU',
    'GAN': 'GAN',
    'VAE': 'VAE',
    'RNN': 'RNN',
    'CNN': 'CNN',
    'DNN': 'DNN',
    'LSTM': 'LSTM',
    'GRU': 'GRU',
    'RL': 'RL',
    'DL': 'DL',
    'ML': 'ML',
    'AI': 'AI',
    'LLM': 'LLM',
    'RAG': 'RAG',
    'LoRA': 'LoRA',
    'QLoRA': 'QLoRA',
    'SFT': 'SFT',
    'RLHF': 'RLHF',
    'PPO': 'PPO',
    'DQN': 'DQN',
    'DDPG': 'DDPG',
    'SAC': 'SAC',
    'A2C': 'A2C',
    'A3C': 'A3C',
    'PPO': 'PPO',
    'MARL': 'MARL',
    'MDP': 'MDP',
    'POMDP': 'POMDP',
    'Ontology': 'Ontology',
    'KG': 'KG',
    'RDF': 'RDF',
    'OWL': 'OWL',
    'SPARQL': 'SPARQL',
    'Cypher': 'Cypher',
    'SQL': 'SQL',
    'API': 'API',
    'GUI': 'GUI',
    'UI': 'UI',
    'UX': 'UX',
    'SDK': 'SDK',
    'IDE': 'IDE',
    'CLI': 'CLI',
    'OS': 'OS',
    'CPU': 'CPU',
    'GPU': 'GPU',
    'TPU': 'TPU',
    'FPGA': 'FPGA',
    'ASIC': 'ASIC',
    'SoC': 'SoC',
    'IP': 'IP',
    'EDA': 'EDA',
    'RTL': 'RTL',
    'GDSII': 'GDSII',
    'OPC': 'OPC',
    'RET': 'RET',
    'DUV': 'DUV',
    'EUV': 'EUV',
    'ArF': 'ArF',
    'KrF': 'KrF',
    'i-line': 'i-line',
    'FinFET': 'FinFET',
    'GAA': 'GAA',
    'CFET': 'CFET',
    '3D-IC': '3D-IC',
    'HBM': 'HBM',
    'CoWoS': 'CoWoS',
    'SoIC': 'SoIC',
    'InFO': 'InFO',
    '2.5D': '2.5D',
    '3D': '3D',
    'Chiplet': 'Chiplet',
}


def convert_text(text):
    if not isinstance(text, str):
        return text
    if not text.strip():
        return text
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text
    
    result = text
    for simp, trad in sorted(TERM_OVERRIDES.items(), key=lambda x: -len(x[0])):
        result = result.replace(simp, trad)
    
    result = cc.convert(result)
    return result


import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt
import matplotlib.axes as maxes
import matplotlib.figure as mfigure
import matplotlib.text as mtext

_original_set_title = maxes.Axes.set_title
_original_set_xlabel = maxes.Axes.set_xlabel
_original_set_ylabel = maxes.Axes.set_ylabel
_original_text = maxes.Axes.text
_original_set_xticklabels = maxes.Axes.set_xticklabels
_original_set_yticklabels = maxes.Axes.set_yticklabels
_original_legend = maxes.Axes.legend
_original_annotate = maxes.Axes.annotate
_original_suptitle = mfigure.Figure.suptitle
_original_set_ylabel_fig = mfigure.Figure.suptitle

def patched_set_title(self, label, *args, **kwargs):
    return _original_set_title(self, convert_text(label), *args, **kwargs)

def patched_set_xlabel(self, xlabel, *args, **kwargs):
    return _original_set_xlabel(self, convert_text(xlabel), *args, **kwargs)

def patched_set_ylabel(self, ylabel, *args, **kwargs):
    return _original_set_ylabel(self, convert_text(ylabel), *args, **kwargs)

def patched_text(self, x, y, s, *args, **kwargs):
    return _original_text(self, x, y, convert_text(s), *args, **kwargs)

def patched_set_xticklabels(self, labels, *args, **kwargs):
    converted = [convert_text(l) if isinstance(l, str) else l for l in labels]
    return _original_set_xticklabels(self, converted, *args, **kwargs)

def patched_set_yticklabels(self, labels, *args, **kwargs):
    converted = [convert_text(l) if isinstance(l, str) else l for l in labels]
    return _original_set_yticklabels(self, converted, *args, **kwargs)

def patched_legend(self, *args, **kwargs):
    handles, labels = self.get_legend_handles_labels()
    if not args and 'labels' not in kwargs and labels:
        kwargs['labels'] = [convert_text(l) for l in labels]
    elif 'labels' in kwargs:
        kwargs['labels'] = [convert_text(l) for l in kwargs['labels']]
    return _original_legend(self, *args, **kwargs)

def patched_annotate(self, text, xy, *args, **kwargs):
    return _original_annotate(self, convert_text(text), xy, *args, **kwargs)

def patched_suptitle(self, t, *args, **kwargs):
    return _original_suptitle(self, convert_text(t), *args, **kwargs)

maxes.Axes.set_title = patched_set_title
maxes.Axes.set_xlabel = patched_set_xlabel
maxes.Axes.set_ylabel = patched_set_ylabel
maxes.Axes.text = patched_text
maxes.Axes.set_xticklabels = patched_set_xticklabels
maxes.Axes.set_yticklabels = patched_set_yticklabels
maxes.Axes.legend = patched_legend
maxes.Axes.annotate = patched_annotate
mfigure.Figure.suptitle = patched_suptitle

np.random.seed(42)

ZH_TW_IMAGE_DIR = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-TW\images'
os.makedirs(ZH_TW_IMAGE_DIR, exist_ok=True)

# Patch plt.savefig and Figure.savefig to redirect output
_original_plt_savefig = plt.savefig
_original_fig_savefig = plt.Figure.savefig

def patched_plt_savefig(*args, **kwargs):
    if args and isinstance(args[0], str):
        fname = os.path.basename(args[0])
        new_path = os.path.join(ZH_TW_IMAGE_DIR, fname)
        print(f"  已儲存: {fname}")
        return _original_plt_savefig(new_path, *args[1:], **kwargs)
    return _original_plt_savefig(*args, **kwargs)

def patched_fig_savefig(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        fname = os.path.basename(args[0])
        new_path = os.path.join(ZH_TW_IMAGE_DIR, fname)
        print(f"  已儲存: {fname}")
        return _original_fig_savefig(self, new_path, *args[1:], **kwargs)
    return _original_fig_savefig(self, *args, **kwargs)

plt.savefig = patched_plt_savefig
plt.Figure.savefig = patched_fig_savefig

print("=== 生成剩餘的繁體流程圖 (flowcharts_all.py) ===")

# Execute flowcharts_all.py
script_path = os.path.join(ORIGINAL_DEMOS, 'flowcharts_all.py')
with open(script_path, 'r', encoding='utf-8') as f:
    script_content = f.read()

# Execute in current namespace
exec(script_content, globals())

print("\n=== 完成 ===")
total = len([f for f in os.listdir(ZH_TW_IMAGE_DIR) if f.endswith('.png')])
print(f"繁體中文圖片總數: {total}")
