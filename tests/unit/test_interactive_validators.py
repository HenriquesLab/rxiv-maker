"""Tests for interactive prompt validators."""

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError

from src.rxiv_maker.cli.interactive import (
    GithubOrgValidator,
    NumericChoiceValidator,
    PathValidator,
    RepositoryNameValidator,
    TemplateValidator,
)


class TestPathValidator:
    """Test path validator."""

    def test_empty_path(self):
        """Test that empty paths are rejected."""
        validator = PathValidator()
        doc = Document("")

        with pytest.raises(ValidationError, match="Path cannot be empty"):
            validator.validate(doc)

    def test_nonexistent_path_when_must_exist(self, tmp_path):
        """Test that non-existent paths are rejected when must_exist=True."""
        validator = PathValidator(must_exist=True)
        nonexistent = tmp_path / "does_not_exist"
        doc = Document(str(nonexistent))

        with pytest.raises(ValidationError, match="Path does not exist"):
            validator.validate(doc)

    def test_valid_directory(self, tmp_path):
        """Test that valid directories pass validation."""
        validator = PathValidator(must_exist=True, must_be_dir=True)
        doc = Document(str(tmp_path))

        # Should not raise
        validator.validate(doc)

    def test_file_when_directory_required(self, tmp_path):
        """Test that files are rejected when directories are required."""
        validator = PathValidator(must_exist=True, must_be_dir=True)
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        doc = Document(str(test_file))

        with pytest.raises(ValidationError, match="must be a directory"):
            validator.validate(doc)

    def test_expanduser_support(self, tmp_path, monkeypatch):
        """Test that ~ is expanded properly."""
        # This test might need adjustment based on actual expanduser behavior
        validator = PathValidator(must_exist=False)
        doc = Document("~/test")

        # Should not raise for non-existent path when must_exist=False
        validator.validate(doc)


class TestGithubOrgValidator:
    """Test GitHub organization name validator."""

    def test_valid_org_names(self):
        """Test that valid org names pass validation."""
        validator = GithubOrgValidator()
        valid_names = ["test-org", "MyOrg", "org123", "a"]

        for name in valid_names:
            doc = Document(name)
            # Should not raise
            validator.validate(doc)

    def test_empty_org_name(self):
        """Test that empty org names are allowed (optional field)."""
        validator = GithubOrgValidator()
        doc = Document("")

        # Should not raise (optional field)
        validator.validate(doc)

    def test_org_with_invalid_characters(self):
        """Test that org names with invalid characters are rejected."""
        validator = GithubOrgValidator()
        invalid_names = ["org_name", "org.name", "org name", "org/name"]

        for name in invalid_names:
            doc = Document(name)
            with pytest.raises(ValidationError):
                validator.validate(doc)

    def test_org_starts_with_hyphen(self):
        """Test that org names starting with hyphen are rejected."""
        validator = GithubOrgValidator()
        doc = Document("-org")

        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validator.validate(doc)

    def test_org_ends_with_hyphen(self):
        """Test that org names ending with hyphen are rejected."""
        validator = GithubOrgValidator()
        doc = Document("org-")

        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validator.validate(doc)


class TestNumericChoiceValidator:
    """Test numeric choice validator."""

    def test_valid_choice(self):
        """Test that valid numeric choices pass validation."""
        validator = NumericChoiceValidator(max_choice=5)
        for num in range(1, 6):
            doc = Document(str(num))
            # Should not raise
            validator.validate(doc)

    def test_choice_too_low(self):
        """Test that choices below min are rejected."""
        validator = NumericChoiceValidator(max_choice=5, min_choice=1)
        doc = Document("0")

        with pytest.raises(ValidationError, match="Enter a number between"):
            validator.validate(doc)

    def test_choice_too_high(self):
        """Test that choices above max are rejected."""
        validator = NumericChoiceValidator(max_choice=5)
        doc = Document("6")

        with pytest.raises(ValidationError, match="Enter a number between"):
            validator.validate(doc)

    def test_non_numeric_input(self):
        """Test that non-numeric input is rejected."""
        validator = NumericChoiceValidator(max_choice=5)
        doc = Document("abc")

        with pytest.raises(ValidationError, match="Please enter a valid number"):
            validator.validate(doc)

    def test_empty_input_not_allowed(self):
        """Test that empty input is rejected when not allowed."""
        validator = NumericChoiceValidator(max_choice=5, allow_empty=False)
        doc = Document("")

        with pytest.raises(ValidationError, match="Please enter a number"):
            validator.validate(doc)

    def test_empty_input_allowed(self):
        """Test that empty input is accepted when allowed."""
        validator = NumericChoiceValidator(max_choice=5, allow_empty=True)
        doc = Document("")

        # Should not raise
        validator.validate(doc)


