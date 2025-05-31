from utils.config import current_config
from pathlib import Path

def return_file_path(path: str) -> str | Path:
    """Creates a file path based on the current configuration settings.

    This function combines the base storage path with the provided path parameter
    and returns either a string path (for Firebase storage) or a Path object
    (for development environment).

    Args:
        path (str): The relative path to be appended to the storage base path.
            Typically obtained from RatingsParams.file_path property.

    Returns:
        Union[str, Path]: A complete file path as either:
            - str: When config.STORAGE_TYPE is 'firebase'
            - Path: For all other storage types (development)

    Examples:
        >>> return_file_path("2023/12/2023-12-01.json")
        'storage/2023/12/2023-12-01.json'  # if STORAGE_TYPE is 'firebase'
        Path('storage/2023/12/2023-12-01.json')  # otherwise
    """

    path_stem = f"{current_config.STORAGE_PATH}/{path}"

    if current_config.STORAGE_TYPE == 'firebase':
        return path_stem
    else:
        return Path(path_stem)
