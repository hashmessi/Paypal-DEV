#!/usr/bin/env bash
# harness:managed — installed from ~/agent-harness/bin/verify.sh by harness-init.sh. Do not edit in a project:
# put project-specific checks in scripts/verify.d/*.sh (run in sorted order, each must exit 0).
#
# Single deterministic verification gate.  Usage: bash scripts/verify.sh [--tree-hash]
#   exit 0  every applicable check passed
#   exit 1  at least one check failed
#   exit 2  nothing to verify (no stack detected and no scripts/verify.d checks)
#
# Detects Node/TS, Python, Rust, Go at the repo root (or one directory deep when the root has no manifest).
# Runs only tools the repo configures; a configured tool that cannot run is a FAIL, never a silent skip.
# Guards (git repos): test integrity, unexplained suppressions, secrets — over the diff vs. the base ref.
#
# Environment (human-only overrides — agents must not set these on their own):
#   HARNESS_BASE=<ref>               diff base for guards (default: merge-base with origin/HEAD|main|master, else HEAD)
#   HARNESS_ALLOW_TEST_CHANGES=1     waive the test-integrity guard
#   HARNESS_ALLOW_SUPPRESSIONS=1     waive the suppression guard
#   VERIFY_SKIP=name,name            skip steps by name (reported as SKIP; result is never a clean PASS)

set -uo pipefail
export LC_ALL=C

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 1
GITDIR="$(git rev-parse --absolute-git-dir 2>/dev/null || true)"

tree_hash() {
  # Content hash of the whole working tree (tracked + untracked, minus ignored) without touching the real index.
  # verify-gate.mjs computes the same value the same way.
  local tmp="$GITDIR/harness/index.$$"
  mkdir -p "$GITDIR/harness"
  if [ -f "$GITDIR/index" ]; then cp "$GITDIR/index" "$tmp"; else rm -f "$tmp"; fi
  GIT_INDEX_FILE="$tmp" git add -A -- . >/dev/null 2>&1 && GIT_INDEX_FILE="$tmp" git write-tree
  local rc=$?
  rm -f "$tmp"
  return $rc
}

if [ "${1:-}" = "--tree-hash" ]; then
  [ -n "$GITDIR" ] || { echo "not a git repository" >&2; exit 1; }
  tree_hash; exit $?
fi

if [ -n "$GITDIR" ]; then LOGDIR="$GITDIR/harness/logs"; else LOGDIR="${TMPDIR:-/tmp}/harness-verify-$$"; fi
rm -rf "$LOGDIR"; mkdir -p "$LOGDIR"

R_NAME=(); R_STATUS=(); R_SECS=(); R_NOTE=()
STACK_CHECKS=0

record() { R_NAME+=("$1"); R_STATUS+=("$2"); R_SECS+=("$3"); R_NOTE+=("$4"); printf '[%s] %s (%ss)%s\n' "$2" "$1" "$3" "${4:+ — $4}"; }
is_skipped() { case ",${VERIFY_SKIP:-}," in *",$1,"*) return 0 ;; esac; return 1; }
logfile() { printf '%s/%s.log' "$LOGDIR" "$(printf '%s' "$1" | tr '/: ' '___')"; }

# run_step NAME DIR CMD... — runs CMD inside DIR, captures output, prints the tail on failure.
run_step() {
  local name="$1" dir="$2"; shift 2
  STACK_CHECKS=$((STACK_CHECKS + 1))
  if is_skipped "$name"; then record "$name" SKIP 0 "VERIFY_SKIP"; return; fi
  local log; log="$(logfile "$name")"
  local start=$SECONDS
  ( cd "$dir" && "$@" ) >"$log" 2>&1
  local rc=$? secs=$((SECONDS - start))
  if [ $rc -eq 0 ]; then record "$name" PASS "$secs" ""
  else
    record "$name" FAIL "$secs" "exit $rc, log: $log"
    echo "----- tail: $name -----"; tail -n 40 "$log"; echo "-----"
  fi
}
fail_step() { STACK_CHECKS=$((STACK_CHECKS + 1)); record "$1" FAIL 0 "$2"; }

# Directories holding a manifest: the root if it has one, otherwise first-level subdirectories that do.
find_dirs() {
  local d m found=0
  for m in "$@"; do [ -e "$m" ] && found=1; done
  if [ $found -eq 1 ]; then echo "."; return; fi
  for d in */; do
    d="${d%/}"
    case "$d" in node_modules|vendor|dist|build|target|venv|.venv|__pycache__|coverage) continue ;; esac
    for m in "$@"; do if [ -e "$d/$m" ]; then echo "$d"; break; fi; done
  done
}
label() { if [ "$1" = "." ]; then echo "$2"; else echo "$2[$1]"; fi; }

