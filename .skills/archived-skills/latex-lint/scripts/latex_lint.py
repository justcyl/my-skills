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
    context: Optional[str] = None

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


def _strip_comments(line: str) -> str:
    """Strip LaTeX comments (naive: first unescaped %)."""
    result = []
    i = 0
    while i < len(line):
        if line[i] == '%' and (i == 0 or line[i-1] != '\\'):
            break
        result.append(line[i])
        i += 1
    return ''.join(result)


# ===================================================================
# LABEL CHECKS
# ===================================================================

def check_label_naming(lines: list[str], filepath: str) -> list[Issue]:
    """Check label naming conventions."""
    issues = []
    valid_prefixes = {
        "thm", "lem", "cor", "def", "fac", "sec", "eq", "fig",
        "tab", "alg", "app", "rem", "prop", "ass", "cla", "clm",
    }
    label_pat = re.compile(r"\\label\{([^}]+)\}")

    for i, line in enumerate(lines, 1):
        for m in label_pat.finditer(line):
            label = m.group(1)

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

            if prefix.lower() not in valid_prefixes:
                issues.append(Issue(
                    Severity.WARN, filepath, i, "label-prefix",
                    f"label 前缀 '{prefix}' 不在常用列表中: \\label{{{label}}}",
                    fix=f"常用前缀: {', '.join(sorted(valid_prefixes))}",
                    context=line,
                ))

            if "-" in name_part:
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-hyphen",
                    f"label 使用了减号（应用下划线）: \\label{{{label}}}",
                    fix=f"\\label{{{label.replace('-', '_')}}}",
                    context=line,
                ))

            if name_part != name_part.lower():
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-case",
                    f"label 名应全小写: \\label{{{label}}}",
                    fix=f"\\label{{{prefix}:{name_part.lower()}}}",
                    context=line,
                ))

            if " " in label:
                issues.append(Issue(
                    Severity.ERROR, filepath, i, "label-space",
                    f"label 中不应有空格: \\label{{{label}}}",
                    fix=f"\\label{{{label.replace(' ', '_')}}}",
                    context=line,
                ))

            # Detect meaningless numeric-only labels like eq:1, lem:2
            if re.match(r"^\d+$", name_part):
                issues.append(Issue(
                    Severity.WARN, filepath, i, "label-semantic",
                    f"label 名仅为数字，缺少语义: \\label{{{label}}} — 用英文单词概括内容",
                    fix=f"如 \\label{{{prefix}:privacy_loss}} 或 \\label{{{prefix}:main_bound}}",
                    context=line,
                ))
    return issues


def check_label_order(lines: list[str], filepath: str) -> list[Issue]:
    """Check that \\label comes after [display name], not before."""
    issues = []
    pat = re.compile(r"\\begin\{(\w+\*?)\}\s*\\label\{[^}]+\}\s*\[")
    for i, line in enumerate(lines, 1):
        if pat.search(line):
            issues.append(Issue(
                Severity.ERROR, filepath, i, "label-order",
                "\\label 应在 [display name] 之后——交换顺序可能产生 bug",
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


def check_eq_label_prefix(lines: list[str], filepath: str) -> list[Issue]:
    """Check that equation labels use 'eq:' not 'equation:'."""
    issues = []
    for i, line in enumerate(lines, 1):
        if re.search(r"\\label\{equation:", line):
            issues.append(Issue(
                Severity.ERROR, filepath, i, "eq-label-long",
                "equation label 前缀应用 eq: 而非 equation:",
                fix="\\label{eq:xxx}",
                context=line,
            ))
    return issues


def check_informal_formal_labels(lines: list[str], filepath: str) -> list[Issue]:
    """Check consistency of informal/formal label suffixes."""
    issues = []
    has_informal = any(re.search(r"_informal\b", l) for l in lines)
    has_formal = any(re.search(r"_formal\b", l) for l in lines)
    has_appendix = any(re.search(r"\\appendix|\\begin\{appendix\}", l) for l in lines)

    if has_appendix and has_informal and not has_formal:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "informal-formal",
            "检测到 _informal label 但无 _formal — 如果 appendix 有对应 theorem，应添加 _formal 版本",
        ))
    if has_formal and not has_informal:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "informal-formal",
            "检测到 _formal label 但无 _informal — 如果 main body 有对应 theorem，应添加 _informal 版本",
        ))
    return issues


