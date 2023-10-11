"""
compile build dependencies module.

Heavily rely on pip-tools BacktrackingResolver and our own find_build_deps
to recursively find all build dependencies and generate a pinned list
of build dependencies.
"""

from __future__ import annotations

from typing import Iterable

from pip._internal.req import InstallRequirement
from pip._internal.req.constructors import install_req_from_req_string
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver

from .finder import find_build_dependencies
from .utils import get_version


class BuildDependencyCompiler:
    """Resolve exact build dependencies."""

    def __init__(self, repository: PyPIRepository) -> None:
        self.repository = repository
        self.resolver = None

    def resolve(
        self,
        install_requirements: Iterable[InstallRequirement],
        constraints: Iterable[InstallRequirement] | None = None,
    ) -> set[InstallRequirement]:
        """Resolve all build dependencies for a given set of dependencies."""
        constraints: list[InstallRequirement] = list(constraints) if constraints else []
        constraint_qty = len(constraints)
        for req in install_requirements:
            req_version = get_version(req)
            raw_build_dependencies = find_build_dependencies(
                req.name, req_version, raise_setuppy_parsing_exc=False
            )
            for raw_build_req in raw_build_dependencies:
                build_req = install_req_from_req_string(
                    raw_build_req, comes_from=req.name
                )
                constraints.append(build_req)
        # override resolver - we only want the latest and greatest
        self.resolver = BacktrackingResolver(
            constraints=constraints,
            existing_constraints={},
            repository=self.repository,
            allow_unsafe=True,
        )
        build_dependencies = self.resolver.resolve()
        # dependencies of build dependencies might have their own build dependencies,
        # so let's recursively search for those.
        while len(build_dependencies) != constraint_qty:
            constraint_qty = len(build_dependencies)
            build_dependencies = self.resolve(
                build_dependencies, constraints=build_dependencies
            )
        return build_dependencies
