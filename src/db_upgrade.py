#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import logging

from pymongo import MongoClient

logger = logging.getLogger(__name__)


def _upgrade_mongo_9_10(mongo_uri):
    myclient = MongoClient(mongo_uri)
    mydb = myclient["osm"]
    collist = mydb.list_collection_names()

    if "alarms" in collist:
        mycol = mydb["alarms"]
        for x in mycol.find():
            if not x.get("alarm_status"):
                myquery = {"_id": x["_id"]}
                mycol.update_one(myquery, {"$set": {"alarm_status": "ok"}})


MONGODB_UPGRADE_FUNCTIONS = {"9": {"10": [_upgrade_mongo_9_10]}}
MYSQL_UPGRADE_FUNCTIONS = {}


class MongoUpgrade:
    """Upgrade MongoDB Database."""

    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri

    def upgrade(self, current, target):
        """Validates the upgrading path and upgrades the DB."""
        self._validate_upgrade(current, target)
        for function in MONGODB_UPGRADE_FUNCTIONS.get(current)[target]:
            function(self.mongo_uri)

    def _validate_upgrade(self, current, target):
        """Check if the upgrade path chosen is possible."""
        logger.info("Validating the upgrade path")
        if current not in MONGODB_UPGRADE_FUNCTIONS:
            raise Exception(f"cannot upgrade from {current} version.")
        if target not in MONGODB_UPGRADE_FUNCTIONS[current]:
            raise Exception(f"cannot upgrade from version {current} to {target}.")


class MysqlUpgrade:
    """Upgrade Mysql Database."""

    def __init__(self, mysql_uri):
        self.mysql_uri = mysql_uri

    def upgrade(self, current, target):
        """Validates the upgrading path and upgrades the DB."""
        self._validate_upgrade(current, target)
        for function in MYSQL_UPGRADE_FUNCTIONS[current][target]:
            function(self.mysql_uri)

    def _validate_upgrade(self, current, target):
        """Check if the upgrade path chosen is possible."""
        logger.info("Validating the upgrade path")
        if current not in MYSQL_UPGRADE_FUNCTIONS:
            raise Exception(f"cannot upgrade from {current} version.")
        if target not in MYSQL_UPGRADE_FUNCTIONS[current]:
            raise Exception(f"cannot upgrade from version {current} to {target}.")
