#!/usr/bin/env python3
"""
api-diff-table: 源码接口 vs Swagger 接口 二维对比表生成器
输入: source-api-doc.md + spec-samples.json
输出: {project}-api-diff-table.md + {project}-api-diff-summary.json
"""

import json
import re
import sys
import os
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# 配置参数（从命令行传入）
# ──────────────────────────────────────────────────────────────
# SOURCE_DIR = sys.argv[1]        # 源码项目目录（含 source-api-doc.md）
# SWAGGER_DIR = sys.argv[2]       # Swagger 输出目录（含 spec-samples.json）
# PROJECT_NAME = sys.argv[3]      # 项目名称
# OUTPUT_DIR = sys.argv[4]        # 输出目录（可选，默认同 SOURCE_DIR）

# ──────────────────────────────────────────────────────────────
# Step 0: 环境预检
# ──────────────────────────────────────────────────────────────
def check_env(source_dir, swagger_dir):
    errors = []
    if not os.path.exists(source_dir):
        errors.append(f"❌ 源码目录不存在: {source_dir}")
    else:
        doc_path = os.path.join(source_dir, "source-api-doc.md")
        if not os.path.exists(doc_path):
            errors.append(f"❌ 缺少 source-api-doc.md，请先运行 api-scanner-from-source")
    if not os.path.exists(swagger_dir):
        errors.append(f"❌ Swagger 目录不存在: {swagger_dir}")
    else:
        spec_path = os.path.join(swagger_dir, "spec-samples.json")
        if not os.path.exists(spec_path):
            errors.append(f"❌ 缺少 spec-samples.json，请先运行 api-scanner-from-swagger")
    if not sys.warnoptions:
        pass  # Python 内置 json 始终可用
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)

# ──────────────────────────────────────────────────────────────
# Step 1: 解析源码接口索引表
# ──────────────────────────────────────────────────────────────
def parse_source_doc(doc_path):
    """从 source-api-doc.md 的接口索引表提取所有接口行"""
    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 找到接口索引总表区块
    m = re.search(r'## 📋 接口索引总表\n\n\|.*?\n(.*?)(?:\n##|\Z)', content, re.DOTALL)
    if not m:
        print("⚠️ 未找到接口索引表，跳过")
        return []

    table_content = m.group(0)
    apis = []

    # 匹配每一行数据：| # | /path | HTTP | 名称 | 入参 | 出参 | 必填 |
    pattern = r'^\|\s*\d+\s*\|\s*([^\s|]+?)\s*\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    for line in table_content.split('\n'):
        line = line.strip()
        if not line.startswith('|') or '---' in line or line.startswith('|#'):
            continue
        match = re.match(pattern, line)
        if match:
            path = match.group(1).strip()
            method = match.group(2).strip().upper()
            input_type = match.group(3).strip() or "-"
            output_type = match.group(4).strip() or "-"
            apis.append({
                "path": path,
                "method": method,
                "input_type": input_type,
                "output_type": output_type,
                "source": "source"
            })

    return apis

# ──────────────────────────────────────────────────────────────
# Step 2: 解析 Swagger spec-samples.json
# ──────────────────────────────────────────────────────────────
def parse_swagger_spec(spec_path):
    """从 spec-samples.json 提取接口列表"""
    with open(spec_path, 'r', encoding='utf-8', errors='ignore') as f:
        spec = json.load(f)

    apis = []
    base_url = spec.get("base_url", "")

    for module in spec.get("modules", []):
        module_name = module.get("name", "unknown")
        for ep in module.get("endpoints", []):
            path = ep.get("path", "")
            method = ep.get("method", "GET").upper()

            # 参数签名：取 in=body 的参数类型名字符串拼接
            body_params = [p for p in ep.get("parameters", []) if p.get("in") == "body"]
            if body_params:
                input_sig = ",".join(sorted([p.get("name", "") for p in body_params]))
            else:
                input_sig = "-"

            output_type = ep.get("response_type", "-") or "-"

            apis.append({
                "path": path,
                "method": method,
                "input_sig": input_sig,
                "output_type": output_type,
                "module": module_name,
                "source": "swagger"
            })

    return apis

# ──────────────────────────────────────────────────────────────
# Step 3: 路径标准化与归一化
# ──────────────────────────────────────────────────────────────
def normalize_path(path):
    """移除末尾斜杠、合并连续斜杠"""
    path = path.strip().rstrip('/')
    path = re.sub(r'/+', '/', path)
    return path

def normalize_type(t):
    """移除类型名中的空格"""
    return t.strip().replace(' ', '')

def api_key(path, method):
    return f"{normalize_path(path)}::{method.upper()}"

