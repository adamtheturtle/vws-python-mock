"""
Common utilities for creating mock routes.
"""

import base64
import cgi
import hashlib
import hmac
import io
import json
from typing import Any, Callable, Dict, List, Mapping, Tuple, Union

import wrapt
from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context


class Route:
    """
    A container for the route details which `requests_mock` needs.

    We register routes with names, and when we have an instance to work with
    later.
    """

    def __init__(
        self,
        route_name: str,
        path_pattern: str,
        http_methods: List[str],
    ) -> None:
        """
        Args:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            http_methods: HTTP methods that map to the route function.

        Attributes:
            route_name: The name of the method.
            path_pattern: The end part of a URL pattern. E.g. `/targets` or
                `/targets/.+`.
            http_methods: HTTP methods that map to the route function.
            endpoint: The method `requests_mock` should call when the endpoint
                is requested.
        """
        self.route_name = route_name
        self.path_pattern = path_pattern
        self.http_methods = http_methods


def json_dump(body: Dict[str, Any]) -> str:
    """
    Returns:
        JSON dump of data in the same way that Vuforia dumps data.
    """
    return json.dumps(obj=body, separators=(',', ':'))


@wrapt.decorator
def set_content_length_header(
    wrapped: Callable[..., str],
    instance: Any,  # pylint: disable=unused-argument
    args: Tuple[_RequestObjectProxy, _Context],
    kwargs: Dict,
) -> str:
    """
    Set the `Content-Length` header.

    Args:
        wrapped: An endpoint function for `requests_mock`.
        instance: The class that the endpoint function is in.
        args: The arguments given to the endpoint function.
        kwargs: The keyword arguments given to the endpoint function.

    Returns:
        The result of calling the endpoint.
    """
    _, context = args

    result = wrapped(*args, **kwargs)
    context.headers['Content-Length'] = str(len(result))
    return result


def parse_multipart(  # pylint: disable=invalid-name
    fp: io.BytesIO,
    pdict: Mapping[str, bytes],
) -> Dict[str, List[Union[str, bytes]]]:
    """
    This wraps ``_parse_multipart`` to work around
    https://bugs.python.org/issue34226.

    See https://docs.python.org/3.7/library/cgi.html#_parse_multipart.
    """
    pdict = {
        'CONTENT-LENGTH': str(len(fp.getvalue())).encode(),
        **pdict,
    }

    # Ignore type error as per
    # https://github.com/python/typeshed/issues/2473
    return cgi.parse_multipart(  # type: ignore
        fp=fp,
        pdict=pdict,
    )


def _compute_hmac_base64(key: bytes, data: bytes) -> bytes:
    """
    Return the Base64 encoded HMAC-SHA1 hash of the given `data` using the
    provided `key`.
    """
    hashed = hmac.new(key=key, msg=None, digestmod=hashlib.sha1)
    hashed.update(msg=data)
    return base64.b64encode(s=hashed.digest())


def authorization_header(  # pylint: disable=too-many-arguments
    access_key: bytes,
    secret_key: bytes,
    method: str,
    content: bytes,
    content_type: str,
    date: str,
    request_path: str,
) -> bytes:
    """
    Return an `Authorization` header which can be used for a request made to
    the VWS API with the given attributes.

    Args:
        access_key: A VWS server or client access key.
        secret_key: A VWS server or client secret key.
        method: The HTTP method which will be used in the request.
        content: The request body which will be used in the request.
        content_type: The `Content-Type` header which will be used in the
            request.
        date: The current date which must exactly match the date sent in the
            `Date` header.
        request_path: The path to the endpoint which will be used in the
            request.
    """
    hashed = hashlib.md5()
    hashed.update(content)
    content_md5_hex = hashed.hexdigest()

    components_to_sign = [
        method,
        content_md5_hex,
        content_type,
        date,
        request_path,
    ]
    string_to_sign = '\n'.join(components_to_sign)
    signature = _compute_hmac_base64(
        key=secret_key,
        data=bytes(
            string_to_sign,
            encoding='utf-8',
        ),
    )
    auth_header = b'VWS %s:%s' % (access_key, signature)
    return auth_header
