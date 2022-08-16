#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Upgrade DB charm module."""

import json
import logging

from pymongo import MongoClient

logger = logging.getLogger(__name__)


class MongoUpgrade1012:
    """Upgrade MongoDB Database from OSM v10 to v12."""

    @staticmethod
    def _remove_namespace_from_k8s(nsrs, nsr):
        namespace = "kube-system:"
        if nsr["_admin"].get("deployed"):
            k8s_list = []
            for k8s in nsr["_admin"]["deployed"].get("K8s"):
                if k8s.get("k8scluster-uuid"):
                    k8s["k8scluster-uuid"] = k8s["k8scluster-uuid"].replace(namespace, "", 1)
                k8s_list.append(k8s)
            myquery = {"_id": nsr["_id"]}
            nsrs.update_one(myquery, {"$set": {"_admin.deployed.K8s": k8s_list}})

    @staticmethod
    def _update_nsr(osm_db):
        """Update nsr.

        Add vim_message = None if it does not exist.
        Remove "namespace:" from k8scluster-uuid.
        """
        if "nsrs" not in osm_db.list_collection_names():
            return
        logger.info("Entering in MongoUpgrade1012._update_nsr function")

        nsrs = osm_db["nsrs"]
        for nsr in nsrs.find():
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
                    nsrs.update_one(myquery, {"$set": {key: item_list}})
            MongoUpgrade1012._remove_namespace_from_k8s(nsrs, nsr)

    @staticmethod
    def _update_vnfr(osm_db):
        """Update vnfr.

        Add vim_message to vdur if it does not exist.
        Copy content of interfaces into interfaces_backup.
        """
        if "vnfrs" not in osm_db.list_collection_names():
            return
        logger.info("Entering in MongoUpgrade1012._update_vnfr function")
        mycol = osm_db["vnfrs"]
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

    @staticmethod
    def _update_k8scluster(osm_db):
        """Remove namespace from helm-chart and helm-chart-v3 id."""
        if "k8sclusters" not in osm_db.list_collection_names():
            return
        logger.info("Entering in MongoUpgrade1012._update_k8scluster function")
        namespace = "kube-system:"
        k8sclusters = osm_db["k8sclusters"]
        for k8scluster in k8sclusters.find():
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
            k8sclusters.update_one(myquery, {"$set": k8scluster})

    @staticmethod
    def upgrade(mongo_uri):
        """Upgrade nsr, vnfr and k8scluster in DB."""
        logger.info("Entering in MongoUpgrade1012.upgrade function")
        myclient = MongoClient(mongo_uri)
        osm_db = myclient["osm"]
        MongoUpgrade1012._update_nsr(osm_db)
        MongoUpgrade1012._update_vnfr(osm_db)
        MongoUpgrade1012._update_k8scluster(osm_db)


class MongoUpgrade910:
    """Upgrade MongoDB Database from OSM v9 to v10."""

    @staticmethod
    def upgrade(mongo_uri):
        """Add parameter alarm status = OK if not found in alarms collection."""
        myclient = MongoClient(mongo_uri)
        osm_db = myclient["osm"]
        collist = osm_db.list_collection_names()

        if "alarms" in collist:
            mycol = osm_db["alarms"]
            for x in mycol.find():
                if not x.get("alarm_status"):
                    myquery = {"_id": x["_id"]}
                    mycol.update_one(myquery, {"$set": {"alarm_status": "ok"}})


class MongoPatch1837:
    """Patch Bug 1837 on MongoDB."""

    @staticmethod
    def _update_nslcmops_params(osm_db):
        """Updates the nslcmops collection to change the additional params to a string."""
        logger.info("Entering in MongoPatch1837._update_nslcmops_params function")
        if "nslcmops" in osm_db.list_collection_names():
            nslcmops = osm_db["nslcmops"]
            for nslcmop in nslcmops.find():
                if nslcmop.get("operationParams"):
                    if nslcmop["operationParams"].get("additionalParamsForVnf") and isinstance(
                        nslcmop["operationParams"].get("additionalParamsForVnf"), list
                    ):
                        string_param = json.dumps(
                            nslcmop["operationParams"]["additionalParamsForVnf"]
                        )
                        myquery = {"_id": nslcmop["_id"]}
                        nslcmops.update_one(
                            myquery,
                            {
                                "$set": {
                                    "operationParams": {"additionalParamsForVnf": string_param}
                                }
                            },
                        )
                    elif nslcmop["operationParams"].get("primitive_params") and isinstance(
                        nslcmop["operationParams"].get("primitive_params"), dict
                    ):
                        string_param = json.dumps(nslcmop["operationParams"]["primitive_params"])
                        myquery = {"_id": nslcmop["_id"]}
                        nslcmops.update_one(
                            myquery,
                            {"$set": {"operationParams": {"primitive_params": string_param}}},
                        )

    @staticmethod
    def _update_vnfrs_params(osm_db):
        """Updates the vnfrs collection to change the additional params to a string."""
        logger.info("Entering in MongoPatch1837._update_vnfrs_params function")
        if "vnfrs" in osm_db.list_collection_names():
            mycol = osm_db["vnfrs"]
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

    @staticmethod
    def patch(mongo_uri):
        """Updates the database to change the additional params from dict to a string."""
        logger.info("Entering in MongoPatch1837.patch function")
        myclient = MongoClient(mongo_uri)
        osm_db = myclient["osm"]
        MongoPatch1837._update_nslcmops_params(osm_db)
        MongoPatch1837._update_vnfrs_params(osm_db)


MONGODB_UPGRADE_FUNCTIONS = {
    "9": {"10": [MongoUpgrade910.upgrade]},
    "10": {"12": [MongoUpgrade1012.upgrade]},
}
MYSQL_UPGRADE_FUNCTIONS = {}
BUG_FIXES = {
    1837: MongoPatch1837.patch,
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
