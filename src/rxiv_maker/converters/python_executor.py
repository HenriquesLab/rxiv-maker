"""Python code execution for markdown commands.

This module provides execution of Python code within markdown documents.
It includes output capture and error handling with comprehensive reporting.
"""

import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class PythonExecutionError(Exception):
    """Exception raised during Python code execution."""

    pass


class PythonExecutor:
    """Python code executor for markdown commands."""

    def __init__(self, timeout: int = 10, max_output_length: int = 10000):
        """Initialize Python executor.

        Args:
            timeout: Maximum execution time in seconds
            max_output_length: Maximum length of captured output
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
        self.execution_context: Dict[str, Any] = {}
        self.manuscript_dir: Optional[Path] = None
        self.initialization_imports = []  # Track imports from initialization blocks
        self._detect_manuscript_directory()

        # Initialize execution reporter for tracking Python activities
        try:
            from ..utils.python_execution_reporter import get_python_execution_reporter

            self.reporter = get_python_execution_reporter()
        except ImportError:
            self.reporter = None

    def _detect_manuscript_directory(self) -> None:
        """Detect the manuscript directory structure for src/py path integration."""
        try:
            # First check if manuscript path is set via environment variable
            from ..core.environment_manager import EnvironmentManager

            env_manuscript_path = EnvironmentManager.get_manuscript_path()
            if env_manuscript_path:
                env_path = Path(env_manuscript_path)
                if env_path.exists() and env_path.is_dir():
                    self.manuscript_dir = env_path
                    return

            # Start from current working directory and look for manuscript markers
            current_dir = Path.cwd()

            # Look for typical manuscript markers in current directory or parent directories
            manuscript_markers = ["00_CONFIG.yml", "MANUSCRIPT", "FIGURES"]

            # Check current directory and up to 3 levels up
            for level in range(4):
                check_dir = current_dir
                for _ in range(level):
                    check_dir = check_dir.parent
                    if check_dir == check_dir.parent:  # Reached root
                        break

                # Check if this directory has manuscript markers
                if any((check_dir / marker).exists() for marker in manuscript_markers):
                    self.manuscript_dir = check_dir
                    return

            # If not found, assume current directory is the manuscript directory
            self.manuscript_dir = current_dir

        except Exception:
            # If detection fails, use current directory
            self.manuscript_dir = Path.cwd()

    def _extract_imports(self, code: str) -> list[str]:
        """Extract import statements from Python code.

        Args:
            code: Python code to analyze

        Returns:
            List of import statement lines
        """
        import ast

        try:
            tree = ast.parse(code)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    import_line = "import " + ", ".join(alias.name for alias in node.names)
                    imports.append(import_line)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(alias.name for alias in node.names)
                    import_line = f"from {module} import {names}"
                    imports.append(import_line)

            return imports
        except SyntaxError:
            # If parsing fails, fall back to simple text search
            lines = code.strip().split("\n")
            imports = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped)
            return imports

    def _get_src_py_paths(self) -> list[str]:
        """Get the src/py paths to add to PYTHONPATH."""
        paths = []

        if self.manuscript_dir:
            # Add manuscript/src/py if it exists
            src_py_path = self.manuscript_dir / "src" / "py"
            if src_py_path.exists() and src_py_path.is_dir():
                paths.append(str(src_py_path.absolute()))

            # Also check for MANUSCRIPT/src/py structure
            manuscript_src_py = self.manuscript_dir / "MANUSCRIPT" / "src" / "py"
            if manuscript_src_py.exists() and manuscript_src_py.is_dir():
                paths.append(str(manuscript_src_py.absolute()))

            # Also check for ../manuscript-rxiv-maker/MANUSCRIPT/src/py structure
            example_src_py = self.manuscript_dir / "../manuscript-rxiv-maker/MANUSCRIPT" / "src" / "py"
            if example_src_py.exists() and example_src_py.is_dir():
                paths.append(str(example_src_py.absolute()))

        return paths

    def _filter_python_comments(self, code: str) -> str:
        """Filter Python comments from code before execution.

        Removes both full-line comments and inline comments while preserving
        line numbers for accurate error reporting. Comments should never be executed.

        Args:
            code: Python code that may contain comments

        Returns:
            Python code with comments filtered out
        """
        lines = code.split("\n")
        filtered_lines = []

        for line in lines:
            # Handle inline comments - everything after # is a comment
            # But we need to be careful about # inside strings
            comment_pos = self._find_python_comment_start(line)

            if comment_pos >= 0:
                # Comment found, keep everything before the #
                filtered_lines.append(line[:comment_pos].rstrip())
            else:
                # No comment found, keep entire line
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _find_python_comment_start(self, line: str) -> int:
        """Find the position where a Python comment starts.

        Handles # inside strings correctly by parsing string literals.

        Args:
            line: Line of Python code

        Returns:
            Position of # comment start, -1 if no comment, 0 if entire line is comment
        """
        # Skip lines that are entirely whitespace
        if not line.strip():
            return -1

        # Check if line starts with # (full line comment)
        if line.lstrip().startswith("#"):
            # Return the actual position of the # to preserve indentation
            return line.find("#")

        # Look for # outside of strings
        in_single_quote = False
        in_double_quote = False
        escaped = False

        for i, char in enumerate(line):
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "#" and not in_single_quote and not in_double_quote:
                return i

        return -1

    def execute_code_safely(
        self, code: str, context: Optional[Dict[str, Any]] = None, manuscript_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, bool]:
        """Execute Python code safely with output capture.

        Args:
            code: Python code to execute
            context: Optional execution context/variables
            manuscript_context: Optional context about manuscript location (file, line number)

        Returns:
            Tuple of (output, success_flag)

        Raises:
            PythonExecutionError: If execution fails
        """
        # CRITICAL: Filter out Python comments before execution
        # Comments should never be executed, this is essential for security
        code = self._filter_python_comments(code)

        # Normalize LaTeX-escaped paths in string literals
        code = code.replace("\\_", "_")  # Handle escaped underscores

        # Prepare execution context with full builtins access
        exec_context = {"__builtins__": __builtins__}

        # Add context variables if provided
        if context:
            exec_context.update(context)

        # Add persistent execution context
        exec_context.update(self.execution_context)

        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_output = io.StringIO()
        captured_errors = io.StringIO()

        try:
            # Redirect stdout and stderr
            sys.stdout = captured_output
            sys.stderr = captured_errors

            # Execute code with timeout using subprocess for better isolation
            result = self._execute_with_subprocess(code, exec_context, manuscript_context)

            if result["success"]:
                output = result["output"]
                # Update persistent context with any new variables
                self.execution_context.update(result.get("context", {}))
            else:
                # Return the detailed error directly without additional formatting
                output = result["error"]

            # Limit output length
            if len(output) > self.max_output_length:
                output = output[: self.max_output_length] + "... (output truncated)"

            return output.strip(), result["success"]

        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _execute_with_subprocess(
        self, code: str, context: Dict[str, Any], manuscript_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute code in subprocess for better isolation.

        Args:
            code: Python code to execute
            context: Execution context
            manuscript_context: Optional context about manuscript location (file, line number)

        Returns:
            Dictionary with execution results
        """
        # Create a script that properly handles context persistence
        # Filter context to include only JSON-serializable types, with better error handling
        filtered_context = {}
        for k, v in context.items():
            if k == "__builtins__":
                continue
            # Try to serialize each item individually to catch problematic values
            try:
                # Allow more types including None, and handle nested structures
                if isinstance(v, (int, float, str, bool, list, dict, type(None))):
                    # Test if it's actually serializable (nested structures might contain functions)
                    json.dumps(v)
                    filtered_context[k] = v
                elif hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
                    # Handle iterables by converting to list and filtering contents
                    try:
                        list_v = list(v)
                        if all(isinstance(item, (int, float, str, bool, type(None))) for item in list_v):
                            filtered_context[k] = list_v
                    except Exception:
                        # Skip problematic iterables
                        pass
            except (TypeError, ValueError):
                # Skip non-serializable values (like functions)
                continue

        context_json = json.dumps(filtered_context)

        # Get src/py paths to add to PYTHONPATH
        src_py_paths = self._get_src_py_paths()
        src_py_paths_json = json.dumps(src_py_paths)

        # Prepare manuscript context for error reporting
        manuscript_context = manuscript_context or {}
        # Convert None values to strings to avoid JSON null -> Python parsing issues
        safe_manuscript_context = {k: v if v is not None else "None" for k, v in manuscript_context.items()}
        manuscript_context_json = json.dumps(safe_manuscript_context)

        # Prepare initialization imports
        init_imports = "\n".join(self.initialization_imports)

        # Escape the code and imports for safe embedding in the script
        import json as json_module

        # Create proper JSON strings that can be embedded in the script
        # Use ensure_ascii=False to properly handle Unicode characters
        code_json_str = json_module.dumps(code, ensure_ascii=False)
        init_imports_json_str = json_module.dumps(init_imports, ensure_ascii=False)

        script_content = f"""
import sys
import io
import json
import traceback
import os

# Add manuscript src/py directories to Python path
src_py_paths = {src_py_paths_json}
for path in src_py_paths:
    if path not in sys.path:
        sys.path.insert(0, path)

# Load initial context
initial_context = {context_json}

# Manuscript context for error reporting
manuscript_context = {manuscript_context_json}
# Convert string "None" back to Python None
for key, value in manuscript_context.items():
    if value == "None":
        manuscript_context[key] = None

# Capture output
output_buffer = io.StringIO()
error_msg = None
final_context = {{}}

try:
    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    # Create execution namespace with initial context (full builtins access)
    exec_globals = initial_context.copy()
    exec_globals.update({{
        '__builtins__': __builtins__
    }})

    # Add special MANUSCRIPT_PATH variable
    manuscript_dir = manuscript_context.get('manuscript_dir')
    if manuscript_dir and manuscript_dir != "None":
        exec_globals['MANUSCRIPT_PATH'] = manuscript_dir
    else:
        exec_globals['MANUSCRIPT_PATH'] = os.getcwd()

    # Add figure generation utilities to context
    try:
        from rxiv_maker.manuscript_utils.figure_utils import (
            convert_mermaid, convert_python_figure, convert_r_figure,
            convert_figures_bulk, list_available_figures, get_figure_info,
            clean_figure_outputs
        )
        exec_globals.update({{
            'convert_mermaid': convert_mermaid,
            'convert_python_figure': convert_python_figure,
            'convert_r_figure': convert_r_figure,
            'convert_figures_bulk': convert_figures_bulk,
            'list_available_figures': list_available_figures,
            'get_figure_info': get_figure_info,
            'clean_figure_outputs': clean_figure_outputs,
        }})
    except ImportError:
        # Figure utilities not available, continue without them
        pass

    # Load code and imports from JSON to ensure proper escaping
    init_imports_code = {init_imports_json_str}
    user_code = {code_json_str}

    # Execute initialization imports first
    if init_imports_code:
        exec(init_imports_code, exec_globals)

    # Execute user code in the context
    exec(user_code, exec_globals)

    # Capture final context (only simple types that can be JSON serialized)
    for key, value in exec_globals.items():
        if not key.startswith('_') and key not in ['__builtins__']:
            if isinstance(value, (int, float, str, bool, list, dict)):
                final_context[key] = value

    # Restore stdout
    sys.stdout = old_stdout

    success = True
except Exception as e:
    sys.stdout = old_stdout
    # Enhanced error reporting with manuscript context
    error_parts = [str(e)]

    # Add manuscript location if available
    if manuscript_context.get('file') or manuscript_context.get('line'):
        location = f"{{manuscript_context.get('file', 'manuscript')}}:{{manuscript_context.get('line', 'unknown')}}"
        error_parts.insert(0, f"Error in {{location}}")

    # Get the traceback but filter out our subprocess wrapper
    tb_lines = traceback.format_exc().splitlines()
    # Filter out lines related to our wrapper script
    filtered_tb = []
    for line in tb_lines:
        if 'exec(' not in line and 'temp' not in line.lower() and 'subprocess' not in line.lower():
            filtered_tb.append(line)

    # For FileNotFoundError, provide helpful guidance
    if isinstance(e, FileNotFoundError):
        error_parts.append("\\nHint: Check that the file path is correct and the file exists relative to the manuscript directory.")
        error_parts.append("The Python code executes from the manuscript directory context.")

    if len(filtered_tb) > 1:  # More than just the exception line
        error_parts.append("Traceback:")
        error_parts.extend(filtered_tb[-3:])  # Last 3 lines of relevant traceback

    error_msg = "\\n".join(error_parts)
    success = False

# Output result as JSON
result = {{
    'success': success,
    'output': output_buffer.getvalue(),
    'error': error_msg,
    'context': final_context,
    'manuscript_context': manuscript_context
}}

print(json.dumps(result))
"""

        # Create a temporary file with the script, using UTF-8 encoding explicitly
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name

        try:
            # Execute in subprocess with timeout
            # CRITICAL: Use manuscript directory as working directory if available
            # This ensures that paths like 'DATA/arxiv_monthly_submissions.csv' work correctly
            # when Python code is executed in manuscript context. The manuscript directory
            # is where the manuscript files (01_MAIN.md, etc.) are located.
            working_dir = self.manuscript_dir if self.manuscript_dir else Path.cwd()

            # Set environment variables to ensure UTF-8 encoding
            import os

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["LC_ALL"] = "C.UTF-8"
            env["LANG"] = "C.UTF-8"

            # Determine Python executable, handling CI environments where only 'python3' exists
            python_executable = sys.executable
            if not Path(python_executable).exists():
                # Fallback to 'python3' for CI environments like GitHub Actions
                python_executable = "python3"

            process = subprocess.run(
                [python_executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=working_dir,
                encoding="utf-8",
                env=env,
            )

            if process.returncode == 0:
                try:
                    # The output should be JSON from the temp script
                    stdout_lines = process.stdout.strip().split("\n")
                    # Find the JSON line (should be the last line)
                    json_line = stdout_lines[-1] if stdout_lines else "{}"
                    result = json.loads(json_line)
                    return result
                except (json.JSONDecodeError, IndexError) as e:
                    # Provide more detailed debugging information
                    debug_info = f"JSON parsing failed: {e}\n"
                    debug_info += f"Process stdout:\n{process.stdout}\n"
                    debug_info += f"Process stderr:\n{process.stderr}\n"
                    debug_info += f"Last line attempted: {repr(json_line if 'json_line' in locals() else 'N/A')}"
                    return {"success": False, "output": process.stdout, "error": debug_info}
            else:
                # Provide detailed error information
                error_detail = f"Process exited with code {process.returncode}\n"
                error_detail += f"Stdout: {process.stdout}\n"
                error_detail += f"Stderr: {process.stderr}"
                return {
                    "success": False,
                    "output": process.stdout,
                    "error": error_detail,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Code execution timed out after {self.timeout} seconds"}
        except Exception as e:
            return {"success": False, "output": "", "error": f"Execution error: {str(e)}"}
        finally:
            # Clean up temporary file
            try:
                Path(temp_file_path).unlink()
            except Exception:
                pass

    def execute_block(self, code: str) -> str:
        """Execute Python code block and return formatted output.

        Args:
            code: Python code to execute

        Returns:
            Formatted output for insertion into document
        """
        try:
            # Pass manuscript directory context and execution context for MANUSCRIPT_PATH and variables
            manuscript_context = {"manuscript_dir": str(self.manuscript_dir)} if self.manuscript_dir else {}
            output, success = self.execute_code_safely(
                code, context=self.execution_context, manuscript_context=manuscript_context
            )

            if success:
                if output.strip():
                    # Break long output lines to prevent overfull hbox
                    import textwrap

                    output_lines = output.split("\n")
                    wrapped_lines = []
                    for line in output_lines:
                        if len(line) > 40:  # Wrap lines longer than 40 characters to prevent overfull hbox
                            wrapped_lines.extend(textwrap.wrap(line, width=40))
                        else:
                            wrapped_lines.append(line)
                    wrapped_output = "\n".join(wrapped_lines)

                    # Format as LaTeX verbatim block (since we're in the LaTeX conversion pipeline)
                    # Note: Don't escape characters inside verbatim - they should be displayed literally
                    return f"\\begin{{verbatim}}\n{wrapped_output}\n\\end{{verbatim}}"
                else:
                    # No output, return empty string
                    return ""
            else:
                # Format error as warning - don't escape in verbatim environment
                return f"\\begin{{verbatim}}\nPython execution error: {output}\n\\end{{verbatim}}"

        except PythonExecutionError as e:
            import textwrap

            # Break long error messages into multiple lines to prevent overfull hbox
            error_msg = str(e)
            # Create shorter lines with explicit newlines for verbatim environment
            wrapped_lines = textwrap.wrap(error_msg, width=40)  # Use even shorter width to prevent overfull hbox
            wrapped_error = "\n".join(wrapped_lines)
            return f"\\begin{{verbatim}}\nPython execution error:\n{wrapped_error}\n\\end{{verbatim}}"

    def execute_inline(self, code: str, line_number: Optional[int] = None, file_path: str = "manuscript") -> str:
        """Execute Python code inline and return result.

        Args:
            code: Python code to execute (should be expression)
            line_number: Optional line number for reporting
            file_path: Source file path for reporting

        Returns:
            String result for inline insertion
        """
        start_time = time.time()
        original_code = code

        try:
            # For inline execution, wrap in print() if it's an expression
            if not any(
                keyword in code for keyword in ["print(", "=", "import", "def ", "class ", "for ", "if ", "while "]
            ):
                # Looks like an expression, wrap in print
                code = f"print({code})"

            # Pass manuscript directory context and execution context for MANUSCRIPT_PATH and variables
            manuscript_context = {"manuscript_dir": str(self.manuscript_dir)} if self.manuscript_dir else {}
            output, success = self.execute_code_safely(
                code, context=self.execution_context, manuscript_context=manuscript_context
            )
            execution_time = time.time() - start_time

            if success:
                # Report successful inline execution
                if self.reporter:
                    self.reporter.track_inline_execution(
                        code=original_code,
                        output=output,
                        line_number=line_number,
                        file_path=file_path,
                        execution_time=execution_time,
                    )
                return output.strip() or ""
            else:
                # Report inline execution error
                if self.reporter:
                    self.reporter.track_error(
                        error_message=output, code_snippet=original_code, line_number=line_number, file_path=file_path
                    )
                # Escape underscores in error messages for LaTeX compatibility
                escaped_output = output.replace("_", "\\_")
                return f"[Error: {escaped_output}]"

        except PythonExecutionError as e:
            # Report inline execution error
            if self.reporter:
                self.reporter.track_error(
                    error_message=str(e), code_snippet=original_code, line_number=line_number, file_path=file_path
                )
            # Escape underscores in error messages for LaTeX compatibility
            error_msg = str(e).replace("_", "\\_")
            return f"[Error: {error_msg}]"

    def execute_initialization_block(
        self, code: str, manuscript_file: Optional[str] = None, line_number: Optional[int] = None
    ) -> None:
        """Execute Python code as an initialization block ({{py:exec}}).

        This method executes code and stores any variables in the persistent
        execution context for later use by {{py:get}} blocks.

        Args:
            code: Python code to execute
            manuscript_file: Optional filename for error context
            line_number: Optional line number for error context

        Raises:
            PythonExecutionError: If execution fails
            SecurityError: If code violates security restrictions
        """
        # Track execution start time for reporting
        start_time = time.time()

        # Execute the code and update persistent context
        try:
            # For initialization blocks, execute directly to preserve functions
            output, success = self._execute_initialization_directly(code, manuscript_file, line_number)

            # Calculate execution time
            execution_time = time.time() - start_time

            if success:
                # Report successful execution
                if self.reporter:
                    self.reporter.track_exec_block(
                        code=code,
                        output=output,
                        line_number=line_number,
                        file_path=manuscript_file or "manuscript",
                        execution_time=execution_time,
                    )
            else:
                # Report execution error
                if self.reporter:
                    self.reporter.track_error(
                        error_message=output,
                        code_snippet=code,
                        line_number=line_number,
                        file_path=manuscript_file or "manuscript",
                    )

                error_context = ""
                if manuscript_file or line_number:
                    error_context = f" (in {manuscript_file or 'manuscript'}:{line_number or 'unknown'})"
                raise PythonExecutionError(f"Initialization block execution failed{error_context}: {output}")

        except PythonExecutionError:
            raise
        except Exception as e:
            # Report unexpected error
            if self.reporter:
                self.reporter.track_error(
                    error_message=str(e),
                    code_snippet=code,
                    line_number=line_number,
                    file_path=manuscript_file or "manuscript",
                )

            error_context = ""
            if manuscript_file or line_number:
                error_context = f" (in {manuscript_file or 'manuscript'}:{line_number or 'unknown'})"
            raise PythonExecutionError(f"Unexpected error in initialization block{error_context}: {str(e)}") from e

    def _execute_initialization_directly(
        self, code: str, manuscript_file: Optional[str] = None, line_number: Optional[int] = None
    ) -> Tuple[str, bool]:
        """Execute initialization code directly in main process to preserve functions.

        Args:
            code: Python code to execute
            manuscript_file: Optional filename for error context
            line_number: Optional line number for error context

        Returns:
            Tuple of (output, success_flag)
        """
        import io
        import os
        import sys

        # Add manuscript src/py directories to sys.path
        src_py_paths = self._get_src_py_paths()
        original_sys_path = sys.path.copy()  # Save original to restore later
        original_cwd = os.getcwd()  # Save original working directory

        for path in src_py_paths:
            if path not in sys.path:
                sys.path.insert(0, path)

        # CRITICAL: Change to manuscript directory for relative path resolution
        # This ensures that paths like 'DATA/arxiv_monthly_submissions.csv' work correctly
        # when executing initialization blocks in the manuscript context.
        if self.manuscript_dir:
            os.chdir(self.manuscript_dir)

        try:
            # Filter comments for security
            code = self._filter_python_comments(code)

            # Normalize LaTeX-escaped paths
            code = code.replace("\\_", "_")

            # Extract and track imports from this initialization block
            imports = self._extract_imports(code)
            self.initialization_imports.extend(imports)

            # Prepare execution context
            exec_context = {"__builtins__": __builtins__}
            exec_context.update(self.execution_context)

            # Add special MANUSCRIPT_PATH variable
            if self.manuscript_dir:
                exec_context["MANUSCRIPT_PATH"] = str(self.manuscript_dir)
            else:
                exec_context["MANUSCRIPT_PATH"] = os.getcwd()

            # Add figure utilities if available
            try:
                from rxiv_maker.manuscript_utils.figure_utils import (
                    clean_figure_outputs,
                    convert_figures_bulk,
                    convert_mermaid,
                    convert_python_figure,
                    convert_r_figure,
                    get_figure_info,
                    list_available_figures,
                )

                exec_context.update(
                    {
                        "convert_mermaid": convert_mermaid,
                        "convert_python_figure": convert_python_figure,
                        "convert_r_figure": convert_r_figure,
                        "convert_figures_bulk": convert_figures_bulk,
                        "list_available_figures": list_available_figures,
                        "get_figure_info": get_figure_info,
                        "clean_figure_outputs": clean_figure_outputs,
                    }
                )
            except ImportError:
                pass

            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = io.StringIO()
            captured_errors = io.StringIO()

            try:
                sys.stdout = captured_output
                sys.stderr = captured_errors

                # Execute code directly
                exec(code, exec_context)

                # Update persistent context with all new variables (including functions)
                for key, value in exec_context.items():
                    if not key.startswith("_") and key != "__builtins__":
                        self.execution_context[key] = value

                output = captured_output.getvalue()
                if captured_errors.getvalue():
                    output += "\n" + captured_errors.getvalue()

                return output, True

            except Exception as e:
                error_output = captured_errors.getvalue() or str(e)
                return error_output, False

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        finally:
            # Restore original sys.path and working directory
            sys.path[:] = original_sys_path
            os.chdir(original_cwd)

    def get_variable_value(
        self, variable_name: str, line_number: Optional[int] = None, file_path: str = "manuscript"
    ) -> Any:
        """Get the value of a variable from the execution context ({{py:get}}).

        Args:
            variable_name: Name of the variable or expression to evaluate
            line_number: Optional line number where variable is accessed
            file_path: Source file path for reporting

        Returns:
            The value of the variable or expression result

        Raises:
            PythonExecutionError: If variable cannot be retrieved
        """
        # First try simple variable lookup
        if variable_name in self.execution_context:
            variable_value = self.execution_context[variable_name]

            # Report successful variable access
            if self.reporter:
                self.reporter.track_get_variable(
                    variable_name=variable_name,
                    variable_value=variable_value,
                    line_number=line_number,
                    file_path=file_path,
                )
            return variable_value

        # If not a simple variable, try to evaluate as expression
        try:
            # For security, only allow simple expressions like len(var), var['key'], etc.
            # Use ast.literal_eval for safe evaluation when possible
            import ast

            # First try ast.literal_eval for simple literal expressions
            try:
                variable_value = ast.literal_eval(variable_name)
            except (ValueError, SyntaxError):
                # If not a literal, use restricted eval with limited builtins
                # Create safe execution context for evaluation
                safe_builtins = {"len": len, "str": str, "int": int, "float": float, "bool": bool}
                eval_context = {"__builtins__": safe_builtins}
                eval_context.update(self.execution_context)

                # Add special MANUSCRIPT_PATH variable if available
                if self.manuscript_dir:
                    eval_context["MANUSCRIPT_PATH"] = str(self.manuscript_dir)

                # Evaluate the expression with restricted context
                variable_value = eval(variable_name, eval_context)  # noqa: S307

            # Report successful expression evaluation
            if self.reporter:
                self.reporter.track_get_variable(
                    variable_name=variable_name,
                    variable_value=variable_value,
                    line_number=line_number,
                    file_path=file_path,
                )

            return variable_value

        except Exception:
            # Report variable/expression access error
            if self.reporter:
                self.reporter.track_error(
                    error_message=f"Variable '{variable_name}' not found in context",
                    code_snippet=f"{{{{py:get {variable_name}}}}}",
                    line_number=line_number,
                    file_path=file_path,
                )
            raise PythonExecutionError(f"Variable '{variable_name}' not found in context") from None

    def reset_context(self) -> None:
        """Reset the execution context."""
        self.execution_context.clear()


# Global executor instance for persistence across commands
_global_executor = None


def get_python_executor() -> PythonExecutor:
    """Get or create global Python executor instance."""
    global _global_executor
    if _global_executor is None:
        # Use longer timeout for data processing scenarios that may fetch from web
        _global_executor = PythonExecutor(timeout=60)
    return _global_executor


def reset_python_executor() -> None:
    """Reset the global Python executor instance.

    This is useful for testing to ensure clean state between tests.
    """
    global _global_executor
    _global_executor = None
