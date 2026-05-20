---
name: k8s-deploy
description: |
  通过Kustomize在已有K8s集群上部署项目。
  **版本：v2**
  触发关键词：部署、上线、发布、重新部署
  触发场景：K8s集群已就绪、需要部署/更新项目到集群
  部署前必确认：源码来源（Git/服务器已有/本地克隆/其他），见下方源码确认流程
  约束：只操作指定服务器和项目，禁止修改系统无关配置。
---

# k8s-deploy

**Phase 2: 部署项目（每次部署）**

---

## 🚫 禁止操作（违反立即停止）

| 禁止 | 原因 |
|------|------|
| 不要修改 `/etc/` 系统目录 | 除非是 K8s 必要配置 |
| 不要删除未确认的资源 | 破坏性操作需确认；但调度冲突时自动判断执行，目标是服务平稳运行 |
| 不要跳过 `generate.sh` 直接 apply | 会导致本地修改被覆盖 |
| 不要在不确定上下文时执行 | 上下文/namespace/服务器身份不确定立即停止 |
| 不要修改系统 SSH/防火墙/内核参数 | 只做 K8s 相关操作 |
| 不要读取包含密码的配置文件内容 | 只读不写，含密码文件禁止展示内容 |
| 不要部署未经源码确认的项目 | 必须先确认源码来源 |
| 不要修改白名单外的 K8s 资源 | 只操作 RESOURCE_ALLOWLIST 内的资源 |
| 不要在生产环境执行未经预览的变更 | 必须先 diff 预览确认；调度冲突等紧急情况除外，事后报告 |

---

## ⚠️ 安全预设

```bash
PREVIEW_MODE=${PREVIEW_MODE:-true}
SSH_CONNECT_TIMEOUT=${SSH_CONNECT_TIMEOUT:-10}
KUBECTL_APPLY_TIMEOUT=${KUBECTL_APPLY_TIMEOUT:-300000}
WAIT_TIMEOUT=${WAIT_TIMEOUT:-600}
```

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
Step 4a 开始：检测所有组件内存配置...
Step 4a 完成：✅ 总 limits 21Gi < 可用 15Gi，资源足够
Step 5 开始：执行 generate.sh 生成清单...
Step 5 完成：✅ 生成 release/<project>.yml
...
```

```
Step 4a 开始：检测所有组件内存配置...
Step 4a 完成：⚠️ 总 limits 21Gi > 可用 12Gi，需要压缩
Step 4d 开始：自动压缩内存配置...
Step 4d 完成：✅ tomcat→4Gi，redis→1Gi，JVM→2g
Step 5 开始：执行 generate.sh 生成清单...
...
```

---

## 🔄 任务相关性检测

### ✅ 属于本技能的范围
- 部署/更新 K8s 项目（generate.sh + kubectl apply）
- 查看 Pod/Service/Deployment 状态
- 健康检查、日志查看
- 扩缩容（scale replica）
- 配置变更（generate.sh + diff + apply）
- 滚动重启（rollout restart）

### ❌ 不属于本技能的范围（立即停止并告知）
- 安装/重装 K8s 集群 → 请使用 `k8s-install`
- 安装/升级 Kubernetes 版本
- 安装/配置 Istio/Cilium 等基础设施组件
- Docker/Containerd 运行时问题排查
- 节点级别操作（系统包、内核参数、防火墙）
- 非 K8s 相关的应用问题（纯代码 bug）
- 数据库迁移、数据修复
- SSL 证书相关操作
- 跨集群操作
- 任何需要修改 `/etc/` 或系统级配置的操作

---

## 📦 参数规格

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SERVER_HOST` | SSH 目标主机（IP 或域名） | **必填** |
| `SSH_USER` | SSH 用户名 | **必填** |
| `SSH_PASSWORD` | SSH 密码 | **必填** |
| `SSH_PORT` | SSH 端口 | `22` |
| `PROJECT_PATH` | 项目部署配置目录 | **必填** |
| `NAMESPACE` | K8s 命名空间 | **必填** |
| `RESOURCE_ALLOWLIST` | 允许操作的 K8s 资源名或 label | **必填** |
| `DEPLOY_IMAGE` | 容器镜像 tag | 由项目配置指定 |
| `JVM_XMX` | JVM 最大堆（如 `1g`、`512m`） | 项目默认值 |
| `TOMCAT_MEMORY_LIMIT` | K8s memory limit | `2Gi` |
| `REDIS_MEMORY_LIMIT` | Redis memory limit | `1Gi` |
| `VOLUME_ALLOWLIST` | 允许写入的 hostPath/数据目录 | 空 |
| `EXPECTED_CONTEXT` | 预期 kube-context | 可选 |
| `EXPECTED_NAMESPACE` | 预期 namespace（额外校验） | 可选 |
| `RELEASE_DIR` | generate.sh 输出目录 | `release` |
| `SKIP_PREVIEW` | 跳过 diff 预览（默认 false） | `false` |
| `FORCE_APPLY` | 失败时使用 --force-conflicts | `false` |

---

## 📋 源码确认流程（部署前必须执行）

| 优先级 | 来源 | 用户需提供 |
|--------|------|-----------|
| 1 | Git 仓库 | `https://git.xxx.com/repo.git` + 分支 + Token |
| 2 | 服务器已有代码 | 绝对路径 |
| 3 | 本地已克隆 | 本机路径 |
| 4 | 其他方式 | 压缩包、镜像内置等 |

**询问清单（部署前必问）：**
```
1. 项目名称（用于 namespace）
2. 源码来源：Git / 服务器已有 / 本地克隆 / 其他
3. Git 地址 + 分支 + Token（如选 Git）
4. 目标服务器 + SSH 凭证
5. 部署配置路径
6. 私有镜像仓库地址
```

---

## 📋 部署完成报告（固定格式）

> 🎉 **部署完成！**
> - 项目：`<name>`
> - 命名空间：`<namespace>`
> - 状态：`<Ready/Failed>`
> - 访问地址：`<url>`（如有）
> - 源码来源：`<来源方式>`
> - 部署时间：`<timestamp>`
> - 各组件 memory limits 总和：`<sum>`

---

### 最终报告应包含以下内容（每步报告 + 最终汇总）

#### Step 0 报告：环境预检
- 目标服务器、namespace、cluster 信息确认
- 节点总内存、可分配内存
- 当前 running Pod 数量（如有遗留）

#### Step 1 报告：环境确认（自动）
- 自动展示目标环境摘要，继续执行下一步

#### Step 2 报告：前置校验
- SSH 连接结果
- 路径安全检查结果
- generate.sh 是否存在

#### Step 3 报告：前置检查（如有 preflight.sh）
- preflight.sh 执行结果

#### Step 4a 报告：资源规划
- 各组件 memory limit/reques
- 所有 limits 总和 vs 节点可用内存
- 通过 / 不通过 + 调整建议

#### Step 4b 报告：JVM vs 容器内存
- JVM -Xmx 值 vs 容器 limit
- 通过 / 不通过

#### Step 4c 报告：硬编码检测
- 检测结果
- 如有硬编码立即停止

#### Step 5 报告：清单生成
- generate.sh 执行结果
- 生成文件数量

#### Step 6 报告：部署前审查
- kubectl diff 结果
- 致命错误检测（CRD 缺失/namespace 不匹配）
- 通过 / 不通过

#### Step 7 报告：应用部署
- kubectl apply 结果
- 每种资源类型的操作数量（configured/created）

#### Step 8 报告：等待就绪
- Pod 列表（NAME/READY/STATUS/RESTARTS/AGE）
- 超时 / OOM 检测结果

#### Step 9 报告：健康检查
- Service 列表
- HTTPRoute / Gateway 状态
- ingressgateway 是否就绪

---

### 🎉 最终部署状态报告模板（部署完成后输出）

```markdown
# 🎉 <项目名> K8s 部署完成报告

## 部署概况
| 项目 | 内容 |
|------|------|
| 服务器 | <host> |
| 命名空间 | <namespace> |
| 源码来源 | <source> |
| 部署时间 | <timestamp> |
| 部署状态 | <Success/Failed> |

## 最终 Pod 状态
| Pod | READY | STATUS | RESTARTS | AGE | Memory Limit | Memory Request |
|-----|-------|--------|----------|-----|-------------|---------------|
| <name> | <ready> | <status> | <restarts> | <age> | <mem limit> | <mem req> |
| ... | ... | ... | ... | ... | ... | ... |

## 各组件资源分配
| 组件 | memory limit | memory request | 说明 |
|------|-------------|---------------|------|
| <comp> | <limit> | <request> | <note> |
**所有 limits 之和：<sum> Gi**（节点可用：<avail> Gi）

## Service & 路由状态
| 资源 | 类型 | 状态 |
|------|------|------|
| <svc> | ClusterIP/LoadBalancer | <ready> |
| <httproute> | HTTPRoute | <status> |
| <gateway> | Gateway | <status> |

## 访问方式
| 入口 | 地址 | 说明 |
|------|------|------|
| 内部访问 | <cluster-ip>:<port> | K8s 内部 Service |
| 外部访问 | <external-url> | 通过 Istio Gateway |

## 节点资源状态
| 指标 | 部署前 | 部署后 | 变化 |
|------|--------|--------|------|
| 内存占用 | <before> | <after> | <diff> |
| 可用内存 | <avail_before> | <avail_after> | <diff> |

## 使用方法
### 查看 Pod 状态
\`\`\`bash
kubectl get pods -n <namespace> -o wide
\`\`\`

### 查看日志
\`\`\`bash
kubectl logs -n <namespace> -l app=<app> --tail=100
\`\`\`

### 进入容器调试
\`\`\`bash
kubectl exec -it -n <namespace> <pod-name> -- /bin/bash
\`\`\`

### 重启指定组件
\`\`\`bash
kubectl rollout restart deployment/<name> -n <namespace>
\`\`\`

### 更新配置后重新部署
\`\`\`bash
# 1. 修改 service/<component>/01-deployment.yml
# 2. 重新生成清单
cd <project-path> && bash generate.sh
# 3. 重新应用
kubectl apply -n <namespace> -f <release-path>/
\`\`\`

### 扩缩容
\`\`\`bash
kubectl scale deployment <name> -n <namespace> --replicas=3
\`\`\`

## 常见问题排查
| 问题 | 排查命令 |
|------|---------|
| Pod 卡 Pending | \`kubectl describe pod <pod> -n <ns>\` |
| Pod OOMKilled | \`kubectl describe pod <pod> -n <ns> | grep -A5 OOM\` |
| Service 无法访问 | \`kubectl get svc -n <ns>\` + \`kubectl get endpoints -n <ns>\` |
| 路由 404 | \`kubectl get httproute -n <ns>\` + \`kubectl describe gateway -n istio-system\` |

---
**报告生成时间：<timestamp>**
```

---

## 🔄 完整工作流程

