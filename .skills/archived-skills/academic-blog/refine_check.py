#!/usr/bin/env python3
"""
research-essay-page refine checker
───────────────────────────────────
Reads a generated HTML file and runs structural + visual sanity checks.
Outputs a PASS/FAIL checklist that an agent can iterate on.

Usage:
    python3 refine_check.py <path-to-html>

Exit code 0 = all passed, 1 = has failures.
"""

import sys, re, os
from html.parser import HTMLParser
from collections import Counter

# ─── Helpers ───

class TagCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = Counter()
        self.open_tags = []
        self.ids = []
        self.classes = []
        self.imgs = []           # (src, alt, has_max_width_ancestor)
        self.links = []          # (href, text)
        self.empty_texts = []    # tags with only whitespace
        self.placeholders = []   # {{...}} remnants
        self.tables = []         # (id_or_index, col_counts_per_row)
        self._current_table = None
        self._current_row_cols = 0
        self._table_index = 0

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        d = dict(attrs)
        if 'id' in d:
            self.ids.append(d['id'])
        if 'class' in d:
            self.classes.extend(d['class'].split())
        if tag == 'img':
            self.imgs.append((d.get('src',''), d.get('alt',''), d.get('loading','')))
        if tag == 'a':
            self.links.append((d.get('href',''), ''))
        if tag == 'table':
            self._current_table = {'id': d.get('id', f'table-{self._table_index}'),
                                   'class': d.get('class',''),
                                   'rows': []}
            self._table_index += 1
        if tag == 'tr':
            self._current_row_cols = 0
        if tag in ('td', 'th'):
            colspan = int(d.get('colspan', 1))
            self._current_row_cols += colspan

    def handle_endtag(self, tag):
        if tag == 'tr' and self._current_table is not None:
            self._current_table['rows'].append(self._current_row_cols)
        if tag == 'table' and self._current_table is not None:
            self.tables.append(self._current_table)
            self._current_table = None

    def handle_data(self, data):
        if '{{' in data and '}}' in data:
            found = re.findall(r'\{\{[A-Z_]+\}\}', data)
            self.placeholders.extend(found)


