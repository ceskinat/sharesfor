#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Sample interface functions to routeX

Created on Wed Sep 14 13:21:19 2022

@author: cem

"""

from config import MONGO_CONN_STRING

from pymongo import MongoClient
client = MongoClient(MONGO_CONN_STRING)




# app = Flask(__name__)

# app.register_blueprint(routeX_app)

import re 
def object_list(inp):
    # returns a sample list of objects
    db = client.routeX_demo
    lst = list(db.objects.find({"oname": re.compile(inp, re.I)}))

    return lst


def object_name(otype, oid):
    for obj in object_list(""):
        if obj["otype"] == otype and obj["oid"] == oid:
            return obj["oname"]
    return None


def all_users():
    db = client.routeX_demo
    return list(db.users.find())
    # return [
    #         "ceskinat@gmail.com",
    #         "cem@solusmart.com",
    #         "falan@filan.com"
    #         ]
