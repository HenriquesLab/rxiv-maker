"""Comprehensive tests for validate_manuscript.py script."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.scripts.validate_manuscript import ManuscriptValidator, main


class TestManuscriptValidator:
    """Test suite for ManuscriptValidator class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)
        self.validator = ManuscriptValidator(self.manuscript_path)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test ManuscriptValidator initialization."""
        validator = ManuscriptValidator("/test/path", skip_enhanced=True, show_stats=True)
        assert validator.manuscript_path == Path("/test/path")
        assert validator.skip_enhanced is True
        assert validator.show_stats is True
        assert validator.errors == []
        assert validator.warnings == []
        assert validator.info_messages == []
        assert validator.validation_metadata == {}

    def test_validate_directory_structure_exists(self):
        """Test directory structure validation when directory exists."""
        result = self.validator.validate_directory_structure()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_directory_structure_not_exists(self):
        """Test directory structure validation when directory doesn't exist."""
        validator = ManuscriptValidator("/nonexistent/path")
        result = validator.validate_directory_structure()
        assert result is False
        assert len(validator.errors) == 1
        assert "not found" in validator.errors[0]

    def test_validate_directory_structure_not_directory(self):
        """Test directory structure validation when path is not a directory."""
        # Create a file instead of directory
        file_path = Path(self.temp_dir) / "not_a_dir"
        file_path.write_text("test")

        validator = ManuscriptValidator(file_path)
        result = validator.validate_directory_structure()
        assert result is False
        assert len(validator.errors) == 1
        assert "not a directory" in validator.errors[0]

    def test_validate_required_files_all_present(self):
        """Test required files validation when all files are present."""
        # Create all required files
        for filename in ManuscriptValidator.REQUIRED_FILES:
            (self.manuscript_path / filename).write_text("test content")

        result = self.validator.validate_required_files()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_required_files_missing(self):
        """Test required files validation when files are missing."""
        result = self.validator.validate_required_files()
        assert result is False
        assert len(self.validator.errors) == len(ManuscriptValidator.REQUIRED_FILES)

        for error in self.validator.errors:
            assert "missing" in error

    def test_validate_required_files_partial(self):
        """Test required files validation with some files missing."""
        # Create only one file
        (self.manuscript_path / "00_CONFIG.yml").write_text("test: value")

        result = self.validator.validate_required_files()
        assert result is False
        assert len(self.validator.errors) == len(ManuscriptValidator.REQUIRED_FILES) - 1

    def test_validate_optional_files_present(self):
        """Test optional files validation when files are present."""
        for filename in ManuscriptValidator.OPTIONAL_FILES:
            (self.manuscript_path / filename).write_text("test content")

        self.validator.validate_optional_files()
        assert len(self.validator.warnings) == 0

    def test_validate_optional_files_missing(self):
        """Test optional files validation when files are missing."""
        self.validator.validate_optional_files()
        assert len(self.validator.warnings) == len(ManuscriptValidator.OPTIONAL_FILES)

        for warning in self.validator.warnings:
            assert "missing" in warning

    def test_validate_required_directories_present(self):
        """Test required directories validation when directories are present."""
        for dirname in ManuscriptValidator.REQUIRED_DIRS:
            (self.manuscript_path / dirname).mkdir()

        result = self.validator.validate_required_directories()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_required_directories_missing(self):
        """Test required directories validation when directories are missing."""
        result = self.validator.validate_required_directories()
        assert result is False
        assert len(self.validator.errors) == len(ManuscriptValidator.REQUIRED_DIRS)

    def test_validate_required_directories_not_directory(self):
        """Test required directories validation when path is a file."""
        # Create file instead of directory
        for dirname in ManuscriptValidator.REQUIRED_DIRS:
            (self.manuscript_path / dirname).write_text("test")

        result = self.validator.validate_required_directories()
        assert result is False
        assert len(self.validator.errors) == len(ManuscriptValidator.REQUIRED_DIRS)

        for error in self.validator.errors:
            assert "not a directory" in error

    def test_validate_config_file_valid(self):
        """Test config file validation with valid YAML."""
        config_data = {
            "title": "Test Title",
            "authors": ["Author 1", "Author 2"],
            "date": "2024-01-01",
            "keywords": ["test", "validation"],
        }
        config_path = self.manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.validator.validate_config_file()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_config_file_missing(self):
        """Test config file validation when file is missing."""
        result = self.validator.validate_config_file()
        assert result is False

    def test_validate_config_file_invalid_yaml(self):
        """Test config file validation with invalid YAML."""
        config_path = self.manuscript_path / "00_CONFIG.yml"
        config_path.write_text("invalid: yaml: content: [")

        result = self.validator.validate_config_file()
        assert result is False
        assert len(self.validator.errors) == 1
        assert "Invalid YAML" in self.validator.errors[0]

    def test_validate_config_file_not_dict(self):
        """Test config file validation when content is not a dictionary."""
        config_path = self.manuscript_path / "00_CONFIG.yml"
        config_path.write_text("- this is a list")

        result = self.validator.validate_config_file()
        assert result is False
        assert len(self.validator.errors) == 1
        assert "dictionary" in self.validator.errors[0]

    def test_validate_config_file_missing_fields(self):
        """Test config file validation with missing required fields."""
        config_data = {"title": "Test Title"}  # Missing other required fields
        config_path = self.manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.validator.validate_config_file()
        assert result is False
        expected_missing = len(ManuscriptValidator.REQUIRED_CONFIG_FIELDS) - 1
        assert len(self.validator.errors) == expected_missing

    def test_validate_config_file_empty_fields(self):
        """Test config file validation with empty required fields."""
        config_data = {"title": "", "authors": [], "date": "", "keywords": []}
        config_path = self.manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = self.validator.validate_config_file()
        assert result is True  # Structure is valid, but warnings about empty fields
        assert len(self.validator.warnings) == len(ManuscriptValidator.REQUIRED_CONFIG_FIELDS)

    def test_validate_bibliography_valid(self):
        """Test bibliography validation with valid BibTeX content."""
        bib_content = """
        @article{test2024,
            title={Test Article},
            author={Test Author},
            journal={Test Journal},
            year={2024}
        }
        """
        bib_path = self.manuscript_path / "03_REFERENCES.bib"
        bib_path.write_text(bib_content)

        result = self.validator.validate_bibliography()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_bibliography_missing(self):
        """Test bibliography validation when file is missing."""
        result = self.validator.validate_bibliography()
        assert result is False

    def test_validate_bibliography_empty(self):
        """Test bibliography validation with empty file."""
        bib_path = self.manuscript_path / "03_REFERENCES.bib"
        bib_path.write_text("")

        result = self.validator.validate_bibliography()
        assert result is True
        assert len(self.validator.warnings) == 1
        assert "empty" in self.validator.warnings[0]

    def test_validate_bibliography_no_entries(self):
        """Test bibliography validation with no BibTeX entries."""
        bib_path = self.manuscript_path / "03_REFERENCES.bib"
        bib_path.write_text("This is not a BibTeX file")

        result = self.validator.validate_bibliography()
        assert result is True
        assert len(self.validator.warnings) == 1
        assert "no BibTeX entries" in self.validator.warnings[0]

    def test_validate_main_content_valid(self):
        """Test main content validation with valid content."""
        main_content = """
        # Abstract
        This is the abstract.

        # Introduction
        This is the introduction.

        # Methods
        These are the methods.

        # Results
        These are the results.

        # Discussion
        This is the discussion.
        """
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text(main_content)

        result = self.validator.validate_main_content()
        assert result is True
        assert len(self.validator.errors) == 0

    def test_validate_main_content_missing(self):
        """Test main content validation when file is missing."""
        result = self.validator.validate_main_content()
        assert result is False

    def test_validate_main_content_empty(self):
        """Test main content validation with empty file."""
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text("")

        result = self.validator.validate_main_content()
        assert result is False
        assert len(self.validator.errors) == 1
        assert "empty" in self.validator.errors[0]

    def test_validate_main_content_few_sections(self):
        """Test main content validation with few standard sections."""
        main_content = "# Introduction\nThis is just an introduction."
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text(main_content)

        result = self.validator.validate_main_content()
        assert result is True
        assert len(self.validator.warnings) == 1
        assert "few standard sections" in self.validator.warnings[0]

    def test_check_figure_references_valid(self):
        """Test figure reference checking with valid references."""
        # Create main content with figure references
        main_content = """
        Here is a figure: ![Test Figure](FIGURES/test.png)
        Another figure: ![Another Figure](FIGURES/test2.jpg)
        """
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text(main_content)

        # Create figures directory and files
        figures_dir = self.manuscript_path / "FIGURES"
        figures_dir.mkdir()
        (figures_dir / "test.png").write_text("fake image")
        (figures_dir / "test2.jpg").write_text("fake image")

        self.validator.check_figure_references()
        assert len(self.validator.warnings) == 0

    def test_check_figure_references_missing(self):
        """Test figure reference checking with missing references."""
        # Create main content with figure references
        main_content = """
        Here is a figure: ![Test Figure](FIGURES/test.png)
        Missing figure: ![Missing](FIGURES/missing.jpg)
        """
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text(main_content)

        # Create figures directory but only one file
        figures_dir = self.manuscript_path / "FIGURES"
        figures_dir.mkdir()
        (figures_dir / "test.png").write_text("fake image")

        self.validator.check_figure_references()
        assert len(self.validator.warnings) == 1
        assert "missing.jpg" in self.validator.warnings[0]

    def test_check_figure_references_no_main_file(self):
        """Test figure reference checking when main file doesn't exist."""
        self.validator.check_figure_references()
        # Should not crash and not add any warnings
        assert len(self.validator.warnings) == 0

    def test_check_figure_references_no_figures_dir(self):
        """Test figure reference checking when figures directory doesn't exist."""
        main_path = self.manuscript_path / "01_MAIN.md"
        main_path.write_text("![Test](FIGURES/test.png)")

        self.validator.check_figure_references()
        # Should not crash and not add any warnings
        assert len(self.validator.warnings) == 0

    def test_run_enhanced_validation_skip(self):
        """Test enhanced validation when skipped."""
        validator = ManuscriptValidator(self.manuscript_path, skip_enhanced=True)
        result = validator.run_enhanced_validation()
        assert result is True

    @patch("rxiv_maker.scripts.validate_manuscript.ENHANCED_VALIDATION_AVAILABLE", False)
    def test_run_enhanced_validation_not_available(self):
        """Test enhanced validation when not available."""
        result = self.validator.run_enhanced_validation()
        assert result is True
        assert len(self.validator.warnings) == 1
        assert "not available" in self.validator.warnings[0]

    @patch("rxiv_maker.scripts.validate_manuscript.ENHANCED_VALIDATION_AVAILABLE", True)
    @patch("rxiv_maker.scripts.validate_manuscript.CitationValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.ReferenceValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.FigureValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.MathValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.SyntaxValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.LaTeXErrorParser")
    def test_run_enhanced_validation_success(
        self, mock_latex, mock_syntax, mock_math, mock_figure, mock_reference, mock_citation
    ):
        """Test successful enhanced validation."""
        # Mock validation results
        mock_result = MagicMock()
        mock_result.validator_name = "TestValidator"
        mock_result.metadata = {}
        mock_result.errors = []

        for mock_validator in [mock_citation, mock_reference, mock_figure, mock_math, mock_syntax, mock_latex]:
            mock_instance = mock_validator.return_value
            mock_instance.validate.return_value = mock_result

        result = self.validator.run_enhanced_validation()
        assert result is True

    @patch("rxiv_maker.scripts.validate_manuscript.ENHANCED_VALIDATION_AVAILABLE", True)
    @patch("rxiv_maker.scripts.validate_manuscript.CitationValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.ReferenceValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.FigureValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.MathValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.SyntaxValidator")
    @patch("rxiv_maker.scripts.validate_manuscript.LaTeXErrorParser")
    def test_run_enhanced_validation_exception(
        self, mock_latex, mock_syntax, mock_math, mock_figure, mock_reference, mock_citation
    ):
        """Test enhanced validation with exception."""
        mock_citation.side_effect = Exception("Test error")

        # Mock other validators to return valid results
        mock_result = MagicMock()
        mock_result.validator_name = "TestValidator"
        mock_result.metadata = {}
        mock_result.errors = []

        for mock_validator in [mock_reference, mock_figure, mock_math, mock_syntax, mock_latex]:
            mock_instance = mock_validator.return_value
            mock_instance.validate.return_value = mock_result

        result = self.validator.run_enhanced_validation()
        assert result is True
        assert len(self.validator.warnings) >= 1
        assert any("validation failed" in warning for warning in self.validator.warnings)

    def test_validate_full_success(self):
        """Test full validation with all checks passing."""
        # Set up a complete valid manuscript
        self._create_valid_manuscript()

        result = self.validator.validate()
        assert result is True

    def test_validate_directory_failure(self):
        """Test validation fails early on directory structure."""
        validator = ManuscriptValidator("/nonexistent/path")
        result = validator.validate()
        assert result is False

    def test_print_summary_success(self):
        """Test print summary with no errors or warnings."""
        with patch("builtins.print") as mock_print:
            self.validator.print_summary()

        # Check that success message was printed
        printed_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "PASSED" in printed_text
        assert "No issues found" in printed_text

    def test_print_summary_with_errors(self):
        """Test print summary with errors."""
        self.validator.errors = ["Test error 1", "Test error 2"]

        with patch("builtins.print") as mock_print:
            self.validator.print_summary()

        printed_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "FAILED" in printed_text
        assert "ERRORS" in printed_text
        assert "Test error 1" in printed_text

    def test_print_summary_with_warnings(self):
        """Test print summary with warnings only."""
        self.validator.warnings = ["Test warning 1", "Test warning 2"]

        with patch("builtins.print") as mock_print:
            self.validator.print_summary()

        printed_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "PASSED with warnings" in printed_text
        assert "WARNINGS" in printed_text

    def test_print_summary_with_info(self):
        """Test print summary with info messages."""
        self.validator.info_messages = ["Test info 1"]

        with patch("builtins.print") as mock_print:
            self.validator.print_summary()

        printed_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "INFO" in printed_text

    @patch("rxiv_maker.scripts.validate_manuscript.ENHANCED_VALIDATION_AVAILABLE", True)
    def test_print_validation_statistics(self):
        """Test printing validation statistics."""
        # Set up validation metadata
        self.validator.validation_metadata = {
            "CitationValidator": {"total_citations": 10, "unique_citations": 8, "bibliography_keys": 15},
            "ReferenceValidator": {"total_labels_defined": 5, "total_references_used": 4},
            "FigureValidator": {"total_figures": 3, "available_files": 3},
        }
        self.validator.show_stats = True

        with patch("builtins.print") as mock_print:
            self.validator._print_validation_statistics()

        printed_text = " ".join(str(call) for call in mock_print.call_args_list)
        assert "VALIDATION STATISTICS" in printed_text
        assert "Citation" in printed_text
        assert "Reference" in printed_text
        assert "Figure" in printed_text

    def _create_valid_manuscript(self):
        """Helper method to create a valid manuscript structure."""
        # Create required files
        config_data = {"title": "Test Title", "authors": ["Author 1"], "date": "2024-01-01", "keywords": ["test"]}
        config_path = self.manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        main_content = """
        # Abstract
        Test abstract

        # Introduction
        Test introduction

        # Methods
        Test methods
        """
        (self.manuscript_path / "01_MAIN.md").write_text(main_content)

        bib_content = "@article{test2024, title={Test}, year={2024}}"
        (self.manuscript_path / "03_REFERENCES.bib").write_text(bib_content)

        # Create required directories
        (self.manuscript_path / "FIGURES").mkdir()


