# tasks.json 字段约束

> 用于在生成 `tasks.json` 时快速校验关键字段。

## 顶层结构

```json
{
  "tasks": []
}
```

- `tasks` 必须是数组，至少包含 1 个任务。
- 任务按依赖层次排序：基础层在前，组合层在后。

## 单个任务字段

1. `task`
- 字符串，建议 3-80 字符。
- 使用祈使语气，任务名在数组内唯一。

2. `description`
- 单句字符串，建议 10-200 字符。
- 不要换行，不要写成多步骤列表。

3. `steps`
- 数组，可为空。
- 若非空：`step` 从 1 递增且无重复；`description` 应是可验证动作。

4. `acceptance-criteria`
- 字符串，写可测量条件。
- 避免“works correctly / properly / safe enough”等模糊表达。

5. `test-plan`
- 必须包含三个键：`unit`、`integration`、`e2e-manual`。
- 三个键都必须是数组（可空）。

6. `skills`
- 字符串数组。
- 只放与该任务直接相关的 skill；不要重复。

7. `complete`
- 布尔值。
- 新任务必须是 `false`。

## Shift-Left 检查

写测试项前先问：这个问题能否更早在更低层捕获？

1. 能在 `unit` 抓到的缺陷，不得放到 `integration` 或 `e2e-manual`。
2. `integration` 只检查跨层连接与真实数据流。
3. `e2e-manual` 只保留自动化难以验证的人工感知项。

## 最终检查清单

1. JSON 解析通过。
2. 每个任务均含必填字段。
3. `steps` 编号连续。
4. `test-plan` 三键齐全。
5. 所有 `complete` 都是 `false`。
