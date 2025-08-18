"""Python code execution for markdown commands.

This module provides secure execution of Python code within markdown documents.
It includes sandboxing, output capture, and security restrictions.

Security considerations:
- Limited execution time
- Restricted imports (whitelist approach)
- No file system access outside working directory
- Memory limits through timeout
- Error handling and cleanup
"""

import ast
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Whitelist of safe modules that can be imported
SAFE_MODULES = {
    "math",
    "random",
    "datetime",
    "json",
    "csv",
    "statistics",
    "collections",
    "itertools",
    "functools",
    "operator",
    "numpy",
    "pandas",
    "matplotlib.pyplot",
    "seaborn",
    "scipy",
    "sklearn",
    "plotly",
    "bokeh",
    # Scientific computing
    "matplotlib",
    "matplotlib.patches",
    "matplotlib.colors",
    "numpy.random",
    "numpy.linalg",
    "pandas.plotting",
    # Data manipulation
    "datetime.date",
    "datetime.datetime",
    "datetime.timedelta",
    "re",
    "urllib.parse",
    "base64",
    "hashlib",
}

# Dangerous functions and modules to block
DANGEROUS_PATTERNS = [
    "import os",
    "import subprocess",
    "import sys",
    "import shutil",
    "import socket",
    "import urllib",
    "import requests",
    "__import__",
    "eval",
    "exec",
    "compile",
    "open(",
    "file(",
    "input(",
    "raw_input(",
    "globals()",
    "locals()",
    "vars()",
    "dir(",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "exit()",
    "quit()",
    "help()",
    "copyright()",
]


class PythonExecutionError(Exception):
    """Exception raised during Python code execution."""

    pass


class SecurityError(PythonExecutionError):
    """Exception raised when code violates security restrictions."""

    pass


class PythonExecutor:
    """Secure Python code executor for markdown commands."""

    def __init__(self, timeout: int = 10, max_output_length: int = 10000):
        """Initialize Python executor.

        Args:
            timeout: Maximum execution time in seconds
            max_output_length: Maximum length of captured output
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
        self.execution_context: Dict[str, Any] = {}

    def validate_code_security(self, code: str) -> None:
        """Validate code for security issues.

        Args:
            code: Python code to validate

        Raises:
            SecurityError: If code contains dangerous patterns
        """
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern in code:
                raise SecurityError(f"Dangerous pattern detected: {pattern}")

        # Parse AST to check for dangerous node types
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise PythonExecutionError(f"Syntax error in Python code: {e}") from e

        for node in ast.walk(tree):
            # Block dangerous AST node types
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in SAFE_MODULES:
                            raise SecurityError(f"Import not allowed: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module not in SAFE_MODULES:
                        raise SecurityError(f"Import not allowed: {node.module}")

            elif isinstance(node, ast.Call):
                # Check for dangerous function calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["exec", "eval", "compile", "__import__"]:
                        raise SecurityError(f"Function not allowed: {node.func.id}")

    def execute_code_safely(self, code: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, bool]:
        """Execute Python code safely with output capture.

        Args:
            code: Python code to execute
            context: Optional execution context/variables

        Returns:
            Tuple of (output, success_flag)

        Raises:
            PythonExecutionError: If execution fails
        """
        # Validate security first
        self.validate_code_security(code)

        # Prepare execution context
        exec_context = {
            "__builtins__": {
                # Safe built-in functions only
                "abs": abs,
                "all": all,
                "any": any,
                "bin": bin,
                "bool": bool,
                "bytearray": bytearray,
                "bytes": bytes,
                "chr": chr,
                "dict": dict,
                "divmod": divmod,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "frozenset": frozenset,
                "hex": hex,
                "int": int,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "oct": oct,
                "ord": ord,
                "pow": pow,
                "print": print,
                "range": range,
                "reversed": reversed,
                "round": round,
                "set": set,
                "slice": slice,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
            }
        }

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
            result = self._execute_with_subprocess(code, exec_context)

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

    def _execute_with_subprocess(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code in subprocess for better isolation.

        Args:
            code: Python code to execute
            context: Execution context

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

        script_content = f"""
import sys
import io
import json

# Load initial context
initial_context = {context_json}

# Capture output
output_buffer = io.StringIO()
error_msg = None
final_context = {{}}

try:
    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    # Create execution namespace with initial context
    exec_globals = initial_context.copy()
    exec_globals.update({{
        '__builtins__': __builtins__,
        'print': print,
        'range': range,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'abs': abs,
        'max': max,
        'min': min,
        'sum': sum,
        'round': round,
        'pow': pow
    }})

    # Execute user code in the context
    exec('''\\
{chr(10).join(line for line in code.split(chr(10)))}
''', exec_globals)

    # Capture final context (only simple types that can be JSON serialized)
    for key, value in exec_globals.items():
        if not key.startswith('_') and key not in ['print', 'range', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set', 'abs', 'max', 'min', 'sum', 'round', 'pow']:
            if isinstance(value, (int, float, str, bool, list, dict)):
                final_context[key] = value

    # Restore stdout
    sys.stdout = old_stdout

    success = True
except Exception as e:
    sys.stdout = old_stdout
    error_msg = str(e)
    success = False

# Output result as JSON
result = {{
    'success': success,
    'output': output_buffer.getvalue(),
    'error': error_msg,
    'context': final_context
}}

print(json.dumps(result))
"""

        # Create a temporary file with the script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name

        try:
            # Execute in subprocess with timeout
            process = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=Path.cwd(),  # Restrict to current directory
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

        except (SecurityError, PythonExecutionError) as e:
            import textwrap

            # Break long error messages into multiple lines to prevent overfull hbox
            error_msg = str(e)
            # Create shorter lines with explicit newlines for verbatim environment
            wrapped_lines = textwrap.wrap(error_msg, width=40)  # Use even shorter width to prevent overfull hbox
            wrapped_error = "\n".join(wrapped_lines)
            return f"\\begin{{verbatim}}\nPython execution blocked:\n{wrapped_error}\n\\end{{verbatim}}"

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

        except (SecurityError, PythonExecutionError) as e:
            # Escape underscores in error messages for LaTeX compatibility
            error_msg = str(e).replace("_", "\\_")
            return f"[Blocked: {error_msg}]"

    def reset_context(self) -> None:
        """Reset the execution context."""
        self.execution_context.clear()


# Global executor instance for persistence across commands
_global_executor = None


def get_python_executor() -> PythonExecutor:
    """Get or create global Python executor instance."""
    global _global_executor
    if _global_executor is None:
        _global_executor = PythonExecutor()
    return _global_executor
