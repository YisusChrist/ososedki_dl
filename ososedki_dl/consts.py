"""Constants for the package."""

from pathlib import Path
from platformdirs import user_log_dir  # type: ignore

try:
    from importlib import metadata
except ImportError:  # for Python < 3.8
    import importlib_metadata as metadata  # type: ignore

__version__: str = metadata.version(__package__ or __name__)
__desc__: str = metadata.metadata(__package__ or __name__)["Summary"]
GITHUB: str = metadata.metadata(__package__ or __name__)["Home-page"]
PACKAGE: str | None = __package__

CACHE_PATH = Path(".cache")
LOG_PATH: str = user_log_dir(appname=PACKAGE, ensure_exists=True)

LOG_FILE: Path = Path(LOG_PATH).resolve() / f"{PACKAGE}.log"

MAX_TIMEOUT = 5

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

DEBUG = False
CHECK_CACHE = False
