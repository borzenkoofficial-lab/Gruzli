from __future__ import annotations
import argparse
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

def reward_func(completions, **kwargs):
    rewards=[]
    for completion in completions:
        text=str(completion).lower()
        rewards.append(1.0 if 'verified' in text or 'success' in text else 0.0)
    return rewards

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--dataset',default='datasets/grpo/tasks.jsonl')
    p.add_argument('--out',default='artifacts/grpo')
    args=p.parse_args()
    data=load_dataset('json',data_files=args.dataset,split='train')
    config=GRPOConfig(output_dir=args.out,num_train_epochs=1,per_device_train_batch_size=1,gradient_accumulation_steps=4,learning_rate=1e-6,report_to='none')
    trainer=GRPOTrainer(model=args.model,args=config,train_dataset=data,reward_funcs=reward_func)
    trainer.train()
    trainer.save_model(args.out)

if __name__=='__main__': main()
