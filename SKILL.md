---
name: everything-search
description: 用 Everything 在本机全盘按文件名搜索文件，毫秒级。经 ES 命令行走 IPC 连接 Everything 实例，不监听端口、无网络暴露。当用户问「某个文件在哪」「找一下 XX 文件」「有哪些 XX 类型的文件」「最近改过的 XX」，或需要按文件名、扩展名、大小、修改时间在整盘范围定位文件时使用。不适用于搜索文件内容，内容搜索仍用 Grep。
agent_created: true
---

# Everything 文件搜索

经 ES 命令行工具（es.exe）用 IPC 连接运行中的 Everything 实例。不走网络，不监听端口。
比递归遍历快三到四个数量级。

**本文件只写跨机器成立的内容。** 版本号、路径、实测命中数这些随环境变化的东西在
`local-notes.md`，机器相关路径在 `config.json`。换机器时改那两个文件，本文件不用动。

## 前置检查

用之前确认两件事：

1. **Everything 进程在运行。** ES 只是查询端，索引在 `everything.exe` 里。
   进程不在会报 `Error 8: Everything IPC not found. Please make sure Everything is running.`
   解法是启动 Everything，不是调 es 的参数。
2. **es.exe 能被找到。** 脚本按下面的顺序查找，命中即停：
   `config.json` 的 `es_path` → 环境变量 `ES_PATH` → PATH 里的 `es.exe` / `es` →
   `%LOCALAPPDATA%\es\es.exe` → `%ProgramFiles%\Everything\es.exe`。

一条命令同时确认两者并打印版本：

```bash
"$PY" "$E" --where
```

## 用法

```bash
# Git Bash 里 $HOME 是 /c/Users/xxx 格式，直接拿它拼路径会访问失败，
# 必须把开头的 /c/ 换成 C:/ 再用。这一步是必须的，不是可选优化。
H="$(echo "$HOME" | sed 's|^/c/|C:/|')"
PY="$(ls -d "$H"/.workbuddy/binaries/python/versions/*/python.exe 2>/dev/null | head -1)"
E="$H/.workbuddy/skills/everything-search/scripts/esearch.py"

"$PY" "$E" "ext:md" --in "C:/搜索根目录" -n 20
"$PY" "$E" "关键词 ext:pdf" -s date_modified --desc
"$PY" "$E" "ext:log size:>10mb" --files-only -n 50
"$PY" "$E" "dupe: size:>500mb" -n 30
"$PY" "$E" "ext:md" --count-only          # 只返回数量
"$PY" "$E" --where                        # 打印 es 路径与版本
```

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
| --config <文件> | 指定配置文件，默认读 skill 根目录的 config.json |
| --where | 打印 es 路径与两个版本号，用于换机器后校准 |

输出列固定为文件名、大小、修改时间（ISO-8601，由 ES 的 `-date-format 1` 产生）。

## 四个实测结论

1. **参数拼接**：ES 把位置参数用空格连接成搜索表达式，**含空格的单个参数被当作精确短语**。
   实测同一个查询，作为一个参数传得到 0 条，拆成两个参数得到 363 条。所以查询必须拆分。

2. **不要用 `shlex.split` 拆分**，它把反斜杠当转义符吃掉：
   `shlex.split(r'path:C:\Users\someone\project')` 的结果是
   `['path:C:Userssomeoneproject']`，反斜杠全没了。脚本里的 `split_query()`
   自己按空格拆，只保留引号内的空格。

3. **路径限定用 `-path` 选项，不要用 `path:"..."`**。实测带引号的写法返回 0 条，
   而 `-path` 连含空格的路径都能查：`-path "C:\Program Files" ext:exe` 正常返回。
   脚本的 `--in` 就是映射到 `-path`。

4. **stdout 是系统本地代码页**（简体中文 Windows 上是 GBK）。按 UTF-8 解码会得到乱码，
   必须按 GBK 解码。需要 UTF-8 时用 `-export-csv <文件> -utf8-bom` 导出再读。

## ES 选项速查（取自 `es -h`）

搜索：

| 选项 | 作用 |
|---|---|
| `-path <path>` | 搜索该路径下的子目录和文件（递归） |
| `-parent <path>` | 只匹配父目录正好是该路径的项 |
| `-parent-path <path>` | 搜索 path 的父目录下 |
| `/a-d` | 只列文件 |
| `/ad` | 只列目录 |
| `/a[RHSDAVNTPLCOIEUPM]` | 按属性过滤，前缀 `-` 表示排除 |
| `-r, -regex <expr>` | 正则 |
| `-i, -case` | 大小写敏感 |
| `-w, -ww, -whole-word(s)` | 全字匹配 |
| `-p, -match-path` | 匹配完整路径 |
| `-prefix` / `-suffix` | 匹配词首 / 词尾 |
| `-ignore-punctuation` / `-ignore-whitespace` | 忽略标点 / 空白 |

数量与统计：

| 选项 | 作用 |
|---|---|
| `-n <num>, -count <num>` | 最大结果数 |
| `-get-result-count` | 只输出命中总数，很快 |
| `-get-total-size` | 结果总大小 |
| `-get-folder-size <dir>` | 目录总大小 |

