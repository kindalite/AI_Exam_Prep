# Stage-1 AI Study-Tool Contracts

The quiz, mock-exam, study-plan, and grading endpoints use the identified
student's private collections plus approved canonical collections. Model output
must validate as JSON; one constrained repair call is allowed, after which the
API returns `invalid_model_output` instead of forwarding malformed text.

Quiz answers/explanations and mock-exam model answers are deliberately `null` in
generation responses. Complete solution data is saved under the student's
`generated_practice/solution_sets` directory and remains protected by the
existing hidden-solution flow.

Mock-exam question points are scaled deterministically so their sum equals
`total_points`. Study plans are proposals only: Python schedules returned tasks
into non-overlapping validated slots, but does not create or update Lovable
planner/localStorage records. AI grading writes only per-student practice
performance reports and never changes real frontend grades or averages.

The grading API returns the exact formula `1 + 5 * points_awarded / max_points`,
clamped to 1–6 without half-grade display rounding.
