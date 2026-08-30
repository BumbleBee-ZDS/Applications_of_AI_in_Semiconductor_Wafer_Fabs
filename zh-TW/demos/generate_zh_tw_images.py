# -*- coding: utf-8 -*-
"""
Generate all flowchart and demo images with Traditional Chinese (Taiwan) labels.
Uses OpenCC to dynamically convert Simplified Chinese text to Traditional Chinese
by monkeypatching matplotlib's text rendering functions.

Author: Dawson Zhu
"""
import os
import sys
import re
import numpy as np
import opencc

# Add the original demos directory to path
ORIGINAL_DEMOS = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\demos'
sys.path.insert(0, ORIGINAL_DEMOS)

# Setup OpenCC converter (Simplified -> Taiwan Traditional with phrase conversion)
cc = opencc.OpenCC('s2twp')

# Semiconductor-specific terminology overrides (OpenCC may not get these right)
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
    '互联': '互聯',
    '互通': '互通',
    '落地': '落地',
    '弯道超车': '彎道超車',
}


def convert_text(text):
    """Convert Simplified Chinese text to Traditional Chinese with term overrides."""
    if not isinstance(text, str):
        return text
    if not text.strip():
        return text
    
    # Check if text contains any Chinese characters
    if not re.search(r'[\u4e00-\u9fff]', text):
        return text
    
    # Apply term overrides first (longest match first for accuracy)
    result = text
    for simp, trad in sorted(TERM_OVERRIDES.items(), key=lambda x: -len(x[0])):
        result = result.replace(simp, trad)
    
    # Then apply OpenCC for remaining characters
    result = cc.convert(result)
    
    return result


# Now monkeypatch matplotlib BEFORE importing
import matplotlib
matplotlib.use('Agg')

# Set font for Traditional Chinese
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt
import matplotlib.text as mtext
import matplotlib.axes as maxes

# Save original methods
_original_set_title = maxes.Axes.set_title
_original_set_xlabel = maxes.Axes.set_xlabel
_original_set_ylabel = maxes.Axes.set_ylabel
_original_text = maxes.Axes.text
_original_set_xticklabels = maxes.Axes.set_xticklabels
_original_set_yticklabels = maxes.Axes.set_yticklabels
_original_legend = maxes.Axes.legend
_original_annotate = maxes.Axes.annotate

# Patch methods
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

maxes.Axes.set_title = patched_set_title
maxes.Axes.set_xlabel = patched_set_xlabel
maxes.Axes.set_ylabel = patched_set_ylabel
maxes.Axes.text = patched_text
maxes.Axes.set_xticklabels = patched_set_xticklabels
maxes.Axes.set_yticklabels = patched_set_yticklabels
maxes.Axes.legend = patched_legend
maxes.Axes.annotate = patched_annotate

# Also patch Figure.suptitle
import matplotlib.figure as mfigure
_original_suptitle = mfigure.Figure.suptitle
def patched_suptitle(self, t, *args, **kwargs):
    return _original_suptitle(self, convert_text(t), *args, **kwargs)
mfigure.Figure.suptitle = patched_suptitle

np.random.seed(42)

# Output directory
ZH_TW_IMAGE_DIR = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-TW\images'
os.makedirs(ZH_TW_IMAGE_DIR, exist_ok=True)

# Import original modules and redirect save paths
# We'll manually run each function and save to our output dir

print("=== 生成繁體中文版流程圖 ===")

