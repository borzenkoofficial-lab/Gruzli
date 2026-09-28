# Nexum AI Core

Private foundation repository for the Nexum AI model and agentic intelligence stack.

## Mission

Build an independent AI foundation focused on:

- reasoning
- software engineering
- architecture
- UI/UX and design
- vision
- research and source verification
- tool use
- autonomous agents
- memory
- evaluation and self-correction
- multimodal capabilities
- model training and fine-tuning

## Repository boundary

This repository is intentionally separate from `nexum-dev`.

`nexum-dev` is the product/builder layer.

This repository is the AI Core / model layer that can later expose APIs to Nexum.dev and other products.

## Development strategy

1. Establish reproducible AI Core infrastructure.
2. Use open-weight models during the bootstrap phase.
3. Build a high-quality proprietary training-data pipeline.
4. Train and evaluate specialized Nexum models.
5. Gradually reduce dependency on external model providers.
6. Develop a proprietary multimodal foundation model as compute and data allow.

## Initial architecture

```
Nexum AI Core
├── model
├── inference
├── reasoning
├── agents
├── tools
├── memory
├── vision
├── design
├── data generation
├── training
├── evaluation
├── serving
├── security
├── experiments
└── docs
```

## Training principle

The core training unit is not only prompt → answer.

We collect verified trajectories:

task → plan → tool actions → implementation → execution → error → correction → tests → verified result

Successful and failed trajectories are both valuable training/evaluation data.

## Status

Bootstrap repository initialized.

Next milestones:

- repository foundation
- reproducible runtime
- model abstraction
- agent orchestration
- dataset schema
- evaluation harness
- first local training experiment
- SFT/LoRA pipeline
- tool-use training
- multimodal pipeline
