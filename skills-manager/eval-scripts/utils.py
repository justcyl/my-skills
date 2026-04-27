"""Shared utilities for creator scripts."""

import os
from pathlib import Path



def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def find_my_skills_root(start: Path | None = None) -> Path:
    """Resolve the managed my-skills repository root."""
    env_root = os.environ.get("MY_SKILLS_REPO_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if (candidate / "skills-manager" / "SKILL.md").exists():
            return candidate

    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "skills-manager" / "SKILL.md").exists():
            return parent
        if (parent / ".skills").is_dir():
            return parent

    return current


def skill_workspace_root(skill_path: Path, repo_root: Path | None = None) -> Path:
    """Return the canonical workspace directory for a managed skill."""
    resolved_skill_path = skill_path.resolve()
    resolved_repo_root = repo_root or find_my_skills_root(resolved_skill_path.parent)
    return resolved_repo_root / ".skills" / "workspaces" / resolved_skill_path.name


def package_output_root(repo_root: Path | None = None) -> Path:
    """Return the canonical package output directory for my-skills."""
    resolved_repo_root = repo_root or find_my_skills_root()
    return resolved_repo_root / ".skills" / "packages"
