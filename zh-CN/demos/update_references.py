# -*- coding: utf-8 -*-
"""向 references.md 追加新增参考文献（学术文献+产业官方资料，[78]-[102]）"""
import io

path = r'H:\code\traework\AI在半导体晶圆厂的应用\references.md'

new_refs = """## 八、良率建模经典文献

[78] Murphy, B. T. (1964). Cost-Size Optima of Monolithic Integrated Circuits. *Proceedings of the IEEE*, 52(12), 1537–1545.

[79] Stapper, C. H. (1973). Defect Density Distribution for LSI Yield Calculations. *IEEE Transactions on Electron Devices*, 20(7), 655–657. DOI: 10.1109/T-ED.1973.17719.

[80] Stapper, C. H. (1989). Fact and Fiction in Yield Modeling. *Microelectronics Journal*, 20(1–2).

[81] Walker, D. M. H., & Director, S. W. (1985). VLASIC: A Yield Simulator for Integrated Circuits. In *Proceedings of the IEEE International Conference on Computer-Aided Design (ICCAD-85)*, 318–320.

[82] Shen, W., Maly, W., & Pileggi, L. T. (1999). DRC-Based Algorithm for Extraction of Critical Areas for Opens in Large VLSI Circuits. *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems*, 18(2), 151–162.

## 九、强化学习与芯片设计自动化（DSO.ai与AlphaChip生态）

[83] Synopsys. (2023, February 7). *AI-Designed Chips Reach Scale with First 100 Commercial Tape-outs Using Synopsys DSO.ai Technology*. Synopsys Newsroom. Available at: https://news.synopsys.com/2023-02-07-AI-designed-Chips-Reach-Scale-with-First-100-Commercial-Tape-outs-Using-Synopsys-Technology

[84] Synopsys. (2021, November 29). *Synopsys Expands Use of AI to Optimize Samsung's Latest Mobile Designs*. Synopsys Newsroom. Available at: https://news.synopsys.com/2021-11-29-Synopsys-Expands-Use-of-AI-to-Optimize-Samsungs-Latest-Mobile-Designs

[85] Mirhoseini, A., & Goldie, A. (2024). *A Critique of Unfounded Skepticism Around AI for Chip Design*. arXiv:2411.10053.

[86] TechCrunch. (2026, January 26). *AI Chip Startup Ricursive Hits $4B Valuation 2 Months After Launch*. Available at: https://techcrunch.com/2026/01/26/ai-chip-startup-ricursive-hits-4b-valuation-two-months-after-launch/

## 十、AI驱动的半导体生产调度（AISSI与Flexciton）

[87] AISSI Project Consortium. (2021–2024). *AISSI – Autonomous Integrated Scheduling for Semiconductor Industry* (Eureka/ITEA4 Project 20212). Available at: https://itea4.org/project/aissi.html

[88] Stöckermann, P., et al. (2025). Scalability of Reinforcement Learning Methods for Semiconductor Manufacturing Scheduling Problems. arXiv:2505.11135.

[89] Konstantelos, I., Wiebe, J., Moss, R., Steele, S., Xenos, D., O'Donnell, T., & Feely, S. (2022). Fab-Wide Scheduling of Semiconductor Plants: A Large-Scale Industrial Deployment Case Study. In *Proceedings of the Winter Simulation Conference (WSC 2022)*, 3297–3308. DOI: 10.1109/WSC57314.2022.10015364.

[90] Flexciton. (2023). *Realising AI's Potential in Semiconductor Manufacturing* (SEMI White Paper). Available at: https://flexciton.com/resources/semi-white-paper-realising-ais-potential-in-semiconductor-manufacturing

## 十一、虚拟量测与工艺控制产业实践

[91] Gauss Labs. *Panoptes Virtual Metrology*. Gauss Labs. Available at: https://www.gausslabs.ai/vm

[92] SK hynix. (2023, January 16). *SK hynix Deploys Gauss Labs's AI-Based Virtual Metrology Solution*. SK hynix Newsroom. Available at: https://news.skhynix.com/en/gauss-labss-ai-based-virtual-metrology-solution/

## 十二、Ontology工业平台官方文档

[93] Palantir Technologies. *Foundry Ontology: Overview*. Palantir Documentation. Available at: https://www.palantir.com/docs/foundry/ontology/overview/

[94] Palantir Technologies & NVIDIA. (2026, March 12). *Palantir and NVIDIA Team to Deliver Sovereign AI Operating System Reference Architecture*. Palantir Investor Relations. Available at: https://investors.palantir.com/news-details/2026/Palantir-and-NVIDIA-Team-to-Deliver-Sovereign-AI-Operating-System-Reference-Architecture/

## 十三、光刻与制造设备的AI应用

[95] ASML & Mistral AI. (2025, September 9). *ASML and Mistral AI Enter Strategic Partnership*. ASML Press Release. Available at: https://www.asml.com/en/news/press-releases/2025/asml-mistral-ai-enter-strategic-partnership

[96] ASML. (2026). *The Machines Behind the Machines*. ASML Stories. Available at: https://www.asml.com/en/company/stories/2026/machines-behind-machines

## 十四、神经符号AI与约束学习

[97] Diligenti, M., Gori, M., & Saccà, C. (2017). Semantic-Based Regularization for Learning and Inference. *Artificial Intelligence*, 244, 143–165. DOI: 10.1016/j.artint.2015.08.011.

[98] Zheng, X., et al. (2021). A Survey on Neural-Symbolic Learning Systems. arXiv:2111.08164.

## 十五、具身智能与机器人学

[99] Driess, D., Xia, F., Sajjadi, M. S. M., et al. (2023). PaLM-E: An Embodied Multimodal Language Model. In *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. arXiv:2303.03378.

[100] The Open X-Embodiment Collaboration. (2024). Open X-Embodiment: Robotic Learning Datasets and RT-X Models. In *2024 IEEE International Conference on Robotics and Automation (ICRA)*. arXiv:2310.08864.

## 十六、离线强化学习与序列决策

[101] Kumar, A., Zhou, A., Tucker, G., & Levine, S. (2020). Conservative Q-Learning for Offline Reinforcement Learning. In *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. arXiv:2006.04779.

[102] Chen, L., Lu, K., Rajeswaran, A., Lee, K., Grover, A., Laskin, M., Abbeel, P., Srinivas, A., & Mordatch, I. (2021). Decision Transformer: Reinforcement Learning via Sequence Modeling. In *Advances in Neural Information Processing Systems 34 (NeurIPS 2021)*. arXiv:2106.01345.

"""

