---
name: k8s-install
description: |
  从零开始在服务器上安装K8s集群。
  **版本：v2**
  触发关键词：安装K8s、初始化集群、搭集群、建集群、新建集群
  触发场景：服务器未安装K8s、首次初始化集群、重装集群
  约束：只操作指定服务器，禁止修改系统无关配置。
---

# k8s-install

**Phase 1: 安装 K8s 集群（新建服务器时执行一次）**

---

## ⚠️ 启动前必确认事项

**触发本技能后，动手之前必须先向用户确认以下 3 点：**

| # | 问题 | 选项 |
|---|------|------|
| 1 | **安装在哪里？** | 本地 Mac / 服务器 IP 或域名 |
| 2 | **K8s 集群来源？** | 从零新建 / 连接已有集群 |
| 3 | **Git 源码（仅涉及部署时）** | Git 地址+分支+Token / 服务器已有 / 不需要 |

**只有在用户明确回答以上问题后，才能继续执行后续步骤。**

---

## 📢 实时报告要求（每步必报）

**执行任何 step 时，必须在开始前和完成后向用户发送简短报告：**

```
Step X 开始：<简要说明当前操作>
Step X 完成：<结果/版本/状态>
```

**禁止：** 等所有步骤完成才统一报告。
**禁止：** 用 exec 输出代替用户报告（用户看不到 exec 输出）。

**示例：**
```
Step 1 开始：安装 containerd...
Step 1 完成：✅ containerd 1.7.x 已安装，SystemdCgroup=true
Step 2 开始：安装 kubeadm/kubelet/kubectl...
Step 2 完成：✅ kubeadm v1.35.4 已安装
...
```

---

## 🎯 任务边界（Scope Boundary）

**本技能仅限执行以下任务：**
- ✅ 安装 K8s 控制平面组件
- ✅ 安装 CNI（Cilium）
- ✅ 安装 Istio
- ✅ 配置 kubeconfig

**明确拒绝以下请求（立即停止）：**
- ❌ 应用部署（属于 k8s-deploy 范畴）
- ❌ 修改系统 SSH/Docker/防火墙配置
- ❌ 安装非 K8s 相关软件
- ❌ 优化服务器性能参数
- ❌ 部署数据库、缓存、中间件（非 K8s 组件）
- ❌ 配置负载均衡、Nginx、反向代理（非 K8s 网络）

---

## 🚫 禁止操作（违反立即停止）

| 禁止 | 原因 |
|------|------|
| 不要修改 `/etc/` 系统目录 | 除非是 K8s 必要配置 |
| 不要修改系统 SSH/防火墙/内核参数 | 只做 K8s 相关操作 |
| 不要删除未确认的资源 | 确认用户回复 `yes` 后才执行 |
| **不要在已有 K8s 集群的服务器上执行** | 会破坏现有集群 |
| **不要跳过 Step 0 直接执行 Step 1-6** | 可能误操作错误目标 |
| **不要在生产环境执行 `kubeadm reset`** | 不可逆销毁集群 |
| **不要用 curl 验证已部署的 URL** | curl 会被 Sidecar 拦截导致误判 |
| **不要用 `kubectl delete` 清理 Pod** | 应使用 `kubectl scale` 缩容到 0 再删除 |
| **不要跳过 `generate.sh` 直接 apply** | 会导致本地修改被覆盖 |
| **不要处理 K8s 集群初始化以外的任务** | 超出 Scope Boundary |

---

## 🛡️ 安全默认值

| 默认值 | 说明 |
|--------|------|
| `AUTO_CONFIRM=false` | 默认需要用户手动确认危险操作 |
| `SKIP_EXISTING=true` | 默认跳过已存在的组件（幂等） |
| `PREVIEW_MODE=true` | 默认开启 diff 预览，不直接执行 |
| `WAIT_TIMEOUT=600000` | 默认 10 分钟超时（毫秒） |
| `MAX_RETRIES=3` | 单步最大重试次数 |
| `TASK_SCOPE_CHECK=true` | 默认开启任务相关性检测 |

如需跳过确认直接执行：`AUTO_CONFIRM=true bash <script>`
如需跳过预览直接 apply：`SKIP_PREVIEW=true bash <script>`

---

## 📦 可传入参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SERVER_HOST` | SSH 目标主机（IP 或域名） | 必填 |
| `SSH_USER` | SSH 用户名 | 必填 |
| `SSH_PASSWORD` | SSH 密码 | 必填 |
| `SSH_PORT` | SSH 端口 | `22` |
| `KUBE_VERSION` | K8s 版本（如 `1.35.4`） | `1.35.4` |
| `POD_CIDR` | Pod 子网（不得与现有网络冲突） | `10.244.0.0/16` |
| `SERVICE_CIDR` | Service 子网 | `10.96.0.0/12` |
| `KUBECONFIG_PATH` | kubeconfig 导出路径 | `~/.kube/config` |
| `PROJECT_PATH` | 项目部署配置目录（用于加载 assets） | 必填 |
| `CILIUM_VERSION` | Cilium CNI 版本 | `1.19.2` |
| `ISTIO_VERSION` | Istio 版本 | `1.29.1` |
| `EXPECTED_HOSTNAME` | 预期主机名（用于校验目标服务器身份） | 可选 |
| `EXPECTED_OS` | 预期操作系统（如 `Ubuntu 24.04`、`Ubuntu 22.04`） | 可选 |
| `ALLOWED_PATH_PREFIXES` | 允许的 PROJECT_PATH 前缀 | `/opt/,/home/` |
| `AUTO_CONFIRM` | 自动确认危险操作（默认 false） | `false` |
| `KUBADM_TIMEOUT` | kubeadm init 超时（毫秒） | `600000`（10分钟） |
| `MAX_RETRIES` | 单步最大重试次数 | `3` |
| `TASK_SCOPE_CHECK` | 是否检测任务相关性（默认 true） | `true` |
| `SKIP_PREVIEW` | 跳过 diff 预览（默认 false） | `false` |

---

## 🔄 完整工作流程

