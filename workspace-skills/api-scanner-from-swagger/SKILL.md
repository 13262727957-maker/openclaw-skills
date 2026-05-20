---
name: api-scanner-from-swagger
description: |
  对已部署系统的 Swagger 文档进行解析，生成接口文档 + 分析报告。
  
  触发词：Swagger解析、在线接口文档、已部署系统接口、Swagger扫描、解析Swagger文档、从Swagger生成接口文档
  场景：用户有 Swagger URL，需要解析已部署系统的接口文档时使用
  
  与其他技能区分：
  - api-scanner-from-source：有 Git 仓库地址，源码级深度扫描（不需要已部署）
  - api-fusion-engine：已有 source-api-doc.md 和 spec-samples.json，需要融合为最终文档
triggers:
  - Swagger解析
  - 在线API文档
  - 已部署系统接口
  - Swagger扫描
  - 解析Swagger文档
  - 从Swagger生成接口文档
  - Swagger接口分析
  - 在线接口文档生成
  - 已部署系统接口提取
  - Swagger JSON解析
scenarios:
  - 有 Swagger URL，需要解析已部署系统的接口
  - 需要从在线 Swagger JSON 生成接口文档
  - 需要分析 Swagger 文档的接口分布和结构
  - 没有 Git 仓库，无法用源码扫描方式
  - 已有运行中的服务，需要提取接口清单
constraints:
  - 只读操作，不调用实际接口（只解析文档）
  - 不修改 Swagger 源文件或目标系统
  - 超大 JSON（>500MB）需要分组获取
  - 需要网络可达 Swagger URL
---

# api-scanner-from-swagger

## 定位

对已部署项目的 Swagger 文档进行解析，生成结构化接口文档 + 分析报告。

---

## 📢 实时报告要求（每步必报）

**执行任何 step 时，必须在开始前和完成后向用户发送简短聊天消息：**

```
Step X 开始：<简要说明当前操作>
Step X 完成：<结果/版本/状态>
```

**强制要求：**
- ✅ 必须发送，**禁止**等所有步骤完成才统一报告
- ✅ 禁止用 exec 输出代替用户报告（用户看不到 exec 输出）
- ✅ 每步报告发送给用户，而不是只输出到日志
- ✅ 即使失败也要报告：Step X 失败 → <原因>
- ✅ 全自动执行，不等待用户确认，各 step 自动连续进行

**示例：**
```
Step 0 开始：环境预检...
Step 0 完成：✅ curl、python3 正常，URL 可达
Step 0.5 开始：加载模块归属报告...
Step 0.5 完成：✅ 匹配到 5 个 Swagger 模块
Step 0.6 开始：逐模块检测缓存...
Step 0.6 完成：✅ 3 个模块缓存命中跳过，2 个需要处理
Step 1 开始：下载缺失的模块 JSON...
Step 1 完成：✅ 下载完成，基础模块.json (456 MB)
Step 2 开始：逐个处理模块...
Step 2 完成：✅ 共处理 2 个模块，生成接口文档 2 份
```

---

## 🚫 禁止操作（违反立即停止）

| 禁止 | 原因 |
|------|------|
| 不要修改源码或目标系统 | 只读操作，禁止任何写操作 |
| 不要在 OUTPUT_DIR 外写入文件 | 输出目录白名单保护 |
| 不要跳过 Step 0 直接执行后续步骤 | 环境预检是强制入口 |
| 不要对超大 Swagger 文档（>500MB）直接全量下载 | 会导致超时和内存溢出 |
| 不要在未确认的情况下覆盖已存在的输出目录 | 幂等性保护 |

---

## 🎯 任务边界（Scope Boundary）

**本技能仅限执行以下任务：**
- ✅ 获取并解析 Swagger 2.0 / OpenAPI 3.x JSON
- ✅ 生成 Markdown 格式接口文档
- ✅ 生成分析报告

