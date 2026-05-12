#!/bin/sh
# POSIX sh — runs under bash, dash, BusyBox ash (iSH), zsh.
set -eu
APP=xsint
REPO=h1lw/xsint

MUTED='\033[0;2m'
RED='\033[0;31m'
ORANGE='\033[38;5;214m'
GREEN='\033[0;32m'
NC='\033[0m'

usage() {
    cat <<EOF
xsint installer

Usage: install.sh [options]

Options:
    -h, --help              Display this help message
    -v, --version <ref>     Install a specific tag, branch, or commit (default: main)
    -d, --dir <path>        Source install directory (default: ~/.local/share/xsint)
    -b, --bin-dir <path>    Wrapper bin directory (default: ~/.local/bin)
        --no-modify-path    Don't modify shell config files (.profile, .bashrc, etc.)
        --skip-extras       Skip ghunt and gitfive (auto-enabled on iSH/Alpine)
        --with-extras       Force-install ghunt and gitfive even on iSH/Alpine

Examples:
    curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | sh
    curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | sh -s -- --version v1.0.0
EOF
}

requested_ref="${VERSION:-main}"
no_modify_path=0
install_dir="${XSINT_INSTALL_DIR:-$HOME/.local/share/xsint}"
bin_dir="${XSINT_BIN_DIR:-$HOME/.local/bin}"
skip_extras=0
with_extras=0

print_message() {
    level=$1
    msg=$2
    color="$NC"
    case "$level" in
        info)    color="$NC" ;;
        warning) color="$ORANGE" ;;
        error)   color="$RED" ;;
        ok)      color="$GREEN" ;;
    esac
    printf '%b%b%b\n' "$color" "$msg" "$NC"
}

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -v|--version)
            [ $# -ge 2 ] || { print_message error "Error: --version requires a ref"; exit 1; }
            requested_ref="$2"; shift 2 ;;
        -d|--dir)
            [ $# -ge 2 ] || { print_message error "Error: --dir requires a path"; exit 1; }
            install_dir="$2"; shift 2 ;;
        -b|--bin-dir)
            [ $# -ge 2 ] || { print_message error "Error: --bin-dir requires a path"; exit 1; }
            bin_dir="$2"; shift 2 ;;
        --no-modify-path) no_modify_path=1; shift ;;
        --skip-extras)    skip_extras=1; shift ;;
        --with-extras)    with_extras=1; shift ;;
        *) print_message warning "Warning: unknown option '$1'" >&2; shift ;;
    esac
done

# In update mode (set by `xsint --update`) the user already has xsint
# working — skip the first-time framing and use "Updating ..." section
# headers instead of "Installing ...".
UPDATE_MODE="${XSINT_UPDATE_MODE:-}"
ACTION_VERB_PROG="Installing"
COMPLETION_MSG="Setup complete."
if [ -n "$UPDATE_MODE" ]; then
    ACTION_VERB_PROG="Updating"
    COMPLETION_MSG="Update complete."
fi

# ---------- 1. Platform detection (iSH / Alpine) ----------

detect_platform() {
    # iSH exposes /proc/ish and identifies itself in uname/proc/version.
    if [ -d /proc/ish ] || [ -e /proc/ish ]; then
        echo ish; return
    fi
    if [ -r /proc/version ] && grep -qi 'ish' /proc/version 2>/dev/null; then
        echo ish; return
    fi
    if command -v uname >/dev/null 2>&1 && uname -a 2>/dev/null | grep -qi 'ish'; then
        echo ish; return
    fi
    if [ -f /etc/alpine-release ]; then
        echo alpine; return
    fi
    echo other
}

PLATFORM=$(detect_platform)

# On iSH (and Alpine, since it shares the apk/musl story), skip the
# heavy extras by default — ghunt and gitfive pull in pydantic-core
# (Rust) and a long compile chain that's painful or impossible on
# emulated x86. xsint's modules guard the imports, so missing extras
# degrades gracefully.
if [ "$PLATFORM" = "ish" ] || [ "$PLATFORM" = "alpine" ]; then
    if [ "$with_extras" -eq 0 ] && [ "$skip_extras" -eq 0 ]; then
        skip_extras=1
        print_message info "${MUTED}Detected ${PLATFORM} — skipping ghunt/gitfive (override with --with-extras)${NC}"
    fi
fi

