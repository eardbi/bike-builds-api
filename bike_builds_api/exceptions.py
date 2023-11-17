# --------------------------------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------------------------------

__all__ = [
    'HandledException',
    'ConfigError',
]


# --------------------------------------------------------------------------------------------------
# Base Class
# --------------------------------------------------------------------------------------------------

class HandledException(Exception):
    """Errors that are handled by the program. This is a base class for all handled exceptions."""
    pass


# --------------------------------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------------------------------

class ConfigError(HandledException):
    """Errors that are caused by bugs in a config."""
    pass