# ===================================================================
# REFERENCE / CITATION CHECKS
# ===================================================================

def check_equation_ref(lines: list[str], filepath: str) -> list[Issue]:
    """Check equation reference format."""
    issues = []

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)

        # \ref{eq:...} should be \eqref{eq:...}
        if re.search(r"\\ref\{eq[:\s_]", stripped):
            issues.append(Issue(
                Severity.WARN, filepath, i, "eq-ref-format",
                "equation 引用应使用 \\eqref 而非 \\ref（\\eqref 自带括号）",
                fix="Eq.~\\eqref{eq:...}",
                context=line,
            ))

        # Spelled-out "Equation" before ref
        if re.search(r"(?i)\bequation\b\s*[~\\]*(\\eqref|\\ref)", stripped):
            issues.append(Issue(
                Severity.INFO, filepath, i, "eq-ref-abbrev",
                "建议缩写为 Eq. 而非完整拼写 Equation",
                fix="Eq.~\\eqref{eq:xxx}",
                context=line,
            ))

        # Missing ~ before \ref or \eqref (word or abbreviation right before)
        for m in re.finditer(r"([A-Za-z.])\s+(\\(?:eq)?ref\{)", stripped):
            issues.append(Issue(
                Severity.INFO, filepath, i, "ref-tilde",
                "引用前建议使用 ~ 产生不换行空格",
                fix="Lemma~\\ref{...} 或 Eq.~\\eqref{...}",
                context=line,
            ))
            break  # one per line
    return issues


def check_nonumber_vs_notag(lines: list[str], filepath: str) -> list[Issue]:
    """Prefer \\notag over \\nonumber."""
    issues = []
    for i, line in enumerate(lines, 1):
        if "\\nonumber" in _strip_comments(line):
            issues.append(Issue(
                Severity.INFO, filepath, i, "nonumber-notag",
                "建议使用 \\notag 代替 \\nonumber（统一规范）",
                fix="\\notag",
                context=line,
            ))
    return issues


# ===================================================================
# BRACKET / FRACTION CHECKS
# ===================================================================

def check_bracket_sizing(lines: list[str], filepath: str) -> list[Issue]:
    """Detect manual bracket sizing commands."""
    issues = []
    sizing_pat = re.compile(r"\\(big|Big|bigg|Bigg)[lr]?\b")
    seen_lines = set()

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        for m in sizing_pat.finditer(stripped):
            if i not in seen_lines:
                issues.append(Issue(
                    Severity.WARN, filepath, i, "bracket-sizing",
                    f"手动括号大小调整 \\{m.group(0)} — 初学者保持默认大小，留给 advisor 调整",
                    fix="移除 sizing 命令",
                    context=line,
                ))
                seen_lines.add(i)

    # Excessive \left/\right pairs on single line
    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        left_count = len(re.findall(r"\\left[(\[{|.\\]", stripped))
        if left_count >= 3:
            issues.append(Issue(
                Severity.INFO, filepath, i, "left-right-overuse",
                f"单行中有 {left_count}+ 个 \\left/\\right — 确认是否都必要",
                context=line,
            ))
    return issues


# ===================================================================
# MATH SYMBOL CHECKS
# ===================================================================

def check_definition_symbol(lines: list[str], filepath: str) -> list[Issue]:
    """Check that definitions use := not \\triangleq."""
    issues = []
    for i, line in enumerate(lines, 1):
        if "\\triangleq" in _strip_comments(line):
            issues.append(Issue(
                Severity.WARN, filepath, i, "define-coloneq",
                "定义符号建议用 := 而非 \\triangleq",
                fix=":= 或 \\coloneqq",
                context=line,
            ))
    return issues


