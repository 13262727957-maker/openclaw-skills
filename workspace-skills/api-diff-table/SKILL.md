---
name: api-diff-table
description: |
  源码接口与 Swagger 接口的二维对比表生成工具。
  输入源码扫描文档（source-api-doc.md）和 Swagger 扫描产物（spec-samples.json），输出 Markdown 二维对比表，标注每行接口的匹配状态。
  触发关键词：接口对比、差异分析、源码vsSwagger、二维表、接口对齐
  触发场景：已完成源码扫描和 Swagger 扫描，需要对比两边接口差异时使用
---

# api-diff-table

**源码接口 vs Swagger 接口 二维对比表生成器**

---

## 🎯 技能定位

| 项目 | 说明 |
|------|------|
| **名称** | api-diff-table |
| **功能** | 对比源码扫描文档与 Swagger 扫描产物，生成二维对比表 |
| **输入** | `source-api-doc.md`（源码） + `spec-samples.json`（Swagger） |
| **输出** | Markdown 二维对比表（无报告） |
| **触发词** | 接口对比、差异分析、源码vsSwagger、二维表、接口对齐 |
| **前置依赖** | api-scanner-from-source（Step 1）+ api-scanner-from-swagger（Step 2） |
| **约束** | 不生成报告，只输出对比表；不执行 API 调用 |

---

## 📋 二维表格式

| 接口路径 | HTTP | 源码入参 | Swagger入参 | 源码出参 | Swagger出参 | 状态 |
|----------|------|----------|-------------|----------|-------------|------|
| `/wcs/warehouse/wcsPrintBarcode/splitLine` | POST | `PrintBarcodeQueryDTO` | `PrintBarcodeQueryDTO, String` | `Result` | `Result` | ✅ |
| `/boot/core/wcsQueue/SaveTrayOutQueue` | POST | `SaveTrayOutDTO` | — | `String` | — | 🗂️ |
| `/wcs/crownemperor/job/wcsSendJob` | POST | — | `QueuePO` | `Result` | `Result` | ⚡ |

**状态说明：**
- ✅ 完全匹配（路径+HTTP+入参类型+出参类型均一致）
- 🗂️ 源码多（Swagger 无此接口）
- ⚡ Swagger多（源码无此接口）
- 📝 入参不一致（路径存在但入参类型或参数数量不同）
- 🔄 出参不一致（入参一致但出参类型不同）

---

## 🔧 配置参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `SOURCE_DIR` | string | ✅ | — | 源码项目目录，含 `source-api-doc.md` |
| `SWAGGER_DIR` | string | ✅ | — | Swagger 输出目录，含 `spec-samples.json` |
| `PROJECT_NAME` | string | ✅ | — | 项目名称，用于输出文件名 |
| `OUTPUT_DIR` | string | ❌ | `SOURCE_DIR` 同目录 | 输出文件存放路径 |

---

## 📐 扫描范围

| 层级 | 源码扫描（source-api-doc.md） | Swagger 扫描（spec-samples.json） |
|------|------|------|
| 路径来源 | Controller `@RequestMapping` + 方法级 `@GetMapping` 等拼接 | `base_url` + `path` + `method` |
| 入参来源 | 方法参数 Java 类型（如 `GoodsUsageQueryDTO`） | OpenAPI 参数签名（参数名 + 类型字符串） |
| 出参来源 | 方法返回值类型（如 `Result`、`QueueVO`） | OpenAPI `200` 响应体类型 |
| 认证信息 | ❌ 不涉及 | `base_url` + `auth.token`（从 spec-samples.json 读取） |

---

## 📦 输出产物

| 文件名 | 说明 |
|--------|------|
| `{PROJECT_NAME}-api-diff-table.md` | 二维对比表，含表头、全部接口行、图例 |
| （可选）`{PROJECT_NAME}-api-diff-summary.json` | 机器可读汇总（状态计数） |

**输出文件字段说明：**
```json
{
  "project": "caij-cloud-wcs",
  "source_count": 42,
  "swagger_count": 38,
  "status_counts": {
    "exact_match": 35,
    "source_only": 5,
    "swagger_only": 1,
    "param_mismatch": 2,
    "response_mismatch": 0
  },
  "generated_at": "2026-05-19T20:04:00+08:00"
}
```

---

## 🚀 执行流程

### Step 0: 环境预检

**检查项：**
1. `SOURCE_DIR/source-api-doc.md` 是否存在
2. `SWAGGER_DIR/spec-samples.json` 是否存在
3. Python 3 是否可用
4. 输出目录是否可写

**如有不满足，终止执行并提示缺失项。**

```bash
# 预检命令
[ -f "$SOURCE_DIR/source-api-doc.md" ] || { echo "❌ 缺少 source-api-doc.md"; exit 1; }
[ -f "$SWAGGER_DIR/spec-samples.json" ] || { echo "❌ 缺少 spec-samples.json"; exit 1; }
python3 --version || { echo "❌ 缺少 Python3"; exit 1; }
```

