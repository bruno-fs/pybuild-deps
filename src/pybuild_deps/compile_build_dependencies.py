"""
compile build dependencies module.

Heavily rely on pip-tools BacktrackingResolver and our own find_build_deps
to recursively find all build dependencies and generate a pinned list
of build dependencies.
"""

from __future__ import annotations

from functools import partial
from typing import Iterable

from pip._internal.exceptions import DistributionNotFound
from pip._internal.req import InstallRequirement
from pip._internal.req.constructors import install_req_from_req_string
from pip._vendor.resolvelib.resolvers import ResolutionImpossible
from piptools.repositories import PyPIRepository
from piptools.resolver import BacktrackingResolver

from .exceptions import UnsolvableDependenciesError
from .finder import find_build_dependencies
from .logger import log
from .utils import get_version


class BuildDependencyCompiler:
    """Resolve exact build dependencies."""

    def __init__(self, repository: PyPIRepository) -> None:
        self.repository = repository
        self.resolver = None
        self.dependency_cache = {}

    def resolve(
        self,
        install_requirements: Iterable[InstallRequirement],
    ) -> set[InstallRequirement]:
        """Resolve all build dependencies for a given set of dependencies."""
        all_build_deps = []
        for ireq in install_requirements:
            log.info("=" * 80)
            log.info(str(ireq))
            log.info("-" * 80)
            req_version = get_version(ireq)
            ireq_name = f"{ireq.name}=={req_version}"
            if ireq_name in self.dependency_cache:
                all_build_deps.extend(self.dependency_cache[ireq_name])
                log.debug(f"{ireq} exists in our cache, moving on...")
                continue
            raw_build_dependencies = find_build_dependencies(
                ireq.name, req_version, raise_setuppy_parsing_exc=False
            )
            if not raw_build_dependencies:
                self.dependency_cache[ireq_name] = set()
                continue
            # 'find_build_dependencies' is very naive - by design - and only returns
            # a simple list of strings representing build (or transitive) dependencies.
            # We will use the excellent resolver from piptools to find dependencies of
            # build dependencies, but first we need to convert our list of requirements
            # to the format used by piptools
            build_ireqs = map(
                partial(install_req_from_req_string, comes_from=ireq.name),
                raw_build_dependencies,
            )
            build_dependencies = self._resolve_with_piptools(
                package=ireq_name, ireqs=build_ireqs
            )
            # dependencies of build dependencies might have their own build
            # dependencies, so let's recursively search for those.
            build_deps_qty = 0
            while len(build_dependencies) != build_deps_qty:
                build_deps_qty = len(build_dependencies)
                build_dependencies |= set(self.resolve(build_dependencies))
            self.dependency_cache[ireq_name] = build_dependencies

            all_build_deps.extend(build_dependencies)

        return deduplicate_install_requirements(all_build_deps)

    def _resolve_with_piptools(
        self, package: str, ireqs: Iterable[InstallRequirement]
    ) -> set[InstallRequirement]:
        # backup unsafe data before overriding resolver, we will need it later
        # on piptools writer to export the file
        unsafe_packages = getattr(self.resolver, "unsafe_packages", set())
        unsafe_constraints = getattr(self.resolver, "unsafe_constraints", set())
        # override resolver - we only want the latest and greatest
        self.resolver = BacktrackingResolver(
            constraints=ireqs,
            existing_constraints={},
            repository=self.repository,
            allow_unsafe=True,
        )
        try:
            requirements = self.resolver.resolve()
        except DistributionNotFound as err:
            if isinstance(err.__cause__, ResolutionImpossible):  # pragma: no branch
                raise UnsolvableDependenciesError(package, err.__cause__.args)  # noqa: B904
            # TODO: We don't know how to reproduce the condition below, or even know if
            # it is possible.
            raise err  # pragma: no cover
        self.resolver.unsafe_packages |= unsafe_packages
        self.resolver.unsafe_constraints |= unsafe_constraints
        return requirements


def deduplicate_install_requirements(ireqs: Iterable[InstallRequirement]):
    """Deduplicate InstallRequirements."""
    unique_ireqs = {}
    for ireq in ireqs:
        version_tuple = ireq.name, get_version(ireq)
        if version_tuple not in unique_ireqs:
            # NOTE: piptools hacks pip's InstallRequirement to allow support from
            # multiple sources. Let's use the same attr so piptools file writer can
            # use this information.
            # https://github.com/jazzband/pip-tools/blob/53309647980e2a4981db54c0033f98c61142de0b/piptools/resolver.py#L118-L122
            # https://github.com/jazzband/pip-tools/blob/53309647980e2a4981db54c0033f98c61142de0b/piptools/writer.py#L309-L314
            ireq._source_ireqs = getattr(ireq, "_source_ireqs", [ireq])
            unique_ireqs[version_tuple] = ireq
        else:
            unique_ireqs[version_tuple]._source_ireqs.append(ireq)
    return set(unique_ireqs.values())
