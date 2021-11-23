#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import logging

logger = logging.getLogger(__name__)


class DbUpgrade:
    """Upgrade Database."""

    def __init__(self):

        self.VALID_PATHS = {}

    def _get_upgrade_functions(self, current, target):
        """Get the functions in charge of the upgrade."""
        upgrade_functions = []
        for i in range(current, target):
            upgrade_functions.append(self.VALID_PATHS[f"{i}_{i + 1}"])
        return upgrade_functions

    def upgrade(self, current, target, db):
        """Validates the upgrading path and upgrades the DB."""
        logger.info(f"Upgrading {db} DB")
        self.validate_upgrade(current, target, db)
        functions = self._get_upgrade_functions(current, target)
        for function in functions:
            function()

    def validate_upgrade(self, current, target, db):
        """Check if the upgrade path chosen is possible."""
        logger.info(f"Validating the upgrade path: {current}_{target} for {db}")
        for i in range(current, target):
            if f"{i}_{i + 1}" not in self.VALID_PATHS.keys():
                raise Exception(
                    f"There is not a valid upgrade path for {db} from {current} to {target} versions"
                )
