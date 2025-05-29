from utils.data_management import RatingsParams
from utils.config import current_config
from pathlib import Path
def create_file_path(params:RatingsParams) -> str | Path:
    """Returns a string or a Path object, depending on config state (development or production).
    Path object is used for development, str path is used for Firebase."""

    path_stem = f"{current_config.STORAGE_PATH}/{params.file_path}"

    if current_config.STORAGE_TYPE == 'firebase':
        return path_stem
    else:
        return Path(path_stem)