```
Phase 2: 部署项目
├── Step 0: 环境预检（身份、集群、路径、参数完整性）
├── Step 1: 展示并确认目标环境
├── Step 2: 前置校验（SSH + 路径安全 + 危险路径过滤）
├── Step 3: 前置检查（可选脚本 preflight.sh）
├── Step 4: 修改配置（如需）+ K8s 环境适配检测
│   ├── Step 4a: 资源规划强制检查（所有组件 limits vs 节点可用内存）
│   ├── Step 4b: JVM vs 容器内存一致性检查
│   ├── Step 4c: 硬编码检测
│   ├── Step 4d: 资源自动协调（JVM/内存超限自动修复）
│   └── Step 4e: Probe 路径自动探测与修复（HTTP probe 404 → tcpSocket）
├── Step 5: 生成清单（必须 generate.sh）
├── Step 6: 部署前审查（diff / dry-run）
├── Step 7: 应用部署
├── Step 8: 等待就绪
└── Step 9: 健康检查
```

---

## Step 0: 环境预检

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  🔍 Step 0: 环境预检"
echo "═══════════════════════════════════════════════════════"

# 0.1 SSH 连通性
echo "  ➤ 检查 SSH 连通性..."
if ! ssh -o ConnectTimeout=5 \
         -o BatchMode=yes \
         -o StrictHostKeyChecking=no \
         -p ${SSH_PORT:-22} \
         "${SSH_USER}@${SERVER_HOST}" "echo ok" > /dev/null 2>&1; then
  echo "❌ SSH 连接失败: ${SSH_USER}@${SERVER_HOST}:${SSH_PORT:-22}"
  echo "   请检查：1) 主机地址 2) SSH 服务 3) 防火墙 4) 用户名/密码"
  exit 1
fi
echo "  ✅ SSH 连通性 OK"

# 0.2 主机身份
echo "  ➤ 确认主机身份..."
HOSTNAME=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "hostname 2>/dev/null")
echo "     主机名: ${HOSTNAME}"
echo "  ✅ 主机身份 OK"

# 0.3 kube-context
echo "  ➤ 检查 kube-context..."
CURRENT_CONTEXT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl config current-context 2>/dev/null" || echo "")
if [ -z "${CURRENT_CONTEXT}" ]; then
  echo "❌ 无法获取 kube-context"
  exit 1
fi
echo "     当前 context: ${CURRENT_CONTEXT}"
if [ -n "${EXPECTED_CONTEXT:-}" ] && [ "${CURRENT_CONTEXT}" != "${EXPECTED_CONTEXT}" ]; then
  echo "❌ Context 不匹配！当前=${CURRENT_CONTEXT} 预期=${EXPECTED_CONTEXT}"
  exit 1
fi
echo "  ✅ kube-context OK"

# 0.4 namespace
echo "  ➤ 检查 namespace..."
NS_EXISTS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get ns ${NAMESPACE} --no-headers 2>/dev/null" || echo "")
[ -z "${NS_EXISTS}" ] && echo "     namespace '${NAMESPACE}' 将被创建"
echo "  ✅ namespace OK"

# 0.5 路径安全
echo "  ➤ 路径安全检查..."
PROJECT_REALPATH="$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "cd ${PROJECT_PATH} && pwd -P 2>/dev/null" || echo "")"
[ -z "${PROJECT_REALPATH}" ] && { echo "❌ 无法获取真实路径"; exit 1; }
echo "     项目路径: ${PROJECT_REALPATH}"
case "${PROJECT_REALPATH}" in
  /|/etc|/usr|/var|/System|/Library|/home) echo "❌ 危险路径"; exit 1 ;;
esac
echo "  ✅ 路径安全 OK"

# 0.6 generate.sh
if ! ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
       "[ -f '${PROJECT_PATH}/generate.sh' ]" 2>/dev/null; then
  echo "❌ generate.sh 不存在"
  exit 1
fi
echo "  ✅ generate.sh 存在"

# 0.7 RESOURCE_ALLOWLIST
[ -z "${RESOURCE_ALLOWLIST:-}" ] && { echo "❌ RESOURCE_ALLOWLIST 不能为空"; exit 1; }
echo "  ✅ 参数完整 OK"

echo ""
echo "✅ Step 0: 环境预检通过，可以继续"
```

---

## Step 1: 展示并确认目标环境（自动，无需用户确认）

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  📋 Step 1: 确认目标环境"
echo "═══════════════════════════════════════════════════════"

ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "hostname && whoami && pwd"
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "kubectl config current-context"
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "kubectl get ns ${NAMESPACE} 2>&1 || echo 'namespace 将被创建'"
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "ls ${PROJECT_PATH}/"
echo ""
echo "  ✅ Step 1 环境确认完成"
```

---

## Step 2: 前置校验（参数 + SSH + 路径安全）

```bash
set -euo pipefail

RELEASE_PATH="${PROJECT_REALPATH}/${RELEASE_DIR:-release}"

case "${PROJECT_REALPATH}" in
  /|/etc|/usr|/var|/System|/Library|"$HOME/.ssh")
    echo "错误：危险路径: ${PROJECT_REALPATH}"; exit 1 ;;
esac

case "${RELEASE_PATH}" in
  "${PROJECT_REALPATH}"/*) ;;
  *) echo "错误：RELEASE_DIR 必须在 PROJECT_PATH 内"; exit 1 ;;
esac

if ! ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "[ -d '${PROJECT_PATH}' ]" 2>/dev/null; then
  echo "错误：PROJECT_PATH 不存在: ${PROJECT_PATH}"; exit 1
fi

echo "✅ 前置校验通过"
```

---

## Step 3: 前置检查（可选脚本）

```bash
echo "🔍 Step 3: 执行前置检查..."
if ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
       "[ -f ${PROJECT_PATH}/scripts/preflight.sh ]" 2>/dev/null; then
  echo "  ➤ 执行 preflight.sh..."
  ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "export PROJECT_PATH='${PROJECT_PATH}' NAMESPACE='${NAMESPACE}' \
            SERVER_HOST='${SERVER_HOST}' SSH_USER='${SSH_USER}' && \
     bash ${PROJECT_PATH}/scripts/preflight.sh"
else
  echo "  ⏭️  跳过 preflight.sh（不存在）"
fi
```

---

## Step 4: 修改配置 + K8s 环境适配检测

**⚠️ 铁律：改了配置 → 必须 Step 5 generate.sh → 才能 kubectl apply**

**⚠️ 强制规则：Step 4a 和 Step 4d 每次部署都必须无条件执行，不论本地 YAML 是否被改动过。这是防止配置漂移（configuration drift）的核心机制——即使上次部署是对的，这次部署前也要检查，防止他人手动改坏了 YAML。**

### 4a. 资源规划强制检查（强制，不通过则停止）

```bash
# ============================================
# Step 4a: 资源规划强制检查 ⭐
# 检查不通过则立即停止部署，不允许继续
# ============================================

echo "🔍 Step 4a: 资源规划强制检查..."

# 获取节点总内存（单位：Ki）
NODE_MEMORY=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get node -o jsonpath='{.items[0].status.capacity.memory}'" 2>/dev/null || echo "0")
NODE_MEMORY_GI=$((NODE_MEMORY / 1024 / 1024))
echo "     节点总内存: ${NODE_MEMORY_GI} Gi"

# K8s 系统组件预估内存（控制平面单节点）
K8S_SYSTEM_MEM=3  # Gi，etcd + apiserver + kubelet + cilium + istio
AVAILABLE_MEM=$((NODE_MEMORY_GI - K8S_SYSTEM_MEM))
echo "     K8s 系统占用: ~${K8S_SYSTEM_MEM} Gi"
echo "     可用内存: ${AVAILABLE_MEM} Gi"

# 遍历 service/ 下所有组件，汇总 memory limits
COMPONENTS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "ls -d ${PROJECT_PATH}/service/*/ 2>/dev/null" || echo "")

for comp_dir in ${COMPONENTS}; do
  COMP_NAME=$(basename "${comp_dir}")
  DEPLOY_FILE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "ls ${comp_dir}01-deployment.yml 2>/dev/null || echo ''")
  if [ -n "${DEPLOY_FILE}" ]; then
    MEM_LIMIT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "grep -A2 'memory:' ${DEPLOY_FILE} 2>/dev/null | grep 'limit' | awk '{print \$2}' | head -1" || echo "")
    if [ -n "${MEM_LIMIT}" ]; then
      echo "     ${COMP_NAME}: limit=${MEM_LIMIT}"
    fi
  fi
done

# 计算 limits 总和
TOTAL_LIMITS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "cd ${PROJECT_PATH} && grep -r 'memory:' service/*/01-deployment.yml 2>/dev/null | \
   grep 'limit' | awk '{print \$2}' | sed 's/Gi//g; s/Mi//g' | paste -sd+ | bc" 2>/dev/null || echo "0")

echo ""
echo "     所有组件 limits 之和: ${TOTAL_LIMITS} Gi"
echo "     节点可用: ${AVAILABLE_MEM} Gi"
echo "     建议上限（80%）: $((AVAILABLE_MEM * 80 / 100)) Gi"

# 强制检查：limits 不能超过可用内存的 100%，否则立即停止
if [ "${TOTAL_LIMITS}" -gt "${AVAILABLE_MEM}" ] 2>/dev/null; then
  echo ""
  echo "❌ 资源不足！所有组件 limits 之和（${TOTAL_LIMITS} Gi）超过节点可用内存（${AVAILABLE_MEM} Gi）"
  echo "   部署会导致 OOMKilled，立即停止。"
  echo ""
  echo "💡 修复方案（按优先级）："
  echo "   1. 扩容节点内存（推荐至少 32Gi）"
  echo "   2. 降低 memory limit（参考值）："
  echo "        redis:    1Gi（生产 2Gi）"
  echo "        minio:    512Mi（生产 1Gi）"
  echo "        nginx:    256Mi"
  echo "        tomcat:   4Gi（需同步调整 JVM -Xmx）"
  echo "   3. 减少同时部署的组件数量，先部署核心服务"
  echo ""
  echo "❌ 停止部署，等待调整后再试"
  exit 1
fi

echo "  ✅ 资源规划检查通过"
```

### 4b. JVM vs 容器内存检查

