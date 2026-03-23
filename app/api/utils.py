"""
api/utils.py

Response envelope helpers for the public REST API.

Every API response — success or error — goes through one of these
helpers to ensure a consistent outer shape across all endpoints.
"""


def success_response(data):
    """
    Wrap data in a success envelope.

    Collections receive a ``count`` field; single objects do not.
    """
    if isinstance(data, list):
        return {"success": True, "data": data, "count": len(data)}
    return {"success": True, "data": data}


def error_response(message):
    """Wrap an error message in the standard error envelope."""
    return {"success": False, "error": message}
