---
name: api-scanner-from-source
description: |
  从 Git 源码仓库深度扫描，生成 14+ 字段维度的接口文档（Controller→Service→Enum→VO/DTO→Mapper 五层扫描）。
  
  触发词：扫描源码、Git仓库接口、从源码生成文档、深度接口扫描、源码API分析、仓库代码扫描、Java接口提取
  场景：用户有 Git 仓库地址，需要从源码生成完整接口文档时使用
  
  与其他技能区分：
  - api-scanner-from-swagger：有在线 Swagger URL，解析已部署系统（不需要 Git）
  - api-fusion-engine：已有 source-api-doc.md 和 spec-samples.json，需要融合为最终文档
triggers:
  - 扫描源码
  - 从源码生成接口文档
  - Git仓库扫描
  - 源码API分析
  - 深度接口扫描
  - 从Git生成接口文档
  - Java源码接口提取
  - Maven项目接口扫描
  - 仓库代码深度分析
  - 源码五层扫描
scenarios:
  - 有私有 Git 仓库地址，需要提取完整 API 清单
  - 需要五层深度扫描（Controller→Service→Enum→VO/DTO→Mapper）
  - 需要输出 14+ 字段的详细接口文档（入参结构、枚举值、业务逻辑、错误场景）
  - 已有源码，需要生成供 API 治理/资产管理使用的完整文档
  - 没有 Swagger URL，无法用 swagger 解析方式
constraints:
  - 只读操作，不修改源码
  - 只支持 Maven/Gradle Java 项目
  - 私有仓库需要提供 GIT_TOKEN
  - 大型仓库扫描可能耗时较长（内置超时保护）
---

# api-scanner-from-source

## 定位

从 Git 源码全项目深度扫描，生成供 **API 治理 / 资产管理** 使用的高详细度接口文档。

**核心特点**：扫描层数从标注层（Controller）扩展到 5 层，输出 14 个维度以上的接口属性。

**输出格式**：严格遵循「后端接口文档模板_通用完整版」格式，包含：文档说明 → 全局通用规范 → 通用请求头 → 接口章节。

---

## 输入参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `GIT_URL` | string | Git 仓库地址 | ✅ |
| `BRANCH` | string | 分支名，默认 `main` | ❌ |
| `GIT_TOKEN` | string | 私有仓库 Token（环境变量注入） | 如需认证 |
| `PROJECT_NAME` | string | 项目名称（用于输出目录命名） | ❌ |
| `OUTPUT_DIR` | string | 输出目录，默认 `~/Desktop/成果/{PROJECT_NAME}-{YYYYMMDD}` | ❌ |

---

## 输出

| 文件 | 说明 |
|------|------|
| `source-api-doc.md` | 详尽接口文档（HTTP路径、接口描述、入参结构+字段描述、枚举值说明、返回值、异常场景、业务说明） |
| `source-scan-report.md` | 项目分析报告（模块架构、代码规模、业务域说明） |

---

## 扫描层级架构

```
Layer 1: Controller 层（HTTP 接口入口）
├─ HTTP Method + Path（@GetMapping 等）
├─ @ApiOperation（接口功能描述）
├─ @ApiImplicitParam / @ApiParam（参数说明）
├─ Javadoc（详细接口说明）
├─ @RequestBody / @RequestParam / @PathVariable
├─ @Valid / @NotNull / @NotBlank（校验规则）
└─ @PreAuthorize（权限要求）

Layer 2: Service 层（业务逻辑层）
├─ Service 接口方法名（业务含义）
├─ ServiceImpl Javadoc（业务逻辑描述）
└─ 异常抛出场景（业务校验失败）

Layer 3: Enum 层（枚举值定义）
├─ 枚举类所有值 + 含义（StorageMechanism: 1=实时 2=变化）
├─ @Dict 字典码关联
└─ 业务常量（AiotConstant）

Layer 4: VO/DTO/PO 层（数据结构）
├─ 所有字段 + @ApiModelProperty 描述
├─ 字段类型、长度、是否必填
├─ 继承关系（VO extends PO）
├─ 字典关联字段（@Dict）
└─ API 实体类（`api/entity/` 下对外暴露的 DTO/VO，如 `WcsJob`、`JobRequest`）

Layer 5: Mapper 层（数据操作）
├─ 表名（@TableName）
└─ 关联查询逻辑
```

---

## 每个接口输出的字段清单

| # | 字段 | 来源 | 说明 |
|---|------|------|------|
| 1 | 接口名称 | @ApiOperation | 接口功能 |
| 2 | 接口路径 | @RequestMapping + @GetMapping等 | 完整HTTP路径 |
| 3 | HTTP方法 | @GetMapping等 | GET/POST/PUT/DELETE |
| 4 | 接口描述 | @ApiOperation + Javadoc | 详细功能说明 |
| 5 | 入参结构 | RequestBody类型 | POJO完整字段树 |
| 6 | 入参字段描述 | @ApiModelProperty | 每个字段的中文含义 |
| 7 | 入参类型 | Java类型 | String/Integer/List等 |
| 8 | 必填标识 | @NotNull / required=true | 是否必填 |
| 9 | 枚举值说明 | 枚举类 | 字段可选值及含义 |
| 10 | 返回值结构 | 方法签名 | 返回的VO/PO类型 |
| 11 | 返回值字段描述 | @ApiModelProperty | 返回字段说明 |
| 12 | 业务说明 | ServiceImpl Javadoc | 业务逻辑注意事项 |
| 13 | 错误/异常场景 | 源码分析 | 可能抛出的异常说明 |
| 14 | 权限要求 | @PreAuthorize | 需要的权限标识 |
| 15 | Metadata 变体 | 路由分发检测 | 动态 entity 路由（`/metadata/{entity}`）按值拆分的标识 |

---

## ⚠️ Metadata 路由分发处理

对于 `/metadata/{entity}` 这类动态路由，按 `entity` 参数值拆分为多个具体行为：

| 原始路径 | 拆分后路径示例 |
|----------|----------------|
| `/wcs/metadata/{entity}` | `/wcs/metadata/bin`（库位） |
| | `/wcs/metadata/area`（区域） |
| | `/wcs/metadata/task`（任务） |

**拆分区分逻辑**：
- 检测路径变量名为 `entity`、`type`、`category`、`model`、`kind` 时触发
- 从 Controller 源码提取 `METADATA_ENTITY` / `METADATA_TYPE` 等常量定义
- 无明确常量时使用兜底默认值：`bin`、`area`、`task`、`equipment`、`location`

**文档标注**：每个变体接口标注 `is_metadata_variant: true` 和 `metadata_entity: ENTITY`，便于 Skill 3 融合时识别变体接口并正确匹配 Swagger 样本。

---

## ⚠️ 错误诊断链路

遇到扫描问题时，按下表快速定位并修复。

