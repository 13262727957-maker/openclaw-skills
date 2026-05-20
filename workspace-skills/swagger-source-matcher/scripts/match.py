#!/usr/bin/env python3
"""Swagger 模块与源码项目路径匹配脚本

功能：按源码项目分组，生成每个源码项目对应的 Swagger 模块匹配报告。
供下游 api-scanner-from-swagger 技能使用——扫描哪个 Swagger JSON 文件由本脚本输出决定。

输出（每个源码项目单独一份报告）：
  ~/Desktop/成果/{项目名}-swagger-match-report.md
"""
import os, re, json
from pathlib import Path
from datetime import datetime

# ========== 配置区（修改这里适配不同环境）==========
SWAGGER_DIR = Path.home() / "Desktop/成果/swagger/swagger-dev-20260518"

SOURCE_PROJECTS = {
    'caij-cloud-basics': Path.home() / "Desktop/成果/caij-cloud-basics-20260519",
    'caij-cloud-mom':    Path.home() / "Desktop/成果/caij-cloud-mom-20260518",
    'caij-cloud-wcs':    Path.home() / "Desktop/成果/caij-cloud-wcs-20260518",
}

# 辅助匹配规则：路径前缀 → 源码项目名
PATH_PREFIX_RULES = {
    '/mom/':             'caij-cloud-mom',
    '/mom/costing':      'caij-cloud-mom',
    '/mom/basics':       'caij-cloud-mom',
    '/mom/produce':      'caij-cloud-mom',
    '/mom/manufacutre':  'caij-cloud-mom',
    '/aps':              'caij-cloud-mom',
    '/qc/board':         'caij-cloud-mom',
    '/prdUnitPriceCost': 'caij-cloud-mom',
    '/wcs/':             'caij-cloud-wcs',
    '/wcs/basics':       'caij-cloud-wcs',
    '/wcs/warehouse':    'caij-cloud-wcs',
    '/wcs/crownemperor': 'caij-cloud-wcs',
    '/boot/core':        'caij-cloud-wcs',
    '/boot/system':      'caij-cloud-wcs',
    '/boot/medadata':    'caij-cloud-wcs',
    '/boot/metadata':    'caij-cloud-wcs',
    '/boot/pub':         'caij-cloud-wcs',
    '/boot/equipment':   'caij-cloud-wcs',
    '/boot/traceability':'caij-cloud-wcs',
    '/boot/basics':      'caij-cloud-basics',
    '/bd':               'caij-cloud-basics',
    '/bdEm':             'caij-cloud-basics',
    '/boot/basics/bd':   'caij-cloud-basics',
    '/boot/basics/sys':  'caij-cloud-basics',
    '/boot/basics/person':'caij-cloud-basics',
}
# ===============================================


def extract_paths_from_source_doc(proj_dir):
    doc = proj_dir / 'source-api-doc.md'
    if not doc.exists():
        return set(), {}
    content = doc.read_text(encoding='utf-8', errors='ignore')
    paths = set(re.findall(r'`(/[^`]+)`', content))
    prefix_stats = {}
    for p in paths:
        parts = p.strip('/').split('/')
        key = '/' + parts[0] + '/' + parts[1] if len(parts) >= 2 else ('/' + parts[0] if parts else '')
        if key:
            prefix_stats[key] = prefix_stats.get(key, 0) + 1
    return paths, prefix_stats


def extract_paths_from_swagger(fpath):
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
    except:
        return set(), {}
    if not isinstance(data, dict):
        return set(), {}
    paths = set(data.get('paths', {}).keys())
    prefix_stats = {}
    for p in paths:
        parts = p.strip('/').split('/')
        key = '/' + parts[0] + '/' + parts[1] if len(parts) >= 2 else ('/' + parts[0] if parts else '')
        if key:
            prefix_stats[key] = prefix_stats.get(key, 0) + 1
    return paths, prefix_stats