def check_transpose(lines: list[str], filepath: str) -> list[Issue]:
    """Check that transpose uses \\top, not bare ^T."""
    issues = []
    # Match ^T or ^{T} where T is transpose (not followed by more letters)
    # This won't match ^\top because \top starts with backslash
    pat = re.compile(r"\^(?:\{T\}|T(?![a-zA-Z]))")

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        if not stripped.strip():
            continue
        # Skip lines that are pure text (no $ or math env)
        if '$' not in stripped and '\\[' not in stripped and '&' not in stripped:
            continue
        if pat.search(stripped) and '\\top' not in stripped:
            issues.append(Issue(
                Severity.WARN, filepath, i, "transpose-top",
                "transpose 建议用 ^\\top 而非 ^T — T 常表示 iteration horizon，容易冲突",
                fix="将 ^T 或 ^{T} 改为 ^\\top 或 ^{\\top}",
                context=line,
            ))
    return issues


def check_norm_bars(lines: list[str], filepath: str) -> list[Issue]:
    """Check that norms use \\| not keyboard ||."""
    issues = []
    # Match || that is likely a norm (not \| and not ||= etc)
    # We look for || followed by content then ||
    pat = re.compile(r"(?<!\\)\|\|")

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        matches = list(pat.finditer(stripped))
        if len(matches) >= 2:  # Need at least open and close
            issues.append(Issue(
                Severity.WARN, filepath, i, "norm-bars",
                "norm 应使用 \\|x\\| 而非键盘 ||x|| — 后者间距不正确",
                fix="将 ||x|| 改为 \\|x\\|",
                context=line,
            ))
    return issues


def check_log_power(lines: list[str], filepath: str) -> list[Issue]:
    """Detect powers inside \\log."""
    issues = []
    pat = re.compile(r"\\log\s*[\({]\s*[^)\}]*\^[^)\}]*[\)}]")
    for i, line in enumerate(lines, 1):
        if pat.search(_strip_comments(line)):
            issues.append(Issue(
                Severity.WARN, filepath, i, "log-power",
                "\\log 内部包含幂次 — 应提取: log(a^d) → d·log(a)",
                fix="n \\log(x)",
                context=line,
            ))
    return issues


def check_big_o_constant(lines: list[str], filepath: str) -> list[Issue]:
    """Detect explicit constants inside O(...)."""
    issues = []
    # Match O(NUMBER * ...) or O(NUMBER ...) where NUMBER is like 2, 16, 100
    pat = re.compile(r"[OΘΩ]\s*\(\s*\d{2,}\s*[a-zA-Z\\]")

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        if pat.search(stripped):
            issues.append(Issue(
                Severity.WARN, filepath, i, "big-o-constant",
                "big-O 内部有显式常数 — O() 已隐藏常数，不应同时出现 O(16d...)",
                fix="移除常数或改为精确 bound",
                context=line,
            ))
    return issues


# ===================================================================
# PROOF CHECKS
# ===================================================================

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
                    f"Proof（第 {proof_start_line}-{i} 行）有 {consecutive_nonempty} 行连续非空 — 在步骤间添加空行",
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


def check_vague_reasons(lines: list[str], filepath: str) -> list[Issue]:
    """Detect vague proof reasons like 'clearly', 'obviously'."""
    issues = []
    vague_words = re.compile(
        r"\b(clearly|obviously|trivially|it is easy to see|it is straightforward)\b",
        re.IGNORECASE,
    )
    in_proof = False

    for i, line in enumerate(lines, 1):
        if re.search(r"\\begin\{proof\}", line):
            in_proof = True
        if re.search(r"\\end\{proof\}", line):
            in_proof = False
        if in_proof:
            stripped = _strip_comments(line)
            m = vague_words.search(stripped)
            if m:
                issues.append(Issue(
                    Severity.INFO, filepath, i, "vague-reason",
                    f"Proof 中使用了 \"{m.group(0)}\" — 如果这一步对读者并不 clear，应给出真实原因",
                    fix="替换为具体原因: by Lemma~\\ref{...}, by Jensen's inequality 等",
                    context=line,
                ))
    return issues


def check_defensive_probability(lines: list[str], filepath: str) -> list[Issue]:
    """Detect non-round probability denominators that may be hard to maintain."""
    issues = []
    # Match \delta/3, \delta/4, \delta/7 etc (not /10, /100, /2)
    # We flag denominators that aren't powers of 10 or 2
    pat = re.compile(r"\\delta\s*/\s*(\d+)")
    ok_denoms = {2, 10, 20, 100, 1000}

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        for m in pat.finditer(stripped):
            denom = int(m.group(1))
            if denom not in ok_denoms and denom > 2:
                issues.append(Issue(
                    Severity.INFO, filepath, i, "defensive-prob",
                    f"δ/{denom} — 防御性写证明建议用十进制分母（δ/10）留余地",
                    fix=f"改为 δ/10 或 δ/100，避免增加 event 时全文改动",
                    context=line,
                ))
    return issues


