#!/usr/bin/env python3
"""通过 ES（Everything 官方命令行工具）搜索本机文件。

ES 经 IPC 连接运行中的 Everything 实例，不走网络，没有端口暴露问题。

用法示例：
    python esearch.py "ext:md" --in C:/Users/someone/project -n 20
    python esearch.py "关键词 ext:pdf" -s date_modified --desc
    python esearch.py "ext:log size:>10mb" --files-only -n 50
    python esearch.py "dupe: size:>500mb" -n 30
    python esearch.py "ext:md" --count-only          # 只返回数量

实测要点（ES 1.1.0.38 + Everything 1.4.1.1032）：
1. ES 把位置参数用空格拼接成搜索表达式，含空格的单个参数会被当作精确短语。
   实测 path:C:\\...\\WorkBuddy ext:md 作为一个参数传得到 0 条，拆成两个参数得到 363 条。
   本脚本按空格拆分查询，引号内的空格保留。
2. 不要用 shlex.split 拆分：它会把反斜杠当转义符吃掉。
3. 路径限定用 -path 选项，不要用 path:"..." 写法。实测带引号的 path: 返回 0 条，
   而 -path 选项连含空格的路径（C:\\Program Files）都能正确查询。
4. ES 的 stdout 是系统本地代码页（简体中文 Windows 上是 GBK），必须按 GBK 解码，
   按 UTF-8 解码会得到乱码。
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CONFIG_NAME = "config.json"
ES_PATH_ENV = "ES_PATH"

SORT_MAP = {
    "name": "name",
    "path": "path",
    "size": "size",
    "date_modified": "date-modified",
    "date_created": "date-created",
    "extension": "extension",
    "run_count": "run-count",
}


def load_config(explicit=None):
    """读取本机配置。找不到或解析失败时返回空字典，不中断执行。"""
    script_dir = Path(__file__).resolve().parent
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(script_dir.parent / CONFIG_NAME)
    candidates.append(script_dir / CONFIG_NAME)
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def find_es(config):
    """按配置、环境变量、PATH、常见安装位置的顺序查找 es.exe。"""
    tried = []

    configured = config.get("es_path")
    if configured:
        if Path(configured).exists():
            return configured
        tried.append("config.json 的 es_path: {}".format(configured))

    from_env = os.environ.get(ES_PATH_ENV)
    if from_env:
        if Path(from_env).exists():
            return from_env
        tried.append("环境变量 {}: {}".format(ES_PATH_ENV, from_env))

    for name in ("es.exe", "es"):
        try:
            subprocess.run([name, "-version"], capture_output=True, timeout=15)
            return name
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            tried.append("PATH 里的 {}".format(name))

    guesses = [
        Path(os.environ.get("LOCALAPPDATA") or ".") / "es" / "es.exe",
        Path(os.environ.get("ProgramFiles") or ".") / "Everything" / "es.exe",
        Path(os.environ.get("ProgramFiles(x86)") or ".") / "Everything" / "es.exe",
    ]
    for guess in guesses:
        if guess.is_absolute() and guess.exists():
            return str(guess)
        tried.append("常见位置 {}".format(guess))

    raise SystemExit(
        "找不到 es.exe。\n已尝试：\n  "
        + "\n  ".join(tried)
        + "\n请从 https://github.com/voidtools/ES/releases 下载，"
        "把路径写进 config.json 的 es_path，或把所在目录加入 PATH。"
    )


def split_query(text):
    """按空格拆分查询，引号内的空格保留，反斜杠原样保留。"""
    tokens, current, in_quote = [], "", False
    for char in text:
        if char == '"':
            in_quote = not in_quote
            current += char
        elif char == " " and not in_quote:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char
    if current:
        tokens.append(current)
    return tokens


def run_es(es, argv, timeout):
    result = subprocess.run([es] + argv, capture_output=True, timeout=timeout)
    text = result.stdout.decode("gbk", errors="replace")
    if result.returncode != 0 and not text.strip():
        err = result.stderr.decode("gbk", errors="replace")[:400]
        raise SystemExit(
            "es.exe 返回码 {}。请确认 Everything 正在运行（ES 依赖 IPC）。\n{}".format(
                result.returncode, err
            )
        )
    return text


def human_size(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if number < 1024 or unit == "TB":
            if unit == "B":
                return "{:.0f} B".format(number)
            return "{:.1f} {}".format(number, unit)
        number /= 1024


def main():
    parser = argparse.ArgumentParser(
        description="通过 ES 命令行工具搜索本机文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="Everything 搜索语法")
    parser.add_argument("-i", "--in", dest="in_dir", help="限定目录，递归包含子目录")
    parser.add_argument("-n", "--count", type=int, default=100, help="返回条数上限，默认 100")
    parser.add_argument(
        "-s", "--sort", default="name", choices=sorted(SORT_MAP), help="排序字段，默认 name"
    )
    parser.add_argument("--desc", action="store_true", help="降序排列")
    parser.add_argument("--offset", type=int, default=0, help="跳过前 N 条")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--files-only", action="store_true", help="只列文件")
    group.add_argument("--folders-only", action="store_true", help="只列目录")
    parser.add_argument("--count-only", action="store_true", help="只输出命中数量")
    parser.add_argument("--json", action="store_true", dest="as_json", help="输出 JSON")
    parser.add_argument("--timeout", type=float, default=60.0, help="超时秒数")
    parser.add_argument("--config", help="配置文件路径，默认读 skill 根目录的 config.json")
    parser.add_argument("--where", action="store_true", help="输出 es 路径与版本，用于换机器后校准")
    args = parser.parse_args()

    es = find_es(load_config(args.config))

    if args.where:
        print("es.exe: {}".format(es))
        for label, flags in (
            ("es 版本", ["-version"]),
            ("Everything 版本", ["-get-everything-version"]),
        ):
            try:
                print("{}: {}".format(label, run_es(es, flags, args.timeout).strip()))
            except SystemExit as exc:
                print("{}: 读取失败（{}）".format(label, exc))
        return

    search_tokens = split_query(args.query or "")
    display = " ".join(search_tokens)
    if args.in_dir:
        clause = "path:{}".format(args.in_dir)
        display = (display + " " + clause).strip() if display else clause

    tokens = list(search_tokens)
    if args.in_dir:
        tokens += ["-path", args.in_dir]

    common = list(tokens)
    if args.files_only:
        common.insert(0, "/a-d")
    elif args.folders_only:
        common.insert(0, "/ad")

    if not args.query and not args.in_dir:
        raise SystemExit("查询为空。请给出搜索词，或用 --in 指定目录。")

    if args.count_only:
        text = run_es(es, ["-get-result-count"] + common, args.timeout)
        print(text.strip())
        return

    order = SORT_MAP[args.sort] + ("-descending" if args.desc else "-ascending")
    argv = ["-n", str(args.count), "-json", "-size", "-date-modified",
            "-date-format", "1", "-no-digit-grouping", "-sort", order]
    if args.offset:
        argv += ["-viewport-offset", str(args.offset)]
    argv += common

    text = run_es(es, argv, args.timeout)
    stripped = text.strip()
    if not stripped or stripped == "[]":
        print("命中 0 条")
        return
    try:
        rows = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise SystemExit("解析 ES 输出失败：{}\n原始输出前 300 字符：{}".format(
            exc, stripped[:300]))

    if args.as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print("查询: {}".format(display))
    print("返回 {} 条".format(len(rows)))
    print()
    for row in rows:
        name = row.get("filename", "")
        stamp = (row.get("date_modified") or "").replace("T", " ")
        size = human_size(row.get("size"))
        kind = "D" if name.endswith("\\") else " "
        print("{} {}  {:<9} {}".format(kind, stamp[:16], size, name))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
