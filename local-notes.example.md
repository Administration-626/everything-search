# 本机实测记录（模板）

复制本文件为 `local-notes.md`，填入本机数据。`local-notes.md` 已列入 `.gitignore`，
不会进仓库，所以可以放心写真实路径。

本文件放**随机器变化**的内容。换机器后按下面的重测清单更新 `local-notes.md`，
`SKILL.md` 里的通用知识不用动。

## 环境

| 项 | 值 | 来源 |
|---|---|---|
| es.exe | `C:\Users\<用户名>\AppData\Local\es\es.exe` | config.json |
| ES 版本 | `es -version` 的输出 | 命令 |
| Everything 版本 | `es -get-everything-version` 的输出 | 命令 |
| Everything 位置 | 主程序所在目录 | 手动填 |
| Python | `C:\Users\<用户名>\.workbuddy\binaries\python\versions\<版本>\python.exe` | WorkBuddy 自带 |
| 常用搜索根 | 你的常用目录 | 目录习惯 |

一条命令拿到前两项和 es 路径：`esearch.py --where`

**便携版的注意点**：不开机自启，点窗口关闭按钮会退出进程（配置里 `minimize_to_tray=0`）。
ES 报 `Error 8: Everything IPC not found` 时，去启动 `everything.exe`。

## 搜索语法命中数

记下本机的实际命中数。数字只作判据样例，用来说明该函数确实生效、量级如何。

| 语法 | 行为 | 本机命中 |
|---|---|---|
| `path:<目录>` | 递归包含，含全部子目录 | |
| `infolder:<目录>` | 只匹配直接子项 | |
| `parent:<目录>` | 与 infolder 行为一致 | |
| `ext:md` | 单扩展名 | |
| `ext:txt;md` | 多扩展名用分号 | |
| `folder:` / `file:` | 只列目录 / 只列文件 | |
| `startwith:<前缀>` | 文件名以此开头 | |
| `endwith:<后缀>` | 文件名以此结尾 | |
| `child:<名字>` | 匹配子项名 | |
| `wfn:<通配>` | 文件名通配 | |
| `type:file` | 按类型 | |
| `dm:today` / `dc:thisweek` | 修改 / 创建日期 | |
| `dupe:` | 重复文件 | |
| `empty:` | 空文件夹 | |
| `len:>100` | 文件名长度 | |
| `case:Foo` / `wholeword:foo` | 大小写敏感 / 全字匹配 | |
| `regex:^test_.*\.txt$` | 正则 | |
| `!条件` / `条件1\|条件2` | 取反 / 或 | |
| `path-part:<词>` | **无效果** | 应为 0，且要有裸词对照 |
| `attrib:H` | 读属性，**极慢** | 会超时 |
| `content:` | 内容搜索，需 Everything 1.5 | 1.4 上会超时 |

**交叉验证**：`infolder:` 的命中数应当等于 `ls -A <目录> | wc -l` 的输出，
可用它确认"直接子项"这个语义。

## 判据样例

判断函数是否生效，要拿它和不带函数的同一个词对比：

| 函数查询 | 命中 | 裸词对照 | 结论 |
|---|---|---|---|
| `startwith:<前缀>` | | | |
| `endwith:<后缀>` | | | |
| `child:<名字>` | | | |
| `path-part:<词>` | | | |

## 性能

| count | 返回 | 耗时 |
|---|---|---|
| 100 | | |
| 1000 | | |
| 10000 | | |

## 换机器后的重测清单

1. `es -version` 与 `es -get-everything-version`，更新版本号
2. `esearch.py --where`，确认 es 路径被找到
3. 跑几条语法查询记录 `totalResults`，更新命中数表
4. 验证编码：`es -n 2 -csv -size "ext:iso"`，输出按 GBK 解码正常则不必改
5. 确认 Everything 的运行方式（便携版还是安装版，是否开机自启）
6. 把新机器的 es 路径写进 `config.json`
