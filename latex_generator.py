"""LaTeX resume templates and generator."""

import re
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Escape special LaTeX characters in plain text."""
    if not text:
        return ""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _url(href: str, label: str = "") -> str:
    """Return a LaTeX hyperref link."""
    if not href:
        return ""
    label = label or href
    return rf"\href{{{href}}}{{\underline{{{_esc(label)}}}}}"


# ---------------------------------------------------------------------------
# ATS Classic Template
# ---------------------------------------------------------------------------

_ATS_PREAMBLE = r"""\documentclass[10pt,letterpaper]{article}
\usepackage[left=0.5in,top=0.5in,right=0.5in,bottom=0.5in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{fontenc}
\usepackage[utf8]{inputenc}
\pagestyle{empty}

% Section formatting
\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{noitemsep, topsep=2pt, leftmargin=*}
"""

def _ats_resume(data: dict[str, Any]) -> str:
    profile = data["profile"]
    name = _esc(profile.get("name", profile.get("username", "Your Name")))
    email = profile.get("email", "")
    blog = profile.get("blog", "")
    github_url = profile.get("html_url", "")
    location = _esc(profile.get("location", ""))
    summary = _esc(data.get("summary", ""))
    projects = data.get("projects", [])
    skills = data.get("skills_section", {})
    jd = data.get("jd_analysis", {})
    role = _esc(jd.get("role_title", "Software Engineer"))

    # Contact line
    contact_parts = []
    if location:
        contact_parts.append(location)
    if email:
        contact_parts.append(_url(f"mailto:{email}", email))
    if github_url:
        contact_parts.append(_url(github_url, "GitHub"))
    if blog:
        blog_url = blog if blog.startswith("http") else f"https://{blog}"
        contact_parts.append(_url(blog_url, "Portfolio"))
    contact_line = " $|$ ".join(contact_parts)

    lines = [
        _ATS_PREAMBLE,
        r"\begin{document}",
        "",
        r"% ===== HEADER =====",
        rf"\begin{{center}}",
        rf"  {{\Huge \textbf{{{name}}}}} \\[4pt]",
        rf"  \small {contact_line}",
        rf"\end{{center}}",
        "",
    ]

    # Summary
    if summary:
        lines += [
            r"\section{Professional Summary}",
            summary,
            "",
        ]

    # Skills
    all_skills: list[str] = []
    for category, skill_list in skills.items():
        if skill_list:
            label = _esc(category)
            skills_str = ", ".join(_esc(s) for s in skill_list if s)
            all_skills.append(rf"\textbf{{{label}:}} {skills_str}")

    if all_skills:
        lines += [
            r"\section{Technical Skills}",
            r"\begin{itemize}[noitemsep, topsep=0pt]",
        ]
        for s in all_skills:
            lines.append(rf"  \item {s}")
        lines += [r"\end{itemize}", ""]

    # Projects
    if projects:
        lines.append(r"\section{Projects}")
        for proj in projects:
            proj_name = _esc(proj["name"])
            proj_url = proj.get("url", "")
            tech = ", ".join(_esc(t) for t in proj.get("tech_stack", [])[:6] if t)
            one_liner = _esc(proj.get("one_liner", ""))

            name_part = _url(proj_url, proj_name) if proj_url else proj_name
            tech_part = rf" $|$ \textit{{{tech}}}" if tech else ""

            lines.append(
                rf"\noindent\textbf{{{name_part}}}{tech_part} \hfill"
                rf" \textit{{GitHub}}"
            )
            if one_liner:
                lines.append(rf"\noindent\small\textit{{{one_liner}}}\\[2pt]")

            bullets = proj.get("bullets", [])
            if bullets:
                lines.append(r"\begin{itemize}")
                for b in bullets:
                    lines.append(rf"  \item {_esc(b)}")
                lines.append(r"\end{itemize}")
            lines.append(r"\vspace{4pt}")

    lines += ["", r"\end{document}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Modern ATS Template
# ---------------------------------------------------------------------------

_MODERN_PREAMBLE = r"""\documentclass[10pt,letterpaper]{article}
\usepackage[left=0.5in,top=0.5in,right=0.5in,bottom=0.5in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[table,xcdraw]{xcolor}
\usepackage[utf8]{inputenc}
\pagestyle{empty}
\definecolor{accent}{RGB}{79,70,229}

\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\color{accent}\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\setlist[itemize]{noitemsep, topsep=2pt, leftmargin=*}
"""

def _modern_resume(data: dict[str, Any]) -> str:
    # Same structure as ATS but with color preamble
    body = _ats_resume(data)
    # Replace preamble
    body = body.replace(_ATS_PREAMBLE, _MODERN_PREAMBLE)
    return body


# ---------------------------------------------------------------------------
# Research / Academic Template
# ---------------------------------------------------------------------------

_RESEARCH_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[left=0.75in,top=0.75in,right=0.75in,bottom=0.75in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[utf8]{inputenc}
\pagestyle{empty}

\titleformat{\section}{\large\scshape\bfseries}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{10pt}{6pt}
\setlength{\parindent}{0pt}
\setlist[itemize]{noitemsep, topsep=2pt, leftmargin=*}
"""

def _research_resume(data: dict[str, Any]) -> str:
    body = _ats_resume(data)
    body = body.replace(_ATS_PREAMBLE, _RESEARCH_PREAMBLE)
    return body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

TEMPLATES = {
    "ATS Classic": _ats_resume,
    "Modern": _modern_resume,
    "Research": _research_resume,
}


def generate_latex(
    resume_data: dict[str, Any],
    template: str = "ATS Classic",
) -> str:
    """
    Generate LaTeX source code from resume data.

    Args:
        resume_data: Output from resume_generator.generate_full_resume()
        template: One of "ATS Classic", "Modern", "Research"

    Returns:
        LaTeX source string ready to compile with pdflatex.
    """
    fn = TEMPLATES.get(template, _ats_resume)
    return fn(resume_data)
