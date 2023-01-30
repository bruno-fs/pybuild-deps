"""Command-line interface."""
import logging

import click


@click.group()
@click.version_option()
@click.option("--log-level", default="ERROR")
def cli(log_level) -> None:
    """Entrypoint for PyBuild Deps."""
    logging.basicConfig(level=log_level)


@cli.command()
@click.argument("package-name")
@click.argument("version")
def find_build_deps(package_name, version):
    """Find build dependencies for given package."""
    from pybuild_deps.find_build_dependencies import find_build_dependencies

    deps = find_build_dependencies(package_name=package_name, version=version)
    for dep in deps:
        click.echo(dep)


if __name__ == "__main__":
    cli(prog_name="pybuild-deps")  # pragma: no cover
