---
name: m1-object-model-builder
description: "Build M1 business object models for an Agent from enterprise system artifacts. Use when Codex needs to turn database metadata, SQL Server tables, source Entity/DTO classes, Swagger/OpenAPI files, real sample document numbers, and business notes into M1 object ontology outputs: entities, fields, field layers, states, relations, runtime lookup entries, examples, and evidence files."
---

# M1 Object Model Builder

## Purpose

Build the M1 layer of a seven-layer business model: the object semantics map that lets an Agent know what business entities exist, what fields mean, how objects relate, what states mean, and how real instances are queried.

Use this skill to produce both human-readable Markdown and Agent-readable JSON. Keep scope strict: model only the requested business stage or flow.

## Workflow

1. Confirm the scope, target database, source directories, Swagger files, and sample business document numbers.
2. Identify candidate entities from metadata first, then cross-check source Entity classes, Swagger schemas, and real data.
3. Select the correct metadata records when table names are reused by multiple business objects.
4. Extract fields into three layers:
   - `coreFields`: instance identity, state, relationship, and reasoning-critical fields.
   - `extendedFields`: meaningful business fields, UI-visible/queryable/editable fields, reference fields, and value-set fields.
   - `rawFields`: every metadata/table field, including custom, reserved, audit, and low-frequency fields.
5. Extract states from value sets before relying on code comments.
6. Extract relations from metadata relations, parent/child metadata, foreign-like columns, and flow fields such as `sourceId`, `sourceBid`, `firstId`, `firstBid`, and `billCode`.
7. Verify the model with real sample records. Record normal samples and anomalies.
8. Write outputs with source evidence and unresolved ambiguity clearly marked.

## Source Priority

Use this precedence unless the user overrides it:

1. Database metadata: table/entity records, column metadata, value sets, relation metadata.
2. SQL Server physical schema: type, length, nullability, defaults, keys, indexes.
3. Source code: Entity/PO classes, DTO/VO classes, service/rule code for state transitions.
4. Swagger/OpenAPI: API-facing fields, descriptions, request/response shapes.
5. Real business records: sample document numbers and runtime status distributions.
6. Human notes/screenshots: scope, table choices, business terminology, known caveats.

When sources conflict, preserve the conflict in evidence and prefer metadata/value sets for static definitions; use code and runtime data to explain behavior.

## SQL Server Metadata Pattern

For metadata-driven systems like the WMS pilot, use this join path:

```text
md_bill_property
md_table_property
  -> md_column_property
  -> md_table_relation
md_column_property.preset_id
  -> sys_preset_file
  -> sys_preset_file_item
```

Use `md_table_property.class_name`, `full_class_name`, `source_entity_id`, `relation_colum_id`, and `bill_property_id` to choose the right record when the same table appears more than once.

Use `md_column_property` fields:

```text
column_code, column_name, entity_code, column_component,
sql_data_type, java_type, ref_id, preset_id,
description, show_flag, edit_flag, is_query_condition,
null_able, length, precise, default_value
```

Use `sys.columns` or `information_schema.columns` to add physical field constraints.

## Field Layering Rules

Classify fields consistently:

```text
coreFields:
  id, business key, bill/status fields, approval/closed status,
  parent-child join keys, source/first reference keys,
  critical quantity/date/person/organization fields used in the requested flow

extendedFields:
  visible/query/edit fields, ref_id fields, preset_id fields,
  meaningful domain fields such as supplier, item, warehouse, batch,
  amount/tax/date/organization/source fields not needed for first-pass reasoning

rawFields:
  all remaining fields, reserved/custom fields, audit fields,
  low-frequency fields, technical fields, and fields whose meaning is unclear
```

Do not drop raw fields. Store them in separate `raw-fields/*.json` files when there are many fields, and reference those files from the entity JSON.

## Required Outputs

Create this structure unless the user asks for a different layout:

```text
ontology/m1-object/
  <entity-display-name>.md
  <entity-name>.json
  metadata-evidence.json
  raw-fields/
    <entity-or-table>.json
    summary.json
index/
  entity-index.json
  field-index.json
```

For real samples, also create a concise sample verification report or an `examples` JSON file when useful.

## Entity Markdown Template

Each Markdown file should include:

```text
1. Basic information
2. Core field definitions
2.1 Field layering and raw field references
3. Child/detail fields, if any
4. State definitions
5. Entity relations
6. Field mappings across objects
7. Natural-language aliases
8. Data/sample notes, if available
```

Keep Markdown readable. Do not paste hundreds of raw fields into it; link to raw field JSON.

## Entity JSON Template

Each entity JSON should include:

```json
{
  "id": "M1.ENTITY.X",
  "type": "entity",
  "name": "X",
  "displayName": "中文名",
  "aliases": [],
  "description": "",
  "source": [],
  "confidence": 0.0,
  "completeness": "pilot_core_fields|full_fields_available",
  "runtimeLookup": {
    "table": "",
    "businessKey": "",
    "primaryKey": ""
  },
  "aggregate": {
    "rootClass": "",
    "rootTable": "",
    "children": []
  },
  "fieldModel": {
    "strategy": "coreFields + extendedFields + rawFields",
    "rawFieldsRef": []
  },
  "fields": [],
  "states": [],
  "relations": [],
  "fieldMappings": [],
  "examples": []
}
```

Mark embedded `fields` with `"layer": "core"` when the full field set is stored externally.

## Validation

Always validate:

1. JSON syntax for every output JSON file.
2. Each entity has a runtime lookup table and business key.
3. Each status field has value-set evidence or is marked inferred.
4. Real sample records can be queried by business key.
5. Known anomalies are not silently normalized.

For SQL Server metadata export, adapt or run `scripts/export_sqlserver_m1_metadata.py`.

## Useful References

- See `references/sqlserver-metadata.md` for SQL examples and evidence queries.
- See `references/output-checklist.md` for a compact completion checklist.
