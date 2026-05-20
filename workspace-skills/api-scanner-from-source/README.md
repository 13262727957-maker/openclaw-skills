# api-scanner-from-source

## 作用

从 Git 源码全项目扫描，生成结构化接口文档 + 项目分析报告。

## 概况

| 项目 | 说明 |
|------|------|
| 输入 | Git 仓库地址 + 分支 |
| 输出 | `source-api-doc.md`（接口文档）、`source-scan-report.md`（项目分析报告） |
| 扫描内容 | Controller 接口、参数类型、VO/DTO、模块架构 |
| 接口数量 | 支持 1500+ 接口规模 |
| 技术栈 | Java Maven + Spring Boot |

## 使用方式

```
输入参数：
  GIT_URL = "https://git.xxx.com/repo.git"
  BRANCH = "main"  # 可选，默认 main

输出文件：
  /tmp/api-scan/{项目名}/source-api-doc.md     ← 接口文档
  /tmp/api-scan/{项目名}/source-scan-report.md ← 项目分析报告
```

## 文档内容

**source-api-doc.md**：
- 按模块分组（system、core 等）
- 每个接口：HTTP方法、完整路径、传参方式、参数名、参数类型、响应示例

**source-scan-report.md**：
- 项目定位与技术栈
- Maven 模块结构
- 代码规模统计

## 版本

v3.0.0（2026-05-14）