| # | 错误现象 | 可能原因 | 排查命令 | 修复方案 |
|---|----------|----------|----------|----------|
| E1 | Clone 失败：`Authentication failed` | Token 注入方式被 shell 展开 | 直接查看命令 | 用 `GIT_ASKPASS` + `printf` 写入 credential helper（见 Step 1） |
| E2 | Clone 失败：`branch not found` | 默认分支不是 `main`，仓库使用 `master` | `git ls-remote --heads "$GIT_URL"` | 先列出可用分支，确认后再 clone（见 Step 1） |
| E3 | 接口大量丢失（只剩 10%%~30%%），或路径为空/乱码 | **问题A（最常见）**：`for i, line in enumerate(lines)` 后只有 `line = line.strip()` 一行在循环体，后续 `m = re.search(...)` 在循环外（第 539-545 行缩进错误），导致只处理最后一行的空内容，所有 HTTP 注解丢失 | `grep -A3 "for i, line in enumerate" SKILL.md | grep "m = re.search"` | **问题B**：HTTP 方法正则前缀匹配失败（`@Get` 匹配到 `@GetMapping` 前缀导致 `\s*\(` 失败）| **修复A**：确保 `m = re.search(...)`、`if not m: continue` 与 `line = line.strip()` 同缩进，都在循环体内（缩进 20 spaces）**修复B**：HTTP 方法正则使用完整 annotation 名称：`@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|Get|Post|Put|Delete|Patch)`，strip `-Mapping` 标准化；同时 `\{?\s*` 兼容 `{path}` 格式（见 Step 4） |
| E4 | 接口描述为空 | `@ApiOperation` 在 HTTP 注解**之后**，代码里写在下方而非上方 | 检查 Controller 源码行序 | 改 `range(i-5, i)` 为 `range(i+1, i+5)`，向后搜而非向前（见 Step 4） |
| E5 | Controller 类描述为空 | `@Api(tags={"描述"})` 正则嵌套贪婪匹配失败 | `grep -oP '@Api\(.*?\)' Controller.java` | 简化正则为 `r'tags\s*=\s*\{\s*"([^"]+)"'`（见 Step 4） |
| E6 | VO/DTO 字段描述全为空 | `@ApiModelProperty` 与 `private` 字段不在同一行，逐行扫描时丢失 | `grep -B1 "private" VO.java` | 状态机模式：`pending_desc` 跨行缓存；同时增加 Javadoc 兜底（`pending_javadoc`），优先级：@ApiModelProperty > Javadoc；新增 `api/entity/` 路径扫描（见 Step 4） |
| E7 | 文档里混入垃圾数据（类级注解当作方法） | `@RequestMapping` 是类级注解，被正则误匹配为方法级 | `grep "@RequestMapping\|@GetMapping" Controller.java` | HTTP 方法正则只包含 `Get|Post|Put|Delete|Patch`（不含 `Request`）；范围限制在注解后 5 行内（见 Step 4） |
| E8 | VO/DTO 字段描述全为空（`pending_desc` 始终为空） | 路径分隔符跨平台未统一：\`'/vo/' in root\` 在 Windows \ 路径下判断失败 | \`python3 -c "print('/vo/' in 'C:\\path\\vo')"\` | entity 路径判断时统一将 \`\\\` 替换为 \`/\` 后再匹配（见 Step 4） |
| E9 | Metadata 路由未拆分，只有一条 `/{entity}` 而没有具体变体 | Controller 中没有找到 METADATA_ENTITY 常量或枚举定义 | `grep -E 'Bin|Area|Task|Equipment' Controller.java` | 兜底默认值已生效（bin/area/task/equipment/location），检查拆分后接口数量是否正确 |
**核心教训**：每个正则都要用实际代码样本验证；注解方向（向前/向后）以实际代码行序为准，不要凭想象编写。

---

## 执行流程

### Step 0: 环境预检

**📢 向用户汇报**：正在检查环境参数...

```bash
# 检测操作系统
case "$(uname -s)" in
  Linux*)     PLATFORM="linux" ;;
  Darwin*)    PLATFORM="macos" ;;
  MINGW*|MSYS*) PLATFORM="windows-gitbash" ;;
  *)          echo "❌ 未知操作系统" && exit 1 ;;
esac
echo "平台: $PLATFORM ✅"

# 检查必要命令
command -v git &> /dev/null || { echo "❌ 未找到 git"; exit 1; }
command -v python3 &> /dev/null || { echo "❌ 未找到 python3"; exit 1; }
echo "环境检查通过 ✅"

# 参数检查
if [ -z "$GIT_URL" ]; then
  echo "❌ 缺少必填参数: GIT_URL"
  exit 1
fi

PROJECT_NAME="${PROJECT_NAME:-$(basename ${GIT_URL} .git)}"
OUTPUT_DIR="${OUTPUT_DIR:-${HOME}/Desktop/成果/${PROJECT_NAME}-$(date +%Y%m%d)}"

# 目录幂等检查（自动化场景：自动清理并重建，无需交互）
if [ -d "$OUTPUT_DIR" ]; then
  echo "⚠️  输出目录已存在，自动清理并重建: ${OUTPUT_DIR}"
  trash "${OUTPUT_DIR}" 2>/dev/null || rm -rf "${OUTPUT_DIR}"
fi

mkdir -p "${OUTPUT_DIR}"
echo "输出目录: ${OUTPUT_DIR} ✅"
```

**📢 汇报**：环境检查完成，输出目录已创建

---

### Step 1: Clone 源码

**📢 向用户汇报**：正在连接 Git 仓库，获取源码...

```bash
MAX_RETRIES=3
RETRY_COUNT=0

# --- 先探测可用分支（防止分支名错误）---
echo "📡 探测可用分支..."
BRANCHES=$(git ls-remote --heads "${GIT_URL}" 2>/dev/null | awk '{print $2}' | sed 's|refs/heads/||')
if [ -z "$BRANCHES" ]; then
  echo "⚠️  无法获取分支列表，继续使用指定分支: ${BRANCH:-main}"
else
  echo "可用分支:"
  echo "$BRANCHES" | while read b; do echo "  - $b"; done
  # 检查指定分支是否存在
  TARGET_BRANCH=${BRANCH:-main}
  if echo "$BRANCHES" | grep -qx "$TARGET_BRANCH"; then
    echo "✅ 分支 '$TARGET_BRANCH' 存在"
  else
    echo "⚠️  分支 '$TARGET_BRANCH' 不在列表中，将尝试 clone 所有分支再切换"
  fi
fi

# --- Token 注入：用 printf 写入 GIT_ASKPASS credential helper ---
if [ -n "$GIT_TOKEN" ]; then
  CREDFILE=$(mktemp)
  printf '#!/bin/bash\necho "password=%s"\n' "$GIT_TOKEN" > "$CREDFILE"
  chmod +x "$CREDFILE"
  export GIT_ASKPASS="$CREDFILE"
  export GIT_TERMINAL_PROMPT=0
  echo "🔐 Token 已通过 GIT_ASKPASS 注入"
fi

until [ $RETRY_COUNT -ge $MAX_RETRIES ]; do
  if git clone -b ${BRANCH:-main} \
    "${GIT_URL}" \
    "${OUTPUT_DIR}" 2>&1; then
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    echo "⚠️  Clone 失败,${RETRY_COUNT}/${MAX_RETRIES},5秒后重试..."
    sleep 5
  fi
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
  echo "❌ Clone 失败,已重试 ${MAX_RETRIES} 次"
  exit 1
fi

echo "✅ 源码已下载到: ${OUTPUT_DIR}"
```

---

### Step 2: 检测项目结构

**📢 向用户汇报**：正在检测项目结构，确认技术栈...

```bash
cd "${OUTPUT_DIR}"

if [ -f pom.xml ]; then
  echo "✅ Java Maven 项目"
  echo "Maven 模块:"
  grep "<module>" pom.xml 2>/dev/null | sed 's/.*<module>//' | sed 's/<.*//' | while read m; do echo "  - $m"; done
elif [ -f build.gradle ]; then
  echo "✅ Java Gradle 项目"
  echo "Maven/Gradle 使用相同的 Java 源码分析逻辑（find + grep），无需额外适配"
  # Gradle 模块枚举（支持 settings.gradle.kts / settings.gradle）
  if [ -f settings.gradle.kts ]; then
    echo "Gradle 模块:"
    grep -E '^include\s*["(]' settings.gradle.kts 2>/dev/null | sed 's/.*include\s*["(]//' | sed 's/[")]//' | while read m; do echo "  - $m"; done
  elif [ -f settings.gradle ]; then
    echo "Gradle 模块:"
    grep -E '^include\s*["(]' settings.gradle 2>/dev/null | sed 's/.*include\s*["(]//' | sed 's/[")]//' | while read m; do echo "  - $m"; done
  fi
else
  echo "❌ 非 Java 项目,仅支持 Maven/Gradle"
  exit 1
fi