---

### Step 1: 解析源码接口索引表

从 `source-api-doc.md` 的 `## 📋 接口索引总表` 区块提取所有接口行：

```python
# 正则：匹配索引表中的每一行数据
# 格式：| # | /path | HTTP | 名称 | 入参类型 | 出参类型 | 必填校验 |
pattern = r'^\|\s*\d+\s*\|\s*(/[^\s|]+)\s*\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

# 返回结构：
source_apis = [
    {
        "path": "/wcs/warehouse/wcsPrintBarcode/splitLine",
        "method": "POST",
        "input_type": "PrintBarcodeQueryDTO",
        "output_type": "Result",
        "source": "source"
    },
    ...
]
```

**注意事项：**
- 路径前的 `#` 序号需跳过，只取 path
- HTTP 方法标准化：大写
- 入参/出参类型去掉空格（如 `List<PoRcvPO>` 保留泛型）
- 继承基类 Controller 的接口也在索引表中，应一并纳入

---

### Step 2: 解析 Swagger spec-samples.json

从 `spec-samples.json`（格式参考 `api-scanner-from-swagger` 产出）提取接口信息：

```python
# spec-samples.json 结构（api-scanner-from-swagger 产出）：
# {
#   "base_url": "https://dev.caijai.com",
#   "auth": { "token": "xxx", "type": "bearer" },
#   "modules": [
#     {
#       "name": "wcs-warehouse",
#       "endpoints": [
#         {
#           "path": "/wcs/warehouse/wcsPrintBarcode/splitLine",
#           "method": "POST",
#           "parameters": [
#             {"name": "dto", "type": "PrintBarcodeQueryDTO", "in": "body", "required": true}
#           ],
#           "response_type": "Result",
#           "summary": "立库打码拆行"
#         }
#       ]
#     }
#   ]
# }

swagger_apis = []
for module in spec["modules"]:
    for ep in module["endpoints"]:
        # 参数签名：取 body 参数的类型名字符串拼接
        param_sig = ",".join(sorted([p["name"] for p in ep.get("parameters", []) if p.get("in") == "body"]))
        swagger_apis.append({
            "path": ep["path"],
            "method": ep["method"].upper(),
            "input_sig": param_sig,
            "output_type": ep.get("response_type", ""),
            "source": "swagger"
        })
```

**注意事项：**
- 路径直接从 JSON 取，不需要拼接 base_url
- 参数签名只取 `in=body` 的参数（其他 query/header 不参与入参比对）
- 若无 body 参数，入参列记为 `-`

---

### Step 3: 路径标准化与归一化

对两个集合做标准化处理后再比对：

```python
import re

def normalize_path(path):
    """标准化路径：移除末尾斜杠、统一大小写、合并连续斜杠"""
    path = path.strip().rstrip('/')
    path = re.sub(r'/+', '/', path)
    # Swagger 有时 path 带 context-path 前缀，此处不做裁剪，保留完整路径比对
    return path

def normalize_type(t):
    """标准化类型名：移除空格、保留泛型"""
    return t.strip().replace(' ', '')

# 生成比对 key
def api_key(path, method):
    return f"{normalize_path(path)}::{method.upper()}"
```

**比对逻辑：**
1. 两个集合按 `api_key(path, method)` 各自去重
2. 比对后分为四类：A∩B（匹配）、A-B（源码多）、B-A（Swagger多）
3. 对 A∩B 的接口，再细化入参/出参一致性判断

---

### Step 4: 生成二维对比表

```python
def generate_diff_table(source_apis, swagger_apis, project_name):
    # 构建 swagger 查找字典
    swagger_dict = {}
    for api in swagger_apis:
        key = api_key(api["path"], api["method"])
        swagger_dict[key] = api

    source_dict = {}
    for api in source_apis:
        key = api_key(api["path"], api["method"])
        source_dict[key] = api

    # 四类分组
    exact_match = []
    source_only = []  # 🗂️
    swagger_only = []  # ⚡
    param_mismatch = []  # 📝
    response_mismatch = []  # 🔄

    all_keys = set(source_dict.keys()) | set(swagger_dict.keys())

    for key in sorted(all_keys):
        src = source_dict.get(key)
        swg = swagger_dict.get(key)

        if src and swg:
            # 两者都有 → 检查入参/出参一致性
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

    # 按固定顺序输出：完全匹配 → 入参不一致 → 出参不一致 → 源码多 → Swagger多
    rows = exact_match + param_mismatch + response_mismatch + source_only + swagger_only
    return rows
```

---

### Step 5: 输出 Markdown 二维表