with io.open(path, 'r', encoding='utf-8', ) as f:
    text = f.read()

anchor = '\n---\n\n**说明：**'
assert anchor in text, 'anchor not found'
text = text.replace(anchor, '\n' + new_refs.replace('\n', '\n') + '\n---\n\n**说明：**')

old_note = """本参考文献按照学术规范组织，涵盖本书涉及的以下领域：

1. **AI基础与三大学派**（符号主义、连接主义、行为主义的经典文献与教科书）
2. **AI融合方向**（NB神经符号、NA神经行为、SA符号行为、NSA全融合与具身智能）
3. **AI在半导体晶圆厂的应用**（缺陷检测、虚拟量测、智能调度、预测性维护、R2R控制、良率分析、数字孪生）
4. **芯片设计与RL**（AlphaChip等）
5. **半导体制造AI综述**
6. **Ontology与工业AI**
7. **认知科学与AI哲学**

所有文献均经过学术数据库（IEEE Xplore、Nature、NeurIPS/ICML/ICLR会议录、ACM Digital Library、Google Scholar等）验证。"""

new_note = """本参考文献按照学术规范组织，涵盖本书涉及的以下领域：

1. **AI基础与三大学派**（符号主义、连接主义、行为主义的经典文献与教科书）
2. **AI融合方向**（NB神经符号、NA神经行为、SA符号行为、NSA全融合与具身智能）
3. **AI在半导体晶圆厂的应用**（缺陷检测、虚拟量测、智能调度、预测性维护、R2R控制、良率分析、数字孪生）
4. **芯片设计与RL**（AlphaChip、DSO.ai商业部署、Ricursive Intelligence）
5. **半导体制造AI综述**
6. **Ontology与工业AI**（含Palantir Foundry官方文档与主权AI架构）
7. **认知科学与AI哲学**
8. **良率建模经典文献**（Murphy、Stapper、Walker与Maly等奠基性研究）
9. **AI驱动的半导体生产调度**（AISSI项目、Flexciton全厂调度部署）
10. **虚拟量测产业实践**（Gauss Labs Panoptes VM与SK hynix部署）
11. **光刻与制造设备的AI应用**（ASML与Mistral AI合作）
12. **神经符号AI与约束学习、具身智能机器人学、离线强化学习**

学术文献均经过学术数据库（IEEE Xplore、Nature、NeurIPS/ICML/ICLR会议录、ACM Digital Library、Google Scholar、arXiv、dblp等）验证；产业资料来源于相关公司官方网站与新闻稿。"""

assert old_note in text, 'note not found'
text = text.replace(old_note, new_note)

with io.open(path, 'w', encoding='utf-8', ) as f:
    f.write(text)
print('references.md updated.')