# ──────────────────────────────────────────────────────────────
# Step 4: 生成对比结果
# ──────────────────────────────────────────────────────────────
def diff(source_apis, swagger_apis):
    swagger_dict = {}
    for api in swagger_apis:
        key = api_key(api["path"], api["method"])
        swagger_dict[key] = api

    source_dict = {}
    for api in source_apis:
        key = api_key(api["path"], api["method"])
        source_dict[key] = api

    exact_match = []
    source_only = []
    swagger_only = []
    param_mismatch = []
    response_mismatch = []

    all_keys = sorted(source_dict.keys() | swagger_dict.keys())

    for key in all_keys:
        src = source_dict.get(key)
        swg = swagger_dict.get(key)

        if src and swg:
            src_in = normalize_type(src["input_type"])
            swg_in = normalize_type(swg["input_sig"]) if swg["input_sig"] != "-" else ""
            src_out = normalize_type(src["output_type"])
            swg_out = normalize_type(swg["output_type"])

            if src_in == swg_in and src_out == swg_out:
                status = "✅"
                exact_match.append((src, swg, status))
            elif src_in != swg_in:
                status = "📝"
                param_mismatch.append((src, swg, status))
            elif src_out != swg_out:
                status = "🔄"
                response_mismatch.append((src, swg, status))
        elif src and not swg:
            status = "🗂️"
            source_only.append((src, None, status))
        elif not src and swg:
            status = "⚡"
            swagger_only.append((src, swg, status))

    # 顺序：完全匹配 → 入参不一致 → 出参不一致 → 源码多 → Swagger多
    return exact_match + param_mismatch + response_mismatch + source_only + swagger_only

# ──────────────────────────────────────────────────────────────
# Step 5: 输出 Markdown 二维表
# ──────────────────────────────────────────────────────────────
def write_markdown_table(rows, project_name, output_path, source_count, swagger_count):
    status_counts = {
        "exact_match": 0, "source_only": 0, "swagger_only": 0,
        "param_mismatch": 0, "response_mismatch": 0
    }

    lines = []
    lines.append(f"# {project_name} 接口对比表\n")
    lines.append(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**说明**：✅完全匹配 | 🗂️源码多 | ⚡Swagger多 | 📝入参不一致 | 🔄出参不一致\n")
    lines.append(f"\n")
    lines.append(f"| 接口路径 | HTTP | 源码入参 | Swagger入参 | 源码出参 | Swagger出参 | 状态 |\n")
    lines.append(f"|----------|------|----------|-------------|----------|-------------|------|\n")

    for src, swg, status in rows:
        path = src["path"] if src else (swg["path"] if swg else "-")
        method = (src["method"] if src else (swg["method"] if swg else "-"))
        src_in = src["input_type"] if src else "-"
        swg_in = swg["input_sig"] if swg else "-"
        src_out = src["output_type"] if src else "-"
        swg_out = swg["output_type"] if swg else "-"

        # 统计
        if status == "✅":
            status_counts["exact_match"] += 1
        elif status == "🗂️":
            status_counts["source_only"] += 1
        elif status == "⚡":
            status_counts["swagger_only"] += 1
        elif status == "📝":
            status_counts["param_mismatch"] += 1
        elif status == "🔄":
            status_counts["response_mismatch"] += 1

        lines.append(f"| {path} | {method} | {src_in} | {swg_in} | {src_out} | {swg_out} | {status} |")

    lines.append("\n")
    lines.append(f"**汇总**：源码 {source_count} 接口 | Swagger {swagger_count} 接口 | ")
    lines.append(f"✅{status_counts['exact_match']} ")
    lines.append(f"📝{status_counts['param_mismatch']} ")
    lines.append(f"🔄{status_counts['response_mismatch']} ")
    lines.append(f"🗂️{status_counts['source_only']} ")
    lines.append(f"⚡{status_counts['swagger_only']}\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("".join(lines))

    return status_counts

# ──────────────────────────────────────────────────────────────
# Step 6: 输出汇总 JSON（可选）
# ──────────────────────────────────────────────────────────────
def write_summary(project_name, source_count, swagger_count, status_counts, output_path):
    summary = {
        "project": project_name,
        "source_count": source_count,
        "swagger_count": swagger_count,
        "status_counts": status_counts,
        "generated_at": datetime.now().isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 4:
        print("用法: python3 api_diff_table.py <SOURCE_DIR> <SWAGGER_DIR> <PROJECT_NAME> [OUTPUT_DIR]")
        sys.exit(1)

    source_dir = sys.argv[1]
    swagger_dir = sys.argv[2]
    project_name = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else source_dir

    # Step 0
    check_env(source_dir, swagger_dir)

    # Step 1
    doc_path = os.path.join(source_dir, "source-api-doc.md")
    source_apis = parse_source_doc(doc_path)
    print(f"✅ 解析源码接口: {len(source_apis)} 条")

    # Step 2
    spec_path = os.path.join(swagger_dir, "spec-samples.json")
    swagger_apis = parse_swagger_spec(spec_path)
    print(f"✅ 解析 Swagger 接口: {len(swagger_apis)} 条")

    # Step 3-4
    rows = diff(source_apis, swagger_apis)

    # Step 5
    os.makedirs(output_dir, exist_ok=True)
    table_path = os.path.join(output_dir, f"{project_name}-api-diff-table.md")
    status_counts = write_markdown_table(rows, project_name, table_path, len(source_apis), len(swagger_apis))
    print(f"✅ 输出对比表: {table_path}")

    # Step 6
    summary_path = os.path.join(output_dir, f"{project_name}-api-diff-summary.json")
    write_summary(project_name, len(source_apis), len(swagger_apis), status_counts, summary_path)
    print(f"✅ 输出汇总: {summary_path}")

if __name__ == "__main__":
    main()