#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Interface functions for CoursePage application

Created on Mon Sep 9, 2024

@author: cem

"""

from config import MONGO_CONN_STRING

from pymongo import MongoClient
client = MongoClient(MONGO_CONN_STRING)




# app = Flask(__name__)

# app.register_blueprint(routeX_app)

import re 
def object_list(inp, user):
    # user is a dictionary containing username, userid, email
    # returns a list of objects
    dbn = client.netkent
    db = client.netkent_lectures
    doc = db.s4s4rights.find_one({"userid": user["userid"]})
    if not doc:
        return # no data
    elif doc.get("role") == "master":
        courselist = [x["ders_kodu"] for x in db.courses.find()]

    elif doc.get("role") == "lecturer":
        courselist = doc["courses"]

    elif doc.get("role") == "student":
        courselist = [x["ders_kodu"] for x in dbn.courselist.find({"ogrenci_no": user["userid"]})]


    lst = []

    #courses
    for crs in db.courses.find({"ders_kodu": {"$in": courselist},
                                "$or": [{"ders_kodu": re.compile(inp, re.I)},
                                        {"ders_adi": re.compile(inp, re.I)}]}):
        lst.append({"id": {"id": ["ders", str(crs["ders_kodu"])], "name": crs["ders_adi"]},
                    "name": "ders" + ":" + crs["ders_adi"]})

    #lectures
    for lect in db.lectures.find({"course": {"$in": courselist},
                                    "$or": [{"course": re.compile(inp, re.I)},
                                        {"description": re.compile(inp, re.I)}]}):
        lst.append({"id": {"id": ["oturum", lect["course"] + "*!*!" + lect["session_no"]], "name": lect["description"]},
                    "name": "oturum" + ":" + lect["description"]})

    #titles
    for title in db.titles.find({"course": {"$in": courselist},
                                    "$or": [{"course": re.compile(inp, re.I)},
                                            {"title": re.compile(inp, re.I)}]}):
        lst.append({"id": {"id": ["başlık", title["course"] + "*!*!" + title["title"]], "name": title["title"]},
                    "name": "başlık" + ":" + title["course"] + " " + title["title"]})

    return lst


def object_name(otype, oid):
    db = client.netkent_lectures
    if otype == "ders":
        doc = db.courses.find_one({"ders_kodu": oid})
        if doc:
            return doc["ders_adi"]
    elif otype in ["oturum", "başlık"]:
        course = oid.split('*!*!')[0]
        if otype == "oturum":
            doc = db.lectures.find_one({"course": course,
                                        "session_no": oid.split('*!*!')[1]})
            if doc:
                return doc["description"]
        else: # otype == başlık
            return oid.split('*!*!')[1]



"""
def all_users():
    # returns in the form of {"id": id, "name": username}
    db = client.routeX_demo
    
    return [{"id": x["_id"], "name": x["username"], "email": x.get("email", "") } for x in db.users.find()]
"""
def authorized_users(otype, oid):
    db = client.netkent_lectures
    dbn = client.netkent

    auth_users = []
    # admins
    for admin in db.s4s4rights.find({"role": {"$in": ["master", "admin"]}}):
        auth_users.append({"id": admin["userid"], "name": admin["username"], "email": admin.get("email")})

    if otype == "ders":
        course = oid
    elif otype in ["oturum", "başlık"]:
        course = oid.split('*!*!')[0]
    else:
        course = ""

    # lecturers
    for lect in db.s4s4rights.find({"role": "lecturer",
                                "courses": course }):
        auth_users.append({"id": lect["userid"], "name": lect["username"], "email": lect.get("email")})

    # students
    for std in dbn.courselist.find({"ders_kodu": course}):
        ogr = dbn.ogrencilist.find_one({"ogrenci_no": std["ogrenci_no"]})
        if ogr:
            auth_users.append({"id": ogr["ogrenci_no"], "name": ogr["ad"] + " " + ogr["soyad"], "email": ogr["eposta_adresi"]})

    return auth_users