# Autonomous learning daemon
from __future__ import annotations
import argparse, asyncio, os
from nexum_core.learning.autonomous import AutonomousLearningEngine

async def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model', default=os.getenv('NEXUM_BASE_MODEL',''))
    p.add_argument('--interval', type=int, default=int(os.getenv('NEXUM_LEARNING_INTERVAL','300')))
    p.add_argument('--min-records', type=int, default=int(os.getenv('NEXUM_MIN_TRAIN_RECORDS','8')))
    p.add_argument('--output', default=os.getenv('NEXUM_TRAIN_OUTPUT','artifacts/sft'))
    a=p.parse_args()
    if not a.model: raise SystemExit('Set NEXUM_BASE_MODEL to a local Hugging Face model path/name.')
    engine=AutonomousLearningEngine('.')
    print('Nexum autonomous learning daemon started.')
    while True:
        cycle=engine.cycle()
        print(f'[learning] trajectories={cycle.total_trajectories} verified={cycle.verified} added={cycle.sft_records}')
        if cycle.accepted >= a.min_records:
            result=await asyncio.to_thread(engine.train_sft,a.model,a.output,a.min_records)
            print(f"[training] ok={result.get('ok')} status={result.get('status')}")
        await asyncio.sleep(a.interval)

if __name__=='__main__': asyncio.run(main())
