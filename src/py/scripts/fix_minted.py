#!/usr/bin/env python3
"""Quick script to fix the minted issues in MANUSCRIPT.tex."""

import sys


def fix_minted_issues(filename):
    """Fix minted package issues in LaTeX files by replacing problematic patterns.

    Args:
        filename: Path to the LaTeX file to fix.
    """
    with open(filename) as f:
        content = f.read()

    # Replace the problematic texttt patterns with verb
    # Pattern 1: \texttt{\begin{minted}{python}... \end{minted}}
    content = content.replace(
        r"\texttt{\begin{minted}{python}... \end{minted}}",
        r"\verb|\begin{minted}{python}... \end{minted}|",
    )

    # Pattern 2: \texttt{\begin{minted}{python}\nprint("Hi")\n\end{minted}}
    content = content.replace(
        r'\texttt{\begin{minted}{python}\nprint("Hi")\n\end{minted}}',
        r'\verb|\begin{minted}{python}\nprint("Hi")\n\end{minted}|',
    )

    with open(filename, "w") as f:
        f.write(content)

    print(f"Fixed minted issues in {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_minted.py <filename>")
        sys.exit(1)

    fix_minted_issues(sys.argv[1])
