# k8s-deploy 技能报告

> **技能名称**：k8s-deploy
> **版本**：v2.0（2026-05-13 重大更新）
> **生成时间**：2026-05-13
> **功能**：在已有 K8s 集群上，通过 Kustomize 部署项目（含资源规划、自动化修复、诊断链路）

---

## 零、版本变更记录（v1.0 → v2.0）

本次更新解决了 Redis 连接失败的根本原因，并完善了自动修复机制。

| # | 变更类型 | 变更内容 | 原因 |
|---|----------|----------|------|
| 1 | **新增 Step 4f** | Redis 配置检查与修复（自动检测 WAR 包内 host 硬编码） | Pod Ready=1 但 Redis 连不上（`地址: 127.0.0.1:6379`），根因是 WAR 包内 `application-dev.yml` 写死了 `host: 127.0.0.1`，环境变量无效 |
| 2 | **新增问题 4** | "Redis 连不上（WAR 包内配置文件硬编码）"根因分析与修复方案 | 反复出现的 Redis 连接问题，之前的错误手册只写了添加环境变量，但环境变量对硬编码 YAML 配置无效 |
| 3 | **新增错误 4 完整修复链路** | Step 1-5 诊断 + 方案 B（volume mount 覆盖）+ 验证命令 | 错误手册条目 4 原本只写了"添加环境变量"，不完整 |
| 4 | **更新错误手册** | 错误 4 修复方案改为 volume mount + Step 4f | 环境变量方案对 WAR 内硬编码配置无效 |
| 5 | **更新示例 2** | Redis 连接失败示例改为 volume mount 路径 | 反映真实修复路径 |
| 6 | **Probe 改为 tcpSocket（历史）** | startupProbe/readinessProbe/livenessProbe 从 HTTP 改为 tcpSocket | `/actuator/health/ping` 返回 404（应用未实现该端点），导致 READY=0 |
| 7 | **JVM 内存修正（历史）** | JVM -Xmx 从 12g 降至 2g，memory limit 从 16Gi 降至 4Gi | Git 仓库配置针对 32Gi+ 服务器，实际节点 15Gi，OOM 数学上必然 |

---

## 一、概述

**触发关键词**

`部署` `上线` `发布` `重新部署`

**触发场景**

- K8s 集群已就绪、需要部署/更新项目到集群
- 项目需要资源调整后重新部署

**约束**：
- 只操作指定服务器和项目，禁止修改系统无关配置
- 所有参数显式提供，不使用硬编码默认值
- 全自动执行，不等待用户确认，各 step 自动连续进行

---

## 二、参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SERVER_HOST` | SSH 目标主机（IP 或域名） | 必填 |
| `SSH_USER` | SSH 用户名 | 必填 |
| `SSH_PORT` | SSH 端口 | `22` |
| `PROJECT_PATH` | 项目部署配置目录 | 必填 |
| `NAMESPACE` | K8s 命名空间 | 必填 |
| `RESOURCE_ALLOWLIST` | 允许操作的 K8s 资源名或 label | 必填 |
| `EXPECTED_CONTEXT` | 预期 kube-context | 可选 |
| `RELEASE_DIR` | generate.sh 输出目录 | `release` |
| `SKIP_PREVIEW` | 跳过 kubectl diff 预览 | `false` |
| `FORCE_APPLY` | 强制 apply（字段冲突时） | `false` |
| `WAIT_TIMEOUT` | Pod 就绪等待超时（秒） | `900` |

---

## 三、完整工作流程

```
Phase 1: 部署项目（每次部署）
├── Step 0: 环境预检（身份、集群、路径、参数完整性）
├── Step 1: 展示并确认目标环境（自动，无需用户确认）
├── Step 2: 前置校验（参数 + SSH + 路径安全）
├── Step 3: 前置检查（可选脚本 preflight.sh）
├── Step 4: 修改配置 + K8s 环境适配检测
│   ├── Step 4a: 资源规划强制检查（所有组件 limits vs 节点可用内存）
│   ├── Step 4b: JVM vs 容器内存一致性检查
│   ├── Step 4c: 硬编码检测
│   ├── Step 4d: 资源自动协调（JVM/内存超限自动修复）⚠️ 每次部署前无条件执行
│   ├── Step 4e: Probe 路径自动探测与修复（HTTP probe 404 → tcpSocket）
│   └── Step 4f: Redis 配置检查与修复（WAR 包内 host 硬编码检测）
├── Step 5: 生成清单（必须 generate.sh）
├── Step 6: 部署前审查（diff / dry-run）
├── Step 7: 应用部署
├── Step 8: 等待就绪
└── Step 9: 健康检查
```

