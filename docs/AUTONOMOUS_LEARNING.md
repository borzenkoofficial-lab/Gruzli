# Nexum autonomous learning

Nexum records verified agent trajectories and converts them into filtered SFT/DPO datasets. Training is gated by a minimum verified-record threshold.

Run: `python scripts/autonomous_learning.py --model /path/to/local/model`

Continuous mode: `python scripts/autonomous_learning.py --model /path/to/local/model --interval 300`

The daemon never treats an unverified trajectory as training truth. A trained checkpoint is a candidate and should be promoted only after evaluation passes.

API: GET `/learning/status`, POST `/learning/cycle`, POST `/learning/train`.

This is continual-learning infrastructure; it is not proof of human-like consciousness or cognition.
