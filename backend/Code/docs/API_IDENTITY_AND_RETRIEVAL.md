# Stage-1 API Identity and Retrieval

Supabase remains the authentication authority. For local Stage 1 integration,
the frontend sends its authenticated user ID in `X-Student-Id`; the Python
process does not consult the legacy local-auth database and does not verify a
Supabase JWT. `resolve_student_context()` is the single header-to-context
bridge, and `StudentContext` sanitizes the ID before any storage helper sees it.

User-scoped operations require the header by default. `API_DEV_STUDENT_ID` may
be configured explicitly for developer-only manual work, but its default is
empty. FastAPI wiring must not silently invent a production-local identity.

`retrieve_student_study_context()` resolves the public subject/component to
concrete corpora and merges layers in this order:

1. current request (kept by prompt construction);
2. current student's indexed notes/uploads (`user_<id>__subject_<corpus>` plus
   a matching `user_id` metadata filter);
3. approved shared learning goals and exam criteria loaded directly from
   canonical files, never from a shared private-note collection;
4. approved shared syllabus files;
5. current student's separately indexed chat/practice/performance memory;
6. optional trusted public web sources searched with a public subject query,
   never private note or question text.

SPF requests resolve to one selected component corpus or both component
corpora. Private content is never copied into shared collections, and the
virtual parent has no duplicate collection. Optional `material_ids` and
`learning_goal_id` filters are applied to chunk metadata when supplied.

The legacy Streamlit login and current shared chat retrieval remain available
only for that legacy UI during migration. Future API chat routes must call the
student-scoped retrieval service and set Python transcript persistence off,
because Supabase owns the transcript.