---

## 四、核心自动化机制

### Step 4a：资源规划强制检查（入口门卫）

**每次部署前无条件执行**，防止配置漂移。

```bash
# 获取节点总内存
NODE_MEMORY_GI=$(kubectl get node -o jsonpath='{.items[0].status.capacity.memory}' / 1024 / 1024)
K8S_SYSTEM_MEM=3  # Gi，etcd + apiserver + kubelet + cilium + istio
AVAILABLE_MEM=$((NODE_MEMORY_GI - K8S_SYSTEM_MEM))

# 遍历 service/ 下所有组件，汇总 memory limits
# 计算 limits 总和 vs 节点可用内存

if [ ${TOTAL_LIMITS} -gt ${AVAILABLE_MEM} ]; then
  echo "❌ 资源不足！立即停止"
  exit 1
fi
```

**强制规则**：limits 总和超过节点可用内存 → 停止部署，不允许继续。

---

### Step 4d：资源自动协调（防OOM）

**每次部署前无条件执行**，防止配置漂移。

```bash
# 内存超限 → 自动按比例压缩所有组件 limits
# JVM -Xmx > 容器 limit 70% → 自动下调至 limit 的 70%
# 不提问，直接修，修完继续
```

**修复逻辑**：
- `TOTAL_LIMITS > AVAILABLE_MEM` → 按比例压缩所有组件 memory limit
- `JVM -Xmx > CONTAINER_LIMIT × 70%` → 自动将 JVM heap 下调至 limit 的 70%

---

### Step 4e：Probe 路径自动修复（防 READY=0）

**检测触发，非无条件执行**。

```bash
# 检测机制：Pod Running 但 READY=0，且 HTTP probe 返回 404
# 自动判断：应用未实现 /actuator 路径 → 将 probe 改为 tcpSocket
# 修改源码 YAML，generate.sh 后生效，永久有效
```

### Step 4f：Redis 配置检查与修复（防 Redis host 硬编码）

**检测触发，非无条件执行**（但 Step 4f 会在 generate.sh 后、kubectl apply 前检查是否有运行中 pod）。

```bash
# 检测机制：检查当前 deployment 是否已有 webapps-classes volume
# 若无运行中 pod → 跳过（generate.sh 后仍会检测）
# 若有运行中 pod → 检查 pod 内 application-dev.yml 的 host 字段
# 若 host: 127.0.0.1 → 自动执行修复流程

# 修复流程：
# 1. 导出 pod 内 application-dev.yml
# 2. sed 修改 host: 127.0.0.1 → host: redis
# 3. scp 到服务器 volumes 目录
# 4. 将 webapps-classes volume + volumeMount 写入源码 YAML（永久生效）
# 5. 重启 Pod
```

---

## 五、关键设计理念

### 全自动执行

Step 0 → Step 9 全程自动连续执行，不等待用户"继续"确认。报告每步执行状态，但不中断等待。

### 配置漂移防护

> **⚠️ 强制规则：Step 4a 和 Step 4d 每次部署都必须无条件执行，不论本地 YAML 是否被改动过。这是防止配置漂移（configuration drift）的核心机制。**

原因：Git 仓库配置给大服务器（32Gi+），实际部署节点内存偏小（8-16Gi），每次 `git checkout` 会恢复仓库的错误值。Step 4a/4d 作为前置门卫，确保每次部署出来的配置都是匹配目标服务器的正确值。

### 根因分离

| 层级 | 问题 | 处置 |
|------|------|------|
| 源头 | Git 仓库默认值不匹配目标服务器 | ❌ 无写权限，暂不处理 |
| 兜底 | 每次部署前自动修正（Step 4d/4e） | ✅ 已实现 |
| 监控 | 部署后 YAML 被手动改坏 | ✅ Step 4a/4d 每次强制执行 |

---

## 六、错误诊断链路手册

| # | 错误现象 | 诊断要点 | 修复方案 |
|---|----------|----------|----------|
| 1 | OOMKilled | JVM -Xmx vs 容器 limit | Step 4d 自动降 heap；或手动调低 memory limit |
| 2 | Pod Pending（Insufficient memory） | limits 总和 vs 节点内存；多 RS 残留 | 清理旧 RS；缩容空闲组件 |
| 3 | Pod Running 但 READY=0 | HTTP probe 404？tcpSocket 失败？ | Step 4e 自动修复；或删除 probe |
| 4 | 应用连不上 Redis/MySQL | WAR 包内 host 硬编码？网络策略？ | volume mount 覆盖 application-dev.yml（Step 4f）；或检查 NetworkPolicy |
| 5 | ImagePullBackOff | 镜像地址错误/不存在 | 确认 DEPLOY_IMAGE 和私仓认证 |
| 6 | CrashLoopBackOff | 应用启动失败 | kubectl logs 查因 |

