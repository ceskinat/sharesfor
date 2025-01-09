#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 07:08:59 2022

@author: cem
"""

# import json
# f = open('config.json')
# configurations = json.load(f)

#from sampleintfcs import object_name, all_users, authorized_users
from interfaces import object_name, authorized_users, object_list
from config import LANG, MONGO_CONN_STRING, EMAIL_SENDER_ACC, EMAIL_SENDER_PWD, EMAIL_INTEGRATED,  S4S4_BASE

from datetime import datetime

from pymongo import MongoClient
client = MongoClient(MONGO_CONN_STRING)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import json

""" authorization """
def authorize_app(client_id, api_key):
    db = client.sharesfor

    doc = db.authorized_apps.find_one({"client_id": client_id})
        
    if (doc and doc.get("api_key") == api_key):
        return {"authorized":True,
                "client_id": client_id,
                "api_urls": doc.get("api_urls", {})
                }
    else:
        return False


""" multilang section """
LABELS_MSGS = {} # read once from database; then serve from memory
def xlate_msg(msg_id, lang):
    if not LABELS_MSGS:
        db = client.sharesfor
        for lbl in db.labels.find():
            LABELS_MSGS[lbl["label"]] = lbl["output"]

    if msg_id is None: # this part returns all messages for xlated_msgs() decorator in app.py; for labels in jinja templates
        return {x: LABELS_MSGS[x][LANG] for x in list(LABELS_MSGS)}

    return LABELS_MSGS.get(msg_id).get(lang)

def get_all_labels(lang):
# read all labels at once
    db = client.sharesfor
    return {x["label"]: x["output"][lang] for x in db.labels.find()}

def get_label(label, lang):
# read a specific label
    db = client.sharesfor
    lbl = db.labels.find_one({"label": label})
    if lbl:
        return lbl["output"].get(lang)

def get_error_message(exc_ID, lang):
# get the exception message in the designated language
    db = client.sharesfor
    msg = db.exceptions.find_one({"exc_ID": exc_ID,
                                  "lang": lang })
    if not msg:  # exception not defined
        msg = db.exceptions.find_one({"exc_ID": "EnD",
                                      "lang": lang })
    return msg

        
def get_threads(otype, oid):
# returns the message threads belonging to a certain object
    db = client.sharesfor
    threads = []
    # for rtg in db.routings.find({"obj_type": otype,
    #                              "obj_id": oid}):
    # return all threads that the object is tagged
    for rtg in db.routings.find({"tags.id": [otype, oid]}):
        # lists added for simpler display
        rtg["tagslist"] = [x["name"] for x in rtg["tags"]]
        rtg["audlist"] = [x["name"] for x in rtg["audience"]]
        threads.append(rtg)
    return threads

def get_user_threads(user):
    db = client.sharesfor
    return db.routings.aggregate([{"$match": {"audience.id": user["userid"]}},
                                      {"$addFields": {"lastm": {"$last": "$messages"}}},
                                      {"$sort": {"lastm.time": -1}}])   


def make_new_thread(rqform, user):
    # creates an active thread object for a new thread (id="0") 
    if not rqform.get("audience"):
        audience = [{"id": user["userid"], "name": user["username"], "email": user["email"]}] # include the user to audience in new threads
    else:
        audience = json.loads(rqform["audience"])

    if not rqform.get("tags"):
        tags = [{"id": [rqform["otype"], rqform["oid"]],
                 "name": object_name(rqform["otype"], rqform["oid"])}]
    else:
        tags = json.loads(rqform["tags"])
        
    
    activethr = {"_id": "0",
                 "new": True,
                 "audience": audience,
                 "audlist": [x["name"] for x in audience],
                 "tags": tags,
                 "tagslist": [x["name"] for x in tags],
                 "authorized_users": authorized_users(rqform["otype"], rqform["oid"]),
                 "user": user
                 }
    # print(activethr)
    return activethr    

def json_dumps(thread):
    # json.dumps audience and tag fields for proper json exchange
    thread["audary"] = thread["audience"]
    thread["tagary"] = [{"tag": x, "tagidstr": json.dumps(x)} for x in thread["tags"]]
    thread["audience"] = json.dumps(thread["audience"])
    thread["tags"] = json.dumps(thread["tags"])
    return thread


def get_active_thread(thread_id):
# retrieves a thread from db and creates fileds required to display the thread 
    db = client.sharesfor
    thread = db.routings.find_one({"_id": ObjectId(thread_id)})
    
    # lists added for simpler display
    thread["tagslist"] = [x["name"] for x in thread["tags"]]
    thread["audlist"] = [x["name"] for x in thread["audience"]]
    
    # thread["authorized_users"] = [x["username"] for x in all_users()]
    thread["authorized_users"] = authorized_users(thread["obj_type"], thread["obj_id"])
    return thread


""" attachment handling """
from gridfs import GridFS
from werkzeug.utils import secure_filename
import os
UPLOADS_FOLDER = "uploads/"

def handle_attachment(rq_files):
# uses gridfs to store the attachment 
    file = rq_files.get("file")
    if not file or not file.filename: # no file selected
        return None
    filename = secure_filename(file.filename)
    print("file: ", filename)
    #save the file temporarily
    file.save(os.path.join(UPLOADS_FOLDER, filename))
    
    fs = GridFS(client.grid)
    with open(os.path.join(UPLOADS_FOLDER, filename), "rb") as f: #option "rb" is for treating the file as binary
        gid = fs.put(f)

    #remove the temporary file
    os.unlink(os.path.join(UPLOADS_FOLDER, filename))

    if gid:
        return {"gid": gid, "fname": filename}
    
from flask import Response
def file_response(file_id, file_name):
# prepares a response as attachment from GridFS filesystem
    fs = GridFS(client.grid)
    f = fs.get(ObjectId(file_id))       
    r = Response(f, direct_passthrough=True, mimetype='application/octet-stream')
    r.headers.set('Content-Disposition', 'attachment', filename=file_name)
    return r


def create_rt_thread(otype, oid, thr_params, message, rq_files):
#creates a new message thread (in DB) and returns the thread id (or exception code)
    db = client.sharesfor
    unread = [x["id"] for x in thr_params["audience"]]
    if thr_params["user"]["userid"] in unread:
        unread.remove(thr_params["user"]["userid"])
   
    
    name = object_name(otype, oid)
    try:
        msg = {"user": thr_params["user"],
                      "message": message,
                      "time": datetime.now()}
        if "file" in rq_files and rq_files["file"].filename:
            try: 
                attach = handle_attachment(rq_files)
                if attach:
                    msg["file"] = attach   
                else:
                    thr_params["exc_ID"] = "AtchFail"
            except:
                thr_params["exc_ID"] = "AtchFail"
                    

        res = db.routings.insert_one({"tags": thr_params["tags"],
                                      "obj_type": otype,       
                                      "obj_id": oid,     
                                      "obj_name": name,
                                      "audience": thr_params["audience"],
                                      "unread": unread,
                                      "messages": [msg]})
            
        if res.acknowledged:
            thr_params["_id"] = res.inserted_id
        else: 
            thr_params["exc_ID"] = "CrThrFail"
    except:
        thr_params["exc_ID"] = "CrThrFail"
        
    
    return thr_params




def add_rt_message(th, user, message, rq_files, source):
    # add to existing thread
    # source can be either sharesfor or email replies

    db = client.sharesfor
    try: 
        # th = db.routings.find_one({"_id": ObjectId(thr_params["_id"])})
        usr = { "id": user["userid"],
                "name": user["username"],
                "email": user["email"]}
        if usr not in th["audience"]:
            print("3: ", th["audience"])
            th["audience"].append(usr)
        unread = [x["id"] for x in th["audience"]]
        if user["userid"] in unread:
            unread.remove(user["userid"])
    
        msg = {"user": user,
                "message": message,
                "source": source,
                "time": datetime.now()}
        
        if "file" in rq_files and rq_files["file"].filename:
            try:
                attach = handle_attachment(rq_files)
                if attach:
                    msg["file"] = attach   
                else:
                    th["exc_ID"] = "AtchFail"
            except:
                th["exc_ID"] = "AtchFail"

        th["messages"].append(msg)
        res = db.routings.update_one({"_id": th["_id"]},
                                     {"$set": {"audience": th["audience"],
                                               "unread": unread,
                                               "messages": th["messages"]}})    
        if res.matched_count == 0:
            th["exc_ID"] = "AddMsgFail"
        elif source != "email" and EMAIL_INTEGRATED: # send emails unless the source of message is already email; avoid duplication
            pop_emails(th, message, user)
    except Exception as e:
        th["exc_ID"] = e

    return th
        
        
def remove_from_unread(thread_id, user):
# remove the useer from unread list
    db = client.sharesfor
    db.routings.update_one({"_id": thread_id},
                           {"$pull": {"unread": user["userid"]}})



from bson import ObjectId

def aud_str2ary(audstr):
# returns a list from a string containing a list
    return audstr.replace("[","").replace("]","").replace("'", "").split(",") # convert str - list
       
def add_audience_rtg(thr, aud):
# add audience to a thread     
# the aud parameter is in {id, name, email} dict format   
        
    if aud not in thr["audience"]:
        thr["audience"].append(aud)
    if thr["_id"] != "0":  #new thread

        db = client.sharesfor
        doc = db.routings.find_one({"_id": thr["_id"]})
        if doc: 
            old_aud = doc.get("audience", [])
            old_unread = doc.get("unread", [])
        else: 
            old_aud = []            
            old_unread = []
            # should actually return error
            
        if aud not in old_aud:
            old_aud.append(aud)
        if aud not in old_unread:
            old_unread.append(aud)
        
        try:
            result = db.routings.update_one({"_id": thr["_id"]},
                                            {"$set": {"audience": old_aud, "unread": old_unread}})
            if result.matched_count == 0:
                thr["exc_ID"] = "AudAddFail"
        except: 
                thr["exc_ID"] = "AudAddFail"
    return thr


def del_audience_rtg(thread, aud):
    """ 
    audience format is: [{id: person_id1, name: person_name1}, ....]
    aud contains the person_id of the person to be deleted
    """
    new_aud = [d for d in thread["audience"] if d["id"] != aud]
    thread["audience"] = new_aud
    thread["audlist"] = [x["name"] for x in new_aud]
    if thread["_id"] != 0:
        try:
            db = client.sharesfor
            res = db.routings.update_one({"_id": ObjectId(thread["_id"])},
                                         {"$pull": {"audience": {"id": aud},
                                                    "unread": {"id": aud}}})
            if res.matched_count == 0: 
                thread["exc_ID"] = "AudDelFail"
        except:
            thread["exc_ID"] = "AudDelFail"
        
    return thread
    
    
""" add remove tag functions """
""" tag format as on DB

    [{"id": [<object_type>, <object_id>],
      "name": <object_name>}]
