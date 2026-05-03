#!/usr/bin/env bash
# Promptix — Kali / Debian / Ubuntu installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/xM4skByt3z/promptix/main/install.sh | bash
#   PROMPTIX_REF=v0.1.0 bash install.sh
set -euo pipefail

REPO_URL="${PROMPTIX_REPO:-https://github.com/xM4skByt3z/promptix.git}"
REPO_REF="${PROMPTIX_REF:-main}"
REPO_DIR="${PROMPTIX_DIR:-$HOME/tools/promptix}"
PYTHON="${PYTHON:-python3}"
BIN_DIR="${PROMPTIX_BIN_DIR:-/usr/local/bin}"

c_info()  { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
c_ok()    { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
c_warn()  { printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2; }
c_err()   { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; }

SUDO=""
if [[ $EUID -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

c_info "Promptix installer"
c_info "Repo:   $REPO_URL ($REPO_REF)"
c_info "Target: $REPO_DIR"

# ---- system dependencies -----------------------------------------------------
if command -v apt-get >/dev/null 2>&1; then
    c_info "Installing system packages (python3, venv, pip, git)..."
    $SUDO apt-get update -qq
    $SUDO apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip git ca-certificates >/dev/null
elif command -v dnf >/dev/null 2>&1; then
    $SUDO dnf install -y python3 python3-pip git >/dev/null
elif command -v pacman >/dev/null 2>&1; then
    $SUDO pacman -Sy --noconfirm python python-pip git >/dev/null
else
    c_warn "Unknown package manager — make sure python3, pip, venv and git are installed."
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    c_err "python3 not found in PATH"; exit 1
fi

# ---- clone or update ---------------------------------------------------------
mkdir -p "$(dirname "$REPO_DIR")"
if [[ -d "$REPO_DIR/.git" ]]; then
    c_info "Updating existing clone..."
    git -C "$REPO_DIR" fetch --tags --prune origin
    git -C "$REPO_DIR" checkout "$REPO_REF"
    git -C "$REPO_DIR" pull --ff-only origin "$REPO_REF" || true
else
    c_info "Cloning..."
    git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$REPO_DIR" 2>/dev/null \
        || git clone "$REPO_URL" "$REPO_DIR"
    git -C "$REPO_DIR" checkout "$REPO_REF" 2>/dev/null || true
fi

cd "$REPO_DIR"

# ---- virtualenv + install ----------------------------------------------------
if [[ ! -d ".venv" ]]; then
    c_info "Creating virtualenv (.venv)..."
    "$PYTHON" -m venv .venv
fi

c_info "Upgrading pip..."
.venv/bin/python -m pip install --quiet --upgrade pip wheel

c_info "Installing promptix (editable)..."
.venv/bin/python -m pip install --quiet -e .

# ---- symlinks ----------------------------------------------------------------
if [[ -w "$BIN_DIR" ]] || [[ -n "$SUDO" ]]; then
    c_info "Linking CLI into $BIN_DIR ..."
    $SUDO ln -sf "$REPO_DIR/.venv/bin/promptix" "$BIN_DIR/promptix"
    $SUDO ln -sf "$REPO_DIR/.venv/bin/promptix" "$BIN_DIR/pix"
else
    c_warn "$BIN_DIR not writable; add this to your shell rc instead:"
    echo "    export PATH=\"$REPO_DIR/.venv/bin:\$PATH\""
fi

# ---- smoke test --------------------------------------------------------------
if "$REPO_DIR/.venv/bin/promptix" --help >/dev/null 2>&1; then
    c_ok "Installed successfully."
else
    c_err "Install finished but 'promptix --help' failed. Check the output above."
    exit 1
fi

cat <<'EOF'

[+] Try:
    promptix --help
    pix --help
    promptix --echo                          # offline demo
    promptix -u http://localhost:8080/v1     # local LLM API

EOF