# Re-implement save_fig to redirect to zh-TW directory
def save_fig_zh_tw(fig, name):
    path = os.path.join(ZH_TW_IMAGE_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  已儲存: {name}")


# We need to import each module and modify its save path, then call functions.
# Since the original scripts have their own save logic, let's run them differently.
# Approach: import each module, override its IMAGE_DIR / save function, then call.

import importlib.util

def run_module_with_redirect(module_path, function_names, output_dir):
    """Run a module's functions with redirected image output."""
    spec = importlib.util.spec_from_file_location(
        os.path.basename(module_path).replace('.py', ''),
        module_path
    )
    module = importlib.util.module_from_spec(spec)
    
    # Override save path before executing
    # We'll monkey patch plt.savefig and fig.savefig
    original_savefig = plt.savefig
    original_fig_savefig = plt.Figure.savefig
    
    saved_files = []
    
    def patched_savefig(*args, **kwargs):
        if args and isinstance(args[0], str):
            fname = os.path.basename(args[0])
            new_path = os.path.join(output_dir, fname)
            saved_files.append(fname)
            return original_savefig(new_path, *args[1:], **kwargs)
        return original_savefig(*args, **kwargs)
    
    def patched_fig_savefig(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            fname = os.path.basename(args[0])
            new_path = os.path.join(output_dir, fname)
            saved_files.append(fname)
            return original_fig_savefig(self, new_path, *args[1:], **kwargs)
        return original_fig_savefig(self, *args, **kwargs)
    
    plt.savefig = patched_savefig
    plt.Figure.savefig = patched_fig_savefig
    
    try:
        spec.loader.exec_module(module)
        for func_name in function_names:
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                if callable(func):
                    func()
    finally:
        plt.savefig = original_savefig
        plt.Figure.savefig = original_fig_savefig
    
    return saved_files


# Run all flowchart batches
flowchart_scripts = [
    ('flowcharts_batch1.py', ['generate_all']),
    ('flowcharts_batch2.py', ['generate_all']),
    ('flowcharts_batch3.py', ['generate_all']),
]

for script, funcs in flowchart_scripts:
    script_path = os.path.join(ORIGINAL_DEMOS, script)
    if os.path.exists(script_path):
        print(f"\n執行 {script}...")
        try:
            run_module_with_redirect(script_path, funcs, ZH_TW_IMAGE_DIR)
        except Exception as e:
            print(f"  [錯誤] {script}: {e}")

# Run all demo scripts
demo_scripts = [
    'demo_ch2_three_schools.py',
    'demo_ch6_wafer_defect.py',
    'demo_ch7_smart_scheduling.py',
    'demo_ch8_predictive_maintenance.py',
    'demo_ch14_kg_rca.py',
    'demo_ch15_cnn_detection.py',
    'demo_ch15_yield_prediction.py',
    'demo_ch16_rl_optimization.py',
    'demo_ch16_marl.py',
    'demo_ch18_nb_fusion.py',
    'demo_ch19_na_fusion.py',
    'demo_ch20_sa_fusion.py',
    'demo_ch21_nsa_fusion.py',
    'demo_ch22_llm_fab.py',
    'demo_ch23_agent_system.py',
]

print("\n=== 生成繁體中文版Demo圖 ===")

for script in demo_scripts:
    script_path = os.path.join(ORIGINAL_DEMOS, script)
    if os.path.exists(script_path):
        print(f"\n執行 {script}...")
        try:
            # Try to find the main function
            spec = importlib.util.spec_from_file_location(
                script.replace('.py', ''),
                script_path
            )
            module = importlib.util.module_from_spec(spec)
            
            # Patch savefig
            original_fig_savefig = plt.Figure.savefig
            saved = []
            def patched_fig_savefig(self, *args, **kwargs):
                if args and isinstance(args[0], str):
                    fname = os.path.basename(args[0])
                    new_path = os.path.join(ZH_TW_IMAGE_DIR, fname)
                    saved.append(fname)
                    return original_fig_savefig(self, new_path, *args[1:], **kwargs)
                return original_fig_savefig(self, *args, **kwargs)
            
            original_plt_savefig = plt.savefig
            def patched_plt_savefig(*args, **kwargs):
                if args and isinstance(args[0], str):
                    fname = os.path.basename(args[0])
                    new_path = os.path.join(ZH_TW_IMAGE_DIR, fname)
                    saved.append(fname)
                    return original_plt_savefig(new_path, *args[1:], **kwargs)
                return original_plt_savefig(*args, **kwargs)
            
            plt.Figure.savefig = patched_fig_savefig
            plt.savefig = patched_plt_savefig
            
            try:
                spec.loader.exec_module(module)
                # Look for main-like function or generate function
                main_funcs = [f for f in dir(module) if f.startswith('generate') or f.startswith('demo') or f == 'main']
                if main_funcs:
                    for fname in main_funcs:
                        func = getattr(module, fname)
                        if callable(func):
                            try:
                                func()
                            except Exception as e:
                                pass
                if not saved:
                    # Try the __main__ block by running as script
                    pass
                for s in saved:
                    print(f"  已儲存: {s}")
            finally:
                plt.Figure.savefig = original_fig_savefig
                plt.savefig = original_plt_savefig
        except Exception as e:
            print(f"  [錯誤] {script}: {e}")

print(f"\n\n繁體中文圖片生成完成，輸出目錄: {ZH_TW_IMAGE_DIR}")
total = len([f for f in os.listdir(ZH_TW_IMAGE_DIR) if f.endswith('.png')])
print(f"總計: {total} 個檔案")
