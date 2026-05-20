---
name: api-fusion-engine
description: |
  融合源码接口文档（Skill 1）与 Swagger 样本数据（Skill 2），生成统一的最终接口文档 + 机器可读 JSON。
  
  触发词：融合接口文档、合并文档、生成最终文档、生成机器规范、接口融合、API融合、合并源码与Swagger、生成JSON规范
  场景：已有 source-api-doc.md（Skill 1）和 spec-samples.json（Skill 2），需要融合为一套完整文档时使用
  
  与其他技能区分：
  - api-scanner-from-source：第一阶段，从 Git 源码生成 source-api-doc.md（不是融合）
  - api-scanner-from-swagger：第一阶段，从 Swagger URL 生成 swagger-api-doc.md + spec-samples.json（不是融合）
  - api-fusion-engine：第二阶段，对已有两份文档进行融合（不是第一步）
triggers:
  - 融合接口文档
  - 合并文档
  - 生成最终文档
  - 生成机器规范
  - 接口融合
  - API融合
  - 合并源码与Swagger
  - 生成JSON规范
  - 综合接口文档
  - 最终接口文档
  - api-spec-machine
  - final-api-spec
scenarios:
  - 有 source-api-doc.md 和 spec-samples.json，需要融合输出最终版
  - 需要同时输出人类可读文档 + 机器可读 JSON
  - 需要统一认证信息、示例数据和源码定义的最终文档
  - 为 Skill 4（业务执行器）准备输入数据
constraints:
  - 只读操作，不修改源码
  - 依赖 source-api-doc.md（api-scanner-from-source 输出）
  - spec-samples.json 为可选（无 Swagger 时仅基于源码输出）
  - swagger-api-doc.md 为可选（用于交叉校验）
---

# api-fusion-engine

## 定位

**融合器** — 将 Skill 1（源码扫描）的深度接口定义与 Skill 2（Swagger 扫描）的实时样本数据融合，输出：

| 输出 | 说明 |
|------|------|
| `final-api-spec.md` | 最终接口文档（人类可读，含匹配验证报告 + 14+字段/接口） |
| `api-spec-machine.json` | 机器可读规范（Skill 4 直接使用，含匹配统计） |

**融合规则（优先级）：**

| 维度 | 来源优先级 |
|------|-----------|
| HTTP 路径 / Method | 源码（Swagger 交叉校验，不一致时警告） |
| 入参结构 / 字段类型 | 源码 |
| 🔶 隐藏/隐式参数 | 源码（api-scanner-from-source 已改） |
| 校验规则（@Valid / @NotNull） | 源码 |
| 业务逻辑 / 异常场景 | 源码（Service 层扫描） |
| 枚举值定义 | 源码 |
| 请求/响应示例 | **Swagger（spec-samples.json）** |
| Base URL + 端口 | **Swagger（spec-samples.json）** |
| 认证方式 | **Swagger（spec-samples.json）** |
| 字段描述 | 源码（@ApiModelProperty）> Swagger |

---

## 输入参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `SOURCE_API_DOC` | file | Skill 1 输出的源码接口文档（`source-api-doc.md`） | ✅ |
| `SOURCE_CODE` | string | 源码根目录（用于补全字段定义） | ❌ |
| `SPEC_SAMPLES_JSON` | file | Skill 2 输出的样本数据（`spec-samples.json`） | ❌ |
| `SWAGGER_API_DOC` | file | Skill 2 输出的 Swagger 文档（可选，交叉校验用） | ❌ |
| `SWAGGER_DIR` | string | Swagger JSON 模块目录（可选，用于模块名映射） | ❌ |
| `SOURCE_MATCH_REPORT` | file | swagger-source-matcher 输出的模块归属报告（可选） | ❌ |
| `OUTPUT_DIR` | string | 输出目录 | ❌（默认从 SOURCE_API_DOC 路径推导） |

> **说明**：SPEC_SAMPLES_JSON、SWAGGER_API_DOC、SOURCE_MATCH_REPORT 均为可选参数
> - **有 Swagger 样本** → 示例数据、base_url、auth 从 spec-samples.json 补充
> - **无 Swagger 样本** → 仅基于源码输出，示例占位
> - **有模块归属报告** → 在分析报告中展示 Swagger 模块与源码项目的匹配关系

---

## ⚠️ 负面指令（Do Not）

- **不要修改源码** — 仅读取分析
- **不要执行任何写操作到源码目录** — 只写入 OUTPUT_DIR
- **不要跳过环境检查** — Step 0 必须执行
- **不要直接执行 API 调用** — 本技能只做文档融合，不调接口

---

## 核心逻辑

### Step 0: 环境预检

```bash
#!/bin/bash
set -e

echo "[Step 0] 环境预检..."

# 检查源码接口文档
if [ ! -f "$SOURCE_API_DOC" ]; then
    echo "❌ 错误：源码接口文档不存在"
    echo "    提示：先运行 api-scanner-from-source 生成 source-api-doc.md"
    exit 1
fi

# 检查 spec-samples.json（可选）
HAS_SWAGGER=false
if [ -n "$SPEC_SAMPLES_JSON" ] && [ -f "$SPEC_SAMPLES_JSON" ]; then
    echo "  ✅ 检测到 Swagger 样本数据（spec-samples.json）"
    HAS_SWAGGER=true
else
    echo "  ⚠️  无 Swagger 样本数据，将仅基于源码输出"
fi

# 检查模块归属报告（可选）
HAS_MATCH_REPORT=false
if [ -n "$SOURCE_MATCH_REPORT" ] && [ -f "$SOURCE_MATCH_REPORT" ]; then
    echo "  ✅ 检测到模块归属报告（SOURCE_MATCH_REPORT）"
    HAS_MATCH_REPORT=true
else
    echo "  ⚠️  无模块归属报告，跳过模块匹配分析"
fi

# 检查 swagger-api-doc.md（可选，交叉校验用）
HAS_SWAGGER_API=false
if [ -n "$SWAGGER_API_DOC" ] && [ -f "$SWAGGER_API_DOC" ]; then
    echo "  ✅ 检测到 Swagger 接口文档（用于交叉校验）"
    HAS_SWAGGER_API=true
fi

# 检查 Swagger 模块目录（可选，模块名映射用）
if [ -n "$SWAGGER_DIR" ] && [ -d "$SWAGGER_DIR" ]; then
    echo "  ✅ 检测到 Swagger 模块目录: $SWAGGER_DIR"
else
    echo "  ℹ️  未配置 SWAGGER_DIR，模块名映射跳过"
fi

# 设置输出目录
OUTPUT_DIR="${OUTPUT_DIR:-$(dirname "$SOURCE_API_DOC")}/fusion"
mkdir -p "$OUTPUT_DIR"
echo "  ✅ 输出目录: $OUTPUT_DIR"

# 检查 python3
command -v python3 &> /dev/null || { echo "❌ 未找到 python3"; exit 1; }
echo "  ✅ python3 存在"

echo "[Step 0] ✅ 环境检查通过"
```