# ---------------------------------------------------------------- Node / TypeScript
verify_node() {
  local d="$1" L; L="$(label "$d" node)"
  if ! command -v node >/dev/null 2>&1; then fail_step "$L:toolchain" "node not found on PATH"; return; fi
  local pm=npm
  if [ -f "$d/pnpm-lock.yaml" ]; then pm=pnpm
  elif [ -f "$d/yarn.lock" ]; then pm=yarn
  elif [ -f "$d/bun.lockb" ] || [ -f "$d/bun.lock" ]; then pm=bun; fi
  if ! command -v "$pm" >/dev/null 2>&1; then fail_step "$L:toolchain" "$pm not found (lockfile requires it)"; return; fi

  local scripts
  scripts="$(cd "$d" && node -e '
    const p = JSON.parse(require("fs").readFileSync("package.json", "utf8"));
    const s = p.scripts || {};
    const deps = Object.keys(Object.assign({}, p.dependencies, p.devDependencies));
    for (const k of Object.keys(s)) console.log("script\t" + k + "\t" + s[k]);
    if (deps.length) console.log("hasdeps");')" || { fail_step "$L:package.json" "package.json is not valid JSON"; return; }
  if grep -qx hasdeps <<<"$scripts" && [ ! -d "$d/node_modules" ]; then
    fail_step "$L:deps" "node_modules missing — run '$pm install' in $d"; return
  fi
  has() { grep -q "^script	$1	" <<<"$scripts"; }
  first() { local n; for n in "$@"; do has "$n" && { echo "$n"; return 0; }; done; return 1; }

  local s
  if s="$(first typecheck type-check check-types tsc)"; then run_step "$L:typecheck" "$d" "$pm" run "$s"
  elif [ -f "$d/tsconfig.json" ] && [ -e "$d/node_modules/.bin/tsc" ]; then run_step "$L:typecheck" "$d" ./node_modules/.bin/tsc --noEmit
  elif [ -f "$d/tsconfig.json" ]; then fail_step "$L:typecheck" "tsconfig.json present but typescript is not installed"; fi
  if s="$(first lint)"; then run_step "$L:lint" "$d" "$pm" run "$s"; fi
  if s="$(first format:check fmt:check prettier:check)"; then run_step "$L:format" "$d" "$pm" run "$s"; fi
  if has test && ! grep -q '^script	test	.*no test specified' <<<"$scripts"; then
    run_step "$L:test" "$d" env CI=true "$pm" run test
  fi
  if s="$(first build)"; then run_step "$L:build" "$d" "$pm" run "$s"; fi
}

# ---------------------------------------------------------------- Python
pick_python() {
  local d="$1" c
  if [ -f "$d/uv.lock" ] && command -v uv >/dev/null 2>&1; then echo "uv run python"; return; fi
  if [ -f "$d/poetry.lock" ] && command -v poetry >/dev/null 2>&1; then echo "poetry run python"; return; fi
  for c in .venv/Scripts/python.exe .venv/bin/python venv/Scripts/python.exe venv/bin/python; do
    [ -x "$d/$c" ] && { echo "./$c"; return; }
  done
  for c in python3 python; do "$c" -c 'import sys' >/dev/null 2>&1 && { echo "$c"; return; }; done
  return 1
}
cfg_has() { local d="$1" pat="$2" f; for f in pyproject.toml setup.cfg tox.ini; do [ -f "$d/$f" ] && grep -qE "$pat" "$d/$f" && return 0; done; return 1; }