---

## 七、调度冲突自动决策原则

当 Pod Pending（资源不足）时，自动判断并执行，无需询问：

| 场景 | 自动决策 |
|------|---------|
| 新 Pod Pending + 旧版 Pod Running | 删除旧版 Pod，释放资源给新 Pod |
| 多个 ReplicaSet 同时存在 | 删除 DESIRED=0 的旧 RS，释放资源 |
| 某组件空闲（无流量）且占用大量内存 | 临时缩容到 0，调度新 Pod 后再扩容 |
| 节点内存即将耗尽（>115%） | 优先保核心服务，缩容或删除边缘服务 |

**决策原则**：
1. 服务平稳运行优先于保持旧版本
2. 核心服务优先于边缘服务（由用户定义或根据组件名判断）
3. 有新版本时旧版服从新版本调度
4. 所有决策事后报告，不事前询问（紧急情况）

---

## 八、反复出现问题的根因与应对

### 问题 1：OOMKilled / JVM -Xmx 超容器 limit

**根因**：Git 仓库配置值与目标服务器硬件不匹配（仓库按大服务器32Gi+配置，实际节点偏小8-16Gi）。

**我们能做什么**：
- ❌ 改 Git 仓库——需要写权限，当前无权限
- ✅ **Step 4d 自动修复**：检测到 JVM > 容器 limit 70% 时自动压缩
- ✅ **服务器本地副本已修正**：内存 4Gi、JVM -Xmx2g，下次部署如果 git checkout 覆盖了，Step 4d 会再次修回来

### 问题 2：Pod Running 但 READY=0（HTTP probe 返回 404）

**根因**：probe 路径（如 `/actuator/health/ping`）在应用里不存在（应用未实现该端点，或路径不匹配）。

**我们能做什么**：
- ❌ 改 Git 仓库——需要写权限，当前无权限
- ✅ **Step 4e 自动修复**：检测到 HTTP probe 404 → 自动改为 tcpSocket
- ✅ **服务器本地副本已修正**：所有 probes 改为 tcpSocket，generate.sh 后生效

### 问题 4：Redis 连不上（WAR 包内配置文件硬编码）

**根因**：应用读取的是 **WAR 包内**的 `application-dev.yml`，其中 `redis.host: 127.0.0.1`。这是应用打包时写死的，不是 K8s 配置问题。环境变量 `REDIS_HOST=redis` 对 Spring Boot 配置有效，但当 Redisson 直接读取 YAML 而非通过 Spring 环境变量时，环境变量不生效。

**诊断要点**：
- 应用日志出现 `地址: 127.0.0.1:6379` 或 `Unable to connect to Redis server: 127.0.0.1/127.0.0.1:6379`
- 从 pod 内读取：`kubectl exec <pod> cat /usr/local/tomcat/webapps/caij_saas/WEB-INF/classes/application-dev.yml | grep host:` → 返回 `host: 127.0.0.1`（确认是 WAR 内文件的问题）

**修复方案（方案 B：volume mount 覆盖）**：
1. 从运行中 pod 导出 `application-dev.yml`
2. 修改 `host: 127.0.0.1` → `host: redis`
3. 复制到服务器 `/opt/caij-saas/volumes/tomcat/webapps-classes/application-dev.yml`
4. 在 `01-deployment.yml` 中加入 `webapps-classes` volume 和 volumeMount，挂载到 `/usr/local/tomcat/webapps/caij_saas/WEB-INF/classes`
5. 重启 Pod 生效

**永久修复**：webapps-classes volume 和 volumeMount 已写入源码 YAML（`service/tomcat/01-deployment.yml`），`generate.sh` 后自动生效，下次部署无需重复修复。

---

## 九、部署完成报告（固定格式）

部署完成后，必须按以下格式报告：

> 🎉 **部署完成！**
> - 项目：`<name>`
> - 命名空间：`<namespace>`
> - 状态：`<Ready/Failed>`
> - 访问地址：`<url>`（如有）
> - 源码来源：`<来源方式>`

---

## 十、幂等性说明

- **generate.sh**：幂等，可重复执行
- **kubectl apply**：幂等，重复执行会保持目标状态
- **kubectl delete**：非幂等，删除操作不可恢复，执行前必须用户确认 `yes`
- **kubectl scale**：幂等

---

## 十一、停止条件（立即停止，不要尝试"顺手修好"）

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

## 十二、常用命令速查

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