```bash
# ============================================
# Step 4b: JVM vs 容器内存一致性检查 ⭐
# ============================================

echo "🔍 Step 4b: JVM vs 容器内存一致性检查..."

DEPLOY_FILE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "ls ${PROJECT_PATH}/service/tomcat/01-deployment.yml 2>/dev/null || echo ''")

if [ -n "${DEPLOY_FILE}" ]; then
  # 读取容器 memory limit
  CONTAINER_LIMIT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "grep -A2 'memory:' ${DEPLOY_FILE} 2>/dev/null | grep 'limit' | awk '{print \$2}' | head -1" || echo "")

  # 读取 JVM -Xmx
  JVM_XMX=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "grep 'Xmx' ${DEPLOY_FILE} 2>/dev/null | head -1" || echo "")

  echo "     容器 memory limit: ${CONTAINER_LIMIT:-未设置}"
  echo "     JVM -Xmx: ${JVM_XMX:-未在配置中找到，请在镜像启动脚本中确认}"

  if [ -n "${CONTAINER_LIMIT}" ] && [ -n "${JVM_XMX}" ]; then
    # 提取数值（Gi/g/m 单位）
    CONV_LIMIT=$(echo "${CONTAINER_LIMIT}" | sed 's/Gi/*1024/g; s/Mi//g; s/G/*1024/g; s/M//g' | bc 2>/dev/null || echo "0")
    JVM_VAL=$(echo "${JVM_XMX}" | grep -oP 'Xmx\K[\d]+' || echo "0")
    JVM_UNIT=$(echo "${JVM_XMX}" | grep -oP 'Xmx\d+\K[a-zA-Z]+' || echo "m")
    if [ "${JVM_UNIT}" = "g" ]; then
      JVM_MEM=$(echo "${JVM_VAL} * 1024" | bc)
    else
      JVM_MEM="${JVM_VAL}"
    fi

    LIMIT_MIB=$(echo "${CONV_LIMIT}" | bc)
    if [ "${JVM_MEM}" -gt $((LIMIT_MIB - 512))" ] 2>/dev/null; then
      echo ""
      echo "❌ 风险：JVM -Xmx (${JVM_XMX}) 接近或超过容器 memory limit (${CONTAINER_LIMIT})"
      echo "   修复：将 -Xmx 降低到容器 limit 的 60-70%"
      echo "   示例：limit=${CONTAINER_LIMIT} → -Xmx 应设置为 1536m 或 2g"
      echo ""
      echo "❌ JVM 内存配置不合理，部署会导致 OOMKilled，立即停止"
      exit 1
    else
      echo "  ✅ JVM 内存配置合理"
    fi
  fi
fi
```

### 4c. K8s 环境适配检测（硬编码地址检测）

```bash
# ============================================
# Step 4c: K8s 环境适配检测
# 检测硬编码本地地址（127.0.0.1/localhost）
# ============================================

echo "🔍 Step 4c: K8s 环境适配检测..."

K8S_SERVICES=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get svc -n ${NAMESPACE} -o jsonpath='{.items[*].metadata.name}'" 2>/dev/null || echo "")
echo "  集群 Services: ${K8S_SERVICES}"

declare -A PORT_SERVICE_MAP=(
  ["6379"]="redis:REDIS_HOST"
  ["3306"]="mysql:DB_HOST"
  ["27017"]="mongodb:MONGODB_HOST"
  ["5432"]="postgres:DB_HOST"
)

ISSUES_FOUND=0

CONFIG_FILES=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "find ${PROJECT_PATH}/service -type f \( -name '*.yml' -o -name '*.yaml' -o -name '*.properties' \) 2>/dev/null" || echo "")

for config_file in ${CONFIG_FILES}; do
  case "${config_file}" in
    *configmap*|*kustomization*|*namespace*|*ingress*|*gateway*|*route*|*certificate*|*secret*) continue ;;
  esac

  HARDCODED=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "grep -n '127\\.0\\.0\\.1\\|localhost' ${config_file} 2>/dev/null | \
     grep -v '^[#;]' | grep -v 'http://localhost' | grep -v 'https://localhost' || true")

  if [ -n "${HARDCODED}" ]; then
    ISSUES_FOUND=1
    echo ""
    echo "❌ 检测到疑似硬编码本地地址: ${config_file}"
    echo "${HARDCODED}" | head -5
    echo ""
    echo "  💡 修复方式：在 Deployment env 中添加对应环境变量（如 REDIS_HOST=redis）"
    echo "  ⚠️  注意：如果配置硬编码在 WAR/JAR 包内，环境变量注入无效，"
    echo "          必须修改源码重新打包"
    echo ""
    echo "❌ 检测到不可修复的硬编码配置，部署会在 K8s 环境失败，立即停止"
    exit 1
  fi
done

[ "${ISSUES_FOUND}" = "0" ] && echo "  ✅ 未检测到明显的硬编码本地地址问题"
```

### 4d. 资源自动协调（检测到问题后自动修复，不提问）

```bash
# ============================================
# Step 4d: 资源自动协调 ⭐ （无需提问）
# ⚠️ 每次部署前无条件执行，防止配置被他人手动改坏（配置漂移）
# 内存超限则自动压缩，JVM 越限则自动降 heap，无需提问
# ============================================

echo "🔍 Step 4d: 资源自动协调..."

# --- 获取节点可用内存 ---
NODE_TOTAL_MEM_KIB=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get node -o jsonpath='{.items[0].status.capacity.memory}' 2>/dev/null" || echo "0")
NODE_TOTAL_MEM_GI=$((NODE_TOTAL_MEM_KIB / 1024 / 1024))
K8S_RESERVED_GI=3
AVAILABLE_MEM_GI=$((NODE_TOTAL_MEM_GI - K8S_RESERVED_GI))
SAFE_LIMIT_GI=$((AVAILABLE_MEM_GI * 80 / 100))  # 80% 安全线

echo "     节点总内存: ${NODE_TOTAL_MEM_GI} Gi"
echo "     K8s 系统保留: ${K8S_RESERVED_GI} Gi"
echo "     可用内存: ${AVAILABLE_MEM_GI} Gi"
echo "     安全上限（80%）: ${SAFE_LIMIT_GI} Gi"

# --- 遍历所有组件，扫描 memory limits ---
COMPONENTS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "ls -d ${PROJECT_PATH}/service/*/ 2>/dev/null" || echo "")

declare -A COMP_MEM_LIMIT
declare -A COMP_CPU_LIMIT
declare -A COMP_MEM_REQ
declare -A COMP_CPU_REQ
TOTAL_LIMIT_GI=0

for comp_dir in ${COMPONENTS}; do
  COMP_NAME=$(basename "${comp_dir}")
  DEPLOY_FILE="${comp_dir}01-deployment.yml"
  
  if [ ! -f "${DEPLOY_FILE}" ]; then
    # 本地文件检查
    DEPLOY_FILE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "ls ${comp_dir}01-deployment.yml 2>/dev/null || echo ''")
  fi
  
  if [ -n "${DEPLOY_FILE}" ] && ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "[ -f '${DEPLOY_FILE}' ]" 2>/dev/null; then
    # 提取 memory limit（limit 在 requests 前面）
    MEM_LINE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "grep -n 'memory:' ${DEPLOY_FILE} 2>/dev/null | head -2" || echo "")
    
    if [ -n "${MEM_LINE}" ]; then
      # 解析 limit 和 request（交替出现：limit, request, limit, request...）
      MEM_VALUES=$(echo "${MEM_LINE}" | awk -F: '{print $2}' | xargs)
      MEM_LIMIT=$(echo "${MEM_VALUES}" | awk '{print $1}')
      MEM_REQ=$(echo "${MEM_VALUES}" | awk '{print $2}')
      
      # 统一转换为 Mi
      convert_mem() {
        echo "$1" | sed 's/Gi$/*1024/g; s/Mi$//g; s/G$/*1024/g; s/M$//g' | bc 2>/dev/null || echo "0"
      }
      
      LIMIT_MI=$(convert_mem "${MEM_LIMIT}")
      REQ_MI=$(convert_mem "${MEM_REQ}")
      
      TOTAL_LIMIT_GI=$((TOTAL_LIMIT_GI + LIMIT_MI / 1024))
      
      COMP_MEM_LIMIT["${COMP_NAME}"]="${LIMIT_MI}"
      COMP_MEM_REQ["${COMP_NAME}"]="${REQ_MI}"
    fi
  fi
done

echo "     各组件 limits 之和: ${TOTAL_LIMIT_GI} Gi"

# --- 资源超限检测 + 自动压缩 ---
if [ ${TOTAL_LIMIT_GI} -gt ${AVAILABLE_MEM_GI} ] 2>/dev/null; then
  echo ""
  echo "⚠️  资源超限！自动压缩内存配置..."
  
  RATIO=$((AVAILABLE_MEM_GI * 100 / TOTAL_LIMIT_GI))
  NEW_LIMIT_GI=$((AVAILABLE_MEM_GI * 90 / 100))  # 按可用量的 90% 分配
  
  for comp_dir in ${COMPONENTS}; do
    COMP_NAME=$(basename "${comp_dir}")
    DEPLOY_FILE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "ls ${comp_dir}01-deployment.yml 2>/dev/null || echo ''")
    
    [ -z "${DEPLOY_FILE}" ] && continue
    
    OLD_LIMIT_MI=${COMP_MEM_LIMIT["${COMP_NAME}"]}
    OLD_REQ_MI=${COMP_MEM_REQ["${COMP_NAME}"]}
    
    [ "${OLD_LIMIT_MI}" = "0" ] && continue
    
    NEW_LIMIT_MI=$((OLD_LIMIT_MI * NEW_LIMIT_GI * 100 / TOTAL_LIMIT_GI / 100))
    NEW_REQ_MI=$((OLD_REQ_MI * NEW_LIMIT_GI * 100 / TOTAL_LIMIT_GI / 100))
    
    # 保证最小值
    [ ${NEW_LIMIT_MI} -lt 64 ] && NEW_LIMIT_MI=64
    [ ${NEW_REQ_MI} -lt 32 ] && NEW_REQ_MI=32
    [ ${NEW_REQ_MI} -gt ${NEW_LIMIT_MI} ] && NEW_REQ_MI=$((NEW_LIMIT_MI / 2))
    
    # 写回 YAML（limit 在前，request 在后）
    MEM_LIMIT_STR=""
    MEM_REQ_STR=""
    if [ ${NEW_LIMIT_MI} -ge 1024 ]; then
      MEM_LIMIT_STR="$((NEW_LIMIT_MI / 1024))Gi"
    else
      MEM_LIMIT_STR="${NEW_LIMIT_MI}Mi"
    fi
    if [ ${NEW_REQ_MI} -ge 1024 ]; then
      MEM_REQ_STR="$((NEW_REQ_MI / 1024))Gi"
    else
      MEM_REQ_STR="${NEW_REQ_MI}Mi"
    fi
    
    ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "sed -i 's/memory: [0-9]*[GM]i\?/memory: ${MEM_LIMIT_STR}/2' ${DEPLOY_FILE}" 2>/dev/null
    
    echo "     ${COMP_NAME}: ${OLD_LIMIT_MI}Mi → ${NEW_LIMIT_MI}Mi"
  done
  
  echo "  ✅ Step 4d 资源自动压缩完成"
else
  echo "  ✅ Step 4d 资源检查通过，无需调整"
fi

# --- JVM 内存自动修正 ---
TOMCAT_DEPLOY=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "ls ${PROJECT_PATH}/service/tomcat/01-deployment.yml 2>/dev/null || echo ''")

if [ -n "${TOMCAT_DEPLOY}" ] && ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "[ -f '${TOMCAT_DEPLOY}' ]" 2>/dev/null; then
  JVM_XMX=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "grep -oP 'Xmx\d+[gGmMkK]' ${TOMCAT_DEPLOY} 2>/dev/null | head -1" || echo "")
  
  if [ -n "${JVM_XMX}" ]; then
    TOMCAT_LIMIT_MI=${COMP_MEM_LIMIT["tomcat"]}
    
    if [ -n "${TOMCAT_LIMIT_MI}" ] && [ "${TOMCAT_LIMIT_MI}" != "0" ]; then
      # JVM 堆内存建议上限 = 容器 limit * 70%
      RECOMMEND_JVM_MI=$((TOMCAT_LIMIT_MI * 70 / 100))
      
      JVM_VAL=$(echo "${JVM_XMX}" | grep -oP '\d+' | head -1)
      JVM_UNIT=$(echo "${JVM_XMX}" | grep -oP '[gGmMkK]+$' | tr '[:upper:]' '[:lower:]')
      
      case "${JVM_UNIT}" in
        g)  JVM_CURRENT_MI=$((JVM_VAL * 1024)) ;;
        m)  JVM_CURRENT_MI=${JVM_VAL} ;;
        k)  JVM_CURRENT_MI=$((JVM_VAL / 1024)) ;;
        *)  JVM_CURRENT_MI=${JVM_VAL} ;;
      esac
      
      echo "     tomcat 容器 limit: ${TOMCAT_LIMIT_MI} Mi"
      echo "     JVM 当前 -Xmx: ${JVM_CURRENT_MI} Mi"
      echo "     JVM 建议上限: ${RECOMMEND_JVM_MI} Mi"
      
      if [ ${JVM_CURRENT_MI} -gt ${RECOMMEND_JVM_MI} ]; then
        echo "⚠️  JVM -Xmx 超过容器 limit，自动下调..."
        
        if [ ${RECOMMEND_JVM_MI} -ge 1024 ]; then
          NEW_JVM_STR="-Xmx$((RECOMMEND_JVM_MI / 1024))g -Xms$((RECOMMEND_JVM_MI / 1024))g"
        else
          NEW_JVM_STR="-Xmx${RECOMMEND_JVM_MI}m -Xms${RECOMMEND_JVM_MI}m"
        fi
        
        ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
          "sed -i 's/-Xmx[0-9]*[gGmMkK]* -Xms[0-9]*[gGmMkK]*/${NEW_JVM_STR}/g' ${TOMCAT_DEPLOY}" 2>/dev/null
        
        echo "     JVM -Xmx: ${JVM_CURRENT_MI}Mi → ${RECOMMEND_JVM_MI}Mi"
        echo "  ✅ Step 4d JVM 自动修正完成"
      else
        echo "  ✅ Step 4d JVM 内存检查通过"
      fi
    fi
  fi
fi
```