> 📢 **Step 0 报告**：检测到文档数量、是否有 Swagger、输出目录

### Step 1: 融合生成（核心）

```python
#!/usr/bin/env python3
"""
融合器主逻辑
读取 source-api-doc.md（Skill 1）+ spec-samples.json（Skill 2）
输出 final-api-spec.md + api-spec-machine.json
"""

import json
import os
import re
from datetime import datetime

SOURCE_API_DOC = "${SOURCE_API_DOC}"
SPEC_SAMPLES_JSON = "${SPEC_SAMPLES_JSON:-}"
SWAGGER_API_DOC = "${SWAGGER_API_DOC:-}"
SWAGGER_DIR = "${SWAGGER_DIR:-}"
OUTPUT_DIR = "${OUTPUT_DIR}"
HAS_SWAGGER = ${HAS_SWAGGER:-false}
HAS_SWAGGER_API = ${HAS_SWAGGER_API:-false}
HAS_MATCH_REPORT = ${HAS_MATCH_REPORT:-false}
SOURCE_MATCH_REPORT = "${SOURCE_MATCH_REPORT:-}"


# ============================================================
# 工具函数
# ============================================================

def build_module_map():
    """
    扫描 SWAGGER_DIR 中各模块 JSON，建立 路径前缀 → Swagger 模块名 的映射。
    供 bias="swagger" 输出时使用。
    """
    module_map = {}
    if not SWAGGER_DIR or not os.path.isdir(SWAGGER_DIR):
        print('  ⚠️  SWAGGER_DIR 未配置或不存在，跳过模块映射')
        return module_map

    import glob as _glob
    json_files = _glob.glob(os.path.join(SWAGGER_DIR, '*.json'))
    for fpath in json_files:
        fname = os.path.basename(fpath)
        if fname in ('OpenAPI.json', 'swagger-original.json'):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
        except:
            continue
        if not isinstance(data, dict):
            continue
        module_name = os.path.splitext(fname)[0]
        paths = data.get('paths', {})
        for p in paths.keys():
            parts = p.strip('/').split('/')
            key = parts[0] + '/' + parts[1] if len(parts) >= 2 else (parts[0] if parts else None)
            if key and key not in module_map:
                module_map[key] = module_name
        print(f'    indexed {fname} ({len(paths)} paths)')
    print(f'  ✅ 模块映射建成: {len(module_map)} 个路径前缀')
    return module_map


def simple_type(t):
    """简化类型名"""
    if not t:
        return 'unknown'
    for prefix in ['java.lang.', 'java.util.', 'java.io.', 'java.math.',
                   'caij.boot.core.', 'caij.boot.pub.', 'caij.boot.system.',
                   'java.time.']:
        t = t.replace(prefix, '')
    t = re.sub(r'ArrayList<(.+?)>', r'\1[]', t)
    t = re.sub(r'List<(.+?)>', r'\1[]', t)
    t = re.sub(r'Map<.+?,\s*(.+?)>', r'map<\1>', t)
    return t


def extract_header(endpoint):
    """从端点路径推导 HEADER 参数（项目约定：Org-Id, Group-Id, User-Id）"""
    base = set()
    # 通用 Header
    if any(k in endpoint.lower() for k in ['/auth/', '/login', '/token']):
        return []
    base.append({'name': 'Token', 'type': 'string', 'required': True, 'description': '认证 Token（需先调用登录接口获取）'})
    base.append({'name': 'Org-Id', 'type': 'string', 'required': False, 'description': '组织 ID'})
    base.append({'name': 'Group-Id', 'type': 'string', 'required': False, 'description': '集团 ID'})
    base.append({'name': 'User-Id', 'type': 'string', 'required': False, 'description': '用户 ID'})
    return base


# ============================================================
# 加载 Swagger 样本数据
# ============================================================

def load_swagger_samples():
    """加载 spec-samples.json"""
    if not HAS_SWAGGER or not SPEC_SAMPLES_JSON or not os.path.exists(SPEC_SAMPLES_JSON):
        return {}

    with open(SPEC_SAMPLES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按 path+method 建立索引
    indexed = {}
    apis = data.get('apis', {})
    if isinstance(apis, list):
        for api in apis:
            key = f"{api['method'].upper()} {api['path']}"
            indexed[key] = api
    elif isinstance(apis, dict):
        indexed = apis
    return {
        'base_url': data.get('base_url', ''),
        'auth': data.get('auth', {}),
        'project': data.get('project', ''),
        'apis': indexed
    }


# ============================================================
# 解析 source-api-doc.md
# ============================================================

# ============================================================
# 预匹配验证（Step 1.5）
# ============================================================

def validate_match(source_doc, swagger_data):
    """
    预匹配验证：逐接口对比源码路径 vs Swagger 路径
    输出匹配率、差异清单、参数结构对比
    """
    source_apis = {}
    for ctrl_name, methods in source_doc.get('controllers', {}).items():
        for method in methods:
            key = f"{method['method']} {method['path']}"
            source_apis[key] = {
                'controller': ctrl_name,
                'method': method['method'],
                'path': method['path'],
                'params': method.get('params', []),
                'request_body_type': method.get('request_body_type', '')
            }

    swagger_apis = swagger_data.get('apis', {})
    swagger_flat = {}
    for key, api in swagger_apis.items():
        swagger_flat[key] = api

    # 统计
    exact_match = []  # 完全匹配
    source_only = []  # 源码有，Swagger 无
    swagger_only = []  # Swagger 有，源码无
    param_diff = []  # 路径匹配但参数结构不一致

    for s_key, s_api in source_apis.items():
        if s_key in swagger_flat:
            # 路径完全匹配
            sw_api = swagger_flat[s_key]
            # 对比入参结构
            source_body_type = s_api.get('request_body_type', '')
            swagger_body = sw_api.get('example_request', {}).get('body', {})
            has_swagger_body = bool(swagger_body)
            if source_body_type and not has_swagger_body:
                param_diff.append({'api': s_key, 'issue': f'源码有 body 类型 {source_body_type}，但 Swagger 样本中无 body 示例'})
            exact_match.append(s_key)
        else:
            source_only.append(s_key)

    for sw_key in swagger_flat.keys():
        if sw_key not in source_apis:
            swagger_only.append(sw_key)

    total_source = len(source_apis)
    total_swagger = len(swagger_flat)
    match_rate = len(exact_match) / total_source * 100 if total_source > 0 else 0

    report = {
        'total_source': total_source,
        'total_swagger': total_swagger,
        'exact_match': exact_match,
        'match_count': len(exact_match),
        'match_rate': match_rate,
        'source_only': source_only,
        'source_only_count': len(source_only),
        'swagger_only': swagger_only,
        'swagger_only_count': len(swagger_only),
        'param_diffs': param_diff,
        'param_diff_count': len(param_diff)
    }

    return report


def print_match_report(report):
    """打印匹配验证报告"""
    print('\n' + '='*60)
    print('📊 Step 1.5: 匹配验证报告')
    print('='*60)
    print(f'  \n  源码接口数: {report["total_source"]}')
    print(f'  Swagger 接口数: {report["total_swagger"]}')
    print(f'  \n  ✅ 完全匹配: {report["match_count"]} ({report["match_rate"]:.1f}%)')
    print(f'  ⚠️  源码独有（Swagger 无）: {report["source_only_count"]}')
    print(f'  👻 Swagger 独有（源码无）: {report["swagger_only_count"]}')
    print(f'  🔄 参数结构差异: {report["param_diff_count"]}')

    if report['source_only_count'] > 0:
        print(f'\n  --- 源码独有接口（前10个）---')
        for api in report['source_only'][:10]:
            print(f'    ⚠️  {api}')

    if report['swagger_only_count'] > 0:
        print(f'\n  --- Swagger 独有接口（前10个）---')
        for api in report['swagger_only'][:10]:
            print(f'    👻  {api}')

    if report['param_diff_count'] > 0:
        print(f'\n  --- 参数结构差异（前5个）---')
        for d in report['param_diffs'][:5]:
            print(f'    🔄  {d["api"]}: {d["issue"]}')

    print('='*60 + '\n')


def parse_source_doc():
    """解析 source-api-doc.md，从索引表提取完整路径"""
    with open(SOURCE_API_DOC, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    full_content = ''.join(lines)

    result = {
        'project': '',
        'base_url': '',
        'auth': {},
        'controllers': {}
    }

    # 从索引表提取全路径映射: | N | `/full/path` | Method | ...
    index_entries = []
    for m in re.finditer(r'^| \d+ | `(/[/\w\.\-\{\}]+)` | (Get|Post|Put|Delete|Patch) |', full_content, re.MULTILINE):
        index_entries.append({'path': m.group(1), 'method': m.group(2).upper()})

    current_controller = None
    current_method = None
    in_implicit_section = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Controller 名称行
        cm = re.match(r'^## 🔷 (\w+)', line)
        if cm:
            current_controller = cm.group(1)
            result['controllers'][current_controller] = []
            i += 1
            continue

        # 项目名（第一行 # xxx 接口文档）
        pm = re.match(r'^# (.+?) 接口文档', line)
        if pm:
            result['project'] = pm.group(1)
            i += 1
            continue

        # API 行：### GET|POST|PUT|DELETE /path
        am = re.match(r'^### (GET|POST|PUT|DELETE|PATCH)\s+(/?(?:[/\w\.\-\{\}]+))', line)
        if am:
            rel_path = am.group(2)
            full_path = rel_path
            for entry in index_entries:
                if entry['method'] == am.group(1) and entry['path'].endswith(rel_path):
                    full_path = entry['path']
                    break
            current_method = {
                'method': am.group(1),
                'path': full_path,
                'full_path': full_path,
                'description': '',
                'params': [],
                'implicit_params': [],
                'request_body_type': '',
                'return_type': 'Result',
                'auth': '',
                'valid': '',
                'service_exception': ''
            }
            in_implicit_section = False
            if current_controller:
                result['controllers'][current_controller].append(current_method)
            i += 1
            continue

        # 接口描述
        dm = re.match(r'^\*\*接口描述：\*\*(.*)', line)
        if dm and current_method:
            current_method['description'] = dm.group(1).strip()

        # 接口权限
        auth_m = re.match(r'^\*\*接口权限：\*\*(.*)', line)
        if auth_m and current_method:
            current_method['auth'] = auth_m.group(1).strip()

        # 业务规则
        valid_m = re.match(r'^\*\*业务规则：\*\*(.*)', line)
        if valid_m and current_method:
            current_method['valid'] = valid_m.group(1).strip()

        # 🔶 隐式参数区块
        if current_method and '🔶 隐式参数' in line:
            in_implicit_section = True
            i += 1
            continue

        # 隐式参数表格行
        if in_implicit_section and current_method and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5:
                current_method['implicit_params'].append({
                    'name': parts[1],
                    'type': parts[2],
                    'description': parts[4]
                })
            i += 1
            continue

        # 离开隐式参数区
        if in_implicit_section and (line.startswith('**') or line.startswith('#')):
            in_implicit_section = False

        # Body 参数表格（位置为 Body 的行）
        bm = re.match(r'^\|\s*Body\s*\|', line)
        if bm and current_method:
            # | Body | fieldName | String | 是 | 描述 | ...
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                current_method['params'].append({
                    'name': parts[2],
                    'type': simple_type(parts[3]),
                    'in': 'body',
                    'required': parts[4],
                    'description': parts[5].replace('⚠️ ', '').strip()
                })
            i += 1
            continue

        # Path 参数
        ppm = re.match(r'^\|\s*Path\s*\|', line)
        if ppm and current_method:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                current_method['params'].append({
                    'name': parts[2],
                    'type': simple_type(parts[3]),
                    'in': 'path',
                    'required': parts[4],
                    'description': parts[5].replace('⚠️ ', '').strip()
                })
            i += 1
            continue

        # Query 参数
        qm = re.match(r'^\|\s*Query\s*\|', line)
        if qm and current_method:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                current_method['params'].append({
                    'name': parts[2],
                    'type': simple_type(parts[3]),
                    'in': 'query',
                    'required': parts[4],
                    'description': parts[5].replace('⚠️ ', '').strip()
                })
            i += 1
            continue

        # 入参类型
        rt = re.match(r'^\*\*入参类型：\*\*\s*`(\w+)`', line)
        if rt and current_method:
            current_method['request_body_type'] = rt.group(1)
            i += 1
            continue

        i += 1

    return result


# ============================================================
# 融合逻辑
# ============================================================

def fuse(source_doc, swagger_data):
    """融合源码定义 + Swagger 样本数据"""

    base_url = swagger_data.get('base_url', '')
    auth = swagger_data.get('auth', {})
    swagger_apis = swagger_data.get('apis', {})
    swagger_project = swagger_data.get('project', '')

    # 统计
    total_apis = 0
    fusion_stats = {'matched_samples': 0, 'unmatched_apis': 0, 'swagger_only': 0}

    fused_apis = []

    for ctrl_name, methods in source_doc.get('controllers', {}).items():
        for method in methods:
            total_apis += 1
            key = f"{method['method']} {method['path']}"

            # 查找对应的 Swagger 样本
            swagger_api = swagger_apis.get(key, {})

            api_entry = {
                'controller': ctrl_name,
                'method': method['method'],
                'path': method['path'],
                'description': method.get('description', '⚠️ **[待补充]**'),
                'params': method.get('params', []),
                'implicit_params': method.get('implicit_params', []),
                'request_body_type': method.get('request_body_type', ''),
                'return_type': method.get('return_type', 'Result'),
                'auth_required': method.get('auth', ''),
                'valid_required': method.get('valid', ''),
                'service_exception': method.get('service_exception', ''),
                'headers': extract_header(method['path']),
                # 来自 Swagger 的补充数据
                'example_request': swagger_api.get('example_request', {}),
                'example_response': swagger_api.get('example_response', {})
            }

            if swagger_api:
                fusion_stats['matched_samples'] += 1
            else:
                fusion_stats['unmatched_apis'] += 1

            fused_apis.append(api_entry)

    # 补充：Swagger 有但源码没有的接口（幽灵接口）
    for key, swagger_api in swagger_apis.items():
        found = False
        for api in fused_apis:
            if f"{api['method']} {api['path']}" == key:
                found = True
                break
        if not found:
            fusion_stats['swagger_only'] += 1
            fused_apis.append({
                'controller': '（Swagger 独有）',
                'method': swagger_api.get('method', ''),
                'path': swagger_api.get('path', ''),
                'description': swagger_api.get('description', '（Swagger 独有接口，源码无对应）'),
                'params': [],
                'implicit_params': [],
                'request_body_type': '',
                'return_type': 'Result',
                'auth_required': '',
                'valid_required': '',
                'service_exception': '',
                'headers': extract_header(swagger_api.get('path', '')),
                'example_request': swagger_api.get('example_request', {}),
                'example_response': swagger_api.get('example_response', {})
            })

    return {
        'project': source_doc.get('project') or swagger_project,
        'base_url': base_url,
        'auth': auth,
        'total_apis': len(fused_apis),
        'fusion_stats': fusion_stats,
        'apis': fused_apis
    }


# ============================================================
# 输出 api-spec-machine.json
# ============================================================

def output_machine_json(fused, output_path, bias="swagger", module_map=None):
    """
    输出机器可读 JSON
    bias="swagger": 按 Swagger 模块分组（适合 AI 调用 API）
    bias="source":  按 Controller 扁平列表（兼容旧结构）
    """
    enums = {}
    entities = {}

    def module_from_path(path):
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            return parts[0] + '/' + parts[1]
        return parts[0] if parts else 'other'

    if bias == "swagger":
        # 按模块分组（优先用 module_map 将路径前缀转为业务模块名）
        _mmap = module_map or {}
        modules = {}
        module_order = []
        for api in fused['apis']:
            mod = module_from_path(api['path'])
            swg_mod = _mmap.get(mod, mod)  # /mom/costing/ → "生产成本核算模块"
            if swg_mod not in modules:
                modules[swg_mod] = []
                module_order.append(swg_mod)
            modules[mod].append({
                'method': api['method'],
                'path': api['path'],
                'description': api['description'],
                'headers': api['headers'],
                'params': api['params'],
                'request_body_type': api['request_body_type'],
                'return_type': api['return_type'],
                'auth_required': bool(api['auth_required']),
                'valid_required': bool(api['valid_required']),
                'controller': api['controller'],
                'service_exception': api['service_exception'],
                'example_request': api['example_request'],
                'example_response': api['example_response']
            })
        machine = {
            'version': '2.0',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'project': fused['project'],
            'base_url': fused['base_url'],
            'auth': fused['auth'],
            'enums': enums,
            'entities': entities,
            'match_stats': fused.get('match_report', None),
            'modules': modules,
            'module_order': module_order
        }
    else:
        # 按 Controller 扁平列表（原逻辑）
        machine = {
            'version': '1.0',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'project': fused['project'],
            'base_url': fused['base_url'],
            'auth': fused['auth'],
            'enums': enums,
            'entities': entities,
            'match_stats': fused.get('match_report', None),
            'apis': []
        }
        for api in fused['apis']:
            machine['apis'].append({
                'controller': api['controller'],
                'method': api['method'],
                'path': api['path'],
                'description': api['description'],
                'headers': api['headers'],
                'params': api['params'],
                'implicit_params': api['implicit_params'],
                'request_body_type': api['request_body_type'],
                'return_type': api['return_type'],
                'auth_required': bool(api['auth_required']),
                'valid_required': bool(api['valid_required']),
                'service_exception': api['service_exception'],
                'example_request': api['example_request'],
                'example_response': api['example_response']
            })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(machine, f, ensure_ascii=False, indent=2)
    count = len(fused['apis'])
    print(f'  ✅ api-spec-machine.json 已生成 ({count} 个接口, bias="{bias}")')


# ============================================================
# 输出 final-api-spec.md
# ============================================================

def output_human_doc(fused, output_path, bias="source"):
    """输出人类可读的最终接口文档（bias="source" 按 Controller 组织，不变）"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {fused['project']} 接口文档（融合版）\n\n")

        # ========== 一、分析报告 ==========
        f.write("\n---\n\n## 一、分析报告\n\n")

        # 模块概况
        ctrl_names = set()
        ctrl_count = {}
        for api in fused['apis']:
            c = api.get('controller', '未分组')
            ctrl_names.add(c)
            ctrl_count[c] = ctrl_count.get(c, 0) + 1
        f.write("### 1.1 模块概况\n\n")
        f.write(f"| 项目 | 值 |\n")
        f.write(f"|------|----|\n")
        f.write(f"| 项目名称 | {fused['project']} |\n")
        f.write(f"| 接口总数 | {fused['total_apis']} 个 |\n")
        f.write(f"| Controller 数 | {len(ctrl_names)} 个 |\n")
        if fused.get('base_url'):
            f.write(f"| 服务地址 | `{fused['base_url']}` |\n")
        if fused.get('auth', {}).get('type'):
            f.write(f"| 认证方式 | {fused['auth']['type']} |\n")
        f.write("\n")

        # 主要业务功能
        f.write("### 1.2 主要业务功能\n\n")
        f.write("| Controller | 接口数 | 业务说明 |\n")
        f.write("|------------|:------:|----------|\n")
        for c in sorted(ctrl_names):
            api_count = ctrl_count.get(c, 0)
            # 从 controller 名称推导业务说明
            biz_desc = c.replace('Controller', '')
            # 中文前缀映射
            biz_desc = biz_desc.replace('Bd', '基础数据-')
            biz_desc = biz_desc.replace('Sys', '系统-')
            biz_desc = biz_desc.replace('Oa', 'OA-')
            biz_desc = biz_desc.replace('St', '库存-')
            # 驼峰转中文
            import re as _re
            readable = _re.sub(r'([a-z])([A-Z])', r'\1 \2', biz_desc)
            f.write(f"| {c} | {api_count} | {readable}管理 |\n")
        f.write("\n")

        # 匹配验证报告
        match_report = fused.get('match_report', None)
        if match_report:
            f.write("### 1.3 接口匹配验证\n\n")
            f.write(f"| 指标 | 数量 |\n")
            f.write(f"|------|:----:|\n")
            f.write(f"| 源码接口数 | {match_report['total_source']} |\n")
            f.write(f"| Swagger 接口数 | {match_report['total_swagger']} |\n")
            f.write(f"| ✅ 完全匹配 | {match_report['match_count']} ({match_report['match_rate']:.1f}%) |\n")
            f.write(f"| ⚠️ 源码独有（Swagger 无） | {match_report['source_only_count']} |\n")
            f.write(f"| 👻 Swagger 独有（源码无） | {match_report['swagger_only_count']} |\n")
            f.write(f"| 🔄 参数结构差异 | {match_report['param_diff_count']} |\n\n")

            if match_report['source_only']:
                f.write("**⚠️ 源码独有接口**\n\n")
                f.write("| 接口 | 说明 |\n")
                f.write("|------|------|\n")
                for api in match_report['source_only']:
                    f.write(f"| `{api}` | 源码有，Swagger 无样本数据 |\n")
                f.write("\n")

            if match_report['swagger_only']:
                f.write("**👻 Swagger 独有接口**\n\n")
                f.write("| 接口 | 说明 |\n")
                f.write("|------|------|\n")
                for api in match_report['swagger_only']:
                    f.write(f"| `{api}` | Swagger 有样本，但源码中无此接口 |\n")
                f.write("\n")

            if match_report['param_diffs']:
                f.write("**🔄 参数结构差异**\n\n")
                f.write("| 接口 | 差异说明 |\n")
                f.write("|------|-----------|\n")
                for d in match_report['param_diffs']:
                    f.write(f"| `{d['api']}` | {d['issue']} |\n")
                f.write("\n")

        # 模块与 Swagger 归属匹配
        source_match_data = fused.get('source_match_data', {})
        if source_match_data:
            f.write("### 1.4 模块与 Swagger 归属匹配\n\n")
            if 'raw_text' in source_match_data:
                # 文本格式报告
                lines = source_match_data['raw_text'].split('\n')
                f.write("```\n")
                for line in lines[:50]:
                    # Remove ANSI escape codes if any
                    import re as _ansire
                    clean = _ansire.sub(r'\x1b\[[0-9;]*[mK]', '', line)
                    f.write(clean + "\n")
                f.write("```\n")
            else:
                # JSON 格式报告
                for swagger_mod, info in source_match_data.items():
                    if swagger_mod == 'summary':
                        continue
                    f.write(f"**Swagger 模块：{swagger_mod}**\n\n")
                    f.write(f"| 项目 | 值 |\n")
                    f.write(f"|------|----|\n")
                    if isinstance(info, dict):
                        f.write(f"| 匹配源码项目 | {info.get('matched_project', '未知')} |\n")
                        f.write(f"| 置信度 | {info.get('confidence', '未知')} |\n")
                        f.write(f"| 精确匹配数 | {info.get('exact_match_count', 'N/A')} |\n")
                        f.write(f"| 前缀匹配率 | {info.get('prefix_match_rate', 'N/A')} |\n")
                    f.write("\n")
            f.write("\n")

        # 认证说明
        auth = fused.get('auth', {})
        if auth.get('login_url'):

        # 重新编号 1.4 → 1.5
            f.write("### 1.5 认证方式\n\n")
            f.write(f"| 项目 | 说明 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 类型 | {auth.get('type', 'unknown')} |\n")
            f.write(f"| 登录接口 | {auth.get('method', 'POST')} {auth['login_url']} |\n")
            f.write(f"| 请求体 | {json.dumps(auth.get('login_body', {}), ensure_ascii=False)} |\n")
            f.write(f"| Token 字段 | `{auth.get('token_field', 'data.token')}` |\n\n")
            f.write("**调用流程：**\n\n")
            f.write(f"1. 调用 {auth.get('method', 'POST')} `{auth['login_url']}` 获取 token\n")
            f.write(f"2. 后续请求在 Header 中携带 `Token: {{{{token}}}}`\n\n")

        f.write("---\n\n## 二、接口详情\n\n")
        f.write(f"| 属性 | 值 |\n")
        f.write(f"|------|----|\n")
        f.write(f"| 生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |\n")
        f.write(f"| 接口总数 | {fused['total_apis']} |\n")
        if fused['base_url']:
            f.write(f"| 服务地址 | `{fused['base_url']}` |\n")
        if fused['auth'].get('login_url'):
            f.write(f"| 登录接口 | `{fused['auth']['method']} {fused['auth']['login_url']}` |\n")
            f.write(f"| Token 字段 | `{fused['auth']['token_field']}` |\n")
        f.write("\n---\n\n")



        # 接口索引
        f.write("## 📋 接口索引表\n\n")
        f.write("| # | 接口路径 | HTTP | 名称 | 入参 | 出参 | 有样本 |\n")
        f.write("|---|----------|------|------|------|------|:------:|\n")
        for idx, api in enumerate(fused['apis'], 1):
            desc = api['description']
            if len(desc) > 30:
                desc = desc[:27] + '...'
            req_type = api['request_body_type'] or api.get('params', [{}])[0].get('name', '-') if api.get('params') else '-'
            resp_type = api['return_type'] or '-'
            has_sample = '✅' if api.get('example_request', {}).get('body') or api.get('example_request', {}).get('query') else '❌'
            f.write(f"| {idx} | `{api['path']}` | {api['method']} | {desc} | {req_type} | {resp_type} | {has_sample} |\n")
        f.write("\n---\n\n")

        # 按 Controller 分组，详细接口
        controllers = {}
        for api in fused['apis']:
            ctrl = api.get('controller', '未分组')
            if ctrl not in controllers:
                controllers[ctrl] = []
            controllers[ctrl].append(api)

        for ctrl_name, apis in controllers.items():
            f.write(f"## 🔷 {ctrl_name}\n\n")
            for api in apis:
                desc = api.get('description', '⚠️ **[待补充]**')
                f.write(f"### {api['method']} {api['path']}\n\n")
                f.write(f"**接口描述：** {desc}\n\n")
                if api.get('auth_required'):
                    f.write(f"**接口权限：** {api['auth_required']}\n\n")
                if api.get('valid_required'):
                    f.write(f"**业务规则：** {api['valid_required']}\n\n")

                # ---- 1. 入参信息 ----
                f.write("**1. 入参信息**\n\n")

                body_params = [p for p in api.get('params', []) if p.get('in') == 'body']
                path_params = [p for p in api.get('params', []) if p.get('in') == 'path']
                query_params = [p for p in api.get('params', []) if p.get('in') == 'query']
                implicit_params = api.get('implicit_params', [])

                # Header 参数
                headers = api.get('headers', [])
                if headers:
                    f.write("**Header 参数**\n\n")
                    f.write("| 字段名 | 类型 | 必填 | 说明 |\n")
                    f.write("|--------|------|:----:|------|\n")
                    for h in headers:
                        f.write(f"| {h['name']} | {h['type']} | {'是' if h['required'] else '否'} | {h['description']} |\n")
                    f.write("\n")

                if api.get('request_body_type'):
                    f.write(f"**入参类型：** `{api['request_body_type']}`\n\n")
                    if body_params:
                        f.write("| 位置 | 字段名 | 类型 | 必填 | 描述 |\n")
                        f.write("|------|--------|------|:----:|------|\n")
                        for p in body_params:
                            f.write(f"| Body | {p['name']} | {p['type']} | {p.get('required', '否')} | {p.get('description', '')} |\n")
                        f.write("\n")

                if path_params:
                    f.write("| 位置 | 字段名 | 类型 | 描述 |\n")
                    f.write("|------|--------|------|------|\n")
                    for p in path_params:
                        f.write(f"| Path | {p['name']} | {p['type']} | {p.get('description', '')} |\n")
                    f.write("\n")

                if query_params:
                    f.write("| 位置 | 字段名 | 类型 | 必填 | 描述 |\n")
                    f.write("|------|--------|------|:----:|------|\n")
                    for p in query_params:
                        f.write(f"| Query | {p['name']} | {p['type']} | {p.get('required', '否')} | {p.get('description', '')} |\n")
                    f.write("\n")

                if not body_params and not path_params and not query_params and not implicit_params:
                    rb_type = api.get("request_body_type", "")
                    if rb_type:
                        f.write(f'**入参类型：** `{rb_type}`\n\n> ⚠️ 具体字段定义请参考 Swagger 文档\n\n')
                    else:
                        f.write("*无显式参数，请参考 Swagger 文档*\n\n")

                # 🔶 隐式参数
                if implicit_params:
                    f.write("**🔶 隐式参数（框架注入，不体现在请求体）**\n\n")
                    f.write("| 字段名 | 类型 | 来源 | 说明 |\n")
                    f.write("|--------|------|:----:|------|\n")
                    for p in implicit_params:
                        desc_text = p.get('description', '')
                        source = 'Spring MVC'
                        if 'Header' in desc_text:
                            source = 'Header'
                        elif 'Cookie' in desc_text:
                            source = 'Cookie'
                        elif 'Security' in desc_text:
                            source = 'Security'
                        elif '配置' in desc_text:
                            source = 'Config'
                        f.write(f"| {p['name']} | {p['type']} | {source} | {desc_text} |\n")
                    f.write("\n")

                # ---- 2. 出参信息 ----
                f.write("**2. 出参信息**\n\n")
                ret_type = api.get('return_type', 'Result') or 'Result'
                f.write(f"**返回类型：** `{ret_type}`\n\n")
                f.write("| 字段名 | 类型 | 描述 |\n")
                f.write("|--------|------|------|\n")
                f.write("| code | Integer | 响应状态码（200 成功） |\n")
                f.write("| msg | String | 响应提示信息 |\n")
                f.write("| data | Object | 业务数据 |\n")
                f.write("| timestamp | Long | 时间戳 |\n")
                f.write("\n")

                # ---- 3. 示例数据（来自 Swagger） ----
                f.write("**3. 示例数据**\n\n")
                f.write("**请求示例：**\n```\n")
                req_example = api.get('example_request', {})
                qs = req_example.get('query', {})
                qs_str = '&'.join([f'{k}={v}' for k, v in qs.items()]) if qs else ''
                url = api['path']
                if qs_str:
                    url += f'?{qs_str}'
                f.write(f"{api['method']} {url} HTTP/1.1\n")
                f.write(f"Host: {fused.get('base_url', '').replace('https://', '').replace('http://', '') if fused.get('base_url') else 'localhost'}\n")
                f.write("Content-Type: application/json;charset=UTF-8\n")
                if api.get('auth_required') or fused.get('auth', {}).get('login_url'):
                    f.write("Token: eyJhbGciOiJIUzI1NiJ9...\n")
                f.write("\n")
                body = req_example.get('body', {})
                if body:
                    f.write(json.dumps(body, ensure_ascii=False, indent=2) + '\n')
                else:
                    f.write('{}\n')
                f.write("```\n\n")

                f.write("**成功响应示例：**\n```json\n")
                resp = api.get('example_response', {})
                if resp:
                    f.write(json.dumps(resp, ensure_ascii=False, indent=2) + '\n')
                else:
                    f.write('{\n  "code": 200,\n  "msg": "操作成功",\n  "data": {},\n  "timestamp": 1714525200000\n}\n')
                f.write("```\n\n")

                # ---- 4. 异常场景说明 ----
                f.write("**4. 异常场景说明**\n\n")
                f.write("| 异常场景 | 响应码 | 提示信息 | 解决方案 |\n")
                f.write("|----------|:------:|----------|----------|\n")
                f.write("| 入参缺失 | 400 | 参数错误：XXX不能为空 | 补充必填参数 |\n")
                f.write("| 资源不存在 | 404 | 资源不存在 | 核对 ID 后重试 |\n")
                f.write("| 权限不足 | 403 | 无操作权限 | 申请对应权限 |\n")
                f.write("| 服务器内部错误 | 500 | 服务器异常 | 联系管理员 |\n")
                if api.get('service_exception'):
                    f.write(f"| 业务异常 | - | {api['service_exception']} | - |\n")
                f.write("\n---\n\n")

    print(f'  ✅ final-api-spec.md 已生成')


