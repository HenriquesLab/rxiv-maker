#!/usr/bin/env python3
"""Test edge cases that could cause empty manuscript name"""

import os


def test_edge_cases():
    """Test edge cases that might cause empty manuscript name"""

    test_cases = [
        "CCT8_paper/",
        "CCT8_paper",
        "./CCT8_paper/",
        "./CCT8_paper",
        "",  # Empty string
        "/",  # Just slash
        ".",  # Current directory
        "..",  # Parent directory
        "//",  # Double slash
        " CCT8_paper/ ",  # With spaces
    ]

    for manuscript_path in test_cases:
        print(f"=== Testing manuscript_path: {manuscript_path!r} ===")

        try:
            # BuildManager logic (lines 594-600)
            normalized_path = manuscript_path.rstrip("/")
            manuscript_name = os.path.basename(normalized_path)

            if not manuscript_name or manuscript_name in (".", ".."):
                manuscript_name = "MANUSCRIPT"

            print(f"  normalized_path: {normalized_path!r}")
            print(f"  manuscript_name: {manuscript_name!r}")

            # Simulate env var setting
            os.environ["MANUSCRIPT_PATH"] = manuscript_name

            # write_manuscript_output logic (lines 77-78)
            env_manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
            env_manuscript_name = os.path.basename(env_manuscript_path)

            if not env_manuscript_name or env_manuscript_name in (".", ".."):
                env_manuscript_name = "MANUSCRIPT"

            print(f"  env_manuscript_path: {env_manuscript_path!r}")
            print(f"  env_manuscript_name: {env_manuscript_name!r}")

            output_file = f"output/{env_manuscript_name}.tex"
            print(f"  output_file: {output_file}")

            if env_manuscript_name == "" or ".tex" in output_file.replace(env_manuscript_name, ""):
                print("  ⚠️  POTENTIAL ISSUE FOUND!")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")

        print()


if __name__ == "__main__":
    test_edge_cases()
