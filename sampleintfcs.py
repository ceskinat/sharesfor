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
#    lst = list(db.objects.find({"oname": re.compile(inp, re.I)}))
    lst = []
    for obj in db.objects.find({"oname": re.compile(inp, re.I)}):
        lst.append({"id": {"id": [obj["otype"], str(obj["oid"])], "name": obj["oname"]},
                    "name": obj["otype"] + ":" + obj["oname"]})


    return lst


def object_name(otype, oid):
    for obj in object_list(""):
        if obj["id"]["id"][0] == otype and str(obj["id"]["id"][1]) == oid:
            return obj["id"]["name"]
    return None


def all_users():
    # returns in the form of {"id": id, "name": username}
    db = client.routeX_demo
    
    return [{"id": x["_id"], "name": x["username"], "email": x.get("email", "") } for x in db.users.find()]
    # return [
    #         "ceskinat@gmail.com",
    #         "cem@solusmart.com",
    #         "falan@filan.com"
    #         ]

def authorized_users(otype, oid):
    return all_users() #assume everyone is authorized for every object