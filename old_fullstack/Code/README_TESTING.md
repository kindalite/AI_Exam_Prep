# Testing

Run from `Code/` with the target conda environment:

```bash
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/verify_environment.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/system_smoke_gemma3.py
conda run -p ~/anaconda3/envs/alim_study_assistant pytest
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_user_isolated_rag_and_practice_flow.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_timed_quiz_exam_flow.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant pytest tests/features/test_token_budget_context_packing.py -v
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/smoke_test.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/system_smoke_user_accounts.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_pipeline.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_multimodal_adaptive_pipeline.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_full_system_no_external.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_user_isolated_rag.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_timed_quiz_exam.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_token_budget_128k.py
conda run -p ~/anaconda3/envs/alim_study_assistant python scripts/dry_run_full_student_system.py
conda run -p ~/anaconda3/envs/alim_study_assistant python -m py_compile app.py src/*.py
```

`system_smoke_gemma3.py` intentionally fails if Ollama or `gemma3:4b` is missing. Unit and feature tests mock external tools.