# ============================================================
# 主流程
# ============================================================

def main():
    print("[Step 1] 加载源码文档...")
    source_doc = parse_source_doc()
    source_apis = sum(len(v) for v in source_doc.get('controllers', {}).values())
    print(f'   解析到 {source_apis} 个接口, {len(source_doc.get("controllers", {}))} 个 Controller')

    swagger_data = {}
    if HAS_SWAGGER:
        print("[Step 1] 加载 Swagger 样本数据...")
        swagger_data = load_swagger_samples()
        swagger_apis = len(swagger_data.get('apis', {}))
        if swagger_data.get('base_url'):
            print(f'   Base URL: {swagger_data[\"base_url\"]}')
        if swagger_data.get('auth', {}).get('login_url'):
            print(f'   认证接口: {swagger_data[\"auth\"][\"method\"]} {swagger_data[\"auth\"][\"login_url\"]}')
        print(f'   样本数据: {swagger_apis} 个接口')

    # ========== Step 1.5: 预匹配验证 ==========
    source_match_data = {}
    if HAS_MATCH_REPORT and os.path.exists(SOURCE_MATCH_REPORT):
        print("[Step 1.5] 加载模块归属报告...")
        import json as _json
        try:
            with open(SOURCE_MATCH_REPORT, 'r', encoding='utf-8') as _f:
                raw = _f.read()
            # 尝试解析 JSON，如果失败则读取纯文本
            if raw.strip().startswith('{'):
                source_match_data = _json.loads(raw)
            else:
                source_match_data = {'raw_text': raw[:5000]}
            print(f'   模块归属报告已加载')
        except Exception as e:
            print(f'   ⚠️ 模块归属报告加载失败: {e}')

    if HAS_SWAGGER:
        print("[Step 1.5] 预匹配验证...")
        match_report = validate_match(source_doc, swagger_data)
        print_match_report(match_report)

        print(f'   ✅ 匹配率: {match_report["match_count"]}/{match_report["total_source"]} ({match_report["match_rate"]:.1f}%)')
        if match_report['source_only_count'] > 0:
            print(f'   ⚠️  源码独有: {match_report["source_only_count"]} 个')
        if match_report['swagger_only_count'] > 0:
            print(f'   👻 Swagger 独有: {match_report["swagger_only_count"]} 个')
        if match_report['param_diff_count'] > 0:
            print(f'   🔄 参数差异: {match_report["param_diff_count"]} 项')

    print("[Step 2] 融合中...")
    fused = fuse(source_doc, swagger_data)

    # 将匹配报告和模块归属数据附加到 fused 中
    if HAS_SWAGGER:
        fused['match_report'] = match_report
    if source_match_data:
        fused['source_match_data'] = source_match_data

    print(f'   融合接口总数: {fused["total_apis"]}')
    print(f'   匹配 Swagger 样本: {fused["fusion_stats"]["matched_samples"]}')
    print(f'   源码独有: {fused["fusion_stats"]["unmatched_apis"]}')
    print(f'   Swagger 独有: {fused["fusion_stats"]["swagger_only"]}')

    print("[Step 3] 输出机器可读 JSON（偏向 Swagger 模块分组）...")
    _module_map = build_module_map()
    output_machine_json(fused, os.path.join(OUTPUT_DIR, 'api-spec-machine.json'), bias="swagger", module_map=_module_map)

    print("[Step 4] 输出人类可读文档（偏向源码 Controller 组织）...")
    output_human_doc(fused, os.path.join(OUTPUT_DIR, 'final-api-spec.md'), bias="source")
    try:
        output_html_doc(os.path.join(OUTPUT_DIR, 'final-api-spec.md'))
    except Exception as _e:
        print(f'  ⚠️ HTML 生成跳过: {_e}')

    print(f"\n✅ 融合完成！输出目录: {OUTPUT_DIR}")
    print(f"   人类可读: final-api-spec.md")
    print(f"   机器可读: api-spec-machine.json")
    print(f"   HTML: final-api-spec.html")

