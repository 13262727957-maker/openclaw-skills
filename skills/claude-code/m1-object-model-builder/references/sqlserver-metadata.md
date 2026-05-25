# SQL Server Metadata Reference

Use these patterns for metadata-driven M1 extraction.

## Locate Entity Metadata

```sql
select *
from dbo.md_table_property
where table_name in ('wms_po_order', 'wms_po_rcv')
order by table_name, id;
```

When duplicate table names exist, choose by `class_name`, `full_class_name`, `source_entity_id`, `relation_colum_id`, and `bill_property_id`.

## Extract Columns

```sql
select
  t.table_name,
  c.id,
  c.column_code,
  c.column_name,
  c.entity_code,
  c.column_component,
  c.sql_data_type,
  c.java_type,
  c.ref_id,
  c.preset_id,
  c.description,
  c.show_flag,
  c.edit_flag,
  c.is_query_condition,
  c.null_able,
  c.length,
  c.precise,
  c.default_value
from dbo.md_column_property c
join dbo.md_table_property t on t.id = c.table_property_id
where t.table_name = '<table_name>'
  and isnull(c.dr, 0) = 0
order by isnull(c.sort, 999999), c.column_code;
```

## Add Physical Schema

```sql
select
  c.name as column_name,
  type_name(c.user_type_id) as db_type,
  c.max_length,
  c.precision,
  c.scale,
  c.is_nullable,
  dc.definition as default_definition
from sys.columns c
left join sys.default_constraints dc
  on dc.object_id = c.default_object_id
where c.object_id = object_id('dbo.<table_name>')
order by c.column_id;
```

## Resolve Value Sets

```sql
select *
from dbo.sys_preset_file
where id = '<preset_id>';

select
  preset_file_id,
  file_item_code as status_value,
  file_item_name as status_name,
  file_item_describe as status_description,
  is_archive,
  dr
from dbo.sys_preset_file_item
where preset_file_id = '<preset_id>'
order by try_convert(int, file_item_code), file_item_code;
```

## One-Shot State Query

```sql
select
  t.table_name,
  c.column_code,
  c.column_name,
  c.entity_code,
  c.preset_id,
  pf.file_code,
  pf.file_name,
  pfi.file_item_code as status_value,
  pfi.file_item_name as status_name,
  pfi.file_item_describe as status_description
from dbo.md_column_property c
join dbo.md_table_property t on t.id = c.table_property_id
left join dbo.sys_preset_file pf on pf.id = c.preset_id
left join dbo.sys_preset_file_item pfi on pfi.preset_file_id = pf.id
where t.table_name in ('<table1>', '<table2>')
  and c.column_code in ('bill_status', 'row_status', 'accraditation_status', 'closed_status')
order by t.table_name, c.column_code, try_convert(int, pfi.file_item_code), pfi.file_item_code;
```

## Runtime Status Distribution

```sql
select bill_status, count(*) as cnt
from dbo.<table_name>
group by bill_status
order by bill_status;
```

Compare runtime values with value-set items. Preserve undefined runtime values as anomalies.