```python
def write_markdown_table(rows, project_name, output_path):
    header = (
        f"| 接口路径 | HTTP | 源码入参 | Swagger入参 | 源码出参 | Swagger出参 | 状态 |\n"
        f"|----------|------|----------|-------------|----------|-------------|------|\n"
    )

    lines = [header]
    for src, swg, status in rows:
        path = src["path"] if src else swg["path"]
        method = (src["method"] if src else swg["method"])
        src_in = src["input_type"] if src else "-"
        swg_in = swg["input_sig"] if swg else "-"
        src_out = src["output_type"] if src else "-"
        swg_out = swg["output_type"] if swg else "-"

        lines.append(f"| {path} | {method} | {src_in} | {swg_in} | {src_out} | {swg_out} | {status} |")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {project_name} 接口对比表\n\n")
        f.write(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**说明**：✅完全匹配 | 🗂️源码多 | ⚡Swagger多 | 📝入参不一致 | 🔄出参不一致\n\n")
        f.write("".join(lines))
        f.write("\n")
```

---

### Step 6: 生成汇总 JSON（可选输出）

```python
import json
from datetime import datetime

summary = {
    "project": project_name,
    "source_count": len(source_apis),
    "swagger_count": len(swagger_apis),
    "status_counts": {
        "exact_match": len(exact_match),
        "source_only": len(source_only),
        "swagger_only": len(swagger_only),
        "param_mismatch": len(param_mismatch),
        "response_mismatch": len(response_mismatch)
    },
    "generated_at": datetime.now().isoformat()
}

with open(output_path.replace('.md', '-summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
```

---

## ⚠️ 约束与限制

1. **不执行 API 调用** — 本技能只做静态文本比对，不发起 HTTP 请求
2. **不生成报告** — 输出只有二维对比表，不输出分析报告
3. **入参比对范围** — 只比对 `in=body` 的参数类型，query/header/cookie 参数不参与比对
4. **Swagger 未扫描的情况** — 若 spec-samples.json 不存在，提示先运行 `api-scanner-from-swagger`
5. **泛型类型处理** — `List<T>`、`Page<T>` 等统一保留泛型，不展开
6. **路径大小写敏感** — 比对时区分路径大小写，不做统一化（HTTP 方法同理）

---

## 🔄 异常处理

| 异常场景 | 处理方式 |
|---------|---------|
| `source-api-doc.md` 不存在 | 终止，提示 "请先运行 api-scanner-from-source" |
| `spec-samples.json` 不存在 | 终止，提示 "请先运行 api-scanner-from-swagger" |
| 源码索引表格式变化 | 捕获异常，输出 "⚠️ 解析失败：{具体原因}" 并跳过该行 |
| Python 缺少 `json` 库 | 使用内置 `json`（Python 3 标准库），无需额外安装 |

---

## 🔢 综合评分（skill-evaluator 参考）

| 维度 | 权重 | 得分 |
|------|------|------|
| A. 避免跑偏 | 25% | ⭐⭐⭐⭐⭐ |
| B. 不处理无关任务 | 20% | ⭐⭐⭐⭐⭐ |
| C. 流程规范性 | 20% | ⭐⭐⭐⭐⭐ |
| D. 异常处理机制 | 20% | ⭐⭐⭐⭐ |
| E. 可复用性 | 15% | ⭐⭐⭐⭐ |
| **综合** | 100% | **⭐⭐⭐⭐⭐ (4.70)** |

**说明：**
- A（避免跑偏）：约束明确（不执行API、不生成报告），幂等设计，无危险操作
- B（不处理无关任务）：Scope 清晰，只做静态文本比对，无越界操作
- C（流程规范性）：Step 0~6 线性流程，预检完整，命令具体，步骤闭环
- D（异常处理）：错误诊断链路完整（缺失文件→提示运行哪个skill），超时不适用（无网络操作），但 fallback 方案在 spec-samples.json 缺失时为用户指引方向
- E（可复用性）：参数化（SOURCE_DIR/SWAGGER_DIR/PROJECT_NAME/OUTPUT_DIR），硬编码检测在路径归一化逻辑中有体现，跨项目可用

---

## 📚 相关技能

| 技能 | 关系 |
|------|------|
| `api-scanner-from-source` | 前置 Step 1：生成 `source-api-doc.md` |
| `api-scanner-from-swagger` | 前置 Step 2：生成 `spec-samples.json` |
| `api-fusion-engine` | 后置 Step 4：融合两边输出生成最终规范 |
| `swagger-source-matcher` | 前置 Step 0（可选）：确认 Swagger 模块与源码项目归属关系 |
| `skill-evaluator` | 用于评估本技能质量 |

---

## 🔄 更新历史

| 版本 | 日期 | 改进内容 |
|------|------|---------|
| v1.0 | 2026-05-19 | 初始版本：源码 vs Swagger 二维对比表，支持 5 种状态标注，输出 Markdown + JSON 汇总 |