from __future__ import annotations
import argparse
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--dataset", default="datasets/processed/sft.jsonl")
    ap.add_argument("--out", default="artifacts/sft")
    ap.add_argument("--epochs", type=float, default=1.0)
    args=ap.parse_args()

    ds=load_dataset("json", data_files=args.dataset, split="train")
    tok=AutoTokenizer.from_pretrained(args.model, use_fast=True)
    model=AutoModelForCausalLM.from_pretrained(args.model, device_map="auto")
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    trainer=SFTTrainer(
        model=model, tokenizer=tok, train_dataset=ds,
        args=TrainingArguments(
            output_dir=args.out, num_train_epochs=args.epochs,
            per_device_train_batch_size=1, gradient_accumulation_steps=8,
            logging_steps=5, save_strategy="steps", save_steps=100,
            learning_rate=2e-5, fp16=False, bf16=False, report_to="none"
        )
    )
    trainer.train()
    trainer.save_model(args.out)

if __name__=="__main__": main()
