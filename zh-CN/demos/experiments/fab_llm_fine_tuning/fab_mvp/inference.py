"""
微调后小模型推理 (三种模式)
============================================================
- 懒加载: 仅在首次调用时加载模型, 避免import时卡顿
- 三种模式: mode_a 领域感知增强 / mode_b 术语翻译 / mode_c SQL模板路由
- 与训练格式严格一致 (共用 SYSTEM_PROMPT / MODE_PROMPTS)
- robust JSON 解析 (兼容小模型偶尔输出markdown/多余文字)
"""
import os
import json
import re
import torch
from functools import lru_cache
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Qwen2-0.5B")
ADAPTER_PATH = os.path.join(os.path.dirname(__file__), "outputs", "lora_adapter")

# 共用训练时的 prompt (保持格式一致, 这是微调生效的关键)
SYSTEM_PROMPT = (
    "你是晶圆厂(半导体制造)领域查询预处理助手。根据指定模式, 对工程师的口语提问进行预处理, "
    "输出严格JSON(不要输出JSON以外的内容, 不要用markdown代码块包裹)。"
)
MODE_PROMPTS = {
    "mode_a": (
        "[领域感知增强] 请对以下晶圆厂工程师提问进行领域感知增强, "
        "输出JSON: {\"intent\":..., \"entities\":{...}, \"domain_hints\":..., \"enhanced_query\":...}\n"
        "问题: {q}"
    ),
    "mode_b": (
        "[术语翻译] 请把以下晶圆厂工程师的口语提问翻译为含专业术语与表名的专业表述, "
        "输出JSON: {\"translated\":...}\n"
        "问题: {q}"
    ),
    "mode_c": (
        "[SQL模板路由] 请为以下晶圆厂工程师提问匹配最合适的SQL模板, "
        "输出JSON: {\"template_id\":..., \"reason\":..., \"params\":{...}}\n"
        "问题: {q}"
    ),
}

# 模式中文别名 (UI 展示用)
MODE_LABELS = {
    "mode_a": "领域感知增强",
    "mode_b": "术语翻译",
    "mode_c": "SQL模板路由",
}


def extract_json(text: str):
    """robust JSON 提取: 去掉markdown代码块, 取第一个完整JSON对象"""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_model():
    """懒加载基座+LoRA adapter (单例)"""
    from peft import PeftModel

    has_cuda = torch.cuda.is_available()
    dtype = torch.bfloat16 if has_cuda else torch.float32
    print(f"[小模型加载] 设备={'CUDA' if has_cuda else 'CPU'}, dtype={dtype}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=dtype)
    if os.path.exists(ADAPTER_PATH):
        model = PeftModel.from_pretrained(base, ADAPTER_PATH)
        print(f"[小模型加载] 已加载 LoRA adapter: {ADAPTER_PATH}")
    else:
        model = base
        print(f"[小模型加载] adapter 不存在, 使用基座模型(未微调): {ADAPTER_PATH}")
    model.eval()
    return tokenizer, model


class SmallModelPredictor:
    """微调后小模型预测器"""

    def __init__(self):
        self.tokenizer, self.model = _load_model()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    @torch.no_grad()
    def predict_raw(self, query: str, mode: str, max_new_tokens: int = 200) -> str:
        """原始生成文本"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": MODE_PROMPTS[mode].replace("{q}", query)},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,        # 贪心, 输出稳定可复现
            repetition_penalty=1.3, # 抑制重复循环 (训练不足时尤需)
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        gen = out[0][inputs["input_ids"].shape[1]:]   # 去掉prompt部分
        return self.tokenizer.decode(gen, skip_special_tokens=True).strip()

    def predict(self, query: str, mode: str) -> dict:
        """返回解析后的dict; 解析失败时回退到 {raw: ...}"""
        raw = self.predict_raw(query, mode)
        parsed = extract_json(raw)
        if parsed is None:
            return {"raw": raw, "_parse_error": True}
        return parsed


@lru_cache(maxsize=1)
def get_predictor() -> SmallModelPredictor:
    """单例获取预测器 (UI/Agent共用)"""
    return SmallModelPredictor()


if __name__ == "__main__":
    # 自检: 用一个测试问题跑三种模式
    p = get_predictor()
    q = "昨天3号机良率掉的厉害咋回事"
    for mode in ["mode_a", "mode_b", "mode_c"]:
        print(f"\n=== {MODE_LABELS[mode]} ===")
        print(json.dumps(p.predict(q, mode), ensure_ascii=False, indent=2))
