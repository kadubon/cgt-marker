# Limitations

`cgt-marker` is deliberately narrow.

- It is not a truth oracle. A marker means configured detectors found a conflict; it
  does not decide which claim is true.
- It is not a theorem prover, paraconsistent logic engine, or belief-revision
  system.
- It does not extract claims from natural language. Callers must supply structured
  `Claim` objects.
- It does not automatically resolve, delete, or merge contradictory claims.
- It does not enforce global consistency.
- Temporal detection expects normalized ISO date or datetime strings.
- Numeric interval detection supports a small predicate set: `lt`, `lte`, `gt`,
  `gte`, and `equals`.
- JSONL storage is a simple append/replay log. It is not a concurrent database and
  does not provide transactions.
- Framework adapters are optional helpers, not core dependencies.
- Reserved policy modes are future work and raise on conflict finalization.
- The Ollama experiment is a lightweight proxy evaluation under fixed scenarios and
  string-matching metrics. It is not a strong proof of general effectiveness, agent
  reliability, or scientific validity across models and tasks.
- Raw experiment JSONL includes prompts and model responses and is kept under
  `experiments/results/`, which is ignored by the repository. Public sharing should
  use compact reports generated under `experiments/reports/`.

These limits are part of the MVP design. The library is intended to be a small state
layer that remains easy to inspect and port.