**明确拒绝以下请求（立即停止）：**
- ❌ 调用任何实际 API 接口（只解析文档，不发请求）
- ❌ 修改 Swagger 源文件或目标系统配置
- ❌ 生成非 Markdown 格式的文档
- ❌ 跨 Swagger 实例合并文档（如需合并请使用其他技能）

---

## 🛡️ 安全默认值

| 默认值 | 说明 |
|--------|------|
| `CURL_TIMEOUT=60` | curl 超时 60 秒，防止无限等待 |
| `IDEMPOTENT=true` | 输出目录已存在时提示确认，不直接覆盖 |
| `PREVIEW_MODE=false` | 默认直接执行（非预览模式） |
| `MAX_JSON_SIZE_MB=500` | 超过 500MB 的 JSON 需特殊处理 |

---

## 📦 参数规格

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `SWAGGER_URL` | string | Swagger JSON 在线地址 | 二选一 |
| `SWAGGER_FILE` | file | 或直接上传 Swagger JSON 文件 | 二选一 |
| `PROJECT_NAME` | string | 项目名称（用于输出目录命名） | ❌（默认从 URL 推导） |
| `OUTPUT_DIR` | string | 输出目录 | ❌（默认 `~/Desktop/成果/{PROJECT_NAME}`） |
| `CURL_TIMEOUT` | number | curl 超时秒数 | ❌（默认 60） |
| `IDEMPOTENT` | bool | 输出目录已存在时是否确认 | ❌（默认 true） |
| `MODULE_MATCH_REPORT` | file | swagger-source-matcher 输出的模块归属报告（可选） | ❌ |
| `SWAGGER_CACHE_DIR` | dir | 已扫描模块的缓存目录，存在则跳过（默认 `~/Desktop/成果/swagger`） | ❌ |

## 📋 执行流程

```
Step 0: 环境预检（强制）
Step 0.5: 加载模块归属报告 → 确定要扫描的 Swagger 模块
Step 0.6: 逐模块检测缓存 → 已有接口文档的模块直接跳过
Step 1: 获取 Swagger JSON（只下载缓存缺失的模块 JSON）
Step 2: 逐个处理模块 → 生成接口文档、分析报告、样本数据
Step 3: 汇报完成
Step 3: 生成接口文档（swagger-api-doc.md）
Step 4: 生成分析报告（swagger-analysis-report.md）
Step 5: 生成示例数据（spec-samples.json，机器可读，含 base_url/auth/请求响应示例）
Step 6: 汇报完成
```

---

## Step 0: 环境预检（强制，每步必报）

**开始前必须向用户发送：**
```
Step 0 开始：环境预检...
```

