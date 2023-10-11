"""Build depenencies parser for setup.py files."""

from __future__ import annotations

import ast
import operator
from contextlib import suppress

from ..exceptions import PyBuildDepsError


class SetupPyParsingError(PyBuildDepsError):
    """Error class to be used when a setup.py can't be parsed."""


def attrgetter(attr, obj):
    """Get attribute from object.

    Get attribute(s) acceppting a dotted notation.
    Returns None if attr is not found.
    """
    with suppress(AttributeError):
        return operator.attrgetter(attr)(obj)


def parse_setup_py(content: str):
    """Parse build dependencies from setup.py file.

    It attempts to cover more conventional use cases only.
    See its tests to have a better idea of what's supported.
    """
    try:
        code_tree = ast.parse(content)
        setup_expr = _get_setup_expr(code_tree)
        if setup_expr is None:
            # module don't have a setup/setuptools.setup
            return []

        setup_requires_ast = _get_setup_requires(setup_expr)
        return _resolve_deps(setup_requires_ast, code_tree)
    except (NotImplementedError, SyntaxError) as err:
        raise SetupPyParsingError from err


def _get_setup_expr(module: ast.Module) -> ast.Expr | None:
    for elem in module.body:
        if isinstance(elem, ast.Expr) and isinstance(
            attrgetter("value", elem), ast.Call
        ):
            func_id = attrgetter("func.id", elem.value)
            if func_id == "setup":
                return elem
            func_attr = attrgetter("func.attr", elem.value)
            func_value_id = attrgetter("func.value.id", elem.value)
            if func_attr == "setup" and func_value_id == "setuptools":
                return elem


def _get_setup_requires(setup_expr: ast.Expr):
    keywords = attrgetter("value.keywords", setup_expr) or []
    for kw in keywords:
        if kw.arg == "setup_requires":
            return kw.value


def _resolve_name(name: ast.Name, module: ast.Module):
    for elem in module.body:
        if isinstance(elem, ast.Assign):
            if not (len(elem.targets) == 1 and isinstance(elem.targets[0], ast.Name)):
                raise NotImplementedError()
            if elem.targets[0].id == name.id:
                if isinstance(elem.value, ast.Name):
                    return _resolve_name(elem.value, module)
                return elem.value


def _ast_value_getter(element, module: ast.Module):
    if isinstance(element, ast.Constant):
        return element.value
    elif isinstance(element, ast.Name):
        target_element = _resolve_name(element, module)
        return _ast_value_getter(target_element, module)
    raise NotImplementedError()


def _resolve_deps(deps_ast, module: ast.Module):
    if deps_ast is None:
        return []
    if isinstance(deps_ast, ast.List):
        return [_ast_value_getter(el, module) for el in deps_ast.elts]
    elif isinstance(deps_ast, ast.Name):
        value = _resolve_name(deps_ast, module)
        return _resolve_deps(value, module)
    raise NotImplementedError()
