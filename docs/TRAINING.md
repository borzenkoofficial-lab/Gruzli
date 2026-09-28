# Training Strategy

## Bootstrap

Use strong open-weight or external teacher models only as temporary bootstrap infrastructure. Keep the provider layer replaceable.

## Training unit

Prefer verified trajectories:

task -> plan -> tool calls -> implementation -> execution -> failure -> correction -> tests -> verified result

## Stages

- cleaning and deduplication
- supervised fine-tuning
- structured tool-use training
- preference optimization
- verifier/reward modeling
- agent trajectory training
- multimodal training
- continual evaluation

## Quality gate

Only independently verifiable successful trajectories enter the positive training set. Failures are retained separately for negative examples and debugging research.

## Scaling

Start small. Scale parameter count and GPU count only after the data/evaluation loop shows reproducible gains.
