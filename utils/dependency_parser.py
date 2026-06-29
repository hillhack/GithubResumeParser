"""dependency_parser.py — Deterministically extracts technology names from project files.

No LLM used here. Each parser returns raw package names; the caller should
run them through technology_normalizer.normalize_list() before storing.
"""

import re
import json
import logging
from typing import List, Dict

log = logging.getLogger(__name__)


def parse_requirements_txt(content: str) -> List[str]:
    """Parse requirements.txt / requirements-*.txt format."""
    techs = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers and extras: pkg[extra]>=1.0,<2.0
        name = re.split(r"[>=<!;\[\s]", line)[0].strip()
        if name:
            techs.append(name)
    return techs


def parse_pyproject_toml(content: str) -> List[str]:
    """Parse pyproject.toml dependencies section (basic regex, no full TOML parser needed)."""
    techs = []
    in_deps = False
    for line in content.splitlines():
        if re.match(r"\[tool\.poetry\.dependencies\]|\[project\.dependencies\]|\[dependencies\]", line.strip()):
            in_deps = True
            continue
        if in_deps and line.strip().startswith("["):
            in_deps = False
        if in_deps:
            m = re.match(r'^"?([a-zA-Z0-9_\-\.]+)"?\s*[=\^~><!]', line.strip())
            if m:
                techs.append(m.group(1))
    return techs


def parse_setup_py(content: str) -> List[str]:
    """Extract install_requires list from setup.py."""
    techs = []
    m = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if m:
        for pkg in re.findall(r"['\"]([a-zA-Z0-9_\-\.]+)", m.group(1)):
            techs.append(pkg)
    return techs


def parse_package_json(content: str) -> List[str]:
    """Parse package.json dependencies and devDependencies."""
    techs = []
    try:
        data = json.loads(content)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for pkg in data.get(section, {}).keys():
                techs.append(pkg)
    except (json.JSONDecodeError, Exception) as e:
        log.debug(f"package.json parse error: {e}")
    return techs


def parse_cargo_toml(content: str) -> List[str]:
    """Parse Cargo.toml [dependencies] section."""
    techs = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in ("[dependencies]", "[dev-dependencies]", "[build-dependencies]"):
            in_deps = True
            continue
        if in_deps and stripped.startswith("["):
            in_deps = False
        if in_deps:
            m = re.match(r'^([a-zA-Z0-9_\-]+)\s*=', stripped)
            if m:
                techs.append(m.group(1))
    return techs


def parse_go_mod(content: str) -> List[str]:
    """Parse go.mod require blocks."""
    techs = []
    for line in content.splitlines():
        m = re.match(r'\s*([a-zA-Z0-9_\-\./]+)\s+v[\d\.]+', line)
        if m:
            # Use the last segment of the module path as the name
            techs.append(m.group(1).split("/")[-1])
    return techs


def parse_pom_xml(content: str) -> List[str]:
    """Extract artifactId values from pom.xml."""
    return re.findall(r"<artifactId>([^<]+)</artifactId>", content)


def parse_build_gradle(content: str) -> List[str]:
    """Extract dependency names from build.gradle."""
    techs = []
    for m in re.finditer(r"['\"]([a-zA-Z0-9_\-\.]+:[a-zA-Z0-9_\-\.]+):[^'\"]+['\"]", content):
        # Use the artifactId portion (second segment)
        parts = m.group(1).split(":")
        if len(parts) >= 2:
            techs.append(parts[1])
    return techs


def parse_gemfile(content: str) -> List[str]:
    """Parse Ruby Gemfile."""
    techs = []
    for m in re.finditer(r"gem\s+['\"]([a-zA-Z0-9_\-]+)['\"]", content):
        techs.append(m.group(1))
    return techs


def parse_composer_json(content: str) -> List[str]:
    """Parse PHP composer.json."""
    techs = []
    try:
        data = json.loads(content)
        for section in ("require", "require-dev"):
            for pkg in data.get(section, {}).keys():
                if pkg != "php":
                    techs.append(pkg.split("/")[-1])
    except Exception:
        pass
    return techs