```bash
# 0.1 检查 curl 是否存在
if ! command -v curl &> /dev/null; then
  echo "❌ curl 未安装，无法执行"
  echo "   修复：brew install curl（macOS）或 apt-get install curl（Linux）"
  exit 1
fi
echo "  ✅ curl 存在"

# 0.2 检查 python3 是否存在（用于 JSON 解析）
if ! command -v python3 &> /dev/null; then
  echo "❌ python3 未安装"
  echo "   修复：brew install python3（macOS）或 apt-get install python3（Linux）"
  exit 1
fi
echo "  ✅ python3 存在"

# 0.3 参数校验（二选一）
if [ -z "$SWAGGER_URL" ] && [ ! -f "$SWAGGER_FILE" ]; then
  echo "❌ 缺少必填参数：需要 SWAGGER_URL 或 SWAGGER_FILE"
  exit 1
fi

# 0.4 从 URL 推导 PROJECT_NAME（如果未提供）
if [ -z "$PROJECT_NAME" ] && [ -n "$SWAGGER_URL" ]; then
  PROJECT_NAME=$(echo "$SWAGGER_URL" | python3 -c "
import sys, re, urllib.parse
url = sys.stdin.read().strip()
parsed = urllib.parse.urlparse(url)
path_parts = [p for p in parsed.path.split('/') if p]
PROJECT_NAME = path_parts[-1] if path_parts else 'unknown'
print(PROJECT_NAME)
" 2>/dev/null || echo "unknown")
fi
PROJECT_NAME="${PROJECT_NAME:-swagger-scan}"
echo "  ✅ 项目名称：${PROJECT_NAME}"

# 0.5 设置输出目录
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/Desktop/成果/${PROJECT_NAME}}"
echo "  ✅ 输出目录：${OUTPUT_DIR}"

# 0.6 幂等检查：输出目录已存在则确认
if [ -d "$OUTPUT_DIR" ]; then
  echo "⚠️  输出目录已存在：${OUTPUT_DIR}"
  if [ "${IDEMPOTENT:-true}" = "true" ]; then
    echo "   输入 'yes' 确认覆盖，或 'no' 退出："
    read -r confirm
    if [ "$confirm" != "yes" ]; then
      echo "❌ 已取消扫描"
      exit 0
    fi
  fi
  echo "⚠️  确认覆盖，继续执行..."
else
  mkdir -p "${OUTPUT_DIR}"
  echo "  ✅ 输出目录已创建"
fi

# 0.6 初始化缓存目录
SWAGGER_CACHE_DIR="${SWAGGER_CACHE_DIR:-${HOME}/Desktop/成果/swagger}"
mkdir -p "$SWAGGER_CACHE_DIR"
echo "  ✅ 缓存目录: ${SWAGGER_CACHE_DIR}"

# 0.7 测试网络连通性（仅 URL 模式）
if [ -n "$SWAGGER_URL" ]; then
  echo "  ➤ 测试 URL 可达性..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SWAGGER_URL" 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "000" ]; then
    echo "❌ 无法访问：${SWAGGER_URL}"
    echo "   可能原因：网络不通 / URL 错误 / 需要认证"
    echo "   排查：curl -v --max-time 10 '${SWAGGER_URL}'"
    exit 1
  elif [ "$HTTP_CODE" -ge 400 ]; then
    echo "❌ URL 返回 HTTP ${HTTP_CODE}"
    echo "   可能原因：路径不存在 / 需要登录 / 权限不足"
    exit 1
  fi
  echo "  ✅ URL 可达（HTTP ${HTTP_CODE}）"
fi

echo ""
echo "✅ Step 0 环境预检通过"
```

**完成后必须发送：**
```
Step 0 完成：环境检查通过，输出目录已就绪
```

---

## Step 0.5: 加载模块归属报告（可选）

**开始前发送：`Step 0.5 开始：加载模块归属报告...`**

```bash
MODULE_FILTER=""
MATCHED_MODULES=""

if [ -n "$MODULE_MATCH_REPORT" ] && [ -f "$MODULE_MATCH_REPORT" ]; then
  echo "  📋 检测到模块归属报告，过滤需要扫描的 Swagger 模块..."
  
  # 从报告中提取匹配的 Swagger 模块名
  # 报告格式为 JSON: {"matched_projects": {"基础模块": true, ...}}
  # 或文本格式: ## Swagger 模块与源码项目的匹配结果
  
  FIRST_LINE=$(head -1 "$MODULE_MATCH_REPORT")
  if echo "$FIRST_LINE" | grep -q '^{'; then
    # JSON 格式
    MATCHED_MODULES=$(python3 -c "
import json
with open('${MODULE_MATCH_REPORT}', 'r') as f:
    data = json.load(f)
matched = data.get('matched_modules', {})
for mod, info in matched.items():
    if info.get('should_scan', True) and not mod.startswith('summary'):
        print(mod)
" 2>/dev/null)
  else:
    # 文本格式，提取 = 所属项目列
    MATCHED_MODULES=$(grep -E '^\|' "$MODULE_MATCH_REPORT" 2>/dev/null | \
      awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+\$/,"",\$2); print \$2}' | \
      grep -v '^Swagger' || true)
  fi
  
  MODULE_COUNT=$(echo "$MATCHED_MODULES" | grep -c . || echo "0")
  if [ "$MODULE_COUNT" -gt 0 ]; then
    echo "  ✅ 匹配到 ${MODULE_COUNT} 个 Swagger 模块："
    echo "$MATCHED_MODULES" | while read m; do echo "    - $m"; done
  else
    echo "  ⚠️  未从报告中提取到匹配模块，将扫描全部模块"
  fi
else
  echo "  ℹ️  无模块归属报告，将扫描全部 Swagger 模块"
fi

echo ""
echo "✅ Step 0.5 模块过滤完成"
```

