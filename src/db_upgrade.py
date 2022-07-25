#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import json
import logging

from pymongo import MongoClient

logger = logging.getLogger(__name__)


def _upgrade_mongo_10_12(mongo_uri):
    logger.info("Entering in _update_mongo_10_12 function")
    myclient = MongoClient(mongo_uri)
    mydb = myclient["osm"]

    def _update_nsr():
        logger.info("Entering in _update_nsr function")
        namespace = "kube-system:"
        mycol = mydb["nsrs"]

        for nsr in mycol.find():
            logger.debug(f"Updating {nsr['_id']} nsr")
            for key, values in nsr.items():
                if isinstance(values, list):
                    item_list = []
                    for value in values:
                        if isinstance(value, dict) and value.get("vim_info"):
                            index = list(value["vim_info"].keys())[0]
                            if not value["vim_info"][index].get("vim_message"):
                                value["vim_info"][index]["vim_message"] = None
                            item_list.append(value)
                        myquery = {"_id": nsr["_id"]}
                        mycol.update_one(myquery, {"$set": {key: item_list}})
            if nsr["_admin"].get("deployed"):
                k8s_list = []
                for k8s in nsr["_admin"]["deployed"].get("K8s"):
                    if k8s.get("k8scluster-uuid"):
                        k8s["k8scluster-uuid"] = k8s["k8scluster-uuid"].replace(namespace, "", 1)
                    k8s_list.append(k8s)
                myquery = {"_id": nsr["_id"]}
                mycol.update_one(myquery, {"$set": {"_admin.deployed.K8s": k8s_list}})

    def _update_vnfr():
        logger.info("Entering in _update_vnfr function")
        mycol = mydb["vnfrs"]
        for vnfr in mycol.find():
            logger.debug(f"Updating {vnfr['_id']} vnfr")
            vdur_list = []
            for vdur in vnfr["vdur"]:
                if vdur.get("vim_info"):
                    index = list(vdur["vim_info"].keys())[0]
                    if not vdur["vim_info"][index].get("vim_message"):
                        vdur["vim_info"][index]["vim_message"] = None
                    if vdur["vim_info"][index].get(
                        "interfaces", "Not found"
                    ) != "Not found" and not vdur["vim_info"][index].get("interfaces_backup"):
                        vdur["vim_info"][index]["interfaces_backup"] = vdur["vim_info"][index][
                            "interfaces"
                        ]
                vdur_list.append(vdur)
            myquery = {"_id": vnfr["_id"]}
            mycol.update_one(myquery, {"$set": {"vdur": vdur_list}})

    def _update_k8scluster():
        logger.info("Entering in _update_k8scluster function")
        namespace = "kube-system:"
        mycol = mydb["k8sclusters"]
        for k8scluster in mycol.find():
            if k8scluster["_admin"].get("helm-chart") and k8scluster["_admin"]["helm-chart"].get(
                "id"
            ):
                if k8scluster["_admin"]["helm-chart"]["id"].startswith(namespace):
                    k8scluster["_admin"]["helm-chart"]["id"] = k8scluster["_admin"]["helm-chart"][
                        "id"
                    ].replace(namespace, "", 1)
            if k8scluster["_admin"].get("helm-chart-v3") and k8scluster["_admin"][
                "helm-chart-v3"
            ].get("id"):
                if k8scluster["_admin"]["helm-chart-v3"]["id"].startswith(namespace):
                    k8scluster["_admin"]["helm-chart-v3"]["id"] = k8scluster["_admin"][
                        "helm-chart-v3"
                    ]["id"].replace(namespace, "", 1)
            myquery = {"_id": k8scluster["_id"]}
            mycol.update_one(myquery, {"$set": k8scluster})

    _update_nsr()
    _update_vnfr()
    _update_k8scluster()


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


def _update_nslcmops_params(mongo_uri):
    """Updates the nslcmops collection to change the addtional params to a string."""
    logger.info("Entering in _update_nslcmops_params function")
    myclient = MongoClient(mongo_uri)
    mydb = myclient["osm"]
    collist = mydb.list_collection_names()

    if "nslcmops" in collist:
        mycol = mydb["nslcmops"]
        for x in mycol.find():
            if x.get("operationParams"):
                if x["operationParams"].get("additionalParamsForVnf") and isinstance(
                    x["operationParams"].get("additionalParamsForVnf"), list
                ):
                    string_param = json.dumps(x["operationParams"]["additionalParamsForVnf"])
                    myquery = {"_id": x["_id"]}
                    mycol.update_one(
                        myquery,
                        {"$set": {"operationParams": {"additionalParamsForVnf": string_param}}},
                    )
                elif x["operationParams"].get("primitive_params") and isinstance(
                    x["operationParams"].get("primitive_params"), dict
                ):
                    string_param = json.dumps(x["operationParams"]["primitive_params"])
                    myquery = {"_id": x["_id"]}
                    mycol.update_one(
                        myquery,
                        {"$set": {"operationParams": {"primitive_params": string_param}}},
                    )


def _update_vnfrs_params(mongo_uri):
    """Updates the vnfrs collection to change the additional params to a string."""
    logger.info("Entering in _update_vnfrs_params function")
    myclient = MongoClient(mongo_uri)
    mydb = myclient["osm"]
    collist = mydb.list_collection_names()

    if "vnfrs" in collist:
        mycol = mydb["vnfrs"]
        for vnfr in mycol.find():
            if vnfr.get("kdur"):
                kdur_list = []
                for kdur in vnfr["kdur"]:
                    if kdur.get("additionalParams") and not isinstance(
                        kdur["additionalParams"], str
                    ):
                        kdur["additionalParams"] = json.dumps(kdur["additionalParams"])
                    kdur_list.append(kdur)
                myquery = {"_id": vnfr["_id"]}
                mycol.update_one(
                    myquery,
                    {"$set": {"kdur": kdur_list}},
                )
                vnfr["kdur"] = kdur_list


def _patch_1837(mongo_uri):
    """Updates de database to change the additional params from dict to a string."""
    logger.info("Entering in _patch_1837 function")
    _update_nslcmops_params(mongo_uri)
    _update_vnfrs_params(mongo_uri)


MONGODB_UPGRADE_FUNCTIONS = {
    "9": {"10": [_upgrade_mongo_9_10]},
    "10": {"12": [_upgrade_mongo_10_12]},
}
MYSQL_UPGRADE_FUNCTIONS = {}
BUG_FIXES = {
    1837: _patch_1837,
}


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

    def apply_patch(self, bug_number: int) -> None:
        """Checks the bug-number and applies the fix in the database."""
        if bug_number not in BUG_FIXES:
            raise Exception(f"There is no patch for bug {bug_number}")
        patch_function = BUG_FIXES[bug_number]
        patch_function(self.mongo_uri)


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