def match_swagger_to_source(swagger_paths, swagger_prefix_stats, source_proj_data):
    """返回 (matched_proj, reason, confidence)"""
    # 策略1: 精确路径重叠
    for proj_name, (proj_paths, _) in source_proj_data.items():
        overlap = swagger_paths & proj_paths
        if overlap:
            return proj_name, f'精确重叠 {len(overlap)} 个路径', '高', sorted(overlap)[:5]

    # 策略2: 前缀规则匹配
    sorted_prefixes = sorted(swagger_prefix_stats.keys(), key=lambda k: -len(k))
    prefix_rule_hits = {}
    for pref in sorted_prefixes:
        for rule_prefix, proj_name in PATH_PREFIX_RULES.items():
            if pref.startswith(rule_prefix) or rule_prefix.startswith(pref):
                prefix_rule_hits[pref] = (proj_name, swagger_prefix_stats[pref])
                break

    if prefix_rule_hits:
        proj_match_counts = {}
        for pref, (proj_name, cnt) in prefix_rule_hits.items():
            proj_match_counts[proj_name] = proj_match_counts.get(proj_name, 0) + cnt
        best_proj = max(proj_match_counts, key=proj_match_counts.get)
        total_match = proj_match_counts[best_proj]
        total_swagger = sum(swagger_prefix_stats.values())
        ratio = total_match / total_swagger if total_swagger > 0 else 0
        top_prefixes = sorted(prefix_rule_hits.items(), key=lambda x: -x[1][1])[:5]
        reason = ', '.join([f"{k}({v[1]})" for k, v in top_prefixes])
        confidence = '高' if ratio >= 0.5 else ('中' if ratio >= 0.1 else '低')
        return best_proj, reason, confidence, top_prefixes

    # 策略3: 源码前缀重叠兜底
    for proj_name, (proj_paths, proj_prefix_stats) in source_proj_data.items():
        overlap_prefixes = set(swagger_prefix_stats.keys()) & set(proj_prefix_stats.keys())
        if overlap_prefixes:
            total_match = sum(swagger_prefix_stats[k] for k in overlap_prefixes)
            total_swagger = sum(swagger_prefix_stats.values())
            ratio = total_match / total_swagger if total_swagger > 0 else 0
            if ratio >= 0.1:
                top_overlap = sorted(overlap_prefixes, key=lambda k: -swagger_prefix_stats[k])[:5]
                reason = ', '.join(top_overlap)
                confidence = '高' if ratio >= 0.5 else '中'
                return proj_name, reason, confidence, top_overlap

    return '未知', '', '低', []