**完成后发送：`Step 0.5 完成：{匹配到 X 个 Swagger 模块，将按模块列表过滤} / {无模块报告，扫描全部}`**

---

## Step 0.6: 逐模块检测缓存（跳过已有接口文档的模块）

**开始前发送：`Step 0.6 开始：逐模块检测缓存，跳过已有接口文档的模块...`**

```bash
SWAGGER_CACHE_DIR="${SWAGGER_CACHE_DIR:-${HOME}/Desktop/成果/swagger}"
mkdir -p "$SWAGGER_CACHE_DIR"

echo "  缓存目录: ${SWAGGER_CACHE_DIR}"

SKIP_MODULES=""
DOWNLOAD_MODULES=""

if [ -n "$MATCHED_MODULES" ]; then
  echo "  检查各模块文件夹是否已有接口文档..."
  echo "$MATCHED_MODULES" | while IFS= read -r mod; do
    [ -z "$mod" ] && continue
    MOD_DIR="${SWAGGER_CACHE_DIR}/${mod}"
    DOC_FILE="${MOD_DIR}/${mod}-接口文档.md"
    
    if [ -f "$DOC_FILE" ]; then
      SIZE=$(wc -c < "$DOC_FILE" 2>/dev/null || echo "0")
      if [ "$SIZE" -gt 10000 ]; then
        echo "    ✅ 缓存命中: ${mod}/（已有接口文档${SIZE}B），跳过"
        SKIP_MODULES="${SKIP_MODULES}${mod}\n"
      else
        echo "    ⚠️  接口文档不完整: ${mod} (${SIZE}B)，重新生成"
        DOWNLOAD_MODULES="${DOWNLOAD_MODULES}${mod}\n"
      fi
    else
      DOWNLOAD_MODULES="${DOWNLOAD_MODULES}${mod}\n"
    fi
  done
  
  DOWNLOAD_MODULES=$(echo -e "$DOWNLOAD_MODULES" | grep -v '^$')
  DOWNLOAD_COUNT=$(echo "$DOWNLOAD_MODULES" | grep -c . || echo "0")
  SKIP_COUNT=$(echo -e "$SKIP_MODULES" | grep -c . || echo "0")
  
  MATCHED_MODULES="$DOWNLOAD_MODULES"
  
  if [ "$DOWNLOAD_COUNT" -gt 0 ]; then
    echo "   需处理: ${DOWNLOAD_COUNT} 个，缓存跳过: ${SKIP_COUNT} 个"
  else
    echo "   ✅ 全部缓存命中，无需处理"
  fi
else
  echo "  ℹ️  无模块过滤列表，跳过缓存检测"
fi

echo ""
echo "✅ Step 0.6 缓存检测完成"
```

**完成后发送：`Step 0.6 完成：需处理 {N} 个模块，缓存跳过 {M} 个`**

---

## Step 1: 获取 Swagger JSON

**开始前发送：`Step 1 开始：获取 Swagger JSON...`**

