# Update And Refresh

## Use This Module

当用户要求以下任务时读取本模块：

- 更新某个已托管 skill
- 刷新全部 upstream skill
- 重新生成 managed 版本

## Flow

1. 读取 `catalog/sources/<skill-id>.json`
2. 判断是否启用了 upstream 更新
3. 拉取或读取最新上游内容
4. 比较 `upstream_revision`
5. 有变化时：
   - 更新 `upstream/`
   - 重新执行风险筛查
   - 重新生成 `managed/`
   - 更新报告和 registry
6. 如果 `managed_dirty = true`，在覆盖前必须询问用户
7. 在确认后才执行分发与 git 发布

## Local-Only Skills

对于 `source_type = local-bootstrap` 且 `upstream_enabled = false` 的 skill：

- 不尝试拉取外部来源
- 仅支持本地 managed 编辑与重新分发
