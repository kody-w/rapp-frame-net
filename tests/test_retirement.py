#!/usr/bin/env python3
"""Offline acceptance tests for the frame-net retirement boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "a78a9c2aba06f9e788d735341b9ff7d2cace3189"
INVENTORY = ROOT / "audit" / "immutable-evidence.json"
CLASSIFICATION = ROOT / "audit" / "tracked-path-classification.json"
OWNER_INPUTS = ROOT / "audit" / "owner-decommission-inputs.json"
MUTABLE_POINTER = {
    "path": "net/latest.json",
    "baseline_blob_sha1": "0d135be578b9530b36033d134f6f8d18cd790ba7",
    "sha256": "89b7e44d40e9e3de625be27a069600af4c94f974122e4c609230ec0e98cee4e7",
}
IMMUTABLE_PINS = {
    "events/frame-1.json": (
        "b4fcefae3579bb04c00540c6002cd56f76f1d053",
        "809e00ce7640b30bedafc82f8441cebe0d55e3ec5bc373c8639018c8b1c95add",
    ),
    "keys/verify.json": (
        "8f0677b9f4820b387dff4dc9f70e545103698e2a",
        "b564167c871f9ca6a0d73b505203137a452ea321379fcae100a8ae5dafefb94c",
    ),
    "net/frames/740aa862e9dcc3d651f625355d638fb0a0a29caad35957e6dfc868216b06cb14.json": (
        "7db10e6e92cbf04878d9018281ca88446b3bbf4a",
        "e50ffed130aa8c1ba1a8dca3430bae01b68a304f35228cfb8fab2716bdef69da",
    ),
    "twins/edge-demo/inbox/latest.json": (
        "7f72ff54b0b68cf64b72a3566aee6bf9c1dc7175",
        "85da1534a6a0ff3000cd5a011bc63de32b659801044ac2d5ec6384dd073e824a",
    ),
    "twins/edge-demo/state.json": (
        "64dc53af792c99ce5bed2a8d9ba8802bc65e9090",
        "e089f186f66f6d7d5b5075a625bcfc8c9bdf548befed7ac545307ecb82a51a9f",
    ),
    "twins/edge-demo/twin.json": (
        "1f4d56fd2d9952d10bbe2d994b3167c00da23b6c",
        "9cd2f78c567ac2f42ecfbc0fcabfa44de660d06619a4258a1a416f55c57df9a6",
    ),
    "twins/edge-mac/inbox/latest.json": (
        "471e18301743bf0668431a0613ec665aa7ab3302",
        "290e8ec2caf988614bd5e75d86e479a41654e5df8d7009644e41aade4393334c",
    ),
    "twins/edge-mac/state.json": (
        "86ed97fa6c91ceea1a812652011cb70cace712f9",
        "eb9a27700b755ab1be8b1bd4b82fc74a8459d0b21b220acf71c67593fd22db43",
    ),
    "views/events.json": (
        "ac1f83bd4f6d19987d71fa2f366eb1095d151cd3",
        "b32d730a166d165c1fe021be52250335c5043935f4eab5a783af10b4e20dde29",
    ),
}
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
OWNER_INPUT_KEYS = {
    "legacy_token_revocation_evidence",
    "legacy_agent_process_stop_evidence",
    "legacy_scheduler_stop_evidence",
    "issues_write_plane_disabled_evidence",
    "repository_metadata_retired_evidence",
    "mirror_and_cdn_advertisement_retirement_evidence",
    "cdn_cache_invalidation_evidence",
    "reviewed_consumer_migration_target",
    "consumer_migration_acceptance_evidence",
    "owner_decommission_acceptance",
}


def git_result(*args: str, input_bytes: bytes | None = None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        input=input_bytes,
        capture_output=True,
        check=False,
    )


def git_bytes(*args: str) -> bytes:
    result = git_result(*args)
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def git_blob_id(content: bytes) -> str:
    result = git_result("hash-object", "--stdin", input_bytes=content)
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout.decode("ascii").strip()


def nul_paths(raw: bytes) -> set[str]:
    return {part.decode("utf-8") for part in raw.split(b"\0") if part}


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def immutable_errors(
    path: str, manifest_record: dict[str, object], current_bytes: bytes | None = None
) -> list[str]:
    expected_blob, expected_sha = IMMUTABLE_PINS[path]
    resolved_blob = git_text("rev-parse", f"{BASELINE}:{path}")
    baseline_bytes = git_bytes("cat-file", "blob", resolved_blob)
    baseline_via_ref = git_bytes("show", f"{BASELINE}:{path}")
    current = (ROOT / path).read_bytes() if current_bytes is None else current_bytes
    errors: list[str] = []
    if manifest_record.get("baseline_blob_sha1") != expected_blob:
        errors.append("manifest blob differs from independent pin")
    if manifest_record.get("sha256") != expected_sha:
        errors.append("manifest sha256 differs from independent pin")
    if resolved_blob != expected_blob:
        errors.append("resolved baseline blob differs from independent pin")
    if baseline_via_ref != baseline_bytes:
        errors.append("baseline ref bytes differ from resolved blob bytes")
    if hashlib.sha256(baseline_bytes).hexdigest() != expected_sha:
        errors.append("resolved baseline bytes differ from independent sha256 pin")
    if current != baseline_bytes:
        errors.append("current bytes differ from pinned baseline bytes")
    if git_blob_id(current) != expected_blob:
        errors.append("current Git blob id differs from pinned baseline blob")
    return errors


def classification_errors(
    tracked_paths: set[str], records: list[dict[str, object]]
) -> list[str]:
    paths = [record.get("path") for record in records]
    classified = {path for path in paths if isinstance(path, str)}
    errors: list[str] = []
    if len(paths) != len(classified):
        errors.append("duplicate or non-string classification path")
    missing = tracked_paths - classified
    extra = classified - tracked_paths
    if missing:
        errors.append("unclassified tracked paths: " + ",".join(sorted(missing)))
    if extra:
        errors.append("classification paths not tracked: " + ",".join(sorted(extra)))
    for record in records:
        if set(record) != {"path", "origin", "classification", "rationale"}:
            errors.append(f"invalid classification shape: {record.get('path')}")
        if not all(
            isinstance(record.get(field), str) and record[field]
            for field in ("path", "origin", "classification", "rationale")
        ):
            errors.append(f"empty classification value: {record.get('path')}")
    return errors


class RetirementTests(unittest.TestCase):
    def test_baseline_and_immutable_manifest_against_independent_pins(self) -> None:
        self.assertEqual(git_text("rev-parse", f"{BASELINE}^{{commit}}"), BASELINE)
        self.assertEqual(git_text("cat-file", "-t", BASELINE), "commit")
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(inventory["baseline_commit"], BASELINE)
        self.assertEqual(
            inventory["normative_authority"],
            {
                "repository": "kody-w/rapp-1",
                "commit": "6723c7add2aed36bb68992fc71a56b0a4bd5ad81",
                "path": "SPEC.md",
                "sha256": "6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b",
            },
        )
        self.assertEqual(inventory["trust_status"], "UNVERIFIED")
        self.assertFalse(inventory["active_authority"])
        records = {item["path"]: item for item in inventory["artifacts"]}
        self.assertEqual(set(records), set(IMMUTABLE_PINS))
        for path, record in records.items():
            self.assertEqual(immutable_errors(path, record), [], path)

    def test_updating_blob_and_manifest_together_still_fails(self) -> None:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        record = dict(inventory["artifacts"][0])
        path = str(record["path"])
        baseline = git_bytes("show", f"{BASELINE}:{path}")
        tampered = baseline + b"\nco-tamper"
        record["baseline_blob_sha1"] = git_blob_id(tampered)
        record["sha256"] = hashlib.sha256(tampered).hexdigest()
        errors = immutable_errors(path, record, current_bytes=tampered)
        self.assertIn("manifest blob differs from independent pin", errors)
        self.assertIn("manifest sha256 differs from independent pin", errors)
        self.assertIn("current bytes differ from pinned baseline bytes", errors)
        self.assertIn("current Git blob id differs from pinned baseline blob", errors)

    def test_exact_inventory_rejects_unclassified_additions(self) -> None:
        document = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
        self.assertEqual(document["baseline_commit"], BASELINE)
        tracked = nul_paths(git_bytes("ls-files", "-z"))
        baseline = nul_paths(git_bytes("ls-tree", "-r", "-z", "--name-only", BASELINE))
        records = document["paths"]
        self.assertEqual(classification_errors(tracked, records), [])
        by_path = {record["path"]: record for record in records}
        for path in tracked:
            expected_origin = "baseline" if path in baseline else "added"
            self.assertEqual(by_path[path]["origin"], expected_origin, path)
        retired = {item["path"] for item in document["retired_baseline_paths"]}
        self.assertEqual(baseline - tracked, retired)
        self.assertEqual(retired, {"net/latest.json"})
        simulated = classification_errors(tracked | {"unreviewed.bin"}, records)
        self.assertTrue(
            any("unclassified tracked paths: unreviewed.bin" in error for error in simulated)
        )

    def test_mutable_head_absent_now_and_preserved_at_baseline(self) -> None:
        self.assertFalse((ROOT / MUTABLE_POINTER["path"]).exists())
        self.assertEqual(
            git_text("rev-parse", f"{BASELINE}:{MUTABLE_POINTER['path']}"),
            MUTABLE_POINTER["baseline_blob_sha1"],
        )
        baseline = git_bytes("show", f"{BASELINE}:{MUTABLE_POINTER['path']}")
        self.assertEqual(
            hashlib.sha256(baseline).hexdigest(), MUTABLE_POINTER["sha256"]
        )
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.assertEqual(inventory["retired_mutable_live_paths"], [
            {
                "path": "net/latest.json",
                "baseline_blob_sha1": MUTABLE_POINTER["baseline_blob_sha1"],
                "sha256": MUTABLE_POINTER["sha256"],
                "historical_ref": f"{BASELINE}:net/latest.json",
                "current_disposition": "absent-current-tree",
                "classification": "legacy mutable head pointer; historical evidence but not an immutable content-addressed artifact",
            }
        ])

    def test_owner_external_acceptance_blocked_on_null_inputs(self) -> None:
        document = json.loads(OWNER_INPUTS.read_text(encoding="utf-8"))
        values = document["owner_inputs"]
        self.assertEqual(set(values), OWNER_INPUT_KEYS)
        self.assertTrue(all(value is None for value in values.values()))
        self.assertEqual(document["acceptance_status"], "BLOCKED_NULL_OWNER_INPUTS")
        self.assertFalse(document["decommission_accepted"])
        criteria = document["external_acceptance_criteria"]
        self.assertEqual(
            {criterion["owner_input"] for criterion in criteria}, OWNER_INPUT_KEYS
        )
        self.assertEqual(
            {criterion["id"] for criterion in criteria},
            {f"EXT-{number:02d}" for number in range(1, 11)},
        )
        self.assertFalse(all(value is not None for value in values.values()))

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
