# akcheckinPy

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

## 配置模板与填写指引

项目根目录已提供 `config.template.json`。首次使用时请复制为 `config.json` 并按下面步骤填写。

```bash
cp config.template.json config.json
```

### 1) 计算账号键名（手机号 MD5）

脚本会读取 `config.json` 中以 `MD5(手机号)` 为键名的配置对象。

```bash
uv run python -c "import hashlib;print(hashlib.md5('你的手机号'.encode()).hexdigest())"
```

将模板中的 `<手机号的MD5值>` 替换为上面命令输出的字符串。

### 2) 必填项说明

- `enableRecruit`：是否执行公招。
- `enableBattle`：是否执行自动作战（需要可用 `battleLog`）。
- `enableBatchBuilding`：是否执行基建一键换班/休息。
- `battleStage`：自动作战关卡 ID，例如 `main_01-07`。
- `battleLog.<关卡ID>`：自动作战上报数据，必须包含：
  - `completeTime`：作战时长（秒）。
  - `stats.killedEnemiesCnt`：击杀数。
  - `stats.charStats` / `enemyStats` / `skillTrigStats` 等字段结构。

> 建议：先将 `enableBattle` 设为 `false`，确认签到/收菜流程正常后，再补全 `battleLog` 并开启自动作战。

### 3) 多账号写法

`config.json` 顶层可以放多个账号（多个手机号 MD5 作为不同键）：

```json
{
  "md5_账号A": {"enableRecruit": true},
  "md5_账号B": {"enableRecruit": false}
}
```

### 4) 常见问题

- 如果运行时 `battleLog` 相关字段缺失，自动作战会失败。
- 如果手机号 MD5 键名不匹配，会回退到空配置，导致大部分自动行为不开启。

## 开发检查

```bash
uv run ruff format .
uv run ruff check .
```