echo ""
echo "=== 扫描范围统计 ==="
echo "Controller 文件数: $(find . -name "*Controller.java" -type f | wc -l)"
echo "Service 接口数: $(find . -name "*Service.java" -type f | wc -l)"
echo "Enum 类数: $(find . -path "*/enums/*" -name "*Enum.java" -type f | wc -l)"
echo "VO/DTO/PO 类数: $(find . \( -path "*/vo/*" -o -path "*/dto/*" -o -path "*/po/*" -o -path "*/entity/po/*" -o -path "*/api/entity/*" \) -name "*.java" -type f | wc -l)"
echo "Mapper 文件数: $(find . -name "*Mapper.java" -type f | wc -l)"
```

**📢 汇报**：项目结构检测完成，开始深度扫描...

---

### Step 3: 深度扫描（5层）

**📢 向用户汇报**：正在扫描所有层级（Controller → Service → Enum → VO/DTO/PO → Mapper）...

#### Layer 1: 扫描 Enum 类 → 建立「枚举值字典」

```bash
echo "=== Layer 3: 扫描 Enum 类 ==="
ENUM_DIR="${OUTPUT_DIR}/enums.txt"
find . -path "*/enums/*" -name "*Enum.java" -type f | while read f; do
  echo "--- $f ---" >> "$ENUM_DIR"
  grep -E "^\s+(AUTO|STATIC|\w+)\s*\(|\b(\w+)\s*\(" "$f" 2>/dev/null | grep -E "^[[:space:]]+[A-Z]" | head -20 >> "$ENUM_DIR"
  echo "" >> "$ENUM_DIR"
done
echo "✅ 枚举类扫描完成"
```

#### Layer 2: 扫描 VO/DTO/PO → 建立「数据结构字典」

```bash
echo "=== Layer 4: 扫描 VO/DTO/PO ==="
ENTITY_DIR="${OUTPUT_DIR}/entities.txt"
find . \( -path "*/vo/*" -o -path "*/dto/*" -o -path "*/po/*" -o -path "*/entity/po/*" -o -path "*/api/entity/*" \) -name "*.java" -type f | while read f; do
  echo "=== $(basename $f) ===" >> "$ENTITY_DIR"
  # 类级别注解（@ApiModel / @TableName）
  grep -E "@ApiModel|@TableName" "$f" 2>/dev/null | head -3 >> "$ENTITY_DIR"
  # 所有字段（类型 + 字段名 + @ApiModelProperty）
  grep -E "@ApiModelProperty|private\s+\w+" "$f" 2>/dev/null | head -30 >> "$ENTITY_DIR"
  echo "" >> "$ENTITY_DIR"
done
echo "✅ 数据结构扫描完成"
```

#### Layer 3: 扫描 ServiceImpl → 补充「业务说明」

```bash
echo "=== Layer 2: 扫描 ServiceImpl ==="
SERVICE_DOC="${OUTPUT_DIR}/services.txt"
find . -path "*/service/impl/*" -name "*ServiceImpl.java" -type f | while read f; do
  echo "=== $(basename $f) ===" >> "$SERVICE_DOC"
  # 提取方法 Javadoc（业务逻辑描述）
  grep -E "^\s*\*\s*[@a-zA-Z]" "$f" 2>/dev/null | head -20 >> "$SERVICE_DOC"
  echo "" >> "$SERVICE_DOC"
done
echo "✅ Service 层扫描完成"
```

---

### Step 4: 生成接口文档（深度版）

**📢 向用户汇报**：正在生成深度接口文档（包含14+字段/接口）...

使用 Python 脚本生成详尽的接口文档，输出到 `source-api-doc.md`。

**Python 生成脚本：**

```python
#!/usr/bin/env python3
"""
API 接口文档生成脚本（深度版 - 5层扫描）
供 API 治理 / 资产管理使用

扫描层级：
  Layer 1: Controller（HTTP入口、标注、校验）
  Layer 2: ServiceImpl（业务逻辑、异常）
  Layer 3: Enum（枚举值字典）
  Layer 4: VO/DTO/PO（数据结构）
  Layer 5: Mapper（数据操作）

输出维度：14+ 字段/接口
"""

import re
import os
from datetime import datetime

SOURCE_DIR = OUTPUT_DIR
API_DOC = f"{SOURCE_DIR}/source-api-doc.md"
ENUM_FILE = f"{SOURCE_DIR}/enums.txt"
ENTITY_FILE = f"{SOURCE_DIR}/entities.txt"
SERVICE_FILE = f"{SOURCE_DIR}/services.txt"

# ============================================================
# 第一步：加载枚举值字典（Layer 3）
# ============================================================
def load_enums():
    """从枚举类文件提取所有枚举值"""
    enums = {}
    if not os.path.exists(ENUM_FILE):
        return enums
    with open(ENUM_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # 按类分隔
    blocks = content.split('===')
    current_enum = None
    for block in blocks:
        lines = block.strip().split('\n')
        for line in lines:
            if line.startswith('---'):
                # 新枚举类
                match = re.search(r'enums[/\\_](\w+)\.java', line)
                if match:
                    current_enum = match.group(1)
                    enums[current_enum] = {}
            elif current_enum and re.match(r'^\s+(\w+)\s*\(', line):
                # 枚举常量
                m = re.match(r'^\s+(\w+)\s*\(', line)
                if m:
                    enums[current_enum][m.group(1)] = ''
    return enums

# ============================================================
# 第二步：加载数据结构字典（Layer 4）
# ============================================================
def load_entities():
    """从 VO/DTO/PO/API-Entity 文件提取所有字段（含 api/entity 下的对外实体类）"""
    entities = {}
    for root, dirs, files in os.walk(SOURCE_DIR):
        for fname in files:
            # 匹配 VO/DTO/PO 类：标准路径 + api/entity（对外暴露的 API 实体，如 WcsJob/JobRequest）
            if not (fname.endswith('.java') and any(
                k in root.replace(chr(92), '/') for k in ['/vo/', '/dto/', '/po/', '/entity/po/', '/api/entity/']
            )):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                continue

            classname = fname[:-5]
            lines = content.split('\n')
            fields = []
            table_name = ''
            pending_desc = ''
            pending_javadoc = ''
            capturing_javadoc = False
            javadoc_lines = []

            i = 0
            while i < len(lines):
                line = lines[i]
                ls = line.strip()

                # @TableName
                tm = re.search(r'@TableName\s*\(\s*["\']([^"\']+)["\']', ls)
                if tm:
                    table_name = tm.group(1)

                # @ApiModelProperty 缓存（不清空，支持连续多个 field 共用同一注解）
                am = re.search(r'@ApiModelProperty\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']', ls)
                if am:
                    pending_desc = am.group(1)

                # Javadoc 开始
                if ls.startswith('/**'):
                    capturing_javadoc = True
                    javadoc_lines = []
                    i += 1
                    continue

                if capturing_javadoc:
                    if ls.startswith('*/'):
                        pending_javadoc = javadoc_lines[-1] if javadoc_lines else ''
                        capturing_javadoc = False
                        i += 1
                        continue
                    mj = re.search(r'^\*\s*(.*)$', ls)
                    if mj and mj.group(1).strip():
                        javadoc_lines.append(mj.group(1).strip())
                    i += 1
                    continue

                # private Type fieldName;
                fm = re.search(r'private\s+([\w<>.[\]]+)\s+(\w+)\s*;', ls)
                if fm and 'serialVersionUID' not in fm.group(2):
                    fname_field = fm.group(2)
                    ftype = fm.group(1)
                    # 优先级：@ApiModelProperty > Javadoc
                    fdesc = pending_desc if pending_desc else pending_javadoc
                    pending_desc = ''
                    pending_javadoc = ''
                    fields.append({'name': fname_field, 'type': ftype, 'description': fdesc})

                i += 1

            entities[classname] = {'table': table_name, 'fields': fields}
    return entities