verify_python() {
  local d="$1" L py; L="$(label "$d" py)"
  if ! py="$(pick_python "$d")"; then fail_step "$L:toolchain" "no working python interpreter found"; return; fi
  # shellcheck disable=SC2206
  local PY=($py)
  if [ -f "$d/ruff.toml" ] || [ -f "$d/.ruff.toml" ] || cfg_has "$d" '^\[tool\.ruff'; then
    run_step "$L:ruff" "$d" "${PY[@]}" -m ruff check .
    if cfg_has "$d" '^\[tool\.ruff\.format\]'; then run_step "$L:ruff-format" "$d" "${PY[@]}" -m ruff format --check .; fi
  fi
  if [ -f "$d/.flake8" ] || cfg_has "$d" '^\[flake8\]'; then run_step "$L:flake8" "$d" "${PY[@]}" -m flake8; fi
  if cfg_has "$d" '^\[tool\.black\]'; then run_step "$L:black" "$d" "${PY[@]}" -m black --check .; fi
  if [ -f "$d/mypy.ini" ] || [ -f "$d/.mypy.ini" ] || cfg_has "$d" '^\[(tool\.)?mypy'; then run_step "$L:mypy" "$d" "${PY[@]}" -m mypy .; fi
  if [ -f "$d/pyrightconfig.json" ] || cfg_has "$d" '^\[tool\.pyright\]'; then
    if command -v pyright >/dev/null 2>&1; then run_step "$L:pyright" "$d" pyright
    else run_step "$L:pyright" "$d" "${PY[@]}" -m pyright; fi
  fi
  local has_tests=0
  if [ -f "$d/pytest.ini" ] || [ -f "$d/conftest.py" ] || [ -d "$d/tests" ] || [ -d "$d/test" ] || cfg_has "$d" '^\[(tool:pytest|tool\.pytest)'; then has_tests=1
  elif [ -n "$(find "$d" -maxdepth 3 \( -name node_modules -o -name .venv -o -name venv -o -name .git \) -prune -o \( -name 'test_*.py' -o -name '*_test.py' \) -print 2>/dev/null | head -n 1)" ]; then has_tests=1; fi
  if [ $has_tests -eq 1 ]; then run_step "$L:pytest" "$d" "${PY[@]}" -m pytest -q; fi
}

# ---------------------------------------------------------------- Rust / Go
verify_rust() {
  local d="$1" L; L="$(label "$d" rust)"
  if ! command -v cargo >/dev/null 2>&1; then fail_step "$L:toolchain" "cargo not found on PATH"; return; fi
  run_step "$L:fmt" "$d" cargo fmt --all -- --check
  run_step "$L:clippy" "$d" cargo clippy --all-targets --quiet
  run_step "$L:test" "$d" cargo test --quiet
}
verify_go() {
  local d="$1" L; L="$(label "$d" go)"
  if ! command -v go >/dev/null 2>&1; then fail_step "$L:toolchain" "go not found on PATH"; return; fi
  run_step "$L:gofmt" "$d" bash -c 'out="$(gofmt -l .)"; [ -z "$out" ] || { echo "unformatted:"; echo "$out"; exit 1; }'
  run_step "$L:vet" "$d" go vet ./...
  run_step "$L:test" "$d" go test ./...
  run_step "$L:build" "$d" go build ./...
}

# ---------------------------------------------------------------- Guards (diff vs base)
# Exported so awk reads it via ENVIRON: `awk -v` would unescape `\.` into "any character".
export TEST_PATH_RE='(^|/)(tests?|__tests__|specs?)/|[._-](test|spec)s?\.[A-Za-z0-9]+$|(^|/)test_[^/]*\.py$|_test\.(go|py|rs)$'
SKIP_RE='\b(it|test|describe|context|suite)\.(skip|only|todo)\b|(^|[^A-Za-z0-9_.$])(xit|xdescribe|xtest|fit|fdescribe)\(|@pytest\.mark\.(skip|skipif|xfail)\b|pytest\.skip\(|@unittest\.(skip|skipIf|skipUnless|expectedFailure)\b|unittest\.SkipTest|\bt\.(Skip|SkipNow|Skipf)\('
ASSERT_RE='\bassert|\bexpect\(|\.should\b|\bt\.(Error|Errorf|Fatal|Fatalf)\('
SUPP_RE='eslint-disable|@ts-ignore|@ts-nocheck|@ts-expect-error|#[[:space:]]*type:[[:space:]]*ignore|#[[:space:]]*noqa|#[[:space:]]*pyright:[[:space:]]*ignore|//[[:space:]]*nolint|#!?\[allow\(|@SuppressWarnings|biome-ignore'
JUSTIFIED_RE='[Rr][Ee][Aa][Ss][Oo][Nn]:| -- [A-Za-z]'
SECRET_FILE_RE='(^|/)\.env(\.[^/]*)?$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$|\.(pem|p12|pfx|keystore|jks)$'
SECRET_FILE_OK_RE='\.(example|sample|template|dist|defaults)$'
SECRET_NAMES=(private-key aws-access-key anthropic-key openai-key github-token slack-token google-api-key stripe-live-key jwt)
SECRET_RES=(
  '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'
  '(^|[^A-Z0-9])(AKIA|ASIA)[0-9A-Z]{16}([^A-Z0-9]|$)'
  '(^|[^A-Za-z0-9_-])sk-ant-[A-Za-z0-9_-]{20,}'
  '(^|[^A-Za-z0-9_-])sk-(proj-)?[A-Za-z0-9_-]{32,}'
  'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,}'
  'xox[abprs]-[A-Za-z0-9-]{10,}'
  'AIza[0-9A-Za-z_-]{35}'
  '(sk|rk)_live_[0-9A-Za-z]{20,}'
  'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
)
GENERIC_SECRET_RE='(password|passwd|secret|api_?key|access_?token|auth_?token|client_?secret)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'[:space:]]{12,}["'"'"']'
EXCLUDE_SPEC=(':(exclude)scripts/verify.sh' ':(exclude)*.lock' ':(exclude)package-lock.json' ':(exclude)pnpm-lock.yaml' ':(exclude)*.min.js' ':(exclude)*.svg')

