import functools
import pprint
from dataclasses import asdict, is_dataclass
from typing import Any, Sequence

import pytest
from requests.models import Response

from common.types import Dataclass
from core.api.exceptions import NotFoundError

prettify = functools.partial(pprint.pformat, indent=4)


def object_matches_data(
    obj: Any, data: dict[str, Any] | Dataclass, *, exclude: Sequence[str] | None = None
):
    """
    Assert attribute values of provided object match expected data
    Data can be either dictionary or dataclass
    Optionally you can exclude fields from being checked
    """

    if exclude:
        assert isinstance(
            exclude, (tuple, list, set)
        ), "Invalid exclude value. Should be tuple, list or set of strings"

    if is_dataclass(data):
        data = asdict(data)

    for key, val in data.items():  # type: ignore
        if exclude and key in exclude:
            continue

        try:
            actual_val = getattr(obj, key)
        except AttributeError:
            pytest.fail(f"Object doesn't have attribute {key}. Expected {repr(val)}")

        if not actual_val == val:
            pytest.fail(f"Expected {repr(val)}, but got {repr(actual_val)}")


def _check_status_code(response: Response, expected: int):
    if not response.status_code == expected:
        try:
            response_content = response.json()
        except ValueError:
            response_content = response.content

        pytest.fail(
            f"Expected status {expected}, but {response.status_code} received"
            f"\n\nResponse content: \n{prettify(response_content)}"
        )


def response_validation_error(
    response: Response,
    *,
    loc: str | None = None,
    msg: str | None = None,
    type: str | None = None,
):
    """
    Assert response returns 422 status code
    Optionally check loc, msg or type attributes in returned json
    """

    _check_status_code(response, 422)
    response_data = response.json()

    # TODO: handle multiple elements in response_data['detail']

    if loc:
        assert (
            loc in response_data["detail"][0]["loc"]
        ), f"expected loc {loc} not found in response\n{response_data}"

    if msg:
        assert (
            response_data["detail"][0]["msg"] == msg
        ), f"expected msg {msg} not found in response\n{response_data}"

    if type:
        assert (
            response_data["detail"][0]["type"] == type
        ), f"expected type {type} not found in response\n{response_data}"


def response_error_with_detail(response: Response, status_code: int, detail: str):
    """
    Assert response returns expected error status code and detail in json matches
    expectation
    """
    _check_status_code(response, status_code)

    try:
        response_data = response.json()
        actual_detail = response_data["detail"]
    except (ValueError, KeyError):
        pytest.fail(f"Invalid response received \n{prettify(response.content)}")

    if actual_detail != detail:
        pytest.fail(
            "Expected detail not found in response\n\n"
            f"Expected: {detail}\nActual: {actual_detail}\n\n"
            f"Full response: {prettify(response_data)}"
        )


def response_not_found(response: Response):
    """
    Assert response returns NotFoundError status code and detail in json matches
    expectation
    """
    _check_status_code(response, NotFoundError.status_code)

    try:
        response_data = response.json()
        actual_detail = response_data["detail"]
    except (ValueError, KeyError):
        pytest.fail(f"Invalid response received \n{prettify(response.content)}")

    if actual_detail != NotFoundError.detail:
        pytest.fail(
            "Expected detail not found in response\n\n"
            f"Expected: {NotFoundError.detail}\nActual: {actual_detail}\n\n"
            f"Full response: {prettify(response_data)}"
        )
