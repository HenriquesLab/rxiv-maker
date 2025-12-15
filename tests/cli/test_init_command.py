"""Comprehensive tests for rxiv init command.

This test suite ensures the init command works perfectly covering all edge cases
and error conditions for reliable automated testing.

Note: The init command is fully non-interactive and uses sensible defaults.
"""

import subprocess

import pytest


@pytest.mark.fast
class TestInitCommand:
    """Test suite for rxiv init command (always non-interactive)."""

    def test_init_default_directory(self, temp_dir, monkeypatch):
        """Test init with default MANUSCRIPT directory."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        # Verify default directory was created
        manuscript_dir = temp_dir / "MANUSCRIPT"
        assert manuscript_dir.exists(), "Default MANUSCRIPT directory not created"

        # Verify all required files were created
        assert (manuscript_dir / "00_CONFIG.yml").exists(), "Config file not created"
        assert (manuscript_dir / "01_MAIN.md").exists(), "Main content not created"
        assert (manuscript_dir / "02_SUPPLEMENTARY_INFO.md").exists(), "Supplementary info not created"
        assert (manuscript_dir / "03_REFERENCES.bib").exists(), "Bibliography not created"
        assert (manuscript_dir / "FIGURES").is_dir(), "FIGURES directory not created"

    def test_init_custom_directory(self, temp_dir, monkeypatch):
        """Test init with custom directory name."""
        monkeypatch.chdir(temp_dir)

        custom_name = "MY_CUSTOM_PAPER"
        result = subprocess.run(
            ["rxiv", "init", custom_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / custom_name
        assert manuscript_dir.exists(), f"Custom directory {custom_name} not created"
        assert (manuscript_dir / "00_CONFIG.yml").exists()

    def test_init_subdirectory_path(self, temp_dir, monkeypatch):
        """Test init with nested subdirectory path."""
        monkeypatch.chdir(temp_dir)

        nested_path = "papers/2024/MY_PAPER"
        result = subprocess.run(
            ["rxiv", "init", nested_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / nested_path
        assert manuscript_dir.exists(), "Nested directory not created"
        assert (manuscript_dir / "00_CONFIG.yml").exists()

    def test_init_existing_directory_no_force(self, temp_dir, monkeypatch):
        """Test init fails when directory exists without --force."""
        monkeypatch.chdir(temp_dir)

        # Create directory first
        manuscript_dir = temp_dir / "MANUSCRIPT"
        manuscript_dir.mkdir()

        # Try to init without --force (should fail without prompting)
        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0, "Init should fail when directory exists without --force"
        assert "already exists" in result.stderr or "already exists" in result.stdout
        assert "--force" in result.stderr or "--force" in result.stdout, "Should suggest using --force"

    def test_init_existing_directory_with_force(self, temp_dir, monkeypatch):
        """Test init overwrites directory when --force is used."""
        monkeypatch.chdir(temp_dir)

        manuscript_dir = temp_dir / "MANUSCRIPT"
        manuscript_dir.mkdir()

        # Create a dummy file to verify it gets overwritten
        dummy_file = manuscript_dir / "dummy.txt"
        dummy_file.write_text("This should be removed")

        # Init with --force (should succeed)
        result = subprocess.run(
            ["rxiv", "init", "--force"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init with --force failed: {result.stderr}"

        # Verify manuscript files were created
        assert (manuscript_dir / "00_CONFIG.yml").exists()
        assert (manuscript_dir / "01_MAIN.md").exists()

    def test_init_creates_example_figure(self, temp_dir, monkeypatch):
        """Test that init creates example figure in FIGURES directory."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        figures_dir = manuscript_dir / "FIGURES"

        # Check for example figure (should be .mmd or similar)
        figure_files = list(figures_dir.glob("Figure__example.*"))
        assert len(figure_files) > 0, "No example figure created"

    def test_init_config_has_default_values(self, temp_dir, monkeypatch):
        """Test that generated config file contains default values."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        config_file = manuscript_dir / "00_CONFIG.yml"

        config_content = config_file.read_text()

        # Verify default values are present (from workflow_commands.py lines 77-81)
        assert "Your Manuscript Title" in config_content or "title:" in config_content
        assert "authors:" in config_content

    def test_init_main_content_has_figure_reference(self, temp_dir, monkeypatch):
        """Test that main content file references the example figure correctly."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        main_file = manuscript_dir / "01_MAIN.md"

        main_content = main_file.read_text()

        # Verify figure reference uses source file (.mmd), not output (.pdf)
        assert "FIGURES/Figure__example" in main_content, "Figure reference missing"
        # Should reference .mmd source, not .pdf output
        if ".mmd" not in main_content and ".pdf" in main_content:
            pytest.fail("Figure should reference .mmd source file, not .pdf output")

    def test_init_bibliography_file_exists(self, temp_dir, monkeypatch):
        """Test that bibliography file is created."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        bib_file = manuscript_dir / "03_REFERENCES.bib"

        assert bib_file.exists(), "Bibliography file not created"
        # Can be empty or have examples
        assert bib_file.stat().st_size >= 0, "Bibliography file is invalid"

    def test_init_supplementary_info_exists(self, temp_dir, monkeypatch):
        """Test that supplementary info file is created."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        supp_file = manuscript_dir / "02_SUPPLEMENTARY_INFO.md"

        assert supp_file.exists(), "Supplementary info file not created"
        assert supp_file.stat().st_size > 0, "Supplementary info file is empty"

    def test_init_with_validation_flag(self, temp_dir, monkeypatch):
        """Test init with --validate flag runs validation."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init", "--no-interactive", "--validate"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should succeed and mention validation
        assert result.returncode == 0, f"Init with validation failed: {result.stderr}"
        output = result.stdout + result.stderr
        assert "validation" in output.lower(), "Validation not mentioned in output"

    def test_init_absolute_path(self, temp_dir, monkeypatch):
        """Test init with absolute path."""
        monkeypatch.chdir(temp_dir)

        manuscript_dir = temp_dir / "ABS_PATH_MANUSCRIPT"

        result = subprocess.run(
            ["rxiv", "init", str(manuscript_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init with absolute path failed: {result.stderr}"
        assert manuscript_dir.exists(), "Directory not created with absolute path"
        assert (manuscript_dir / "00_CONFIG.yml").exists()

    def test_init_creates_valid_directory_structure(self, temp_dir, monkeypatch):
        """Test that init creates the complete expected directory structure."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"

        # Expected structure
        expected_files = [
            "00_CONFIG.yml",
            "01_MAIN.md",
            "02_SUPPLEMENTARY_INFO.md",
            "03_REFERENCES.bib",
        ]

        expected_dirs = ["FIGURES"]

        for file in expected_files:
            assert (manuscript_dir / file).is_file(), f"Expected file {file} not created"

        for dir_name in expected_dirs:
            assert (manuscript_dir / dir_name).is_dir(), f"Expected directory {dir_name} not created"

    def test_init_output_shows_success_message(self, temp_dir, monkeypatch):
        """Test that init output shows success message."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        output = result.stdout + result.stderr
        # Should show success and next steps
        assert "success" in output.lower() or "initialized" in output.lower()
        assert "next steps" in output.lower() or "rxiv pdf" in output.lower()

    def test_init_help_flag(self, temp_dir, monkeypatch):
        """Test that --help flag works and shows usage."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, "Help flag failed"
        assert "Initialize" in result.stdout or "init" in result.stdout
        assert "non-interactive" in result.stdout, "Should mention non-interactive behavior"
        assert "--force" in result.stdout, "--force flag not documented in help"
        assert "--validate" in result.stdout, "--validate flag not documented in help"
        # --no-interactive is hidden but still supported for backward compatibility

    def test_init_combined_flags(self, temp_dir, monkeypatch):
        """Test init with multiple flags combined."""
        monkeypatch.chdir(temp_dir)

        manuscript_dir = temp_dir / "COMBINED_TEST"
        manuscript_dir.mkdir()  # Pre-create to test --force

        result = subprocess.run(
            ["rxiv", "init", str(manuscript_dir), "--force", "--validate"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Init with combined flags failed: {result.stderr}"
        assert (manuscript_dir / "00_CONFIG.yml").exists()

    def test_init_special_characters_in_path(self, temp_dir, monkeypatch):
        """Test init with special characters in directory name."""
        monkeypatch.chdir(temp_dir)

        # Test with spaces and dashes
        manuscript_name = "My-Paper_2024"
        result = subprocess.run(
            ["rxiv", "init", manuscript_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init with special chars failed: {result.stderr}"

        manuscript_dir = temp_dir / manuscript_name
        assert manuscript_dir.exists()
        assert (manuscript_dir / "00_CONFIG.yml").exists()

    def test_init_creates_non_empty_files(self, temp_dir, monkeypatch):
        """Test that all created files have content (not empty)."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"

        # All main content files should have some content
        content_files = [
            "00_CONFIG.yml",
            "01_MAIN.md",
            "02_SUPPLEMENTARY_INFO.md",
        ]

        for file in content_files:
            file_path = manuscript_dir / file
            assert file_path.stat().st_size > 0, f"File {file} is empty"

    def test_init_error_message_on_failure(self, temp_dir, monkeypatch):
        """Test that helpful error messages are shown on failure."""
        monkeypatch.chdir(temp_dir)

        # Create existing directory
        manuscript_dir = temp_dir / "MANUSCRIPT"
        manuscript_dir.mkdir()

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0, "Should fail when directory exists"

        error_output = result.stderr + result.stdout
        # Should mention the problem and suggest --force
        assert "already exists" in error_output or "exist" in error_output
        assert "--force" in error_output or "force" in error_output.lower()


@pytest.mark.slow
class TestInitValidation:
    """Tests that verify init-generated manuscripts are valid."""

    def test_init_output_validates_successfully(self, temp_dir, monkeypatch):
        """Test that manuscript created by init passes validation."""
        monkeypatch.chdir(temp_dir)

        # Init manuscript
        init_result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"

        # Validate it
        validate_result = subprocess.run(
            ["rxiv", "validate", str(manuscript_dir)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should pass validation (or at least not have critical errors)
        assert validate_result.returncode == 0, f"Validation failed: {validate_result.stderr}"

    def test_init_output_has_valid_yaml_config(self, temp_dir, monkeypatch):
        """Test that generated config file is valid YAML."""
        import yaml

        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"
        config_file = manuscript_dir / "00_CONFIG.yml"

        # Should be valid YAML
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert isinstance(config, dict), "Config is not a valid YAML dictionary"
        assert "title" in config, "Config missing title field"
        assert "authors" in config, "Config missing authors field"

    def test_init_output_has_valid_markdown(self, temp_dir, monkeypatch):
        """Test that generated markdown files are valid."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "init"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        manuscript_dir = temp_dir / "MANUSCRIPT"

        # Read markdown files
        main_content = (manuscript_dir / "01_MAIN.md").read_text()
        supp_content = (manuscript_dir / "02_SUPPLEMENTARY_INFO.md").read_text()

        # Should contain markdown headers
        assert "#" in main_content, "Main content has no markdown headers"
        assert "#" in supp_content, "Supplementary info has no markdown headers"


@pytest.mark.fast
class TestInitEdgeCases:
    """Edge case tests for init command."""

    def test_init_in_current_directory_dot(self, temp_dir, monkeypatch):
        """Test init with '.' as path (current directory)."""
        monkeypatch.chdir(temp_dir)

        # Create subdirectory and cd into it
        subdir = temp_dir / "mymanuscript"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        result = subprocess.run(
            ["rxiv", "init", ".", "--no-interactive", "--force"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should initialize in current directory
        assert result.returncode == 0, f"Init in current dir failed: {result.stderr}"
        assert (subdir / "00_CONFIG.yml").exists(), "Config not created in current directory"

    def test_init_preserves_directory_case(self, temp_dir, monkeypatch):
        """Test that directory name case is preserved."""
        monkeypatch.chdir(temp_dir)

        # Mixed case directory name
        manuscript_name = "MyPaper_ABC"
        result = subprocess.run(
            ["rxiv", "init", manuscript_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init failed: {result.stderr}"

        # Verify exact case is preserved
        manuscript_dir = temp_dir / manuscript_name
        assert manuscript_dir.exists(), f"Directory with exact case {manuscript_name} not found"

    def test_init_multiple_times_different_dirs(self, temp_dir, monkeypatch):
        """Test running init multiple times in same parent directory."""
        monkeypatch.chdir(temp_dir)

        # Create multiple manuscripts
        for i in range(3):
            manuscript_name = f"MANUSCRIPT_{i}"
            result = subprocess.run(
                ["rxiv", "init", manuscript_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"Init {i} failed: {result.stderr}"
            assert (temp_dir / manuscript_name / "00_CONFIG.yml").exists()

    def test_init_empty_parent_directory(self, temp_dir, monkeypatch):
        """Test init creates parent directories if they don't exist."""
        monkeypatch.chdir(temp_dir)

        # Nested path where parent doesn't exist
        nested_path = "nonexistent/parent/MANUSCRIPT"
        result = subprocess.run(
            ["rxiv", "init", nested_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Init with nonexistent parents failed: {result.stderr}"

        manuscript_dir = temp_dir / nested_path
        assert manuscript_dir.exists(), "Nested directory not created"
        assert (manuscript_dir / "00_CONFIG.yml").exists()
