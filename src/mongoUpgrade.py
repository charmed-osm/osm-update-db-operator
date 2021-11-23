#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import logging

from pymongo import MongoClient

from dbUpgrade import DbUpgrade

logger = logging.getLogger(__name__)


class MongoUpgrade(DbUpgrade):
    """Upgrade MongoDB Database."""

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
                        myquery = {"_id": x["_id"]}
                        mycol.update_one(myquery, {"$set": {"alarm_status": "ok"}})
