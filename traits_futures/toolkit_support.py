from __future__ import absolute_import, print_function, unicode_literals

import warnings

import pkg_resources

from pyface.toolkit import toolkit_object


#: entry-point group for message routers.
MESSAGE_ROUTER_GROUP = "traits_futures.routers"


def message_router_class_for_toolkit(toolkit):
    matching_entry_points = list(
        pkg_resources.iter_entry_points(
            group=MESSAGE_ROUTER_GROUP, name=toolkit))

    if not matching_entry_points:
        raise RuntimeError(
            "No message router object found for toolkit {!r}".format(toolkit))

    if len(matching_entry_points) > 1:
        msg = (
            "Multiple {!r} entry points found for "
            "toolkit {!r}. Using the first one found. "
        ).format(MESSAGE_ROUTER_GROUP, toolkit)
        warnings.warn(msg, RuntimeWarning)

    entry_point = matching_entry_points[0]
    return entry_point.load()


def message_router_class():
    return message_router_class_for_toolkit(toolkit_object.toolkit)
