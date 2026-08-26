"""Build and upload an Obot MCP package to PyPI.

PyPI rejects a version that already exists. This script keeps the current
version if it is unpublished, otherwise it bumps the patch number until unique.

Usage (from my-mcp-skill):
    python publish.py
    python publish.py --package card-verify-mcp
    python publish.py --package weather-mcp
    python publish.py --bump minor
    python publish.py --no-bump
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN_FILE = ROOT / ".pypi-token"

PACKAGES = {
    "card-verify-mcp": ROOT / "card-verify-mcp",
    "weather-mcp": ROOT / "weather-mcp",
}

CATALOG_TENANCY = "Multi-tenant"

VERSION_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$', re.M)
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"(\d+\.\d+\.\d+)"\s*$', re.M)
NAME_RE = re.compile(r'^name\s*=\s*"([^"]+)"\s*$', re.M)


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd, env=env)


def read_token() -> str:
    token = os.environ.get("PYPI_API_TOKEN", "").strip()
    if not token and TOKEN_FILE.is_file():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token.startswith("pypi-"):
        raise SystemExit(
            "Missing PyPI token. Set PYPI_API_TOKEN or put it in .pypi-token "
            "(this file is gitignored)."
        )
    return token


def parse_pyproject(package_dir: Path) -> tuple[str, tuple[int, int, int]]:
    text = (package_dir / "pyproject.toml").read_text(encoding="utf-8")
    name_match = NAME_RE.search(text)
    version_match = VERSION_RE.search(text)
    if not name_match or not version_match:
        raise SystemExit(f"Could not parse name/version in {package_dir / 'pyproject.toml'}")
    version = tuple(int(part) for part in version_match.groups())
    return name_match.group(1), version


def format_version(version: tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


def bump_version(version: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def published_versions(package_name: str) -> set[str]:
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return set()
        raise SystemExit(f"Failed to query PyPI for {package_name}: HTTP {exc.code}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to query PyPI for {package_name}: {exc}")
    return set(payload.get("releases", {}).keys())


def write_version(package_dir: Path, new_version: str) -> None:
    pyproject = package_dir / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    updated, count = VERSION_RE.subn(f'version = "{new_version}"', text, count=1)
    if count != 1:
        raise SystemExit(f"Failed to update version in {pyproject}")
    pyproject.write_text(updated, encoding="utf-8")

    for init in package_dir.glob("*/__init__.py"):
        init_text = init.read_text(encoding="utf-8")
        if INIT_VERSION_RE.search(init_text):
            init.write_text(
                INIT_VERSION_RE.sub(f'__version__ = "{new_version}"', init_text),
                encoding="utf-8",
            )


def choose_version(
    package_name: str,
    current: tuple[int, int, int],
    bump: str | None,
) -> str:
    existing = published_versions(package_name)
    version = current
    if bump:
        version = bump_version(version, bump)
    while format_version(version) in existing:
        version = bump_version(version, "patch")
    chosen = format_version(version)
    if chosen != format_version(current):
        print(f"{package_name}: {format_version(current)} already on PyPI, using {chosen}")
    else:
        print(f"{package_name}: publishing {chosen}")
    return chosen


def catalog_markdown(name: str, package_name: str, version: str) -> str:
    if name == "card-verify-mcp":
        display_name = "证照鉴伪"
        short = "根据图片 URL 核验行驶证等证照，调用 id-vision cardVerify 接口。"
        description = f"""根据证照图片 URL 做鉴伪/识别，适合行驶证等现场核验场景。

## 功能
- 提交图片 URL，调用 `card_verify`
- 支持证照类型（默认 `VEHICLE_LICENSE`）和正反面（`FRONT` / `BACK`）
- 凭证通过环境变量注入，不写进代码

## 使用前需要
- **App Id**：`CARD_VERIFY_APP_ID`（请求头 `X-App-Id`）
- **API Key**：`CARD_VERIFY_API_KEY`（请求头 `X-Api-Key`）
- **Base URL**（可选）：`CARD_VERIFY_BASE_URL`

UVX 包名：`{package_name}=={version}`
"""
        extra_env = """
## Obot 环境变量
- CARD_VERIFY_APP_ID（必填）
- CARD_VERIFY_API_KEY（必填，敏感）
- CARD_VERIFY_BASE_URL（可选）
"""
    else:
        display_name = "天气查询"
        short = "查询北京、上海、广州、深圳、纽约的演示天气和三日预报。"
        description = f"""提供演示天气数据，无需 API Key，适合联调和现场作业流程演示。

## 功能
- `list_cities`：列出支持的城市
- `get_weather`：当前天气
- `get_forecast`：三日预报
- 支持中文城市名：北京 / 上海 / 广州 / 深圳 / 纽约

UVX 包名：`{package_name}=={version}`
"""
        extra_env = "\n## Obot 环境变量\n无需配置。\n"

    return f"""# Obot Catalog Entry（发布时覆盖写入，直接复制到创建表单）

## Name
{display_name}

## Short Description
{short}

## Description
{description.rstrip()}

## Server Tenancy / Type
{CATALOG_TENANCY}

## Runtime
- Runtime: UVX
- Package: `{package_name}=={version}`
{extra_env}
## 说明
- Type 选 Multi-tenant：所有用户共用同一份 MCP 实例和同一组环境变量。
- 此项保存后不能改，要改必须删除后重建。
"""


def write_catalog_entry(name: str, package_name: str, version: str) -> Path:
    path = PACKAGES[name] / "CATALOG.md"
    path.write_text(catalog_markdown(name, package_name, version), encoding="utf-8")
    return path


def publish_one(name: str, bump: str | None, token: str) -> None:
    package_dir = PACKAGES[name]
    if not (package_dir / "pyproject.toml").is_file():
        raise SystemExit(f"Missing {package_dir / 'pyproject.toml'}")

    package_name, current = parse_pyproject(package_dir)
    new_version = choose_version(package_name, current, bump)
    if new_version != format_version(current):
        write_version(package_dir, new_version)

    for folder in ("dist", "build"):
        path = package_dir / folder
        if path.exists():
            shutil.rmtree(path)

    python = sys.executable
    run([python, "-m", "pip", "install", "-q", "build", "twine"], cwd=package_dir)
    run([python, "-m", "build"], cwd=package_dir)

    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    run(
        [python, "-m", "twine", "upload", "--non-interactive", "dist/*"],
        cwd=package_dir,
        env=env,
    )
    write_catalog_entry(name, package_name, new_version)
    print(f"OK  {package_name}=={new_version}")
    print(f"    uvx {package_name}=={new_version}")
    print(f"    catalog: {package_dir / 'CATALOG.md'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish MCP packages to PyPI")
    parser.add_argument(
        "--package",
        choices=["all", *PACKAGES],
        default="all",
        help="Which package to publish (default: all)",
    )
    parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default=None,
        help="Force a version bump before checking PyPI. Default: bump only if needed.",
    )
    parser.add_argument(
        "--no-bump",
        action="store_true",
        help="Fail instead of bumping when the current version already exists.",
    )
    args = parser.parse_args()

    token = read_token()
    targets = list(PACKAGES) if args.package == "all" else [args.package]

    for name in targets:
        package_name, current = parse_pyproject(PACKAGES[name])
        existing = published_versions(package_name)
        if args.no_bump and format_version(current) in existing:
            raise SystemExit(
                f"{package_name}=={format_version(current)} already exists on PyPI. "
                "Drop --no-bump or pass --bump patch."
            )
        publish_one(name, args.bump, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