def check(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n         → {detail}"
    return (passed, msg)


def _find_math_blocks(html):
    r"""Return math blocks delimited by $$...$$ or $...$.

    We intentionally keep this lightweight and HTML-oriented rather than fully
    parsing TeX. Delimiters escaped as \$ are ignored.
    """
    blocks = []
    i = 0
    n = len(html)
    while i < n:
        if html[i] != '$' or (i > 0 and html[i - 1] == '\\'):
            i += 1
            continue

        if i + 1 < n and html[i + 1] == '$':
            delim = '$$'
            start = i
            i += 2
            content_start = i
            while i + 1 < n:
                if html[i] == '$' and html[i + 1] == '$' and html[i - 1] != '\\':
                    blocks.append({
                        'delim': delim,
                        'content': html[content_start:i],
                        'start': start,
                        'end': i + 2,
                    })
                    i += 2
                    break
                i += 1
            else:
                break
            continue

        delim = '$'
        start = i
        i += 1
        content_start = i
        while i < n:
            if html[i] == '$' and html[i - 1] != '\\':
                blocks.append({
                    'delim': delim,
                    'content': html[content_start:i],
                    'start': start,
                    'end': i + 1,
                })
                i += 1
                break
            i += 1
        else:
            break
    return blocks


def _find_raw_angle_brackets_in_math(content):
    r"""Find suspicious raw < or > inside TeX math.

    Allowed patterns:
    - \left< / \right< / \big< / friends
    - \langle / \rangle
    - already-escaped \lt / \gt
    """
    issues = []
    for m in re.finditer(r'[<>]', content):
        ch = m.group(0)
        idx = m.start()
        prefix = content[max(0, idx - 16):idx]
        suffix = content[idx:idx + 16]

        if ch == '<':
            if re.search(r'\\(?:left|right|big|Big|bigl|bigr|Bigl|Bigr|bigm|Bigm)\s*$', prefix):
                continue
            if re.search(r'\\langle\s*$', prefix):
                continue
            if re.search(r'\\lt\s*$', prefix):
                continue
        else:
            if re.search(r'\\(?:left|right|big|Big|bigl|bigr|Bigl|Bigr|bigm|Bigm)\s*$', prefix):
                continue
            if re.search(r'\\rangle\s*$', prefix):
                continue
            if re.search(r'\\gt\s*$', prefix):
                continue

        issues.append({
            'char': ch,
            'index': idx,
            'snippet': (prefix + suffix).replace('\n', ' '),
        })
    return issues


def run_checks(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Also load linked CSS files for CSS checks
    html_dir = os.path.dirname(os.path.abspath(html_path))
    css_content = ''
    for css_href in re.findall(r'<link[^>]+href="([^"]+\.css)"', html):
        if css_href.startswith('http'):
            continue  # skip CDN
        css_path = os.path.join(html_dir, css_href)
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as cf:
                css_content += cf.read() + '\n'
    # Also include inline <style>
    for m in re.finditer(r'<style>(.*?)</style>', html, re.DOTALL):
        css_content += m.group(1) + '\n'
    full_content = html + '\n' + css_content  # combined for CSS checks

    parser = TagCounter()
    parser.feed(html)

    results = []

    # ═══ Category 1: Structure ═══
    results.append(("── Structure ──", None))

    results.append(check(
        "No remaining {{ }} placeholders",
        len(parser.placeholders) == 0,
        f"Found: {parser.placeholders[:5]}" if parser.placeholders else ""
    ))

    results.append(check(
        "Has <title> tag",
        parser.tags.get('title', 0) >= 1
    ))

    results.append(check(
        "Has exactly one <h1>",
        parser.tags.get('h1', 0) == 1,
        f"Found {parser.tags.get('h1', 0)} h1 tags"
    ))

    results.append(check(
        "Has at least 2 <section> blocks",
        parser.tags.get('section', 0) >= 2,
        f"Found {parser.tags.get('section', 0)} sections"
    ))

    results.append(check(
        "Lightbox dialog preserved (id=image-lightbox)",
        'image-lightbox' in parser.ids,
        "Required by JS — do NOT remove"
    ))

    has_summary = 'summary' in parser.ids
    results.append(check(
        "Summary block id='summary' present",
        has_summary,
        "Required by scroll-reveal JS"
    ))

    # ═══ Category 2: Images ═══
    results.append(("── Images ──", None))

    for src, alt, loading in parser.imgs:
        if src and not src.startswith('#') and 'lightbox' not in src:
            results.append(check(
                f"Image has alt text: {src[:60]}",
                bool(alt),
                "Missing alt attribute" if not alt else ""
            ))

    # Check CSS has img max-width: 100%
    has_img_max_width = bool(re.search(
        r'(\.(plain-figure|hero-figure|comparison-card|figure-block).*?img|img).*?max-width:\s*100%',
        full_content, re.DOTALL
    ))
    results.append(check(
        "CSS: images have max-width: 100%",
        has_img_max_width,
        "Add 'max-width: 100%; height: auto;' to img rules to prevent overflow"
    ))

    # Check no margin-note overflow
    has_overflow_margin = bool(re.search(
        r'\.with-margin-note\s*\{[^}]*width:\s*calc\(100%\s*\+',
        full_content
    ))
    results.append(check(
        "CSS: .with-margin-note does NOT overflow container",
        not has_overflow_margin,
        "Change 'width: calc(100% + 176px)' to 'width: 100%'"
    ))

    # ═══ Category 3: Tables ═══
    results.append(("── Tables ──", None))

    for tbl in parser.tables:
        if 'lightbox' in tbl.get('class', ''):
            continue
        rows = tbl['rows']
        if not rows:
            continue
        # Check column consistency
        max_cols = max(rows)
        inconsistent = [i for i, c in enumerate(rows) if c != max_cols and c != 0]
        tbl_name = tbl['id'] or tbl['class'][:30]
        results.append(check(
            f"Table '{tbl_name}': consistent column count",
            len(inconsistent) == 0,
            f"Row(s) {inconsistent} have different column counts (expected {max_cols}, got {[rows[i] for i in inconsistent[:3]]})" if inconsistent else f"{len(rows)} rows × {max_cols} cols"
        ))

    if not parser.tables:
        results.append(check("At least one table present", False, "No <table> found"))

    # ═══ Category 4: CSS Integrity ═══
    results.append(("── CSS Integrity ──", None))

    # Check for broken .demo-gallery nesting
    has_demo_gallery_bug = bool(re.search(r'\.demo-gallery\s*\{\s*\n\s*\.summary-block', full_content))
    results.append(check(
        "CSS: no .demo-gallery { nesting bug",
        not has_demo_gallery_bug,
        "'.demo-gallery {' immediately followed by '.summary-block {' breaks CSS nesting — remove '.demo-gallery {' line"
    ))

    # Check for broken @media nesting
    has_media_bug = bool(re.search(r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{\s*\n\s*\.image-lightbox', full_content))
    results.append(check(
        "CSS: no unclosed @media(prefers-reduced-motion) bug",
        not has_media_bug,
        "@media rule swallows .image-lightbox styles — remove the @media line"
    ))

    # Count CSS braces balance (rough check)
    if css_content:
        opens = css_content.count('{')
        closes = css_content.count('}')
        results.append(check(
            f"CSS brace balance: {opens} open, {closes} close",
            opens == closes,
            f"Mismatch: {opens} {{ vs {closes} }}" if opens != closes else ""
        ))
    else:
        style_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
        if style_match:
            css = style_match.group(1)
            opens = css.count('{')
            closes = css.count('}')
            results.append(check(
                f"CSS brace balance: {opens} open, {closes} close",
                opens == closes,
                f"Mismatch: {opens} {{ vs {closes} }}" if opens != closes else ""
            ))

    # ═══ Category 5: Content Quality ═══
    results.append(("── Content ──", None))

    # Check reference list consistency
    ref_ids = [id for id in parser.ids if id.startswith('ref-')]
    inline_refs = re.findall(r'href="#ref-(\d+)"', html)
    missing_targets = [r for r in set(inline_refs) if f'ref-{r}' not in parser.ids]
    results.append(check(
        "Inline refs → reference list links are valid",
        len(missing_targets) == 0,
        f"Inline refs point to missing targets: ref-{', ref-'.join(missing_targets)}" if missing_targets else f"{len(set(inline_refs))} inline refs, {len(ref_ids)} reference entries"
    ))

    # Check for empty href
    broken_links = [href for href, _ in parser.links if href in ('', '#', None) and _ != '']
    # Just check there aren't placeholder links
    placeholder_links = [href for href, _ in parser.links if href and '{{' in href]
    results.append(check(
        "No placeholder URLs in links",
        len(placeholder_links) == 0,
        f"Found: {placeholder_links[:3]}" if placeholder_links else ""
    ))

    math_blocks = _find_math_blocks(html)
    raw_angle_issues = []
    for block in math_blocks:
        issues = _find_raw_angle_brackets_in_math(block['content'])
        for issue in issues:
            raw_angle_issues.append({
                'delim': block['delim'],
                'snippet': issue['snippet'],
                'char': issue['char'],
            })
    preview = '; '.join(
        f"{item['delim']} ... {item['snippet']} ... {item['delim']}"
        for item in raw_angle_issues[:3]
    )
    results.append(check(
        "KaTeX math contains no raw < or > that can break HTML parsing",
        len(raw_angle_issues) == 0,
        "Raw angle bracket found inside $...$ / $$...$$. Browser may parse it as an HTML tag and break the DOM. Replace raw '<' / '>' with '\\lt' / '\\gt'. Examples: " + preview if raw_angle_issues else ""
    ))

    # ═══ Category 6: Accessibility ═══
    results.append(("── Accessibility ──", None))

    results.append(check(
        "Has lang attribute on <html>",
        bool(re.search(r'<html\s+lang="[^"]+"', html)),
    ))

    results.append(check(
        "Has meta viewport",
        bool(re.search(r'<meta\s+name="viewport"', html)),
    ))

    results.append(check(
        "Has meta description",
        bool(re.search(r'<meta\s+name="description"\s+content="[^"]+"', html)),
    ))

    # ═══ Summary ═══
    total = sum(1 for p, _ in results if p is not None and isinstance(p, bool))
    passed = sum(1 for p, _ in results if p is True)
    failed = sum(1 for p, _ in results if p is False)

    print(f"\n{'='*60}")
    print(f"  Research Essay Page — Refine Checklist")
    print(f"  File: {html_path}")
    print(f"{'='*60}\n")

    for passed_val, msg in results:
        if msg is None:
            print(f"\n{passed_val}")  # category header
        else:
            print(msg)

    print(f"\n{'─'*60}")
    print(f"  Total: {total} checks  |  ✅ {passed} passed  |  ❌ {failed} failed")
    print(f"{'─'*60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <path-to-html>")
        sys.exit(2)
    sys.exit(run_checks(sys.argv[1]))
