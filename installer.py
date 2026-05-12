#!/usr/bin/env python3
"""Cross-platform installer for xsint."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

MIN_MINOR = 10
MAX_MINOR = 13


def info(message: str) -> None:
    print(message)


def section(message: str) -> None:
    print(message)


def success(message: str) -> None:
    print(message)


def warn(message: str) -> None:
    print(message)


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_capture(command: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(command, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def run(command: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(command, cwd=str(cwd) if cwd else None)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def find_python() -> str:
    candidates: list[list[str]] = []
    if sys.executable:
        candidates.append([sys.executable])

    for version in ("3.13", "3.12", "3.11", "3.10"):
        candidates.append([f"python{version}"])
        candidates.append(["py", f"-{version}"])

    candidates.extend([["python3"], ["python"], ["py", "-3"]])

    checked: set[tuple[str, ...]] = set()
    for cmd in candidates:
        key = tuple(cmd)
        if key in checked:
            continue
        checked.add(key)

        binary = cmd[0]
        if not Path(binary).is_file() and not command_exists(binary):
            continue

        probe = cmd + [
            "-c",
            "import sys; print(sys.version_info.minor); print(sys.executable)",
        ]
        code, out, _ = run_capture(probe)
        if code != 0:
            continue
        lines = out.splitlines()
        if len(lines) < 2:
            continue
        try:
            minor = int(lines[0].strip())
        except ValueError:
            continue
        if MIN_MINOR <= minor <= MAX_MINOR:
            return lines[1].strip()

    fail(
        f"[!] No compatible Python 3.{MIN_MINOR}-3.{MAX_MINOR} interpreter found.\n"
        "Install Python and rerun this installer."
    )
    return ""


def ensure_pip(python: str) -> None:
    if run_capture([python, "-m", "pip", "--version"])[0] == 0:
        return
    run_capture([python, "-m", "ensurepip", "--upgrade"])
    if run_capture([python, "-m", "pip", "--version"])[0] != 0:
        fail(
            f"[!] pip is not available for {python}.\n"
            "Install pip for your Python interpreter and rerun."
        )


def pip_install(python: str, args: list[str]) -> None:
    code, out, err = _pip_install_try(python, args)
    if code == 0:
        return
    if out:
        info(out)
    if err:
        print(err, file=sys.stderr)
    raise SystemExit(code)


def _pip_install_try(python: str, args: list[str]) -> tuple[int, str, str]:
    """Run pip install. Returns (returncode, stdout, stderr)."""
    cmd = [python, "-m", "pip", "install", "--user", "--no-warn-script-location"] + args
    code, out, err = run_capture(cmd)
    if code == 0:
        return 0, out, err

    text = f"{out}\n{err}".lower()
    if "externally-managed-environment" in text or "externally managed" in text:
        # PEP 668 — retry with --break-system-packages.
        cmd2 = [
            python, "-m", "pip", "install", "--break-system-packages",
            "--user", "--no-warn-script-location",
        ] + args
        code2, out2, err2 = run_capture(cmd2)
        return code2, out2, err2

    return code, out, err


def pip_install_with_fallback(python: str, primary: list[str], *, fallback_no_deps: bool = False) -> None:
    """Install with the given args; on a resolver conflict, retry --no-deps.

    Used for ghunt+gitfive — their pinned transitive deps sometimes
    diverge enough that pip can't find a single resolution. --no-deps
    lets the install land at the cost of skipping dep checks. Both
    tools' actual import-time deps are usually already provided by
    xsint's own install so this is safe in practice.
    """
    code, out, err = _pip_install_try(python, primary)
    if code == 0:
        return

    blob = f"{out}\n{err}".lower()
    is_resolver_conflict = (
        "resolutionimpossible" in blob
        or "conflicting dependencies" in blob
        or "no matching distribution" in blob
    )

    if fallback_no_deps and is_resolver_conflict:
        warn("[!] dep conflict — retrying with --no-deps")
        code2, out2, err2 = _pip_install_try(python, primary + ["--no-deps"])
        if code2 == 0:
            return
        if out2:
            info(out2)
        if err2:
            print(err2, file=sys.stderr)
        raise SystemExit(code2)

    if out:
        info(out)
    if err:
        print(err, file=sys.stderr)
    raise SystemExit(code)


def copy_tree(src: Path, dst: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git",
        ".venv",
        "__pycache__",
        ".claude",
        "*.pyc",
    )
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignore)


def _wrapper_invocation(module: str) -> str:
    """Return the python expression that boots <module>'s CLI.

    `python -m <pkg>` only works when the package ships a __main__.py.
    ghunt and gitfive don't, so we call their installed console_scripts
    entry points directly. xsint has __main__.py and we control it,
    so '-m xsint' is fine.
    """
    if module == "gitfive":
        return '-c "from gitfive.lib.cli import parse_args; parse_args()"'
    if module == "ghunt":
        return '-c "import sys; from ghunt.ghunt import main; sys.exit(main() or 0)"'
    return f"-m {module}"


def write_unix_wrapper(path: Path, python: str, module: str) -> None:
    content = (
        "#!/usr/bin/env sh\n"
        f'exec "{python}" {_wrapper_invocation(module)} "$@"\n'
    )
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_windows_wrapper(path: Path, python: str, module: str) -> None:
    content = f'@echo off\r\n"{python}" {_wrapper_invocation(module)} %*\r\n'
    path.write_text(content, encoding="utf-8")


def default_install_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "xsint"
    return Path.home() / ".local" / "share" / "xsint"


def default_bin_dir(python: str) -> Path:
    if os.name == "nt":
        code, out, _ = run_capture([python, "-c", "import site; print(site.getuserbase())"])
        if code == 0 and out.strip():
            return Path(out.strip()) / "Scripts"
        return Path.home() / "AppData" / "Roaming" / "Python" / "Scripts"
    return Path.home() / ".local" / "bin"


def path_has_dir(target: Path) -> bool:
    raw = os.environ.get("PATH", "")
    sep = ";" if os.name == "nt" else ":"
    resolved_target = str(target.resolve())
    for entry in raw.split(sep):
        if not entry:
            continue
        try:
            if str(Path(entry).resolve()) == resolved_target:
                return True
        except OSError:
            continue
    return False


def suggested_shell_rc() -> str:
    shell = Path(os.environ.get("SHELL", "")).name.lower()
    if "zsh" in shell:
        return "~/.zshrc"
    return "~/.bashrc"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install xsint.")
    parser.add_argument(
        "--install-dir",
        default=os.environ.get("XSINT_INSTALL_DIR"),
        help="Install location for project files.",
    )
    parser.add_argument(
        "--bin-dir",
        default=os.environ.get("XSINT_BIN_DIR"),
        help="Install location for wrapper commands.",
    )
    parser.add_argument(
        "--skip-extras",
        action="store_true",
        default=os.environ.get("XSINT_SKIP_EXTRAS") == "1",
        help="Skip ghunt and gitfive (heavy deps; auto-set on iSH/Alpine).",
    )
    return parser.parse_args()


def _is_ish_or_alpine() -> bool:
    if Path("/proc/ish").exists():
        return True
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as f:
            if "ish" in f.read().lower():
                return True
    except OSError:
        pass
    return Path("/etc/alpine-release").exists()


def main() -> None:
    args = parse_args()
    python = find_python()

    py_ver = run_capture([python, "--version"])[1] or run_capture([python, "--version"])[2]
    section(f"Using: {python} ({py_ver})")
    info("")

    script_dir = Path(__file__).resolve().parent
    install_dir = Path(args.install_dir).expanduser() if args.install_dir else default_install_dir()
    bin_dir = Path(args.bin_dir).expanduser() if args.bin_dir else default_bin_dir(python)

    install_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    skip_extras = args.skip_extras or (_is_ish_or_alpine() and not os.environ.get("XSINT_WITH_EXTRAS"))
    if skip_extras:
        section("ghunt / gitfive will be skipped on this platform.")
        info("")

    ensure_pip(python)
    pip_install(python, ["--upgrade", "pip", "--quiet"])

    section(f"Copying xsint into {install_dir}...")
    copy_tree(script_dir, install_dir)
    info("")

    is_update = bool(os.environ.get("XSINT_UPDATE_MODE"))
    verb = "Updating" if is_update else "Installing"
    section(f"{verb} xsint and dependencies...")
    pip_install(python, ["-e", str(install_dir), "--quiet"])
    info("")

    if not skip_extras:
        # Install ghunt and gitfive in *separate* pip invocations. Combined,
        # pip's resolver sometimes can't satisfy both (each pins different
        # transitive versions). Splitting lets each get its own resolution;
        # on a hard conflict we fall back to --no-deps for that tool.
        section(f"{verb} gitfive...")
        pip_install_with_fallback(
            python, ["--upgrade", "gitfive"], fallback_no_deps=True,
        )
        info("")

        section(f"{verb} ghunt...")
        pip_install_with_fallback(
            python, ["--upgrade", "git+https://github.com/mxrch/ghunt"],
            fallback_no_deps=True,
        )
        info("")

    if os.name == "nt":
        write_windows_wrapper(bin_dir / "xsint.cmd", python, "xsint")
        success(f"Installed xsint wrapper to: {bin_dir / 'xsint.cmd'}")
        if not skip_extras:
            write_windows_wrapper(bin_dir / "ghunt.cmd", python, "ghunt")
            write_windows_wrapper(bin_dir / "gitfive.cmd", python, "gitfive")
            success(f"Installed ghunt wrapper to: {bin_dir / 'ghunt.cmd'}")
            success(f"Installed gitfive wrapper to: {bin_dir / 'gitfive.cmd'}")
    else:
        write_unix_wrapper(bin_dir / "xsint", python, "xsint")
        success(f"Installed xsint wrapper to: {bin_dir / 'xsint'}")
        if not skip_extras:
            write_unix_wrapper(bin_dir / "ghunt", python, "ghunt")
            write_unix_wrapper(bin_dir / "gitfive", python, "gitfive")
            success(f"Installed ghunt wrapper to: {bin_dir / 'ghunt'}")
            success(f"Installed gitfive wrapper to: {bin_dir / 'gitfive'}")
    info("")

    if not path_has_dir(bin_dir):
        if os.name == "nt":
            warn("Add this directory to your PATH, then reopen your terminal:")
            warn(f"  {bin_dir}")
        else:
            rc_file = suggested_shell_rc()
            warn("Run this now for the current shell:")
            warn(f"  export PATH=\"{bin_dir}:$PATH\"")
            warn("")
            warn(f"Persist it for new shells ({rc_file}):")
            warn(f"  echo 'export PATH=\"{bin_dir}:$PATH\"' >> {rc_file}")
        info("")

    # Don't double-print the completion line — install.sh prints its
    # own "Setup complete." / "Update complete." block right after we
    # exit, with the same install-dir / bin-dir / run details. Two of
    # them in a row was confusing.
    if not is_update:
        info("")
        success("Setup complete.")
        info(f"  install dir : {install_dir}")
        info(f"  bin dir     : {bin_dir}")
        if path_has_dir(bin_dir):
            info("  run         : xsint <target>")
        else:
            info(f"  run         : {bin_dir / 'xsint'} <target>")


if __name__ == "__main__":
    main()
