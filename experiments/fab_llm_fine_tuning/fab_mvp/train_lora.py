"""
LoRA 微调 Qwen2-0.5B (一个模型支持三种模式)
============================================================
策略:
  - 一条原始样本拆成3条训练对话 (mode_a / mode_b / mode_c)
  - 用明确的指令前缀区分模式, 推理时用相同前缀即可切换模式
  - LoRA 微调 (r=16), CPU 可跑 (0.5B+LoRA), 有GPU自动用GPU
  - 保存 adapter 到 outputs/lora_adapter/

数据格式 (Qwen2 ChatML):
  system: 你是晶圆厂领域查询预处理助手...
  user:   [领域感知增强] ... 问题: {user_query}
  assistant: {mode_a JSON}
"""
import os
import json
import torch
import argparse
from datasets import Dataset
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

load_dotenv()

BASE_MODEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Qwen2-0.5B")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs", "lora_adapter")

# ResNet Step 1: 三种模式的指令模板 (训练/推理共用, 保证格式一致)
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


# ResNet Step 2: 把 jsonl 转成训练对话 (每条原始样本 -> 3条对话)
def build_training_dataset(jsonl_path: str):
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            s = json.loads(line)
            q = s["user_query"]
            # mode_a: 直接用原始JSON字符串作为target (紧凑无缩进, 贴近推理输出)
            target_a = json.dumps(s["mode_a_enhance"], ensure_ascii=False)
            target_b = json.dumps({"translated": s["mode_b_translate"]}, ensure_ascii=False)
            target_c = json.dumps(s["mode_c_route"], ensure_ascii=False)
            for mode, target in [("mode_a", target_a), ("mode_b", target_b), ("mode_c", target_c)]:
                # 用 replace 而非 format: MODE_PROMPTS 含 JSON 的花括号, format 会误解析
                user_msg = MODE_PROMPTS[mode].replace("{q}", q)
                rows.append({"messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": target},
                ]})
    return Dataset.from_list(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--smoke", action="store_true", help="smoke测试: 仅用少量数据快速验证pipeline")
    ap.add_argument("--limit", type=int, default=0, help="限制原始样本数(0=不限制), 每条拆3模式")
    args = ap.parse_args()

    train_path = os.path.join(DATA_DIR, "train.jsonl")
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"训练数据不存在: {train_path}, 请先运行 data_generation.py")

    print("=== 加载训练数据 ===")
    ds = build_training_dataset(train_path)
    if args.smoke:
        ds = ds.select(range(min(9, len(ds))))  # smoke: 3条样本*3模式=9条
    elif args.limit and args.limit > 0:
        n = min(args.limit * 3, len(ds))
        ds = ds.select(range(n))
        print(f"[--limit] 限制原始样本数={args.limit}, 拆3模式后训练样本={n}")
    print(f"训练样本数: {len(ds)} (每条原始样本拆3模式)")
    print("示例对话:")
    print(ds[0]["messages"])

    print("\n=== 加载基座模型 ===")
    has_cuda = torch.cuda.is_available()
    dtype = torch.bfloat16 if has_cuda else torch.float32
    print(f"设备: {'CUDA' if has_cuda else 'CPU'}, dtype: {dtype}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=dtype)
    model.config.use_cache = False

    # ResNet Step 3: LoRA 配置
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    # ResNet Step 4: 训练配置
    cfg = SFTConfig(
        output_dir=OUTPUT_DIR,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="epoch",
        save_total_limit=1,
        report_to="none",
        bf16=has_cuda,
        max_length=1024,       # trl 1.x 用 max_length (旧版为 max_seq_length)
        packing=False,         # 指令微调: 每样本独立, 不拼接避免指令边界混淆
        dataset_num_proc=1,
    )

    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=ds,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    print("\n=== 开始微调 ===")
    trainer.train()

    # ResNet Step 5: 保存 adapter
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\n微调完成, adapter 已保存到: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
