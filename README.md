# everything-search

Windows 全盘文件秒搜的 skill，面向 Claude Code / WorkBuddy 一类的 agent 运行环境。
通过 Everything 官方命令行工具 ES（`es.exe`）经 IPC 查询，毫秒级返回，替代慢速的目录遍历。

## 与递归遍历的对比

Glob 和 Grep 是递归遍历，范围一大就慢，甚至撞上超时上限。

| 方式 | 1000 条结果 | 说明 |
|---|---|---|
| 递归遍历 | 秒级到超时 | 没有索引，靠逐个目录读 |
| Everything + ES | 22 ms | 索引常驻内存，与文件总量基本无关 |

顺带得到一个好处：ES 走 IPC，不监听端口，没有网络暴露面。

## 依赖

- Windows
- [Everything](https://www.voidtools.com/) 本体，**必须保持运行**，ES 只是查询端
- [ES 命令行工具](https://github.com/voidtools/ES/releases)，解压出 `es.exe`，建议加入 PATH

## 安装

### 放到哪里

agent 工具启动时会扫描固定目录，把里面的 `SKILL.md` 加载成可用能力。位置由工具约定：

| 工具 | 用户级（全局可用） | 项目级（仅该项目可用） |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/` | `<工作区>/.workbuddy/skills/` |
| Claude Code | `~/.claude/skills/` | `<项目>/.claude/skills/` |

本仓库同时兼容两者，放哪个目录取决于你用哪个工具。下面以 WorkBuddy 的用户级目录为例。

### 装法

**目录还不存在时，直接 clone：**

```bash
git clone git@github.com:Administration-626/everything-search.git \
  ~/.workbuddy/skills/everything-search
```

**目录已存在时不要用 clone。** `git clone` 到非空目录会直接报错，改用：

```bash
cd ~/.workbuddy/skills/everything-search
git init
git remote add origin git@github.com:Administration-626/everything-search.git
git fetch origin
git checkout -b main origin/main
```

**不用 git 也行**，下载 zip 解压到目标目录同样可用。

> Git Bash 里 `~` 展开成 `/c/Users/xxx`，某些命令拼这个路径会失败。
> 遇到问题改用 `C:/Users/xxx/...`，详见下面的「用法」一节。

### 配置

```bash
cd ~/.workbuddy/skills/everything-search
cp config.example.json config.json
```

编辑 `config.json`，至少填对 `es_path`。脚本找不到它时会依次尝试环境变量 `ES_PATH`、
PATH、`%LOCALAPPDATA%\es\es.exe`、`%ProgramFiles%\Everything\es.exe`，所以填错也不一定断。

验证：

```bash
python scripts/esearch.py --where
```

打印出 es 路径和两个版本号即为正常。

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
| `query` | Everything 搜索语法，可省略，只给 `--in` 也行 |
| `-i, --in DIR` | 限定目录，递归包含子目录，斜杠方向不限 |
| `-n, --count` | 返回条数上限，默认 100 |
| `-s, --sort` | `name` / `path` / `size` / `date_modified` / `date_created` / `extension` / `run_count` |
| `--desc` | 降序 |
| `--offset N` | 跳过前 N 条 |
| `--files-only` / `--folders-only` | 只列文件 / 只列目录 |
| `--count-only` | 只输出命中数量 |
| `--json` | 输出 JSON |
| `--config <文件>` | 指定配置文件 |
| `--where` | 打印 es 路径与版本号，用于换机器后校准 |

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

## 注意事项

三条会静默失效的坑，都写在 `SKILL.md` 里：

1. ES 把位置参数用空格拼接成搜索表达式，含空格的单个参数会被当作精确短语。
   查询必须拆成多个参数传。
2. 不要用 `shlex.split` 拆分查询，它把反斜杠当转义符吃掉。
3. 路径限定用 `-path` 选项，不要用 `path:"..."`，后者实测返回 0。

另外 ES 的 stdout 是系统本地代码页（简体中文 Windows 上是 GBK），按 UTF-8 解码会乱码。

## 致谢

- [Everything](https://www.voidtools.com/) 与作者 David Carpenter
- [ES CLI](https://github.com/voidtools/ES)

本仓库只是 Everything / ES 的封装，检索能力全部来自上述项目。