# Bootstrap apk system packages on iSH/Alpine. Needs root; iSH runs as
# root by default, on real Alpine we try sudo, otherwise warn.
apk_bootstrap() {
    pkgs="python3 py3-pip curl tar ca-certificates"
    # Build deps for aiohttp / cffi / cryptography wheels that may not
    # have musllinux/i686 binaries.
    build_pkgs="gcc musl-dev python3-dev libffi-dev openssl-dev make"

    sudo_cmd=""
    if [ "$(id -u 2>/dev/null || echo 1)" != "0" ]; then
        if command -v sudo >/dev/null 2>&1; then
            sudo_cmd="sudo"
        else
            print_message warning "Not root and no sudo — skipping apk bootstrap."
            print_message info "Run as root: apk add $pkgs $build_pkgs"
            return 0
        fi
    fi

    print_message info "${MUTED}Installing apk packages: $pkgs${NC}"
    $sudo_cmd apk add --no-cache $pkgs >/dev/null 2>&1 || \
        $sudo_cmd apk add --no-cache $pkgs

    print_message info "${MUTED}Installing build deps (for native wheels): $build_pkgs${NC}"
    $sudo_cmd apk add --no-cache $build_pkgs >/dev/null 2>&1 || \
        $sudo_cmd apk add --no-cache $build_pkgs
}

if [ "$PLATFORM" = "ish" ] || [ "$PLATFORM" = "alpine" ]; then
    if command -v apk >/dev/null 2>&1; then
        apk_bootstrap
    fi
fi

# ---------- 2. Detect a compatible Python (3.10–3.13) ----------

find_python() {
    for cand in python3.13 python3.12 python3.11 python3.10 python3 python; do
        command -v "$cand" >/dev/null 2>&1 || continue
        minor=$("$cand" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "")
        major=$("$cand" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "")
        case "$minor" in
            ''|*[!0-9]*) continue ;;
        esac
        if [ "$major" = "3" ] && [ "$minor" -ge 10 ] && [ "$minor" -le 13 ]; then
            echo "$cand"
            return 0
        fi
    done
    return 1
}

print_message info "${MUTED}Looking for Python 3.10–3.13...${NC}"
PYTHON=$(find_python) || PYTHON=""
if [ -z "$PYTHON" ]; then
    print_message error "[!] No compatible Python 3.10–3.13 interpreter found."
    print_message info  "    Install Python 3.10+ and retry."
    exit 1
fi
PYVER=$("$PYTHON" --version 2>&1)
print_message ok "${MUTED}Using:${NC} $PYTHON ${MUTED}($PYVER)${NC}"

# ---------- 3. Required tools ----------

for tool in curl tar; do
    command -v "$tool" >/dev/null 2>&1 || { print_message error "[!] '$tool' is required but not installed."; exit 1; }
done

# ---------- 4. Download source tarball ----------

