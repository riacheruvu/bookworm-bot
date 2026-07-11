# Environments (future)

This package is intentionally almost empty in v0.

## Planned hooks

1. **`EnvSpec`** — declarative, parametric task (friction μ, mass, incline, …)
2. **`generate_env_for_gaps(skill_ids)`** — map diagnosed gaps → env specs
3. **`run_episode(policy, env)`** — score embodied / sim practice
4. **`reachy_mini/`** — camera page capture + simple desk demos

Keep env generation *template-based* first (safe, gradable). Free-form world invention can come later.
