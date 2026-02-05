"""
Version information for TV Ratings Automation System.
"""

# Follow semantic versioning (semver.org):
# MAJOR version for incompatible API changes
# MINOR version for new functionality in a backwards-compatible manner
# PATCH version for backwards-compatible bug fixes

__version__ = "1.0.0"
__release_date__ = "2026-02-05"
__description__ = "TV Ratings Automation System"


def print_version():
    """Print version information similar to python --version"""
    print(f"{__description__} {__version__} (released {__release_date__})")


if __name__ == "__main__":
    print_version()
