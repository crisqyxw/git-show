#!/usr/bin/env python3
"""
验证贡献是否符合 CONTRIBUTING.md 的要求。

支持两种运行模式：
  1. 本地模式：在本地仓库直接运行
  2. CI 模式：在 GitHub Actions 中自动获取 PR 上下文

用法：
  # 本地验证当前分支对比 origin/main
  python scripts/validate_contribution.py

  # 指定基准和比较分支
  python scripts/validate_contribution.py --base origin/main --head my-branch

  # GitHub Actions 模式（markdown 输出）
  python scripts/validate_contribution.py --format markdown
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class ValidationResult:
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.comments: List[str] = []

    def ok(self, check: str):
        self.passed.append(check)

    def fail(self, check: str, comment: str = ""):
        self.failed.append(check)
        if comment:
            self.comments.append(comment)

    @property
    def success(self) -> bool:
        return len(self.failed) == 0

    def to_markdown(self) -> str:
        lines = ["## 贡献验证结果\n"]
        if self.passed:
            lines.append("### 通过的检查\n")
            for c in self.passed:
                lines.append(f"- ✅ {c}")
            lines.append("")
        if self.failed:
            lines.append("### 未通过的检查\n")
            for c in self.failed:
                lines.append(f"- ❌ {c}")
            lines.append("")
        if self.comments:
            lines.append("### 修改建议\n")
            for c in self.comments:
                lines.append(f"- {c}")
            lines.append("")
        if self.success:
            lines.append("🎉 **所有检查通过，可以合并！**")
        else:
            lines.append("请根据上述意见修改后重新推送（`git push` 即可自动更新此 PR）。")
        return "\n".join(lines)


def git(args: List[str], cwd: Optional[Path] = None) -> str:
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True,
                           cwd=cwd or Path.cwd())
        return r.stdout.strip()
    except Exception as e:
        print(f"git 命令执行失败: {' '.join(args)}: {e}", file=sys.stderr)
        sys.exit(1)


def check_commits(r: ValidationResult, base: str, head: str, repo: Path):
    log = git(["log", f"{base}..{head}", "--oneline"], cwd=repo)
    count = len([l for l in log.split("\n") if l.strip()])
    if count >= 2:
        r.ok(f"包含至少 2 次提交（当前 {count} 次）")
    else:
        r.fail(f"提交次数不足（当前 {count} 次，需要 ≥2 次）",
               "当前提交次数不足。请在本地继续修改并用 `git commit` 新增一次提交，"
               "然后 `git push` 更新此 PR。")


def check_members_file(r: ValidationResult, base: str, head: str, repo: Path):
    out = git(["diff", f"{base}..{head}", "--name-status"], cwd=repo)
    added = re.findall(r'^A\s+(members/.+\.md)$', out, re.MULTILINE)
    modified = re.findall(r'^M\s+(members/.+\.md)$', out, re.MULTILINE)
    if added:
        for f in added:
            r.ok(f"新增了 members 文件：`{f}`")
    elif modified:
        r.ok(f"修改了 members 文件：`{modified[0]}`")
        r.fail("", "在 `members/` 下新增一个以你的 GitHub 用户名命名的文件，"
                    "例如 `members/alice.md`。直接修改已有文件不符合要求。")
    else:
        r.fail("未检测到 members 文件变更",
               "请在 `members/` 目录下新增一个 Markdown 文件，"
               "例如 `members/你的用户名.md`。")


def check_git_notes(r: ValidationResult, base: str, head: str, repo: Path):
    out = git(["diff", f"{base}..{head}", "--", "docs/git-notes.md"], cwd=repo)
    if out:
        r.ok("已更新 `docs/git-notes.md`")
    else:
        r.fail("未更新 `docs/git-notes.md`",
               "请在 `docs/git-notes.md` 末尾新增一行 `- [你的用户名] 你的收获`。")


def check_members_content(r: ValidationResult, base: str, head: str, repo: Path):
    out = git(["diff", f"{base}..{head}", "--name-only"], cwd=repo)
    members_files = re.findall(r'(members/.+\.md)', out)
    for f in members_files:
        content = git(["show", f"{head}:{f}"], cwd=repo)
        has_name = bool(re.search(r'^#\s+\S', content, re.MULTILINE))
        has_github = bool(re.search(r'github\.com/', content, re.IGNORECASE))
        if not has_name:
            r.fail(f"`{f}` 缺少标题",
                   f"请在 `{f}` 的第一行用 `# 你的姓名` 作为标题。")
        if not has_github:
            r.fail(f"`{f}` 缺少 GitHub 链接",
                   f"建议在 `{f}` 中添加 GitHub 个人主页链接。")


def check_pr_title(r: ValidationResult, title: str):
    if re.match(r'^Add profile:\s+\S+', title):
        r.ok(f"PR 标题格式正确：{title}")
    else:
        r.fail(f"PR 标题格式不正确（当前：{title}）",
               "PR 标题请使用 `Add profile: 你的用户名` 格式，"
               "例如 `Add profile: alice`。")


def check_pr_description(r: ValidationResult, desc: str):
    if desc and len(desc.strip()) > 10:
        r.ok("PR 描述已填写")
    else:
        r.fail("PR 描述未填写或内容过短",
               "请在 PR 描述中说明本次修改内容，方便维护者理解。")


def main():
    parser = argparse.ArgumentParser(description="验证贡献是否符合 CONTRIBUTING.md 要求")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    args = parser.parse_args()

    base = os.environ.get("BASE_REF") or args.base
    head = os.environ.get("HEAD_REF") or args.head
    title = os.environ.get("PR_TITLE", "")
    desc = os.environ.get("PR_DESCRIPTION", "")

    r = ValidationResult()

    check_commits(r, base, head, args.repo)
    check_members_file(r, base, head, args.repo)
    check_git_notes(r, base, head, args.repo)
    check_members_content(r, base, head, args.repo)
    if title:
        check_pr_title(r, title)
    else:
        r.fail("PR 标题未获取到")
    if desc:
        check_pr_description(r, desc)
    else:
        r.fail("PR 描述未获取到")

    if args.format == "json":
        print(json.dumps({
            "success": r.success,
            "passed": r.passed,
            "failed": r.failed,
            "comments": r.comments,
            "markdown": r.to_markdown(),
        }, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(r.to_markdown())
    else:
        print(f"通过 {len(r.passed)} 项，未通过 {len(r.failed)} 项")
        for c in r.passed:
            print(f"  ✅ {c}")
        for c in r.failed:
            print(f"  ❌ {c}")
        if r.comments:
            print("\n修改建议：")
            for c in r.comments:
                print(f"  💬 {c}")

    return 0 if r.success else 1


if __name__ == "__main__":
    sys.exit(main())
