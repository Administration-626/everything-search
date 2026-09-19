#!/usr/bin/env python3
"""通过 Everything 的 HTTP 服务器搜索本机文件。

用法示例：
    python evsearch.py "ext:md" --in C:/Users/someone/project -n 20
    python evsearch.py "关键词 ext:pdf" -s date_modified --desc
    python evsearch.py "ext:log size:>10mb" --files-only -n 50

注意：在 Git Bash 等 MSYS 环境里，命令行参数中的反斜杠会被自动转成正斜杠，
因此路径请写在 --in 里，或在 query 中写相对片段，不要写完整的反斜杠路径。
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_ENDPOINT = "http://127.0.0.1:2869/"
FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
VALID_SORT = ("name", "path", "size", "date_modified", "extension")
SANE_YEAR_MIN = 1990


def parse_args():
    parser = argparse.ArgumentParser(
        description="通过 Everything HTTP 服务器搜索本机文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="Everything 搜索语法")
    parser.add_argument(
        "-i", "--in", dest="in_dir", help="限定目录，斜杠方向不限，脚本内部转换"
    )
    parser.add_argument("-n", "--count", type=int, default=100, help="返回条数上限，默认 100")
    parser.add_argument(
        "-s", "--sort", default="name", choices=VALID_SORT, help="排序字段，默认 name"
    )
    parser.add_argument("--desc", action="store_true", help="降序排列")
    parser.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="HTTP 服务地址")
    parser.add_argument("--timeout", type=float, default=30.0, help="请求超时秒数")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--files-only", action="store_true", help="只保留文件")
    group.add_argument("--folders-only", action="store_true", help="只保留目录")
    return parser.parse_args()


def to_backslash(path):
    return path.replace("/", "\\").rstrip("\\")


def normalize_query(query):
    """把 path: 后面被误转成正斜杠的盘符路径改回反斜杠。"""
    def fix(match):
        head, body = match.group(1), match.group(2)
        stripped = body.strip('"')
        if "/" in stripped and re.match(r"^[A-Za-z]:[/\\]", stripped):
            quote = '"' if body.startswith('"') else ""
            return "{}{}{}{}".format(head, quote, to_backslash(stripped), quote)
        return match.group(0)

    return re.sub(r"(path:\s*)(\S+)", fix, query)


def build_query(args):
    query = normalize_query(args.query or "")
    if args.in_dir:
        clause = 'path:"{}"'.format(to_backslash(args.in_dir))
        query = (query + " " + clause).strip() if query else clause
    return query


def request(endpoint, params, timeout):
    url = endpoint + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.URLError as exc:
        raise SystemExit(
            "无法连接 Everything HTTP 服务：{}\n"
            "请确认 Everything 正在运行，且已在 工具 > 选项 > HTTP 服务器 中启用。".format(exc)
        )


def filetime_to_local(raw):
    if not raw:
        return None
    try:
        ticks = int(raw)
    except ValueError:
        return None
    if ticks <= 0:
        return None
    moment = FILETIME_EPOCH + timedelta(microseconds=ticks / 10)
    if moment.year < SANE_YEAR_MIN:
        return None
    return moment.astimezone()


def human_size(raw):
    if not raw:
        return ""
    try:
        value = float(raw)
    except ValueError:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return "{:.0f} B".format(value)
            return "{:.1f} {}".format(value, unit)
        value /= 1024


def main():
    args = parse_args()
    query = build_query(args)
    if not query:
        raise SystemExit("查询为空。请给出搜索词，或用 --in 指定目录。")

    needs_filter = args.files_only or args.folders_only
    fetch_count = min(args.count * 5, 10000) if needs_filter else args.count

    params = {
        "search": query,
        "json": "1",
        "count": str(fetch_count),
        "path_column": "1",
        "size_column": "1",
        "date_modified_column": "1",
        "sort": args.sort,
        "ascending": "0" if args.desc else "1",
    }
    data = request(args.endpoint, params, args.timeout)

    rows = data.get("results", [])
    if args.files_only:
        rows = [r for r in rows if r.get("type") == "file"]
    elif args.folders_only:
        rows = [r for r in rows if r.get("type") == "folder"]
    rows = rows[: args.count]

    if args.as_json:
        print(json.dumps(
            {"query": query, "totalResults": data.get("totalResults"), "results": rows},
            ensure_ascii=False, indent=2))
        return

    total = data.get("totalResults", 0)
    print("查询: {}".format(query))
    print("命中 {} 条，显示 {} 条".format(total, len(rows)))
    if not rows:
        return
    print()

    for row in rows:
        full_path = row.get("path", "") + "\\" + row.get("name", "")
        moment = filetime_to_local(row.get("date_modified"))
        stamp = moment.strftime("%Y-%m-%d %H:%M") if moment else " " * 16
        size = human_size(row.get("size"))
        kind = "D" if row.get("type") == "folder" else " "
        print("{} {}  {:<9} {}".format(kind, stamp, size, full_path))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
