# -*- coding: utf-8 -*-
r"""把 requirements-lib.txt 里的依赖装进包内 lib/（维护者用，不在用户机器上跑）。

    python tools/fetch_lib.py                  # 按当前解释器版本装齐
    python tools/fetch_lib.py --for 3.11 3.13  # 额外给别的版本补齐 [ver] 包
    python tools/fetch_lib.py --list           # 只看分类，不动文件
    python tools/fetch_lib.py --dry-run        # 只让 pip 报告将要装什么

分类规则（见 tools/requirements-lib.txt）：
  * 普通包（PySide6-Essentials / shiboken6 / requests）-> lib/，所有版本共用；
    PySide6 与 shiboken6 是 cp310-abi3 轮子，一份就够 3.10~3.14。
  * 带 [ver] 标记的包（numpy 这类没有 abi3 的）-> lib/pyX.Y/，只有对应版本看得见。
别的版本用 pip 的 --python-version/--only-binary 直接下对应轮子，本机不需要装那个版本。
装完记得把 lib/ 一起提交，用户端就是开箱即用。
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "lib"
MANIFEST = Path(__file__).resolve().parent / "requirements-lib.txt"

_VERSION_MARK = re.compile(r"^\s*\[ver\]\s*")
_ANNOTATION = re.compile(r"#\s*(.*)$")


def read_manifest():
    """返回 (公共包, 版本相关包) 两个 pip 需求列表（去掉注释和 [ver] 标记）。"""
    common, versioned = [], []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = _ANNOTATION.sub("", line).strip()
        if not line:
            continue
        if _VERSION_MARK.match(line):
            versioned.append(_VERSION_MARK.sub("", line).strip())
        else:
            common.append(line)
    return common, versioned


def python_tag(version):
    return "py%s" % ".".join(str(part) for part in version)


def install(packages, target, python_version=None, dry_run=False):
    """把 packages 装进 target 目录，返回是否成功。"""
    if not packages:
        return True
    command = [sys.executable, "-m", "pip", "install",
               "--disable-pip-version-check", "--no-input", "--no-deps",
               "--target", str(target)]
    if dry_run:
        command.append("--dry-run")
    if python_version:
        command += ["--python-version", ".".join(str(p) for p in python_version),
                    "--only-binary=:all:", "--platform", "win_amd64"]
    else:
        target.mkdir(parents=True, exist_ok=True)
    command += list(packages)
    print("$ " + " ".join(command), flush=True)
    return subprocess.call(command) == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="把依赖装进包内 lib/")
    parser.add_argument("--for", dest="versions", nargs="*", default=None, metavar="X.Y",
                        help="额外补齐这些 Python 版本的 [ver] 包（默认只处理当前版本）")
    parser.add_argument("--list", action="store_true", help="只打印分类结果")
    parser.add_argument("--dry-run", action="store_true", help="只让 pip 报告计划")
    args = parser.parse_args(argv)

    common, versioned = read_manifest()
    current = sys.version_info[:2]
    print("依赖清单 : %s" % MANIFEST)
    print("公共依赖 : %s  ->  %s" % (", ".join(common) or "无", LIB))
    print("版本依赖 : %s  ->  lib/%s/" % (", ".join(versioned) or "无", python_tag(current)))
    if args.list:
        return 0

    ok = install(common, LIB, dry_run=args.dry_run)
    ok = install(versioned, LIB / python_tag(current), dry_run=args.dry_run) and ok

    targets = []
    for item in args.versions or []:
        try:
            version = tuple(int(part) for part in item.split(".")[:2])
        except ValueError:
            print("跳过无法解析的版本：%s" % item)
            continue
        if version == current:
            continue
        # 别的版本不能沿用固定版本号：去掉 == 让 pip 挑该版本可用的轮子
        unpinned = [spec.split("==")[0] for spec in versioned]
        targets.append(version)
        ok = install(unpinned, LIB / python_tag(version),
                     python_version=version, dry_run=args.dry_run) and ok

    print()
    print("完成" if ok else "有失败项，请检查上面的 pip 输出")
    if not args.dry_run:
        print("记得把 lib/ 一起提交，用户端才能开箱即用。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
