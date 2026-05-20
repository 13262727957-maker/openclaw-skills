# api-scanner-from-swagger

**一句话描述**：解析已部署系统的 Swagger 文档，生成结构化接口文档 + 分析报告。

---

## 触发词

> Swagger解析、在线API文档、已部署系统接口、解析Swagger文档

**与其他技能区分**：
- 有 Git 仓库地址？→ 用 `api-scanner-from-source`（源码级深度扫描）
- 已有接口文档需要验证？→ 用 `api-validator`（验证/补全）
- **有 Swagger URL？→ 用这个**

---

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `SWAGGER_URL` | ✅* | Swagger JSON 在线地址 |
| `SWAGGER_FILE` | ✅* | 或直接上传 Swagger JSON 文件 |
| `PROJECT_NAME` | ❌ | 项目名称（默认从 URL 推导） |
| `OUTPUT_DIR` | ❌ | 输出目录（默认 `~/Desktop/成果/{PROJECT_NAME}`） |

*二选一

---

## 输出

| 文件 | 说明 |
|------|------|
| `swagger-api-doc.md` | 接口文档（按模块分组，含路径/方法/参数/响应码） |
| `swagger-analysis-report.md` | 分析报告（接口统计/方法分布/模块分布） |
| `scan-errors.log` | 扫描错误记录 |

---

## 快速使用

```bash
# 方式一：在线解析
SWAGGER_URL="https://dev.caijai.com/caij_saas/v2/api-docs" \
PROJECT_NAME="caij-saas" \
bash <技能路径>/SKILL.md

# 方式二：上传文件
SWAGGER_FILE="/path/to/swagger.json" \
PROJECT_NAME="my-api" \
bash <技能路径>/SKILL.md
```

---

## 执行流程

```
Step 0: 环境预检（curl、python3、参数校验、幂等检查）
Step 1: 获取 Swagger JSON（下载或上传）
Step 2: 验证并解析 JSON 结构
Step 3: 生成接口文档
Step 4: 生成分析报告
Step 5: 汇报完成
```

---

## 特点

- ✅ **只读操作** — 只解析文档，不调用实际接口
- ✅ **实时汇报** — 每步执行前/后都会通知
- ✅ **幂等保护** — 输出目录已存在会提示确认
- ✅ **超时保护** — curl 默认 60s 超时
- ✅ **错误诊断** — 内置常见错误排查指南