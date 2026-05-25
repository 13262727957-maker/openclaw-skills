# M1 Output Checklist

Use this checklist before finalizing M1 outputs.

## Scope

- Scope is explicit and limited to the requested business stage.
- Upstream/downstream entities outside scope are named only as references, not fully modeled.

## Entity Identity

- Each entity has Chinese name, English name, aliases, entity class, table, business key, primary key.
- Duplicate metadata records are resolved and documented.

## Fields

- `coreFields` cover identity, state, relation, and critical reasoning fields.
- `extendedFields` cover meaningful UI/query/ref/value-set fields.
- `rawFields` preserve every field from metadata/schema.
- Raw fields are stored separately when too large for Markdown.

## States

- State definitions prefer `sys_preset_file_item`.
- Source code is used for transitions and behavior.
- Runtime status values are compared against value sets.
- Undefined values are marked as anomalies.

## Relations

- Parent-child relations use metadata and join fields.
- Flow/source relations use `sourceId`, `sourceBid`, `firstId`, `firstBid`, business keys, and service rules.
- Field mappings explain which source fields populate target fields.

## Examples

- Sample business document numbers are queried.
- Normal and abnormal samples are documented.
- Examples show enough IDs to verify joins.

## Validation

- All JSON files parse.
- File links and references point to existing files.
- Evidence file records metadata IDs, value-set IDs, ambiguities, and anomalies.
