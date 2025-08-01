"""Commands for the rxiv-maker CLI."""

from .arxiv import arxiv
from .bibliography import bibliography
from .build import build as pdf
from .check_installation import check_installation
from .clean import clean
from .figures import figures
from .init import init
from .install_deps import install_deps
from .setup import setup
from .track_changes import track_changes
from .validate import validate
from .version import version

__all__ = [
    "arxiv",
    "bibliography",
    "pdf",
    "check_installation",
    "clean",
    "figures",
    "init",
    "install_deps",
    "setup",
    "track_changes",
    "validate",
    "version",
]
