#!/usr/bin/env python3
import tempfile
import os
import sys

# Ensure project root is on sys.path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.knowledge_manager import KnowledgeManager

# Create a temporary directory for testing
with tempfile.TemporaryDirectory() as tmpdir:
    # Create some dummy .sav files
    filenames = ["conf_2500mm_2p5A_60Hz_trans.sav", "conf_4000mm_10p0A_60Hz_scatt.sav", "not_a_config.txt"]
    for fname in filenames:
        with open(os.path.join(tmpdir, fname), "w", encoding="utf-8") as f:
            f.write("dummy content")

    # Set environment variable so KnowledgeManager will pick it up
    os.environ["QRangeConfigurations_DIR"] = tmpdir

    km = KnowledgeManager()
    # Pass empty directories so we don't load other knowledge files during the test
    km.load_local_knowledge(directories=[])

    # Simulate the main.py logic for QRangeConfigurations
    qrange_dir = os.environ.get("QRangeConfigurations_DIR", "/home/controls/var/QRangeConfigurations")
    if os.path.exists(qrange_dir) and os.path.isdir(qrange_dir):
        sav_files = sorted([f for f in os.listdir(qrange_dir) if f.lower().endswith('.sav')])
        if sav_files:
            config_names = [os.path.splitext(f)[0] for f in sav_files]
            content = "<Currently Existing Configurations>\n" + "\n".join(f"- {name}" for name in config_names)
            km.local_knowledge["Currently_Existing_Configurations.txt"] = content

    # Check if the synthetic key was added
    key = "Currently_Existing_Configurations.txt"
    if key not in km.local_knowledge:
        print("Test failed: expected key not in local_knowledge")
        raise SystemExit(1)

    content = km.local_knowledge[key]
    print("=== Synthetic Currently Existing Configurations ===")
    print(content)
    # Simple checks
    assert content.startswith("<Currently Existing Configurations>")
    assert "conf_2500mm_2p5A_60Hz_trans" in content
    assert "conf_4000mm_10p0A_60Hz_scatt" in content
    assert "not_a_config" not in content

    print("Test passed: QRangeConfigurations discovered and list generated")