**⚠️ 铁律：Step 4d 完成后 → 必须重新执行 Step 5 (generate.sh) → 才能 kubectl apply**

---

### 4e. Probe 路径自动探测与修复（检测到 Ready=0 时自动执行，无需提问）

```bash
# ============================================
# Step 4e: Probe 路径自动探测与修复 ⭐ （无需提问）
# 检测机制：Pod Running 但 READY=0，且 HTTP probe 返回 404
# 自动判断：应用未实现 /actuator 路径 → 将 probe 改为 tcpSocket
# ============================================

PROBE_FIX_FLAG="false"

# 检查是否有 Pod 处于 Running 但不 Ready 状态
NOT_READY_PODS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} --field-selector=status.phase=Running -o jsonpath='{.items[?(@.status.containerStatuses[0].state.running!=null && @.status.containerStatuses[0].ready==false)].metadata.name}'" 2>/dev/null || echo "")

if [ -n "${NOT_READY_PODS}" ]; then
  echo "🔍 Step 4e: 检测到 Ready=0 的 Pod，正在诊断..."
  for POD_NAME in ${NOT_READY_PODS}; do
    echo "     检查 Pod: ${POD_NAME}"
    
    # 获取当前 probe 类型和路径
    PROBE_TYPE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "kubectl get pod ${POD_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.containers[0].startupProbe.httpGet.path}'" 2>/dev/null || echo "NONE")
    
    if [ "${PROBE_TYPE}" != "NONE" ]; then
      # 尝试探测该路径是否返回 404
      POD_IP=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "kubectl get pod ${POD_NAME} -n ${NAMESPACE} -o jsonpath='{.status.podIP}'" 2>/dev/null || echo "")
      PORT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "kubectl get pod ${POD_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.containers[0].startupProbe.httpGet.port}'" 2>/dev/null || echo "")
      
      if [ -n "${POD_IP}" ] && [ -n "${PORT}" ]; then
        HTTP_CODE=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
          "kubectl exec -n ${NAMESPACE} ${POD_NAME} -c tomcat -- wget -qO- -S http://localhost:${PORT}${PROBE_TYPE} 2>&1 | grep 'HTTP/' | awk '{print \$2}'" 2>/dev/null || echo "000")
        echo "     HTTP probe 路径 ${PROBE_TYPE} → 状态码: ${HTTP_CODE}"
        
        if [ "${HTTP_CODE}" = "404" ]; then
          echo "⚠️  检测到 HTTP probe 路径返回 404，应用未实现该端点"
          PROBE_FIX_FLAG="true"
        fi
      fi
    else
      echo "     startProbe 使用 tcpSocket，无需修复"
    fi
  done
  
  if [ "${PROBE_FIX_FLAG}" = "true" ]; then
    echo "⚠️  HTTP probe 返回 404 → 自动修复：将所有 probe 改为 tcpSocket"
    TOMCAT_DEPLOY=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
      "ls ${PROJECT_PATH}/service/tomcat/01-deployment.yml 2>/dev/null" || echo "")
    
    if [ -n "${TOMCAT_DEPLOY}" ]; then
      # 永久修改源码 YAML（generate.sh 后自动生效）
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "perl -i -0777 -pe 's/(startupProbe:\n\s+)httpGet:\n\s+path: [^\n]+\n\s+port: ([^\n]+)\n/\1tcpSocket:\n            port: \2\n/' ${TOMCAT_DEPLOY}" 2>/dev/null
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "perl -i -0777 -pe 's/(readinessProbe:\n\s+)httpGet:\n\s+path: [^\n]+\n\s+port: ([^\n]+)\n/\1tcpSocket:\n            port: \2\n/' ${TOMCAT_DEPLOY}" 2>/dev/null
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "perl -i -0777 -pe 's/(livenessProbe:\n\s+)httpGet:\n\s+path: [^\n]+\n\s+port: ([^\n]+)\n/\1tcpSocket:\n            port: \2\n/' ${TOMCAT_DEPLOY}" 2>/dev/null
      # 缩短 initialDelaySeconds（从 600s 改为 60s）
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "sed -i 's/initialDelaySeconds: 600/initialDelaySeconds: 60/' ${TOMCAT_DEPLOY}" 2>/dev/null
      # 降低 failureThreshold（从 200 改为 30）
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "sed -i 's/failureThreshold: 200/failureThreshold: 30/' ${TOMCAT_DEPLOY}" 2>/dev/null
      
      echo "  ✅ Step 4e probe 已改为 tcpSocket（源码已更新，generate.sh 后生效）"
      echo "  💡 已同时修复：startupProbe + readinessProbe + livenessProbe"
    fi
  fi
else
  echo "     Step 4e: 未检测到 Ready=0 的 Pod，跳过 probe 检测"
fi
```

### 4f. Redis 配置检查与自动修复（部署前无条件执行）

```bash
# ============================================
# Step 4f: Redis 配置检查与修复 ⭐
# 检测时机：generate.sh 后、kubectl apply 前
# 检测目标：tomcat deployment 是否缺少 webapps-classes volume
# 自动判断：WAR 包内 application-dev.yml 硬编码 host: 127.0.0.1
# 修复方式：volume mount 覆盖 + 写入源码 YAML（永久生效）
# ============================================

echo "🔍 Step 4f: Redis 配置检查..."

if [ ! -d "${PROJECT_PATH}/service/tomcat" ]; then
  echo "     非 tomcat 项目，跳过 Step 4f"
  return 0
fi

# 检查当前 deployment 是否已有 webapps-classes volume
WEBAPP_VOL=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST}   "export KUBECONFIG=/etc/kubernetes/admin.conf &&    kubectl get deployment -n ${NAMESPACE} -o jsonpath='{.items[*].spec.template.spec.volumes[*].name}' 2>/dev/null | grep -w webapps-classes || echo 'NOT_FOUND'" 2>/dev/null || echo "NOT_FOUND")

if [ "${WEBAPP_VOL}" != "NOT_FOUND" ]; then
  echo "     Step 4f: webapps-classes volume 已存在，跳过"
  return 0
fi

echo "     检测到缺少 webapps-classes volume（可能导致 Redis 硬编码问题）"

# 从运行中 pod 导出配置（如果存在）
TOMCAT_POD=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST}   "kubectl get pods -n ${NAMESPACE} -l app=tomcat    -o jsonpath='{.items[0].metadata.name}' --field-selector=status.phase=Running 2>/dev/null" || echo "")

if [ -z "${TOMCAT_POD}" ]; then
  echo "     Step 4f: 无运行中 pod，跳过（generate.sh 后若仍缺则重新检测）"
  return 0
fi

# 检查 pod 内配置文件的 host 值
REDIS_HOST_IN_POD=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST}   "kubectl exec -n ${NAMESPACE} ${TOMCAT_POD} -c tomcat --    grep '^[[:space:]]*host:' /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml 2>/dev/null | head -1" || echo "")

if ! echo "${REDIS_HOST_IN_POD}" | grep -q '127.0.0.1'; then
  echo "     Step 4f: Redis host 配置正确，无需修复"
  return 0
fi

echo "⚠️  检测到 host: 127.0.0.1 → 正在自动修复..."

CONFIG_LOCAL="/tmp/application-dev.yml.$$.$RANDOM"
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST}   "kubectl exec -n ${NAMESPACE} ${TOMCAT_POD} -c tomcat --    cat /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml"   > "${CONFIG_LOCAL}" 2>/dev/null

if [ ! -s "${CONFIG_LOCAL}" ]; then
  echo "     ⚠️  无法导出 pod 内配置文件，跳过 Step 4f"
  rm -f "${CONFIG_LOCAL}"
  return 1
fi

sed -i 's/host: 127\.0\.0\.1/host: redis/' "${CONFIG_LOCAL}"

ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST}   "mkdir -p ${PROJECT_PATH}/volumes/tomcat/webapps-classes"
scp -o StrictHostKeyChecking=no -o ConnectTimeout=10   "${CONFIG_LOCAL}"   "${SSH_USER}@${SERVER_HOST}:${PROJECT_PATH}/volumes/tomcat/webapps-classes/application-dev.yml" 2>/dev/null
rm -f "${CONFIG_LOCAL}"

TOMCAT_DEPLOY="${PROJECT_PATH}/service/tomcat/01-deployment.yml"

python3 << PYEOF
import sys
project_path = sys.argv[2]
with open(sys.argv[1], 'r') as f:
    content = f.read()

if 'webapps-classes' in content:
    print('already exists')
    sys.exit(0)

lines = content.split('
')
result = []
i = 0
while i < len(lines):
    line = lines[i]
    result.append(line + '
')
    if line.strip() == '- name: conf' and i+1 < len(lines) and 'mountPath: /usr/local/tomcat/conf' in lines[i+1]:
        result.append('        - name: webapps-classes
')
        result.append('          mountPath: /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes
')
        i += 1
        continue
    if 'name: zoneinfo' in line and i+1 < len(lines) and 'hostPath:' in lines[i+1]:
        result.append('        - name: webapps-classes
')
        result.append('          hostPath:
')
        result.append('            path: ' + project_path + '/volumes/tomcat/webapps-classes
')
        result.append('            type: DirectoryOrCreate
')
    i += 1

with open(sys.argv[1], 'w') as f:
    f.writelines(result)
print('done')
PYEOF
"${TOMCAT_DEPLOY}" "${PROJECT_PATH}"

echo "  ✅ Step 4f: webapps-classes volume 已写入源码 YAML（永久生效）"
echo "  💡 host: 127.0.0.1 → host: redis"
```

