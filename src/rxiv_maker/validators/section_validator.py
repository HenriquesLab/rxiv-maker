"""Section validator for checking recommended manuscript sections.

This validator checks if manuscripts include important sections that are
commonly required by journals, such as:
- Data Availability
- Code Availability
- Author Contributions
- Acknowledgements
- Funding
- Competing Interests

Missing sections generate warnings (not errors) to help authors ensure
their manuscript is complete before submission.
"""

import re

from ..utils.file_helpers import find_manuscript_md
from .base_validator import BaseValidator, ValidationError, ValidationLevel, ValidationResult


class SectionValidator(BaseValidator):
    """Validator for checking recommended manuscript sections."""

    # Required sections that should generate warnings if missing
    RECOMMENDED_SECTIONS = {
        "data availability": {
            "patterns": [
                r"##\s+Data\s+Availability",
                r"##\s+Data\s+and\s+Code\s+Availability",
            ],
            "suggestion": "Add a '## Data Availability' section describing where your data can be accessed",
        },
        "code availability": {
            "patterns": [
                r"##\s+Code\s+Availability",
                r"##\s+Data\s+and\s+Code\s+Availability",
                r"##\s+Software\s+Availability",
            ],
            "suggestion": "Add a '## Code Availability' section with links to code repositories",
        },
        "author contributions": {
            "patterns": [
                r"##\s+Author\s+Contributions?",
                r"##\s+Contributions?",
            ],
            "suggestion": "Add an '## Author Contributions' section describing each author's role",
        },
        "acknowledgements": {
            "patterns": [
                r"##\s+Acknowledgements?",
                r"##\s+Acknowledgments?",
            ],
            "suggestion": "Add an '## Acknowledgements' section to thank contributors",
        },
        "funding": {
            "patterns": [
                r"##\s+Funding",
                r"##\s+Financial\s+Support",
                r"##\s+Grant\s+Information",
            ],
            "suggestion": "Add a '## Funding' section declaring funding sources or stating 'This research received no external funding.'",
        },
        "competing interests": {
            "patterns": [
                r"##\s+Competing\s+Interests?",
                r"##\s+Conflicts?\s+of\s+Interest",
                r"##\s+Disclosure",
            ],
            "suggestion": "Add a '## Competing Interests' section, even if just to state 'The authors declare no competing interests.'",
        },
    }

    def validate(self) -> ValidationResult:
        """Check for recommended manuscript sections.

        Returns:
            ValidationResult with warnings for missing sections
        """
        errors: list[ValidationError] = []
        metadata = {
            "missing_sections": [],
            "found_sections": [],
        }

        # Find manuscript file
        try:
            manuscript_file = find_manuscript_md(self.manuscript_path)
        except (FileNotFoundError, ValueError) as e:
            return ValidationResult(
                validator_name=self.name,
                errors=[
                    self._create_error(
                        level=ValidationLevel.ERROR,
                        message=f"Could not find manuscript file: {e}",
                    )
                ],
                metadata=metadata,
            )

        # Read manuscript content
        content = self._read_file_safely(manuscript_file)
        if content is None:
            return ValidationResult(
                validator_name=self.name,
                errors=[
                    self._create_error(
                        level=ValidationLevel.ERROR,
                        message=f"Could not read manuscript file: {manuscript_file}",
                    )
                ],
                metadata=metadata,
            )

        # Check for each recommended section
        for section_name, section_info in self.RECOMMENDED_SECTIONS.items():
            found = False
            for pattern in section_info["patterns"]:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    metadata["found_sections"].append(section_name)
                    break

            if not found:
                metadata["missing_sections"].append(section_name)
                errors.append(
                    self._create_error(
                        level=ValidationLevel.WARNING,
                        message=f"Recommended section '{section_name.title()}' not found",
                        file_path=manuscript_file,
                        suggestion=section_info["suggestion"],
                    )
                )

        return ValidationResult(
            validator_name=self.name,
            errors=errors,
            metadata=metadata,
        )
