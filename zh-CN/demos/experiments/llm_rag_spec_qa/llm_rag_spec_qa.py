"""
🔬 LLM RAG 工艺文档问答 / LLM RAG for Process-Spec QA
对应第22章(LLM在晶圆厂的应用)
Corresponds to Chapter 22 (LLMs in Wafer Fabs)

RAG 流程 / Pipeline: 检索 Retrieval -> 增强 Augmentation -> 生成 Generation
默认使用 DeepSeek API; 未配置 Key 时降级为 Mock LLM(离线可运行)
Uses DeepSeek API by default; falls back to a Mock LLM without a key (offline-ready).
"""
import os
import re
import json
import urllib.request

# ---------- 1. 文档库 / Document library (SPEC snippets) ----------
DOCS = [
    {"id": "SPEC-E-103", "title": "刻蚀工艺腔体压力规格 / Etch Chamber Pressure Spec",
     "content": "刻蚀腔体压力规格为 2.0-6.0 mTorr。压力超出窗口会导致侧壁角度偏差与关键尺寸(CD)漂移。"
                "Etch chamber pressure spec is 2.0-6.0 mTorr. Out-of-window pressure causes sidewall angle "
                "deviation and critical dimension (CD) drift."},
    {"id": "SPEC-D-201", "title": "CMP 抛光碟形凹陷控制 / CMP Dishing Control",
     "content": "CMP 后宽金属区域碟形凹陷(Dishing)须小于 5 nm。超标时需调整抛光时间与研磨液流量。"
                "CMP dishing on wide metal regions must be below 5 nm. Otherwise adjust polish time and slurry flow."},
    {"id": "SPEC-L-305", "title": "光刻聚焦-曝光窗口 / Litho FEM Window",
     "content": "光刻聚焦-曝光矩阵(FEM)窗口:聚焦 ±0.15 um, 剂量 ±5%。窗口内 CD 变化须小于 1 nm。"
                "Litho FEM window: focus ±0.15 um, dose ±5%. CD variation within window must stay below 1 nm."},
    {"id": "SPEC-T-112", "title": "炉管温度均匀性 / Furnace Temperature Uniformity",
     "content": "炉管工艺温度均匀性须在 ±0.5°C 以内, 升温速率不超过 10°C/min。"
                "Furnace temperature uniformity must be within ±0.5°C, ramp rate no more than 10°C/min."},
    {"id": "SPEC-Q-050", "title": "虚拟量测免检准则 / VM Skip-Inspection Rule",
     "content": "当虚拟量测预测置信度高于 95% 且误差小于 3 nm 时, 该批次可免检。"
                "A lot may skip inspection when VM prediction confidence > 95% and error < 3 nm."},
    {"id": "SPEC-M-601", "title": "机台匹配标准 / Tool Matching Standard",
     "content": "同型机台间 CD 差异须小于 1 nm, 膜厚差异小于 0.5%。"
                "CD difference among identical tools must be below 1 nm, film thickness below 0.5%."},
]

# ---------- 2. 检索: 简化 BM25 / Retrieval: mini-BM25 ----------
def tokenize(text):
    """中英文分词: 中文按字bigram, 英文按词 / tokenize: CN bigrams + EN words"""
    tokens = re.findall(r'[a-z0-9]+', text.lower())
    for ch in re.findall(r'[\u4e00-\u9fff]', text):
        tokens.append(ch)
    # 中文相邻字组合成双字词 / bigrams of adjacent Chinese chars
    cjk = re.findall(r'[\u4e00-\u9fff]', text)
    tokens += [cjk[i] + cjk[i+1] for i in range(len(cjk)-1)]
    return tokens

