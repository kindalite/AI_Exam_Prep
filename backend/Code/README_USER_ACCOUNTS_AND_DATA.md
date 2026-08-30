# User Accounts And Data

The app uses local-only accounts. There is no cloud authentication.

Storage layout:

```text
data/users/<user_id>/
  profile.json
  subjects/<subject_key>/notes
  subjects/<subject_key>/syllabus
  subjects/<subject_key>/criteria
  chat_history/messages.jsonl
  chat_media/images
  chat_media/audio
  generated_practice/quizzes
  generated_practice/exams
  generated_practice/solution_sets
  attempts
  reports/performance_reports.jsonl
  rag_exports
```

Passwords are stored in `data/auth/users.json` as salted PBKDF2 hashes, never plaintext.

When a new user is created, study material, syllabus, criteria, learning goals, and exam criteria can be copied from a template user. Private chat history, uploaded media, attempts, reports, grades, and hidden solution sets are not copied.

Vector collection names include the user id, such as `user_alim__subject_german` and `user_alim__memory_german`. Retrieval also filters by `user_id`.