class TestTemplateValidator:
    """Test template name validator."""

    def test_valid_templates(self):
        """Test that valid template names pass validation."""
        validator = TemplateValidator()
        valid_templates = ["default", "minimal", "journal", "preprint"]

        for template in valid_templates:
            doc = Document(template)
            # Should not raise
            validator.validate(doc)

    def test_case_insensitive(self):
        """Test that template validation is case-insensitive."""
        validator = TemplateValidator()
        doc = Document("DEFAULT")

        # Should not raise
        validator.validate(doc)

    def test_invalid_template(self):
        """Test that invalid template names are rejected."""
        validator = TemplateValidator()
        doc = Document("invalid-template")

        with pytest.raises(ValidationError, match="Invalid template"):
            validator.validate(doc)

    def test_empty_template(self):
        """Test that empty template is allowed (defaults to 'default')."""
        validator = TemplateValidator()
        doc = Document("")

        # Should not raise (empty is allowed)
        validator.validate(doc)


class TestRepositoryNameValidator:
    """Test repository name validator."""

    def test_valid_repo_names(self):
        """Test that valid repository names pass validation."""
        validator = RepositoryNameValidator()
        valid_names = ["test-repo", "MyRepo", "repo123", "my-test-repo", "a"]

        for name in valid_names:
            doc = Document(name)
            # Should not raise
            validator.validate(doc)

    def test_empty_repo_name(self):
        """Test that empty repository names are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("")

        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate(doc)

    def test_repo_name_too_long(self):
        """Test that repository names exceeding 39 characters are rejected."""
        validator = RepositoryNameValidator()
        long_name = "a" * 40
        doc = Document(long_name)

        with pytest.raises(ValidationError, match="cannot exceed 39 characters"):
            validator.validate(doc)

    def test_repo_name_with_underscores(self):
        """Test that repository names with underscores are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("repo_name")

        with pytest.raises(ValidationError, match="no underscores"):
            validator.validate(doc)

    def test_repo_name_with_invalid_characters(self):
        """Test that repository names with invalid characters are rejected."""
        validator = RepositoryNameValidator()
        invalid_names = ["repo.name", "repo name", "repo/name", "repo\\name"]

        for name in invalid_names:
            doc = Document(name)
            with pytest.raises(ValidationError):
                validator.validate(doc)

    def test_repo_name_starts_with_hyphen(self):
        """Test that repository names starting with hyphen are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("-repo")

        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validator.validate(doc)

    def test_repo_name_ends_with_hyphen(self):
        """Test that repository names ending with hyphen are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("repo-")

        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validator.validate(doc)

    def test_repo_name_consecutive_hyphens(self):
        """Test that repository names with consecutive hyphens are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("repo--name")

        with pytest.raises(ValidationError, match="cannot contain consecutive hyphens"):
            validator.validate(doc)

    def test_repo_name_with_spaces(self):
        """Test that repository names with spaces are rejected."""
        validator = RepositoryNameValidator()
        doc = Document("repo name")

        # Spaces are caught by the general character check
        with pytest.raises(ValidationError, match="can only contain"):
            validator.validate(doc)

    def test_duplicate_repo_name(self):
        """Test that duplicate repository names are rejected."""
        existing_names = ["existing-repo", "another-repo"]
        validator = RepositoryNameValidator(existing_names=existing_names)
        doc = Document("existing-repo")

        with pytest.raises(ValidationError, match="already exists"):
            validator.validate(doc)

    def test_non_duplicate_repo_name(self):
        """Test that non-duplicate repository names pass validation."""
        existing_names = ["existing-repo"]
        validator = RepositoryNameValidator(existing_names=existing_names)
        doc = Document("new-repo")

        # Should not raise
        validator.validate(doc)
