#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Interface functions for interfacing with applications
@author: cem

"""

from config import MONGO_CONN_STRING

from pymongo import MongoClient
client = MongoClient(MONGO_CONN_STRING)


from requests import post

# app = Flask(__name__)

# app.register_blueprint(routeX_app)

from __main__ import session

import re 
def object_list(inp, user):
    result = post(session["authorized"]["api_urls"]["object_list"], 
                    data={"inp": inp, "user": user})
    return result.json()

def object_name(otype, oid):
    result = post(session["authorized"]["api_urls"]["object_name"], 
                    data={"otype": otype, "oid": oid})
    return result.text


def authorized_users(otype, oid):
    print("otype: ", otype, "oid: ", oid)
    result = post(session["authorized"]["api_urls"]["authorized_users"], 
                    data={"otype": otype, "oid": oid})
    return result.json()