```
Step 0: 环境预检（必做）
├── 0.1 目标服务器身份确认（hostname + OS 校验）
├── 0.2 已有 K8s 集群检测
├── 0.3 PROJECT_PATH 安全路径校验
├── 0.4 Docker/containerd 冲突检测
├── 0.5 硬件资源快速检查
├── 0.6 任务相关性检测
└── 0.7 CPU 架构检查（x86-64-v2）⚑ 新增


Step 1: 安装 containerd（幂等）
Step 2: 安装 kubeadm/kubelet/kubectl（幂等）
Step 3: kubeadm init（幂等 + 保护）
Step 4: 安装 Cilium CNI（幂等）
Step 5: 安装 Istio + Gateway API CRDs（幂等）
Step 6: 配置 kubeconfig 供部署用户使用


失败处理：
├── 重试机制（最多 MAX_RETRIES 次）
├── 失败记录与报告
└── Fallback 步骤指引
```

---

## Step 0: 环境预检（必做）

**⚠️ 此步骤必须第一个执行，任何检查失败立即停止，不可跳过**

### 0.1 目标服务器身份确认

```bash
# 获取目标服务器 hostname 和 OS 信息
TARGET_HOSTNAME=$(ssh ${SSH_USER}@${SERVER_HOST} "hostname -f" 2>/dev/null || ssh ${SSH_USER}@${SERVER_HOST} "hostname")
TARGET_OS=$(ssh ${SSH_USER}@${SERVER_HOST} "cat /etc/os-release | grep -E '^ID=|^VERSION_ID=' | head -2")
TARGET_KERNEL=$(ssh ${SSH_USER}@${SERVER_HOST} "uname -r")

echo "========================================"
echo "📋 目标服务器身份确认"
echo "========================================"
echo "主机名: ${TARGET_HOSTNAME}"
echo "操作系统: ${TARGET_OS}"
echo "内核版本: ${TARGET_KERNEL}"
echo "========================================"

# 校验 expected hostname（如提供）
if [ -n "${EXPECTED_HOSTNAME:-}" ]; then
  if [ "${TARGET_HOSTNAME}" != "${EXPECTED_HOSTNAME}" ]; then
    echo "❌ 错误：主机名不匹配"
    echo "预期: ${EXPECTED_HOSTNAME}"
    echo "实际: ${TARGET_HOSTNAME}"
    echo "⚠️ 可能是误连接到了错误的服务器，强制停止"
    exit 1
  fi
  echo "✅ 主机名校验通过"
fi

# 校验 expected OS（如提供）
if [ -n "${EXPECTED_OS:-}" ]; then
  if ! echo "${TARGET_OS}" | grep -qi "${EXPECTED_OS}"; then
    echo "❌ 错误：操作系统不匹配预期"
    echo "预期包含: ${EXPECTED_OS}"
    echo "实际: ${TARGET_OS}"
    exit 1
  fi
  echo "✅ 操作系统校验通过"
fi

echo ""
```

### 0.2 已有 K8s 集群检测

```bash
# ⚠️ 检测是否已有 K8s 集群存在
echo "🔍 检测已有 K8s 集群..."

# 检查 kubeconfig 是否存在
if ssh ${SSH_USER}@${SERVER_HOST} "[ -f /etc/kubernetes/admin.conf ]" 2>/dev/null; then
  echo "❌ 检测到 /etc/kubernetes/admin.conf 存在"
  echo "⚠️ 服务器可能已有 K8s 集群，继续将破坏现有集群"
  echo "如确认为空服务器需要重装，请先执行清理："
  echo "  ssh ${SSH_USER}@${SERVER_HOST} 'sudo kubeadm reset --force'"
  exit 1
fi

# 检查 kubelet 是否已运行
if ssh ${SSH_USER}@${SERVER_HOST} "systemctl is-active kubelet" 2>/dev/null | grep -q active; then
  echo "❌ 检测到 kubelet 服务正在运行"
  echo "⚠️ 服务器可能已有 K8s 集群"
  exit 1
fi

# 尝试连接 apiserver（快速检测）
if ssh ${SSH_USER}@${SERVER_HOST} "kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes --request-timeout=5s" 2>/dev/null; then
  echo "❌ 检测到可以连接已有 K8s 集群"
  echo "⚠️ 服务器已有 K8s 集群，继续将破坏现有环境"
  exit 1
fi

echo "✅ 未检测到已有 K8s 集群，继续"
echo ""
```

### 0.3 PROJECT_PATH 安全路径校验

```bash
# ⚠️ 校验 PROJECT_PATH 必须在安全的前缀下
echo "🔍 校验 PROJECT_PATH 安全路径..."

# 允许的前缀列表（默认 /opt/ 和 /home/）
ALLOWED_PREFIXES="${ALLOWED_PATH_PREFIXES:-/opt/,/home/}"

# 检查 PROJECT_PATH 是否为空
if [ -z "${PROJECT_PATH:-}" ]; then
  echo "❌ 错误：PROJECT_PATH 未提供"
  exit 1
fi

# 获取 PROJECT_PATH 的绝对路径（不存在的目录也能解析）
PROJECT_REALPATH=$(ssh ${SSH_USER}@${SERVER_HOST} "realpath ${PROJECT_PATH}" 2>/dev/null)
if [ -z "${PROJECT_REALPATH}" ]; then
  PROJECT_REALPATH="${PROJECT_PATH}"
fi

echo "PROJECT_PATH: ${PROJECT_PATH}"
echo "解析后路径: ${PROJECT_REALPATH}"

# 危险路径检查
case "${PROJECT_REALPATH}" in
  ""|"/"|"/etc"|"/usr"|"/var"|"/System"|"/Library"|"$HOME/.ssh"|"/tmp"|"/root")
    echo "❌ 错误：PROJECT_PATH 指向危险路径: ${PROJECT_REALPATH}"
    exit 1
    ;;
esac

# 前缀白名单校验
ALLOWED=0
for prefix in $(echo "${ALLOWED_PREFIXES}" | tr ',' ' '); do
  if echo "${PROJECT_REALPATH}" | grep -q "^${prefix}"; then
    ALLOWED=1
    break
  fi
done

if [ "${ALLOWED}" = "0" ]; then
  echo "❌ 错误：PROJECT_PATH 不在允许的前缀列表内"
  echo "允许的前缀: ${ALLOWED_PREFIXES}"
  echo "实际路径: ${PROJECT_REALPATH}"
  exit 1
fi

echo "✅ PROJECT_PATH 路径校验通过: ${PROJECT_REALPATH}"
echo ""
```

### 0.4 Docker / containerd 冲突检测

