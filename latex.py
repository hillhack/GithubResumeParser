"""
latex.py — Optimised LaTeX resume generator for alldone.

Generates a clean, professional resume matching the refined personal template style:
  - fontawesome5 icons for GitHub, email, LinkedIn
  - accent colour per template
  - \resumeProject{Title}{URL}{Tech stack} (three arguments)
  - \resumeItemListStart / \resumeItemListEnd bullet blocks
  - grouped skills and concise project descriptions
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

# ── LaTeX escaping (single-pass, regex-based) ────────────────────────────────
_LATEX_SPECIAL = re.compile(r'[\\&%$#_{}~^]')
_ESCAPE_MAP = {
    '\\': r'\textbackslash{}',
    '&':  r'\&',
    '%':  r'\%',
    '$':  r'\$',
    '#':  r'\#',
    '_':  r'\_',
    '{':  r'\{',
    '}':  r'\}',
    '~':  r'\textasciitilde{}',
    '^':  r'\textasciicircum{}',
}

def _esc(text: Optional[str]) -> str:
    """Escape LaTeX special characters in text."""
    if not text:
        return ""
    return _LATEX_SPECIAL.sub(lambda m: _ESCAPE_MAP[m.group()], text)

def _href(url: str, label: str) -> str:
    """Return a coloured \href command."""
    if not url:
        return _esc(label)
    return rf"\href{{{url}}}{{{_esc(label)}}}"


# ── Colour themes ───────────────────────────────────────────────────────────
_THEMES: Dict[str, str] = {
    "ATS Classic": "0053A0",
    "Modern":      "6D28D9",
    "Research":    "065F46",
}


# ── Preamble (updated with refined custom commands) ──────────────────────────
def _preamble(theme_hex: str) -> str:
    return rf"""
\documentclass[a4paper,11pt]{{article}}

