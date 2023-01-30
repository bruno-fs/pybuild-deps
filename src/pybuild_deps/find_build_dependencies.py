"""Find build dependencies of a python package."""

import logging
import tarfile

from pybuild_deps.get_package_source import get_package_source
from pybuild_deps.parsers import parse_pyproject_toml, parse_setup_cfg, parse_setup_py


def find_build_dependencies(package_name, version):
    """Find build dependencies for a given package."""
    file_parser_map = {
        "pyproject.toml": parse_pyproject_toml,
        "setup.cfg": parse_setup_cfg,
        "setup.py": parse_setup_py,
    }
    logging.info("retrieving source for package %s==%s", package_name, version)
    source_path = get_package_source(package_name, version)
    build_dependencies = []
    with tarfile.open(fileobj=source_path.open("rb")) as tarball:
        for file_name, parser in file_parser_map.items():
            root_dir = tarball.getnames()[0].split("/")[0]
            try:
                file = tarball.extractfile(f"{root_dir}/{file_name}")
            except KeyError:
                logging.info(
                    "%s file not found for package %s==%s",
                    file_name,
                    package_name,
                    version,
                )
                continue
            logging.info(
                "parsing file %s for package %s==%s",
                file_name,
                package_name,
                version,
            )
            build_dependencies += parser(file.read().decode())
    return build_dependencies
