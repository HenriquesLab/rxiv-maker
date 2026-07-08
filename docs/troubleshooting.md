# Troubleshooting

The full, searchable troubleshooting guide lives on the website:

**[Troubleshooting →](https://rxiv-maker.henriqueslab.org/community/troubleshooting/)**

The most common fixes are below. Start with:

```bash
rxiv check-installation   # diagnose the environment
rxiv validate --detailed  # diagnose the manuscript
rxiv pdf --verbose        # see the full build log
```

## Installation Issues

`rxiv: command not found` after `pipx install` usually means pipx's bin directory is not on `PATH` — run `pipx ensurepath` and open a new shell. On macOS, prefer `brew install henriqueslab/formulas/rxiv-maker`, which also installs LaTeX. Verify with `rxiv check-installation`.

## PDF Generation Failures

Almost always a LaTeX problem. Confirm a LaTeX distribution is installed (`pdflatex --version`), then read the error near the end of `rxiv pdf --verbose`. Missing `.sty` packages mean an incomplete TeX install; a clean rebuild (`rxiv clean && rxiv pdf`) clears stale build state.

## Figure Generation Failures

A figure script that errors stops the build. Run the script directly (`python FIGURES/your_figure.py`) to see the traceback, and make sure its dependencies are installed in the same environment as `rxiv`. Use `rxiv pdf --force-figures` to regenerate cached figures.

## Citation and Bibliography Problems

`rxiv validate` lists undefined or duplicate citation keys. Every `[@key]` must match an entry in `03_REFERENCES.bib`. If the bibliography does not render, check for BibTeX syntax errors in that file. Bare DOIs pasted in the text are resolved with `rxiv pdf --resolve-dois`.

## Performance Issues

Slow builds are dominated by figure regeneration. During iteration use `rxiv pdf --skip-figures` (reuse cached figures) and `rxiv pdf --skip-validation`. Only large or high-DPI figures need regenerating each time.

## Platform-Specific Problems

- **Windows** — run inside WSL2; native Windows is not supported for the full LaTeX pipeline.
- **macOS (Apple Silicon)** — install via Homebrew so the bundled LaTeX matches the architecture.
- **Linux** — install a full TeX Live (`texlive-full`) rather than the minimal package to avoid missing `.sty` files.

## More help

The [website troubleshooting guide](https://rxiv-maker.henriqueslab.org/community/troubleshooting/) covers environment setup, advanced debugging, and prevention strategies in full. Still stuck? Ask in [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions) or open an [issue](https://github.com/henriqueslab/rxiv-maker/issues).
