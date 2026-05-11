#!/usr/bin/env python3
"""Unified push / clean / status for pym8 demos.

Replaces the per-task scripts that used to live as
tools/copy_demos_to_m8.py / clean_demos_from_m8.py / clean_local_demos.py.

Subcommands:

    sync.py                              # default = status
    sync.py push  [pattern] [-f] [--test]
    sync.py clean local  [pattern] [-f]
    sync.py clean remote [pattern] [-f] [--test]
    sync.py status [--test]

Local source:  tmp/demos/<category>/<flavor>/
Remote target: /Volumes/M8/Songs/pym8-demos/<category>-<flavor>/
                (or tmp/virtual-m8/ when --test is passed)

Per-item prompts (`y/N`) gate every destructive op when run on a TTY. On a
non-interactive stdin (piped, CI, agent-driven) the prompts auto-confirm —
the verb itself remains the deliberate choice. `-f` skips prompts entirely.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys
from typing import Optional


LOCAL_ROOT = pathlib.Path("tmp/demos")
M8_VOLUME = pathlib.Path("/Volumes/M8")
TEST_VOLUME = pathlib.Path("tmp/virtual-m8")
REMOTE_SUBPATH = pathlib.Path("Songs/pym8-demos")


def remote_root(test_mode: bool) -> pathlib.Path:
    base = TEST_VOLUME if test_mode else M8_VOLUME
    return base / REMOTE_SUBPATH


def m8_name(demo_dir: pathlib.Path) -> str:
    """tmp/demos/acid_303/sampler -> acid-303-sampler"""
    return "-".join(demo_dir.relative_to(LOCAL_ROOT).parts).replace("_", "-")


def find_local(pattern: Optional[str] = None) -> list[pathlib.Path]:
    """Demo directories under tmp/demos/ that contain at least one .m8s file."""
    if not LOCAL_ROOT.exists():
        return []
    seen = set()
    for m8s in LOCAL_ROOT.rglob("*.m8s"):
        seen.add(m8s.parent)
    dirs = sorted(seen)
    if pattern:
        pl = pattern.lower()
        dirs = [d for d in dirs if pl in m8_name(d).lower()]
    return dirs


def find_remote(test_mode: bool, pattern: Optional[str] = None) -> list[pathlib.Path]:
    root = remote_root(test_mode)
    if not root.exists():
        return []
    dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if pattern:
        pl = pattern.lower()
        dirs = [d for d in dirs if pl in d.name.lower()]
    return dirs


def confirm(prompt: str, force: bool) -> bool:
    """`-f` skips the prompt; a non-interactive stdin auto-confirms.

    The verb (push/clean) is the deliberate choice — the prompt is just
    per-item gating. Non-interactive runs (CI, agent-driven) can't answer
    input() so we proceed and log the implicit consent.
    """
    if force:
        return True
    if not sys.stdin.isatty():
        print(f"{prompt}y  (auto-confirmed: non-interactive)")
        return True
    return input(prompt).strip().lower() in ("y", "yes")


# ---- push ----

def _ensure_remote_root(test_mode: bool) -> None:
    """Make sure Songs/pym8-demos/ exists, but never invent /Volumes/M8 itself.

    Walking the path component-by-component avoids a TOCTOU race where the
    M8 unmounts mid-mkdir and macOS silently creates a regular folder at
    /Volumes/M8 that then shadows future mounts.
    """
    if test_mode:
        TEST_VOLUME.mkdir(parents=True, exist_ok=True)
    else:
        if not M8_VOLUME.exists():
            sys.exit(f"M8 not mounted at {M8_VOLUME}")
    base = TEST_VOLUME if test_mode else M8_VOLUME
    cur = base
    for part in REMOTE_SUBPATH.parts:
        cur = cur / part
        if not cur.exists():
            cur.mkdir()


def push(pattern: Optional[str], force: bool, test_mode: bool) -> None:
    demos = find_local(pattern)
    if not demos:
        print("no local demos found in tmp/demos")
        return

    _ensure_remote_root(test_mode)
    root = remote_root(test_mode)
    print(f"found {len(demos)} demo(s); target: {root}")
    copied = 0
    for demo_dir in demos:
        name = m8_name(demo_dir)
        target = root / name
        if target.exists():
            print(f"  {name} (already on device, skipping)")
            continue
        if not confirm(f"  copy {name}? [y/N] ", force):
            continue
        target.mkdir(parents=True, exist_ok=True)
        n_m8s = n_wav = 0
        for m8s in demo_dir.glob("*.m8s"):
            shutil.copy2(m8s, target / m8s.name)
            n_m8s += 1
        samples_src = demo_dir / "samples"
        if samples_src.exists():
            samples_dst = target / "samples"
            samples_dst.mkdir(exist_ok=True)
            for wav in samples_src.glob("*.wav"):
                shutil.copy2(wav, samples_dst / wav.name)
                n_wav += 1
        print(f"  {name} -> {n_m8s} .m8s, {n_wav} .wav")
        copied += 1
    print(f"\ncopied {copied} demo(s) to {root}")


# ---- clean ----

def clean_local(pattern: Optional[str], force: bool) -> None:
    demos = find_local(pattern)
    if not demos:
        print("no local demos found in tmp/demos")
        return
    print(f"found {len(demos)} demo(s):")
    removed = 0
    for d in demos:
        if not confirm(f"  remove {m8_name(d)}? [y/N] ", force):
            continue
        shutil.rmtree(d)
        removed += 1
    # Clean up empty category dirs left behind
    for category in sorted(LOCAL_ROOT.iterdir() if LOCAL_ROOT.exists() else []):
        if category.is_dir() and not any(category.iterdir()):
            category.rmdir()
    print(f"\nremoved {removed} of {len(demos)} demo(s).")


def clean_remote(pattern: Optional[str], force: bool, test_mode: bool) -> None:
    root = remote_root(test_mode)
    if not test_mode and not M8_VOLUME.exists():
        sys.exit(f"M8 not mounted at {M8_VOLUME}")
    if not root.exists():
        print(f"no pym8-demos on {'test volume' if test_mode else 'M8'}")
        return
    demos = find_remote(test_mode, pattern)
    if not demos:
        print(f"no remote demos in {root}")
        return
    print(f"found {len(demos)} demo(s):")
    removed = 0
    for d in demos:
        if not confirm(f"  remove {d.name}? [y/N] ", force):
            continue
        shutil.rmtree(d)
        removed += 1
    print(f"\nremoved {removed} of {len(demos)} demo(s).")


# ---- status ----

def status(test_mode: bool) -> None:
    local = find_local()
    local_names = {m8_name(d) for d in local}
    print(f"local  ({len(local_names):>2}): " + (", ".join(sorted(local_names)) or "—"))

    root = remote_root(test_mode)
    if not test_mode and not M8_VOLUME.exists():
        print(f"remote ( ?): M8 not mounted at {M8_VOLUME}")
        return
    if not root.exists():
        print(f"remote ( 0): {root} does not exist")
        return

    remote = find_remote(test_mode)
    remote_names = {d.name for d in remote}
    print(f"remote ({len(remote_names):>2}): " + (", ".join(sorted(remote_names)) or "—"))

    in_sync = sorted(local_names & remote_names)
    only_local = sorted(local_names - remote_names)
    only_remote = sorted(remote_names - local_names)
    print(f"  in sync     : {', '.join(in_sync) or '—'}")
    print(f"  local-only  : {', '.join(only_local) or '—'}"
          + ("  (run `push` to ship)" if only_local else ""))
    print(f"  remote-only : {', '.join(only_remote) or '—'}")


# ---- argparse ----

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    def add_pattern_and_force(p):
        p.add_argument("pattern", nargs="?", default=None,
                       help="filter demos by substring match on the M8 name")
        p.add_argument("-f", "--force", action="store_true",
                       help="skip per-item prompt")

    push_p = sub.add_parser("push", help="copy local demos to the M8")
    add_pattern_and_force(push_p)
    push_p.add_argument("--test", action="store_true",
                        help="use tmp/virtual-m8 instead of /Volumes/M8")

    clean_p = sub.add_parser("clean", help="remove local or remote demos")
    clean_sub = clean_p.add_subparsers(dest="clean_what", required=True)

    local_p = clean_sub.add_parser("local", help="remove tmp/demos/<demo>")
    add_pattern_and_force(local_p)

    remote_p = clean_sub.add_parser("remote", help="remove M8 /Songs/pym8-demos/<demo>")
    add_pattern_and_force(remote_p)
    remote_p.add_argument("--test", action="store_true",
                          help="operate on tmp/virtual-m8 instead of /Volumes/M8")

    status_p = sub.add_parser("status", help="compare local and remote demo sets")
    status_p.add_argument("--test", action="store_true",
                          help="check tmp/virtual-m8 instead of /Volumes/M8")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cmd = args.cmd or "status"

    if cmd == "push":
        push(args.pattern, args.force, args.test)
    elif cmd == "status":
        status(getattr(args, "test", False))
    elif cmd == "clean":
        if args.clean_what == "local":
            clean_local(args.pattern, args.force)
        else:
            clean_remote(args.pattern, args.force, args.test)


if __name__ == "__main__":
    main()
