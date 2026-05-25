#!/usr/bin/env python3
"""Export SQL Server metadata fields for M1 object modeling.

Requires pymssql. This script only reads metadata and writes JSON files.
"""

import argparse
import json
import re
from pathlib import Path

import pymssql


RAW_PATTERN = re.compile(
    r"^(sdef|ndef)\d+$|^dr$|^ts$|^creator$|^creation_time$|^modifier$|^modified_time$|^id_str$|^current$|^size$",
    re.I,
)


def classify(column_code, row, core_columns):
    if column_code in core_columns:
        return "core"
    text = f"{row.get('column_name') or ''} {row.get('description') or ''}"
    if RAW_PATTERN.match(column_code) or "自定义字段" in text or "预留字段" in text:
        return "raw"
    if row.get("show_flag") == "Y" or row.get("is_query_condition") == 1:
        return "extended"
    if row.get("ref_id") or row.get("preset_id"):
        return "extended"
    semantic_tokens = [
        "source_",
        "first_",
        "status",
        "qty",
        "amount",
        "date",
        "time",
        "person",
        "org",
        "dept",
        "type",
        "code",
        "name",
        "memo",
        "reason",
    ]
    if any(token in column_code for token in semantic_tokens):
        return "extended"
    return "raw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--table",
        action="append",
        required=True,
        help="table_name:metadata_table_id:slug[:core_col1,core_col2]",
    )
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = pymssql.connect(
        server=args.server,
        user=args.user,
        password=args.password,
        database=args.database,
        login_timeout=10,
        timeout=60,
    )
    cur = conn.cursor(as_dict=True)
    summary = []

    for item in args.table:
        parts = item.split(":")
        if len(parts) < 3:
            raise SystemExit("--table must be table_name:metadata_table_id:slug[:core_cols]")
        table_name, metadata_id, slug = parts[:3]
        core_columns = set(parts[3].split(",")) if len(parts) > 3 and parts[3] else set()

        cur.execute(
            """
            select c.column_code, c.column_name, c.entity_code, c.column_component,
                   c.sql_data_type, c.java_type, c.ref_id, c.preset_id,
                   c.description, c.show_flag, c.edit_flag, c.is_query_condition,
                   c.null_able, c.length, c.precise, c.default_value, c.sort,
                   sc.is_nullable, type_name(sc.user_type_id) db_type,
                   sc.max_length, sc.precision, sc.scale
            from dbo.md_column_property c
            left join sys.columns sc
              on sc.object_id = object_id('dbo.' + %s)
             and sc.name = c.column_code
            where c.table_property_id = %s
              and isnull(c.dr, 0) = 0
            order by isnull(c.sort, 999999), c.column_code
            """,
            (table_name, metadata_id),
        )

        fields = []
        for row in cur.fetchall():
            column_code = row["column_code"]
            fields.append(
                {
                    "name": row["entity_code"],
                    "dbColumn": column_code,
                    "displayName": row["column_name"],
                    "layer": classify(column_code, row, core_columns),
                    "component": row["column_component"],
                    "javaType": row["java_type"],
                    "sqlDataType": row["sql_data_type"] or row["db_type"],
                    "dbType": row["db_type"],
                    "maxLength": row["max_length"],
                    "precision": row["precision"],
                    "scale": row["scale"],
                    "nullable": bool(row["is_nullable"]) if row["is_nullable"] is not None else None,
                    "metadataNullable": row["null_able"],
                    "showFlag": row["show_flag"],
                    "editFlag": row["edit_flag"],
                    "isQueryCondition": row["is_query_condition"],
                    "refId": row["ref_id"] or None,
                    "presetId": row["preset_id"] or None,
                    "description": row["description"],
                    "defaultValue": row["default_value"],
                }
            )

        payload = {
            "database": args.database,
            "table": table_name,
            "metadataTableId": metadata_id,
            "fieldCount": len(fields),
            "fields": fields,
        }
        (out_dir / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        counts = {layer: sum(1 for field in fields if field["layer"] == layer) for layer in ["core", "extended", "raw"]}
        summary.append({"table": table_name, "file": str(out_dir / f"{slug}.json"), "fieldCount": len(fields), **counts})

    (out_dir / "summary.json").write_text(json.dumps({"tables": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    conn.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