# ===================================================================
# ROADMAP CHECKS
# ===================================================================

def check_roadmap(lines: list[str], filepath: str) -> list[Issue]:
    """Check for presence of roadmap in main body and appendix."""
    issues = []
    content = "\n".join(lines)

    has_appendix = bool(re.search(r"\\appendix|\\begin\{appendix\}", content))
    roadmap_pat = (
        r"\\paragraph\{[Rr]oadmap|\\paragraph\{[Oo]utline|\\paragraph\{[Oo]rganization|"
        r"\\textbf\{[Rr]oadmap|\\textbf\{[Oo]utline|\\textbf\{[Oo]rganization|"
        r"organized as follows|structure of the paper|structure of this paper|"
        r"[Rr]oadmap\.|[Oo]rganization\.|[Oo]utline\."
    )
    has_roadmap_main = bool(re.search(roadmap_pat, content))

    section_count = len(re.findall(r"\\section\{", content))
    if section_count >= 3 and not has_roadmap_main:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "roadmap-main",
            "论文有 3+ 个 section 但未检测到 roadmap",
            fix="在 intro 末尾添加 \\paragraph{Roadmap.}",
        ))

    if has_appendix:
        appendix_start = None
        for i, line in enumerate(lines, 1):
            if re.search(r"\\appendix|\\begin\{appendix\}", line):
                appendix_start = i
                break
        if appendix_start:
            appendix_head = "\n".join(lines[appendix_start:appendix_start + 40])
            if not re.search(roadmap_pat, appendix_head):
                issues.append(Issue(
                    Severity.INFO, filepath, appendix_start, "roadmap-appendix",
                    "Appendix 开头未检测到 roadmap",
                    fix="在 appendix 开头添加 \\paragraph{Roadmap.}",
                ))
    return issues


# ===================================================================
# MACRO / CONSISTENCY CHECKS
# ===================================================================

def check_probability_expectation(lines: list[str], filepath: str) -> list[Issue]:
    """Check that probability/expectation notation is consistent."""
    issues = []
    # Detect mix of different expectation notations
    uses_E_macro = False
    uses_mathbb_E = False
    uses_bare_E = False

    for i, line in enumerate(lines, 1):
        stripped = _strip_comments(line)
        if re.search(r"\\E\b(?!\w)", stripped):
            uses_E_macro = True
        if re.search(r"\\mathbb\{E\}", stripped):
            uses_mathbb_E = True
        # bare E as expectation (heuristic: E[ or E_{)
        if re.search(r"(?<!\\)(?<!\w)E\s*[\[_{]", stripped):
            uses_bare_E = True

    style_count = sum([uses_E_macro, uses_mathbb_E, uses_bare_E])
    if style_count > 1:
        issues.append(Issue(
            Severity.WARN, filepath, 1, "expectation-inconsistent",
            "期望符号不统一 — 检测到多种写法混用（\\E / \\mathbb{E} / bare E）",
            fix="全文统一使用项目 macro，如 \\E 或 \\mathbb{E}",
        ))
    return issues


def check_set_separator_consistency(lines: list[str], filepath: str) -> list[Issue]:
    """Check that set builder notation uses consistent separator."""
    issues = []
    uses_colon = False
    uses_mid = False

    for line in lines:
        stripped = _strip_comments(line)
        # \{ ... : ... \} pattern
        if re.search(r"\\{[^}]*[^:]:[^:][^}]*\\}", stripped):
            uses_colon = True
        if re.search(r"\\mid\b", stripped):
            uses_mid = True

    if uses_colon and uses_mid:
        issues.append(Issue(
            Severity.INFO, filepath, 1, "set-separator",
            "集合条件分隔符不统一 — 同时使用了 : 和 \\mid",
            fix="全文统一用一种：\\{x \\in X : P(x)\\} 或 \\{x \\in X \\mid P(x)\\}",
        ))
    return issues


