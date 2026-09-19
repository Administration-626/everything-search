# everything-search

Everything 的命令行封装，面向 Claude Code / WorkBuddy 一类的 agent 运行环境。
经 ES（`es.exe`）走 IPC 查询全盘文件，毫秒级返回。

## 与递归遍历的对比

| 方式 | 1000 条结果 |
|---|---|
| 递归遍历 | 秒级到超时 |
| Everything + ES | 22 ms |

ES 走 IPC，不监听端口。

## 依赖

- [Everything](https://www.voidtools.com/) 本体，**必须保持运行**，ES 只是查询端
- [ES 命令行工具](https://github.com/voidtools/ES/releases)

## 安装

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

## 致谢

- [Everything](https://www.voidtools.com/) 与作者 David Carpenter
- [ES CLI](https://github.com/voidtools/ES)