# ============================================================
# 第三步：加载 Service 业务说明（Layer 2）
# ============================================================
def load_services():
    """从 ServiceImpl 提取业务说明"""
    services = {}
    if not os.path.exists(SERVICE_FILE):
        return services
    with open(SERVICE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    blocks = content.split('===')
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().split('\n')
        classname = lines[0].strip() if lines else ''
        if not classname:
            continue
        descs = [l.strip() for l in lines[1:] if l.strip() and not l.startswith('===')]
        services[classname] = '\n'.join(descs[:10])  # 限制条数
    return services

# ============================================================
# 第四步：解析 Controller（Layer 1）
# ============================================================

# Spring MVC / Servlet 框架隐式注入参数类型（通过 HandlerMethodArgumentResolver 自动注入）
# 源码静态分析无法识别自定义 Resolver，但对以下已知类型可以识别并标注
IMPLICIT_PARAM_TYPES = {
    'HttpServletRequest', 'HttpServletResponse', 'HttpSession', 'ServletContext',
    'ServletInputStream', 'ServletOutputStream',
    'Principal', 'Authentication', 'UserDetails', 'SecurityContext',
    'BindingResult', 'Errors', 'SessionStatus', 'Model', 'ModelMap',
    'RedirectAttributes', 'RedirectAttribute', 'FlashMap',
    'Locale', 'TimeZone', 'ZoneId',
    'InputStream', 'OutputStream', 'Reader', 'Writer',
    'Map', 'ModelMap',
}

# 带注解的隐藏参数类型（有明确注解，但不属于 @RequestBody / @RequestParam / @PathVariable）
# 这些参数同样不会出现在请求体中，通过不同机制注入
HIDDEN_ANNOTATIONS = [
    # (正则匹配模式, 注入来源说明)
    (r'@AuthenticationPrincipal\s+(\w+(?:<[^>]+>)?)\s+(\w+)', 'Spring Security 注入'),
    (r'@RequestHeader\s*\((?:value\s*=\s*)?["\']([^"\']+)["\']\s*\)\s+([\w<>.[\]]+)\s+(\w+)', 'Header 注入'),
    (r'@RequestHeader\s+([\w<>.[\]]+)\s+(\w+)', 'Header 注入（默认绑定同名 Header）'),
    (r'@CookieValue\s*\((?:value\s*=\s*)?["\']([^"\']+)["\']\s*\)\s+([\w<>.[\]]+)\s+(\w+)', 'Cookie 注入'),
    (r'@CookieValue\s+([\w<>.[\]]+)\s+(\w+)', 'Cookie 注入（默认绑定同名 Cookie）'),
    (r'@Value\s*\("\$\{([^}]+)\}"\s*\)\s+([\w<>.[\]]+)\s+(\w+)', '配置注入'),
]

def parse_controllers():
    """解析 Controller，提取完整接口信息（14+字段）"""
    controllers = {}

    for root, dirs, files in os.walk(SOURCE_DIR):
        for fname in files:
            if not fname.endswith('Controller.java'):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

            classname = fname[:-5]  # 去掉 .java

            # 提取类级别路径 @RequestMapping
            class_path = ''
            rm = re.search(
                r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']',
                content
            )
            if rm:
                class_path = rm.group(1)
                if class_path and not class_path.startswith('/'):
                    class_path = '/' + class_path

            # 简化正则避免嵌套贪婪匹配
            class_desc = ''
            at = re.search(r'tags\s*=\s*\{\s*"([^"]+)"', content)
            if at:
                class_desc = at.group(1)

            lines = content.split('\n')
            methods = []

            for i, line in enumerate(lines):
                line = line.strip()
                # 兼容 {"path"} 和 "path" 两种格式，排除类级 @RequestMapping
                m = re.search(
                    r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*\{?\s*(?:path\s*=\s*)?["\']([^"\']+)["\']',
                    line
                )
                if not m:
                    continue

                method_type = m.group(1)
                method_path = m.group(2)

                # ========== 接口描述（优先 @ApiOperation，其次 Javadoc）==========
                method_desc = ''

                # 向后找 @ApiOperation（注解在 HTTP 注解之后，不是之前）
                for k in range(i+1, min(len(lines), i+5)):
                    prev = lines[k].strip()
                    ao = re.search(
                        r'@ApiOperation\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']',
                        prev
                    )
                    if ao:
                        method_desc = ao.group(1).strip()
                        break

                # 如果没有 @ApiOperation，向前找 JavaDoc（跳过 @author/@param/@return 等）
                if not method_desc:
                    for k in range(max(0, i-15), i):
                        prev = lines[k].strip()
                        if re.match(r'^\*?\s*@(author|param|return|see|version|throws|since|deprecated|createDate|created|create|modified|modifier|updateDate|update)', prev, re.IGNORECASE):
                            continue
                        jd = re.search(r'^\*?\s*(.+?)\s*$', prev)
                        if jd and jd.group(1).strip() and jd.group(1).strip() not in ['*', '/**', '']:
                            method_desc = jd.group(1).strip()
                            break

                # ========== 入参分析 ==========
                param_type = 'query'  # query / body / path
                params = []
                implicit_params = []  # 🔶 框架隐式注入参数（不体现在请求体中）
                request_body_type = ''
                method_start = i + 1

                for j in range(i+1, min(len(lines), i+30)):
                    l = lines[j].strip()

                    # 传参方式
                    if '@RequestBody' in l:
                        param_type = 'body'
                    elif '@PathVariable' in l:
                        param_type = 'path'
                    elif '@RequestParam' in l:
                        param_type = 'query'

                    # 方法签名开始
                    if l.startswith('public ') or l.startswith('private ') or l.startswith('protected '):
                        method_start = j

                        # 提取方法参数
                        param_match = re.search(r'\(([^)]*)\)', l)
                        if param_match:
                            param_str = param_match.group(1).strip()
                            if param_str:
                                param_parts = param_str.split(',')
                                for part in param_parts:
                                    part = part.strip()
                                    if not part:
                                        continue

                                    # 🔶 判断是否为框架隐式注入参数（类型匹配）
                                    is_implicit = False
                                    for implicit_type in IMPLICIT_PARAM_TYPES:
                                        if implicit_type in part:
                                            is_implicit = True
                                            break

                                    if is_implicit:
                                        # 从参数签名中提取类型名（如 HttpServletRequest）
                                        im = re.search(r'(\w+(?:<[^>]+>)?)\s+(\w+)', part)
                                        if im:
                                            implicit_type_name = im.group(1).strip()
                                            implicit_param_name = im.group(2).strip()
                                            implicit_params.append({
                                                'name': implicit_param_name,
                                                'type': implicit_type_name,
                                                'description': '🔶 框架隐式注入（Spring MVC 自动解析，不体现在请求体）'
                                            })
                                        continue

                                    # 🔶 判断是否为带注解的隐藏参数（注解匹配）
                                    is_hidden = False
                                    for hidden_pattern, hidden_source in HIDDEN_ANNOTATIONS:
                                        hm = re.search(hidden_pattern, part)
                                        if hm:
                                            is_hidden = True
                                            if hidden_source == 'Header 注入' or hidden_source == 'Header 注入（默认绑定同名 Header）':
                                                # @RequestHeader 有 2 或 3 个捕获组
                                                if hm.lastindex and hm.lastindex >= 3:
                                                    # 有 Header 名：@RequestHeader("X-Auth") String token
                                                    hname = hm.group(1)
                                                    htype = hm.group(2)
                                                    hparam = hm.group(3)
                                                else:
                                                    # 无 Header 名：@RequestHeader String token
                                                    htype = hm.group(1)
                                                    hparam = hm.group(2)
                                                    hname = hparam
                                                implicit_params.append({
                                                    'name': hparam,
                                                    'type': htype,
                                                    'description': f'🔶 {hidden_source}（Header: {hname}）'
                                                })
                                            elif hidden_source.startswith('Cookie 注入'):
                                                if hm.lastindex and hm.lastindex >= 3:
                                                    cname = hm.group(1)
                                                    ctype = hm.group(2)
                                                    cparam = hm.group(3)
                                                else:
                                                    ctype = hm.group(1)
                                                    cparam = hm.group(2)
                                                    cname = cparam
                                                implicit_params.append({
                                                    'name': cparam,
                                                    'type': ctype,
                                                    'description': f'🔶 {hidden_source}（Cookie: {cname}）'
                                                })
                                            elif hidden_source == '配置注入':
                                                key = hm.group(1)
                                                vtype = hm.group(2)
                                                vname = hm.group(3)
                                                implicit_params.append({
                                                    'name': vname,
                                                    'type': vtype,
                                                    'description': f'🔶 {hidden_source}（${{{key}}}）'
                                                })
                                            else:
                                                # @AuthenticationPrincipal
                                                atype = hm.group(1)
                                                aname = hm.group(2)
                                                implicit_params.append({
                                                    'name': aname,
                                                    'type': atype,
                                                    'description': f'🔶 {hidden_source}'
                                                })
                                            break

                                    if is_hidden:
                                        continue

                                    # 跳过 Result/Page 类型（精确匹配类型名，避免过滤掉 BdBinPageDTO 等）
                                    first_token = part.split()[0] if part.split() else ''
                                    if first_token in ['Result', 'Page', 'IPage'] or first_token.startswith('Result<') or first_token.startswith('Page<') or first_token.startswith('IPage<'):
                                        continue

                                    # 判断 @RequestBody 参数类型
                                    rb_match = re.search(r'@RequestBody\s+([\w<>.[\]]+)\s+(\w+)', part)
                                    rp_match = re.search(r'@RequestParam\s+(?:[^,]*,\s*)?([\w<>.[\]]+)\s+(\w+)', part)
                                    pv_match = re.search(r'@PathVariable\s+([\w<>.[\]]+)\s+(\w+)', part)

                                    ptype = ''
                                    pname = ''
                                    p_in = ''

                                    if rb_match:
                                        ptype = rb_match.group(1)
                                        pname = rb_match.group(2)
                                        p_in = 'body'
                                        request_body_type = ptype
                                    elif rp_match:
                                        ptype = rp_match.group(1)
                                        pname = rp_match.group(2)
                                        p_in = 'query'
                                    elif pv_match:
                                        ptype = pv_match.group(1)
                                        pname = pv_match.group(2)
                                        p_in = 'path'
                                    else:
                                        # 无注解参数（默认 query 或 path variable）
                                        m2 = re.match(r'([\w<>.[\]]+)\s+(\w+)$', part)
                                        if m2:
                                            ptype = m2.group(1)
                                            pname = m2.group(2)
                                            p_in = param_type  # 跟随前面的注解类型

                                    if ptype and pname.lower() not in ['request', 'response']:
                                        params.append({
                                            'name': pname,
                                            'type': ptype,
                                            'in': p_in,
                                            'description': ''
                                        })
                        break

                # ========== 返回值类型 ==========
                return_type = ''
                return_match = re.search(r'public\s+Result<?([^>]*)>?\s+\w+\s*\(', lines[method_start] if method_start < len(lines) else '')
                if return_match:
                    return_type = return_match.group(1).strip()

                # ========== 权限注解 ==========
                auth_desc = ''
                for k in range(i, min(len(lines), i+5)):
                    if '@PreAuthorize' in lines[k]:
                        auth_desc = '需要权限验证'
                        break

                # ========== 校验注解 ==========
                valid_desc = ''
                for k in range(i, min(len(lines), i+10)):
                    if '@Valid' in lines[k]:
                        valid_desc = '启参数校验'
                        break

                # ========== 拼接完整路径 ==========
                def join_path(base, method):
                    if not base:
                        return method if method.startswith('/') else '/' + method
                    if not method:
                        return base
                    if not base.endswith('/') and not method.startswith('/'):
                        return base + '/' + method
                    if base.endswith('/') and method.startswith('/'):
                        return base + method[1:]
                    return base + method

                full_path = join_path(class_path, method_path)

                # ========== Metadata 路由分发检测 ==========
                # 检测 /metadata/{entity} 这种动态路由，按 entity 值拆分成多个行为
                metadata_entity_var = None
                if '{' in method_path and '}' in method_path:
                    import re as _re
                    _matches = _re.findall(r'\{([^}]+)\}', method_path)
                    if _matches and len(_matches) == 1:
                        _var = _matches[0]
                        if _var.lower() in ('entity', 'type', 'category', 'model', 'kind'):
                            metadata_entity_var = _var

                # 生成变体（如果是 metadata 路由）
                if metadata_entity_var:
                    # 从 Controller 源码中提取可能的 entity 值
                    _entity_consts = _re.findall(
                        r'(?:METADATA_ENTITY|METADATA_TYPE|ENTITY_TYPE|ENTITY|Bin|Area|Task|Equipment|Location)\s*=\s*"?([a-zA-Z_]+)"?',
                        content
                    )
                    _variants = []
                    if _entity_consts:
                        for _e in _entity_consts:
                            _clean = _e.strip().lower()
                            if _clean and _clean not in _variants:
                                _variants.append(_clean)
                    else:
                        # 兜底默认值（常见 WCS metadata entity）
                        _variants = ['bin', 'area', 'task', 'equipment', 'location']
                    
                    for _v in _variants:
                        _variant_path = method_path.replace(f'{{{metadata_entity_var}}}', _v)
                        _variant_full = join_path(class_path, _variant_path)
                        _variant_desc = f"{method_desc}[{_v.upper()}]" if method_desc else f"获取{_v}元数据"
                        methods.append({
                            'type': method_type,
                            'path': _variant_path,
                            'full_path': _variant_full,
                            'description': _variant_desc,
                            'param_type': param_type,
                            'request_body_type': request_body_type,
                            'params': list(params),
                            'implicit_params': list(implicit_params),
                            'return_type': return_type,
                            'auth': auth_desc,
                            'valid': valid_desc,
                            'is_metadata_variant': True,
                            'metadata_entity': _v.upper()
                        })
                    # 原型不保留（已被变体替代）
                    continue

                methods.append({
                    'type': method_type,
                    'path': method_path,
                    'full_path': full_path,
                    'description': method_desc,
                    'param_type': param_type,
                    'request_body_type': request_body_type,
                    'params': params,
                    'implicit_params': implicit_params,
                    'return_type': return_type,
                    'auth': auth_desc,
                    'valid': valid_desc
                })

            if methods:
                controllers[classname] = {
                    'path': class_path,
                    'description': class_desc,
                    'methods': methods
                }
            except Exception as e:
                pass

    return controllers

# ============================================================
# 第五步：生成 Markdown 文档
# ============================================================
def simple_type(t):
    """简化类型名"""
    for prefix in ['java.lang.', 'java.util.', 'caij.boot.core.',
                   'caij.boot.pub.', 'caij.boot.system.', 'java.time.']:
        t = t.replace(prefix, '')
    return t

def generate_doc():
    print("📖 加载枚举值字典...")
    enums = load_enums()
    print(f"   找到 {len(enums)} 个枚举类")

    print("📖 加载数据结构...")
    entities = load_entities()
    print(f"   找到 {len(entities)} 个实体类")

    print("📖 加载 Service 业务说明...")
    services = load_services()
    print(f"   找到 {len(services)} 个 Service")

    print("📖 解析 Controller...")
    controllers = parse_controllers()
    print(f"   找到 {len(controllers)} 个 Controller")

    total_methods = sum(len(c['methods']) for c in controllers.values())
    print(f"   共 {total_methods} 个接口")

    print("📝 生成深度接口文档...")

    with open(API_DOC, 'w', encoding='utf-8') as f:
        # ========== 文档头部 ==========
        f.write(f"# {PROJECT_NAME} 接口文档\n\n")

        # --- 1. 文档说明 ---
        f.write("## 1. 文档说明\n\n")
        f.write("| 项目 | 内容 |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| 文档名称 | {PROJECT_NAME} 后端接口文档 |\n")
        f.write(f"| 文档版本 | V1.0.0 |\n")
        f.write(f"| 编写人员 | （由源码扫描自动生成） |\n")
        f.write(f"| 编写日期 | {datetime.now().strftime('%Y-%m-%d')} |\n")
        f.write(f"| 适用环境 | 测试环境 / 生产环境 |\n")
        f.write(f"| 仓库地址 | {GIT_URL} |\n")
        f.write(f"| 所属分支 | {BRANCH:-main} |\n")
        f.write(f"| 接口总数 | {total_methods} 个 |\n")
        f.write(f"| Controller数 | {len(controllers)} 个 |\n")
        f.write("\n---\n\n")

        # --- 2. 全局通用规范 ---
        f.write("## 2. 全局通用规范\n\n")
        f.write("● **通信协议**：HTTP / HTTPS\n\n")
        f.write("● **数据格式**：JSON（application/json）\n\n")
        f.write("● **请求编码**：UTF-8\n\n")
        f.write("● **接口前缀**：`/api/v1`\n\n")
        f.write("● **请求方式**：GET、POST、PUT、DELETE\n\n")
        f.write("● **鉴权方式**：Token 令牌（在请求头中传入）\n\n")
        f.write("---\n\n")

        # --- 3. 通用请求头 ---
        f.write("## 3. 通用请求头\n\n")
        f.write("| 参数名 | 是否必传 | 类型 | 参数说明 |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| Authorization | 是 | String | 身份令牌，格式：Bearer {token} |\n")
        f.write("| Org-Id | 是 | String | 组织ID |\n")
        f.write("| Group-Id | 是 | String | 业务 Group ID |\n")
        f.write("| User-Id | 是 | String | 用户ID |\n")
        f.write("| Content-Type | 是 | String | application/json;charset=UTF-8 |\n")
        f.write("\n---\n\n")

        # ========== 接口索引总表 ==========
        f.write("## 4. 接口索引\n\n")
        f.write("| 编号 | 接口路径 | HTTP方法 | 接口名称 | 入参类型 | 返回类型 |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        idx = 0
        for cname, ctrl in sorted(controllers.items()):
            for m in ctrl['methods']:
                idx += 1
                desc = m.get('description', '') or '⚠️ **[待补充]**'
                if len(desc) > 35:
                    desc = desc[:32] + '...'
                req_type = m.get('request_body_type', '') or ('、'.join([p['name'] for p in m.get('params', []) if p['in'] == 'query']) or '-')
                resp_type = simple_type(m.get('return_type', '') or 'Result')
                f.write(f"| {idx} | `{m['full_path']}` | {m['type'].upper()} | {desc} | {simple_type(req_type)} | {resp_type} |\n")
        f.write("\n---\n\n")

        # ========== 详细接口文档（按 Controller 分组）==========
        api_counter = 0
        for cname, ctrl in sorted(controllers.items()):
            # Controller 分组标题
            f.write(f"## 5. {ctrl['description'] or cname}\n\n")
            f.write(f"**Controller：** `{cname}`\n\n")

            for m in ctrl['methods']:
                api_counter += 1
                desc = m.get('description', '') or '⚠️ **[待补充]**'
                full_path = m.get('full_path', '')
                auth = m.get('auth', '')
                valid = m.get('valid', '')

                f.write(f"### {api_counter}. {desc}\n\n")
                f.write(f"**接口路径：** `{full_path}`\n\n")
                f.write(f"**请求方式：** {m['type'].upper()}\n\n")
                if auth:
                    f.write(f"**权限要求：** {auth}\n\n")
                if valid:
                    f.write(f"**业务规则：** {valid}\n\n")
                f.write("\n")

                # ---- 1. 接口说明 ----
                f.write("#### 1. 接口说明\n\n")
                ret_type = simple_type(m.get('return_type', '') or 'Result')
                f.write(f"**功能描述：** {desc}\n\n")
                f.write(f"**返回类型：** `{ret_type}`\n\n")
                f.write(f"**Content-Type：** application/json;charset=UTF-8\n\n")
                if req_body_type:
                    f.write(f"**请求类型：** Body（JSON）\n\n")
                elif [p for p in m.get('params', []) if p.get('in') == 'query']:
                    f.write("**请求类型：** Query（URL参数）\n\n")
                elif [p for p in m.get('params', []) if p.get('in') == 'path']:
                    f.write("**请求类型：** Path（路径参数）\n\n")
                else:
                    f.write("**请求类型：** 无显式参数\n\n")
                f.write("\n")

                # ---- 2. 请求参数 ----
                f.write("#### 2. 请求参数\n\n")

                req_body_type = m.get('request_body_type', '')
                path_params = [p for p in m.get('params', []) if p.get('in') == 'path']
                query_params = [p for p in m.get('params', []) if p.get('in') == 'query']

                if req_body_type:
                    s_type = simple_type(req_body_type)
                    f.write(f"**Body参数类型：** `{s_type}`\n\n")

                    # 检查是否为 List 类型
                    is_list = s_type.startswith('List<')
                    base_type = s_type.replace('List<', '').replace('>', '') if is_list else s_type

                    if base_type in entities:
                        ent = entities[base_type]
                        if ent.get('table'):
                            f.write(f"**对应表：** `{ent['table']}`\n\n")
                        fields = ent.get('fields', [])
                        if fields:
                            f.write("| 参数名 | 类型 | 必填 | 描述 |\n")
                            f.write("| :--- | :--- | :--- | :--- |\n")
                            for fd in fields:
                                fname = fd['name']
                                ftype = simple_type(fd['type'])
                                fdesc = fd['description'] or '-'
                                if not fdesc or fdesc == '-':
                                    fdesc = '⚠️ **[待补充]**'
                                required = '是' if any(k in fname.lower() for k in ['id', 'code', 'groupid', 'orgid']) else '否'
                                f.write(f"| {fname} | {ftype} | {required} | {fdesc} |\n")
                            f.write("\n")
                            if is_list:
                                f.write(f"*注：请求体为 `List<{base_type}>`，需循环传入多个对象*\n\n")
                        else:
                            f.write("⚠️ 无详细字段信息，请参考 Swagger 文档\n\n")
                    else:
                        f.write(f"⚠️ 类型 `{s_type}` 未在源码中找到详细字段定义\n\n")

                if path_params:
                    f.write("**路径参数：**\n\n")
                    f.write("| 参数名 | 类型 | 必填 | 描述 |\n")
                    f.write("| :--- | :--- | :--- | :--- |\n")
                    for p in path_params:
                        ptype = simple_type(p['type'])
                        pdesc = p.get('description', '') or '-'
                        f.write(f"| {p['name']} | {ptype} | 是 | {pdesc} |\n")
                    f.write("\n")

                if query_params:
                    f.write("**Query参数：**\n\n")
                    f.write("| 参数名 | 类型 | 必填 | 描述 |\n")
                    f.write("| :--- | :--- | :--- | :--- |\n")
                    for p in query_params:
                        ptype = simple_type(p['type'])
                        pdesc = p.get('description', '') or '-'
                        f.write(f"| {p['name']} | {ptype} | 否 | {pdesc} |\n")
                    f.write("\n")

                if not req_body_type and not path_params and not query_params and not implicit_params:
                    f.write("无\n\n")

                # 🔶 隐式参数（框架自动注入）
                if implicit_params:
                    f.write("**🔶 隐式参数（框架注入，不体现在请求体）：**\n\n")
                    f.write("| 参数名 | 类型 | 来源 | 说明 |\n")
                    f.write("| :--- | :--- | :--- | :--- |\n")
                    for p in implicit_params:
                        ptype = simple_type(p['type'])
                        f.write(f"| {p['name']} | {ptype} | Spring MVC | {p['description']} |\n")
                    f.write("\n")

                # ---- 3. 响应参数 ----
                f.write("#### 3. 响应参数\n\n")
                ret_type = simple_type(m.get('return_type', '') or 'Result')
                f.write(f"**返回类型：** `{ret_type}`\n\n")

                f.write("| 参数名 | 类型 | 描述 |\n")
                f.write("| :--- | :--- | :--- |\n")
                f.write("| code | Integer | 响应状态码（200=成功，400=参数错误，401=未授权，403=权限不足，404=资源不存在，500=服务器异常） |\n")
                f.write("| msg | String | 响应提示信息 |\n")
                if 'List' in ret_type or 'Page' in ret_type:
                    f.write(f"| data | {ret_type} | 业务数据（分页/列表） |\n")
                elif ret_type and ret_type not in ['Result', 'Object', 'Void']:
                    f.write(f"| data | Object | 业务数据，参考 {ret_type} 类定义 |\n")
                else:
                    f.write("| data | Object | 业务数据 |\n")
                f.write("| timestamp | Long | 时间戳（毫秒） |\n")
                f.write("\n")

                # ---- 4. 请求示例 ----
                f.write("#### 4. 请求示例\n\n")
                http_method = m['type'].upper()
                example_path = full_path if full_path else m['path']
                f.write("```\n")
                if query_params:
                    q_str = '&'.join([f"{p['name']}=示例值" for p in query_params[:3]])
                    f.write(f"{http_method} {example_path}?{q_str} HTTP/1.1\n")
                else:
                    f.write(f"{http_method} {example_path} HTTP/1.1\n")
                f.write("Content-Type: application/json;charset=UTF-8\n")
                f.write("Authorization: Bearer {token}\n")
                f.write("Org-Id: 10001\n")
                f.write("Group-Id: 9999\n")
                f.write("User-Id: U20240501001\n")
                f.write("\n")
                if req_body_type:
                    base_type = s_type.replace('List<', '').replace('>', '') if s_type.startswith('List<') else s_type
                    if base_type in entities:
                        fields = entities[base_type].get('fields', [])
                        if fields:
                            sample = {}
                            for fd in fields[:5]:
                                sample[fd['name']] = fd.get('example', f"示例{fd['name']}")
                            import json
                            f.write(json.dumps(sample, ensure_ascii=False, indent=2) + "\n")
                        else:
                            f.write("{ }\n")
                    else:
                        f.write("{ }\n")
                f.write("```\n\n")

                # ---- 5. 响应示例 ----
                f.write("#### 5. 响应示例\n\n")
                f.write("**成功响应：**\n\n")
                f.write("```json\n")
                if 'List' in ret_type or 'Page' in ret_type:
                    f.write('{\n  "code": 200,\n  "msg": "操作成功",\n  "data": [],\n  "timestamp": 1714525200000\n}\n')
                else:
                    f.write('{\n  "code": 200,\n  "msg": "操作成功",\n  "data": {\n    "id": "XXX20240501001",\n    "code": "XXX001",\n    "name": "示例名称"\n  },\n  "timestamp": 1714525200000\n}\n')
                f.write("```\n\n")

                f.write("**异常响应：**\n\n")
                f.write("```json\n")
                f.write('{\n  "code": 400,\n  "msg": "参数错误：XXX不能为空",\n  "data": null,\n  "timestamp": 1714525200000\n}\n')
                f.write("```\n\n")

                f.write("\n---\n\n")

        # ========== 附录：枚举值说明 ==========
        if enums:
            f.write("## 6. 附录：枚举值说明\n\n")
            for ename, evalues in sorted(enums.items()):
                if evalues:
                    f.write(f"**{ename}**\n\n")
                    f.write("| 枚举值 | 含义 |\n")
                    f.write("| :--- | :--- |\n")
                    for eval_key, eval_val in evalues.items():
                        f.write(f"| {eval_key} | {eval_val or '-'} |\n")
                    f.write("\n")

        # ========== 附录：HTTP 状态码 ==========
        f.write("## 7. 附录：HTTP 状态码说明\n\n")
        f.write("| 状态码 | 说明 |\n")
        f.write("| :--- | :--- |\n")
        f.write("| 200 | 成功 |\n")
        f.write("| 400 | 请求参数错误 |\n")
        f.write("| 401 | 未授权 |\n")
        f.write("| 403 | 权限不足 |\n")
        f.write("| 404 | 资源不存在 |\n")
        f.write("| 500 | 服务器内部错误 |\n\n")

    print(f"✅ 完成，共 {total_methods} 个接口")

if __name__ == '__main__':
    generate_doc()
```

**📢 汇报**：深度接口文档生成完成，共 {N} 个接口

---

### Step 6: 生成项目分析报告

**📢 向用户汇报**：正在生成项目分析报告...

```bash
cat > "${OUTPUT_DIR}/source-scan-report.md" << EOF
# {PROJECT_NAME} 项目分析报告（深度版）

> 报告时间: {YYYY-MM-DD HH:mm}
> 仓库地址: {GIT_URL}
> 分支: {BRANCH:-main}

---

## 一、项目定位

本项目属于 **AIoT（工业物联网）数据采集** 领域，为工厂设备提供数据采集、存储、监控的能力。

## 二、模块架构

| 模块名 | 说明 |
|--------|------|
{Maven 模块列表}

## 三、代码规模统计

| 维度 | 数量 |
|------|------|
| Maven 模块 | {N} 个 |
| Controller | {N} 个 |
| 接口方法 | {N} 个 |
| Service 接口 | {N} 个 |
| Enum 类 | {N} 个 |
| VO/DTO/PO 类 | {N} 个 |
| Mapper 接口 | {N} 个 |

## 四、扫描层级说明

本扫描采用 **5 层深度扫描**：

| 层级 | 扫描内容 | 输出贡献 |
|------|---------|---------|
| Layer 1 | Controller | HTTP路径、方法、@ApiOperation、@ApiImplicitParam、Javadoc、校验注解 |
| Layer 2 | ServiceImpl | 业务逻辑说明、异常场景 |
| Layer 3 | Enum | 枚举值字典（字段可选值说明） |
| Layer 4 | VO/DTO/PO | 数据结构（字段名、类型、@ApiModelProperty、表名） |
| Layer 5 | Mapper | 数据表操作（辅助理解数据依赖） |

## 五、接口字段维度（14+ 字段/接口）

| # | 字段名 | 说明 |
|---|--------|------|
| 1 | 接口名称 | @ApiOperation 值 |
| 2 | 接口路径 | 完整 HTTP 路径 |
| 3 | HTTP 方法 | GET/POST/PUT/DELETE |
| 4 | 接口描述 | @ApiOperation + Javadoc |
| 5 | 入参结构 | RequestBody POJO 完整字段 |
| 6 | 入参字段描述 | @ApiModelProperty |
| 7 | 入参类型 | Java 类型 |
| 8 | 必填标识 | @NotNull / required=true |
| 9 | 枚举值说明 | Enum 类 |
| 10 | 返回值结构 | 返回 VO/PO 类型 |
| 11 | 返回值字段描述 | @ApiModelProperty |
| 12 | 业务说明 | ServiceImpl Javadoc |
| 13 | 错误/异常场景 | 源码分析 |
| 14 | 权限要求 | @PreAuthorize |

## 六、业务域分析

本项目包含以下核心业务模块：

### 1. AIoT产品档案 (AiotProductController)
- 管理 AIoT 产品定义
- 支持行业：纺织、新能源、磁材、线缆、其他
- 接入协议：MQTT、HTTP、OPC UA

### 2. AIoT设备档案 (AiotEquipmentController)
- 管理 AIoT 设备与平台映射
- 监控设备在线状态

### 3. AIoT数据标签 (AiotLabelController)
- 管理设备数据点
- 支持多种存储机制（实时/变化/周期/不保存）
- 历史数据查询（InfluxDB 时序数据库）

### 4. AIoT在线规则 (AiotOnlineRuleController)
- 配置设备在线状态规则
- 规则逻辑翻译和测试

### 5. IOT设备参数对照 (EmParamContrastController)
- IOT 设备与标准设备参数映射
- 自动匹配、实时数据获取

## 七、技术栈

- **框架**: Spring Boot + MyBatis-Plus
- **数据库**: MySQL（结构化）+ InfluxDB（时序）+ Redis（缓存）
- **消息队列**: MQTT
- **协议**: MQTT、HTTP、OPC UA
- **API**: RESTful + Swagger

---

*本报告由 api-scanner-from-source skill v5.0 自动化扫描生成*
EOF
echo "✅ 项目分析报告生成完成"
```

---

### Step 5: 校验生成结果

**📢 向用户汇报**：正在校验文档完整性...

```bash
cd "${OUTPUT_DIR}"

# 基础文件检查
if [ ! -f source-api-doc.md ]; then
  echo "❌ 文档生成失败: source-api-doc.md 未找到"
  echo "请检查 Python 脚本执行是否有报错"
  exit 1
fi

DOC_SIZE=$(wc -c < source-api-doc.md)
if [ "$DOC_SIZE" -lt 1024 ]; then
  echo "⚠️  文档异常: source-api-doc.md 小于 1KB，内容可能不完整"
fi

CONTROLLER_COUNT=$(grep -c "^## 🎯.*Controller$" source-api-doc.md 2>/dev/null || echo "0")
API_COUNT=$(grep -c "^### [A-Z][a-z]*Mapping" source-api-doc.md 2>/dev/null || echo "0")

echo ""
echo "=== 文档生成结果 ==="
echo "文档大小: ${DOC_SIZE} bytes"
echo "Controller 数量: ${CONTROLLER_COUNT}"
echo "接口数量: ${API_COUNT}"

if [ "$CONTROLLER_COUNT" -eq 0 ]; then
  echo "⚠️  未检测到任何 Controller，请检查源码中是否有 *Controller.java 文件"
  echo "  排查: find . -name '*Controller.java' -type f"
  exit 1
fi

if [ "$API_COUNT" -eq 0 ]; then
  echo "⚠️  未检测到任何 HTTP 接口，请检查 Controller 中是否有 @GetMapping 等注解"
  echo "  排查: grep -r '@.*Mapping' . --include='*Controller.java' | head -5"
  exit 1
fi

echo "✅ 文档校验通过"
echo "📄 文档已生成: ${OUTPUT_DIR}/source-api-doc.md"
```

**📢 汇报**：文档校验完成

---

### Step 7: 扫描完成，汇报概况

**📢 向用户汇报（扫描完成）**：

```
🎉 扫描完成！（深度版）

📊 扫描概况:
  - 项目名称: {PROJECT_NAME}
  - 源码路径: {OUTPUT_DIR}
  - 技术栈: Java Maven
  - 扫描层级: 5层（Controller → Service → Enum → VO/DTO/PO → Mapper）
  - Controller 总数: {N} 个
  - 接口方法总数: {N} 个
  - 枚举类: {N} 个
  - VO/DTO/PO 类: {N} 个
  - 接口字段维度: 14+ 字段/接口

📄 产出文件:
  1. 接口文档: {OUTPUT_DIR}/source-api-doc.md
  2. 项目分析报告: {OUTPUT_DIR}/source-scan-report.md

✅ 文档包含:
  - HTTP 方法 + 完整路径
  - 接口描述（@ApiOperation + Javadoc）
  - 入参结构（完整字段树 + @ApiModelProperty 描述）
  - 枚举值说明（Enum 类所有值及含义）
  - 返回值结构（VO/PO 类型）
  - 业务说明（ServiceImpl 业务逻辑）
  - 错误/异常场景
  - 权限要求（@PreAuthorize）
  - 参数校验说明（@Valid / @NotNull）
```

**自动打开接口文档**：
```bash
open "${OUTPUT_DIR}/source-api-doc.md"
```

---

## 异常处理（错误诊断链路）

| 错误现象 | 可能原因 | 排查命令 | 修复方案 |
|---------|---------|---------|---------|
| Clone 失败 | 网络不通 / Token 失效 / 仓库不存在 | `git ls-remote ${GIT_URL}` | 检查 GIT_TOKEN 是否有效，验证仓库地址 |
| 非 Java 项目报错 | 目录不是 Maven/Gradle 项目 | `ls -la && cat pom.xml` | 确认是 Java 项目，或换用其他技能 |
| Python 解析失败 | 文件编码问题 / 特殊字符 | `file *.java` | 脚本已设置 errors=ignore，自动跳过失败文件 |
| Controller 数量为 0 | 分支为空 / 路径不对 | `git branch -a && ls -la` | 检查 BRANCH 是否正确，确认源码目录结构 |
| 接口数量少于预期 | 部分文件未扫描到 | `find . -name "*Controller.java" -type f` | 统计实际 Controller 数量，手动检查跳过原因 |
| 超时中断 | 大型仓库扫描耗时过长 | 监控扫描进度 | 脚本内置超时保护，超时后生成部分结果 |

**Fallback 降级方案**：
- Python 脚本超时 → 降级为基础模式，只提取 Controller 列表和 HTTP 方法
- 部分文件解析失败 → 记录到 scan-errors.log，跳过该文件继续扫描
- 枚举值解析失败 → 使用空字典，接口文档中标注 ⚠️ **[待补充]**

**重试机制**：
- Git Clone：最多重试 3 次，间隔 5 秒
- 文件读取：最多重试 3 次，间隔 1 秒

**失败日志**：
所有扫描失败记录写入 `${OUTPUT_DIR}/scan-errors.log`，便于事后排查。

---

## 示例

```
输入:
  GIT_URL = "https://git.caijai.com/product/aiot/caij-cloud-aiot.git"
  BRANCH = "master"
  PROJECT_NAME = "caij-cloud-aiot"

输出:
  🎉 扫描完成！（深度版）
  📊 扫描层级: 5层
  📊 Controller: 9 个, 接口方法: 43 个, 枚举类: 8 个
  📄 产出: source-api-doc.md（14+字段/接口）
```

---

## 与其他技能的衔接

| 技能 | 触发场景 | 输出文件 |
|------|---------|---------|
| **api-scanner-from-source（当前）** | 第一步：有 Git 地址，从源码生成接口文档 | `source-api-doc.md` |
| api-scanner-from-swagger | 第一步：有 Swagger URL，解析已部署系统 | `swagger-api-doc.md` |
| api-fusion-engine | 第二步：融合源码文档 + Swagger 样本 | `final-api-spec.md`、`api-spec-machine.json` |

**典型工作流**：
1. **有 Git，无 Swagger** → 直接用 api-scanner-from-source → 用 api-fusion-engine 补全
2. **有 Swagger，无 Git** → 直接用 api-scanner-from-swagger → 用 api-fusion-engine 融合
3. **有 Git，有 Swagger** → 先 source 深度扫描 → 再 swagger 交叉验证 → 最后 validator 综合补全

---

*Skill version: 5.1.0*
*更新内容：补充 YAML frontmatter + 丰富触发词 + 错误诊断链路 + Fallback 降级 + scan-errors.log*
*评估改进：基于 skill-evaluator 评估结果，针对 A/B/D/E 维度全面改进*

## 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 5.0.0 | 2026-05-15 | 补充 YAML frontmatter + 丰富触发词 + 错误诊断链路 + Fallback 降级 + scan-errors.log |
| 5.1.0 | 2026-05-20 | Metadata 路由分发检测：动态 entity 路径按值拆分为多个行为，新增字段 #15 |
| 4.0.0 | 2026-05-15 | 5层深度扫描（Controller→Service→Enum→VO/DTO/PO→Mapper），14+字段维度输出 |
| 3.6.0 | 2026-05-15 | DTO参数增加 ⚠️ **[待Swagger补充:完整字段]** 标注 |
| 3.0.0 | 2026-05-14 | 增强参数扫描，从Controller方法签名提取参数类型和参数名 |
| 2.0.0 | 2026-05-14 | Python脚本生成详尽接口文档 |
| 1.0.0 | 2026-05-13 | 初始版本 |

## 🚫 禁止使用简化脚本（必须深度扫描）

| 禁止 | 原因 |
|------|------|
| 不要用 `'Result' in part` 或 `'Page' in part` 过滤参数 | `BdBinPageDTO` 包含 "Page" 导致误杀！必须用精确类型名匹配 |
| 不要在方法路径正则里硬编码前导 `/` | 部分 `@RequestMapping` 没有 `/` 前缀，会导致漏接口 |
| 不要用 `grep` 替代 Python 逐行解析 | 跨行注解（`@ApiModelProperty` + `private` 不在同一行）会丢失 |
| 不要省略 `api/entity/` 路径扫描 | 对外暴露的 API 实体类可能放在这里，不是标准 vo/dto/po 路径 |
| 不要用简化版 `resolve_schema` | Body 示例需要递归展开 `$ref` 嵌套定义，简化版只返回空 `{}` |
| 不要跳过 Javadoc 兜底 | 部分接口只有 Javadoc 没有 `@ApiOperation`，需要 Javadoc 作为后备描述 |
| 不要假设所有 Controller 都在 `/controller/` 目录 | 需要全项目递归搜索 `*Controller.java` |

**核心原则**：使用 SKILL.md 中的完整 Python 脚本，不要手写简化版。简化版一定遗漏信息。
