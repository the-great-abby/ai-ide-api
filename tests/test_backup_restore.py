import os
import subprocess
import sys
import time
import uuid
import requests
import pytest

API_URL = os.environ.get("API_URL", "http://api:9103")
MAKE = ["make", "-f", "Makefile.ai"]
BACKUP_RESTORE_PHASE = os.environ.get("BACKUP_RESTORE_PHASE", "setup")

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_BACKUP_RESTORE_TEST") != "1",
    reason="Set RUN_BACKUP_RESTORE_TEST=1 to run destructive backup/restore test."
)

def wait_for_api():
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/env", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("API did not come up in time")

def test_backup_nuke_restore_cycle():
    unique = str(uuid.uuid4())
    if BACKUP_RESTORE_PHASE == "setup":
        # 1. Create unique test data in rulesdb and memorydb
        rule_payload = {
            "rule_type": "backup_restore_test",
            "description": f"Test rule {unique}",
            "diff": f"# Rule: BackupRestore\n## Description\nTest {unique}",
            "submitted_by": "backup-tester",
            "user_story": f"Backup/restore test {unique}"
        }
        r = requests.post(f"{API_URL}/propose-rule-change", json=rule_payload)
        assert r.status_code == 200
        proposal_id = r.json()["id"]
        r2 = requests.post(f"{API_URL}/approve-rule-change/{proposal_id}")
        assert r2.status_code == 200
        # Create a node (embedding is now generated server-side)
        node_payload = {
            "namespace": f"backupns-{unique}",
            "content": f"Backup node {unique}",
            "meta": "{}"
        }
        r3 = requests.post(f"{API_URL}/memory/nodes", json=node_payload)
        assert r3.status_code == 200
        node_id = r3.json()["id"]
        node2_payload = {
            "namespace": f"backupns-{unique}",
            "content": f"Backup node 2 {unique}",
            "meta": "{}"
        }
        r4 = requests.post(f"{API_URL}/memory/nodes", json=node2_payload)
        assert r4.status_code == 200
        node2_id = r4.json()["id"]
        edge_payload = {
            "from_id": node_id,
            "to_id": node2_id,
            "relation_type": "backup_edge",
            "meta": f"{{\"note\": \"Backup edge {unique}\"}}"
        }
        r5 = requests.post(f"{API_URL}/memory/edges", json=edge_payload)
        assert r5.status_code == 200
        edge_id = r5.json()["id"]
        proposal_payload = {
            "rule_type": "backup_pending",
            "description": f"Pending proposal {unique}",
            "diff": f"# Rule: Pending\n## Description\nTest {unique}",
            "submitted_by": "backup-tester",
            "user_story": f"Backup/restore pending {unique}"
        }
        r6 = requests.post(f"{API_URL}/propose-rule-change", json=proposal_payload)
        assert r6.status_code == 200
        pending_proposal_id = r6.json()["id"]
        reject_payload = {
            "rule_type": "backup_reject",
            "description": f"Rejected proposal {unique}",
            "diff": f"# Rule: Reject\n## Description\nTest {unique}",
            "submitted_by": "backup-tester",
            "user_story": f"Backup/restore reject {unique}"
        }
        r7 = requests.post(f"{API_URL}/propose-rule-change", json=reject_payload)
        assert r7.status_code == 200
        reject_proposal_id = r7.json()["id"]
        r8 = requests.post(f"{API_URL}/reject-rule-change/{reject_proposal_id}")
        assert r8.status_code == 200
        enhancement_payload = {
            "description": f"Enhancement {unique}",
            "suggested_by": "backup-tester",
            "page": "/backup",
            "tags": ["backup"],
            "categories": ["test"],
            "user_story": f"Backup/restore enhancement {unique}"
        }
        r9 = requests.post(f"{API_URL}/suggest-enhancement", json=enhancement_payload)
        assert r9.status_code == 200
        enhancement_id = r9.json()["id"]
        r10 = requests.post(f"{API_URL}/accept-enhancement/{enhancement_id}")
        assert r10.status_code == 200
        r11 = requests.post(f"{API_URL}/complete-enhancement/{enhancement_id}")
        assert r11.status_code == 200
        bug_payload = {
            "description": f"Bug {unique}",
            "reporter": "backup-tester",
            "page": "/backup"
        }
        r12 = requests.post(f"{API_URL}/bug-report", json=bug_payload)
        assert r12.status_code == 200
        bug_id = r12.json()["id"]
        update_payload = {
            "rule_id": proposal_id,
            "rule_type": "backup_restore_test",
            "description": f"Test rule updated {unique}",
            "diff": f"# Rule: BackupRestore\n## Description\nTest updated {unique}",
            "submitted_by": "backup-tester",
            "user_story": f"Backup/restore test updated {unique}"
        }
        r13 = requests.post(f"{API_URL}/propose-rule-change", json=update_payload)
        assert r13.status_code == 200
        update_proposal_id = r13.json()["id"]
        r14 = requests.post(f"{API_URL}/approve-rule-change/{update_proposal_id}")
        assert r14.status_code == 200
        del_edge = requests.delete(f"{API_URL}/memory/edges", params={"from_id": node_id, "to_id": node2_id, "relation_type": "backup_edge"})
        ns2 = f"backupns2-{unique}"
        node3_payload = {
            "namespace": ns2,
            "content": f"Backup node ns2 {unique}",
            "meta": "{}"
        }
        r15 = requests.post(f"{API_URL}/memory/nodes", json=node3_payload)
        assert r15.status_code == 200
        node3_id = r15.json()["id"]
        print("[INFO] Please run the backup/restore cycle from the host using scripts/backup_restore_cycle.sh, then re-run this test with BACKUP_RESTORE_PHASE=verify to check data integrity after restore.")
        return
    elif BACKUP_RESTORE_PHASE == "verify":
        # Wait for API to be up again
        wait_for_api()
        # 6. Verify data is present
        # Rule (latest version)
        rules = requests.get(f"{API_URL}/rules").json()
        if not any(unique in r["description"] for r in rules):
            print("[DEBUG] Rules after restore:", rules)
        assert any(unique in r["description"] for r in rules)
        # Rule versioning
        rule_id = [r["id"] for r in rules if unique in r["description"]][0]
        history = requests.get(f"{API_URL}/rules/{rule_id}/history").json()
        if not any("updated" in h["description"] for h in history):
            print("[DEBUG] Rule history after restore:", history)
        assert any("updated" in h["description"] for h in history)
        # Memory nodes (namespace 1)
        nodes = requests.get(f"{API_URL}/memory/nodes", params={"namespace": f"backupns-{unique}"}).json()
        if not any(n["content"] == f"Backup node {unique}" for n in nodes):
            print("[DEBUG] Nodes after restore:", nodes)
        assert any(n["content"] == f"Backup node {unique}" for n in nodes)
        if not any(n["content"] == f"Backup node 2 {unique}" for n in nodes):
            print("[DEBUG] Nodes after restore:", nodes)
        assert any(n["content"] == f"Backup node 2 {unique}" for n in nodes)
        # Memory edge (should NOT exist after deletion)
        edges = requests.get(f"{API_URL}/memory/edges", params={"from_id": node_id}).json()
        if any(e["to_id"] == node2_id and e["relation_type"] == "backup_edge" for e in edges):
            print("[DEBUG] Edges after restore (should be deleted):", edges)
        assert not any(e["to_id"] == node2_id and e["relation_type"] == "backup_edge" for e in edges)
        # Pending proposal
        proposals = requests.get(f"{API_URL}/pending-rule-changes").json()
        if not any(unique in p["description"] for p in proposals):
            print("[DEBUG] Proposals after restore:", proposals)
        assert any(unique in p["description"] for p in proposals)
        # Rejected proposal
        all_rules = requests.get(f"{API_URL}/rules").json()
        rejected = [r for r in all_rules if r.get("status") == "rejected" and unique in r.get("description", "")]
        if not rejected:
            print("[DEBUG] Rejected rules after restore:", all_rules)
        assert rejected
        # Completed enhancement
        enhancements = requests.get(f"{API_URL}/enhancements").json()
        completed = [e for e in enhancements if unique in e["description"] and e["status"] == "completed"]
        if not completed:
            print("[DEBUG] Enhancements after restore:", enhancements)
        assert completed
        # Bug report
        bugs = requests.get(f"{API_URL}/bug-reports").json()
        if not any(unique in b["description"] for b in bugs):
            print("[DEBUG] Bug reports after restore:", bugs)
        assert any(unique in b["description"] for b in bugs)
        # Multiple namespaces
        nodes2 = requests.get(f"{API_URL}/memory/nodes", params={"namespace": ns2}).json()
        if not any(n["content"] == f"Backup node ns2 {unique}" for n in nodes2):
            print("[DEBUG] Namespace 2 nodes after restore:", nodes2)
        assert any(n["content"] == f"Backup node ns2 {unique}" for n in nodes2) 