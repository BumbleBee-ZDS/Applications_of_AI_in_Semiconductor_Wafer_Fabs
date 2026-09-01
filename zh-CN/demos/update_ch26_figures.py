# -*- coding: utf-8 -*-
"""为三语第26章插入新增流程图引用(图26-1/26-2)并重新编号旧图(26-1→26-3, 26-2→26-5)"""
import io

NL = '\r\n'

jobs = [
    # (文件, 锚点1, 图块1, 锚点2, 图块2, 旧图注1, 旧图注2)
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\chapters\part6\chapter26.md',
     'VLA 让机器人的操作从"为每个任务编写程序"走向"用自然语言指挥通用操作"。',
     NL + NL + '![具身智能技术栈](../../images/flow_ch26_tech_stack.png)' + NL + NL +
     '*图26-1：具身智能"感知-理解-规划-执行"技术栈，学习反馈闭环持续改进规划与执行层*',
     '- **异常识别**：发现晶圆破损、位置偏移时立即停止并报警',
     NL + NL + '![洁净室机械臂EFEM自动上下料工作流](../../images/flow_ch26_efem_workflow.png)' + NL + NL +
     '*图26-2：洁净室机械臂 EFEM 自动上下料工作流——视觉引导抓取 × Ontology 规则校验 × 异常即停*',
     ('*图26-1：具身智能 Agent 三层架构', '*图26-3：具身智能 Agent 三层架构'),
     ('*图26-2：晶圆厂具身智能应用场景', '*图26-5：晶圆厂具身智能应用场景')),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-TW\chapters\part6\chapter26.md',
     'VLA 讓機器人的操作從「為每個任務編寫程式」走向「用自然語言指揮通用操作」。',
     NL + NL + '![具身智慧技術堆疊](../../images/flow_ch26_tech_stack.png)' + NL + NL +
     '*圖26-1：具身智慧「感知-理解-規劃-執行」技術堆疊，學習回饋閉環持續改進規劃與執行層*',
     '- **異常辨識**：發現晶圓破損、位置偏移時立即停止並報警',
     NL + NL + '![潔淨室機械臂EFEM自動上下料工作流](../../images/flow_ch26_efem_workflow.png)' + NL + NL +
     '*圖26-2：潔淨室機械臂 EFEM 自動上下料工作流——視覺引導抓取 × Ontology 規則校驗 × 異常即停*',
     ('*圖26-1：具身智慧 Agent 三層架構', '*圖26-3：具身智慧 Agent 三層架構'),
     ('*圖26-2：晶圓廠具身智慧應用場景', '*圖26-5：晶圓廠具身智慧應用場景')),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\en\chapters\part6\chapter26.md',
     'toward "commanding general operations in natural language."',
     NL + NL + '![Embodied AI technology stack](../../images/flow_ch26_tech_stack.png)' + NL + NL +
     '*Figure 26-1: The "perceive–understand–plan–act" technology stack of embodied AI; the learning-feedback loop continuously improves the planning and execution layers*',
     '- **Anomaly recognition**: immediately stopping and alerting on broken wafers or position drift',
     NL + NL + '![Cleanroom robotic-arm EFEM auto load/unload workflow](../../images/flow_ch26_efem_workflow.png)' + NL + NL +
     '*Figure 26-2: Cleanroom robotic-arm EFEM auto load/unload workflow — vision-guided gripping × Ontology rule verification × stop-on-anomaly*',
     ('*Figure 26-1: Three-layer architecture', '*Figure 26-3: Three-layer architecture'),
     ('*Figure 26-2: Embodied AI application scenarios', '*Figure 26-5: Embodied AI application scenarios')),
]

for path, a1, b1, a2, b2, (o1, n1), (o2, n2) in jobs:
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    for anchor, block in ((a1, b1), (a2, b2)):
        assert text.count(anchor) == 1, 'anchor not unique: %s in %s' % (anchor[:30], path)
    assert text.count(o1) == 1 and text.count(o2) == 1, 'old caption count wrong: %s' % path
    # 先重编号旧图注, 再插入新图块(新图块用26-1/26-2编号)
    text = text.replace(o1, n1).replace(o2, n2)
    text = text.replace(a1, a1 + b1).replace(a2, a2 + b2)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print('Updated:', path)
print('All done.')