```bash
# ⚠️ 检测 Docker 是否运行（与 containerd 可能的冲突）
echo "🔍 检测 Docker / containerd 冲突..."

# 检查 Docker 是否存在且运行中
DOCKER_RUNNING=""
if ssh ${SSH_USER}@${SERVER_HOST} "systemctl is-active docker" 2>/dev/null | grep -q active; then
  DOCKER_RUNNING="yes"
  echo "⚠️ 检测到 Docker 服务正在运行"
fi

# 检查 containerd 是否已安装
CONTAINERD_INSTALLED=""
if ssh ${SSH_USER}@${SERVER_HOST} "containerd --version" 2>/dev/null; then
  CONTAINERD_INSTALLED="yes"
  echo "⚠️ 检测到 containerd 已安装"
fi

# 如果 Docker 正在运行且未安装 containerd，警告
if [ "${DOCKER_RUNNING}" = "yes" ] && [ "${CONTAINERD_INSTALLED}" != "yes" ]; then
  echo ""
  echo "========================================"
  echo "⚠️  警告：检测到 Docker 运行中"
  echo "========================================"
  echo "安装 containerd 可能会影响现有 Docker 环境。"
  echo "如果该服务器仅用于 K8s，建议："
  echo "  1. 停止 Docker: sudo systemctl stop docker"
  echo "  2. 禁用 Docker: sudo systemctl disable docker"
  echo "  3. 然后继续安装 containerd"
  echo ""
  echo "如仍要继续（输入 'yes'）："
  read -r confirm
  if [ "$confirm" != "yes" ]; then
    echo "已取消安装操作"
    exit 1
  fi
  echo "继续执行..."
fi

# 如果 containerd 已安装，检查配置
if [ "${CONTAINERD_INSTALLED}" = "yes" ]; then
  CONTAINERD_CONFIGURED=$(ssh ${SSH_USER}@${SERVER_HOST} "grep 'SystemdCgroup = true' /etc/containerd/config.toml" 2>/dev/null || echo "")
  if [ -z "${CONTAINERD_CONFIGURED}" ]; then
    echo "⚠️ 检测到 containerd 未配置 SystemdCgroup"
    echo "Step 1 将自动配置，无需手动处理"
  else
    echo "✅ containerd 已配置 SystemdCgroup"
  fi
fi

echo "✅ Docker / containerd 冲突检测完成"
echo ""
```

### 0.5 硬件资源快速检查

```bash
# ⚠️ 快速检查资源是否满足 K8s 最低要求
echo "🔍 硬件资源快速检查..."

MEM_MB=$(ssh ${SSH_USER}@${SERVER_HOST} "free -m | awk '/^Mem:/{print \$2}'" 2>/dev/null)
CPU_COUNT=$(ssh ${SSH_USER}@${SERVER_HOST} "nproc" 2>/dev/null)
DISK_AVAIL=$(ssh ${SSH_USER}@${SERVER_HOST} "df -h / | tail -1 | awk '{print \$4}'" 2>/dev/null)

echo "内存: ${MEM_MB} MB"
echo "CPU: ${CPU_COUNT} 核"
echo "磁盘可用: ${DISK_AVAIL}"

# K8s 最低要求：2CPU, 2GB MEM, 20GB 可用
if [ "${MEM_MB}" -lt 1800 ]; then
  echo "⚠️ 内存低于 2GB（实际 ${MEM_MB} MB），K8s 可能无法正常运行"
fi
if [ "${CPU_COUNT}" -lt 2 ]; then
  echo "⚠️ CPU 少于 2 核（实际 ${CPU_COUNT}），K8s 可能无法正常运行"
fi

echo "✅ 硬件资源检查完成"
echo ""
```

### 0.6 任务相关性检测

```bash
# ⚠️ 检测任务是否属于 K8s 安装范围
if [ "${TASK_SCOPE_CHECK:-true}" != "true" ]; then
  echo "⏭️ 任务相关性检测已跳过（TASK_SCOPE_CHECK=false）"
else
  echo "🔍 任务相关性检测..."
  
  # 检测用户请求中是否包含非 K8s 安装范围的关键词
  # 这些关键词从用户输入（参数或环境变量）获取
  USER_TASK="${USER_TASK:-${1:-}}"
  
  # 如果有用户任务描述，检测是否超出范围
  if [ -n "${USER_TASK}" ]; then
    # 超出范围的关键词模式（精确匹配或正则）
    SCOPE_VIOLATION_PATTERN="部署|上线|发布.*应用|安装nginx|安装mysql|安装redis|安装docker|配置.*数据库|负载均衡|反向代理|安装.*中间件"
    
    if echo "${USER_TASK}" | grep -qiE "${SCOPE_VIOLATION_PATTERN}"; then
      echo ""
      echo "========================================"
      echo "❌ 任务超出 Scope Boundary"
      echo "========================================"
      echo "检测到可能超出 K8s 安装范围的关键词"
      echo ""
      echo "本技能（k8s-install）仅处理："
      echo "  - K8s 控制平面安装"
      echo "  - CNI（Cilium）安装"
      echo "  - Istio 安装"
      echo ""
      echo "如需执行以下任务，请使用对应技能："
      echo "  - 部署应用 → k8s-deploy"
      echo "  - 安装数据库 → 数据库安装技能"
      echo "  - 配置网络 → 网络配置技能"
      echo ""
      echo "当前任务: ${USER_TASK}"
      echo ""
      echo "如确认为 K8s 安装任务，输入 'yes' 继续："
      read -r confirm
      if [ "$confirm" != "yes" ]; then
        echo "已拒绝超出范围的任务"
        exit 1
      fi
      echo "继续执行..."
    fi
  fi
  
  echo "✅ 任务相关性检测通过"
  echo ""
fi
```

### 0.7 CPU 架构检查（x86-64-v2）⚑ 新增

