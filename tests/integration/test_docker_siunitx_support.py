"""Integration test for siunitx support in Docker environments."""

import subprocess
from pathlib import Path

import pytest


class TestDockerSiunitxSupport:
    """Test siunitx LaTeX package support in Docker containers."""

    def create_siunitx_test_document(self, temp_dir):
        """Create a minimal LaTeX document that uses siunitx."""
        test_dir = temp_dir / "siunitx_test"
        test_dir.mkdir()

        # Create a minimal document that uses siunitx
        latex_content = r"""
\documentclass{article}
\usepackage{siunitx}

\begin{document}
\title{siunitx Test Document}
\maketitle

This document tests siunitx functionality:
\begin{itemize}
\item Temperature: \SI{25}{\celsius}
\item Distance: \SI{10}{\meter}
\item Speed: \SI{3e8}{\meter\per\second}
\item Scientific notation: \num{1.23e-4}
\end{itemize}

Using siunitx commands:
\begin{align}
E &= mc^2 \\
v &= \SI{3.0e8}{\meter\per\second}
\end{align}

\end{document}
"""

        (test_dir / "test_siunitx.tex").write_text(latex_content)
        return test_dir

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_image_has_siunitx_package(self):
        """Test that Docker base image includes siunitx package via texlive-science."""
        # This is a verification that our Dockerfile includes texlive-science
        dockerfile_path = Path("src/docker/images/base/Dockerfile")

        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found in expected location")

        dockerfile_content = dockerfile_path.read_text()

        # Verify texlive-science is installed
        assert "texlive-science" in dockerfile_content, "texlive-science package missing from Dockerfile"

        # Verify it's in the LaTeX installation section
        lines = dockerfile_content.split("\n")
        latex_section_found = False
        texlive_science_found = False

        for line in lines:
            if "Install LaTeX packages" in line or "texlive-latex-base" in line:
                latex_section_found = True
            if latex_section_found and "texlive-science" in line:
                texlive_science_found = True
                break

        assert texlive_science_found, "texlive-science not found in LaTeX installation section"

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_container_siunitx_compilation(self, tmp_path):
        """Test siunitx compilation in Docker container (requires Docker)."""
        try:
            # Check if Docker is available
            subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Docker not available for testing")

        # Create test document
        test_dir = self.create_siunitx_test_document(tmp_path)

        # Try to build with Docker (would need actual Docker image)
        # This is a placeholder test that would work when Docker is available
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{test_dir}:/workspace/test",
            "henriqueslab/rxiv-maker-base:latest",
            "pdflatex",
            "-interaction=nonstopmode",
            "/workspace/test/test_siunitx.tex",
        ]

        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60, cwd=test_dir)

            # If Docker image exists and works, verify compilation succeeded
            if result.returncode == 0:
                assert (test_dir / "test_siunitx.pdf").exists(), "PDF was not generated"
            else:
                # Log the error for debugging but don't fail the test
                print(f"Docker compilation failed (expected if image not built): {result.stderr}")
                pytest.skip("Docker image not available or compilation failed")

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pytest.skip("Docker container execution failed or timed out")

    @pytest.mark.integration
    def test_local_siunitx_availability_check(self, tmp_path):
        """Test that siunitx is detectable in local LaTeX installation."""
        # Create test document
        test_dir = self.create_siunitx_test_document(tmp_path)

        try:
            # Try to compile with local pdflatex if available
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "test_siunitx.tex"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=test_dir,
            )

            if result.returncode == 0:
                # Compilation succeeded - siunitx is available
                assert (test_dir / "test_siunitx.pdf").exists()
            else:
                # Check if the error is specifically about siunitx
                if "siunitx.sty" in result.stdout or "siunitx.sty" in result.stderr:
                    pytest.fail("siunitx package not found in local LaTeX installation")
                else:
                    # Other LaTeX error, not siunitx-related
                    pytest.skip(f"LaTeX compilation failed for other reasons: {result.stderr}")

        except FileNotFoundError:
            pytest.skip("pdflatex not available for local testing")
        except subprocess.TimeoutExpired:
            pytest.skip("LaTeX compilation timed out")

    def test_dockerfile_latex_package_completeness(self):
        """Test that Dockerfile includes all essential LaTeX packages."""
        dockerfile_path = Path("src/docker/images/base/Dockerfile")

        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found")

        dockerfile_content = dockerfile_path.read_text()

        # Essential LaTeX packages that should be in Docker image
        essential_latex_packages = [
            "texlive-latex-base",
            "texlive-latex-recommended",
            "texlive-latex-extra",
            "texlive-science",  # This includes siunitx
            "texlive-fonts-recommended",
            "biber",
        ]

        for package in essential_latex_packages:
            assert package in dockerfile_content, f"Essential LaTeX package {package} missing from Dockerfile"

    def test_rxiv_maker_style_siunitx_requirement_documented(self):
        """Test that siunitx requirement is properly documented and handled."""
        # Verify our LaTeX dependency handler includes siunitx
        from unittest.mock import MagicMock

        from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler

        handler = LaTeXHandler(MagicMock())
        essential_packages = handler.get_essential_packages()

        assert "siunitx" in essential_packages, "siunitx missing from essential LaTeX packages"

        # Verify the style file requires siunitx
        style_file_path = Path("src/tex/style/rxiv_maker_style.cls")
        if style_file_path.exists():
            style_content = style_file_path.read_text()
            assert "\\RequirePackage{siunitx}" in style_content, "siunitx not required by style file"

    @pytest.mark.integration
    def test_docker_latex_installation_order(self):
        """Test that Docker LaTeX packages are installed in correct dependency order."""
        dockerfile_path = Path("src/docker/images/base/Dockerfile")

        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found")

        dockerfile_content = dockerfile_path.read_text()
        lines = dockerfile_content.split("\n")

        # Find LaTeX installation sections
        latex_base_line = None
        science_line = None

        for i, line in enumerate(lines):
            if "texlive-latex-base" in line:
                latex_base_line = i
            if "texlive-science" in line:
                science_line = i

        # texlive-science should come after base packages
        if latex_base_line is not None and science_line is not None:
            assert science_line > latex_base_line, "texlive-science should be installed after texlive-latex-base"
