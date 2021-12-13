# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import unittest
from unittest.mock import MagicMock, Mock, patch

import db_upgrade
from db_upgrade import MongoUpgrade, MysqlUpgrade, _upgrade_mongo_9_10

logger = logging.getLogger(__name__)


class TestUpgradeMongo910(unittest.TestCase):
    @patch("db_upgrade.MongoClient")
    def test_upgrade_mongo_9_10(self, mock_mongo_client):
        mock_db = MagicMock()
        alarms = Mock()
        alarms.find.return_value = [{"_id": "1", "alarm_status": "1"}]
        collection_dict = {"alarms": alarms, "other": {}}
        mock_db.list_collection_names.return_value = collection_dict
        mock_db.__getitem__.side_effect = collection_dict.__getitem__
        mock_mongo_client.return_value = {"osm": mock_db}
        _upgrade_mongo_9_10("mongo_uri")
        alarms.update_one.assert_not_called()

    @patch("db_upgrade.MongoClient")
    def test_upgrade_mongo_9_10_no_alarms(self, mock_mongo_client):
        mock_db = Mock()
        mock_db.__getitem__ = Mock()

        mock_db.list_collection_names.return_value = {"other": {}}
        mock_db.alarms.return_value = None
        mock_mongo_client.return_value = {"osm": mock_db}
        self.assertIsNone(_upgrade_mongo_9_10("mongo_uri"))

    @patch("db_upgrade.MongoClient")
    def test_upgrade_mongo_9_10_no_alarm_status(self, mock_mongo_client):
        mock_db = MagicMock()
        alarms = Mock()
        alarms.find.return_value = [{"_id": "1"}]
        collection_dict = {"alarms": alarms, "other": {}}
        mock_db.list_collection_names.return_value = collection_dict
        mock_db.__getitem__.side_effect = collection_dict.__getitem__
        mock_db.alarms.return_value = alarms
        mock_mongo_client.return_value = {"osm": mock_db}
        _upgrade_mongo_9_10("mongo_uri")
        alarms.update_one.assert_called_once_with({"_id": "1"}, {"$set": {"alarm_status": "ok"}})


class TestMongoUpgrade(unittest.TestCase):
    def setUp(self):
        self.upgrade_function = Mock()
        db_upgrade.MONGODB_UPGRADE_FUNCTIONS = {"9": {"10": [self.upgrade_function]}}

    def test_validate_upgrade_fail_target(self):
        valid_current = "9"
        invalid_target = "7"
        mongo = MongoUpgrade("http://fake_mongo:27017")
        with self.assertRaises(Exception) as context:
            mongo._validate_upgrade(valid_current, invalid_target)
        self.assertEqual("cannot upgrade from version 9 to 7.", str(context.exception))

    def test_validate_upgrade_fail_current(self):
        invalid_current = "7"
        invalid_target = "8"
        mongo = MongoUpgrade("http://fake_mongo:27017")
        with self.assertRaises(Exception) as context:
            mongo._validate_upgrade(invalid_current, invalid_target)
        self.assertEqual("cannot upgrade from 7 version.", str(context.exception))

    def test_validate_upgrade_pass(self):
        valid_current = "9"
        valid_target = "10"
        mongo = MongoUpgrade("http://fake_mongo:27017")
        self.assertIsNone(mongo._validate_upgrade(valid_current, valid_target))

    @patch("db_upgrade.MongoUpgrade._validate_upgrade")
    def test_update_mongo_success(self, mock_validate):
        valid_current = "9"
        valid_target = "10"
        mock_validate.return_value = ""
        mongo = MongoUpgrade("mongodb://fake_mongo:27017")
        mongo.upgrade(valid_current, valid_target)
        self.upgrade_function.assert_called_once()


class TestMysqlUpgrade(unittest.TestCase):
    def setUp(self):
        self.upgrade_function = Mock()
        db_upgrade.MYSQL_UPGRADE_FUNCTIONS = {"9": {"10": [self.upgrade_function]}}

    def test_validate_upgrade_mysql_fail_current(self):
        invalid_current = "7"
        invalid_target = "8"
        mysql = MysqlUpgrade("mysql://fake_mysql:23023")
        with self.assertRaises(Exception) as context:
            mysql._validate_upgrade(invalid_current, invalid_target)
        self.assertEqual("cannot upgrade from 7 version.", str(context.exception))

    def test_validate_upgrade_mysql_fail_target(self):
        valid_current = "9"
        invalid_target = "7"
        mysql = MysqlUpgrade("mysql://fake_mysql:23023")
        with self.assertRaises(Exception) as context:
            mysql._validate_upgrade(valid_current, invalid_target)
        self.assertEqual("cannot upgrade from version 9 to 7.", str(context.exception))

    def test_validate_upgrade_mysql_success(self):
        valid_current = "9"
        valid_target = "10"
        mysql = MysqlUpgrade("mysql://fake_mysql:23023")
        self.assertIsNone(mysql._validate_upgrade(valid_current, valid_target))

    @patch("db_upgrade.MysqlUpgrade._validate_upgrade")
    def test_upgrade_mysql_success(self, mock_validate):
        valid_current = "9"
        valid_target = "10"
        mock_validate.return_value = ""
        mysql = MysqlUpgrade("mysql://fake_mysql:5333")
        mysql.upgrade(valid_current, valid_target)
        self.upgrade_function.assert_called_once()
