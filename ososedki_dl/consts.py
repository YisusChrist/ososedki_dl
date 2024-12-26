"""Constants for the package."""

from pathlib import Path

from core_helpers.xdg_paths import get_user_path

try:
    from importlib import metadata
except ImportError:  # for Python < 3.8
    import importlib_metadata as metadata  # type: ignore

__version__: str = metadata.version(__package__ or __name__)
__desc__: str = metadata.metadata(__package__ or __name__)["Summary"]
GITHUB: str = metadata.metadata(__package__ or __name__)["Home-page"]
PACKAGE: str = metadata.metadata(__package__ or __name__)["Name"]

CACHE_PATH = Path(".cache")
LOG_PATH: Path = get_user_path(package=PACKAGE, path_type="log")
LOG_FILE: Path = Path(LOG_PATH).resolve() / f"{PACKAGE}.log"
CONFIG_PATH: Path = get_user_path(PACKAGE, "config")
CONFIG_FILE: Path = CONFIG_PATH / f"{PACKAGE}.ini"

MAX_TIMEOUT = 5
DEFAULT_DEST_PATH: Path = Path("downloads")

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

DEBUG = False
CHECK_CACHE = False