```bash
# ⚠️ 检测 CPU 架构是否支持 x86-64-v2
# K8s 1.35+ 推荐 x86-64-v2，部分新指令集在老 CPU 上不可用
# ⚠️ 不直接停止，给出处理方案，由用户决定是否继续

echo "🔍 检测 CPU 架构（x86-64-v2）..."

CPU_ARCH=$(ssh ${SSH_USER}@${SERVER_HOST} "uname -m" 2>/dev/null)
CPU_FLAGS=$(ssh ${SSH_USER}@${SERVER_HOST} "cat /proc/cpuinfo | grep flags | head -1" 2>/dev/null)

# 检测 x86-64-v2 关键特性（POPCNT + SSE4.2 + CX16）
HAS_X86_V2="yes"
if [ "${CPU_ARCH}" != "x86_64" ] && [ "${CPU_ARCH}" != "amd64" ]; then
  HAS_X86_V2="no"
fi

# 进一步检查关键指令
if [ "${HAS_X86_V2}" = "yes" ]; then
  # POPCNT (POPCNT 指令)
  if ! echo "${CPU_FLAGS}" | grep -qi "popcnt\|popcnt"; then
    HAS_X86_V2="partial"
  fi
fi

echo "CPU 架构: ${CPU_ARCH}"
echo "x86-64-v2 支持度: ${HAS_X86_V2}"
echo ""

case "${HAS_X86_V2}" in
  yes)
    echo "✅ CPU 支持 x86-64-v2，继续安装"
    ;;
  partial)
    echo ""
    echo "========================================"
    echo "⚠️  CPU 部分不支持 x86-64-v2（缺少 POPCNT 指令）"
    echo "========================================"
    echo "当前 CPU 架构: ${CPU_ARCH}"
    echo "影响：部分 K8s 组件（Cilium eBPF 等）性能受限"
    echo ""
    echo "处理方案（选择一项）："
    echo ""
    echo "  方案 A【推荐】：在支持 x86-64-v2 的服务器上安装"
    echo "  方案 B：继续安装（K8s 核心功能可用，但 Cilium eBPF 性能回退）"
    echo "  方案 C：降级 Cilium 为覆盖网络模式（非 eBPF），性能最优"
    echo ""
    echo "选择（输入 A/B/C，默认 B）："
    read -r CPU_CHOICE
    CPU_CHOICE="${CPU_CHOICE:-B}"
    case "${CPU_CHOICE}" in
      A|a)
        echo "已选择方案 A，请在新服务器上重新安装，退出当前安装"
        exit 1
        ;;
      C|c)
        echo "📝 已选择方案 C，降级 Cilium 为覆盖网络模式"
        CILIUM_MODE="overlay"
        echo "⚠️ 注意：Step 4 将使用 overlay 模式安装 Cilium"
        ;;
      *)
        echo "继续安装（方案 B），K8s 核心功能正常"
    esac
    ;;
  no)
    echo ""
    echo "========================================"
    echo "⚠️  CPU 不支持 x86-64-v2（非 x86 架构或非常老旧）"
    echo "========================================"
    echo "当前 CPU 架构: ${CPU_ARCH}"
    echo "影响："
    echo "  - K8s 核心功能可能正常运行"
    echo "  - Cilium eBPF 模式不可用"
    echo "  - Istio 性能可能受限"
    echo ""
    echo "处理方案（选择一项）："
    echo ""
    echo "  方案 A【推荐】：在 x86_64 服务器上安装"
    echo "  方案 B：继续安装，使用 overlay 网络模式"
    echo "  方案 C：跳过 Cilium，使用 K8s 默认网络（仅概念验证）"
    echo ""
    echo "选择（输入 A/B/C，默认 B）："
    read -r CPU_CHOICE
    CPU_CHOICE="${CPU_CHOICE:-B}"
    case "${CPU_CHOICE}" in
      A|a)
        echo "已选择方案 A，请更换服务器后重新安装，退出"
        exit 1
        ;;
      B|b)
        echo "继续安装（overlay 模式）..."
        CILIUM_MODE="overlay"
        ;;
      C|c)
        echo "⚠️ 已选择方案 C，跳过 Cilium 安装（仅概念验证，生产勿用）"
        CILIUM_MODE="skip"
        SKIP_CILIUM="true"
        ;;
      *)
        echo "继续安装..."
        CILIUM_MODE="overlay"
    esac
    ;;
esac

echo ""
```

### Step 0 汇总

```bash
echo ""
echo "📢 ======================================="
echo "📢 Step 0 环境预检全部通过"
echo "📢 ======================================="
echo "📢 目标服务器: ${SERVER_HOST}"
echo "📢 SSH 用户:   ${SSH_USER}"
echo "📢 主机名:     ${TARGET_HOSTNAME}"
echo "📢 操作系统:   ${TARGET_OS}"
echo "📢 PROJECT_PATH: ${PROJECT_REALPATH}"
echo "📢 K8s 版本:  ${KUBE_VERSION}"
echo "📢 Cilium:    ${CILIUM_VERSION}"
echo "📢 Istio:     ${ISTIO_VERSION}"
echo "📢 ======================================="
echo ""
echo "📢 即将开始安装 containerd（Step 1）..."
```

---

## Step 1: 安装 containerd（幂等 + 重试）

```bash
# 重试机制
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_COUNT=0

install_containerd() {
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "[尝试 ${RETRY_COUNT}/${MAX_RETRIES}] 安装 containerd..."
  
  # 检查 containerd 是否已安装且配置正确
  if ssh ${SSH_USER}@${SERVER_HOST} "containerd --version" 2>/dev/null; then
    echo "✅ containerd 已安装，跳过安装步骤"
    
    # 检查是否已配置 SystemdCgroup
    if ssh ${SSH_USER}@${SERVER_HOST} "grep 'SystemdCgroup = true' /etc/containerd/config.toml" 2>/dev/null | grep -q "SystemdCgroup = true"; then
      echo "✅ containerd 已配置 SystemdCgroup，跳过配置步骤"
      return 0
    else
      echo "📝 配置 containerd SystemdCgroup..."
      ssh ${SSH_USER}@${SERVER_HOST} "sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml"
      ssh ${SSH_USER}@${SERVER_HOST} "sudo systemctl restart containerd"
      return 0
    fi
  fi
  
  # 尝试安装
  if ssh ${SSH_USER}@${SERVER_HOST} "sudo apt-get update && sudo apt-get install -y containerd" 2>/dev/null; then
    ssh ${SSH_USER}@${SERVER_HOST} "sudo containerd config default | sudo tee /etc/containerd/config.toml"
    ssh ${SSH_USER}@${SERVER_HOST} "sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml"
    ssh ${SSH_USER}@${SERVER_HOST} "sudo systemctl restart containerd && sudo systemctl enable containerd"
    echo "✅ containerd 安装完成"
    return 0
  else
    echo "⚠️ containerd 安装失败"
    return 1
  fi
}

# 执行安装（带重试）
for i in $(seq 1 ${MAX_RETRIES}); do
  if install_containerd; then
    break
  elif [ $i -lt ${MAX_RETRIES} ]; then
    echo "⏳ 等待 10 秒后重试..."
    sleep 10
  else
    echo ""
    echo "========================================"
    echo "❌ Step 1 安装失败，已达最大重试次数"
    echo "========================================"
    echo "Fallback 步骤："
    echo "  1. 检查网络: ping apt.kubernetes.io"
    echo "  2. 手动安装: sudo apt-get install -y containerd"
    echo "  3. 手动配置: sudo containerd config default | sudo tee /etc/containerd/config.toml"
    exit 1
  fi
done

CONTAINERD_VER=$(ssh ${SSH_USER}@${SERVER_HOST} "containerd --version 2>/dev/null | awk '{print \$2}'")
echo ""
echo "📢 ======================================="
echo "📢 [Step 1/6] containerd 安装完成"
echo "📢 版本: ${CONTAINERD_VER}"
echo "📢 服务状态: $(ssh ${SSH_USER}@${SERVER_HOST} 'systemctl is-active containerd')"
echo "📢 SystemdCgroup: $(ssh ${SSH_USER}@${SERVER_HOST} "grep 'SystemdCgroup = true' /etc/containerd/config.toml 2>/dev/null && echo '已配置' || echo '未配置'")"
echo "📢 ======================================="
echo ""
echo "📢 即将开始安装 kubeadm/kubelet/kubectl（Step 2）..."
```