ref_clean=${requested_ref#v}
case "$requested_ref" in
    main|master|*/*) tarball_url="https://github.com/$REPO/archive/refs/heads/$requested_ref.tar.gz" ;;
    v*|[0-9]*)       tarball_url="https://github.com/$REPO/archive/refs/tags/v${ref_clean}.tar.gz" ;;
    *)               tarball_url="https://github.com/$REPO/archive/$requested_ref.tar.gz" ;;
esac

# Verify URL exists.
http_status=$(curl -sI -o /dev/null -w "%{http_code}" "$tarball_url" || echo "000")
if [ "$http_status" != "200" ] && [ "$http_status" != "302" ]; then
    # Fall back to tag form for plain version numbers.
    case "$requested_ref" in
        [0-9]*)
            tarball_url="https://github.com/$REPO/archive/refs/tags/v${ref_clean}.tar.gz"
            http_status=$(curl -sI -o /dev/null -w "%{http_code}" "$tarball_url" || echo "000")
            ;;
    esac
fi
if [ "$http_status" != "200" ] && [ "$http_status" != "302" ]; then
    print_message error "[!] Could not resolve ref '$requested_ref' (HTTP $http_status)."
    print_message info  "    Available releases: https://github.com/$REPO/releases"
    exit 1
fi

tmp_dir="${TMPDIR:-/tmp}/xsint_install_$$"
mkdir -p "$tmp_dir"
trap 'rm -rf "$tmp_dir"' EXIT INT TERM

if [ -n "$UPDATE_MODE" ]; then
    print_message info "\n${MUTED}Fetching latest${NC} $APP ${MUTED}from${NC} $tarball_url"
else
    print_message info "\n${MUTED}Downloading${NC} $APP ${MUTED}from${NC} $tarball_url"
fi
curl -fsSL -o "$tmp_dir/src.tar.gz" "$tarball_url"

print_message info "${MUTED}Extracting...${NC}"
tar -xzf "$tmp_dir/src.tar.gz" -C "$tmp_dir"
src_root=$(find "$tmp_dir" -maxdepth 1 -mindepth 1 -type d | head -n1)
[ -d "$src_root" ] || { print_message error "[!] Extracted source not found"; exit 1; }

# ---------- 5. Run the Python installer ----------

print_message info "\n${MUTED}${ACTION_VERB_PROG} into${NC} $install_dir"
set -- "$src_root/installer.py" --install-dir "$install_dir" --bin-dir "$bin_dir"
if [ "$skip_extras" -eq 1 ]; then
    set -- "$@" --skip-extras
fi
"$PYTHON" "$@"

# ---------- 6. PATH wiring ----------

add_to_path() {
    config_file=$1
    cmd=$2
    if grep -Fxq "$cmd" "$config_file" 2>/dev/null; then
        print_message info "${MUTED}Already in${NC} $config_file"
    elif [ -w "$config_file" ]; then
        printf "\n# xsint\n%s\n" "$cmd" >> "$config_file"
        print_message ok "${MUTED}Added xsint to \$PATH in${NC} $config_file"
    else
        print_message warning "Manually add to $config_file (or similar):"
        print_message info "  $cmd"
    fi
}

case ":$PATH:" in
    *":$bin_dir:"*) path_already=1 ;;
    *)              path_already=0 ;;
esac

if [ "$no_modify_path" -ne 1 ] && [ "$path_already" -eq 0 ]; then
    XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
    shell_name=$(basename "${SHELL:-/bin/sh}")
    case "$shell_name" in
        fish)    configs="$HOME/.config/fish/config.fish" ;;
        zsh)     configs="${ZDOTDIR:-$HOME}/.zshrc ${ZDOTDIR:-$HOME}/.zshenv $XDG_CONFIG_HOME/zsh/.zshrc" ;;
        bash)    configs="$HOME/.bashrc $HOME/.bash_profile $HOME/.profile" ;;
        ash|sh)  configs="$HOME/.profile $HOME/.shinit" ;;
        *)       configs="$HOME/.profile $HOME/.bashrc" ;;
    esac

    config=""
    for f in $configs; do
        if [ -f "$f" ]; then
            config="$f"; break
        fi
    done

    # On iSH/Alpine ash, .profile usually doesn't exist yet — create it
    # so a fresh shell picks up the PATH change.
    if [ -z "$config" ]; then
        case "$shell_name" in
            ash|sh) config="$HOME/.profile"; : >> "$config" ;;
        esac
    fi

    if [ -z "$config" ]; then
        print_message warning "No shell config found. Add manually:"
        print_message info    "  export PATH=$bin_dir:\$PATH"
    else
        case "$shell_name" in
            fish) add_to_path "$config" "fish_add_path $bin_dir" ;;
            *)    add_to_path "$config" "export PATH=$bin_dir:\$PATH" ;;
        esac
    fi
fi

if [ -n "${GITHUB_ACTIONS:-}" ] && [ "${GITHUB_ACTIONS}" = "true" ]; then
    echo "$bin_dir" >> "${GITHUB_PATH:-/dev/null}"
    print_message info "${MUTED}Added${NC} $bin_dir ${MUTED}to \$GITHUB_PATH${NC}"
fi

# ---------- 7. Done ----------

echo
print_message ok "$COMPLETION_MSG"
printf '  %binstall dir :%b %s\n' "$MUTED" "$NC" "$install_dir"
printf '  %bbin dir     :%b %s\n' "$MUTED" "$NC" "$bin_dir"
case ":$PATH:" in
    *":$bin_dir:"*)
        printf '  %brun         :%b xsint <target>\n' "$MUTED" "$NC"
        ;;
    *)
        printf '  %brun         :%b %s/xsint <target>\n' "$MUTED" "$NC" "$bin_dir"
        printf '  %bor restart your shell to pick up the PATH change%b\n' "$MUTED" "$NC"
        ;;
esac
echo
if [ "$skip_extras" -eq 1 ]; then
    printf '%bghunt and gitfive were skipped on this platform.%b\n' "$MUTED" "$NC"
    printf '%bRerun with --with-extras to attempt them.%b\n' "$MUTED" "$NC"
    echo
fi
printf '%bOptional auth (only if you want those modules):%b\n' "$MUTED" "$NC"
if [ "$skip_extras" -ne 1 ]; then
    printf '  xsint --auth ghunt       %b# Google account lookup%b\n' "$MUTED" "$NC"
    printf '  xsint --auth gitfive     %b# GitHub email/profile%b\n' "$MUTED" "$NC"
fi
printf '  xsint --auth hibp <key>  %b# HaveIBeenPwned%b\n' "$MUTED" "$NC"
echo
printf '%bDocs: https://github.com/%s%b\n' "$MUTED" "$REPO" "$NC"
echo
