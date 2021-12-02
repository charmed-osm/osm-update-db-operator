# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock, patch

from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus
from ops.testing import Harness

from charm import UpgradeDBCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(UpgradeDBCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_initial_config(self):
        self.assertEqual(self.harness.model.unit.status, MaintenanceStatus(""))

    def test_config_changed(self):
        self.harness.update_config({"mongodb-uri": "foo"})
        print(self.harness.model.config)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_config_changed_blocked(self):
        self.harness.update_config({"log-level": "DEBUG"})
        print(self.harness.model.config)
        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("mongodb-uri and/or mysql-uri must be set"),
        )

    def test_update_db_fail_only(self):
        action_event = Mock(
            params={
                "current-version": 9,
                "target-version": 10,
                "mysql-only": True,
                "mongodb-only": True,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        self.assertEqual(
            action_event.fail.call_args,
            [("Failed DB Upgrade: cannot set both mysql-only and mongodb-only options to True",)],
        )

    @patch("charm.MysqlUpgrade")
    def test_update_db_mysql(self, mock_mysql_upgrade):
        self.harness.update_config({"mysql-uri": "foo"})
        action_event = Mock(
            params={
                "current-version": 9,
                "target-version": 10,
                "mysql-only": True,
                "mongodb-only": False,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        self.assertEqual(mock_mysql_upgrade.call_count, 2)

    @patch("charm.MongoUpgrade")
    def test_update_db_fail_mongo(self, mock_mongo_upgrade):
        self.harness.update_config({"mongodb-uri": "foo"})
        action_event = Mock(
            params={
                "current-version": 7,
                "target-version": 10,
                "mysql-only": False,
                "mongodb-only": True,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        self.assertEqual(mock_mongo_upgrade.call_count, 2)

    @patch("charm.MongoUpgrade")
    def test_update_db_not_configured_mongo(self, mock_mongo_upgrade):
        action_event = Mock(
            params={
                "current-version": 7,
                "target-version": 10,
                "mysql-only": False,
                "mongodb-only": True,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        mock_mongo_upgrade.assert_not_called()

    @patch("charm.MysqlUpgrade")
    def test_update_db_not_configured_mysql(self, mock_mysql_upgrade):
        action_event = Mock(
            params={
                "current-version": 7,
                "target-version": 10,
                "mysql-only": True,
                "mongodb-only": False,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        mock_mysql_upgrade.assert_not_called()

    @patch("charm.MongoUpgrade")
    @patch("charm.MysqlUpgrade")
    def test_update_db_fail(self, mock_mysql_upgrade, mock_mongo_upgrade):
        self.harness.update_config({"mongodb-uri": "foo"})
        self.harness.update_config({"mysql-uri": "foo"})
        action_event = Mock(
            params={
                "current-version": 7,
                "target-version": 10,
                "mysql-only": False,
                "mongodb-only": False,
            }
        )
        self.harness.charm._on_update_db_action(action_event)
        self.assertEqual(mock_mysql_upgrade.call_count, 2)
        self.assertEqual(mock_mongo_upgrade.call_count, 2)
