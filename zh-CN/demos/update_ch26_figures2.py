# -*- coding: utf-8 -*-
"""补丁: 插入 VLA 流程图为图26-2, 并将 EFEM/三层架构编号顺移为 26-3/26-4"""
import io

NL = '\r\n'

jobs = [
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\chapters\part6\chapter26.md',
     '*图26-1：具身智能"感知-理解-规划-执行"技术栈，学习反馈闭环持续改进规划与执行层*',
     NL + NL + '![VLA(视觉-语言-行动)模型工作流程](../../images/flow_ch26_vla_pipeline.png)' + NL + NL +
     '*图26-2：VLA（视觉-语言-行动）模型工作流程——视觉输入与自然语言指令端到端统一生成动作序列*',
     ('*图26-3：具身智能 Agent 三层架构', '*图26-4：具身智能 Agent 三层架构'),
     ('*图26-2：洁净室机械臂 EFEM 自动上下料工作流', '*图26-3：洁净室机械臂 EFEM 自动上下料工作流')),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-TW\chapters\part6\chapter26.md',
     '*圖26-1：具身智慧「感知-理解-規劃-執行」技術堆疊，學習回饋閉環持續改進規劃與執行層*',
     NL + NL + '![VLA(視覺-語言-行動)模型工作流程](../../images/flow_ch26_vla_pipeline.png)' + NL + NL +
     '*圖26-2：VLA（視覺-語言-行動）模型工作流程——視覺輸入與自然語言指令端到端統一生成動作序列*',
     ('*圖26-3：具身智慧 Agent 三層架構', '*圖26-4：具身智慧 Agent 三層架構'),
     ('*圖26-2：潔淨室機械臂 EFEM 自動上下料工作流', '*圖26-3：潔淨室機械臂 EFEM 自動上下料工作流')),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\en\chapters\part6\chapter26.md',
     '*Figure 26-1: The "perceive–understand–plan–act" technology stack of embodied AI; the learning-feedback loop continuously improves the planning and execution layers*',
     NL + NL + '![VLA (Vision-Language-Action) model workflow](../../images/flow_ch26_vla_pipeline.png)' + NL + NL +
     '*Figure 26-2: VLA (Vision-Language-Action) model workflow — visual input and natural-language instruction are unified end-to-end into an action sequence*',
     ('*Figure 26-3: Three-layer architecture', '*Figure 26-4: Three-layer architecture'),
     ('*Figure 26-2: Cleanroom robotic-arm EFEM', '*Figure 26-3: Cleanroom robotic-arm EFEM')),
]

for path, tech_anchor, vla_block, (arch_old, arch_new), (efem_old, efem_new) in jobs:
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    assert text.count(tech_anchor) == 1, 'tech anchor not unique: %s' % path
    assert text.count(arch_old) == 1 and text.count(efem_old) == 1, 'caption anchors wrong: %s' % path
    # 先把 26-3(架构) 顺移为 26-4, 再把 26-2(EFEM) 顺移为 26-3, 避免替换串冲突
    text = text.replace(arch_old, arch_new)
    text = text.replace(efem_old, efem_new)
    text = text.replace(tech_anchor, tech_anchor + vla_block)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print('Updated:', path)
print('All done.')
