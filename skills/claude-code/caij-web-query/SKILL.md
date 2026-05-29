---
name: caij-web-query
description: |-
  通过浏览器自动化查询才匠系统业务数据。支持采购订单统计、延迟交货分析、供应商汇总等业务查询。
  当用户需要统计、分析、汇总才匠系统的业务数据时使用此技能。
keywords:
  - 才匠
  - 采购订单
  - 延迟交货
  - 供应商统计
  - 业务查询
  - 前端查询
metadata:
  openclaw:
    emoji: "\U0001F4CA"
---

# 才匠前端业务查询技能

通过浏览器自动化访问才匠前端页面，执行业务数据查询和统计分析。

## 适用场景

- 统计延迟交货的供应商
- 查询某供应商的历史订单
- 分析采购订单状态分布
- 查询料品采购价格趋势
- 其他需要从才匠系统获取的业务数据

## 前置条件

1. 才匠系统账号（dev.caijai.com）
2. xbrowser 技能已安装
3. Chrome/Edge 浏览器可用

## 登录信息

**测试环境**：https://dev.caijai.com
**用户名**：从环境变量 `CAIJ_USERNAME` 获取，或询问用户
**密码**：从环境变量 `CAIJ_PASSWORD` 获取，或询问用户

## 工作流程

### 1. 初始化浏览器

```bash
NODE="${QCLAW_CLI_NODE_BINARY:-node}"
"$NODE" ~/.qclaw/skills/xbrowser/scripts/xb.cjs init
```

检查返回的 `ok` 字段：
- `true` → 继续
- `false` → 按 `hint` 提示处理

### 2. 打开才匠登录页

```bash
"$NODE" ~/.qclaw/skills/xbrowser/scripts/xb.cjs run --browser default open https://dev.caijai.com
```

### 3. 执行登录

登录表单字段：
- 用户名输入框：`input[type="text"]` 或 `input[placeholder*="账号"]`
- 密码输入框：`input[type="password"]`
- 登录按钮：`button[type="submit"]` 或包含"登录"文字

### 4. 导航到目标页面

根据查询类型导航：
- 采购订单列表：菜单 → 采购管理 → 采购订单
- 采购收货列表：菜单 → 采购管理 → 采购收货

### 5. 应用筛选条件

根据用户需求设置筛选：
- 日期范围
- 供应商
- 状态
- 其他条件

### 6. 提取数据

使用 snapshot 获取页面数据：
```bash
"$NODE" ~/.qclaw/skills/xbrowser/scripts/xb.cjs run --browser default snapshot
```

### 7. 统计分析

从 snapshot 中提取表格数据，进行统计汇总。

### 8. 清理

任务完成后：
```bash
"$NODE" ~/.qclaw/skills/xbrowser/scripts/xb.cjs stop all
```

## 查询模板

### 延迟交货供应商统计

目标：找出交货日期已过但未完成交货的订单，按供应商统计。

步骤：
1. 登录 → 采购订单列表
2. 筛选条件：
   - 状态 = 审批通过（可收货）
   - 交货日期 < 今天
3. 读取列表数据
4. 按供应商分组统计：订单数、订单金额、延迟天数

### 供应商历史订单查询

目标：查询某供应商的所有采购订单。

步骤：
1. 登录 → 采购订单列表
2. 筛选条件：供应商 = 指定供应商
3. 读取列表数据
4. 汇总：订单总数、总金额、平均金额

### 采购订单状态分布

目标：统计各状态的订单数量和金额。

步骤：
1. 登录 → 采购订单列表
2. 读取所有订单（可能需要翻页）
3. 按 `accraditationStatus` 分组统计

## 状态码对照

采购订单状态（accraditationStatus）：
- 0 = 暂存
- 1 = 保存
- 2 = 已确认
- 3 = 审批中
- 4 = 审批通过
- 5 = 审批拒绝

## 注意事项

1. **不要存储密码**：每次询问用户或从环境变量读取
2. **登录态复用**：xbrowser 支持复用已登录的浏览器，减少重复登录
3. **超时处理**：页面加载可能较慢，设置合理超时
4. **分页处理**：数据量大时需要翻页获取完整数据

## 错误处理

- 登录失败：检查账号密码，提示用户重新输入
- 页面加载超时：刷新重试
- 元素找不到：可能页面结构变化，截图排查
