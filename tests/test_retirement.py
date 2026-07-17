#!/usr/bin/env python3
"""Offline regression tests for the frame-net retirement boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "audit" / "immutable-evidence.json"
FRAME_KEYS = {
    "spec",
    "kind",
    "stream_id",
    "seq",
    "utc",
    "payload",
    "payload_hash",
    "frame_hash",
    "prev",
    "prev_wave",
    "sig",
}
LEGACY_FRAMES = (
    "net/frames/740aa862e9dcc3d651f625355d638fb0a0a29caad35957e6dfc868216b06cb14.json",
    "twins/edge-demo/inbox/latest.json",
    "twins/edge-mac/inbox/latest.json",
)


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RetirementTests(unittest.TestCase):
    def test_authority_and_immutable_octet_pins(self) -> None:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(
            inventory["baseline_commit"],
            "a78a9c2aba06f9e788d735341b9ff7d2cace3189",
        )
        authority = inventory["normative_authority"]
        self.assertEqual(
            authority,
            {
                "repository": "kody-w/rapp-1",
                "commit": "6723c7add2aed36bb68992fc71a56b0a4bd5ad81",
                "path": "SPEC.md",
                "sha256": "6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b",
            },
        )
        self.assertEqual(inventory["trust_status"], "UNVERIFIED")
        self.assertFalse(inventory["active_authority"])
        self.assertEqual(len(inventory["artifacts"]), 10)
        self.assertEqual(
            {artifact["path"] for artifact in inventory["artifacts"]},
            {
                "events/frame-1.json",
                "keys/verify.json",
                "net/frames/740aa862e9dcc3d651f625355d638fb0a0a29caad35957e6dfc868216b06cb14.json",
                "net/latest.json",
                "twins/edge-demo/inbox/latest.json",
                "twins/edge-demo/state.json",
                "twins/edge-demo/twin.json",
                "twins/edge-mac/inbox/latest.json",
                "twins/edge-mac/state.json",
                "views/events.json",
            },
        )
        for artifact in inventory["artifacts"]:
            content = (ROOT / artifact["path"]).read_bytes()
            self.assertEqual(
                hashlib.sha256(content).hexdigest(),
                artifact["sha256"],
                artifact["path"],
            )

    def test_legacy_frames_are_evidence_not_rapp1(self) -> None:
        for relative_path in LEGACY_FRAMES:
            frame = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
            self.assertNotEqual(set(frame), FRAME_KEYS, relative_path)
            self.assertEqual(frame.get("spec"), "rapp-frame/2.0", relative_path)
            self.assertNotIn("sig", frame, relative_path)

    def test_python_tombstones_exit_without_side_effects(self) -> None:
        for relative_path in (
            "edge_node_agent.py",
            "scripts/event_store.py",
            "scripts/frame_loop.py",
        ):
            result = subprocess.run(
                [sys.executable, str(ROOT / relative_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(result.returncode, 78, relative_path)
            status = json.loads(result.stderr)
            self.assertEqual(status["status"], "retired", relative_path)
            self.assertFalse(status["active"], relative_path)

    def test_imported_legacy_entry_points_refuse(self) -> None:
        edge = load_module("retired_edge", "edge_node_agent.py")
        with self.assertRaises(edge.RetiredProtocolError):
            edge.EdgeNodeAgent().perform(action="sync")

        store = load_module("retired_store", "scripts/event_store.py")
        with self.assertRaises(store.RetiredEventStoreError):
            store.read_all_events(ROOT)
        with self.assertRaises(store.RetiredEventStoreError):
            store.append_event(ROOT, {})

    def test_active_python_has_no_network_secret_or_write_surface(self) -> None:
        banned = (
            "urllib",
            "urlopen",
            "api.github.com",
            "GITHUB_TOKEN",
            "FRAME_HEADS",
            "FRAME_NET_OWNER",
            "FRAME_NET_REPO",
            "mkstemp",
            "flock",
        )
        for relative_path in (
            "edge_node_agent.py",
            "scripts/event_store.py",
            "scripts/frame_loop.py",
        ):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, source, f"{relative_path}: {token}")

    def test_workflow_is_inert_and_has_no_unpinned_action(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "forge.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("if: ${{ false }}", workflow)
        self.assertIn("permissions: {}", workflow)
        for token in (
            "schedule:",
            "issues:",
            "contents: write",
            "issues: write",
            "uses:",
            "secrets.",
            "/main",
            "@main",
        ):
            self.assertNotIn(token, workflow)

    def test_no_archives_or_installer_were_added(self) -> None:
        archive_suffixes = {".egg", ".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz"}
        archives = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and path.suffix.lower() in archive_suffixes
        ]
        self.assertEqual(archives, [])
        self.assertFalse((ROOT / "install.sh").exists())
        self.assertFalse((ROOT / "installer").exists())


if __name__ == "__main__":
    unittest.main()
