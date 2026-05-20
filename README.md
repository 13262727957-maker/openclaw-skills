# OpenClaw Skills

This repository contains skills for the OpenClaw AI Assistant.

## Structure

- `workspace-skills/` - Custom user skills (18 skills)
- `built-in-skills/` - Built-in skills (53 skills)

## Skills Overview

### Workspace Skills
- `api-diff-table` - 源码接口与 Swagger 接口的二维对比表生成工具
- `api-scanner-from-source` - 从 Git 源码仓库深度扫描，生成接口文档
- `api-scanner-from-swagger` - 对已部署系统的 Swagger 文档进行解析
- `api-validator` - API 校验工具
- `business-skill-executor` - 业务技能执行器
- `feishu-*` - 飞书文档、知识库、权限相关技能
- `k8s-deploy` - 通过 Kustomize 在 K8s 集群上部署项目
- `k8s-install` - 从零安装 K8s 集群
- `minimax-ppt-slides` - MiniMax PPT 演示文稿生成
- `swagger-source-matcher` - Swagger 模块与源码项目的路径匹配工具
- `skill-creator` / `skill-evaluator` - 技能创建与评估
- 其他工具技能

### Built-in Skills
包括 GitHub、Discord、Slack、Notion、Obsidian、Spotify、Weather、Coding Agent 等集成技能。

Generated on 2026-05-20.