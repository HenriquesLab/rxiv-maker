"""Python code execution for markdown commands.

This module provides execution of Python code within markdown documents.
It includes output capture and error handling.
"""

import io
import json
import subprocess
import sys
import tempfile
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
        self._detect_manuscript_directory()

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

            # Also check for EXAMPLE_MANUSCRIPT/src/py structure
            example_src_py = self.manuscript_dir / "EXAMPLE_MANUSCRIPT" / "src" / "py"
            if example_src_py.exists() and example_src_py.is_dir():
                paths.append(str(example_src_py.absolute()))

        return paths

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
                output = f"Error: {result['error']}"

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
        context_json = json.dumps(
            {
                k: v
                for k, v in context.items()
                if k != "__builtins__" and isinstance(v, (int, float, str, bool, list, dict))
            }
        )

        # Get src/py paths to add to PYTHONPATH
        src_py_paths = self._get_src_py_paths()
        src_py_paths_json = json.dumps(src_py_paths)

        # Prepare manuscript context for error reporting
        manuscript_context = manuscript_context or {}
        manuscript_context_json = json.dumps(manuscript_context)

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

    # Execute user code in the context
    exec('''\\
{chr(10).join(line for line in code.split(chr(10)))}
''', exec_globals)

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

        # Create a temporary file with the script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name

        try:
            # Execute in subprocess with timeout
            # Use manuscript directory as working directory if available
            working_dir = self.manuscript_dir if self.manuscript_dir else Path.cwd()
            process = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=working_dir,
            )

            if process.returncode == 0:
                try:
                    # The output should be JSON from the temp script
                    stdout_lines = process.stdout.strip().split("\n")
                    # Find the JSON line (should be the last line)
                    json_line = stdout_lines[-1] if stdout_lines else "{}"
                    result = json.loads(json_line)
                    return result
                except (json.JSONDecodeError, IndexError):
                    return {"success": False, "output": process.stdout, "error": "Failed to parse execution result"}
            else:
                return {
                    "success": False,
                    "output": process.stdout,
                    "error": process.stderr or f"Process exited with code {process.returncode}",
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
            output, success = self.execute_code_safely(code)

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

    def execute_inline(self, code: str) -> str:
        """Execute Python code inline and return result.

        Args:
            code: Python code to execute (should be expression)

        Returns:
            String result for inline insertion
        """
        try:
            # For inline execution, wrap in print() if it's an expression
            if not any(
                keyword in code for keyword in ["print(", "=", "import", "def ", "class ", "for ", "if ", "while "]
            ):
                # Looks like an expression, wrap in print
                code = f"print({code})"

            output, success = self.execute_code_safely(code)

            if success:
                return output.strip() or ""
            else:
                # Escape underscores in error messages for LaTeX compatibility
                escaped_output = output.replace("_", "\\_")
                return f"[Error: {escaped_output}]"

        except PythonExecutionError as e:
            # Escape underscores in error messages for LaTeX compatibility
            error_msg = str(e).replace("_", "\\_")
            return f"[Error: {error_msg}]"

    def execute_initialization_block(
        self, code: str, manuscript_file: Optional[str] = None, line_number: Optional[int] = None
    ) -> None:
        """Execute Python code block for initialization ({{py:exec}}).

        This method executes code and stores results in the persistent context
        but doesn't return any output for insertion into the document.

        Args:
            code: Python code to execute for initialization
            manuscript_file: Name of the manuscript file containing this code
            line_number: Line number in the manuscript where this code appears

        Raises:
            PythonExecutionError: If execution fails
            SecurityError: If code violates security restrictions
        """
        # Execute the code and update persistent context
        try:
            output, success = self.execute_code_safely(
                code, manuscript_context={"file": manuscript_file, "line": line_number}
            )

            if not success:
                error_context = ""
                if manuscript_file or line_number:
                    error_context = f" (in {manuscript_file or 'manuscript'}:{line_number or 'unknown'})"
                raise PythonExecutionError(f"Initialization block execution failed{error_context}: {output}")
        except PythonExecutionError:
            raise
        except Exception as e:
            error_context = ""
            if manuscript_file or line_number:
                error_context = f" (in {manuscript_file or 'manuscript'}:{line_number or 'unknown'})"
            raise PythonExecutionError(f"Unexpected error in initialization block{error_context}: {str(e)}") from e

    def get_variable_value(self, variable_name: str) -> Any:
        """Get the value of a variable from the execution context ({{py:get}}).

        Args:
            variable_name: Name of the variable to retrieve

        Returns:
            The value of the variable, or None if not found

        Raises:
            PythonExecutionError: If variable cannot be retrieved
        """
        if variable_name not in self.execution_context:
            raise PythonExecutionError(f"Variable '{variable_name}' not found in context")

        return self.execution_context[variable_name]

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
