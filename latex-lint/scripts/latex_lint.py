#!/usr/bin/env python3
"""
latex_lint.py — LaTeX 学术写作规范自动检查器

基于「打字抄能力」系列提炼的规范，自动扫描 .tex / .bib 文件中的常见问题。

用法:
    python3 latex_lint.py <file-or-directory> [--bib] [--fix-preview] [--json] [--severity ERROR|WARN|INFO]

示例:
    python3 latex_lint.py paper.tex
    python3 latex_lint.py ./my-paper/ --bib
    python3 latex_lint.py paper.tex --fix-preview --json
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from pathlib import Path
from typing import Optional


class Severity(IntEnum):
    ERROR = 0
    WARN = 1
    INFO = 2

    def __str__(self):
        return self.name


@dataclass
class Issue:
    severity: Severity
    file: str
    line: int
    rule: str
    message: str
    fix: Optional[str] = None
    context: Optional[str] = None  # the offending line content

    def to_dict(self):
        d = asdict(self)
        d["severity"] = str(self.severity)
        return d

    def display(self, fix_preview: bool = False) -> str:
        sev = f"[{self.severity!s:5s}]"
        loc = f"{self.file}:{self.line}"
        parts = [f"{sev} {loc} — {self.message}"]
        if self.context:
            parts.append(f"  | {self.context.rstrip()}")
        if fix_preview and self.fix:
            parts.append(f"  → 修复: {self.fix}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

def check_label_naming(lines: list[str], filepath: str) -> list[Issue]:
    """Check label naming conventions."""
    issues = []
    valid_prefixes = {
        "thm", "lem", "cor", "def", "fac", "sec", "eq", "fig",
        "tab", "alg", "app", "rem", "prop", "ass", "cla",
    }
    # Also allow informal/formal suffixed versions
    label_pat = re.compile(r"\\label\{([^}]+)\}")

    for i, line in enumerate(lines, 1):
        for m in label_pat.finditer(line):
            label = m.group(1)

            # Check prefix format
            if ":" not in label:
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-prefix",
                    f"label 缺少前缀（应为 prefix:name 格式）: \\label{{{label}}}",
                    fix=f"添加合适的前缀，如 eq:{label} 或 lem:{label}",
                    context=line,
                ))
                continue

            prefix = label.split(":")[0]
            name_part = label.split(":", 1)[1]

            # Remove informal/formal suffix for prefix check
            clean_prefix = prefix
            if clean_prefix not in valid_prefixes:
                issues.append(Issue(
                    Severity.WARN, filepath, i, "label-prefix",
                    f"label 前缀 '{prefix}' 不在常用前缀列表中: \\label{{{label}}}",
                    fix=f"常用前缀: {', '.join(sorted(valid_prefixes))}",
                    context=line,
                ))

            # Check for hyphens in label name
            if "-" in name_part:
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-hyphen",
                    f"label 使用了减号（应用下划线分隔）: \\label{{{label}}}",
                    fix=f"\\label{{{label.replace('-', '_')}}}",
                    context=line,
                ))

            # Check for uppercase in label
            if name_part != name_part.lower():
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-case",
                    f"label 名应全小写: \\label{{{label}}}",
                    fix=f"\\label{{{prefix}:{name_part.lower()}}}",
                    context=line,
                ))

            # Check for spaces (shouldn't compile, but just in case)
            if " " in label:
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-space",
                    f"label 中不应有空格: \\label{{{label}}}",
                    fix=f"\\label{{{label.replace(' ', '_')}}}",
                    context=line,
                ))
    return issues


def check_label_order(lines: list[str], filepath: str) -> list[Issue]:
    """Check that \\label comes after [display name], not before."""
    issues = []
    # Pattern: \begin{env}\label{...}[name] — label before display name
    pat = re.compile(r"\\begin\{(\w+\*?)\}\s*\\label\{[^}]+\}\s*\[")
    for i, line in enumerate(lines, 1):
        if pat.search(line):
            issues.append(Issue(
                Severity.ERROR, filepath, i, "label-order",
                "\\label 应在 [display name] 之后，而非之前——交换顺序可能产生 bug",
                fix="\\begin{env}[Display Name]\\label{prefix:name}",
                context=line,
            ))
    return issues


def check_label_in_star(lines: list[str], filepath: str) -> list[Issue]:
    """Check for \\label inside star environments."""
    issues = []
    in_star_env = False
    star_env_name = ""

    for i, line in enumerate(lines, 1):
        # Track star environments
        begin_star = re.search(r"\\begin\{(\w+)\*\}", line)
        end_star = re.search(r"\\end\{(\w+)\*\}", line)

        if begin_star:
            in_star_env = True
            star_env_name = begin_star.group(1)
        if end_star:
            in_star_env = False

        if in_star_env and re.search(r"\\label\{", line):
            issues.append(Issue(
                Severity.ERROR, filepath, i, "label-in-star",
                f"在 {star_env_name}* 环境中使用了 \\label（star 环境无编号，label 无效）",
                fix=f"移除 \\label 或改用非 star 环境 {star_env_name}",
                context=line,
            ))
    return issues


def check_equation_ref(lines: list[str], filepath: str) -> list[Issue]:
    """Check equation reference format."""
    issues = []
    # Pattern: using \ref{eq:...} instead of \eqref{eq:...}
    ref_eq_pat = re.compile(r"\\ref\{eq[:\s_]")

    for i, line in enumerate(lines, 1):
        for m in ref_eq_pat.finditer(line):
            issues.append(Issue(
                Severity.WARN, filepath, i, "eq-ref-format",
                "equation 引用应使用 \\eqref 而非 \\ref（\\eqref 自带括号）",
                fix="将 \\ref{eq:...} 改为 Eq.~\\eqref{eq:...}",
                context=line,
            ))

        # Check for "Equation" spelled out before \eqref
        if re.search(r"(?i)\bequation\b\s*[~\\]*(\\eqref|\\ref)", line):
            issues.append(Issue(
                Severity.INFO, filepath, i, "eq-ref-abbrev",
                "引用 equation 时建议缩写为 Eq. 而非完整拼写 Equation",
                fix="Eq.~\\eqref{eq:xxx}",
                context=line,
            ))

        # Check for missing tilde before \ref or \eqref
        ref_no_tilde = re.compile(r"(?<![~])(\\eqref\{|\\ref\{)")
        for m2 in ref_no_tilde.finditer(line):
            # Check if there's a word/abbreviation right before
            pos = m2.start()
            before = line[:pos].rstrip()
            if before and before[-1].isalpha() or (before and before[-1] == "."):
                issues.append(Issue(
                    Severity.INFO, filepath, i, "ref-tilde",
                    "引用前建议使用 ~ 产生不换行空格",
                    fix="Lemma~\\ref{...} 或 Eq.~\\eqref{...}",
                    context=line,
                ))
                break  # one per line is enough
    return issues


def check_nonumber_vs_notag(lines: list[str], filepath: str) -> list[Issue]:
    """Prefer \\notag over \\nonumber."""
    issues = []
    for i, line in enumerate(lines, 1):
        if "\\nonumber" in line:
            issues.append(Issue(
                Severity.INFO, filepath, i, "nonumber-notag",
                "建议使用 \\notag 代替 \\nonumber（二者等价，统一用 \\notag）",
                fix="将 \\nonumber 替换为 \\notag",
                context=line,
            ))
    return issues


def check_bracket_sizing(lines: list[str], filepath: str) -> list[Issue]:
    """Detect manual bracket sizing commands."""
    issues = []
    sizing_cmds = re.compile(r"\\(big|Big|bigg|Bigg)[lr]?\b")

    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.split("%")[0] if "%" in line else line
        for m in sizing_cmds.finditer(stripped):
            issues.append(Issue(
                Severity.WARN, filepath, i, "bracket-sizing",
                f"检测到手动括号大小调整 \\{m.group(0)}——建议保持默认大小",
                fix="移除 sizing 命令，使用默认括号大小",
                context=line,
            ))


    # Also check excessive \left/\right
    left_right_pat = re.compile(r"\\left[([{|.]|\\right[)\]}|.]")
    for i, line in enumerate(lines, 1):
        stripped = line.split("%")[0] if "%" in line else line
        count = len(left_right_pat.findall(stripped))
        if count >= 4:  # Multiple pairs on one line
            issues.append(Issue(
                Severity.INFO, filepath, i, "left-right-overuse",
                f"单行中有 {count // 2}+ 对 \\left/\\right——确认是否都必要",
                context=line,
            ))
    return issues


def check_definition_symbol(lines: list[str], filepath: str) -> list[Issue]:
    """Check that definitions use := not \\triangleq or bare =."""
    issues = []
    triangleq_pat = re.compile(r"\\triangleq")

    for i, line in enumerate(lines, 1):
        for m in triangleq_pat.finditer(line):
            issues.append(Issue(
                Severity.WARN, filepath, i, "define-coloneq",
                "定义符号建议用 := 而非 \\triangleq",
                fix="将 \\triangleq 替换为 :=（或 \\coloneqq）",
                context=line,
            ))
    return issues


def check_log_power(lines: list[str], filepath: str) -> list[Issue]:
    """Detect powers inside \\log."""
    issues = []
    # Match \log(x^n) or \log x^n patterns
    log_power_pat = re.compile(r"\\log\s*[\({]\s*[^)\}]*\^[^)\}]*[\)}]")

    for i, line in enumerate(lines, 1):
        for m in log_power_pat.finditer(line):
            issues.append(Issue(
                Severity.WARN, filepath, i, "log-power",
                f"\\log 内部包含幂次——应提取到外部: log(a^d) → d·log(a)",
                fix="将 \\log(x^n) 改为 n \\log(x)",
                context=line,
            ))
    return issues


def check_eq_label_prefix(lines: list[str], filepath: str) -> list[Issue]:
    """Check that equation labels use 'eq:' not 'equation:'."""
    issues = []
    for i, line in enumerate(lines, 1):
        if re.search(r"\\label\{equation:", line):
            issues.append(Issue(
                Severity.ERROR, filepath, i, "eq-label-long",
                "equation label 前缀应用 eq: 而非 equation:",
                fix="将 \\label{equation:xxx} 改为 \\label{eq:xxx}",
                context=line,
            ))
    return issues


def check_proof_line_breaks(lines: list[str], filepath: str) -> list[Issue]:
    """Check that proofs have adequate line breaks between steps."""
    issues = []
    in_proof = False
    consecutive_nonempty = 0
    proof_start_line = 0

    for i, line in enumerate(lines, 1):
        if re.search(r"\\begin\{proof\}", line):
            in_proof = True
            consecutive_nonempty = 0
            proof_start_line = i
            continue
        if re.search(r"\\end\{proof\}", line):
            if in_proof and consecutive_nonempty > 20:
                issues.append(Issue(
                    Severity.WARN, filepath, proof_start_line, "proof-linebreak",
                    f"Proof（第 {proof_start_line}-{i} 行）有 {consecutive_nonempty} 行连续非空——建议在推导步骤间添加空行提高可读性",
                ))
            in_proof = False
            consecutive_nonempty = 0
            continue

        if in_proof:
            if line.strip():
                consecutive_nonempty += 1
            else:
                consecutive_nonempty = 0
    return issues


def check_roadmap(lines: list[str], filepath: str) -> list[Issue]:
    """Check for presence of roadmap in main body and appendix."""
    issues = []
    content = "\n".join(lines)

    has_appendix = bool(re.search(r"\\appendix|\\begin\{appendix\}", content))
    has_roadmap_main = bool(re.search(
        r"\\paragraph\{[Rr]oadmap|\\paragraph\{[Oo]utline|\\paragraph\{[Oo]rganization|"
        r"\\textbf\{[Rr]oadmap|\\textbf\{[Oo]utline|\\textbf\{[Oo]rganization|"
        r"[Rr]oadmap\.|[Oo]rganization\.|[Oo]utline\.",
        content
    ))

    # Only warn if there are multiple sections (suggesting a full paper)
    section_count = len(re.findall(r"\\section\{", content))
    if section_count >= 3 and not has_roadmap_main:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "roadmap-main",
            "论文有 3+ 个 section 但未检测到 roadmap 段落",
            fix="在 intro 末尾或 related work 后添加 \\paragraph{Roadmap.}",
        ))

    if has_appendix:
        # Check for roadmap in appendix
        appendix_start = None
        for i, line in enumerate(lines, 1):
            if re.search(r"\\appendix|\\begin\{appendix\}", line):
                appendix_start = i
                break
        if appendix_start:
            appendix_content = "\n".join(lines[appendix_start:appendix_start + 30])
            if not re.search(r"[Rr]oadmap|[Oo]utline|[Oo]rganization", appendix_content):
                issues.append(Issue(
                    Severity.INFO, filepath, appendix_start, "roadmap-appendix",
                    "Appendix 开头未检测到 roadmap",
                    fix="在 appendix 开头添加 \\paragraph{Roadmap.} 概述各 section",
                ))
    return issues


def check_informal_formal_labels(lines: list[str], filepath: str) -> list[Issue]:
    """Check consistency of informal/formal label suffixes."""
    issues = []
    has_informal = False
    has_formal = False
    has_appendix = False

    for line in lines:
        if re.search(r":informal\b", line):
            has_informal = True
        if re.search(r":formal\b", line):
            has_formal = True
        if re.search(r"\\appendix|\\begin\{appendix\}", line):
            has_appendix = True

    if has_appendix and has_informal and not has_formal:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "informal-formal",
            "检测到 :informal label 但无 :formal label——如果 appendix 有对应 theorem，应添加 :formal 版本",
        ))
    if has_formal and not has_informal:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "informal-formal",
            "检测到 :formal label 但无 :informal label——如果 main body 有对应 theorem，应添加 :informal 版本",
        ))
    return issues


# ---------------------------------------------------------------------------
# BibTeX checks
# ---------------------------------------------------------------------------

def check_bibtex(filepath: str) -> list[Issue]:
    """Check BibTeX file for naming conventions."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        issues.append(Issue(Severity.ERROR, filepath, 0, "bib-read", f"无法读取文件: {e}"))
        return issues

    entry_pat = re.compile(r"@\w+\{([^,]+),", re.MULTILINE)
    for m in entry_pat.finditer(content):
        key = m.group(1).strip()
        line = content[:m.start()].count("\n") + 1

        # Check for capitalized key (likely first name or CamelCase)
        if key[0].isupper() and not re.match(r"^[A-Z]+\d{4}", key):
            # Could be CamelCase like "HeZhang2016"
            if re.match(r"[A-Z][a-z]+[A-Z]", key):
                issues.append(Issue(
                    Severity.WARN, filepath, line, "bib-key-case",
                    f"BibTeX key '{key}' 看起来是 CamelCase——应使用全小写 lastname+year 格式",
                    fix=f"改为如 {key.lower()[:key.index(next(c for c in key[1:] if c.isupper()), len(key))].lower()}" if any(c.isupper() for c in key[1:]) else None,
                    context=m.group(0),
                ))

        # Check for year in key
        if not re.search(r"\d{4}", key):
            issues.append(Issue(
                Severity.INFO, filepath, line, "bib-key-year",
                f"BibTeX key '{key}' 中未包含年份——建议使用 lastname+year 格式",
                context=m.group(0),
            ))

        # Check for very long keys that might include first names
        parts = re.findall(r"[a-zA-Z]+", key)
        if len(parts) >= 3 and not any(c.isdigit() for c in key):
            issues.append(Issue(
                Severity.INFO, filepath, line, "bib-key-long",
                f"BibTeX key '{key}' 较长——建议简化为 lastname+year 格式",
                context=m.group(0),
            ))
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

