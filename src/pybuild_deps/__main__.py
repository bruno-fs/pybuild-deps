"""Command-line interface."""

import click

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

    deps = find_build_dependencies(package_name=package_name, version=package_version)
    for dep in deps:
        click.echo(dep)


cli.add_command(compile.compile, "compile")

if __name__ == "__main__":
    cli(prog_name="pybuild-deps")  # pragma: no cover
