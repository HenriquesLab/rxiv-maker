"""Commands for the rxiv-maker CLI."""

from .arxiv import arxiv
from .bibliography import bibliography
from .build import build as pdf
from .cache_management import cache_group as cache
from .changelog import changelog
from .check_installation import check_installation
from .clean import clean
from .completion import completion_cmd
from .config import config_group as config

# Removed: from .containers import containers_cmd (deprecated with container engine support)
from .create_repo import create_repo
from .docx import docx
from .figures import figures
from .get_rxiv_preprint import get_rxiv_preprint
from .init import init
from .install_deps import install_deps
from .repo_init import repo_init
from .repos import repos
from .repos_search import repos_search
from .setup import setup
from .track_changes import track_changes
from .upgrade import upgrade
from .validate import validate
from .version import version

__all__ = [
    "arxiv",
    "bibliography",
    "cache",
    "changelog",
    "config",
    "pdf",
    "check_installation",
    "clean",
    "completion_cmd",
    # Removed: "containers_cmd" (deprecated with container engine support)
    "create_repo",
    "docx",
    "figures",
    "get_rxiv_preprint",
    "init",
    "install_deps",
    "repo_init",
    "repos",
    "repos_search",
    "setup",
    "track_changes",
    "upgrade",
    "validate",
    "version",
]