if __name__ == '__main__':
    main()
```

> 📢 **Step 1 完成**：融合完成，{N} 个接口，{M} 个匹配 Swagger 样本

---

## 最终报告

执行完成后，向用户汇报：

```
═══════════════════════════════════════════════════════
📊 融合完成！
═══════════════════════════════════════════════════════

【基本信息】
- 源码文档: source-api-doc.md
- Swagger 样本: 有/无
- Swagger 交叉文档: 有/无

【融合结果】
- 接口总数: {N} 个
- 匹配 Swagger 样本: {N} 个 ✅
- 源码独有（Swagger 无）: {N} 个
- Swagger 独有（源码无）: {N} 个

【输出文件】
- final-api-spec.md           ← 人类可读最终接口文档
- api-spec-machine.json       ← 机器可读 JSON（供 Skill 4 使用）

【Base URL】{url}
【认证方式】{type}
```

---

## 异常处理

| 错误现象 | 可能原因 | 修复方案 |
|---------|---------|---------|
| 缺少 SOURCE_API_DOC | 未运行 Skill 1 | 先运行 api-scanner-from-source |
| 文档解析为空 | Skill 1 输出格式不兼容 | 检查 source-api-doc.md 格式 |
| spec-samples.json 解析失败 | 文件不完整或格式错误 | 重新运行 api-scanner-from-swagger |
| 融合后无接口 | 源码文档解析失败 | 检查文档格式是否符合预期 |

---

## 与各技能的衔接

```
Skill 1 (api-scanner-from-source)
    ↓ source-api-doc.md（字段定义、隐藏参数、业务逻辑）
    ↓
