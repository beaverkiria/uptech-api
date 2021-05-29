import copy
from typing import Dict


def get_marker_kwargs(pytest_fixture_request, pytest_marker_name, **kwargs):
    """
    Get marker kwargs arguments if they are provided.
    In other case return default values.

    :param pytest_fixture_request: fixture request
    :param pytest_marker_name: marker name
    :param kwargs: default keyword arguments
    :return: keyword arguments
    :rtype: dict
    """
    markers = [*pytest_fixture_request.node.iter_markers(pytest_marker_name)]
    assert not markers or all(not m.args for m in markers), "Marker %s has arguments" % pytest_marker_name

    result = copy.deepcopy(kwargs)
    for m in reversed(markers):
        result.update(copy.deepcopy(m.kwargs))

    return result


def _main_attr(attr):
    return attr.split("__")[0]


def get_factory_kwargs(pytest_fixture_request, factory_name: str, **kwargs) -> Dict:
    """
    Get marker factory kwargs arguments if they are provided.
    In other case return default values.

    :param pytest_fixture_request: fixture request
    :param factory_name: marker name
    :param kwargs: frozen arguments which can't be override
    """
    factory_kwarg = get_marker_kwargs(pytest_fixture_request, f"{factory_name}_factory")
    factory_attrs = {_main_attr(i) for i in factory_kwarg}
    intersection = factory_attrs.intersection(kwargs)
    assert not intersection, f"can't override {', '.join(sorted(intersection))} for {factory_name} fixture"
    factory_kwarg.update(kwargs)
    return factory_kwarg
