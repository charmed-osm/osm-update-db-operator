#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import logging

from dbUpgrade import DbUpgrade
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class MongoUpgrade(DbUpgrade):
    """Upgrade MongoDB Database"""

    def __init__(self, mongo_uri):

        self.mongo_uri = mongo_uri
        self.VALID_PATHS = {
            "9_10": self._upgrade_mongo_9_10,
            }

    def _upgrade_mongo_9_10(self):

        if self.mongo_uri:
            myclient = MongoClient(self.mongo_uri)
            mydb = myclient["osm"]
            collist = mydb.list_collection_names()

            if "alarms" in collist:
                mycol = mydb["alarms"]
                for x in mycol.find():
                    if not x.get("alarm_status"):
                        myquery = { "_id": x["_id"] }
                        mycol.update_one(myquery, {"$set": {"alarm_status": "ok"}})
    
    # def _get_upgrade_functions(self, current, target):
    #     upgrade_functions = []
    #     for i in range(int(current), int(target)):
    #         upgrade_functions.append(self.VALID_PATHS[f"{i}_{i + 1}"])
    #     return upgrade_functions

    # def upgrade(self, current, target):
    #     """"""
    #     logger.warning("Upgrading MongoDB")
    #     self.validate_upgrade(current, target)
    #     functions = self._get_upgrade_functions(current, target)
    #     for function in functions:
    #         function()

    # def validate_upgrade(self, current, target):
    #     """Check if the upgrade path chosen is possible"""
    #     logger.warning(f"{current}_{target}")
    #     for i in range(int(current), int(target)):
    #         if f"{i}_{i + 1}" not in self.VALID_PATHS.keys():
    #             raise Exception(f"There is not a valid MongoDB upgrade path from {current} to {target} versions")
