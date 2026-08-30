# Subject and Language Contract

The backend now defines the frontend's frozen 15 top-level subject IDs in this
order:

1. `mathematics` (`en`)
2. `physics` (`en`)
3. `english` (`en`)
4. `history` (`en`)
5. `french` (`fr`, CEFR B1)
6. `german` (`de`)
7. `biology` (`de`)
8. `chemistry` (`de`)
9. `spf_biology_chemistry` (`de`, virtual)
10. `philosophy` (`de`)
11. `political_education` (`de`)
12. `pedagogics_psychology` (`de`)
13. `economics` (`de`)
14. `art` (`de`)
15. `sport` (`de`)

`spf_biology` and `spf_chemistry` remain concrete corpus/component IDs but are
never public top-level subjects. Requests for `spf_biology_chemistry` query
both component corpora unless one valid component is selected. The virtual
parent has no duplicate material folder or vector collection.

`validate_top_level_subject_id()`, `validate_component_for_subject()`, and
`corpus_keys_for_request()` are the binding validation/routing helpers.
`language_for_api_subject()` returns `de`, `en`, or `fr`; prompt instructions
enforce the corresponding Grade-11 register and CEFR B1 French requirements.

Existing folders are preserved. In particular, legacy `maths_physics`
storage/material is an explicit read alias for both `mathematics` and
`physics`; it is not renamed or deleted. Setup creates missing concrete subject
folders and starter goal/criteria files only when absent, and skips the virtual
SPF parent.

The frontend remains authoritative for labels/cards and all grade-combination
or component-average display behavior.