```bash
CURL_TIMEOUT="${CURL_TIMEOUT:-60}"

if [ -n "$SWAGGER_URL" ]; then
  # 方式一：从 URL 下载
  echo "  ➤ 下载 Swagger JSON from ${SWAGGER_URL}..."
  HTTP_CODE=$(curl -s -o "${OUTPUT_DIR}/swagger-original.json" \
    -w "%{http_code}" \
    --max-time "${CURL_TIMEOUT}" \
    -L "$SWAGGER_URL" 2>/dev/null || echo "000")

  if [ "$HTTP_CODE" = "000" ]; then
    echo "❌ 下载超时（${CURL_TIMEOUT}s），文件可能过大"
    echo "   💡 修复方案："
    echo "   1. 增加超时：CURL_TIMEOUT=300 bash <script>"
    echo "   2. 或使用 SWAGGER_FILE 直接上传文件"
    exit 1
  elif [ "$HTTP_CODE" -ge 400 ]; then
    echo "❌ 下载失败，HTTP ${HTTP_CODE}"
    rm -f "${OUTPUT_DIR}/swagger-original.json"
    exit 1
  fi

  SIZE=$(wc -c < "${OUTPUT_DIR}/swagger-original.json" 2>/dev/null || echo "0")
  SIZE_MB=$((SIZE / 1024 / 1024))
  echo "  ✅ 下载完成，大小：${SIZE_MB} MB"

  # 大文件警告
  if [ "$SIZE_MB" -gt 500 ]; then
    echo "⚠️  文件超过 500MB（${SIZE_MB} MB），解析可能耗时较长"
  fi

elif [ -f "$SWAGGER_FILE" ]; then
  # 方式二：使用上传的文件
  echo "  ➤ 复制上传文件..."
  cp "$SWAGGER_FILE" "${OUTPUT_DIR}/swagger-original.json"
  # 同时保存到缓存目录（若是模块级别 JSON 则按文件名保存）
  if [ -n "$SWAGGER_CACHE_DIR" ]; then
    BASENAME=$(basename "$SWAGGER_FILE")
    cp "$SWAGGER_FILE" "${SWAGGER_CACHE_DIR}/${BASENAME}"
    echo "  ✅ 已同时保存到缓存: ${SWAGGER_CACHE_DIR}/${BASENAME}"
  fi
  SIZE=$(wc -c < "${OUTPUT_DIR}/swagger-original.json")
  SIZE_MB=$((SIZE / 1024 / 1024))
  echo "  ✅ 文件已复制，大小：${SIZE_MB} MB"
fi
```

**完成后发送：`Step 1 完成：Swagger JSON 已获取（${SIZE_MB} MB）`**

---

## Step 2: 逐个处理模块

**开始前发送：`Step 2 开始：逐个处理模块...`**