def mini_bm25(query, doc, k1=1.2, b=0.75):
    """简化 BM25 评分 / simplified BM25 score (单文档版本)"""
    q_tokens = set(tokenize(query))
    d_tokens = tokenize(doc)
    if not d_tokens:
        return 0.0
    dl = len(d_tokens)
    avgdl = dl  # 单文档场景简化为自身长度 / single-doc simplification
    score = 0.0
    for t in q_tokens:
        tf = d_tokens.count(t)
        if tf == 0:
            continue
        idf = 1.0  # 单文档下 IDF 无区分度 / IDF degenerates for single doc
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1)))
    return score

def retrieve(query, top_k=2):
    """检索 Top-K 文档 / retrieve top-K documents"""
    scored = [(mini_bm25(query, d['title'] + d['content']), d) for d in DOCS]
    scored.sort(key=lambda x: -x[0])
    hits = [d for s, d in scored if s > 0][:top_k]
    return hits

# ---------- 3. LLM 调用: DeepSeek / LLM call: DeepSeek ----------
def get_api_key():
    """从环境变量读取 API Key / read API key from env (never hardcode)"""
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    """调用 DeepSeek Chat API / call DeepSeek Chat API"""
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.3,
        "max_tokens": 400,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

def mock_llm(system, user):
    """Mock LLM: 直接从命中文档中抽取关键词句 / extract key sentences from hits"""
    # 提取用户问题中的关键词, 找包含关键词的文档句子
    hits = retrieve(user, top_k=1)
    if not hits:
        return "文档库中未找到相关信息 (Mock LLM)。/ No relevant info found in the doc library (Mock LLM)."
    doc = hits[0]
    kw = set(tokenize(user))
    best_sent = doc['content'].split('。')
    picked = best_sent[0]
    for sent in best_sent:
        if kw & set(tokenize(sent)):
            picked = sent
            break
    return f"根据文档《{doc['title']}》: {picked} [来源: {doc['id']}] (Mock LLM)"

# ---------- 4. RAG 问答主流程 / Main RAG QA loop ----------
SYSTEM = (
    "你是晶圆厂工艺工程师助手。只能根据提供的文档片段回答;若文档中没有相关信息,"
    "请明确回答'文档库中未找到相关信息'。回答需标注来源文档ID。"
    "You are a fab process engineer assistant. Answer ONLY from the provided document snippets; "
    "if the docs do not contain the answer, say 'not found in the doc library'. Cite source doc IDs."
)

def ask(question):
    hits = retrieve(question)
    if not hits:
        print("  (检索无命中 / no retrieval hits)")
        context = "无相关文档。/ No relevant documents."
    else:
        context = "\n".join(f"[{d['id']}] {d['title']}: {d['content']}" for d in hits)
        print(f"  (命中 / hits: {[d['id'] for d in hits]})")
    user_prompt = f"文档片段 / Document snippets:\n{context}\n\n问题 / Question: {question}"
    if get_api_key():
        try:
            return call_deepseek(SYSTEM, user_prompt)
        except Exception as e:
            print(f"  (API调用失败,降级Mock / API failed, fallback to Mock: {e})")
            return mock_llm(SYSTEM, user_prompt)
    return mock_llm(SYSTEM, user_prompt)

def main():
    print('=' * 60)
    print('LLM RAG 工艺文档问答 / Process-Spec QA')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    print('文档库 / Doc library:', ', '.join(d['id'] for d in DOCS))
    print('=' * 60)
    examples = [
        "刻蚀机的腔体压力规格是多少? / What is the etch chamber pressure spec?",
        "CMP 碟形凹陷的标准是什么? / What is the CMP dishing standard?",
        "什么情况下批次可以免检? / When can a lot skip inspection?",
    ]
    for q in examples:
        print(f"\n问 / Q: {q}")
        print(f"答 / A: {ask(q)}")
    print('\n可输入自定义问题, 输入 q 退出 / type your own questions, q to quit.')
    while True:
        q = input('\n问题 / Question: ').strip()
        if q.lower() in ('q', 'quit', 'exit'):
            break
        if q:
            print(f"答 / A: {ask(q)}")

if __name__ == '__main__':
    main()
