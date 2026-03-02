# Overview

## Role

`skills-manager` 是当前仓库 `my-skills` 的统一技能管理入口。

目标：

- 将现有与外部 skill 统一纳管到 `catalog/`
- 维护 `upstream` 与 `managed` 双轨
- 生成中文优化版 managed
- 输出简短风险与用法报告
- 分发到目标 agent 目录
- 在确认后提交并推送仓库

## Operating Mode

默认半自动：

- 自动做：发现、临时下载、风险筛查、managed 生成、registry 更新、报告生成
- 先询问：覆盖现有内容、分发到 agent、`git commit`、`git push`

## Repository Root

仓库根目录固定为当前 `my-skills` 工作区。

脚本和操作都应以仓库根目录为基准，不要在文档中硬编码用户主目录绝对路径。

## Source Of Truth

唯一真源：

- `catalog/skills/<skill-id>/managed/`

只读参考：

- `catalog/skills/<skill-id>/upstream/`

状态文件：

- `catalog/sources/`
- `catalog/reports/`
- `catalog/agents/`
- `catalog/locks/registry.json`