```bash
SWAGGER_CACHE_DIR="${SWAGGER_CACHE_DIR:-${HOME}/Desktop/成果/swagger}"
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/Desktop/成果/${PROJECT_NAME}-$(date +%Y%m%d)}"
mkdir -p "$OUTPUT_DIR"

# 如果有模块需要处理
if [ -n "$MATCHED_MODULES" ]; then
  echo "$MATCHED_MODULES" | while IFS= read -r mod; do
    [ -z "$mod" ] && continue
    echo ""
    echo "========================================="
    echo "📦 处理模块: ${mod}"
    echo "========================================="
    
    MOD_DIR="${SWAGGER_CACHE_DIR}/${mod}"
    mkdir -p "$MOD_DIR"
    
    # 获取模块 JSON（从缓存或下载）
    JSON_FILE="${MOD_DIR}/${mod}.json"
    
    # 如果缓存中没有 JSON，尝试从 swagger-dev 目录找，或需要下载
    if [ ! -f "$JSON_FILE" ] || [ "$(wc -c < "$JSON_FILE")" -lt 1000 ]; then
      # 尝试从旧成果里找
      FOUND=$(find "${HOME}/Desktop/成果" -maxdepth 3 -name "${mod}.json" -type f 2>/dev/null | head -1)
      if [ -n "$FOUND" ]; then
        cp "$FOUND" "$JSON_FILE"
        echo "  找到已有 JSON: $FOUND"
      fi
    fi
    
    if [ -f "$JSON_FILE" ] && [ "$(wc -c < "$JSON_FILE")" -gt 1000 ]; then
      # 正式处理：生成接口文档、分析报告、样本数据
      echo "  生成 ${mod}-接口文档.md ..."
      python3 -c "
import json, os
from datetime import datetime
from collections import defaultdict

MOD_NAME = '${mod}'
JSON_PATH = '${MOD_DIR}/${mod}.json'

with open(JSON_PATH, 'r') as f:
    swagger = json.load(f)

paths = swagger.get('paths', {})
definitions = swagger.get('definitions', {})
tag_apis = defaultdict(list)

for path, methods in paths.items():
    for method, details in methods.items():
        if method.upper() not in ['GET','POST','PUT','DELETE','PATCH']: continue
        summary = details.get('summary', details.get('description', ''))
        tags = details.get('tags', ['未分类'])
        tag = tags[0] if tags else '未分类'
        tag_apis[tag].append({
            'method': method.upper(), 'path': path, 'summary': summary,
            'parameters': details.get('parameters', [])
        })

total = sum(len(apis) for apis in tag_apis.values())

# 接口文档
doc = '${MOD_DIR}/${mod}-接口文档.md'
with open(doc, 'w', encoding='utf-8') as f:
    f.write(f'# {MOD_NAME} 接口文档\n\n')
    f.write(f'> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
    f.write(f'> 接口总数: {total}\n\n---\n\n')
    for tag, apis in sorted(tag_apis.items()):
        f.write(f'## 🔷 {tag}\n\n')
        for api in apis:
            f.write(f'### {api["method"]} {api["path"]}\n\n')
            f.write(f'**接口描述:** {api["summary"] or "⚠️"}\n\n')
            f.write('**入参:**\n\n')
            if api['parameters']:
                for p in api['parameters']:
                    ptype = p.get('type', 'string')
                    desc = p.get('description', '')
                    f.write(f"- {p.get('in','?')} \`\`{p.get('name','')}\`\` ({ptype}) {p.get('required','')} - {desc}\n")
            else:
                f.write('*无*\n')
            f.write('\n---\n\n')

doc_size = os.path.getsize(doc) / 1024 / 1024
print(f'    接口文档: {doc_size:.1f} MB ({total} 接口)')
"
      
      echo "  生成 ${mod}-分析报告.md ..."
      python3 -c "
import json
from datetime import datetime
from collections import defaultdict

MOD_NAME = '${mod}'
JSON_PATH = '${MOD_DIR}/${mod}.json'

with open(JSON_PATH, 'r') as f:
    swagger = json.load(f)

paths = swagger.get('paths', {})
definitions = swagger.get('definitions', {})
tag_apis = defaultdict(list)

for path, methods in paths.items():
    for method, details in methods.items():
        if method.upper() not in ['GET','POST','PUT','DELETE','PATCH']: continue
        tags = details.get('tags', ['未分类'])
        tag = tags[0] if tags else '未分类'
        tag_apis[tag].append({'method': method.upper(), 'path': path})

total = sum(len(apis) for apis in tag_apis.values())
mc = defaultdict(int)
for m in paths.values():
    for method in m:
        mc[method.upper()] += 1

report = '${MOD_DIR}/${mod}-分析报告.md'
with open(report, 'w', encoding='utf-8') as f:
    f.write(f'# {MOD_NAME} 分析报告\n\n| 项目 | 值 |\n|------|----|\n')
    f.write(f'| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M")} |\n')
    f.write(f'| 接口总数 | {total} |\n')
    f.write(f'| Tags数 | {len(tag_apis)} |\n')
    f.write(f'| Definitions | {len(definitions)} |\n\n')
    f.write('## HTTP 分布\n\n| 方法 | 数量 |\n|------|:----:|\n')
    for m in ['GET','POST','PUT','DELETE','PATCH']:
        f.write(f'| {m} | {mc.get(m,0)} |\n')
    f.write('\n## Tag 分布\n\n| 模块 | 接口数 |\n|------|:-----:|\n')
    for tag, apis in sorted(tag_apis.items()):
        f.write(f'| {tag} | {len(apis)} |\n')
print(f'    分析报告: {total} 接口, {len(tag_apis)} 个 Tag')
"
      
      echo "  生成 ${mod}-spec-samples.json ..."
      python3 -c "
import json

MOD_NAME = '${mod}'
JSON_PATH = '${MOD_DIR}/${mod}.json'

with open(JSON_PATH, 'r') as f:
    swagger = json.load(f)

paths = swagger.get('paths', {})
samples = []
processed = 0
for path, methods in paths.items():
    for method, details in methods.items():
        if processed >= 200: break
        if method.upper() not in ['GET','POST','PUT','DELETE','PATCH']: continue
        params = details.get('parameters', [])
        summary = details.get('summary', details.get('description', ''))
        qs, headers, body = {}, {}, {}
        for p in params:
            pin, pn = p.get('in',''), p.get('name','')
            if pin == 'query': qs[pn] = f'示例{pn}'
            elif pin == 'header': headers[pn] = f'示例{pn}'
        samples.append({
            'path': path, 'method': method.upper(),
            'description': summary,
            'example_request': {'query': qs, 'headers': headers, 'body': {}},
            'example_response': {'code': 200, 'msg': '操作成功', 'data': {}}
        })
        processed += 1

spec = '${MOD_DIR}/${mod}-spec-samples.json'
with open(spec, 'w') as f:
    json.dump({
        'project': MOD_NAME, 'version': '1.0',
        'base_url': 'https://dev.caijai.com/caij_saas',
        'auth': {'type': 'token'},
        'apis': samples
    }, f, ensure_ascii=False, indent=2)
print(f'    spec-samples.json: {len(samples)} 个示例')
"
      
      echo "  输出目录: ${MOD_DIR}/"
      ls -lh "$MOD_DIR"
    else
      echo "  ❌ 未找到 ${mod}.json，跳过"
    fi
  done
else
  echo "  ℹ️  无待处理模块，全部缓存命中"
fi

echo ""
echo "✅ Step 2 处理完成"
```