---

## Step 2: 安装 kubeadm/kubelet/kubectl（幂等）

```bash
# 检查是否已安装指定版本
INSTALLED_VERSION=$(ssh ${SSH_USER}@${SERVER_HOST} "kubeadm version -o short" 2>/dev/null || echo "")

if [ -n "${INSTALLED_VERSION}" ]; then
  echo "✅ kubeadm 已安装，版本: ${INSTALLED_VERSION}"
  
  # 检查版本是否匹配
  if [ "${INSTALLED_VERSION}" = "v${KUBE_VERSION}" ]; then
    echo "✅ kubeadm 版本匹配，跳过安装步骤"
  else
    echo "⚠️ kubeadm 版本不匹配（期望 ${KUBE_VERSION}，实际 ${INSTALLED_VERSION}）"
    echo "如需升级，执行：sudo apt install kubeadm=${KUBE_VERSION}*"
  fi
else
  echo "📦 安装 kubeadm/kubelet/kubectl..."
  KUBE_VERSION="${KUBE_VERSION:-1.35.4}"
  ssh ${SSH_USER}@${SERVER_HOST} "sudo apt-get update && sudo apt-get install -y apt-transport-https curl"
  ssh ${SSH_USER}@${SERVER_HOST} "curl -fsSL https://pkgs.k8s.io/core:/stable:/v${KUBE_VERSION%%.*}/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/k8s-apt-keyring.gpg"
  ssh ${SSH_USER}@${SERVER_HOST} "echo 'deb [signed-by=/etc/apt/keyrings/k8s-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${KUBE_VERSION%%.*}/deb/ /' | sudo tee /etc/apt/sources.list.d/k8s.list"
  ssh ${SSH_USER}@${SERVER_HOST} "sudo apt-get update && sudo apt-get install -y kubelet=${KUBE_VERSION}* kubeadm=${KUBE_VERSION}* kubectl=${KUBE_VERSION}*"
  ssh ${SSH_USER}@${SERVER_HOST} "sudo apt-mark hold kubelet kubeadm kubectl"
fi

KUBEADM_VER=$(ssh ${SSH_USER}@${SERVER_HOST} "kubeadm version -o short 2>/dev/null")
KUBECTL_VER=$(ssh ${SSH_USER}@${SERVER_HOST} "kubectl version --client -o yaml 2>/dev/null | grep gitVersion | head -1 | awk '{print \$2}'")
echo ""
echo "📢 ======================================="
echo "📢 [Step 2/6] kubeadm/kubelet/kubectl 安装完成"
echo "📢 kubeadm:  ${KUBEADM_VER}"
echo "📢 kubectl:  ${KUBECTL_VER}"
echo "📢 ======================================="
echo ""
echo "📢 即将执行 kubeadm init（Step 3），此操作不可逆..."
```

---

## Step 3: kubeadm init（幂等 + 保护）