---

## Step 5: 生成清单（必须）

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  📝 Step 5: 生成清单"
echo "═══════════════════════════════════════════════════════"
echo "  项目路径: ${PROJECT_PATH}"
echo "  清单输出: ${RELEASE_PATH}"
echo "  ➤ 执行 generate.sh（预计 10-30 秒）..."
echo ""

GENERATE_OUTPUT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "cd ${PROJECT_PATH} && bash generate.sh 2>&1" \
  || { echo "❌ generate.sh 执行失败"; echo "${GENERATE_OUTPUT}"; exit 1; })

echo "${GENERATE_OUTPUT}"

RELEASE_COUNT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "ls ${RELEASE_PATH}/ 2>/dev/null | wc -l" || echo "0")
if [ "${RELEASE_COUNT}" = "0" ]; then
  echo "❌ generate.sh 未生成任何清单文件"
  exit 1
fi
echo ""
echo "  ✅ Step 5 生成 ${RELEASE_COUNT} 个清单文件"
```

---

## Step 6: 部署前审查（diff / dry-run）

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  🔍 Step 6: 部署前审查"
echo "═══════════════════════════════════════════════════════"

if [ "${SKIP_PREVIEW:-false}" = "true" ]; then
  echo "  ⏭️  跳过预览（SKIP_PREVIEW=true）"
else
  echo "  ➤ kubectl diff -n ${NAMESPACE}（预计 10-30 秒）..."
  DIFF_OUTPUT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "kubectl diff -n ${NAMESPACE} -f ${RELEASE_PATH}/ 2>&1" || true)

  # 检测致命错误：CRD 缺失、namespace 不匹配、语法错误
  DIFF_ERRORS=$(echo "${DIFF_OUTPUT}" | grep -iE "no matches for kind|namespace.*does not match|not found|^error:|invalid|cannot bind" | head -10 || true)
  if [ -n "${DIFF_ERRORS}" ]; then
    echo ""
    echo "❌ kubectl diff 发现致命错误，立即停止："
    echo "${DIFF_ERRORS}" | head -10
    echo ""
    echo "💡 常见错误修复："
    echo "   - no matches for kind HTTPRoute：先安装 Gateway API CRD"
    echo "   - namespace 不匹配：分开 apply Gateway（istio-system）和应用资源"
    echo "   - Invalid value：检查 release/ 目录下的 YAML 文件"
    exit 1
  fi

  [ -n "${DIFF_OUTPUT}" ] && echo "${DIFF_OUTPUT}" | head -50

  echo ""
  echo "  ✅ Step 6 审查通过"
  echo "  💡 如确认无误: SKIP_PREVIEW=true <原命令>"
fi
```

---

## Step 7: 应用部署

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  🚀 Step 7: 应用部署"
echo "═══════════════════════════════════════════════════════"
echo "  ➤ kubectl apply -n ${NAMESPACE}（预计 30-120 秒）..."
echo ""

APPLY_OUTPUT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/ 2>&1" \
  || {
    if [ "${FORCE_APPLY:-false}" = "true" ]; then
      echo "  ⚠️  apply 失败，尝试 --force-conflicts..."
      ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
        "kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/ --force-conflicts 2>&1"
    else
      echo "❌ apply 失败，修复后重试，或 FORCE_APPLY=true"
      exit 1
    fi
  })

echo "${APPLY_OUTPUT}"

# 统计资源操作
echo ""
echo "  📊 资源操作汇总："
CREATED_COUNT=$(echo "${APPLY_OUTPUT}" | grep -c "created" || echo "0")
CONFIGURED_COUNT=$(echo "${APPLY_OUTPUT}" | grep -c "configured" || echo "0")
UNCHANGED_COUNT=$(echo "${APPLY_OUTPUT}" | grep -c "unchanged" || echo "0")
echo "   created: ${CREATED_COUNT}"
echo "   configured: ${CONFIGURED_COUNT}"
echo "   unchanged: ${UNCHANGED_COUNT}"

echo ""
echo "  ✅ Step 7 部署命令执行完成"
```

---

## Step 8: 等待就绪

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ⏳ Step 8: 等待 Pod 就绪"
echo "═══════════════════════════════════════════════════════"
echo "  超时设置：${WAIT_TIMEOUT:-600}s"
echo ""

WAIT_RESULT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "timeout ${WAIT_TIMEOUT:-600} kubectl get pods -n ${NAMESPACE} -o wide -w 2>&1" \
  || echo "TIMEOUT")

# 检测致命状态：OOMKilled / Error / CrashLoopBackOff → 立即停止
OOM_PODS=$(echo "${WAIT_RESULT}" | grep -E "OOMKilled|Error|CrashLoopBackOff" | head -5 || true)
if [ -n "${OOM_PODS}" ]; then
  echo ""
  echo "❌ 检测到异常 Pod 状态，立即停止："
  echo "${OOM_PODS}"
  exit 1
fi

# 超时且仍有 Pending → 资源不足，停止
if echo "${WAIT_RESULT}" | grep -q "TIMEOUT"; then
  PENDING=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
    "kubectl get pods -n ${NAMESPACE} 2>&1" | grep -E "Pending|ContainerCreating" || true)
  if [ -n "${PENDING}" ]; then
    echo ""
    echo "❌ Pod 卡在 Pending 超过 ${WAIT_TIMEOUT:-600}s，资源不足或调度失败，立即停止"
    echo "${PENDING}"
    exit 1
  fi
fi

echo "  ✅ Step 8 等待完成"
echo ""
echo "  📦 当前 Pod 状态："
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} -o wide 2>&1"
```

**超时说明**：
| 组件类型 | 建议超时 |
|---------|---------|
| Redis/MySQL | 3-5 分钟 |
| Tomcat 等 Java | 5-10 分钟 |
| 前端/纯静态 | 1-2 分钟 |

---

## Step 9: 健康检查

```bash
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  📋 Step 9: 健康检查"
echo "═══════════════════════════════════════════════════════"

# 获取节点内存信息
NODE_MEM=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "free -h | grep Mem" 2>/dev/null || echo "unknown")
echo "  节点内存状态: ${NODE_MEM}"

# 获取所有 Pod 状态
echo ""
echo "  📦 Pod 状态："
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} -o wide 2>&1"

# 统计 Ready 数量
READY_COUNT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} -o jsonpath='{range .items[*]}{.status.conditions[?(@.type==\\"Ready\\")].status}{\"\\n\"}{end}' 2>/dev/null" | grep -c "True" || echo "0")
TOTAL_COUNT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} 2>/dev/null | tail -n +2 | wc -l" || echo "0")
echo ""
echo "  ✅ 就绪比例: ${READY_COUNT}/${TOTAL_COUNT}"

# Service 状态
echo ""
echo "  🌐 Service 状态："
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get svc -n ${NAMESPACE} 2>&1"

# Gateway 状态
echo ""
echo "  🚪 Gateway 状态："
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get gateway -n istio-system 2>&1 || kubectl get gateway -n ${NAMESPACE} 2>&1"

# HTTPRoute 状态
echo ""
echo "  🛣️  HTTPRoute 状态："
ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get httproute -n ${NAMESPACE} 2>&1"

echo ""
echo "  ✅ Step 9 健康检查完成"
```

---

## 🎉 部署最终状态报告（每次部署后必须输出）

```bash
# ============================================================
# 🎉 部署最终状态报告
# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           🎉 <项目名> K8s 部署完成报告                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 部署概况"
echo "   项目：<项目名>"
echo "   服务器：${SERVER_HOST}"
echo "   命名空间：${NAMESPACE}"
echo "   源码来源：<Git/本地/服务器已有>"
echo "   部署时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Pod 汇总
POD_SUMMARY=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} -o wide 2>&1" || echo "")
echo "📦 Pod 最终状态"
echo "${POD_SUMMARY}"
echo ""

# 统计
READY_OK=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} -o jsonpath='{range .items[*]}{.status.conditions[?(@.type==\\"Ready\\")].status}{\"\\n\"}{end}' 2>/dev/null" | grep -c "True" || echo "0")
TOTAL_PODS=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} 2>/dev/null | tail -n +2 | wc -l" || echo "0")
OOM_COUNT=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "kubectl get pods -n ${NAMESPACE} 2>/dev/null | grep -c OOMKilled" || echo "0")

echo "📊 部署统计"
echo "   就绪 Pod：${READY_OK}/${TOTAL_PODS}"
echo "   OOMKilled：${OOM_COUNT}"
echo ""

# 资源使用
MEM_USED=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "free -h | grep Mem" 2>/dev/null | awk '{print $3}')
MEM_TOTAL=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} "free -h | grep Mem" 2>/dev/null | awk '{print $2}')
echo "🖥️  节点资源"
echo "   内存使用：${MEM_USED} / ${MEM_TOTAL}"
echo ""

# 各组件 limits 总和
LIMITS_SUM=$(ssh -p ${SSH_PORT:-22} ${SSH_USER}@${SERVER_HOST} \
  "cd ${PROJECT_PATH} && grep -r 'memory:' service/*/01-deployment.yml 2>/dev/null | grep 'limit' | awk '{print $2}' | sed 's/Gi//g; s/Mi//g' | paste -sd+ | bc" 2>/dev/null || echo "unknown")
echo "⚙️  资源配置"
echo "   所有组件 memory limits 之和：${LIMITS_SUM} Gi"
echo ""

# 使用说明
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     使用方法                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📌 查看 Pod 状态"
echo "   kubectl get pods -n ${NAMESPACE} -o wide"
echo ""
echo "📌 查看日志"
echo "   kubectl logs -n ${NAMESPACE} -l app=tomcat --tail=100"
echo ""
echo "📌 进入容器"
echo "   kubectl exec -it -n ${NAMESPACE} <pod-name> -- /bin/bash"
echo ""
echo "📌 重启组件"
echo "   kubectl rollout restart deployment/<name> -n ${NAMESPACE}"
echo ""
echo "📌 扩缩容"
echo "   kubectl scale deployment <name> -n ${NAMESPACE} --replicas=3"
echo ""
echo "📌 更新配置"
echo "   1. 修改 service/<component>/01-deployment.yml"
echo "   2. cd ${PROJECT_PATH} && bash generate.sh"
echo "   3. kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   常见问题排查                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "   Pod 卡 Pending：kubectl describe pod <pod> -n ${NAMESPACE}"
echo "   Pod OOMKilled ：kubectl describe pod <pod> -n ${NAMESPACE} | grep -A5 OOM"
echo "   Service 不可用：kubectl get svc -n ${NAMESPACE} && kubectl get endpoints -n ${NAMESPACE}"
echo "   路由 404      ：kubectl get httproute -n ${NAMESPACE}"
echo ""
echo "──────────────────────────────────────────────────────────────"
echo "🎉 部署完成！报告生成时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "──────────────────────────────────────────────────────────────"
echo ""
```

