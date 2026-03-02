# Audit And Risk

## Goal

做启发式静态风险筛查，不承诺完整安全保证。

## Check Categories

- 危险 shell 命令
- 读写敏感目录，如 `~/.ssh`、`~/.aws`
- 请求 secrets、tokens、私钥
- 下载后直接执行远端内容
- 模糊授权语句，如忽略限制、绕过策略
- 超出常规 skill 管理范围的系统控制请求

## Risk Levels

- `passed`
- `warned`
- `blocked`

## Policy

- `passed`：允许继续 managed 生成
- `warned`：允许导入，但分发前必须明确确认
- `blocked`：默认暂停自动生成和分发，先向用户说明原因

## Output

每次风险筛查都应写入报告，至少包含：

- 风险等级
- 命中规则
- 是否建议分发
