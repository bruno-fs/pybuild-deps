"""Find build dependencies of a python package."""

import tarfile

from .logger import log
from .parsers import parse_pyproject_toml, parse_setup_cfg, parse_setup_py
from .source import get_package_source


def find_build_dependencies(package_name, version):
    """Find build dependencies for a given package."""
    file_parser_map = {
        "pyproject.toml": parse_pyproject_toml,
        "setup.cfg": parse_setup_cfg,
        "setup.py": parse_setup_py,
    }
    log.debug(f"retrieving source for package {package_name}=={version}")
    source_path = get_package_source(package_name, version)
    build_dependencies = []
    with tarfile.open(fileobj=source_path.open("rb")) as tarball:
        for file_name, parser in file_parser_map.items():
            root_dir = tarball.getnames()[0].split("/")[0]
            try:
                file = tarball.extractfile(f"{root_dir}/{file_name}")
            except KeyError:
                log.debug(
                    f"{file_name} file not found for package {package_name}=={version}",
                )
                continue
            log.debug(
                f"parsing file {file_name} for package {package_name}=={version}",
            )
            build_dependencies += parser(file.read().decode())
    return build_dependencies
