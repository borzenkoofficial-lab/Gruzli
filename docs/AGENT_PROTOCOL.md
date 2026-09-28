# Agent Protocol

Every autonomous run has four logical phases: Plan, Act, Observe, Verify.

Only registered tools may be invoked. Tool and model results are recorded in the execution trace. A run is not considered verified merely because the model says it is complete.

The next protocol extension is structured model-emitted tool calls with explicit schemas.