ALL_TEX_CHECKS = [
    check_label_naming,
    check_label_order,
    check_label_in_star,
    check_equation_ref,
    check_nonumber_vs_notag,
    check_bracket_sizing,
    check_definition_symbol,
    check_log_power,
    check_eq_label_prefix,
    check_proof_line_breaks,
    check_roadmap,
    check_informal_formal_labels,
]


def lint_tex_file(filepath: str) -> list[Issue]:
    """Run all TeX checks on a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return [Issue(Severity.ERROR, filepath, 0, "read-error", f"无法读取文件: {e}")]

    issues = []
    for check in ALL_TEX_CHECKS:
        issues.extend(check(lines, filepath))
    return issues


def collect_files(path: str, include_bib: bool) -> tuple[list[str], list[str]]:
    """Collect .tex and optionally .bib files from path."""
    tex_files = []
    bib_files = []
    p = Path(path)

    if p.is_file():
        if p.suffix == ".tex":
            tex_files.append(str(p))
        elif p.suffix == ".bib":
            bib_files.append(str(p))
    elif p.is_dir():
        for f in sorted(p.rglob("*.tex")):
            tex_files.append(str(f))
        if include_bib:
            for f in sorted(p.rglob("*.bib")):
                bib_files.append(str(f))
    return tex_files, bib_files


def main():
    parser = argparse.ArgumentParser(
        description="LaTeX 学术写作规范自动检查器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("path", help="要检查的 .tex/.bib 文件或目录")
    parser.add_argument("--bib", action="store_true", help="同时检查 .bib 文件")
    parser.add_argument("--fix-preview", action="store_true", help="显示修复建议")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument(
        "--severity", choices=["ERROR", "WARN", "INFO"], default="INFO",
        help="最低显示的严重级别（默认 INFO，即显示所有）",
    )
    args = parser.parse_args()

    min_sev = Severity[args.severity]
    tex_files, bib_files = collect_files(args.path, args.bib)

    if not tex_files and not bib_files:
        print(f"未找到 .tex 文件: {args.path}", file=sys.stderr)
        sys.exit(1)

    all_issues: list[Issue] = []
    for tf in tex_files:
        all_issues.extend(lint_tex_file(tf))
    for bf in bib_files:
        all_issues.extend(check_bibtex(bf))

    # Filter by severity
    all_issues = [iss for iss in all_issues if iss.severity <= min_sev]

    # Sort: ERROR first, then WARN, then INFO; within same level by file:line
    all_issues.sort(key=lambda x: (x.severity, x.file, x.line))

    if args.json:
        print(json.dumps([iss.to_dict() for iss in all_issues], ensure_ascii=False, indent=2))
    else:
        if not all_issues:
            print("✅ 未检测到问题。")
        else:
            counts = {s: 0 for s in Severity}
            for iss in all_issues:
                counts[iss.severity] += 1
            summary_parts = []
            for s in Severity:
                if counts[s]:
                    summary_parts.append(f"{counts[s]} {s!s}")
            print(f"共检测到 {len(all_issues)} 个问题（{', '.join(summary_parts)}）\n")

            for iss in all_issues:
                print(iss.display(fix_preview=args.fix_preview))
                print()

    # Exit code: 1 if any ERROR, 0 otherwise
    has_error = any(iss.severity == Severity.ERROR for iss in all_issues)
    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()