排序：`-sort <name-ascending|name-descending>`，name 可取 `name`、`path`、`size`、
`extension`、`date-created`、`date-modified`、`date-accessed`、`attributes`、`run-count`、
`date-recently-changed`、`date-run` 或任意属性名。`-s` 是按完整路径排序。

输出列：`-size`、`-date-modified`、`-date-created`、`-date-accessed`、`-attributes`、
`-run-count`、`-extension`、`-full-path-and-name`、`-add-columns <名;名>`。

输出格式：`-csv`、`-json`、`-tsv`、`-efu`、`-txt`；
`-size-format <0自动|1字节|2KB|3MB>`；
`-date-format <0自动|1ISO8601|2FILETIME|3ISO8601_UTC|4本地化>`；
`-no-digit-grouping`（去掉数值千分位）；`-double-quote`（路径加引号）。

分页：`-viewport-offset <n>`、`-viewport-count <n>`。

导出：`-export-csv <文件>`、`-export-json <文件>` 等，配 `-no-header`、`-utf8-bom`。

其他：`-timeout <毫秒>`（等数据库加载）、`-instance <名>`、`-reindex`、
`-get-everything-version`、`-exit`。

帮助文本里的两条约定：选项前缀可用 `/` 代替 `-`；用 `^` 前缀或双引号转义 `\ & | > < ^`。

## 搜索语法

| 语法 | 行为 |
|---|---|
| `path:C:\Dir\Sub` | 递归包含该路径，含所有子目录 |
| `infolder:C:\Dir` | 只匹配**直接子项**，不含子目录 |
| `parent:C:\Dir` | 与 `infolder:` 行为一致 |
| `ext:md` / `ext:txt;md` | 单扩展名 / 多扩展名用分号 |
| `folder:` / `file:` | 只列目录 / 只列文件 |
| `startwith:x` / `endwith:x` | 文件名以此开头 / 结尾 |
| `child:x` / `wfn:x*` | 匹配子项名 / 文件名通配 |
| `type:file` / `runcount:>0` | 按类型 / 运行次数 |
| `size:>10mb` | 大小 |
| `dm:today` / `dc:thisweek` | 修改日期 / 创建日期 |
| `dupe:` | 重复文件 |
| `empty:` | 空文件夹 |
| `len:>100` | 文件名长度 |
| `case:Foo` / `wholeword:foo` | 大小写敏感 / 全字匹配 |
| `regex:^test_.*\.txt$` | 正则 |
| `!条件` / `条件1\|条件2` | 取反 / 或 |
| `path-part:` | **无效果**，实测返回 0 |
| `attrib:H` | 读属性，**极慢**，实测超时 |
| `content:` | 内容搜索，需要 Everything 1.5 的内容索引 |

多个条件用空格分隔表示 AND。默认只匹配**文件名**，不匹配完整路径，
限定目录必须用 `--in`。

各条在本机的实测命中数见 `local-notes.md`。

## 函数有效性的判据

判断一个搜索函数是否生效，不能拿返回 0 当依据，那样会把语义不匹配误判成函数不存在。
正确做法是**拿函数查询和不带函数的同一个词对比**，两边都有值且不同才算生效。

举个例子：`infolder:` 只匹配直接子项，某个目录下查询返回 0，往往是因为该目录里没有
直属的匹配文件，不是函数不生效。可以拿去和 `ls` 数出的直接子项数交叉验证。

具体对照数据见 `local-notes.md`。

## 环境坑

1. **Git Bash 会把命令行参数里的反斜杠转成正斜杠**，连 Python raw string 里的 `\Users`
   都会被改写，`MSYS_NO_PATHCONV=1` 也拦不住。凡是要把 Windows 路径传给命令行工具，
   把转换逻辑写进脚本里，不要在 bash 里拼路径。

2. **路径格式在 Git Bash 里不稳定**：同一个目录，`/c/Users/...` 可能失败而 `C:/Users/...`
   成功，含中文的路径则相反。实测 `ls "$HOME/.workbuddy/skills/everything-search"`
   返回 No such file or directory，把 `$HOME` 展开的 `/c/` 换成 `C:/` 就正常。
   调用脚本前先做这一步转换，见上面的示例。移动、复制、删除这类写操作，
   同样用 Python 脚本配 `pathlib` 处理，不要依赖 shell 的路径转换。

3. **返回 0 条时先排除环境问题**：用 `--in` 指定一个确定存在的目录，仍为 0 再怀疑查询写法。
   同时确认 Everything 进程在运行。

## 换机器

1. 复制整个 `everything-search/` 目录到新机器的 `~/.workbuddy/skills/`
2. 装 Everything 和 es.exe
3. 改 `config.json` 里的 `es_path`
4. 跑 `esearch.py --where`，确认能读到两个版本号
5. 按 `local-notes.md` 末尾的重测清单更新实测数据

通用知识（ES 选项、语法语义、三条参数陷阱）跨机器有效，不用重测。

## 安全

ES 走 IPC，不监听端口，没有网络暴露面。早先用过 Everything 的 HTTP 服务器
（端口 2869），它默认绑定所有网卡，同网段能拉走全盘文件名列表，已停用。
相关脚本留在 `scripts/evsearch.py` 备用，日常不用。
