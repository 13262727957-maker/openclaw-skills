---
name: swagger-source-matcher
description: |
  Swagger 模块与源码项目的路径匹配工具。将 Swagger 下载的 JSON 模块文件与本地源码项目的接口文档进行路径匹配，
  生成每个源码项目对应的 Swagger 匹配报告，供下游 api-scanner-from-swagger 技能使用。

  触发关键词：Swagger匹配、模块归属、Swagger源码对应、接口归属、Swagger对应项目、模块归属分析、路径前缀匹配

  适用场景：
  1. 已有 swagger-dev-YYYYMMDD 目录（Swagger 下载的 JSON 模块），需要确认各模块归属哪个源码项目
  2. 为 api-scanner-from-swagger 技能提供输入信息（扫描哪个 Swagger JSON 文件）
  3. 按源码项目分拆，每个项目独立一份匹配报告

  匹配逻辑：精确路径重叠 → 前缀规则匹配（PATH_PREFIX_RULES）→ 源码路径前缀重叠兜底
  匹配置信度：高（精确重叠）、中（前缀匹配 10-50%）、低（小于10%）

  输出：每个源码项目单独一份报告，文件名为 {项目名}-swagger-match-report.md
---

# swagger-source-matcher

**Swagger 模块与源码项目路径匹配工具**

将 Swagger 下载的 JSON 模块文件与本地源码项目的接口文档进行路径匹配，按源码项目分拆输出独立报告，供下游 `api-scanner-from-swagger` 技能使用。

---

## 输出文件

每执行一次，生成 **3 份独立报告**（每个源码项目单独一份）：

```
~/Desktop/成果/
├── caij-cloud-basics-swagger-match-report.md
├── caij-cloud-mom-swagger-match-report.md
└── caij-cloud-wcs-swagger-match-report.md
```

每份报告包含：
- 基本信息（源码接口数、对应的 Swagger 模块数/接口数）
- Swagger 模块匹配详情表（含 JSON 文件名、路径前缀匹配说明）
- **Swagger JSON 文件列表**（供下游技能直接使用）
- 源码路径前缀参考表
- 可信度说明（中/低可信度模块标注）

---

## 工作流程

### Step 0: 确认输入

需要准备：
1. **Swagger JSON 模块目录**：如 `~/Desktop/成果/swagger-dev-20260518/`
2. **源码项目接口文档**：各 `caij-cloud-*/source-api-doc.md`

### Step 1: 配置项目和路径

修改脚本中的配置区：

```python
SWAGGER_DIR = Path.home() / "Desktop/成果/swagger-dev-20260518"

SOURCE_PROJECTS = {
    'caij-cloud-basics': Path.home() / "Desktop/成果/caij-cloud-basics-20260519",
    'caij-cloud-mom':    Path.home() / "Desktop/成果/caij-cloud-mom-20260518",
    'caij-cloud-wcs':    Path.home() / "Desktop/成果/caij-cloud-wcs-20260518",
}
```

### Step 2: 执行匹配

```bash
python3 ~/.openclaw/workspace/skills/swagger-source-matcher/scripts/match.py
```

### Step 3: 下游技能使用

以 `caij-cloud-mom` 为例，下游 `api-scanner-from-swagger` 技能读取 `caij-cloud-mom-swagger-match-report.md`，从"Swagger JSON 文件列表"章节获取应扫描的文件路径：

```
- `~/Desktop/成果/swagger-dev-20260518/生产成本核算模块.json` ✅
- `~/Desktop/成果/swagger-dev-20260518/生产管理模块.json` ✅
- `~/Desktop/成果/swagger-dev-20260518/生产基础档案模块.json` ✅
```

---

## 匹配规则

### 策略优先级

1. **精确路径重叠**（高可信度）：Swagger 路径与源码 `source-api-doc.md` 中的路径完全一致
2. **前缀规则匹配**（中/高可信度）：PATH_PREFIX_RULES 中有定义的前缀
3. **源码路径前缀重叠兜底**（中/低可信度）：两者二级前缀有交集（超过10%匹配率）

### 匹配置信度判定

| 置信度 | 条件 |
|--------|------|
| 高 | 精确路径重叠大于0，或前缀匹配率大于等于50% |
| 中 | 前缀匹配率 10% ~ 50% |
| 低 | 前缀匹配率小于10%，或无匹配 |

---

## 常见路径前缀参考

| 前缀 | 归属项目 |
|------|---------|
| /mom/ | caij-cloud-mom |
| /aps | caij-cloud-mom |
| /qc/board | caij-cloud-mom |
| /wcs/ | caij-cloud-wcs |
| /boot/core | caij-cloud-wcs |
| /boot/system | caij-cloud-wcs |
| /boot/basics | caij-cloud-basics |
| /bd | caij-cloud-basics |
| /crm | 外部 CRM 系统 |
| /wms | 外部 WMS 系统 |
| /eam | 外部 EAM 系统 |
| /aiot | 外部 AIoT 系统 |

---

## 扩展路径前缀规则

修改脚本中的 PATH_PREFIX_RULES：

```python
PATH_PREFIX_RULES = {
    '/mom/': 'caij-cloud-mom',
    '/aps': 'caij-cloud-mom',
    '/wcs/': 'caij-cloud-wcs',
    '/bd': 'caij-cloud-basics',
    '/boot/basics/bd': 'caij-cloud-basics',
    # 新增：
    '/新前缀/': '新项目名',
}
```

---

## 依赖

- Python 3
- 标准库：pathlib, re, json（无需安装额外依赖）