# 🔬 LLM RAG 工艺文档问答 (LLM RAG for Process-Spec QA)

**中文简介** | 本实验对应《AI在半导体晶圆厂的应用》**第22章(大语言模型在晶圆厂的应用)**。实现一个精简的 RAG(检索增强生成)系统:从工艺规范(SPEC)文档库中检索相关内容,再交给 LLM 生成带引用的回答。默认使用 DeepSeek API;未配置 API Key 时自动降级为 Mock LLM,便于离线运行。

**English Intro** | This experiment corresponds to **Chapter 22 (LLMs in Wafer Fabs)**. It implements a minimal RAG (Retrieval-Augmented Generation) system: retrieve relevant snippets from a process-spec (SPEC) document library, then let an LLM generate a cited answer. It uses the DeepSeek API by default, and automatically falls back to a Mock LLM when no API key is configured — so it runs offline too.

---

## 🎯 目标 / Objectives

| 中文 | English |
|------|---------|
| 构建小型工艺文档库(SPEC片段) | Build a small SPEC snippet library |
| 实现关键词检索(简化BM25) + 重排 | Implement keyword retrieval (mini-BM25) + reranking |
| 调用 LLM 生成带引用来源的回答 | Call an LLM to generate answers with source citations |
| 支持 Mock 模式离线运行 | Support offline Mock mode |

## 🚀 快速开始 / Quick Start

```bash
pip install requests
# 可选: 配置 DeepSeek API Key (不配置则用 Mock LLM)
echo "DEEPSEEK_API_KEY=你的key" > .env
python llm_rag_spec_qa.py
```

交互示例 / Example interaction:

```
问: 刻蚀机的腔体压力规格是多少?
答: 根据文档 SPEC-E-103, 刻蚀腔体压力规格为 2.0-6.0 mTorr [来源: SPEC-E-103]
```

## 📁 文件结构 / Files

```
llm_rag_spec_qa/
├── llm_rag_spec_qa.py      # 主程序 Main script
├── requirements.txt
├── .env.example            # API Key 模板 (template)
├── README.md
```

## 🧠 原理速览 / Theory at a Glance

1. **RAG 流程 / RAG pipeline**: `检索 Retrieval → 增强 Augmentation → 生成 Generation`
2. **检索 / Retrieval**: 关键词加权(BM25 简化),返回 Top-K 文档片段
3. **生成 / Generation**: 把检索片段拼进 Prompt,LLM 基于"上下文 + 问题"回答,并要求标注来源
4. **防幻觉 / Anti-hallucination**: 文档库无相关内容时,LLM 应回答"文档库中未找到相关信息"

## 📊 预期输出 / Expected Output

- 交互式问答(可逐条提问)
- 每个回答附带来源文档引用
- 控制台显示检索命中的文档片段
