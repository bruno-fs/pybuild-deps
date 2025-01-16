"""Command-line interface."""

import sys
from urllib.parse import urlparse

import click
from pip._internal.req.constructors import install_req_from_req_string

from pybuild_deps.exceptions import PyBuildDepsError

from .finder import find_build_dependencies
from .logger import log
from .scripts import compile


@click.group()
@click.version_option(package_name="pybuild-deps")
def cli() -> None:
    """Entrypoint for PyBuild Deps."""
    log.as_library = False  # pragma: no cover


@cli.command()
@click.argument("package-name")
@click.argument("package-version")
@click.option("-v", "--verbose", count=True, help="Show more output")
def find_build_deps(package_name, package_version, verbose):
    """Find build dependencies for given package."""
    log.verbosity = verbose
    parsed_url = urlparse(package_version)
    is_url = all((parsed_url.scheme, parsed_url.netloc))

    if is_url:
        req = f"{package_name} @ {package_version}"
    else:
        req = f"{package_name}=={package_version}"

    ireq = install_req_from_req_string(req)

    try:
        deps = find_build_dependencies(ireq)
    except PyBuildDepsError as err:
        log.error(str(err))
        sys.exit(2)
    for dep in deps:
        click.echo(dep)


cli.add_command(compile.compile, "compile")

if __name__ == "__main__":
    cli(prog_name="pybuild-deps")  # pragma: no cover