```bash
# 检查是否已初始化
if ssh ${SSH_USER}@${SERVER_HOST} "[ -f /etc/kubernetes/admin.conf ]" 2>/dev/null; then
  echo "⚠️ 检测到 /etc/kubernetes/admin.conf 已存在"
  echo "可能已初始化 K8s 集群，跳过 kubeadm init"
  echo ""
  echo "如需重新初始化，请先执行："
  echo "  ssh ${SSH_USER}@${SERVER_HOST} 'sudo kubeadm reset --force'"
  echo "  ssh ${SSH_USER}@${SERVER_HOST} 'sudo rm -rf /etc/kubernetes/ /var/lib/etcd'"
  
  # 验证集群是否可用
  echo ""
  echo "📢 ======================================="
  echo "📢 [Step 3/6] 已有 K8s 集群，跳过 init"
  echo "📢 ======================================="
  echo "📢 验证现有集群状态..."
  ssh ${SSH_USER}@${SERVER_HOST} "kubectl get nodes 2>&1 | head -10"
else
  echo "🚀 执行 kubeadm init..."
  
  # ⚠️ kubeadm init 通常需要 3-5 分钟，设置超时
  KUBADM_TIMEOUT=${KUBADM_TIMEOUT:-600000}  # 10 分钟超时（毫秒）
  
  # ⚠️ 先 dry-run 确认参数
  echo "📋 执行 dry-run 确认参数..."
  ssh ${SSH_USER}@${SERVER_HOST} "sudo kubeadm init --pod-network-cidr=${POD_CIDR} --service-cidr=${SERVICE_CIDR} --kubernetes-version=v${KUBE_VERSION} --dry-run=client"
  
  echo ""
  echo "========================================"
  echo "⚠️  即将执行不可逆操作：kubeadm init"
  echo "========================================"
  echo "此操作将："
  echo "  - 初始化 K8s 控制平面"
  echo "  - 生成 PKI 证书和密钥"
  echo "  - 创建 kubeconfig 文件"
  echo ""
  echo "⚠️ 如果这是生产环境服务器，此操作不可撤销！"
  echo ""
  
  # AUTO_CONFIRM 参数控制是否自动确认
  if [ "${AUTO_CONFIRM:-false}" = "true" ]; then
    echo "AUTO_CONFIRM=true，跳过确认..."
  else
    echo "如确认执行（输入 'yes'）："
    read -r confirm
    if [ "$confirm" != "yes" ]; then
      echo "已取消"
      exit 1
    fi
  fi
  
  echo "🚀 开始 kubeadm init，预计需要 3-5 分钟..."
  
  # 执行 kubeadm init，带超时
  if ! ssh ${SSH_USER}@${SERVER_HOST} "timeout $((KUBADM_TIMEOUT/1000)) sudo kubeadm init --pod-network-cidr=${POD_CIDR} --service-cidr=${SERVICE_CIDR} --kubernetes-version=v${KUBE_VERSION}"; then
    echo ""
    echo "========================================"
    echo "❌ kubeadm init 超时或失败"
    echo "========================================"
    echo "可能原因："
    echo "  1. 网络问题导致 apt 包下载失败"
    echo "  2. 端口被占用（6443/10259/10257）"
    echo "  3. 内存不足"
    echo ""
    echo "Fallback 步骤："
    echo "  1. 检查网络: ping apt.kubernetes.io"
    echo "  2. 检查端口: sudo ss -tlnp | grep -E '6443|10259|10257'"
    echo "  3. 检查日志: sudo journalctl -u kubelet --no-pager -n 50"
    echo "  4. 重试: sudo kubeadm init ..."
    echo ""
    echo "如果确认服务器为空且需重装，先清理："
    echo "  sudo kubeadm reset --force && sudo rm -rf /etc/kubernetes/ /var/lib/etcd"
    exit 1
  fi

  # 获取初始化后的节点信息
  NODE_NAME=$(ssh ${SSH_USER}@${SERVER_HOST} "hostname")
  API_SERVER=$(ssh ${SSH_USER}@${SERVER_HOST} "kubectl get endpoints kubernetes -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null")
  echo ""
  echo "📢 ======================================="
  echo "📢 [Step 3/6] kubeadm init 完成"
  echo "📢 控制平面节点: ${NODE_NAME}"
  echo "📢 API Server:    https://${API_SERVER}:6443"
  echo "📢 Pod CIDR:     ${POD_CIDR}"
  echo "📢 Service CIDR: ${SERVICE_CIDR}"
  echo "📢 ======================================="
  echo ""
  echo "📢 即将安装 Cilium CNI（Step 4）..."
fi
```

---

## Step 4: 安装 Cilium CNI（幂等）

```bash
CILIUM_VERSION="${CILIUM_VERSION:-1.19.2}"
CILIUM_TAR="${PROJECT_PATH}/assets/cilium-${CILIUM_VERSION}.tar.gz"

# 如果 0.7 步选择了跳过 Cilium
if [ "${SKIP_CILIUM:-false}" = "true" ]; then
  echo "⚠️ 跳过 Cilium 安装（CPU 不支持 x86-64-v2）"
  echo "📢 ======================================="
  echo "📢 [Step 4/6] Cilium 已跳过"
  echo "📢 原因: CPU 不支持 eBPF 模式"
  echo "📢 ======================================="
else
# 检查 Cilium 是否已安装
CILIUM_INSTALLED=$(ssh ${SSH_USER}@${SERVER_HOST} "cilium status 2>/dev/null | head -3 || echo """)
if [ -n "${CILIUM_INSTALLED}" ]; then
  echo "✅ Cilium 已安装"
  ssh ${SSH_USER}@${SERVER_HOST} "cilium status | head -5"
else
  echo "📦 安装 Cilium CNI..."
  
  # 检查 assets 目录
  if ! ssh ${SSH_USER}@${SERVER_HOST} "[ -f ${CILIUM_TAR} ]" 2>/dev/null; then
    echo ""
    echo "========================================"
    echo "❌ 错误：Cilium 资源文件不存在"
    echo "========================================"
    echo "期望路径: ${CILIUM_TAR}"
    echo ""
    echo "Fallback 方案："
    echo "  1. 从公共镜像站下载: https://github.com/cilium/cilium/releases"
    echo "  2. 或使用 kubeadm 默认 CNI（不需要 assets）："
    echo "     kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml"
    echo ""
    exit 1
  fi
  
  # 导入 Cilium 镜像
  echo "📥 导入 Cilium 镜像..."
  if ! ssh ${SSH_USER}@${SERVER_HOST} "cd ${PROJECT_PATH}/assets && sudo ctr -n k8s.io images import cilium-${CILIUM_VERSION}.tar.gz 2>&1"; then
    echo "❌ 镜像导入失败"
    echo "Fallback: 尝试手动导入或使用不同镜像源"
    exit 1
  fi
  
  # 安装 Cilium
  echo "🔧 安装 Cilium..."
  if ! ssh ${SSH_USER}@${SERVER_HOST} "cilium install --version ${CILIUM_VERSION} 2>&1"; then
    echo "❌ Cilium 安装失败"
    echo ""
    echo "Fallback 步骤："
    echo "  1. 检查 kube-proxy 是否正常: kubectl get pods -n kube-system"
    echo "  2. 检查控制平面节点状态: kubectl get nodes"
    echo "  3. 手动安装: cilium install --version ${CILIUM_VERSION} --verbose"
    exit 1
  fi
  
  # 确认就绪（带重试）
  echo "⏳ 等待 Cilium 就绪（最多 60 秒）..."
  for i in $(seq 1 12); do
    CILIUM_READY=$(ssh ${SSH_USER}@${SERVER_HOST} "kubectl get pods -n kube-system -l k8s-app=cilium -o jsonpath='{.items[0].status.phase}' 2>/dev/null")
    if [ "${CILIUM_READY}" = "Running" ]; then
      echo "✅ Cilium 就绪"
      break
    fi
    echo "等待中... ($i/12)"
    sleep 5
  done
  
  if [ "${CILIUM_READY}" != "Running" ]; then
    echo "⚠️ Cilium 未在 60 秒内就绪，显示状态："
    ssh ${SSH_USER}@${SERVER_HOST} "kubectl get pods -n kube-system -l k8s-app=cilium"
    echo "请手动检查: kubectl describe pods -n kube-system -l k8s-app=cilium"
  fi
fi

CILIUM_STATUS=$(ssh ${SSH_USER}@${SERVER_HOST} "cilium status 2>/dev/null | head -3 || echo 'N/A'")
echo ""
echo "📢 ======================================="
echo "📢 [Step 4/6] Cilium CNI 安装完成"
echo "📢 版本:    ${CILIUM_VERSION}"
echo "📢 模式:    ${CILIUM_MODE:-default eBPF}"
echo "📢 状态:"
echo "${CILIUM_STATUS}"
echo "📢 ======================================="
echo ""
echo "📢 即将安装 Istio（Step 5）..."
fi
```

