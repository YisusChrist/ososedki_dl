"""Constants for the package."""

from pathlib import Path

from core_helpers.xdg_paths import PathType, get_user_path

try:
    from importlib import metadata
except ImportError:  # for Python < 3.8
    import importlib_metadata as metadata  # type: ignore

metadata_info = metadata.metadata(__package__ or __name__)

__version__: str = metadata.version(__package__ or __name__)
__desc__: str = metadata_info["Summary"]
GITHUB = (
    metadata_info["Home-page"] or metadata_info["Project-URL"].split(",")[1].strip()
)
PACKAGE: str = metadata_info["Name"]

CACHE_PATH: Path = Path(".cache").resolve()
LOG_PATH: Path = get_user_path(package=PACKAGE, path_type=PathType.LOG)
LOG_FILE: Path = Path(LOG_PATH).resolve() / f"{PACKAGE}.log"
CONFIG_PATH: Path = get_user_path(PACKAGE, PathType.CONFIG)
CONFIG_FILE: Path = CONFIG_PATH / f"{PACKAGE}.ini"

MAX_TIMEOUT = 5
DEFAULT_DEST_PATH: Path = Path("downloads")
MIN_USER_AGENT_VERSION = 120.0

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
