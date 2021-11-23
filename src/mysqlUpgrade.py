#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import logging

from dbUpgrade import DbUpgrade
from mysql import connector

logger = logging.getLogger(__name__)


class MysqlUpgrade(DbUpgrade):
    """Upgrade MongoDB Database"""

    def __init__(self, mysql_uri):

        self.mysql_uri = mysql_uri
        self.VALID_PATHS = {}
 