% -------------------- PACKAGES --------------------
\usepackage{{latexsym}}
\usepackage{{xcolor}}
\usepackage{{ragged2e}}
\usepackage[empty]{{fullpage}}
\usepackage{{tabularx}}
\usepackage{{titlesec}}
\usepackage{{geometry}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage{{fontawesome5}}
\usepackage[T1]{{fontenc}}

% -------------------- COLOUR THEME --------------------
\definecolor{{theme}}{{HTML}}{{{theme_hex}}}

\hypersetup{{
    colorlinks=true,
    urlcolor=theme,
    linkcolor=theme
}}

% -------------------- PAGE LAYOUT --------------------
\geometry{{
    left=1.2cm,
    right=1.2cm,
    top=1cm,
    bottom=1cm
}}

\pagestyle{{fancy}}
\fancyhf{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

% -------------------- SECTION FORMAT --------------------
\titleformat{{\section}}
{{\large\scshape\raggedright\color{{theme}}}}
{{}}{{0em}}{{}}
[\color{{theme}}\titlerule\vspace{{-2pt}}]

\titlespacing*{{\section}}{{0pt}}{{10pt}}{{4pt}}

% -------------------- CUSTOM COMMANDS --------------------
\renewcommand{{\labelitemi}}{{\textcolor{{theme}}{{$\bullet$}}}}

% Refined project header
\newcommand{{\resumeProject}}[4]{{
    \vspace{{5pt}}
    \noindent\textbf{{#1}} $|$ \textit{{#4}} \hfill \href{{#2}}{{\faGithub}} \\
    \vspace{{2pt}}\small\textit{{#3}}
}}

\newcommand{{\resumeItemListStart}}{{
\begin{{itemize}}[
leftmargin=3.5ex,
itemsep=0pt,
topsep=2pt,
parsep=0pt
]\small
}}

\newcommand{{\resumeItemListEnd}}{{
\end{{itemize}}
\vspace{{2pt}}
}}
""".lstrip("\n")


# ── Header (icon-based, cleaner layout) ─────────────────────────────────────
def _header(p: Dict[str, Any]) -> str:
    name     = _esc(p.get("name") or p.get("username", ""))
    email    = p.get("email", "")
    gh_url   = p.get("github_url", "")
    gh_user  = p.get("username", "")
    website  = p.get("website", "")
    linkedin = p.get("linkedin_url", "")
    location = _esc(p.get("location", ""))
    orgs     = p.get("organizations", [])

    # Right column icons
    icons: List[str] = []
    if email:
        icons.append(rf"\href{{mailto:{email}}}{{\faEnvelope\ {_esc(email)}}}")
    if gh_url:
        icons.append(rf"\href{{{gh_url}}}{{\faGithub\ {_esc(gh_user)}}}")
    if linkedin:
        icons.append(rf"\href{{{linkedin}}}{{\faLinkedin\ LinkedIn}}")
    if website:
        icons.append(rf"\href{{{website}}}{{\faGlobe\ Portfolio}}")

    # Left column (description / location)
    left_lines: List[str] = []
    if orgs:
        left_lines.append(rf"\textbf{{{_esc(', '.join(orgs[:2]))}}}")
    if location:
        left_lines.append(rf"\small {location}")

    right_col = r" \\ ".join(icons)
    left_col  = r" \\ ".join(left_lines)

    return rf"""
\begin{{tabular*}}{{\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
{{\Huge \textbf{{\color{{theme}} {name}}}}} & {right_col} \\
{left_col} & \\
\end{{tabular*}}
\vspace{{4pt}}
""".lstrip("\n")


# ── Summary ─────────────────────────────────────────────────────────────────
def _summary(text: str) -> str:
    if not text:
        return ""
    return rf"""
\section{{Summary}}
{_esc(text)}
""".lstrip("\n")


# ── Skills (grouped as Languages / Frameworks / Tools) ──────────────────────
def _skills(skills: Dict[str, List[str]]) -> str:
    if not skills:
        return ""
        
    rows = []
    for cat, items in skills.items():
        if not items: continue
        rows.append(rf"\item \textbf{{{_esc(cat)}:}} {', '.join(_esc(s) for s in items if s)}")
            
    rows_str = "\n".join(rows)
    return rf"""
\section{{Technical Skills}}
\resumeItemListStart
{rows_str}
\resumeItemListEnd
""".lstrip("\n")


# ── Bullet helper ───────────────────────────────────────────────────────────
def _bullet_list(bullets: List[str]) -> str:
    if not bullets:
        return ""
    items = "\n".join(rf"\item {_esc(b)}" for b in bullets)
    return rf"""
\resumeItemListStart
{items}
\resumeItemListEnd
""".lstrip("\n")


# ── Open Source Contributions ────────────────────────────────────────────────
def _contributions(contributions: List[Dict[str, Any]]) -> str:
    if not contributions:
        return ""
    blocks: List[str] = [r"\section{Open Source Contributions}"]
    for c in contributions:
        name = _esc(c.get("name", "Repository"))
        url = c.get("url", "")
        tech_stack = ", ".join(_esc(t) for t in c.get("tech_stack", []) if t)
        desc = _esc(c.get("desc", ""))
        
        # We reuse \resumeProject for OSS, no bullets
        blocks.append(rf"\resumeProject{{{name}}}{{{url}}}{{{desc}}}{{{tech_stack}}}")
        blocks.append(r"\vspace{4pt}")
    return "\n".join(blocks)

# ── Projects (using three-argument \resumeProject) ──────────────────────────
def _projects(projects: List[Dict[str, Any]]) -> str:
    if not projects:
        return ""
    blocks: List[str] = [r"\section{Key Projects}"]
    for proj in projects:
        name    = _esc(proj.get("name", "Project"))
        url     = proj.get("html_url") or proj.get("url", "")
        tech_stack = ", ".join(_esc(t) for t in proj.get("tech_stack", []) if t)
        bullets = proj.get("bullets", [])
        desc = _esc(proj.get("one_liner", ""))

        # Use the four-argument resumeProject: title, GitHub URL, desc, tech stack
        blocks.append(rf"\resumeProject{{{name}}}{{{url}}}{{{desc}}}{{{tech_stack}}}")
        if bullets:
            blocks.append(_bullet_list(bullets))
        else:
            blocks.append(r"\vspace{4pt}")

    return "\n".join(blocks)


# ── Main generator ──────────────────────────────────────────────────────────
def generate_latex(data: Dict[str, Any], template: str = "ATS Classic") -> str:
    """
    Generate a complete, compilable LaTeX resume document.

    Args:
        data:     dict returned by the generate_resume_content MCP tool.
        template: one of "ATS Classic", "Modern", "Research".

    Returns:
        Full LaTeX string.
    """
    theme_hex = _THEMES.get(template, _THEMES["ATS Classic"])
    profile   = data.get("profile", {})
    skills    = data.get("skills_section", {})
    projects  = data.get("projects", [])
    contributions = data.get("contributions", [])
    summary   = data.get("summary", "")

    return (
        _preamble(theme_hex)
        + "\n% ==================== DOCUMENT ====================\n"
        + r"\begin{document}" + "\n"
        + r"\fontfamily{cmr}\selectfont" + "\n\n"
        + "% ==================== HEADER ====================\n"
        + _header(profile)
        + "\n% ==================== SUMMARY ====================\n"
        + _summary(summary)
        + "\n% ==================== SKILLS ====================\n"
        + _skills(skills)
        + "\n% ==================== PROJECTS ====================\n"
        + _projects(projects)
        + "\n% ==================== CONTRIBUTIONS ====================\n"
        + _contributions(contributions)
        + "\n"
        + r"\end{document}" + "\n"
    )
