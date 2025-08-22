"""Mathematical expression validator for checking LaTeX math syntax."""

import os
import re
from typing import Any

from .base_validator import BaseValidator, ValidationLevel, ValidationResult


class MathValidator(BaseValidator):
    """Validates mathematical expressions and LaTeX math syntax."""

    # Math patterns based on codebase analysis
    MATH_PATTERNS = {
        "inline_math": re.compile(r"\$([^$]+)\$"),  # $...$
        "display_math": re.compile(r"\$\$([^$]+)\$\$"),  # $$...$$
        "attributed_math": re.compile(r"\$\$(.*?)\$\$\s*\{([^}]*#[^}]*)\}"),  # $$...$${#eq:label}
        "environment_math": re.compile(r"\\begin\{([^}]+)\}.*?\\end\{\1\}", re.DOTALL),
    }

    # Valid LaTeX math environments
    VALID_ENVIRONMENTS = {
        "equation",
        "align",
        "gather",
        "multiline",
        "split",
        "aligned",
        "gathered",
        "cases",
        "matrix",
        "pmatrix",
        "bmatrix",
        "vmatrix",
        "Vmatrix",
        "array",
        "eqnarray",
    }

    # Common LaTeX math commands and their argument patterns
    MATH_COMMANDS = {
        # Basic commands with arguments
        r"\\frac": 2,  # \frac{numerator}{denominator}
        r"\\sqrt": 1,  # \sqrt{expression} or \sqrt[n]{expression}
        r"\\text": 1,  # \text{content}
        r"\\textbf": 1,  # \textbf{content}
        r"\\textit": 1,  # \textit{content}
        r"\\mathrm": 1,  # \mathrm{content}
        r"\\mathbf": 1,  # \mathbf{content}
        r"\\mathcal": 1,  # \mathcal{content}
        r"\\label": 1,  # \label{eq:name}
        # Operators and functions
        r"\\sum": 0,  # \sum, \sum_{lower}^{upper}
        r"\\int": 0,  # \int, \int_{lower}^{upper}
        r"\\lim": 0,  # \lim, \lim_{x \to a}
        r"\\prod": 0,  # \prod
        r"\\sin": 0,  # \sin
        r"\\cos": 0,  # \cos
        r"\\tan": 0,  # \tan
        r"\\exp": 0,  # \exp
        r"\\log": 0,  # \log
        r"\\ln": 0,  # \ln
        r"\\min": 0,  # \min
        r"\\max": 0,  # \max
        r"\\sup": 0,  # \sup
        r"\\inf": 0,  # \inf
        r"\\arg": 0,  # \arg
        r"\\det": 0,  # \det
        r"\\dim": 0,  # \dim
        r"\\ker": 0,  # \ker
        r"\\gcd": 0,  # \gcd
        r"\\lcm": 0,  # \lcm
        # Greek letters (lowercase)
        r"\\alpha": 0,  # α
        r"\\beta": 0,  # β
        r"\\gamma": 0,  # γ
        r"\\delta": 0,  # δ
        r"\\epsilon": 0,  # ε
        r"\\varepsilon": 0,  # ε (variant)
        r"\\zeta": 0,  # ζ
        r"\\eta": 0,  # η
        r"\\theta": 0,  # θ
        r"\\vartheta": 0,  # θ (variant)
        r"\\iota": 0,  # ι
        r"\\kappa": 0,  # κ
        r"\\lambda": 0,  # λ
        r"\\mu": 0,  # μ
        r"\\nu": 0,  # ν
        r"\\xi": 0,  # ξ
        r"\\pi": 0,  # π
        r"\\varpi": 0,  # π (variant)
        r"\\rho": 0,  # ρ
        r"\\varrho": 0,  # ρ (variant)
        r"\\sigma": 0,  # σ
        r"\\varsigma": 0,  # σ (variant)
        r"\\tau": 0,  # τ
        r"\\upsilon": 0,  # υ
        r"\\phi": 0,  # φ
        r"\\varphi": 0,  # φ (variant)
        r"\\chi": 0,  # χ
        r"\\psi": 0,  # ψ
        r"\\omega": 0,  # ω
        # Greek letters (uppercase)
        r"\\Gamma": 0,  # Γ
        r"\\Delta": 0,  # Δ
        r"\\Theta": 0,  # Θ
        r"\\Lambda": 0,  # Λ
        r"\\Xi": 0,  # Ξ
        r"\\Pi": 0,  # Π
        r"\\Sigma": 0,  # Σ
        r"\\Upsilon": 0,  # Υ
        r"\\Phi": 0,  # Φ
        r"\\Psi": 0,  # Ψ
        r"\\Omega": 0,  # Ω
        # Mathematical operators
        r"\\partial": 0,  # ∂
        r"\\nabla": 0,  # ∇
        r"\\infty": 0,  # ∞
        r"\\pm": 0,  # ±
        r"\\mp": 0,  # ∓
        r"\\times": 0,  # ×
        r"\\div": 0,  # ÷
        r"\\cdot": 0,  # ⋅
        r"\\circ": 0,  # ∘
        r"\\bullet": 0,  # •
        r"\\ast": 0,  # *
        r"\\star": 0,  # ⋆
        r"\\oplus": 0,  # ⊕
        r"\\ominus": 0,  # ⊖
        r"\\otimes": 0,  # ⊗
        r"\\oslash": 0,  # ⊘
        r"\\odot": 0,  # ⊙
        r"\\dagger": 0,  # †
        r"\\ddagger": 0,  # ‡
        r"\\amalg": 0,  # ⨿
        # Relations
        r"\\leq": 0,  # ≤
        r"\\geq": 0,  # ≥
        r"\\neq": 0,  # ≠
        r"\\equiv": 0,  # ≡
        r"\\approx": 0,  # ≈
        r"\\cong": 0,  # ≅
        r"\\simeq": 0,  # ≃
        r"\\sim": 0,  # ∼
        r"\\propto": 0,  # ∝
        r"\\ll": 0,  # ≪
        r"\\gg": 0,  # ≫
        r"\\prec": 0,  # ≺
        r"\\succ": 0,  # ≻
        r"\\preceq": 0,  # ⪯
        r"\\succeq": 0,  # ⪰
        r"\\subset": 0,  # ⊂
        r"\\supset": 0,  # ⊃
        r"\\subseteq": 0,  # ⊆
        r"\\supseteq": 0,  # ⊇
        r"\\in": 0,  # ∈
        r"\\notin": 0,  # ∉
        r"\\ni": 0,  # ∋
        r"\\perp": 0,  # ⊥
        r"\\parallel": 0,  # ∥
        r"\\mid": 0,  # ∣
        r"\\nmid": 0,  # ∤
        # Arrows
        r"\\leftarrow": 0,  # ←
        r"\\rightarrow": 0,  # →
        r"\\leftrightarrow": 0,  # ↔
        r"\\Leftarrow": 0,  # ⇐
        r"\\Rightarrow": 0,  # ⇒
        r"\\Leftrightarrow": 0,  # ⇔
        r"\\uparrow": 0,  # ↑
        r"\\downarrow": 0,  # ↓
        r"\\updownarrow": 0,  # ↕
        r"\\Uparrow": 0,  # ⇑
        r"\\Downarrow": 0,  # ⇓
        r"\\Updownarrow": 0,  # ⇕
        r"\\mapsto": 0,  # ↦
        r"\\longmapsto": 0,  # ⟼
        r"\\to": 0,  # → (alias)
        # Accents and decorations
        r"\\hat": 1,  # \hat{x}
        r"\\bar": 1,  # \bar{x}
        r"\\dot": 1,  # \dot{x}
        r"\\ddot": 1,  # \ddot{x}
        r"\\vec": 1,  # \vec{x}
        r"\\tilde": 1,  # \tilde{x}
        r"\\widetilde": 1,  # \widetilde{x}
        r"\\check": 1,  # \check{x}
        r"\\breve": 1,  # \breve{x}
        r"\\acute": 1,  # \acute{x}
        r"\\grave": 1,  # \grave{x}
        r"\\mathring": 1,  # \mathring{x}
        r"\\widehat": 1,  # \widehat{x}
        r"\\overline": 1,  # \overline{x}
        r"\\underline": 1,  # \underline{x}
        # Miscellaneous
        r"\\prime": 0,  # ′
        r"\\emptyset": 0,  # ∅
        r"\\varnothing": 0,  # ∅ (variant)
        r"\\forall": 0,  # ∀
        r"\\exists": 0,  # ∃
        r"\\nexists": 0,  # ∄
        r"\\neg": 0,  # ¬
        r"\\lnot": 0,  # ¬ (alias)
        r"\\land": 0,  # ∧
        r"\\lor": 0,  # ∨
        r"\\ell": 0,  # ℓ
        r"\\hbar": 0,  # ℏ
        r"\\imath": 0,  # ı
        r"\\jmath": 0,  # ȷ
        r"\\wp": 0,  # ℘
        r"\\Re": 0,  # ℜ
        r"\\Im": 0,  # ℑ
        r"\\aleph": 0,  # ℵ
        r"\\beth": 0,  # ℶ
        r"\\gimel": 0,  # ℷ
        r"\\daleth": 0,  # ℸ
        # Delimiter commands
        r"\\left": 0,  # \left( \left[ \left{ etc.
        r"\\right": 0,  # \right) \right] \right} etc.
        r"\\big": 0,  # \big( \big[ etc.
        r"\\Big": 0,  # \Big( \Big[ etc.
        r"\\bigg": 0,  # \bigg( \bigg[ etc.
        r"\\Bigg": 0,  # \Bigg( \Bigg[ etc.
        r"\\bigl": 0,  # \bigl( \bigl[ etc.
        r"\\bigr": 0,  # \bigr) \bigr] etc.
        r"\\Bigl": 0,  # \Bigl( \Bigl[ etc.
        r"\\Bigr": 0,  # \Bigr) \Bigr] etc.
        r"\\biggl": 0,  # \biggl( \biggl[ etc.
        r"\\biggr": 0,  # \biggr) \biggr] etc.
        r"\\Biggl": 0,  # \Biggl( \Biggl[ etc.
        r"\\Biggr": 0,  # \Biggr) \Biggr] etc.
    }

    # Delimiter pairs that should be balanced
    DELIMITER_PAIRS = [
        (r"\{", r"\}"),  # Braces
        (r"\(", r"\)"),  # Parentheses
        (r"\[", r"\]"),  # Square brackets
        (r"\\left\(", r"\\right\)"),  # \left( \right)
        (r"\\left\[", r"\\right\]"),  # \left[ \right]
        (r"\\left\{", r"\\right\}"),  # \left{ \right}
    ]

    def __init__(self, manuscript_path: str):
        """Initialize math validator.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        super().__init__(manuscript_path)
        self.found_math: list[dict] = []
        self.equation_labels: set[str] = set()

    def validate(self) -> ValidationResult:
        """Validate mathematical expressions in manuscript files."""
        errors = []
        metadata = {}

        # Process manuscript files
        files_to_check = [
            ("01_MAIN.md", "main"),
            ("02_SUPPLEMENTARY_INFO.md", "supplementary"),
        ]

        for filename, file_type in files_to_check:
            file_path = os.path.join(self.manuscript_path, filename)
            if os.path.exists(file_path):
                file_errors = self._validate_file_math(file_path, file_type)
                errors.extend(file_errors)

        # Add statistics to metadata
        metadata.update(self._generate_math_statistics())

        return ValidationResult("MathValidator", errors, metadata)

    def _validate_file_math(self, file_path: str, file_type: str) -> list:
        """Validate mathematical expressions in a specific file."""
        errors = []
        content = self._read_file_safely(file_path)

        if not content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Could not read file: {os.path.basename(file_path)}",
                    file_path=file_path,
                )
            )
            return errors

        # Find and validate all math expressions
        math_errors = self._find_and_validate_math(content, file_path, file_type)
        errors.extend(math_errors)

        return errors

    def _find_and_validate_math(self, content: str, file_path: str, file_type: str) -> list:
        """Find and validate all mathematical expressions in content."""
        errors = []
        processed_ranges = []

        # Skip content within code blocks to avoid false positives
        protected_content = self._protect_code_blocks(content)

        # First, validate attributed math expressions (with labels) to avoid
        # double-matching
        for match in self.MATH_PATTERNS["attributed_math"].finditer(protected_content):
            if "XXPROTECTEDCODEXX" in match.group(0):
                continue

            line_num = protected_content[: match.start()].count("\n") + 1
            math_content = match.group(1)
            attrs_content = match.group(2)

            math_info = {
                "type": "attributed",
                "content": math_content,
                "attributes": attrs_content,
                "line": line_num,
                "file": os.path.basename(file_path),
                "file_type": file_type,
                "full_match": match.group(0),
            }

            self.found_math.append(math_info)

            math_errors = self._validate_math_expression(math_info, file_path, line_num)
            errors.extend(math_errors)

            # Validate equation label
            label_errors = self._validate_equation_label(math_info, file_path, line_num)
            errors.extend(label_errors)

            # Store the range as processed to avoid display_math pattern match
            processed_ranges.append((match.start(), match.end()))

        # Validate inline math expressions, but skip overlapping ranges
        for match in self.MATH_PATTERNS["inline_math"].finditer(protected_content):
            if "XXPROTECTEDCODEXX" in match.group(0):
                continue  # Skip protected code

            # Check if this match overlaps with any processed attributed_math ranges
            match_start, match_end = match.start(), match.end()
            is_overlapping = any(
                not (match_end <= proc_start or match_start >= proc_end) for proc_start, proc_end in processed_ranges
            )

            if is_overlapping:
                continue  # Skip this match as it overlaps with attributed math

            line_num = protected_content[: match.start()].count("\n") + 1
            math_content = match.group(1)

            math_info = {
                "type": "inline",
                "content": math_content,
                "line": line_num,
                "file": os.path.basename(file_path),
                "file_type": file_type,
                "full_match": match.group(0),
            }

            self.found_math.append(math_info)

            math_errors = self._validate_math_expression(math_info, file_path, line_num)
            errors.extend(math_errors)

        # Then validate display math expressions, but skip overlapping ranges
        for match in self.MATH_PATTERNS["display_math"].finditer(protected_content):
            if "XXPROTECTEDCODEXX" in match.group(0):
                continue  # Skip protected code

            # Check if this match overlaps with any processed attributed_math ranges
            match_start, match_end = match.start(), match.end()
            is_overlapping = any(
                not (match_end <= proc_start or match_start >= proc_end) for proc_start, proc_end in processed_ranges
            )

            if is_overlapping:
                continue  # Skip this match as it overlaps with attributed math

            line_num = protected_content[: match.start()].count("\n") + 1
            math_content = match.group(1)

            math_info = {
                "type": "display",
                "content": math_content,
                "line": line_num,
                "file": os.path.basename(file_path),
                "file_type": file_type,
                "full_match": match.group(0),
            }

            self.found_math.append(math_info)

            math_errors = self._validate_math_expression(math_info, file_path, line_num)
            errors.extend(math_errors)

        return errors

    def _validate_math_expression(self, math_info: dict, file_path: str, line_num: int) -> list:
        """Validate a single mathematical expression."""
        errors = []
        math_content = math_info["content"]

        # Check for balanced delimiters
        delimiter_errors = self._check_balanced_delimiters(math_content, file_path, line_num)
        errors.extend(delimiter_errors)

        # Check for valid LaTeX environments
        env_errors = self._check_math_environments(math_content, file_path, line_num)
        errors.extend(env_errors)

        # Check for common syntax issues
        syntax_errors = self._check_math_syntax(math_content, file_path, line_num)
        errors.extend(syntax_errors)

        # Check for empty or whitespace-only math
        if not math_content.strip():
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Empty mathematical expression",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="Remove empty math delimiters or add content",
                    error_code="empty_math",
                )
            )

        return errors

    def _check_balanced_delimiters(self, math_content: str, file_path: str, line_num: int) -> list:
        """Check for balanced delimiters in math expression."""
        errors = []

        for open_delim, close_delim in self.DELIMITER_PAIRS:
            open_count = len(re.findall(open_delim, math_content))
            close_count = len(re.findall(close_delim, math_content))

            if open_count != close_count:
                delim_name = open_delim.replace("\\", "")  # Remove escapes for display
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Unbalanced {delim_name} delimiters in math expression",
                        file_path=file_path,
                        line_number=line_num,
                        context=math_content[:100] + "..." if len(math_content) > 100 else math_content,
                        suggestion=(f"Ensure every {open_delim} has a matching {close_delim}"),
                        error_code="unbalanced_delimiters",
                    )
                )

        return errors

    def _check_math_environments(self, math_content: str, file_path: str, line_num: int) -> list:
        """Check for valid LaTeX math environments."""
        errors = []

        # Find all environments in the math content
        for match in self.MATH_PATTERNS["environment_math"].finditer(math_content):
            env_name = match.group(1)

            if env_name not in self.VALID_ENVIRONMENTS:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Unknown or non-standard math environment: {env_name}",
                        file_path=file_path,
                        line_number=line_num,
                        context=match.group(0)[:100] + "..." if len(match.group(0)) > 100 else match.group(0),
                        suggestion=(
                            f"Use standard environments like: {', '.join(sorted(list(self.VALID_ENVIRONMENTS)[:5]))}"
                        ),
                        error_code="unknown_environment",
                    )
                )

        return errors

    def _check_math_syntax(self, math_content: str, file_path: str, line_num: int) -> list:
        """Check for common LaTeX math syntax issues."""
        errors = []

        # Check for unescaped special characters
        special_chars = ["&", "%", "#", "$"]
        for char in special_chars:
            if (
                char in math_content
                and f"\\{char}" not in math_content
                and not re.search(rf"\\[a-zA-Z]*{re.escape(char)}", math_content)
            ):
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Unescaped special character '{char}' in math",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=f"Use \\{char} to display the character literally",
                        error_code="unescaped_special_char",
                    )
                )

        # Check for common command syntax issues
        command_errors = self._check_command_syntax(math_content, file_path, line_num)
        errors.extend(command_errors)

        # Check for double dollar signs in display math (should be outside)
        if "$$" in math_content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "Nested dollar signs in math expression",
                    file_path=file_path,
                    line_number=line_num,
                    context=math_content,
                    suggestion=("Remove inner $$ - they should only surround the entire expression"),
                    error_code="nested_math_delimiters",
                )
            )

        return errors

    def _check_command_syntax(self, math_content: str, file_path: str, line_num: int) -> list:
        """Check LaTeX command syntax in math expressions."""
        errors = []

        # Find all LaTeX commands
        command_pattern = re.compile(r"\\([a-zA-Z]+)")

        for match in command_pattern.finditer(math_content):
            command = match.group(0)  # Full command including backslash
            command_name = match.group(1)  # Command name without backslash

            # Check if it's a known command that requires arguments
            for cmd_pattern, arg_count in self.MATH_COMMANDS.items():
                # Use the pattern directly since it's already properly escaped
                if re.match(cmd_pattern, command):
                    # Check if the command has the required number of arguments
                    remaining_content = math_content[match.end() :]
                    if arg_count > 0:
                        arg_errors = self._check_command_arguments(
                            command, arg_count, remaining_content, file_path, line_num
                        )
                        errors.extend(arg_errors)
                    break
            else:
                # Unknown command - might be valid but flag as info
                if len(command_name) > 1:  # Single letter commands are usually fine
                    errors.append(
                        self._create_error(
                            ValidationLevel.INFO,
                            f"Unknown or custom LaTeX command: {command}",
                            file_path=file_path,
                            line_number=line_num,
                            suggestion=("Ensure the command is defined or use standard LaTeX commands"),
                            error_code="unknown_command",
                        )
                    )

        return errors

    def _check_command_arguments(
        self,
        command: str,
        expected_args: int,
        remaining_content: str,
        file_path: str,
        line_num: int,
    ) -> list:
        """Check if a command has the expected number of arguments."""
        errors = []

        # Count braced arguments immediately following the command
        found_args = 0
        content = remaining_content.strip()

        while found_args < expected_args and content.startswith("{"):
            # Find matching closing brace, handling nested braces
            brace_count = 0
            pos = 0

            for i, char in enumerate(content):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        pos = i
                        break

            if brace_count == 0:  # Found matching brace
                found_args += 1
                content = content[pos + 1 :].strip()
            else:
                break  # Unmatched braces

        if found_args < expected_args:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    (f"Command {command} expects {expected_args} argument(s), found {found_args}"),
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=f"Provide all required arguments for {command}",
                    error_code="missing_command_arguments",
                )
            )

        return errors

    def _validate_equation_label(self, math_info: dict, file_path: str, line_num: int) -> list:
        """Validate equation labels in attributed math expressions."""
        errors = []
        attrs_content = math_info.get("attributes", "")

        # Extract equation label
        label_match = re.search(r"#eq:([a-zA-Z0-9_:-]+)", attrs_content)
        if label_match:
            label_id = label_match.group(1)

            # Check for duplicate labels
            if label_id in self.equation_labels:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Duplicate equation label: eq:{label_id}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="Use unique labels for each equation",
                        error_code="duplicate_equation_label",
                    )
                )
            else:
                self.equation_labels.add(label_id)

            # Check label format
            if not re.match(r"^[a-zA-Z0-9_:-]+$", label_id):
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Non-standard equation label format: {label_id}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Use letters, numbers, underscores, and hyphens for labels"),
                        error_code="non_standard_label",
                    )
                )

        # Check for environment specification
        env_match = re.search(r"\.([a-zA-Z]+)", attrs_content)
        if env_match:
            env_name = env_match.group(1)
            if env_name not in self.VALID_ENVIRONMENTS:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Unknown math environment specified: {env_name}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=(
                            f"Use standard environments: {', '.join(sorted(list(self.VALID_ENVIRONMENTS)[:5]))}"
                        ),
                        error_code="unknown_specified_environment",
                    )
                )

        return errors

    def _protect_code_blocks(self, content: str) -> str:
        """Protect code blocks from math validation."""
        # Protect fenced code blocks
        protected = re.sub(
            r"```.*?```",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            content,
            flags=re.DOTALL,
        )

        # Protect inline code
        protected = re.sub(
            r"`[^`]+`",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
        )

        # Protect Python code blocks {{py: ...}}
        protected = re.sub(
            r"\{\{py:.*?\}\}",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
            flags=re.DOTALL,
        )

        # Protect inline Python expressions {py: ...}
        protected = re.sub(
            r"\{py:[^}]+\}",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
        )

        return protected

    def _generate_math_statistics(self) -> dict[str, Any]:
        """Generate statistics about mathematical expressions."""
        stats: dict[str, Any] = {
            "total_math_expressions": len(self.found_math),
            "inline_math": 0,
            "display_math": 0,
            "attributed_math": 0,
            "unique_equation_labels": len(self.equation_labels),
            "math_by_file_type": {"main": 0, "supplementary": 0},
            "average_math_length": 0,
        }

        total_length = 0
        for math_expr in self.found_math:
            # Count by type
            math_type = math_expr["type"]
            if math_type == "inline":
                stats["inline_math"] = stats["inline_math"] + 1
            elif math_type == "display":
                stats["display_math"] = stats["display_math"] + 1
            elif math_type == "attributed":
                stats["attributed_math"] = stats["attributed_math"] + 1

            # Count by file type
            file_type_stats: dict[str, int] = stats["math_by_file_type"]
            file_type_stats[math_expr["file_type"]] += 1

            # Calculate length
            total_length += len(math_expr["content"])

        if len(self.found_math) > 0:
            stats["average_math_length"] = total_length / len(self.found_math)

        return stats
