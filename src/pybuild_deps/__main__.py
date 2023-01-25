"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Entrypoint for PyBuild Deps."""


if __name__ == "__main__":
    main(prog_name="pybuild-deps")  # pragma: no cover