"""

def add_tag_rtg(thr_params, added_tagstr):
# add a tag (object) to an existing or new (id="0") thread 
    thr_params["tags"].append(json.loads(added_tagstr))
    thr_params["tagslist"] = [x["name"] for x in thr_params["tags"]]

    if thr_params["_id"] != "0":

        thr_params["thread_id"] = ObjectId(thr_params["_id"])
        try:
            db = client.sharesfor
            res = db.routings.update_one({"_id": ObjectId(thr_params["thread_id"])},
                                   {"$push": {"tags": json.loads(added_tagstr)}})        
            if res.matched_count == 0: 
                thr_params["exc_ID"] = "TagAddFail"
        except:
            thr_params["exc_ID"] = "TagAddFail"
            
    return thr_params


def del_tag_rtg(thr_params, del_tagstr):
# delete a tag from a new or existing thread

    thr_params["tags"].remove(json.loads(del_tagstr))
    thr_params["tagslist"] = [x["name"] for x in thr_params["tags"]]

    if thr_params["_id"] != "0":
        thr_params["thread_id"] = ObjectId(thr_params["_id"])
        try:
            db = client.sharesfor
            res = db.routings.update_one({"_id": ObjectId(thr_params["thread_id"])},
                                         {"$pull": {"tags": json.loads(del_tagstr)}})        
            if res.matched_count == 0: 
                thr_params["exc_ID"] = "TagDelFail"
        except:
            thr_params["exc_ID"] = "TagDelFail"

    return thr_params

""" email integration functions """   
    
def send_email(body, subject, toary, ccary):  
    
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER_ACC
    msg['To'] = ",".join(toary)
    msg['Cc'] = ",".join(ccary)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body,'html'))

    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(EMAIL_SENDER_ACC , EMAIL_SENDER_PWD)
    
    
    server.sendmail(EMAIL_SENDER_ACC, toary + ccary, text)
    server.quit()    

def pop_emails(thread, message, user):
    body = user + ": " + message
    subject = "akvaryum paylaşım: "  + thread.get("obj_name") + " &ID:" + str(thread["_id"])
    # toary = thread["audience"]
    toary = ["cem@solusmart.com"]
    
    ccary = ["akvaryum.solusmart.com"]

    send_email(body, subject, toary, ccary)

""" end of email integration functs """





       