def parse_pubspec_yaml(content: str) -> List[str]:
    """Parse Flutter/Dart pubspec.yaml."""
    techs = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in ("dependencies:", "dev_dependencies:"):
            in_deps = True
            continue
        if in_deps and stripped.endswith(":") and not line.startswith(" "):
            in_deps = False
        if in_deps:
            m = re.match(r"^\s+([a-zA-Z0-9_]+)\s*:", stripped)
            if m:
                techs.append(m.group(1))
    return techs


def parse_dockerfile(content: str) -> List[str]:
    """Extract useful signals from a Dockerfile."""
    techs = ["Docker"]
    for line in content.splitlines():
        line_lower = line.strip().lower()
        if line_lower.startswith("from "):
            base = line.split()[1].split(":")[0].split("/")[-1]
            if base and base not in ("scratch", "alpine", "debian", "ubuntu", "centos"):
                techs.append(base)
        if "apt-get install" in line_lower or "apk add" in line_lower:
            pkgs = re.findall(r"\b(nginx|redis|postgresql|mysql|mongodb|nodejs|npm)\b", line_lower)
            techs.extend(pkgs)
    return techs


def parse_docker_compose(content: str) -> List[str]:
    """Extract service names and images from docker-compose.yml."""
    techs = ["Docker"]
    for m in re.finditer(r"image:\s*([a-zA-Z0-9_\-]+)", content):
        img = m.group(1)
        if img not in ("alpine", "debian", "ubuntu", "scratch"):
            techs.append(img)
    return techs


def parse_github_actions(content: str) -> List[str]:
    """Infer CI/CD technologies from GitHub Actions workflow files."""
    techs = ["GitHub Actions", "CI/CD"]
    content_lower = content.lower()
    signals = {
        "pytest": "pytest",
        "jest": "Jest",
        "cargo test": "Cargo",
        "go test": "Go",
        "docker build": "Docker",
        "terraform": "Terraform",
        "aws": "AWS",
        "gcloud": "GCP",
        "azure": "Azure",
        "kubectl": "Kubernetes",
        "helm": "Helm",
        "sonar": "SonarQube",
        "codecov": "Codecov",
    }
    for signal, label in signals.items():
        if signal in content_lower:
            techs.append(label)
    return techs


def parse_makefile(content: str) -> List[str]:
    """Extract tool references from Makefile targets."""
    techs = []
    signals = {
        "docker": "Docker",
        "pytest": "pytest",
        "terraform": "Terraform",
        "kubectl": "Kubernetes",
        "npm": "npm",
        "cargo": "Cargo",
    }
    content_lower = content.lower()
    for signal, label in signals.items():
        if signal in content_lower:
            techs.append(label)
    return techs


# ── Main dispatcher ──────────────────────────────────────────────────────────

_PARSER_MAP: Dict[str, callable] = {
    "requirements.txt": parse_requirements_txt,
    "pyproject.toml": parse_pyproject_toml,
    "setup.py": parse_setup_py,
    "environment.yml": parse_requirements_txt,  # similar format
    "package.json": parse_package_json,
    "cargo.toml": parse_cargo_toml,
    "go.mod": parse_go_mod,
    "pom.xml": parse_pom_xml,
    "build.gradle": parse_build_gradle,
    "gemfile": parse_gemfile,
    "composer.json": parse_composer_json,
    "pubspec.yaml": parse_pubspec_yaml,
    "dockerfile": parse_dockerfile,
    "docker-compose.yml": parse_docker_compose,
    "makefile": parse_makefile,
}


def parse_file(filename: str, content: str) -> List[str]:
    """Dispatch to the correct parser by filename (case-insensitive)."""
    key = filename.lower().split("/")[-1]
    if "workflow" in filename.lower() or ".github/workflows" in filename.lower():
        return parse_github_actions(content)
    parser = _PARSER_MAP.get(key)
    if parser:
        try:
            return parser(content)
        except Exception as e:
            log.warning(f"Parser error for {filename}: {e}")
    return []


def parse_all_files(file_contents: Dict[str, str]) -> List[str]:
    """Parse all available project files and return a merged raw tech list."""
    all_techs: List[str] = []
    for filename, content in file_contents.items():
        if content:
            all_techs.extend(parse_file(filename, content))
    return all_techs
