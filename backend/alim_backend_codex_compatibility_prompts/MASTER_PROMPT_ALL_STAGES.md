# Master Codex Prompt — Execute the Python Backend → Lovable Compatibility Migration

Use this only if you want Codex to execute the whole migration in a controlled sequence. Prefer the individual prompts for reviewability.

Read `00_README_EXECUTION_ORDER.md` and then execute prompts 01 through 15 in order. Treat each prompt as a separate checkpoint. After each checkpoint:

1. run the requested focused tests;
2. report files changed and test results;
3. do not proceed if a regression breaks an architectural invariant;
4. keep changes modular and reviewable;
5. preserve the existing Streamlit app until the final compatibility audit;
6. do not touch the Lovable frontend code from this backend task.

The binding integration target is the Lovable frontend contract documented in its handoff pack. When backend implementation and old Python docs conflict, preserve intentional Python safety invariants while adapting the public API to the Lovable contract. Never silently weaken user isolation, hidden-solution policy, source grounding, or secret handling just to make a JSON example pass.
