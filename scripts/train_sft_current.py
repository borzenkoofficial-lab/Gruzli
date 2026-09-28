from __future__ import annotations
import argparse
from datasets import load_dataset
from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--dataset', default='datasets/processed/sft.jsonl')
    p.add_argument('--out', default='artifacts/sft')
    args = p.parse_args()
    data = load_dataset('json', data_files=args.dataset, split='train')
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    config = SFTConfig(output_dir=args.out, num_train_epochs=1, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-5, report_to='none', max_length=2048)
    trainer = SFTTrainer(model=args.model, args=config, train_dataset=data, processing_class=tokenizer)
    trainer.train()
    trainer.save_model(args.out)

if __name__ == '__main__':
    main()