resolve_base() {
  if [ -n "${HARNESS_BASE:-}" ]; then git rev-parse --verify -q "$HARNESS_BASE^{commit}"; return; fi
  if ! git rev-parse --verify -q HEAD >/dev/null; then echo 4b825dc642cb6eb9a060e54bf8d69288fbee4904; return; fi  # unborn: empty tree
  local r
  for r in origin/HEAD origin/main origin/master main master; do
    if git rev-parse --verify -q "$r" >/dev/null; then git merge-base HEAD "$r" 2>/dev/null && return; fi
  done
  git rev-parse HEAD
}

# Emits "path<TAB>+|-<TAB>line" for every added/removed line vs base, plus all lines of untracked text files.
collect_changes() {
  local base="$1"
  git diff --no-color --no-ext-diff -U0 "$base" -- . "${EXCLUDE_SPEC[@]}" | awk '
    /^diff --git / { hdr = 1; next }
    hdr && /^\+\+\+ / { f = substr($0, 5); sub(/^b\//, "", f); next }
    hdr && /^@@/ { hdr = 0; next }
    hdr { next }
    /^@@/ { next }
    /^\+/ { print f "\t+\t" substr($0, 2); next }
    /^-/  { print f "\t-\t" substr($0, 2); next }'
  git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
    case "$f" in scripts/verify.sh) continue ;; esac
    [ -f "$f" ] || continue
    [ "$(wc -c <"$f")" -le 1048576 ] || continue
    grep -Iq . "$f" 2>/dev/null || continue   # skip binary/empty
    awk -v f="$f" '{ sub(/\r$/, ""); print f "\t+\t" $0 }' "$f"
  done
}

guard_result() { # name status-if-violations violations-file override-var
  local name="$1" file="$2" override="${3:-}"
  if is_skipped "$name"; then record "$name" SKIP 0 "VERIFY_SKIP"; return; fi
  if [ ! -s "$file" ]; then record "$name" PASS 0 ""; return; fi
  if [ -n "$override" ] && [ "${!override:-}" = "1" ]; then
    record "$name" WAIVED 0 "$override=1 (human override)"; sed 's/^/    /' "$file"; return
  fi
  record "$name" FAIL 0 "see below${override:+ (human-only override: $override=1)}"
  sed 's/^/    /' "$file"
}

run_guards() {
  local base; base="$(resolve_base)" || { record "guards" FAIL 0 "cannot resolve base ref '${HARNESS_BASE:-}'"; return; }
  echo "guards: diff base $(git rev-parse --short "$base" 2>/dev/null || echo "$base")"
  local changes="$LOGDIR/changes.tsv" v
  collect_changes "$base" >"$changes"

  # test integrity
  v="$LOGDIR/guard-tests.txt"; : >"$v"
  git diff --name-status -M --diff-filter=D "$base" -- . | cut -f2- | grep -E "$TEST_PATH_RE" | sed 's/^/deleted test file: /' >>"$v"
  awk -F'\t' '$2 == "+" && $1 ~ ENVIRON["TEST_PATH_RE"]' "$changes" | grep -E "$SKIP_RE" | awk -F'\t' '{ print "skip/focus marker added: " $1 ": " $3 }' >>"$v"
  awk -F'\t' '$2 == "+" && $1 ~ /\.rs$/' "$changes" | grep -E '#\[ignore' | awk -F'\t' '{ print "ignored test added: " $1 }' >>"$v"
  local added removed
  added="$(awk -F'\t' '$2 == "+" && $1 ~ ENVIRON["TEST_PATH_RE"]' "$changes" | cut -f3- | grep -cE "$ASSERT_RE")"
  removed="$(awk -F'\t' '$2 == "-" && $1 ~ ENVIRON["TEST_PATH_RE"]' "$changes" | cut -f3- | grep -cE "$ASSERT_RE")"
  if [ "${removed:-0}" -gt "${added:-0}" ]; then echo "net assertions removed from test files: -$removed / +$added" >>"$v"; fi
  guard_result "guard:test-integrity" "$v" HARNESS_ALLOW_TEST_CHANGES

  # suppressions without a same-line justification
  v="$LOGDIR/guard-suppressions.txt"
  awk -F'\t' '$2 == "+" && $1 !~ /\.(md|mdx|txt|rst)$/' "$changes" | grep -E "$SUPP_RE" | grep -vE "$JUSTIFIED_RE" \
    | awk -F'\t' '{ print "unexplained suppression: " $1 ": " $3 }' >"$v"
  guard_result "guard:suppressions" "$v" HARNESS_ALLOW_SUPPRESSIONS

  # secrets — report file + rule only, never the matched value
  v="$LOGDIR/guard-secrets.txt"; : >"$v"
  local plus="$LOGDIR/added.tsv" i
  awk -F'\t' '$2 == "+"' "$changes" | grep -v 'harness:allow-secret' >"$plus"
  for i in "${!SECRET_NAMES[@]}"; do
    grep -E -- "${SECRET_RES[$i]}" "$plus" | cut -f1 | sort -u | sed "s/^/possible ${SECRET_NAMES[$i]}: /" >>"$v"
  done
  awk -F'\t' '$1 !~ ENVIRON["TEST_PATH_RE"]' "$plus" | grep -iE -- "$GENERIC_SECRET_RE" | cut -f1 | sort -u | sed 's/^/possible hardcoded credential: /' >>"$v"
  { git diff --name-only --diff-filter=A "$base" -- .; git ls-files --others --exclude-standard; } | sort -u \
    | grep -E "$SECRET_FILE_RE" | grep -vE "$SECRET_FILE_OK_RE" | sed 's/^/secret-bearing file not ignored: /' >>"$v"
  guard_result "guard:secrets" "$v"
}

# ---------------------------------------------------------------- main
echo "verify: $ROOT"
while IFS= read -r d; do verify_node "$d"; done < <(find_dirs package.json)
while IFS= read -r d; do verify_python "$d"; done < <(find_dirs pyproject.toml setup.py setup.cfg requirements.txt)
while IFS= read -r d; do verify_rust "$d"; done < <(find_dirs Cargo.toml)
while IFS= read -r d; do verify_go "$d"; done < <(find_dirs go.mod)

if [ -d scripts/verify.d ]; then
  for f in scripts/verify.d/*.sh; do [ -f "$f" ] && run_step "custom:$(basename "$f" .sh)" . bash "$f"; done
fi

if [ -n "$GITDIR" ]; then run_guards; else echo "guards: skipped (not a git repository)"; fi

pass=0 fail=0 skip=0 waived=0
for s in ${R_STATUS[@]+"${R_STATUS[@]}"}; do
  case "$s" in PASS) pass=$((pass + 1)) ;; FAIL) fail=$((fail + 1)) ;; SKIP) skip=$((skip + 1)) ;; WAIVED) waived=$((waived + 1)) ;; esac
done

echo
echo "==================== verify summary ===================="
for i in ${R_NAME[@]+"${!R_NAME[@]}"}; do printf '%-6s %-32s %4ss\n' "${R_STATUS[$i]}" "${R_NAME[$i]}" "${R_SECS[$i]}"; done
echo "logs: $LOGDIR"

if [ $fail -gt 0 ]; then
  echo "RESULT: FAIL ($fail failed, $pass passed, $skip skipped, $waived waived)"; exit 1
fi
if [ $STACK_CHECKS -eq 0 ]; then
  echo "RESULT: NO-CHECKS — no stack detected and no scripts/verify.d/*.sh. Add a project check; this is not a pass."
  exit 2
fi
if [ -n "$GITDIR" ] && [ $skip -eq 0 ] && [ $waived -eq 0 ]; then
  tree_hash >"$GITDIR/harness/verify-stamp" 2>/dev/null || rm -f "$GITDIR/harness/verify-stamp"
fi
if [ $skip -gt 0 ] || [ $waived -gt 0 ]; then
  echo "RESULT: PASS WITH EXCEPTIONS ($pass passed, $skip skipped, $waived waived) — report these as unverified"
else
  echo "RESULT: PASS ($pass passed)"
fi
exit 0