**完成后发送：`Step 2 完成：共处理 {N} 个模块`**

---

## Step 3: 汇报完成

**最终向用户汇报：**

```
🎉 Swagger 扫描完成！

📊 扫描概况：
- 项目名称：{PROJECT_NAME}
- 缓存目录：{SWAGGER_CACHE_DIR}
- 本次处理模块：N 个
- 缓存跳过模块：N 个

📄 缓存目录结构（按模块文件夹存放）：
  基础模块/
    ├── 基础模块.json
    ├── 基础模块-接口文档.md
    ├── 基础模块-分析报告.md
    └── 基础模块-spec-samples.json
```

---

## 异常处理（错误诊断链路）

| 错误现象 | 可能原因 | 排查命令 | 修复方案 |
|---------|---------|---------|---------|
| curl 超时 | 网络慢 / 文件过大 / 服务器响应慢 | `curl -v --max-time 10 '{URL}'` | 增加 CURL_TIMEOUT=300，或改用 SWAGGER_FILE |
| HTTP 401/403 | 需要认证 | `curl -v '{URL}'` | Swagger 需登录，加 Token：`curl -H "Authorization: Bearer {token}"` |
| HTTP 404 | URL 路径错误 | `curl -v '{URL}'` | 确认 Swagger 路径，通常是 `/v2/api-docs` 或 `/swagger-resources` |
| JSON 解析失败 | 下载的不是 JSON（可能是 HTML 登录页） | `head -c 200 swagger-original.json` | 确认是否需要先登录系统再获取 Swagger |
| paths 为空 | Swagger 文档无接口定义 | `grep paths swagger-original.json` | 确认是有效的 Swagger 文件 |
| 文件超过 500MB | Swagger 文档过大 | `ls -lh swagger-original.json` | 分组获取（用 swagger-resources 列表逐个获取小模块） |

