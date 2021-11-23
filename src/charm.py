#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Update DB charm module."""

import logging

from mongoUpgrade import MongoUpgrade
from mysqlUpgrade import MysqlUpgrade
from ops.charm import CharmBase, ConfigChangedEvent, WorkloadEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus
from pymongo import MongoClient

logger = logging.getLogger(__name__)

REQUIRED_CONFIG = ()
VALID_PATHS = (
    "9_10",
    )


class UpgradeDBCharm(CharmBase):
    """Upgrade DB Charm operator."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        mongo_uri = self.config.get("mongodb_uri")
        mysql_uri = self.config.get("mysql_uri")
        self.mongo = MongoUpgrade(mongo_uri) if mongo_uri else None
        self.mysql = MysqlUpgrade(mysql_uri) if mysql_uri else None

        event_observe_mapping = {
            self.on.update_db_pebble_ready: self._on_update_db_pebble_ready,
            self.on.config_changed: self._on_config_changed,
            self.on.update_db_action: self._on_update_db_action,
            self.on.get_valid_paths_action: self._on_get_valid_paths_action,
        }
        for event, observer in event_observe_mapping.items():
            self.framework.observe(event, observer)

    @property
    def container(self):
        """Property to get update-db container."""
        return self.unit.get_container("update-db")

    @property
    def services(self):
        """Property to get the services in the container plan."""
        return self.container.get_plan().services

    def _on_update_db_pebble_ready(self, _: WorkloadEvent):
        self._restart()

    def _on_config_changed(self, event: ConfigChangedEvent):
        if self.container.can_connect():
            self._restart()
        else:
            logger.info("pebble socket not available, deferring config-changed")
            event.defer()
            self.unit.status = MaintenanceStatus("waiting for pebble to start")

    def _on_update_db_action(self, event):
        """Handle the update-db action."""
        
        current_version = event.params["current-version"]
        target_version = event.params["target-version"]
        try:
            if event.params.get("mysql-only") and self.mysql:
                logger.debug(f"Upgrade MySQL only")
                self.mysql.upgrade(current_version, target_version, "MySQL")
            elif event.params.get("mongo-only") and self.mongo:
                logger.debug(f"Upgrade Mongo only")
                self.mongo.upgrade(current_version, target_version, "MongoDB")
            elif self.mysql and self.mongo:
                self.mysql.upgrade(current_version, target_version, "MySQL")
                self.mongo.upgrade(current_version, target_version, "MongoDB")
            else:
                raise Exception(f"Mongo and/or Mysql URI not configured")
            event.set_results({"output": f"DBs Upgraded"})
        except Exception as e:
            event.fail(f"Failed DB Upgrade: {e}")

    def _on_get_valid_paths_action(self, event):
        pass

    def _restart(self):
        layer = self._get_pebble_layer()
        self._set_pebble_layer(layer)
        self._restart_service()
        self.unit.status = ActiveStatus()

    def _restart_service(self):
        container = self.container
        if "update-db" in self.services:
            container.restart("update-db")
            logger.info("update-db service has been restarted")

    def _get_pebble_layer(self):
        return {
            "summary": "update-db layer",
            "description": "pebble config layer for update-db",
            "services": {
                "update-db": {
                    "override": "replace",
                    "summary": "update-db service",
                    "command": "sleep infinity",
                    "startup": "enabled",
                    "environment": {},
                }
            },
        }

    def _set_pebble_layer(self, layer):
        self.container.add_layer("update-db", layer, combine=True)


if __name__ == "__main__":  # pragma: no cover
    main(UpgradeDBCharm, use_juju_for_storage=True)