---

## 🩺 错误诊断链路手册

> **使用说明**：遇到错误时，按"错误现象"定位到对应章节，
> 按顺序执行"诊断步骤"，找到"根因"后用"修复方案"处理。
> 修复后需要重新 apply 并等待就绪。

---

### 🔴 错误 1：OOMKilled

**错误现象**：`kubectl get pods` 显示 `OOMKilled`，或 `STATUS` 为 `OOMKilled`

#### 诊断链路

**Step 1：确认 OOM 来自哪个容器**
```bash
kubectl describe pod <pod-name> -n <namespace> | grep -A5 'Last State'
# 或查看当前状态的 Last State
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | {name, lastState}'
```
→ 确认是主容器 OOM 还是 sidecar/init container OOM

**Step 2：判断是 JVM 还是系统进程 OOM**

**如果是 JVM（Java 容器）：**
```bash
# 查当前 JVM -Xmx 配置
kubectl logs <pod> -n <namespace> 2>&1 | grep -i 'heap\|Xmx\|JVM\|Picked up JAVA'
# 或
kubectl exec <pod> -n <namespace> -- sh -c 'echo $JAVA_TOOL_OPTIONS'
```

**同时查容器 memory limit：**
```bash
kubectl get pod <pod-name> -n <namespace> -o json | jq '.spec.containers[0].resources.limits.memory'
```

**如果 JVM -Xmx >= 容器 limit → 根因确认：JVM 内存配置超过容器限制**

**如果是 init container OOM：**
```bash
kubectl logs <pod> -n <namespace> -c <init-container-name> 2>&1 | tail -5
```
→ 很可能 init container 用的是同一大型 Java 镜像，JVM 启动即 OOM

**Step 3：确认修复优先级**
- 主容器 JVM OOM → 降低 -Xmx 到容器 limit 的 60-70%
- init container OOM → **禁止**在 init container 里运行 Java/JVM，用 busybox + sed 代替

#### 修复方案

**主容器 JVM -Xmx 过大：**
```bash
# 方案A：patch JAVA_OPTS（不重启 deployment，不重新 apply）
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"-server ... -Xms1536m -Xmx1536m ..."}]'

# 方案B：修改 release yaml 后重新 generate + apply
# 在 service/tomcat/01-deployment.yml 中把 -Xmx 调小，然后重新 generate
```

**Init container OOM：**
```bash
# 删除 init container，改用环境变量或 busybox 方案
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"remove","path":"/spec/template/spec/initContainers"}]'
```

---

### 🔴 错误 2：Pod 卡在 Pending（Insufficient memory）

**错误现象**：`kubectl get pods` 显示 `Pending`，Events 里有 `Insufficient memory`

#### 诊断链路

**Step 1：查节点总内存和已分配内存**
```bash
kubectl describe node <node-name> | grep -A 8 'Allocated resources'
# 查看 memory 栏：Requests 和 Limits 各占多少百分比
```

**Step 2：列出所有组件的 memory requests/limits**
```bash
for dep in $(kubectl get deployment -n <namespace> -o jsonpath='{.items[*].metadata.name}'); do
  lim=$(kubectl get deployment $dep -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}' 2>/dev/null)
  rep=$(kubectl get deployment $dep -n <namespace> -o jsonpath='{.spec.replicas}' 2>/dev/null)
  echo "$dep: replicas=$rep limit=$lim"
done
```

**Step 3：判断是绝对不足还是碎片化**

| 情况 | 特征 | 处理 |
|------|------|------|
| limits 之和 > 节点内存 | 绝对不足 | 降低各组件 limits |
| limits 之和 < 节点内存，但 still Pending | 内存碎片化 | 先缩容空闲组件，调度后再扩回去 |
| 单个组件请求 > 节点可用最大连续块 | 碎片化 | 降低该组件 request/limit |

**Step 4：如果有多个 ReplicaSet 同时存在**
```bash
kubectl get rs -n <namespace> -l app=<component>
```
→ 多个 RS 各有 replicas，会重复计算内存需求！删掉多余的 RS。

#### 修复方案

**降低组件内存 limit（最常见）：**
```bash
kubectl patch deployment <name> -n <namespace> --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"2Gi"},
  {"op":"replace","path":"/spec/template/spec/containers/0/resources/requests/memory","value":"1Gi"}
]'
```

**清理多余 ReplicaSet：**
```bash
# 找出所有 RS
kubectl get rs -n <namespace> -l app=<component>
# 删除不想要的（DESIRED=0 的那些）
kubectl delete rs <rs-name> -n <namespace>
```

**内存碎片时：先缩容再调度：**
```bash
kubectl scale deployment <name> -n <namespace> --replicas=0
# 等 Pending pod 消失后再扩回
kubectl scale deployment <name> -n <namespace> --replicas=1
```

---

### 🔴 错误 3：Pod Running 但不 Ready（readiness probe 失败）

**错误现象**：`READY 0/1`，但 `STATUS` 是 `Running`，应用日志正常

#### 诊断链路

**Step 1：确认是哪种 probe 失败**
```bash
kubectl describe pod <pod-name> -n <namespace> | grep -E 'Readiness|Liveness|Startup'
```

**Step 2：针对不同 probe 类型排查**

**HTTP probe 404：**
```bash
# 拿到 pod IP
POD_IP=$(kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.podIP}')
# curl 探测路径
curl -s -o /dev/null -w '%{http_code}' http://<POD_IP>:<port><path>
```
→ 返回 404 说明应用没有这个端点

**TCP probe 失败：**
```bash
# 从同节点其他 pod 测试
kubectl exec -n <namespace> <other-pod> -- nc -zv <pod-ip> <port>
# 或从节点上 curl
ssh <user>@<node> curl -s -o /dev/null -w '%{http_code}' http://<pod-ip>:<port>/
```
→ 端口能连但 probe 仍失败，可能是 Cilium eBPF 和 kubelet 探针兼容性问题

**Exec probe 失败：**
```bash
kubectl logs <pod> -n <namespace> -c <container> --tail=5
```

**Step 3：检查容器实际启动状态**
```bash
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | {name, ready, started, restartCount}'
```
→ 如果 `started: false` 但容器 running，说明容器主进程未正常启动（通常是 Java 应用启动太慢，或启动命令被覆盖）

**Step 4：确认应用是否真正就绪（与 K8s 无关）**
```bash
# 在 pod 内测试
kubectl exec -n <namespace> <pod-name> -- wget -q -O- http://localhost:<port>/
# 或 curl
kubectl exec -n <namespace> <pod-name> -- curl -s http://localhost:<port>/
```

#### 修复方案

**方案 A（推荐）：永久修改源码 YAML —— 一劳永逸**

修改 `service/tomcat/01-deployment.yml`，将 3 个 probe 全部改为 `tcpSocket`，直接删掉 `httpGet` 段落：

```yaml
# 原文（会导致 READY 0/1）：
startupProbe:
  httpGet:
    path: /caij_saas/actuator/health/ping
    port: 8787
  initialDelaySeconds: 600
  ...

# 改为（永久生效，generate.sh 后自动应用）：
startupProbe:
  tcpSocket:
    port: 8787
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 60
```

> **注意**：修改源码 YAML 后，每次 `bash generate.sh` 都会生成正确的 probe 配置，无需重复 patch。
> 同时检查 `kustomization.yaml` 的 `replacements` 字段是否会导致 `generate.sh` 失败（如有 hostPath 替换报错，删除相关 replacement 块）。

**方案 B（临时）：手动 kubectl patch —— 每次部署需重做**

```bash
# 改 readinessProbe
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe","value":{"tcpSocket":{"port":8787},"initialDelaySeconds":30,"periodSeconds":10,"failureThreshold":60}}]'

# 改 startupProbe（必须也改，否则 initialDelay 600s 会导致启动极慢）
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/startupProbe","value":{"tcpSocket":{"port":8787},"initialDelaySeconds":5,"periodSeconds":10,"failureThreshold":60}}]'

# 改 livenessProbe（如有必要）
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe","value":{"tcpSocket":{"port":8787},"initialDelaySeconds":120,"periodSeconds":60,"failureThreshold":60}}]'
```

**方案 C（不推荐）：删除 probe**
```bash
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe","value":null}]'
```

**Cilium eBPF 兼容性问题（tcpSocket/exec probe 都失败，但应用实际正常）：**
```bash
# 删掉所有探针
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe","value":null},{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe","value":null}]'
```

---

### 🔴 错误 4：应用连不上 Redis/MySQL（Connection refused/timeout）

**错误现象**：应用日志出现 `Unable to connect to Redis: 127.0.0.1:6379` 或 `地址: 127.0.0.1:6379`

#### 诊断链路

**Step 1：确认 K8s Service 是否存在**
```bash
kubectl get svc -n <namespace> | grep <service-name>
```

**Step 2：从问题 pod 内测试网络连通性**
```bash
# DNS 解析
kubectl exec -n <namespace> <pod-name> -- nslookup <service-name>
# TCP 连通性（从同节点其他 pod）
kubectl exec -n <namespace> <other-pod> -- nc -zv <service-name> <port>
```

**Step 3：确认应用配置的连接地址**
```bash
kubectl logs -n <namespace> <pod-name> --tail=20 | grep -iE '地址: 127|Redis.*127|Unable to connect.*127|refused.*127|redisson'
```

**Step 4：区分是配置问题还是网络问题**

| 日志中的地址 | 根因 | 修复方案 |
|-------------|------|---------|
| `地址: 127.0.0.1:6379` 或 `Unable to connect to Redis server: 127.0.0.1/127.0.0.1:6379` | **配置硬编码**：application-dev.yml 里写了 `host: 127.0.0.1`，环境变量无效 | 见方案B/C |
| `Unable to connect to Redis server: redis:6379`（但 redis service 存在） | 网络策略/Cilium 问题 | 检查 NetworkPolicy |
| 没有任何 Redis 日志但依然连不上 | 可能是延迟连接，后续自行恢复 | 等待30秒再查 |

**Step 5：检查配置文件来源（关键）**
```bash
# 确认应用读的是哪个配置文件
kubectl exec -n <namespace> <pod-name> -c <container> -- \
  find / -name 'application*.yml' 2>/dev/null | grep -v 'proc\|sys'

# 从容器内读取配置文件，检查 host 字段
kubectl exec -n <namespace> <pod-name> -c <container> -- \
  cat /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml | grep -A3 'redis:'
```

#### 修复方案