# ===================================================================
# BIBTEX CHECKS
# ===================================================================

def check_bibtex(filepath: str) -> list[Issue]:
    """Check BibTeX file for naming conventions."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        issues.append(Issue(Severity.ERROR, filepath, 0, "bib-read", f"无法读取: {e}"))
        return issues

    entry_pat = re.compile(r"@\w+\{([^,]+),", re.MULTILINE)
    seen_keys = {}

    for m in entry_pat.finditer(content):
        key = m.group(1).strip()
        line = content[:m.start()].count("\n") + 1

        # Duplicate key check
        if key in seen_keys:
            issues.append(Issue(
                Severity.ERROR, filepath, line, "bib-key-dup",
                f"重复 BibTeX key '{key}'（首次出现在第 {seen_keys[key]} 行）",
                context=m.group(0),
            ))
        seen_keys[key] = line

        # CamelCase check
        if re.match(r"[A-Z][a-z]+[A-Z]", key):
            issues.append(Issue(
                Severity.WARN, filepath, line, "bib-key-case",
                f"BibTeX key '{key}' 是 CamelCase — 应使用全小写 lastname+year",
                context=m.group(0),
            ))

        # Missing year
        if not re.search(r"\d{4}", key):
            issues.append(Issue(
                Severity.INFO, filepath, line, "bib-key-year",
                f"BibTeX key '{key}' 中未包含年份 — 建议 lastname+year",
                context=m.group(0),
            ))

        # Very long key (might include first names)
        alpha_parts = re.findall(r"[a-zA-Z]+", key)
        if len(alpha_parts) >= 3 and not any(c.isdigit() for c in key):
            issues.append(Issue(
                Severity.INFO, filepath, line, "bib-key-long",
                f"BibTeX key '{key}' 较长 — 建议简化为 lastname+year",
                context=m.group(0),
            ))
    return issues


# ===================================================================
# RUNNER
# ===================================================================

ALL_TEX_CHECKS = [
    # Label
    check_label_naming,
    check_label_order,
    check_label_in_star,
    check_eq_label_prefix,
    check_informal_formal_labels,
    # References
    check_equation_ref,
    check_nonumber_vs_notag,
    # Brackets
    check_bracket_sizing,
    # Symbols
    check_definition_symbol,
    check_transpose,
    check_norm_bars,
    check_log_power,
    check_big_o_constant,
    # Proof
    check_proof_line_breaks,
    check_vague_reasons,
    check_defensive_probability,
    # Structure
    check_roadmap,
    # Consistency
    check_probability_expectation,
    check_set_separator_consistency,
]


def lint_tex_file(filepath: str) -> list[Issue]:
    """Run all TeX checks on a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return [Issue(Severity.ERROR, filepath, 0, "read-error", f"无法读取: {e}")]

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
        description="LaTeX 学术写作规范自动检查器（基于「打字抄能力」系列）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("path", help="要检查的 .tex/.bib 文件或目录")
    parser.add_argument("--bib", action="store_true", help="同时检查 .bib 文件")
    parser.add_argument("--fix-preview", action="store_true", help="显示修复建议")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument(
        "--severity", choices=["ERROR", "WARN", "INFO"], default="INFO",
        help="最低显示级别（默认 INFO）",
    )
    args = parser.parse_args()

    min_sev = Severity[args.severity]
    tex_files, bib_files = collect_files(args.path, args.bib)

    if not tex_files and not bib_files:
        print(f"未找到 .tex/.bib 文件: {args.path}", file=sys.stderr)
        sys.exit(1)

    all_issues: list[Issue] = []
    for tf in tex_files:
        all_issues.extend(lint_tex_file(tf))
    for bf in bib_files:
        all_issues.extend(check_bibtex(bf))

    all_issues = [iss for iss in all_issues if iss.severity <= min_sev]
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
            parts = [f"{counts[s]} {s!s}" for s in Severity if counts[s]]
            print(f"共检测到 {len(all_issues)} 个问题（{', '.join(parts)}）\n")
            for iss in all_issues:
                print(iss.display(fix_preview=args.fix_preview))
                print()

    sys.exit(1 if any(iss.severity == Severity.ERROR for iss in all_issues) else 0)


if __name__ == "__main__":
    main()