def generate_per_project_report(proj_name, proj_dir, proj_data, swagger_results, all_swagger_files, output_dir):
    """生成单个源码项目的 Swagger 匹配报告"""
    proj_paths, ctrl_prefixes = proj_data
    api_count = len(proj_paths)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 该项目对应的 Swagger 模块
    proj_swagger = [r for r in swagger_results if r['matched_proj'] == proj_name]

    lines = [
        f"# {proj_name} — Swagger 模块匹配报告\n\n",
        f"> 生成时间: {now}\n",
        f"> Swagger 目录: `{SWAGGER_DIR}`\n",
        f"> 源码接口文档: `{proj_dir}/source-api-doc.md`\n\n",
        "---\n\n",
        "## 基本信息\n\n",
        f"| 项目 | 值 |\n",
        f"|------|-----|\n",
        f"| 源码接口数 | {api_count} |\n",
        f"| Controller 路径前缀数 | {len(ctrl_prefixes)} |\n",
        f"| 对应 Swagger 模块数 | {len(proj_swagger)} |\n",
        f"| Swagger 接口总数 | {sum(r['path_count'] for r in proj_swagger)} |\n\n",
    ]

    # 精确重叠数
    if proj_swagger:
        total_overlap = 0
        for r in proj_swagger:
            for sp in all_swagger_files:
                if sp.stem == r['name']:
                    sp_paths, _ = extract_paths_from_swagger(sp)
                    overlap = proj_paths & sp_paths
                    total_overlap += len(overlap)
                    break
        lines.append(f"| 精确路径重叠数（源码↔Swagger） | {total_overlap} |\n\n")

    if not proj_swagger:
        lines.append("⚠️ 无对应的 Swagger 模块（可能为外部系统接口）\n\n")
        output_path = output_dir / f"{proj_name}-swagger-match-report.md"
        output_path.write_text(''.join(lines), encoding='utf-8')
        return output_path

    # Swagger 模块详情表
    lines.append("## Swagger 模块匹配详情\n\n")
    lines.append("| # | Swagger 模块 | JSON 文件 | 大小 | 接口数 | 可信度 | 匹配说明 |\n")
    lines.append("|---|-------------|----------|------|--------|--------|----------|\n")
    for i, r in enumerate(sorted(proj_swagger, key=lambda x: -x['path_count']), 1):
        conf = {'高': '✅', '中': '🔶', '低': '❌'}.get(r['confidence'], '')
        json_file = f"`{r['name']}.json`"
        lines.append(
            f"| {i} | {r['name']} | {json_file} | {r['size_kb']:.0f}KB | "
            f"{r['path_count']} | {conf} | {r['reason']} |\n"
        )

    lines.append("\n")

    # 各模块 Swagger JSON 文件路径（供下游技能直接使用）
    lines.append("## Swagger JSON 文件列表（供下游技能使用）\n\n")
    lines.append("下游 `api-scanner-from-swagger` 技能应扫描以下文件：\n\n")
    for r in sorted(proj_swagger, key=lambda x: -x['path_count']):
        conf_emoji = {'高': '✅', '中': '🔶（建议人工核对）', '低': '❌（建议人工核对）'}.get(r['confidence'], '')
        lines.append(f"- `{SWAGGER_DIR}/{r['name']}.json` {conf_emoji}\n")
        lines.append(f"  - 接口数: {r['path_count']}，可信度: {r['confidence']}，匹配说明: {r['reason']}\n\n")

    # 源码路径前缀参考
    if ctrl_prefixes:
        lines.append("## 源码路径前缀参考\n\n")
        lines.append("> 下游技能可通过此前缀列表辅助判断接口归属\n\n")
        lines.append("| 路径前缀 | 接口数 |\n")
        lines.append("|---------|--------|\n")
        for pref, cnt in sorted(ctrl_prefixes.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| `{pref}` | {cnt} |\n")
        lines.append("\n")

    # 外部系统参考（该项目中可信度低的模块）
    low_conf = [r for r in proj_swagger if r['confidence'] != '高']
    if low_conf:
        lines.append("## ⚠️ 可信度说明\n\n")
        lines.append("以下模块可信度为中/低，建议人工核对是否真的属于本项目：\n\n")
        for r in low_conf:
            lines.append(f"- **{r['name']}** — {r['reason']}\n")
        lines.append("\n")

    output_path = output_dir / f"{proj_name}-swagger-match-report.md"
    output_path.write_text(''.join(lines), encoding='utf-8')
    return output_path


# ========== 主程序 ==========
def main():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    print("=== Swagger 模块匹配报告（按源码项目分拆）===\n")

    # 1. 收集源码项目数据
    source_proj_data = {}
    for proj_name, proj_dir in SOURCE_PROJECTS.items():
        paths, ctrl_prefixes = extract_paths_from_source_doc(proj_dir)
        source_proj_data[proj_name] = (paths, ctrl_prefixes)
        print(f"  [{proj_name}] 源码接口: {len(paths)}")

    # 2. 扫描 Swagger 文件并匹配
    swagger_files = [
        f for f in SWAGGER_DIR.glob("*.json")
        if f.name not in ['OpenAPI.json', 'swagger-original.json']
    ]
    print(f"  Swagger 模块文件: {len(swagger_files)} 个\n")

    swagger_results = []
    for fpath in sorted(swagger_files):
        size_kb = fpath.stat().st_size / 1024
        swagger_paths, swagger_prefix_stats = extract_paths_from_swagger(fpath)
        path_count = len(swagger_paths)

        if path_count == 0:
            swagger_results.append({
                'name': fpath.stem,
                'size_kb': size_kb,
                'path_count': 0,
                'matched_proj': '⚠️ 空文件',
                'reason': '',
                'confidence': '',
            })
            continue

        matched_proj, reason, confidence, _ = match_swagger_to_source(
            swagger_paths, swagger_prefix_stats, source_proj_data
        )

        swagger_results.append({
            'name': fpath.stem,
            'size_kb': size_kb,
            'path_count': path_count,
            'matched_proj': matched_proj,
            'reason': reason,
            'confidence': confidence,
        })

    # 3. 输出汇总
    print("匹配结果：")
    for proj_name in SOURCE_PROJECTS:
        matched = [r for r in swagger_results if r['matched_proj'] == proj_name]
        print(f"  [{proj_name}] → {len(matched)} 个 Swagger 模块")

    # 4. 生成每项目单独报告
    output_dir = SWAGGER_DIR.parent  # ~/Desktop/成果/
    generated = []
    for proj_name, proj_dir in SOURCE_PROJECTS.items():
        proj_data = source_proj_data[proj_name]
        output_path = generate_per_project_report(
            proj_name, proj_dir, proj_data, swagger_results, swagger_files, output_dir
        )
        size_kb = output_path.stat().st_size / 1024
        generated.append(output_path)
        print(f"  ✅ {output_path.name} ({size_kb:.1f} KB)")

    # 5. 汇总表
    print(f"\n{'='*60}")
    print(f"{'源码项目':<25} {'Swagger模块':>10} {'Swagger接口':>12} {'源码接口':>10}")
    print(f"{'-'*60}")
    for proj_name, (proj_paths, _) in source_proj_data.items():
        matched = [r for r in swagger_results if r['matched_proj'] == proj_name]
        total_swagger_apis = sum(r['path_count'] for r in matched)
        print(f"{proj_name:<25} {len(matched):>10} {total_swagger_apis:>12} {len(proj_paths):>10}")

    print(f"\n📄 已生成 {len(generated)} 份报告: {output_dir}")
    for p in generated:
        print(f"   {p.name}")


if __name__ == '__main__':
    main()