**方案A（网络问题时用）：环境变量覆盖**
```bash
# 仅当应用通过环境变量读取 Redis 配置时有效
kubectl patch deployment <name> -n <namespace> --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/env/-","value":{"name":"REDIS_HOST","value":"redis"}}]'
```

**方案B（推荐，配置硬编码在 WAR 包内时用）：volume mount 覆盖配置文件**

根因：应用读取的是 WAR 包内的 `application-dev.yml`（`host: 127.0.0.1`），环境变量不生效。

步骤：
```bash
# 1. 从容器内导出原始配置文件
kubectl exec -n <namespace> <pod-name> -c <container> -- \
  cat /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml > /tmp/application-dev.yml

# 2. 修改 host: 127.0.0.1 → host: redis
sed -i 's/host: 127.0.0.1/host: redis/' /tmp/application-dev.yml

# 3. 复制到服务器 volume 目录
ssh <user>@<server> 'mkdir -p <project-path>/volumes/tomcat/webapps-classes'
scp /tmp/application-dev.yml <user>@<server>:<project-path>/volumes/tomcat/webapps-classes/

# 4. patch deployment 添加 volume mount（用 subPath 精确覆盖单个文件）
kubectl patch deployment <name> -n <namespace> --type=json -p=[
  {"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"webapps-classes","hostPath":{"path":"<project-path>/volumes/tomcat/webapps-classes","type":"DirectoryOrCreate"}}},
  {"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"webapps-classes","mountPath":"/usr/local/tomcat/webapps/caij_saas/WEB-INF/classes","subPath":"application-dev.yml"}}
]

# 5. 重启 Pod 生效
kubectl delete pod -n <namespace> -l app=<component>
```

> ⚠️ 注意：如果使用 `subPath` 挂载时报错 `not a directory`，去掉 `subPath`，改为直接挂载整个目录（会覆盖整个 classes 目录，建议确保目录内所有文件都存在）：
> ```bash
> kubectl patch deployment <name> -n <namespace> --type=json -p=[
>   {"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"webapps-classes","hostPath":{"path":"<project-path>/volumes/tomcat/webapps-classes","type":"Directory"}}},
>   {"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"webapps-classes","mountPath":"/usr/local/tomcat/webapps/caij_saas/WEB-INF/classes"}}
> ]
> ```

**方案C（永久修复）：同步修改源码 YAML**

修复后需同步修改源码 `service/tomcat/01-deployment.yml`，否则 `generate.sh` 会覆盖 patch：
1. 在 01-deployment.yml 的 volumes 和 volumeMounts 中加入 webapps-classes volume
2. 确保 volumeMount 使用 subPath 精确覆盖 `application-dev.yml`
3. 后续部署无需重复 patch

#### 验证修复

```bash
# 重启后检查日志中是否还有 Redis 错误
kubectl logs -n <namespace> <new-pod> --tail=20 | grep -iE 'redis|地址.*6379|Connection refused'
# 期望：无输出（无 Redis 错误）

# 确认挂载的文件内容正确
kubectl exec -n <namespace> <new-pod> -c <container> -- \
  cat /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml | grep 'host:'
# 期望：host: redis
```

---

### 🔴 错误 5：ImagePullBackOff

**错误现象**：`kubectl get pods` 显示 `ImagePullBackOff`

#### 诊断链路

**Step 1：确认具体拉取失败原因**
```bash
kubectl describe pod <pod-name> -n <namespace> | grep -A 3 'ImagePullBackOff'
```

**Step 2：常见原因分类**

| 错误信息 | 根因 | 修复命令 |
|---------|------|---------|
| `not found` | 镜像地址错误或不存在 | 确认镜像 tag 正确 |
| `manifest unknown` | 镜像 tag 不存在 | `ctr -n k8s.io images ls \| grep <name>` 查可用 tag |
| `http: server gave HTTP response` | 公网镜像被墙或私有仓库认证失败 | 检查 imagePullSecrets |
| `x509: certificate signed by unknown authority` | 私有仓库 HTTPS 证书问题 | 配置 insecure registry 或导入证书 |

**Step 3：检查私仓认证**
```bash
kubectl get secret -n <namespace> | grep -i docker
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'
```

#### 修复方案

**镜像 tag 错误：**
```bash
# 直接 set image（不改 yaml）
kubectl set image deployment/<name> <container>=<new-image:tag> -n <namespace>
```

**私仓认证缺失：**
```bash
# 创建 docker-registry secret
kubectl create secret docker-registry <secret-name> \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<pass> \
  --docker-email=<email> \
  -n <namespace>

# 关联到 serviceaccount
kubectl patch serviceaccount default -n <namespace> \
  -p '{"imagePullSecrets":[{"name":"<secret-name>"}]}'
```

**手动 tag 镜像到私仓：**
```bash
# 在有公网访问的节点上
sudo ctr -n k8s.io images tag \
  docker.io/<original-image>:<tag> \
  <private-registry>/<image>:<tag>
```

---

### 🔴 错误 6：CrashLoopBackOff

**错误现象**：`STATUS` 为 `CrashLoopBackOff`，`RESTARTS` 不断增加

#### 诊断链路

**Step 1：看上一次退出的退出码和日志**
```bash
kubectl logs -n <namespace> <pod-name> --previous 2>&1 | tail -30
```

**Step 2：常见原因**

| 退出码 | 常见原因 |
|--------|---------|
| 137 (SIGKILL) | OOMKilled（内存不足）→ 跳到"错误 1" |
| 1 | 应用启动脚本错误、配置文件缺失、权限问题 |
| 127 | 命令不存在（启动命令路径错误） |
| 0 但立即退出 | 启动命令被覆盖（参考"错误 3 Step 3"） |
| 1，日志含 `jmx_prometheus_javaagent` | JMX Exporter JAR 文件缺失或 volume 未挂载 |

**Step 3：检查启动命令是否被意外覆盖**
```bash
kubectl get deployment <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].command}' | jq .
# 如果返回非 null，说明 command 被覆盖，原始ENTRYPOINT/CMD 被忽略
```

#### 修复方案

**命令覆盖问题（command 非 null）：**
```bash
# 恢复：去掉 command 字段
kubectl patch deployment <name> -n <namespace> --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":null}]'
```

**JMX Exporter JAR 缺失（`Error opening zip file ... jmx_prometheus_javaagent`）：**
```bash
# 确认 host 上 JAR 是否存在
ssh <user>@<server> ls -la /opt/<project>/volumes/tomcat/exporter/

# 确认 volume 挂载是否正确
kubectl describe pod -n <namespace> <pod-name> | grep -A3 'Mounts:' | grep exporter

# 确认 deployment 中 JAVA_TOOL_OPTIONS 指向的路径
kubectl get deployment <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].env}' | jq '.[] | select(.name=="JAVA_OPTS") | .value' | grep jmx
```

根因：`JAVA_OPTS` 中指定了 `-javaagent:/usr/local/tomcat_exporter/jmx_prometheus_javaagent-1.5.0.jar`，但该文件不存在（volume 未挂载或目录为空），JVM 启动失败。

修复步骤：
1. 确认 host 上 `/opt/<project>/volumes/tomcat/exporter/jmx_prometheus_javaagent-1.5.0.jar` 是否存在
2. 确认 deployment YAML 中 `volumes` 有 `hostPath` 指向该目录，`volumeMounts` 有对应挂载
3. 如文件缺失，从镜像内复制到 host 目录，或在 hostPath 初始化脚本中预置

**配置文件缺失：**
```bash
# 查容器内缺失的文件
kubectl describe pod <pod-name> -n <namespace> | grep -i 'not found\|cannot'
```

---

## 📊 部署前置检查清单（快速参考）

```
部署前必查项目（按顺序）：
□ 1. 节点总内存 > 所有组件 limits 之和 × 1.2
□ 2. JVM -Xmx < 容器 memory limit × 0.7
□ 3. 应用配置中中间件地址为 K8s Service 名称（不是 localhost/127.0.0.1）
□ 4. readiness/liveness/startup probe 不使用 actuator 路径（除非应用明确引入了 Actuator 依赖）；推荐使用 tcpSocket
□ 5. 镜像 tag 在私仓中存在
□ 6. 清理多余 ReplicaSet（kubectl get rs 确认只有一个 active）
□ 7. generate.sh 存在且可执行
□ 8. namespace 存在或 yaml 中有创建配置
□ 9. volume hostPath 目录在节点上存在且权限正确
□ 10. imagePullSecrets 配置（私仓需要）
```

---

## 🆘 Fallback Plan

| 失败场景 | Fallback Plan |
|---------|--------------|
| `generate.sh` 执行失败 | 跳过，直接 `kubectl kustomize ${PROJECT_PATH} > ${PROJECT_PATH}/release/${PROJECT_NAME}.yml` |
| `kubectl apply` 失败（字段冲突） | `FORCE_APPLY=true` 或 `kubectl apply --force-conflicts` |
| `kubectl diff` 超时或卡住 | 跳过 diff，直接 apply（仅限确认过配置的情况下） |
| Pod 卡在 `Pending` 超过 5 分钟 | 先缩容到 0：`kubectl scale deployment -n ${NAMESPACE} <name> --replicas=0`，排查后再扩回 |
| 多 ReplicaSet 导致资源重复计算 | 删掉多余 RS，只保留一个 active |
| `kubectl apply` 部分成功部分失败 | 查看 `kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'` |
| SSH 连接超时 | 检查网络、防火墙、SSH 服务状态 |
| `ImagePullBackOff` 私仓认证失败 | `kubectl create secret docker-registry` 创建镜像拉取密钥 |

---

## 回滚指南

| 场景 | 回滚命令 |
|------|---------|
| 配置变更后出问题 | `kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/` 重刷旧清单 |
| 扩缩容后出问题 | `kubectl scale deployment -n ${NAMESPACE} <name> --replicas=<原副本数>` |
| 删除资源 | `kubectl delete -n ${NAMESPACE} -f ${RELEASE_PATH}/`（幂等） |
| 查看历史版本 | `kubectl rollout history deployment -n ${NAMESPACE}` |
| 回滚到上一版本 | `kubectl rollout undo deployment -n ${NAMESPACE} <name>` |

---

## 🔁 反复出现问题的根因与应对

以下问题在每次部署时都会重复出现，理解根因后才能正确处理。

---

### 问题 1：OOMKilled / JVM -Xmx 超容器 limit

**反复出现的表象**：每次部署都要调低 JVM 和内存 limits。

**Git 仓库配置值与目标服务器硬件不匹配**。仓库通常按大服务器（32Gi+）配置默认值，实际部署节点内存偏小（8-16Gi），导致 OOM 或调度失败。

**我们能做什么**：
- ❌ 改 Git 仓库——需要写权限，当前无权限
- ❌ 每次手动 patch——下次部署又恢复（git checkout 会覆盖）
- ✅ **依赖 Step 4d 自动修复**：检测到 JVM > 容器 limit 70% 时自动压缩
- ✅ **服务器本地副本已修正**：内存 4Gi、JVM -Xmx2g，下次部署如果 git checkout 覆盖了，Step 4d 会再次修回来

