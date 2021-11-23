#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Update DB charm module."""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus

from db_upgrade import MongoUpgrade, MysqlUpgrade

logger = logging.getLogger(__name__)


class UpgradeDBCharm(CharmBase):
    """Upgrade DB Charm operator."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        mongo_uri = self.config.get("mongodb_uri")
        mysql_uri = self.config.get("mysql_uri")
        self.mongo = MongoUpgrade(mongo_uri) if mongo_uri else None
        self.mysql = MysqlUpgrade(mysql_uri) if mysql_uri else None

        if not self.mongo and not self.mysql:
            self.unit.status = BlockedStatus("mongodb_uri and/or mysql_uri must be set")
            return

        # Observe events
        event_observe_mapping = {
            self.on.update_db_action: self._on_update_db_action,
            self.on.get_valid_paths_action: self._on_get_valid_paths_action,
        }
        for event, observer in event_observe_mapping.items():
            self.framework.observe(event, observer)
        self.unit.status = ActiveStatus()

    def _on_update_db_action(self, event):
        """Handle the update-db action."""
        current_version = event.params["current-version"]
        target_version = event.params["target-version"]
        mysql_only = event.params.get("mysql-only")
        mongodb_only = event.params.get("mongodb-only")

        try:
            results = {}
            if mysql_only and mongodb_only:
                raise Exception("cannot set both mysql-only and mongodb-only options to True")
            if mysql_only:
                self._upgrade_mysql(current_version, target_version)
                results["mysql"] = "Upgraded successfully"
            elif mongodb_only:
                self._upgrade_mongodb(current_version, target_version)
                results["mongodb"] = "Upgraded successfully"
            else:
                self._upgrade_mysql(current_version, target_version)
                results["mysql"] = "Upgraded successfully"
                self._upgrade_mongodb(current_version, target_version)
                results["mongodb"] = "Upgraded successfully"
            event.set_results(results)
        except Exception as e:
            event.fail(f"Failed DB Upgrade: {e}")

    def _on_get_valid_paths_action(self, event):
        pass

    def _upgrade_mysql(self, current_version, target_version):
        logger.debug("Upgrading mysql")
        self.mysql.upgrade(current_version, target_version)

    def _upgrade_mongodb(self, current_version, target_version):
        logger.debug("Upgrading mongodb")
        self.mongo.upgrade(current_version, target_version)


if __name__ == "__main__":  # pragma: no cover
    main(UpgradeDBCharm, use_juju_for_storage=True)
