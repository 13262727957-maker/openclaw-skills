# business-skill-executor

## 定位

读取完整接口文档 + BASE_URL，根据用户指定的业务流程和参数，自动发 HTTP 调 API，返回人类可读结果。

## 输入参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `COMPLETE_API_SPEC` | file | Skill 3 输出的完整接口文档（`complete-api-spec.md`） | ✅ |
| `BASE_URL` | string | API 基础地址（如 `http://192.188.107.72:8787/caij_saas`） | ✅ |
| `BUSSINESS_FLOW` | string | 用户选择的业务流程（如：`新增生产订单 → 派工 → 生成派工单`） | ✅ |
| `PARAMS` | json | 用户提供的业务参数（如：`{"material": "螺丝", "quantity": 1000}`） | ✅ |
| `AUTH_TOKEN` | string | 认证 Token（可选，如有接口需要登录） | ❌ |

## 输出

| 输出 | 说明 |
|------|------|
| 执行结果 | 自动调 API → 返回人类可读的业务结果 |

## 执行流程

### Step 1：读取接口文档

读取 `complete-api-spec.md`，解析：
- 所有接口的定义（路径、方法、参数）
- 业务流程依赖图（接口调用顺序）
- 隐藏参数说明

### Step 2：解析业务流程

根据 `BUSSINESS_FLOW` 确定要调用的 API 顺序：
```
"新增生产订单 → 派工 → 生成派工单"
        ↓
1. POST /api/produce/order
2. POST /api/produce/order/dispatch
3. POST /api/produce/dispatchsheet
```

### Step 3：构造并执行 API 调用

按顺序依次调用：

**步骤 1：新增生产订单**
```bash
curl -X POST "${BASE_URL}/api/produce/order" \
  -H "Content-Type: application/json" \
  -d '{
    "material": "螺丝",
    "quantity": 1000
  }'
```

**步骤 2：派工**（从步骤 1 的返回中提取 orderId）
```bash
# 从步骤 1 的返回中提取 orderId
ORDER_ID=$(echo "$PREV_RESPONSE" | jq -r '.orderId')

curl -X POST "${BASE_URL}/api/produce/order/dispatch" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": \"${ORDER_ID}\"
  }"
```

**步骤 3：生成派工单**（从步骤 2 的返回中提取 dispatchId）
```bash
DISPATCH_ID=$(echo "$PREV_RESPONSE" | jq -r '.dispatchId')

curl -X POST "${BASE_URL}/api/produce/dispatchsheet" \
  -H "Content-Type: application/json" \
  -d "{
    \"dispatch_id\": \"${DISPATCH_ID}\"
  }"
```

### Step 4：返回人类可读结果

将 API 原始返回转化为用户友好的结果：

```markdown
✅ 生产订单创建成功！

| 项目 | 值 |
|------|-----|
| 订单号 | PO-20260101 |
| 派工单号 | DSP-20260102 |
| 状态 | 已生成 |
```

## 用户体验示例

```
用户输入：
  BUSSINESS_FLOW = "新增生产订单 → 派工 → 生成派工单"
  PARAMS = {
    "material": "螺丝",
    "quantity": 1000
  }
  BASE_URL = "http://192.188.107.72:8787/caij_saas"

Skill 自动执行：
  1. POST /api/produce/order
     参数：{ "material": "螺丝", "quantity": 1000 }
     返回：{ "orderId": "PO-20260101", "status": "created" }

  2. POST /api/produce/order/dispatch
     参数：{ "orderId": "PO-20260101" }
     返回：{ "dispatchId": "DSP-20260102", "status": "dispatched" }

  3. POST /api/produce/dispatchsheet
     参数：{ "dispatchId": "DSP-20260102" }
     返回：{ "sheetId": "SHT-20260103", "status": "generated" }

用户看到的返回：
  ✅ 生产订单创建成功！
  订单号：PO-20260101
  派工单号：DSP-20260102
  派工单已生成
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| API 返回非 200 状态码 | 提取错误信息，返回人类可读的错误说明 |
| 某个步骤失败 | 停止后续步骤，返回已成功的步骤结果 + 失败原因 |
| 网络超时 | 重试 1 次，仍失败则报错 |
| 参数缺失 | 返回"缺少参数 {xxx}，请提供" |

## 异常处理

| 错误 | 处理方式 |
|------|---------|
| 缺少 COMPLETE_API_SPEC | 报错，要求提供 Skill 3 的输出 |
| 缺少 BASE_URL | 报错，要求提供 API 基础地址 |
| 业务流程中的接口在文档中不存在 | 报错，提示"接口 {xxx} 不在已定义的流程中" |
| 上游 API 调用失败 | 停止后续步骤，返回已成功的结果和失败原因 |

## 示例

```
输入：
  COMPLETE_API_SPEC = "/tmp/api-scan/caij-saas/complete-api-spec.md"
  BASE_URL = "http://192.188.107.72:8787/caij_saas"
  BUSSINESS_FLOW = "新增生产订单 → 派工 → 生成派工单"
  PARAMS = '{"material": "螺丝", "quantity": 1000}'

输出：
  ✅ 生产订单创建成功！
  订单号：PO-20260101
  派工单号：DSP-20260102
  派工单已生成
```

---

*Skill version: 1.0.0*