**结论**：不需要每次问用户，Step 4d 自动处理。如果想根本解决，需要有人给 Git 写权限把默认值改对。

---

### 问题 2：Pod Running 但 READY=0（HTTP probe 返回 404）

**反复出现的表象**：每次部署都出现 READY 0/1，应用日志正常但 K8s 不认可。

**根因**：probe 路径（如 `/actuator/health/ping`）在应用里不存在（应用未实现该端点，或路径不匹配）。HTTP probe 必然 404。

**我们能做什么**：
- ❌ 改 Git 仓库——需要写权限，当前无权限
- ❌ 每次手动 patch → 下次部署又恢复
- ✅ **依赖 Step 4e 自动修复**：检测到 HTTP probe 404 → 自动改为 tcpSocket
- ✅ **服务器本地副本已修正**：所有 probes 改为 tcpSocket，generate.sh 后生效

**结论**：Step 4e 自动处理。如果想根本解决，需要有人把 Git 仓库里的 probe 路径改为 tcpSocket 或确认应用实际端点。

---

### 问题 3：Pod 卡 Pending（多个旧 RS 残留）

**反复出现的表象**：有新 Pod 但调度失败，旧的还在，资源被耗尽。

**根因**：旧 ReplicaSet 未清理（DESIRED=0 但仍占用资源），导致调度时资源碎片化。

**我们能做什么**：
- ✅ 调度冲突自动决策：`kubectl scale deployment <name> -n <ns> --replicas=0` 清掉旧 Pod，立刻释放资源
- ✅ 清理 DESIRED=0 的旧 ReplicaSet

---

### 问题 4：Redis 连不上（WAR 包内配置文件硬编码）

**反复出现的表象**：Pod Ready=1/1，日志干净，但应用连不上 Redis（`Unable to connect to Redis server: 127.0.0.1/127.0.0.1:6379`）。

**根因**：应用读取的是 **WAR 包内**的 `application-dev.yml`，其中 `redis.host: 127.0.0.1`。环境变量 `REDIS_HOST=redis` 对 Spring Boot 有效，但 Redisson 的配置文件如果直接读 YAML 而非 Spring 环境变量，则不生效。根因在**应用打包内容**，不是 K8s 层面。

**我们能做什么**：
- ❌ 改 Git 仓库——需要写权限，当前无权限
- ❌ 环境变量 `REDIS_HOST=redis`——对部分配置有效，对硬编码 YAML 配置无效
- ✅ **volume mount 覆盖配置文件**：将修改后的 `application-dev.yml` 挂载到 `/usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/`，覆盖原文件
- ✅ **永久方案**：将 volume mount 配置写入源码 YAML（`service/tomcat/01-deployment.yml`），使 `generate.sh` 后自动生效

**结论**：按错误 4 修复方案 B 处理，永久修复需同步修改源码 YAML 加入 webapps-classes volume。

---

### 核心逻辑

**Git 仓库 ≠ 真实环境**。仓库配置是给理想大机器用的，实际服务器资源偏小（15Gi）。每次 `git checkout` 会恢复仓库的"错误"值，但 Step 4d/4e 能兜底。

**最优策略**：
1. 服务器本地副本尽量保持正确（已修正内存、JVM、probe、Redis配置）
2. 依赖 Skill 自动化（Step 4a/4d/4e）在每次部署时自动修复OOM和probe问题
3. Redis 连接问题通过 volume mount 覆盖 application-dev.yml 解决，需同步写入源码 YAML
4. 如有 Git 写权限，把默认值改为匹配目标服务器的合理值（一劳永逸）

---

## 幂等性说明

- **generate.sh**: 幂等，可重复执行
- **kubectl apply**: 幂等，重复执行会保持目标状态
- **kubectl delete**: 非幂等，删除操作不可恢复，执行前必须用户确认 `yes`
- **kubectl scale**: 幂等

---

## ⚡ 调度冲突自动决策原则

当 Pod Pending（资源不足）时，自动判断并执行以下方案（无需询问），目标是所有服务最终平稳运行：

| 场景 | 自动决策 |
|------|---------|
| 新 Pod Pending + 旧版 Pod Running | 删除旧版 Pod，释放资源给新 Pod |
| 多个 ReplicaSet 同时存在 | 删除 DESIRED=0 的旧 RS，释放资源 |
| 某组件空闲（无流量）且占用大量内存 | 临时缩容到 0，调度新 Pod 后再扩容 |
| 节点内存即将耗尽（>115%） | 优先保核心服务（tomcat），缩容或删除边缘服务 |

**决策原则**：
1. 服务平稳运行优先于保持旧版本
2. 核心服务优先于边缘服务（由用户定义或根据组件名判断，如 tomcat/db > minio/redis > exporter）
3. 有新版本时旧版服从新版本调度
4. 所有决策事后报告，不事前询问（紧急情况）
5. 非紧急情况优先告知用户，由用户决定

---

## 停止条件（立即停止，不要尝试"顺手修好"）

- 目标 namespace、context、server host 与用户输入不一致
- apply/diff 显示将修改白名单外资源
- release 目录不在 PROJECT_PATH 内
- 需要写入 VOLUME_ALLOWLIST 之外的路径
- 需要修改系统服务、安装软件、改 SSH、改防火墙、改 Docker/K8s 运行时
- 破坏性删除/回滚操作未确认（删除Pod/缩容/回滚配置等）
- generate.sh 不存在或执行失败
- RESOURCE_ALLOWLIST 为空
- **所有组件 limits 之和超过节点总内存 100%（会 OOM，立即停止）**
- **JVM -Xmx 大于容器 memory limit 的 80%（必然 OOM，立即停止）**

---

## 常用命令速查

| 目的 | 命令 |
|------|------|
| 查看资源 | `kubectl get all -n ${NAMESPACE}` |
| 查看 Pod 状态 | `kubectl get pods -n ${NAMESPACE} -o wide` |
| 前置检查 | `ssh ${SSH_USER}@${SERVER_HOST} "bash ${PROJECT_PATH}/scripts/preflight.sh"` |
| 健康检查 | `ssh ${SSH_USER}@${SERVER_HOST} "bash ${PROJECT_PATH}/scripts/health_check.sh"` |
| 查看日志 | `kubectl logs -n ${NAMESPACE} -l app=tomcat --tail=20` |
| 重启 Pod | `kubectl delete pod -n ${NAMESPACE} -l app=tomcat` |
| 缩容 | `kubectl scale deployment -n ${NAMESPACE} <component> --replicas=0` |
| 扩容 | `kubectl scale deployment -n ${NAMESPACE} <component> --replicas=1` |
| 查看节点资源 | `kubectl describe node` |
| 查看 events | `kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'` |
| 强制 apply | `FORCE_APPLY=true kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/` |
| 跳过预览 | `SKIP_PREVIEW=true kubectl apply -n ${NAMESPACE} -f ${RELEASE_PATH}/` |
| 清理多余 RS | `kubectl delete rs <rs-name> -n ${NAMESPACE}` |

---

## 📖 使用示例

### 示例 1：部署一个 Java Tomcat 项目（Git 源码）

```bash
# 标准部署
SSH_USER=ubuntu SSH_PASSWORD=xxx SERVER_HOST=192.168.1.100 \
  PROJECT_PATH=/opt/caij-saas/deploy \
  NAMESPACE=caij-saas \
  RESOURCE_ALLOWLIST="app=tomcat,app=redis" \
  EXPECTED_CONTEXT=kubernetes \
  bash deploy_script.sh
```

**对话流程：**
```
你: 帮我部署 caij-saas 项目
助手: 好的！部署前需要确认：源码来源、服务器、SSH、项目路径

你: Git 源码，分支 main，Token 是 xxx，目标服务器 192.168.1.100

助手: ✅ 信息确认完毕，开始 Step 0 环境预检...
      ✅ SSH 连通性 OK
      ✅ kube-context: kubernetes
      ⚠️  Step 4a 发现：所有组件 limits 之和 > 节点内存 80%
      ⚠️  Step 4b 发现：JVM -Xmx > 容器 limit → 部署前自动调整
      → 部署前自动调整 JVM heap

🎉 部署完成！
- 项目：caij-saas
- 命名空间：caij-saas
- 状态：Ready
```

---

### 示例 2：Redis 连接失败，诊断链路

```
你: 应用日志里出现 Redis Connection refused 127.0.0.1:6379
助手: 开始诊断链路...

Step 1: kubectl get svc → redis service 存在 ✅
Step 2: kubectl logs | grep '地址: 127.0.0.1' → 确认配置文件硬编码 localhost ❌
Step 3: 确认应用读的是 WAR 包内的 application-dev.yml
Step 4: 修复方案：用 volume mount 覆盖 application-dev.yml（host: 127.0.0.1 → host: redis）

助手: ✅ 已修复：volume mount 覆盖了 application-dev.yml
     ✅ 应用已重启，Redis 连接正常
```

---

### 示例 3：Pod Pending（内存不足），多 RS 问题

```
你: tomcat pod 一直 Pending
助手: 开始诊断链路...

Step 1: kubectl describe node → memory 95% allocated
Step 2: kubectl get rs → 发现 3 个 RS，各有 1 replica ❌
Step 3: 确认是历史 deployment 遗留的 RS

助手: 清理了 2 个多余 RS，保留 active RS
      缩容边缘组件（释放内存）
      tomcat 调度成功 ✅
      扩容 redis 回 1 ✅

🎉 所有 pod Ready
```

---

### 快速命令模板

```bash
# 标准部署
SSH_USER=<user> SSH_PASSWORD=<pass> SERVER_HOST=<ip> \
  PROJECT_PATH=<path> NAMESPACE=<ns> RESOURCE_ALLOWLIST=<label> \
  bash deploy_script.sh

# 跳过预览直接部署（非生产环境）
SKIP_PREVIEW=true SSH_USER=<user> SSH_PASSWORD=<pass> \
  SERVER_HOST=<ip> PROJECT_PATH=<path> NAMESPACE=<ns> \
  RESOURCE_ALLOWLIST=<label> bash deploy_script.sh

# 强制 apply（字段冲突时）
FORCE_APPLY=true SSH_USER=<user> SSH_PASSWORD=<pass> \
  SERVER_HOST=<ip> PROJECT_PATH=<path> NAMESPACE=<ns> \
  RESOURCE_ALLOWLIST=<label> bash deploy_script.sh

# 自定义超时（秒）
WAIT_TIMEOUT=900 SSH_USER=<user> SSH_PASSWORD=<pass> \
  SERVER_HOST=<ip> PROJECT_PATH=<path> NAMESPACE=<ns> \
  RESOURCE_ALLOWLIST=<label> bash deploy_script.sh

# 自定义镜像版本
DEPLOY_IMAGE=registry.io/image:tag SSH_USER=<user> \
  SSH_PASSWORD=<pass> SERVER_HOST=<ip> PROJECT_PATH=<path> \
  NAMESPACE=<ns> RESOURCE_ALLOWLIST=<label> bash deploy_script.sh
```
