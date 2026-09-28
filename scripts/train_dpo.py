from __future__ import annotations
import argparse
from datasets import load_dataset
from transformers import AutoTokenizer
from trl import DPOConfig, DPOTrainer

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--dataset',default='datasets/preferences/dpo.jsonl')
    p.add_argument('--out',default='artifacts/dpo')
    args=p.parse_args()
    data=load_dataset('json',data_files=args.dataset,split='train')
    tokenizer=AutoTokenizer.from_pretrained(args.model,use_fast=True)
    if tokenizer.pad_token is None: tokenizer.pad_token=tokenizer.eos_token
    config=DPOConfig(output_dir=args.out,num_train_epochs=1,per_device_train_batch_size=1,gradient_accumulation_steps=8,learning_rate=1e-6,report_to='none')
    trainer=DPOTrainer(model=args.model,args=config,train_dataset=data,processing_class=tokenizer)
    trainer.train()
    trainer.save_model(args.out)

if __name__=='__main__': main()
