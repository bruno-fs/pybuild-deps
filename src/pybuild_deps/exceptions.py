"""custom exceptions for pybuild-deps."""


class PyBuildDepsError(Exception):
    """Custom exception for pybuild-deps."""


class UnsolvableDependenciesError(PyBuildDepsError):
    """Unsolvable dependencies."""

    def __init__(self, unsolvable_deps, constraints) -> None:
        self.unsolvable_deps = unsolvable_deps
        self.constraints = constraints

    def __str__(self):
        packages = {req_list[0].requirement.name for req_list in self.unsolvable_deps}
        packages |= {p.replace("-", "_") for p in packages}
        packages |= {p.replace("_", "-") for p in packages}
        unsolvable_deps = []
        for constraint in self.constraints:
            if constraint.name in packages:
                unsolvable_deps.append(constraint)
        unsolvable_deps = "\n".join(str(p) for p in unsolvable_deps)
        return (
            "Impossible resolve dependencies. See the conflicting dependencies "
            f"below:\n{unsolvable_deps}"
        )
