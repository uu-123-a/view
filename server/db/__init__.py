"""Database backend initialization."""

from .mysql_compat import enable_mysql_compat

MYSQL_ENABLED = enable_mysql_compat()