Skill 2 (api-scanner-from-swagger)  ──→ spec-samples.json（示例数据、auth、base_url）
    ↓ swagger-api-doc.md（交叉校验用）
    ↓                                           ↓
Skill 3 (api-fusion-engine) ←───────────────────┘
    ↓
    ├─ final-api-spec.md           → 人类阅读（含匹配验证报告）
    └─ api-spec-machine.json       → Skill 4 (business-skill-executor) 使用
```

---

*Skill version: 1.0.0*
*首次版本：替代原有的 api-validator（校验器），改为融合器（fusion-engine）*

## 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0.0 | 2026-05-19 | 首次版本，替代 api-validator，改为融合器（fusion-engine） |



def output_html_doc(md_path):
    """从 final-api-spec.md 生成 HTML"""
    import re as _rh
    with open(md_path, 'r', encoding='utf-8') as _fh:
        _md = _fh.read()

    _html = '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
    _html += 'body{font-family:Helvetica,Arial,sans-serif;max-width:950px;margin:40px auto;padding:20px;line-height:1.7;color:#333}'
    _html += 'h1{color:#1a1a2e;border-bottom:3px solid #1a1a2e;padding-bottom:10px;font-size:28px}'
    _html += 'h2{color:#16213e;border-bottom:2px solid #ccc;padding-bottom:8px;margin-top:35px;font-size:22px}'
    _html += 'h3{color:#0f3460;margin-top:30px;font-size:18px}'
    _html += 'h4{color:#533483;margin-top:25px;font-size:16px}'
    _html += 'table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}'
    _html += 'th,td{border:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}'
    _html += 'th{background:#f0f0f0;font-weight:bold;white-space:nowrap;width:1%}'
    _html += 'code{background:#f4f4f4;padding:2px 5px;border-radius:3px;font-size:0.9em}'
    _html += 'pre{background:#f6f8fa;padding:15px;border-radius:5px;overflow-x:auto;border:1px solid #e1e4e8;font-size:13px}'
    _html += 'blockquote{border-left:4px solid #7c3aed;margin:15px 0;padding:8px 15px;background:#faf5ff;border-radius:0 5px 5px 0}'
    _html += 'hr{border:none;border-top:2px solid #eee;margin:30px 0}'
    _html += '</style></head><body>'

    _lines = _md.split('\n')
    _in_code = False
    _in_table = False
    _first_table = True
    _code_lines = []

    for _l in _lines:
        if _l.startswith('```'):
            if _in_code:
                _html += '<pre><code>' + '\n'.join(_code_lines) + '</code></pre>\n'
                _code_lines = []; _in_code = False; _in_table = False
            else:
                _in_code = True
            continue
        if _in_code:
            _code_lines.append(_l.replace('<','&lt;').replace('>','&gt;'))
            continue

        # Skip separator lines like |------| or |:----:|
        if _l.startswith('|') and __import__('re').match(r'^\|[-:\s]+\|', _l):
            continue
        # Table row
        if _l.startswith('|'):
            if not _in_table:
                _in_table = True; _first_table = True
                _html += '\n<table>\n'
            cells = [c.strip() for c in _l.split('|')[1:-1]]
            _tag = 'th' if _first_table else 'td'
            _html += '<tr>' + ''.join(f'<{_tag}>{c}</{_tag}>' for c in cells) + '</tr>\n'
            _first_table = False
            continue
        else:
            if _in_table:
                _html += '</table>\n'; _in_table = False

        _t = _l.strip()
        if not _t: continue
        if _t == '---':
            _html += '<hr>\n'; continue
        if _t.startswith('> '):
            _html += '<blockquote>' + _t[2:] + '</blockquote>\n'; continue

        _t2 = _l  # use original line (with leading spaces for indentation)
        _t2 = _rh.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', _t2)
        _t2 = _rh.sub(r'`([^`]+?)`', r'<code>\1</code>', _t2)

        if _t2.startswith('#### '):
            _html += '<h4>' + _t2[5:] + '</h4>\n'
        elif _t2.startswith('### '):
            _html += '<h3>' + _t2[4:] + '</h3>\n'
        elif _t2.startswith('## '):
            _html += '<h2>' + _t2[3:] + '</h2>\n'
        elif _t2.startswith('# '):
            _html += '<h1>' + _t2[2:] + '</h1>\n'
        else:
            _html += '<p>' + _t2 + '</p>\n'

    if _in_table: _html += '</table>\n'
    _html += '</body></html>'

    _html_path = md_path.replace('.md', '.html')
    with open(_html_path, 'w', encoding='utf-8') as _fh:
        _fh.write(_html)
    _size = os.path.getsize(_html_path) / 1024
    print(f'  HTML: final-api-spec.html ({_size:.0f} KB)')




## 🚫 禁止使用简化脚本（必须深度扫描）

| 禁止 | 原因 |
|------|------|
| 不要手写内联 HTML 转换器 | 必须使用 SKILL.md 中的 `output_html_doc()` 函数 |
| 不要省略 `final-api-spec.html` 生成 | API 文档需要 HTML 版供打印/导出 PDF |
| 不要合并分析报告到接口文档 | 分析报告独立输出 `*-fusion-report.md`，接口文档按模板格式纯输出 |
| 不要假设所有路径都有 `/` 前缀 | 部分方法路径缺失 `/`，需要在索引表匹配时处理 |
| 不要使用简化版 spec-samples.json | 必须使用 Skill 2 完整版生成的 spec-samples（含 45 字段 body 示例） |

**输出检查清单：**
- [ ] `final-api-spec.md`：按模板格式，无分析报告
- [ ] `final-api-spec.html`：表格有 `<th>`，**粗体**工作，`` 代码 `` 工作，无分隔线泄露
- [ ] `api-spec-machine.json`：机器可读，接口数正确
- [ ] `*-fusion-report.md`：独立分析报告
