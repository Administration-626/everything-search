# everything-search

Windows 全盘文件秒搜的 skill，面向 Claude Code / WorkBuddy 一类的 agent 运行环境。
通过 Everything 官方命令行工具 ES（`es.exe`）经 IPC 查询，毫秒级返回，替代慢速的目录遍历。

## 与递归遍历的对比

| 方式 | 1000 条结果 |
|---|---|
| 递归遍历 | 秒级到超时 |
| Everything + ES | 22 ms |

ES 走 IPC，不监听端口。

## 依赖

- Windows
- [Everything](https://www.voidtools.com/) 本体，**必须保持运行**，ES 只是查询端
- [ES 命令行工具](https://github.com/voidtools/ES/releases)，解压出 `es.exe`，建议加入 PATH

## 安装

装到 skill 目录：

| 工具 | 目录 |
|---|---|
| WorkBuddy | `~/.workbuddy/skills/everything-search/` |
| Claude Code | `~/.claude/skills/everything-search/` |

装 Everything、es.exe、生成 `config.json` 这三步交给 AI 做：

> 把 everything-search 装成 skill，装好 Everything 与 es.exe，参照 `config.example.json`
> 生成 `config.json` 并填入本机实际路径，最后跑 `python scripts/esearch.py --where` 验证。

## 用法

Git Bash 里 `$HOME` 展开成 `/c/Users/xxx`，这个格式直接拼路径可能访问不到，
需要把开头的 `/c/` 换成 `C:/` 再用：

```bash
H="$(echo "$HOME" | sed 's|^/c/|C:/|')"
PY="$(ls -d "$H"/.workbuddy/binaries/python/versions/*/python.exe 2>/dev/null | head -1)"
E="$H/.workbuddy/skills/everything-search/scripts/esearch.py"

"$PY" "$E" "ext:md" --in "C:/搜索根目录" -n 20
"$PY" "$E" "关键词 ext:pdf" -s date_modified --desc
"$PY" "$E" "ext:log size:>10mb" --files-only -n 50
"$PY" "$E" "dupe: size:>500mb" -n 30          # 重复的大文件
"$PY" "$E" "ext:md" --count-only              # 只要数量
"$PY" "$E" "--where"                          # 环境信息
```

主要参数：

| 参数 | 说明 |
|---|---|
| query | Everything 搜索语法，可省略，只给 --in 也行 |
| -i, --in DIR | 限定目录，递归包含子目录，斜杠方向不限 |
| -n, --count | 返回条数上限，默认 100 |
| -s, --sort | name / path / size / date_modified / date_created / extension / run_count |
| --desc | 降序 |
| --offset N | 跳过前 N 条 |
| --files-only / --folders-only | 只列文件 / 只列目录 |
| --count-only | 只输出命中数量 |
| --json | 输出 JSON |
| --config <文件> | 指定配置文件 |
| --where | 打印 es 路径与版本号，用于换机器后校准 |

## 文件说明

| 文件 | 内容 | 换机器时 |
|---|---|---|
| `SKILL.md` | 通用知识：ES 选项表、搜索语法语义、参数陷阱、判据方法 | 不用动 |
| `config.json` | 本机路径与版本号（已 gitignore，不入库） | 改这里 |
| `config.example.json` | 配置模板 | 参考 |
| `local-notes.md` | 本机实测命中数、性能数字（已 gitignore，不入库） | 重测后覆盖 |
| `local-notes.example.md` | 上者的脱敏模板 | 参考 |
| `scripts/esearch.py` | 主脚本，走 ES 命令行 | 不用动 |
| `scripts/evsearch.py` | 备用脚本，走 Everything 的 HTTP 服务器（默认关闭，有网络暴露面） | 不用动 |

`config.json` 和 `local-notes.md` 含本机信息，已列入 `.gitignore`，不进仓库。
首次使用时从对应的 `.example` 文件复制一份再填。

## 致谢

- [Everything](https://www.voidtools.com/) 与作者 David Carpenter
- [ES CLI](https://github.com/voidtools/ES)
