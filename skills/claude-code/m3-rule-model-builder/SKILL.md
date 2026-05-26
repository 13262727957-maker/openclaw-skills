---
name: m3-rule-model-builder
description: Build M3 rule models for enterprise business systems. Use when Codex needs to extract, validate, or update the rules layer from source code, Swagger/OpenAPI, SQL Server metadata, runtime data, web pages, screenshots, flow diagrams, and existing M1/M2/M4 models; especially for rules about action preconditions, required fields, state transitions, blocking conditions, side effects, and Agent execution guards.
---

# M3 Rule Model Builder

## Purpose

Build the M3 rules layer that tells an Agent why a business action can run, why it is blocked, what state changes it causes, and what evidence supports that conclusion.

M3 is not a field list and not a process diagram. It is the executable diagnosis layer between:

- M1 objects and states
- M2 actions and API paths
- M4 business scenarios
- runtime instance data

## Inputs To Prefer

Use all available evidence, ordered by reliability:

1. Source code: service methods, controllers, DTO validators, `BusinessException`, state assignment, quantity calculation, external calls.
2. Swagger/OpenAPI: endpoint, method, path/body/query parameters, response shape.
3. SQL Server metadata: `md_table_property`, `md_column_property`, `sys_preset_file`, `sys_preset_file_item`, `sys_encoding_rules`, `sys_encoding_rules_segment`.
4. Runtime data: real bill numbers, observed status distribution, child rows, downstream records.
5. Existing models: M1 entity/state model, M2 action model, M4 scenario model.
6. Page evidence: buttons, filters, disabled states, detail-page validation, screenshots.
7. Flow diagrams and business notes: use as process evidence; mark inferred when not confirmed by code/data.

Do not store credentials in the skill output or model files.

## Rule Layer Taxonomy

Use this layer naming unless the project already has a stronger convention:

- `L1.database_constraint`: database metadata, dictionaries, encoding rules, non-null fields.
- `L2.swagger_parameter`: API method/path and parameter requirements.
- `L3.source_business_rule`: source-code business checks, exceptions, state assignment, writeback logic.
- `L4.page_interaction_rule`: page filters, buttons, visibility, disabled states, front-end validation.
- `L5.process_rule`: scenario sequence and cross-document dependency from M4 or flow diagrams.
- `L6.inferred_fusion_rule`: inference from multiple weak signals; never treat as execution-safe without confirmation.

## Build Workflow

1. Define scope
   - Name the scenario and included business objects.
   - Link each rule back to M1 entity, M2 action, and M4 scenario when possible.

2. Collect dictionaries and metadata rules
   - Query table metadata, column metadata, preset files, preset file items, and encoding rules.
   - Convert status values into dictionaries.
   - Record unknown runtime values as warnings, not invented definitions.

3. Extract action preconditions from source and Swagger
   - For every M2 action, find required IDs, request body requirements, status checks, user context, external config checks, and child-row requirements.
   - Treat thrown business exceptions as blocker rules.

4. Extract state transition rules
   - Capture source state, target state, trigger action/API, and state assignment evidence.
   - If state is recalculated from child rows or quantities, record the aggregation condition.

5. Extract quantity, traceability, and downstream guards
   - Model quantity limits, remaining quantity, received/delivered/in-stock writeback, source/first document trace fields, and delete/update guards when downstream records exist.

6. Add page interaction rules
   - Include list filters, toolbar actions, row actions, print/export/table settings if observed.
   - Mark page-only or UI-only behaviors separately from API-callable rules.

7. Create execution guards
   - Each rule that affects API execution should include `executionGuard`.
   - Use `blockExecution=true` for definite blockers.
   - Use `severity=warning` for encoding, inference, unknown status, incomplete evidence, or non-blocking derived behavior.

8. Mark confidence and completeness
   - `verified`: confirmed by code/data/API.
   - `partial`: enough for diagnosis, not enough for all execution cases.
   - `inferred`: plausible but requires business or source confirmation.
   - `conflict`: sources disagree; prohibit execution and explain conflict.

## Rule Object Contract

Each rule should include at least:

```json
{
  "id": "M3.RULE.DOMAIN.ACTION.CONDITION",
  "name": "camelCaseRuleName",
  "displayName": "人类可读规则名",
  "ruleType": "required_input | action_precondition | state_precondition | state_transition | quantity_constraint | traceability | mutation_guard | encoding_rule | page_interaction | external_system",
  "layer": "L3.source_business_rule",
  "appliesTo": {
    "m1Entity": "M1.ENTITY.X",
    "m2Action": "M2.ACTION.X",
    "m4Scenario": "M4.SCENARIO.X"
  },
  "trigger": {
    "event": "user invokes action",
    "api": "POST /path"
  },
  "condition": "machine-readable or concise pseudo expression",
  "stateTransition": {
    "entity": "EntityName",
    "field": "statusField",
    "from": "optional",
    "to": "value",
    "toName": "status name"
  },
  "onFail": {
    "code": "BUSINESS_CODE",
    "message": "system or business message",
    "agentExplanation": "Agent-facing explanation"
  },
  "evidence": [
    {
      "type": "source | swagger | sqlserver_metadata | runtime | page | flowchart | inference",
      "path": "file path, SQL, URL, or model path",
      "lines": "optional",
      "note": "optional"
    }
  ],
  "confidence": 0.9,
  "completeness": "verified",
  "executionGuard": {
    "applicableBeforeApiCall": true,
    "blockExecution": true,
    "severity": "blocker",
    "evaluationSource": "source_rule"
  }
}
```

For output details and review checklist, read `references/m3-output-contract.md` only when you need a stricter schema or validation checklist.

## SQL Evidence Patterns

Prefer parameterized SQL. Common metadata probes:

```sql
select * from md_table_property where table_name = @tableName;
select * from md_column_property where table_property_id = @tablePropertyId;
select * from sys_preset_file where id = @presetFileId;
select * from sys_preset_file_item where preset_file_id = @presetFileId;
select * from sys_encoding_rules where md_table_property_id = @tablePropertyId;
select * from sys_encoding_rules_segment where sys_encoding_rules_id = @ruleId;
```

Use runtime SQL only for diagnosis or evidence, not for changing business data.

## Output Set

When the task asks for final artifacts, produce:

- Agent-readable JSON: nested dictionaries, rules, execution guards, source policy, layer review.
- Knowledge-graph JSON: rule nodes, dictionary nodes, action/entity/scenario edges.
- Human-readable Markdown: concise but complete explanation of rule categories, state transitions, action blockers, evidence, and gaps.

Keep source evidence only when it helps trust, review, or future completion. Remove noisy raw scan evidence from human summaries unless the user asks for it.

## Review Checklist

Before finishing, verify:

- Every major M2 action has at least one rule decision: allowed, blocked, warning, or missing evidence.
- Every state-changing action has a state transition or an explicit “not confirmed”.
- Every blocker has `executionGuard.blockExecution=true`.
- Every inferred rule is marked `completeness=inferred` or similar.
- Status dictionaries include source IDs and unknown runtime values are not silently renamed.
- Rule IDs are stable and namespaced.
- JSON parses successfully.
- The final answer states what is usable for Agent execution and what is diagnosis-only.
