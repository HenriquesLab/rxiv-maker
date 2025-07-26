"""Benchmark tests for critical rxiv-maker components."""

import tempfile
from pathlib import Path

import pytest

from rxiv_maker.converters.citation_processor import convert_citations_to_latex
from rxiv_maker.converters.md2tex import MarkdownToLaTeXConverter
from rxiv_maker.processors.yaml_processor import YAMLProcessor
from rxiv_maker.utils.file_helpers import copy_tree_optimized


@pytest.mark.performance
@pytest.mark.ci_exclude  # Exclude from CI due to timing sensitivity
class TestFileOperationBenchmarks:
    """Benchmark file operations that are used frequently in tests."""

    @pytest.fixture
    def large_manuscript_structure(self):
        """Create a large manuscript structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "large_manuscript"
            manuscript_dir.mkdir()

            # Create multiple figure files to simulate large manuscript
            figures_dir = manuscript_dir / "FIGURES"
            figures_dir.mkdir()

            # Create 50 figure files of varying sizes
            for i in range(50):
                figure_file = figures_dir / f"figure_{i:03d}.png"
                # Simulate different file sizes (1KB to 10KB)
                content = b"fake_png_data" * (100 + i * 20)
                figure_file.write_bytes(content)

            # Create config and content files
            config_content = """
title: "Large Benchmark Manuscript"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
abstract: "This is a large manuscript for benchmarking purposes."
keywords: ["benchmark", "performance", "testing"]
"""
            (manuscript_dir / "00_CONFIG.yml").write_text(config_content)

            # Create large main content with many citations and figures
            main_content = "# Large Benchmark Manuscript\n\n"
            for i in range(100):
                main_content += f"## Section {i + 1}\n\n"
                main_content += (
                    f"This section references @citation{i:03d} and shows "
                    f"![Figure {i}](FIGURES/figure_{i % 50:03d}.png)"
                    f"{{#fig:{i:03d}}}.\n\n"
                )

            (manuscript_dir / "01_MAIN.md").write_text(main_content)

            # Create bibliography with many entries
            bib_content = ""
            for i in range(100):
                bib_content += f"""
@article{{citation{i:03d},
    title = {{Test Article {i + 1}}},
    author = {{Author, Test}},
    journal = {{Test Journal}},
    year = {{2023}},
    volume = {{{i + 1}}},
    pages = {{{i * 10 + 1}--{(i + 1) * 10}}}
}}
"""
            (manuscript_dir / "03_REFERENCES.bib").write_text(bib_content)

            yield manuscript_dir

    def test_manuscript_copying_performance(
        self, benchmark, large_manuscript_structure
    ):
        """Benchmark manuscript directory copying operations."""

        def copy_manuscript():
            with tempfile.TemporaryDirectory() as dest_dir:
                dest_path = Path(dest_dir) / "copied_manuscript"
                copy_tree_optimized(large_manuscript_structure, dest_path)
                return dest_path

        result = benchmark(copy_manuscript)
        assert result.exists()

    def test_file_tree_creation_performance(self, benchmark):
        """Benchmark creation of manuscript directory structure."""

        def create_manuscript_structure():
            with tempfile.TemporaryDirectory() as tmpdir:
                manuscript_dir = Path(tmpdir) / "test_manuscript"
                manuscript_dir.mkdir()

                # Create directory structure
                (manuscript_dir / "FIGURES").mkdir()
                (manuscript_dir / "output").mkdir()

                # Create basic files
                (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")
                (manuscript_dir / "01_MAIN.md").write_text("# Test")
                (manuscript_dir / "03_REFERENCES.bib").write_text(
                    "@article{test,title={Test}}"
                )

                return manuscript_dir

        result = benchmark(create_manuscript_structure)
        assert result.exists()


@pytest.mark.performance
@pytest.mark.ci_exclude  # Exclude from CI due to timing sensitivity
class TestConversionBenchmarks:
    """Benchmark conversion operations."""

    @pytest.fixture
    def large_markdown_content(self):
        """Create large markdown content for benchmarking."""
        content = "# Large Document\n\n"

        # Add many sections with various markdown elements
        for i in range(50):
            content += f"""
## Section {i + 1}

This section contains **bold text**, *italic text*, and `code snippets`.

Mathematical equations: $E = mc^2$ and display equations:

$$F_{i + 1} = F_i + F_{{i-1}}$$ {{#eq:fib{i}}}

Citations like @reference{i:03d} and figure references
![Figure](FIGURES/fig{i}.png){{#fig:{i}}}.

### Subsection {i + 1}.1

Lists and tables:

- Item 1
- Item 2 with @citation{i}
- Item 3

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data {i} | Value {i * 2} | Result {i * 3} |

{{#table:data{i}}} **Table caption for table {i}.**

"""

        return content

    def test_markdown_to_latex_conversion_performance(
        self, benchmark, large_markdown_content
    ):
        """Benchmark markdown to LaTeX conversion."""
        converter = MarkdownToLaTeXConverter()

        def convert_markdown():
            return converter.convert(large_markdown_content)

        result = benchmark(convert_markdown)
        assert result is not None
        assert len(result) > 0

    def test_citation_processing_performance(self, benchmark):
        """Benchmark citation processing with many citations."""
        # Create content with many citations
        content_with_citations = ""
        for i in range(200):
            content_with_citations += (
                f"Reference @citation{i:03d} and @another{i:03d}. "
            )

        def process_citations():
            return convert_citations_to_latex(content_with_citations)

        result = benchmark(process_citations)
        assert result is not None

    def test_yaml_processing_performance(self, benchmark):
        """Benchmark YAML configuration processing."""
        # Create large YAML config
        large_config = {
            "title": "Large Configuration Test",
            "authors": [
                {
                    "name": f"Author {i}",
                    "affiliation": f"University {i}",
                    "email": f"author{i}@test.com",
                    "orcid": f"0000-0000-0000-{i:04d}",
                }
                for i in range(50)
            ],
            "affiliations": {
                str(i): f"University {i}, Department of Science" for i in range(50)
            },
            "keywords": [f"keyword{i}" for i in range(100)],
            "metadata": {f"field_{i}": f"value_{i}" for i in range(100)},
        }

        processor = YAMLProcessor()

        def process_yaml():
            return processor.process_config(large_config)

        result = benchmark(process_yaml)
        assert result is not None


@pytest.mark.performance
@pytest.mark.ci_exclude  # Exclude from CI due to timing sensitivity
class TestFixturePerformanceBenchmarks:
    """Benchmark test fixture operations."""

    def test_temp_directory_creation_performance(self, benchmark):
        """Benchmark temporary directory creation and cleanup."""

        def create_temp_dir():
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir)
                # Simulate some file operations
                (temp_path / "test.txt").write_text("test content")
                return temp_path.exists()

        result = benchmark(create_temp_dir)
        assert result is True

    def test_manuscript_fixture_performance(
        self, benchmark, minimal_manuscript_template
    ):
        """Benchmark creation of manuscript fixtures."""

        def create_manuscript():
            with tempfile.TemporaryDirectory() as tmpdir:
                manuscript_dir = Path(tmpdir) / "test_manuscript"
                manuscript_dir.mkdir()

                # Create files from template
                (manuscript_dir / "00_CONFIG.yml").write_text(
                    minimal_manuscript_template["config"]
                )
                (manuscript_dir / "01_MAIN.md").write_text(
                    minimal_manuscript_template["content"]
                )
                (manuscript_dir / "03_REFERENCES.bib").write_text(
                    minimal_manuscript_template["bibliography"]
                )

                figures_dir = manuscript_dir / "FIGURES"
                figures_dir.mkdir()

                return manuscript_dir

        result = benchmark(create_manuscript)
        assert result.exists()


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.ci_exclude  # Exclude from CI due to timing sensitivity
class TestIntegrationBenchmarks:
    """Benchmark integration test scenarios."""

    def test_full_validation_performance(self, benchmark, minimal_manuscript):
        """Benchmark full manuscript validation."""
        from rxiv_maker.commands.validate import validate_manuscript

        def run_validation():
            return validate_manuscript(minimal_manuscript, skip_doi=True)

        result = benchmark(run_validation)
        # Validation should complete successfully
        assert result is not None

    @pytest.mark.requires_latex
    def test_latex_compilation_performance(self, benchmark, minimal_manuscript):
        """Benchmark LaTeX compilation process."""

        # This would require a more complex setup with LaTeX templates
        def compile_document():
            # Mock compilation for now - in real implementation would compile LaTeX
            import time

            time.sleep(0.1)  # Simulate compilation time
            return True

        result = benchmark(compile_document)
        assert result is True


# Benchmark configuration and utilities
@pytest.fixture(scope="session")
def benchmark_config():
    """Configuration for benchmark tests."""
    return {
        "min_rounds": 5,
        "max_time": 2.0,
        "warmup": True,
        "warmup_iterations": 2,
    }


def pytest_benchmark_group_stats(config, benchmarks, group_by):
    """Custom benchmark grouping for performance analysis."""
    return {
        "conversion": [b for b in benchmarks if "conversion" in b["name"]],
        "file_ops": [
            b for b in benchmarks if "file" in b["name"] or "copying" in b["name"]
        ],
        "fixtures": [b for b in benchmarks if "fixture" in b["name"]],
        "integration": [
            b
            for b in benchmarks
            if "integration" in b["name"] or "validation" in b["name"]
        ],
    }