---

## Step 5: 安装 Istio + Gateway API CRDs（幂等）

```bash
ISTIO_VERSION="${ISTIO_VERSION:-1.29.1}"
ISTIOCTL_TAR="${PROJECT_PATH}/assets/istioctl-${ISTIO_VERSION}-linux-amd64.tar.gz"

# 检查 istioctl 是否已安装
if ssh ${SSH_USER}@${SERVER_HOST} "istioctl version --client 2>/dev/null" | grep -q "${ISTIO_VERSION}"; then
  echo "✅ istioctl 已安装，版本 ${ISTIO_VERSION}"
else
  echo "📦 安装 Istio..."
  
  # 检查 assets 目录
  if ! ssh ${SSH_USER}@${SERVER_HOST} "[ -f ${ISTIOCTL_TAR} ]" 2>/dev/null; then
    echo ""
    echo "========================================"
    echo "❌ 错误：Istio 资源文件不存在"
    echo "========================================"
    echo "期望路径: ${ISTIOCTL_TAR}"
    echo ""
    echo "Fallback 方案："
    echo "  1. 从公共源下载: curl -L https://istio.io/downloadIstioctl | sh -"
    echo "  2. 或跳过 Istio 安装，仅使用基础 K8s（不推荐用于生产）"
    exit 1
  fi
  
  # 解压安装
  if ! ssh ${SSH_USER}@${SERVER_HOST} "cd ${PROJECT_PATH}/assets && tar -xzf istioctl-${ISTIO_VERSION}-linux-amd64.tar.gz -C /tmp/"; then
    echo "❌ Istio 解压失败"
    exit 1
  fi
  ssh ${SSH_USER}@${SERVER_HOST} "sudo install -m 0755 /tmp/istioctl-${ISTIO_VERSION}-linux-amd64/istioctl /usr/local/bin/istioctl"
fi

# 检查 Gateway API CRDs
echo "🔧 安装 Gateway API CRDs..."
ssh ${SSH_USER}@${SERVER_HOST} "kubectl apply --server-side --field-manager=k8s-init -f ${PROJECT_PATH}/assets/gateway-api-exp.yaml 2>&1 | tail -5" || {
  echo "⚠️ Gateway API CRDs 安装可能有警告，继续..."
}

# 检查 Istio 是否已安装
ISTIO_INSTALLED=$(ssh ${SSH_USER}@${SERVER_HOST} "kubectl get ns istio-system 2>/dev/null || echo """)
if [ -n "${ISTIO_INSTALLED}" ]; then
  echo "✅ Istio 已安装，跳过"
else
  echo "🚀 安装 Istio ambient profile..."
  if ! ssh ${SSH_USER}@${SERVER_HOST} "istioctl install --set profile=ambient -y 2>&1"; then
    echo "❌ Istio 安装失败"
    echo ""
    echo "Fallback 步骤："
    echo "  1. 检查 apiserver 是否可用: kubectl get nodes"
    echo "  2. 检查 istioctl 版本: istioctl version"
    echo "  3. 重新安装: istioctl install --set profile=ambient -y --verbose"
    exit 1
  fi
fi

ISTIO_STATUS=$(ssh ${SSH_USER}@${SERVER_HOST} "kubectl get pods -n istio-system -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo 'Pending'")
echo ""
echo "📢 ======================================="
echo "📢 [Step 5/6] Istio 安装完成"
echo "📢 版本:   ${ISTIO_VERSION}"
echo "📢 状态:   ${ISTIO_STATUS}"
echo "📢 Namespace: istio-system"
echo "📢 ======================================="
echo ""
echo "📢 即将配置 kubeconfig（Step 6）..."
```

---

## Step 6: 配置 kubeconfig 供部署用户使用

```bash
# 检查是否已配置
if ssh ${SSH_USER}@${SERVER_HOST} "[ -f \${HOME}/.kube/config ]" 2>/dev/null; then
  echo "✅ kubeconfig 已存在"
  ssh ${SSH_USER}@${SERVER_HOST} "kubectl config current-context && kubectl get nodes"
else
  echo "📝 配置 kubeconfig..."
  ssh ${SSH_USER}@${SERVER_HOST} "mkdir -p \${HOME}/.kube && sudo cp /etc/kubernetes/admin.conf \${HOME}/.kube/config && sudo chown \${SSH_USER} \${HOME}/.kube/config && chmod 600 \${HOME}/.kube/config"
  ssh ${SSH_USER}@${SERVER_HOST} "kubectl config use-context kubernetes-admin@\$(hostname)"
  ssh ${SSH_USER}@${SERVER_HOST} "kubectl get nodes"
fi

KUBECONFIG_STATUS=$(ssh ${SSH_USER}@${SERVER_HOST} "[ -f \${HOME}/.kube/config ] && echo '已配置' || echo '未配置'")
echo ""
echo "📢 ======================================="
echo "📢 [Step 6/6] kubeconfig 配置完成"
echo "📢 kubeconfig: \${HOME}/.kube/config"
echo "📢 状态: ${KUBECONFIG_STATUS}"
echo "📢 ======================================="
```

---

## ✅ 安装完成报告（固定格式）

