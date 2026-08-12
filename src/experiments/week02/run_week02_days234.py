#!/usr/bin/env python3
"""Execute Week 2 Day 2-4 on the Habitat host and recover all evidence.

Credentials are read only from VM_PASS in the current process environment. The
password is never written to disk, included in commands, or printed.
"""

from __future__ import annotations

import json
import os
import shlex
import socket
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


REPO = Path(__file__).resolve().parents[3]
EXPERIMENTS = REPO / "src" / "experiments" / "week02"
RESULTS = REPO / "src" / "results" / "week02"

import paramiko


HOST = os.environ.get("VM_HOST", "10.190.20.110")
USER = os.environ.get("VM_USER", "ubuntu")
PASSWORD = os.environ.get("VM_PASS")
PORT = int(os.environ.get("VM_PORT", "22"))
BIND = os.environ.get("VM_BIND", "10.176.167.215")
RUN_ID = os.environ.get("WEEK02_RUN_ID") or datetime.now(
    timezone.utc
).strftime("%Y%m%dT%H%M%SZ")

UPLOAD_FILES = (
    "preflight.sh",
    "shortest_path_follower.py",
    "run_shortest_path.sh",
    "run_tiny_ppo.sh",
)


def connect() -> paramiko.SSHClient:
    if not PASSWORD:
        raise RuntimeError(
            "VM_PASS is required in the current process environment; it is not "
            "read from files or command-line arguments."
        )

    sock = None
    if BIND:
        sock = socket.create_connection(
            (HOST, PORT),
            timeout=20,
            source_address=(BIND, 0),
        )

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    if known_hosts.exists():
        client.load_host_keys(str(known_hosts))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        hostname=HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        auth_timeout=20,
        banner_timeout=20,
        sock=sock,
    )
    return client


def mkdir_p(sftp: paramiko.SFTPClient, remote_path: str) -> None:
    current = ""
    for part in PurePosixPath(remote_path).parts:
        if part == "/":
            current = "/"
            continue
        current = f"{current.rstrip('/')}/{part}"
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def run_remote(client: paramiko.SSHClient, label: str, command: str) -> int:
    print(f"\n===== {label} =====", flush=True)
    transport = client.get_transport()
    if transport is None or not transport.is_active():
        raise RuntimeError("SSH transport is not active")

    channel = transport.open_session()
    channel.get_pty(width=160, height=48)
    channel.set_combine_stderr(True)
    channel.exec_command(f"bash -lc {shlex.quote(command)}")

    pending = b""
    while True:
        if channel.recv_ready():
            pending += channel.recv(65536)
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                print(line.decode("utf-8", errors="replace"), flush=True)
        elif channel.exit_status_ready():
            break
        else:
            time.sleep(0.05)

    while channel.recv_ready():
        pending += channel.recv(65536)
    if pending:
        print(pending.decode("utf-8", errors="replace"), end="", flush=True)

    exit_code = channel.recv_exit_status()
    print(f"===== {label} exit={exit_code} =====", flush=True)
    return exit_code


def safe_extract(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    destination_resolved = destination.resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if target != destination_resolved and destination_resolved not in target.parents:
                raise RuntimeError(f"Unsafe archive member: {member.name}")
        archive.extractall(destination, filter="data")


def activation_prefix() -> str:
    return r"""
set -euo pipefail
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
eval "$("$HOME/.local/bin/micromamba" shell hook -s bash)"
micromamba activate habitat
export HABITAT_ROOT="$HOME/habitat-lab"
""".strip()


def main() -> int:
    missing = [name for name in UPLOAD_FILES if not (EXPERIMENTS / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing local experiment files: {missing}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    local_destination = RESULTS / f"remote_{RUN_ID}"
    local_archive = RESULTS / f"remote_{RUN_ID}.tar.gz"
    if local_destination.exists() or local_archive.exists():
        raise FileExistsError(f"Run id already exists locally: {RUN_ID}")

    client = connect()
    stage_results: dict[str, int | str] = {
        "run_id": RUN_ID,
        "host": HOST,
        "user": USER,
        "bind": BIND,
    }
    remote_archive = ""
    remote_results = ""

    try:
        sftp = client.open_sftp()
        remote_home = sftp.normalize(".")
        remote_scripts = f"{remote_home}/week02_codex_{RUN_ID}/scripts"
        remote_results_candidate = f"{remote_home}/week02_codex_{RUN_ID}/results"
        mkdir_p(sftp, remote_scripts)
        mkdir_p(sftp, remote_results_candidate)
        remote_results = remote_results_candidate
        remote_archive = f"{remote_home}/week02_codex_{RUN_ID}.tar.gz"
        for name in UPLOAD_FILES:
            local_path = EXPERIMENTS / name
            remote_path = f"{remote_scripts}/{name}"
            print(f"upload {local_path} -> {remote_path}", flush=True)
            sftp.put(str(local_path), remote_path)
            sftp.chmod(remote_path, 0o700)
        sftp.close()

        prefix = activation_prefix()
        stages = (
            (
                "day2_preflight",
                f"{prefix}\n"
                f"bash {shlex.quote(remote_scripts + '/preflight.sh')} "
                f"{shlex.quote(remote_results + '/preflight')}",
            ),
            (
                "day3_shortest_path",
                f"{prefix}\n"
                f"bash {shlex.quote(remote_scripts + '/run_shortest_path.sh')} "
                f"{shlex.quote(remote_results + '/shortest_path')}",
            ),
            (
                "day4_tiny_ppo",
                f"{prefix}\n"
                "export SEED=100 TOTAL_STEPS=1000\n"
                f"bash {shlex.quote(remote_scripts + '/run_tiny_ppo.sh')} "
                f"{shlex.quote(remote_results + '/tiny_ppo_seed100_1000')}",
            ),
        )

        for label, command in stages:
            exit_code = run_remote(client, label, command)
            stage_results[label] = exit_code
            if exit_code != 0:
                break
    finally:
        if remote_archive and remote_results:
            archive_command = (
                "set -euo pipefail; "
                f"tar -C {shlex.quote(remote_results)} -czf "
                f"{shlex.quote(remote_archive)} ."
            )
            archive_exit = run_remote(client, "archive_evidence", archive_command)
            stage_results["archive_evidence"] = archive_exit
            if archive_exit == 0:
                sftp = client.open_sftp()
                sftp.get(remote_archive, str(local_archive))
                sftp.close()
        client.close()

    if local_archive.exists():
        safe_extract(local_archive, local_destination)
        (local_destination / "orchestration_summary.json").write_text(
            json.dumps(stage_results, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    required = ("day2_preflight", "day3_shortest_path", "day4_tiny_ppo")
    passed = all(stage_results.get(label) == 0 for label in required)
    print(json.dumps(stage_results, indent=2, sort_keys=True), flush=True)
    print(f"local_evidence={local_destination}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
