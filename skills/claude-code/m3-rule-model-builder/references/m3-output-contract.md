# M3 Output Contract

Load this reference when building or reviewing a full M3 artifact.

## Required Top-Level JSON Shape

```json
{
  "version": "M3-*",
  "scope": "business scenario",
  "modelType": "M3.RuleModel",
  "purpose": "why this model exists",
  "sourcePolicy": {
    "verifiedSources": [],
    "pendingSources": [],
    "ruleLayers": {}
  },
  "statusDictionaries": [],
  "rules": [],
  "executionValidationPolicy": {},
  "layerReview": {}
}
```

## Recommended Rule Types

- `required_input`: request/body/child row/user context required.
- `action_precondition`: condition that must hold before an action.
- `state_precondition`: status or approval state required before action.
- `state_transition`: action changes status.
- `field_derivation`: field generated or copied by rule.
- `quantity_constraint`: limits by ordered/delivered/received/remaining quantity.
- `traceability`: source/first document relation must exist or be written.
- `mutation_guard`: update/delete/close blocked by downstream data.
- `encoding_rule`: bill number or code generation rule.
- `page_interaction`: query, print, export, table settings, disabled button, visible action.
- `external_system`: OA, ERP/U9, QMS, or other external integration requirement.

## Execution Guard Rules

Use this convention:

```json
{
  "applicableBeforeApiCall": true,
  "blockExecution": true,
  "severity": "blocker",
  "evaluationSource": "source_rule"
}
```

Severity:

- `blocker`: Agent must not prepare or execute the action if the condition fails.
- `warning`: Agent may explain or prepare with warning; do not use as sole blocker.
- `info`: context only.

Evaluation source:

- `source_rule`
- `swagger_parameter`
- `database_or_metadata`
- `runtime_data`
- `page_observation`
- `process_model`
- `inference`

## Human Summary Sections

For human-readable Markdown, use:

1. Scope and evidence sources.
2. Status dictionaries.
3. Action blocker rules.
4. State transition rules.
5. Quantity and traceability rules.
6. Page interaction rules.
7. Execution readiness.
8. Gaps and required confirmation.

## Knowledge Graph Edges

Recommended edges:

- `RULE_APPLIES_TO_ENTITY`
- `RULE_GUARDS_ACTION`
- `RULE_IN_SCENARIO`
- `RULE_USES_FIELD`
- `RULE_TRANSITIONS_STATE`
- `RULE_HAS_EVIDENCE`
- `DICT_DEFINES_FIELD`
- `ACTION_BLOCKED_BY_RULE`
- `ACTION_WARNED_BY_RULE`

## Quality Bar

The M3 model is usable for Agent diagnostics when:

- Status dictionaries are available for major status fields.
- Rule blockers exist for major business commands.
- State-changing actions identify expected transitions or missing evidence.
- Evidence and confidence are present.

The M3 model is usable for execution preparation when:

- Applicable M2 actions have API paths and parameter definitions.
- Blocker rules have executable pre-call conditions.
- Runtime fields needed by the conditions are resolvable from M1 or query tools.
- Missing permissions, compensation, idempotency, and audit are explicitly treated as external runtime gates.
