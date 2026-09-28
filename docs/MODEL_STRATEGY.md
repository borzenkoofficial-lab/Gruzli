# Nexum Model Strategy

Nexum is developed as a system, not a single checkpoint.

1. Base open-weight model.
2. Structured reasoning and tool protocol.
3. Planner, executor and verifier.
4. Verified trajectory factory.
5. SFT.
6. DPO preference optimization.
7. GRPO/RLOO where measurable rewards exist.
8. Distillation from stronger teachers.
9. Domain and multimodal specialists.
10. Continuous benchmark gating.

Promote a model only when benchmarks improve without unacceptable regressions.
Store structured actions, observations and verification rather than exposing private chain-of-thought.

## Engineering status

The runtime is being hardened around verified tool execution, structured trajectories, and reproducible post-training. Training is gated by evaluation rather than by model size alone.