**Fallback 降级方案**：
- curl 超时 → 增加 CURL_TIMEOUT，或改用 SWAGGER_FILE 直接上传
- JSON 解析失败 → 检查文件是否为有效的 JSON（可能需要登录认证）
- paths 为空 → 确认 Swagger 版本（v2.0 vs 3.0），路径可能不同

**失败日志**：
所有扫描失败记录写入 `${OUTPUT_DIR}/scan-errors.log`，便于事后排查。

---

## 示例

```
输入（方式一 URL）：
  SWAGGER_URL = "https://dev.caijai.com/caij_saas/v2/api-docs"
  PROJECT_NAME = "caij-saas"
  CURL_TIMEOUT = 60

输出：
  🎉 Swagger 扫描完成！
  📊 接口总数：1200 个
  📊 模块数量：45 个
  📄 swagger-api-doc.md + swagger-analysis-report.md

输入（方式二文件）：
  SWAGGER_FILE = "/path/to/swagger.json"
  PROJECT_NAME = "my-api"

输出：
  🎉 Swagger 扫描完成！
  📊 接口总数：800 个
  📄 swagger-api-doc.md + swagger-analysis-report.md
```

---

## 与其他技能的衔接

| 技能 | 触发场景 | 输出文件 |
|------|---------|---------|
| api-scanner-from-source | 第一步：有 Git 地址，从源码生成接口文档 | `source-api-doc.md` |
| **api-scanner-from-swagger（当前）** | 第一步：有 Swagger URL，解析已部署系统 | `swagger-api-doc.md` |
| api-fusion-engine | 第二步：融合源码文档 + Swagger 样本 | `final-api-spec.md`、`api-spec-machine.json` |

**典型工作流**：
1. **有 Git，无 Swagger** → 直接用 api-scanner-from-source → 用 api-fusion-engine 补全
2. **有 Swagger，无 Git** → 直接用 api-scanner-from-swagger → 用 api-fusion-engine 融合
3. **有 Git，有 Swagger** → 先 source 深度扫描 → 再 swagger 交叉验证 → 最后 validator 综合补全

---

*Skill version: 3.0.0*
*更新内容：补充 YAML frontmatter + 丰富触发词 + 错误诊断链路 + Fallback 降级 + scan-errors.log*
*评估改进：基于 skill-evaluator 评估结果，针对 B/C/D/E 维度全面改进*

## 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 3.0.0 | 2026-05-15 | 补充 YAML frontmatter + 丰富触发词 + 错误诊断链路 + Fallback 降级 + scan-errors.log |
| 2.0.0 | 2026-05-14 | 增强禁止操作列表、Scope Boundary、实时报告要求 |
| 1.0.0 | 2026-05-13 | 初始版本 |

## 🚫 禁止使用简化脚本（必须深度扫描）

| 禁止 | 原因 |
|------|------|
| 不要用简化版 `resolve_schema` 生成 spec-samples | 简化版不递归展开 `$ref`，body 示例全是空 `{}`。必须用完整版递归 3 层 |
| 不要假设 `swagger-original.json` 一定完整 | 大文件（>200MB）可能被截断。应使用独立模块 JSON 合并 |
| 不要假定 `swagger-resources` 一直可用 | 该端点可能返回 404（nginx 层问题）。有缓存就用缓存 |
| 不要一次性下载 34 个模块 | 逐个下载，每个模块 20 秒超时，总时间可能 >10 分钟 |
| 不要忽略 Swagger JSON 的认证要求 | 需要登录 token 才能访问 `/v2/api-docs?group=xxx` |
| 不要用子串匹配过滤参数 | 和 Skill 1 同样的问题，需精确匹配类型名 |

**修改必须做完整测试验证：**
1. 修改脚本后首先在单个模块上测试
2. 检查 body 示例字段数（BdBinPO 应有 45 个字段）
3. 检查无参数的接口是否真的有参数
4. 对比修改前后接口数量一致性