class TestMainFunction:
    """Test suite for main function."""

    @patch("sys.argv", ["validate_manuscript.py", "/test/path"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    def test_main_basic(self, mock_validator_class):
        """Test main function with basic arguments."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator

        with patch("sys.exit") as mock_exit:
            main()

        mock_validator_class.assert_called_once()
        mock_validator.validate.assert_called_once()
        mock_validator.print_summary.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--verbose"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    @patch("logging.getLogger")
    def test_main_verbose(self, mock_logger, mock_validator_class):
        """Test main function with verbose flag."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator

        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        with patch("sys.exit"):
            main()

        mock_logger_instance.setLevel.assert_called()

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--quiet"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    @patch("logging.getLogger")
    def test_main_quiet(self, mock_logger, mock_validator_class):
        """Test main function with quiet flag."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator

        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        with patch("sys.exit"):
            main()

        mock_logger_instance.setLevel.assert_called()

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--basic-only"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    def test_main_basic_only(self, mock_validator_class):
        """Test main function with basic-only flag."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator

        with patch("sys.exit"):
            main()

        # Check that skip_enhanced=True was passed
        args, kwargs = mock_validator_class.call_args
        assert kwargs.get("skip_enhanced") is True

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--show-stats"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    def test_main_show_stats(self, mock_validator_class):
        """Test main function with show-stats flag."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = True
        mock_validator_class.return_value = mock_validator

        with patch("sys.exit"):
            main()

        # Check that show_stats=True was passed
        args, kwargs = mock_validator_class.call_args
        assert kwargs.get("show_stats") is True

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--detailed"])
    @patch("subprocess.run")
    @patch("sys.exit")
    def test_main_detailed(self, mock_exit, mock_subprocess):
        """Test main function with detailed flag."""
        mock_result = MagicMock()
        mock_result.returncode = 1  # Simulate validation failure
        mock_subprocess.return_value = mock_result

        main()

        mock_subprocess.assert_called_once()
        # The detailed path calls sys.exit with the returncode from subprocess
        mock_exit.assert_called_with(1)

    @patch("sys.argv", ["validate_manuscript.py", "/test/path", "--detailed"])
    @patch("subprocess.run")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_detailed_file_not_found(self, mock_print, mock_exit, mock_subprocess):
        """Test main function with detailed flag when command not found."""
        mock_subprocess.side_effect = FileNotFoundError()

        main()

        # The detailed path calls sys.exit with 1 when FileNotFoundError
        mock_exit.assert_called_with(1)

    @patch("sys.argv", ["validate_manuscript.py", "/test/path"])
    @patch("rxiv_maker.scripts.validate_manuscript.ManuscriptValidator")
    def test_main_validation_failure(self, mock_validator_class):
        """Test main function when validation fails."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = False
        mock_validator_class.return_value = mock_validator

        with patch("sys.exit") as mock_exit:
            main()

        mock_exit.assert_called_once_with(1)


class TestValidationErrorFormatting:
    """Test suite for validation error formatting methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ManuscriptValidator("/test/path")

    def test_format_validation_error_minimal(self):
        """Test formatting validation error with minimal information."""
        mock_error = MagicMock()
        mock_error.file_path = None
        mock_error.line_number = None
        mock_error.column = None
        mock_error.message = "Test error message"
        mock_error.suggestion = None

        result = self.validator._format_validation_error(mock_error)
        assert result == "Test error message"

    def test_format_validation_error_with_file(self):
        """Test formatting validation error with file path."""
        mock_error = MagicMock()
        mock_error.file_path = "test.py"
        mock_error.line_number = None
        mock_error.column = None
        mock_error.message = "Test error message"
        mock_error.suggestion = None

        result = self.validator._format_validation_error(mock_error)
        assert result == "(test.py) Test error message"

    def test_format_validation_error_with_location(self):
        """Test formatting validation error with full location."""
        mock_error = MagicMock()
        mock_error.file_path = "test.py"
        mock_error.line_number = 10
        mock_error.column = 5
        mock_error.message = "Test error message"
        mock_error.suggestion = None

        result = self.validator._format_validation_error(mock_error)
        assert result == "(test.py:10:5) Test error message"

    def test_format_validation_error_with_suggestion(self):
        """Test formatting validation error with suggestion."""
        mock_error = MagicMock()
        mock_error.file_path = None
        mock_error.line_number = None
        mock_error.column = None
        mock_error.message = "Test error message"
        mock_error.suggestion = "Try this fix"

        result = self.validator._format_validation_error(mock_error)
        assert result == "Test error message → Try this fix"

    def test_process_validation_result_errors(self):
        """Test processing validation result with errors."""
        from unittest.mock import MagicMock

        # Mock ValidationLevel enum
        mock_validation_level = MagicMock()
        mock_validation_level.ERROR = "ERROR"
        mock_validation_level.WARNING = "WARNING"
        mock_validation_level.INFO = "INFO"

        with patch("rxiv_maker.scripts.validate_manuscript.ValidationLevel", mock_validation_level):
            mock_result = MagicMock()
            mock_result.validator_name = "TestValidator"
            mock_result.metadata = {"test": "data"}

            mock_error = MagicMock()
            mock_error.level = "ERROR"
            mock_error.file_path = None
            mock_error.line_number = None
            mock_error.column = None
            mock_error.message = "Test error"
            mock_error.suggestion = None

            mock_result.errors = [mock_error]

            result = self.validator._process_validation_result(mock_result)

            assert result is False
            assert len(self.validator.errors) == 1
            assert "Test error" in self.validator.errors[0]
            assert self.validator.validation_metadata["TestValidator"] == {"test": "data"}

    def test_process_validation_result_warnings(self):
        """Test processing validation result with warnings."""
        from unittest.mock import MagicMock

        # Mock ValidationLevel enum
        mock_validation_level = MagicMock()
        mock_validation_level.ERROR = "ERROR"
        mock_validation_level.WARNING = "WARNING"
        mock_validation_level.INFO = "INFO"

        with patch("rxiv_maker.scripts.validate_manuscript.ValidationLevel", mock_validation_level):
            mock_result = MagicMock()
            mock_result.validator_name = "TestValidator"
            mock_result.metadata = {}

            mock_warning = MagicMock()
            mock_warning.level = "WARNING"
            mock_warning.file_path = None
            mock_warning.line_number = None
            mock_warning.column = None
            mock_warning.message = "Test warning"
            mock_warning.suggestion = None

            mock_result.errors = [mock_warning]

            result = self.validator._process_validation_result(mock_result)

            assert result is True
            assert len(self.validator.warnings) == 1
            assert "Test warning" in self.validator.warnings[0]
