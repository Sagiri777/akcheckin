# akcheckin（Python + uv）

明日方舟自动签到/日常脚本的 Python 重构版本，使用 `uv` 管理依赖与运行。

## 功能

- 自动签到
- 收取邮件
- 基建相关操作
- 公招
- 剿灭扫荡
- 日常/周常任务奖励
- 信用商店购买

## 使用方式

```bash
uv sync
uv run akcheckin <手机号> <密码>
```

## 开发检查

```bash
uv run ruff format .
uv run ruff check .
```