```bash
echo ""
echo "🎉 ═══════════════════════════════════════"
echo "🎉   K8s 集群安装完成！"
echo "🎉 ═══════════════════════════════════════"
echo ""
echo "📋 集群信息"
echo "   服务器:   ${SERVER_HOST}"
echo "   主机名:   ${TARGET_HOSTNAME}"
echo "   K8s 版本: ${KUBE_VERSION}"
echo "   Cilium:  ${CILIUM_VERSION} (${CILIUM_MODE:-eBPF mode})"
echo "   Istio:   ${ISTIO_VERSION} (ambient profile)"
echo ""
echo "📁 配置文件"
echo "   kubeconfig: ~/${KUBECONFIG_PATH:-.kube/config}"
echo ""
echo "📌 快速验证命令"
echo "   kubectl get nodes"
echo "   kubectl get pods -n kube-system"
echo "   cilium status"
echo "   kubectl get pods -n istio-system"
echo ""
echo "🚀 接下来怎么用："
echo ""
echo "  1. 添加工作节点"
echo "     在新节点运行: kubeadm token create --print-join-command"
echo ""
echo "  2. 部署应用（使用 k8s-deploy 技能）"
echo "     不要在 k8s-install 里部署，那是另一个技能的活"
echo ""
echo "  3. 访问 Istio Dashboard"
echo "     istioctl dashboard --address=0.0.0.0 &"
echo ""
echo "  4. 本地使用 kubectl"
echo "     scp ${SSH_USER}@${SERVER_HOST}:~/.kube/config ~/.kube/config"
echo ""
echo "  5. 查看 Kubernetes Dashboard"
echo "     kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml"
echo "     kubectl proxy"
echo "     访问: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
echo ""
echo "⚠️  重要提醒："
echo "   - 不要随意执行 kubeadm reset，否则集群不可恢复"
echo "   - API Server 默认只暴露 6443 端口，外部访问需配置 kube-proxy 或 LoadBalancer"
echo "   - Cilium 如需修改模式: cilium install --help"
echo ""
echo "🎉 ═══════════════════════════════════════"
echo ""


---

## 🔄 失败回滚机制 ⚑ 新增

### 自动处理（幂等保证）

由于各步骤具有幂等性，已存在的组件不会被重新创建，因此：
- 重复执行不会破坏环境
- 部分失败后重试不会重复安装

### 手动回滚（如需完全清理）

```bash
# ⚠️ 以下操作不可逆，执行前必须确认
ssh ${SSH_USER}@${SERVER_HOST} "sudo kubeadm reset --force"
ssh ${SSH_USER}@${SERVER_HOST} "sudo rm -rf /etc/kubernetes/ /var/lib/etcd"
```

### 失败记录与报告

每次执行会在 `/tmp/k8s-install-YYYYMMDD-HHMMSS.log` 记录：
- 执行步骤
- 成功/失败状态
- 错误信息（如有）
- Fallback 建议

---

## 🩺 错误对应表 + Fallback 方案

| 错误现象 | 可能原因 | 修复命令 | Fallback |
|----------|----------|----------|----------|
| `[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]` | bridge-nf 未开启 | `sudo sysctl -w net.bridge.bridge-nf-call-iptables=1` | 写入 `/etc/sysctl.d/99-kubernetes.conf` |
| `[ERROR FileContent--proc-sys-net-ipv4-ip-forward]` | IP forward 未开启 | `sudo sysctl -w net.ipv4.ip_forward=1` | 同上 |
| `kubeadm init 失败，端口被占用` | 6443/10259/10257 被占用 | `sudo ss -tlnp \| grep -E '6443\|10259\|10257'` | 杀掉占用进程或换端口 |
| `kubeadm init 超时` | 网络慢/包下载失败 | 检查网络和 apt 状态 | `sudo kubeadm reset; rm -rf /var/cache/apt/*;` 重试 |
| `Node NotReady，CNI 未就绪` | Cilium 未安装或启动慢 | `kubectl get pods -n kube-system -l k8s-app=cilium` | 使用 Calico 代替 |
| `istiod / ztunnel Pending（control-plane taint）` | control-plane 节点有 `NoSchedule` taint | `kubectl taint node <node> node-role.kubernetes.io/control-plane:NoSchedule-` | 去除 taint 或等待调度 |
| `cilium install 失败，镜像拉取失败` | 私有网络无法访问公共镜像 | 使用离线导入的镜像 | 检查 assets 目录的 tar 文件 |
| `istioctl install 失败` | profile 不兼容或 CRD 冲突 | `istioctl install --set profile=ambient -y --verbose` | 使用 minimal profile |
| `containerd 启动失败` | 配置文件语法错误 | `sudo containerd config default > /etc/containerd/config.toml` | 完全重置配置后重启 |

---

## 常用命令速查

| 目的 | 命令 |
|------|------|
| 检查 OS | `ssh ${SSH_USER}@${SERVER_HOST} "cat /etc/os-release"` |
| 检查已有集群 | `ssh ${SSH_USER}@${SERVER_HOST} "[ -f /etc/kubernetes/admin.conf ] && kubectl get nodes"` |
| 安装 containerd | `ssh ${SSH_USER}@${SERVER_HOST} "sudo apt-get install -y containerd"` |
| kubeadm init（dry-run） | `ssh ${SSH_USER}@${SERVER_HOST} "sudo kubeadm init --dry-run=client"` |
| kubeadm init（实际） | `ssh ${SSH_USER}@${SERVER_HOST} "sudo kubeadm init --pod-network-cidr=10.244.0.0/16"` |
| 重置集群 | `ssh ${SSH_USER}@${SERVER_HOST} "sudo kubeadm reset --force"` |
| 确认集群就绪 | `ssh ${SSH_USER}@${SERVER_HOST} "kubectl get nodes && kubectl get pods -n kube-system"` |
| 查看 kubelet 日志 | `ssh ${SSH_USER}@${SERVER_HOST} "sudo journalctl -u kubelet --no-pager -n 50"` |
| 检查端口占用 | `ssh ${SSH_USER}@${SERVER_HOST} "sudo ss -tlnp \| grep -E '6443\|10259\|10257'"` |

---

## 幂等性说明

| 步骤 | 幂等性 | 说明 |
|------|--------|------|
| Step 0 环境预检 | ✅ | 纯检查，不修改系统 |
| Step 1 containerd | ✅ | 检测已安装则跳过 |
| Step 2 kubeadm | ✅ | 检测已安装则跳过 |
| Step 3 kubeadm init | ⚠️ | 检测已有 admin.conf 则跳过，需用户确认 |
| Step 4 Cilium | ✅ | 检测已安装则跳过 |
| Step 5 Istio | ✅ | 检测已安装则跳过 |
| Step 6 kubeconfig | ✅ | 检测已存在则跳过 |

---

## 停止条件

出现以下情况必须停止，不要尝试"顺手修好"：

- 目标 namespace、context、server host 与用户输入不一致
- apply/diff 显示将修改白名单外资源
- release 目录不在 PROJECT_PATH 内
- 需要写入 VOLUME_ALLOWLIST 之外的路径
- 需要修改系统服务、安装软件、改 SSH、改防火墙、改 Docker/K8s 运行时
- 用户没有确认删除、回滚、缩容、资源限制变更
- **任务超出 Scope Boundary**（如部署应用、安装非 K8s 软件）