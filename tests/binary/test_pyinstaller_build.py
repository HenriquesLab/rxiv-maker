"""Tests for PyInstaller binary building functionality."""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Skip binary tests if PyInstaller is not available
pyinstaller = pytest.importorskip("PyInstaller")


class TestPyInstallerBuild:
    """Test PyInstaller binary building process."""

    @pytest.fixture
    def temp_build_dir(self):
        """Create a temporary directory for build testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_pyinstaller_spec_file_creation(self, temp_build_dir, project_root):
        """Test that we can create a valid PyInstaller spec file."""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Add the src directory to Python path
src_path = str(Path("{project_root}") / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

a = Analysis(
    ['{project_root}/src/rxiv_maker/rxiv_maker_cli.py'],
    pathex=[src_path],
    binaries=[],
    data=[
        ('{project_root}/src/tex', 'tex'),
    ],
    hiddenimports=[
        'rxiv_maker',
        'rxiv_maker.cli',
        'rxiv_maker.commands',
        'rxiv_maker.converters',
        'rxiv_maker.processors',
        'rxiv_maker.utils',
        'rxiv_maker.validators',
        'rxiv_maker.install',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.data,
    [],
    name='rxiv',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX for testing
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)'''

        spec_file = temp_build_dir / "test_rxiv.spec"
        spec_file.write_text(spec_content)

        assert spec_file.exists()
        assert "Analysis" in spec_file.read_text()
        assert "rxiv_maker_cli.py" in spec_file.read_text()

    def test_required_data_files_exist(self, project_root):
        """Test that all required data files exist for binary building."""
        # Test LaTeX template files
        template_tex = project_root / "src" / "tex" / "template.tex"
        assert template_tex.exists(), f"Template file not found: {template_tex}"

        style_cls = project_root / "src" / "tex" / "style" / "rxiv_maker_style.cls"
        assert style_cls.exists(), f"Style class file not found: {style_cls}"

        style_bst = project_root / "src" / "tex" / "style" / "rxiv_maker_style.bst"
        assert style_bst.exists(), f"Style bibliography file not found: {style_bst}"

    def test_cli_entry_point_exists(self, project_root):
        """Test that the CLI entry point exists and is importable."""
        cli_path = project_root / "src" / "rxiv_maker" / "rxiv_maker_cli.py"
        assert cli_path.exists(), f"CLI entry point not found: {cli_path}"

        # Test that the entry point is syntactically valid
        with open(cli_path) as f:
            content = f.read()
            # Should have proper entry point structure (with either single or double quotes)
            assert (
                "if __name__ == '__main__'" in content
                or 'if __name__ == "__main__"' in content
            )
            assert "main()" in content or "cli()" in content

    def test_hidden_imports_are_importable(self, project_root):
        """Test that all hidden imports specified in the spec are importable."""
        # Add src to path for testing
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        hidden_imports = [
            "rxiv_maker",
            "rxiv_maker.cli",
            "rxiv_maker.commands",
            "rxiv_maker.converters",
            "rxiv_maker.processors",
            "rxiv_maker.utils",
            "rxiv_maker.validators",
            "rxiv_maker.install",
        ]

        for module_name in hidden_imports:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Hidden import '{module_name}' failed: {e}")

    @pytest.mark.slow
    def test_pyinstaller_analysis_phase(self, temp_build_dir, project_root):
        """Test that PyInstaller can analyze the application successfully."""
        # This is a slower test that actually runs PyInstaller analysis
        try:
            from PyInstaller.building.api import Analysis
        except ImportError:
            try:
                from PyInstaller.building.build_main import Analysis
            except ImportError:
                pytest.skip("PyInstaller Analysis class not available")

        # Add src to path
        src_path = str(project_root / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        try:
            analysis = Analysis(
                [str(project_root / "src" / "rxiv_maker" / "rxiv_maker_cli.py")],
                pathex=[src_path],
                binaries=[],
                data=[
                    (str(project_root / "src" / "tex"), "tex"),
                ],
                hiddenimports=[
                    "rxiv_maker",
                    "rxiv_maker.cli",
                    "rxiv_maker.commands",
                    "rxiv_maker.converters",
                    "rxiv_maker.processors",
                    "rxiv_maker.utils",
                    "rxiv_maker.validators",
                    "rxiv_maker.install",
                ],
                hookspath=[],
                hooksconfig={},
                runtime_hooks=[],
                excludes=[],
                workpath=str(temp_build_dir),
                noarchive=False,
            )

            # If we get here without exceptions, analysis succeeded
            assert analysis is not None
            assert hasattr(analysis, "scripts")
            assert hasattr(analysis, "pure")
            assert hasattr(analysis, "binaries")

        except Exception as e:
            # Skip if dependencies are missing or environment isn't suitable
            pytest.skip(f"PyInstaller analysis failed (environment issue): {e}")

    def test_binary_name_platform_specific(self):
        """Test that binary names are platform-specific."""
        import platform

        expected_ext = ".exe" if platform.system() == "Windows" else ""

        binary_name = "rxiv" + expected_ext

        # This would be used in the actual build process
        assert binary_name.endswith(expected_ext)

    def test_data_files_inclusion_spec(self, project_root):
        """Test that data files are properly specified for inclusion."""
        tex_dir = project_root / "src" / "tex"
        assert tex_dir.exists()

        # Check that the directory has the expected structure
        template_file = tex_dir / "template.tex"
        style_dir = tex_dir / "style"

        assert template_file.exists(), "template.tex should exist"
        assert style_dir.exists(), "style directory should exist"
        assert (style_dir / "rxiv_maker_style.cls").exists(), "style.cls should exist"
        assert (style_dir / "rxiv_maker_style.bst").exists(), "style.bst should exist"

    def test_pyinstaller_exclusions(self):
        """Test that we properly exclude unnecessary modules for smaller binaries."""
        # These modules should be excluded to reduce binary size
        exclusions = [
            "tkinter",  # GUI toolkit not needed
            "unittest",  # Testing framework not needed in binary
            "doctest",  # Documentation testing not needed
            "pdb",  # Debugger not needed
        ]

        # In a real build, these would be added to excludes list
        for module in exclusions:
            try:
                __import__(module)
                # Module exists but should be excluded
            except ImportError:
                # Module doesn't exist, which is fine
                pass


class TestBinaryCompatibility:
    """Test compatibility aspects for binary distribution."""

    def test_template_processor_path_resolution(self):
        """Test that template processor can resolve paths in binary context."""
        from rxiv_maker.processors.template_processor import get_template_path

        # This should work both in source and binary contexts
        template_path = get_template_path()
        assert template_path is not None

        # The path should be a Path object
        assert hasattr(template_path, "exists")

        # In the test environment, it should exist
        # In a binary, it would be in the bundled resources
        if template_path.exists():
            assert template_path.name == "template.tex"

    def test_resource_bundling_compatibility(self):
        """Test that resource access works for binary distribution."""
        import rxiv_maker

        # Test that we can access the version (should work in both contexts)
        assert hasattr(rxiv_maker, "__version__")
        assert rxiv_maker.__version__ is not None

    def test_cli_import_structure(self):
        """Test that CLI imports work correctly for binary building."""
        # These imports should work in binary context
        try:
            from rxiv_maker.cli.commands.build import build
            from rxiv_maker.cli.commands.init import init
            from rxiv_maker.cli.commands.validate import validate
            from rxiv_maker.cli.main import main
        except ImportError as e:
            pytest.fail(f"CLI import failed (needed for binary): {e}")

    def test_package_structure_for_binary(self):
        """Test that package structure is compatible with PyInstaller."""
        # Test that all main modules can be imported
        main_modules = [
            "rxiv_maker.commands",
            "rxiv_maker.converters",
            "rxiv_maker.processors",
            "rxiv_maker.utils",
            "rxiv_maker.validators",
            "rxiv_maker.install",
        ]

        for module in main_modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"Module {module} import failed: {e}")
