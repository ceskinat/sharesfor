#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 07:08:59 2022

@author: cem
"""

# import json
# f = open('config.json')
# configurations = json.load(f)

from sampleintfcs import object_name, all_users, authorized_users
from config import LANG, MONGO_CONN_STRING, EMAIL_SENDER_ACC, EMAIL_SENDER_PWD, EMAIL_INTEGRATED, MODAL_DISPLAY, S4S4_BASE

from datetime import datetime

from pymongo import MongoClient
client = MongoClient(MONGO_CONN_STRING)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import json

def display_exception(exc_ID, lang):
    db = client.routeX
    
    body = "<div class='exc-display'>"    
    
    doc = db.exceptions.find_one({"exc_ID": exc_ID,
                                  "lang": lang})
    if not doc: #exception undefined
        doc = db.exceptions.find_one({"exc_ID": "EnD",
                                          "lang": lang})
    if not doc: 
        doc = {"mesage": "Exceptions not Properly Defined"}
    
    body += doc["message"]
    body += "</div>"
    
    return body

""" multilang section """
LABELS_MSGS = {} # read once from database; then serve from memory
def xlate_msg(msg_id, lang):
    if not LABELS_MSGS:
        db = client.routeX
        for lbl in db.labels.find():
            LABELS_MSGS[lbl["label"]] = lbl["output"]

    if msg_id is None: # this part returns all messages for xlated_msgs() decorator in app.py; for labels in jinja templates
        return {x: LABELS_MSGS[x][LANG] for x in list(LABELS_MSGS)}

    return LABELS_MSGS.get(msg_id).get(lang)

def get_all_labels(lang):
    db = client.routeX
    return {x["label"]: x["output"][lang] for x in db.labels.find()}

    
def get_threads(otype, oid):
    db = client.routeX
    threads = []
    for rtg in db.routings.find({"obj_type": otype,
                                 "obj_id": oid}):
        # lists added for simpler display
        rtg["tagslist"] = [x["name"] for x in rtg["tags"]]
        rtg["audlist"] = [x["name"] for x in rtg["audience"]]
        threads.append(rtg)
    return threads

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
    print(activethr)
    return activethr    

def json_dumps(thread):
    # json.dumps audience and tag fields for proper json exchange
    thread["audary"] = thread["audience"]
    thread["tagary"] = [{"tag": x, "tagidstr": json.dumps(x)} for x in thread["tags"]]
    thread["audience"] = json.dumps(thread["audience"])
    thread["tags"] = json.dumps(thread["tags"])
    return thread


def get_active_thread(thread_id):
    db = client.routeX
    thread = db.routings.find_one({"_id": ObjectId(thread_id)})
    
    # lists added for simpler display
    thread["tagslist"] = [x["name"] for x in thread["tags"]]
    thread["audlist"] = [x["name"] for x in thread["audience"]]
    
    # thread["authorized_users"] = [x["username"] for x in all_users()]
    thread["authorized_users"] = authorized_users(thread["obj_type"], thread["obj_id"])
    return thread

""" display_routing and related functions """

def display_obj_summary(otype, oid):
    summary = ""
    name = object_name(otype, oid)
    if not name:
        # return "Özne bulunamadı"
        return xlate_msg("ObjNotFound", LANG)
    if otype == "contact":
        # title = "İrtibat Kişisi: "
        title = xlate_msg("ContactTitle", LANG)

    elif otype == "account":
        # title = "Firma/Kurum: "
        title = xlate_msg("AccTitle", LANG)
    # elif: otype == "opportunity":
    # elif: otype == "news":
    # elif: otype == "post":
    else:
        title = otype + ": "
        
    summary = "<h4>" +  title + name + "</h4>"

    return summary


def aud_list(aud):
    # abbreviated audience list
    lst = [x.split("@")[0].split(".")[0] for x in aud]
    return "[" + ", ".join(lst) + "]"



def display_routing(otype, oid, thread, thr_list):
    
    # thread is a  dictionary containing thread_id, user, audience and tags if new thread;
    # only thread_id and user is enopugh if existing thread
    # thr_list is a boolean denoting if the thread list on the left is displayed or only active thread is returned


    def tag_section(tags):


        def tag_add_section():
            body = "<div class='m-2'>"
            body += '<form id="tag-add" action="' + S4S4_BASE + '/add_tag" method="POST">'
            body += hidden_inputs()            
            # body += "<div class='input-group'>"
            body += "<div class='input-group-append'>"
            body += '<input type="text" id="tagname" name="tagname" onkeyup="filterFunct(' +"'obj-list'" + "," + "'tagname'" + ')" placeholder="' + xlate_msg("AddTagPlc", LANG) + '" autocomplete="off"/>'
            body += '<input type="hidden" id="tagid" name="tagid" />'

            body += "<input type='submit' id='tag-submit' form='tag-add' class='btn-aksiyon' value='" + xlate_msg("AddTag", LANG) + "'>"
            body += "</div>"
            body += '<div id= "obj-list" class="obj-list">' 
            body += '</div>'
            # body += "<input type='submit' form='aud-add' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='Alıcılara Ekle'/>"
            # body += "<input type='submit' form='aud-add' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='" + xlate_msg("AddRcpt", LANG) + "'/>"
            body += "</form>"
            body += "</div>"
            return body


        def tag_del_section():
            body = "<div class='m-2'>"
            body += '<form id="tag-del" action="' + S4S4_BASE + '/del_tag" method="POST">'
            body += hidden_inputs()            
            body += "<div class='input-group-append'>"
            body += "<select name='slct-del-tag' id='slct-del-tag' class='form-control text-sm'>"
            # tags_json = json.loads(tags)
            for tg in tags:
                if tg["id"] != [otype, oid]:
                    # body += "<option value=" + person["email"] + ">" + person["email"] + "</option>"
                    body += "<option value='" + json.dumps(tg) + "'>" + tg["name"] + "</option>"
            body += "</select>"
            # body += "<div class='input-group-append'>"
            body += "<input type='submit' form='tag-del' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='" + xlate_msg("RmTag", LANG) + "'/>"
            body += "</div>"
            body += "</form>"
            body += "</div>"
            return body




        """ main part for tag_section """
        body = "<div class='tag-display aud-selector p1 pl-3'>"
        body += "<form id='tag-add' action='" + S4S4_BASE + "/add_tag' method= 'POST'>"
        
        body += "<div class='row'>"
        body += "<div class='col-xl-2'>"
        body += "<h6>" + xlate_msg("TagsTitle", LANG) +  "</h6></div>" 

        body += "<div class='col-xl-10'>"
        str_tags = ", ".join([x["name"] for x in tags])
        # body += '<div><textarea readonly style="font-size:small;" name="tags-display" class="form-control bg-light" >' + str_tags + '</textarea></div>'
        body += '<div class="tags-list">' + str_tags + '</div>'
        body += '</div></div>'

        body += "<a id='toggle-tag-slct' class='akv-link text-sm' onclick='displaySlcts_tags()'>" + xlate_msg("ToggleAddRmTags", LANG) + "</a>"
        body += "<div id='tag-selectors' style='display:none; border:1px groove;'>"
        body += tag_add_section()
        body += tag_del_section()            
        body += "</div>"

        
        body += "</form>"
        body += "</div>"
 
        return body





    def aud_selector(audience):
        # selector for users/BU's; can be accessed from other modules
        
        # dbli =client.linkedin
        # from portalcommon import all_users
                
        def aud_add():
            body = "<div class='m-2'>"
            body += '<form id="aud-add" action="' + S4S4_BASE + '/add_audience" method="POST">'
            body += hidden_inputs()            
            body += "<div class='input-group'>"
            body += "<select name='slct-aud' id='slct-aud' class='form-control text-sm'>"
            body += "<optgroup label='Kişiler'>"
            # for person in dbli.cclists.find({"forBU": False,
            #                                  "inactive": {"$ne":True}}):
            users = [x["username"] for x in all_users()]
            users.sort()
            for person in users:
                # body += "<option value=" + person["email"] + ">" + person["email"] + "</option>"
                body += "<option value=" + person + ">" + person + "</option>"
            
            # skip BU's unti later
            # body += "</optgroup>"
            # body += "<optgroup label='İş Birimleri'>"            
            # for unit in dbli.cclists.find({"forBU": True}):
            #     body += "<option value=" + unit["BU"] + ">" + unit["BU"] + "</option>"
            # body += "</optgroup>"
            body += "</select>"
            # body += "<div class='input-group-append'>"
            # body += "<input type='submit' form='aud-add' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='Alıcılara Ekle'/>"
            body += "<input type='submit' form='aud-add' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='" + xlate_msg("AddRcpt", LANG) + "'/>"
            body += "</div>"
            body += "</form>"
            body += "</div>"
            return body


        def aud_del():
            body = "<div class='m-2'>"
            body += '<form id="aud-del" action="' + S4S4_BASE + '/del_audience" method="POST">'
            body += hidden_inputs()            
            body += "<div class='input-group'>"
            body += "<select name='slct-del-aud' id='slct-del-aud' class='form-control text-sm'>"
            for person in audience:
                # body += "<option value=" + person["email"] + ">" + person["email"] + "</option>"
                body += "<option value=" + person + ">" + person + "</option>"
            body += "</select>"
            # body += "<div class='input-group-append'>"
            # body += "<input type='submit' form='aud-del' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='Kişiyi Çıkar'/>"
            body += "<input type='submit' form='aud-del' class='btn btn-aksiyon form-control btn-sm btn-aud-add' value='" + xlate_msg("RmRcpt", LANG) + "'/>"
            body += "</div>"
            body += "</form>"
            body += "</div>"
            return body
        
        
        
        """ main part for aud_selector """
        # body = "<div class='input-group m-2 audience-selector'>"
        body = "<div class='aud-selector p-1 pl-3'>" 
        # body += "<h6>Alıcılar:</h6>"
        # body += "<div class='p-0 mb-3 border border-light'>"
        body += "<div class='row'>"
        body += "<div class='col-xl-2'>"
        body += "<h6>" + xlate_msg("RcptsTitle", LANG) +  "</h6></div>"
        # body += "<div class='row p-0 mb-3 border border-light'>"
        # body += "<div class='col-xl-6'>"
        # body += '<div><textarea readonly style="font-size:small;" name="audience" class="form-control bg-light" >' + ", ".join(audience) + '</textarea></div>'
        body += '<div class="col-xl-10">'
        body += '<div class="tags-list">' + ", ".join(audience) + '</div></div>'
        # body += "<div class='col-xl-1 align-middle text-center'><h4><input type='submit' form='aud-add' class='btn-aksiyon form-control' value='İlgililere Ekle'/></h4></div>"  
        # body += "<div class='col-xl-2 p-1'>"
        # body += "<input type='submit' form='aud-add' class='btn-aksiyon form-control btn-sm' value='<- Alıcılara Ekle'/>"
        # body += "</div>"
        # body += "<div class='col-xl-3 p-1'>"
        # body += "<a id='toggle-aud-slct' class='akv-link text-sm' onclick='displaySlcts()'>Kişi Ekle/Çıkar</a>"
        body += "</div>"
        body += "<a id='toggle-aud-slct' class='akv-link text-sm' onclick='displaySlcts()'>" + xlate_msg("ToggleAddRmRcpt", LANG) + "</a>"
        body += "<div id='aud-selectors' style='display:none; border:1px groove;'>"
        body += aud_add()
        if thread["thread_id"] != "0":
            body += aud_del()
            # do not allow deleting if thread is not yet recorded
        body += "</div>"
        # body += "</div>"
        body += "</div>"
        
        return body    


    def hidden_inputs():
        # hidden inputs holding the thread parameters for all forms
        body = "<input type='hidden' name='otype' value='" + otype + "'>"
        body += "<input type='hidden' name='oid'  value='" + str(oid) + "'>"
        # tags are added below
        
        body += "<input type='hidden' name='thread_id'  value='" + str(thread["thread_id"]) + "'>"
        if thread["thread_id"] == "0":
            body += "<input type='hidden' name='audience'  value=" + ",".join(thread["audience"]) + ">"
            body += "<input type='hidden' name='tags'  value='" + json.dumps(thread["tags"]) + "'>"
        return body
    
    


    def display_active_thread(msgs):

        body = "<div class='magnifier'>"
        body += "<h4 onclick='showOnModal()'  title='" + xlate_msg("ZoomTitle", LANG) + "'>+</h4></div>"
        body += "<div class='active-thread'>"


        print("thr-aud: ", thread["audience"])
        body += aud_selector(thread["audience"])

        body += tag_section(thread["tags"])
        
        body += "<div class='messages-area p-2'>"
        # body += "<h6>İletiler/Notlar:</h6>"
        body += "<h6>" + xlate_msg("MsgsTitle", LANG) + "</h6>"
        # body += "</form>"
        if msgs:
            for msg in msgs:
                # body += "<div class='row mt-2'>"
                # body += "<div class='col-xl-3 text-sm'><b>" + msg["user"].split("@")[0].split(".")[0] + "</b>"
                # body += " - " + msg["time"].strftime("%d/%m/%y-%H:%M") + "</div>"
                # body += "<div class='col-xl-7 bg-msg'>" + msg["message"].replace("\n","<br>") + "</div>"
          
                # body += "<div class='col-xl-3 text-sm'><b>" + msg["user"].split("@")[0].split(".")[0] + "</b>"
                # body += " - " + msg["time"].strftime("%d/%m/%y-%H:%M") + "</div>"
                body += "<div class='row'>"
                body += "<div class='col-xl-8 bg-msg m-2'>" 
                body += "<div class='text-sm'><b>" + msg["user"].split("@")[0].split(".")[0] + "</b>"
                body += " - " + msg["time"].strftime("%d/%m/%y-%H:%M") + "</div>"
                body += msg["message"].replace("\n","<br>") + "</div>"
                # body += "</div>" 
        
                # attachment
                if msg.get("file"):
                    # body += "<div class='row'><div class='col-xl-4'></div>"
                    body += "<div class='attachment-display col-xl-4 mb-3'>"
                    body += "<a class='btn' href='/download_file?file_id=" + str(msg["file"].get("gid")) + "&file_name=" + msg["file"].get("fname") + "'>"
                    # attachment sign
                    body += '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-paperclip" viewBox="0 0 16 16">'
                    body += '<path d="M4.5 3a2.5 2.5 0 0 1 5 0v9a1.5 1.5 0 0 1-3 0V5a.5.5 0 0 1 1 0v7a.5.5 0 0 0 1 0V3a1.5 1.5 0 1 0-3 0v9a2.5 2.5 0 0 0 5 0V5a.5.5 0 0 1 1 0v7a3.5 3.5 0 1 1-7 0V3z"/></svg>'

                    body += msg["file"].get("fname") + "</a></div>"
                body += "</div>"  #row
        body += '<form id="message-add" enctype="multipart/form-data" action="' + S4S4_BASE + '/add_message" method="POST"  >'


        body += hidden_inputs()             
        body += "<div class='input-group mt-4 ml-4 col-xl-10'>"
        # body += "<textarea type='textarea' name='message' class='form-control' placeholder='İleti/Not Giriniz' rows='2'></textarea>"
        body += "<textarea type='textarea' name='message' class='form-control' placeholder='" + xlate_msg("EnterMsg", LANG) + "' rows='2'></textarea>"
        # body += "<input type='submit' form='message-add' class='btn-aksiyon' value='Gönder' >"
        body += "<input type='submit' form='message-add' class='btn-aksiyon' value='" + xlate_msg("BtnSend", LANG) + "' >"
        # body += "</div></div></div>"
        

        body += "</div>"

        """ attachment """
        body += "<div class='attach-file mt-1 ml-5'>"
        # body += "<label class='attachent-upload'>"
        body += "<h6>"
        body += '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-paperclip" viewBox="0 0 16 16">'
        body += '<path d="M4.5 3a2.5 2.5 0 0 1 5 0v9a1.5 1.5 0 0 1-3 0V5a.5.5 0 0 1 1 0v7a.5.5 0 0 0 1 0V3a1.5 1.5 0 1 0-3 0v9a2.5 2.5 0 0 0 5 0V5a.5.5 0 0 1 1 0v7a3.5 3.5 0 1 1-7 0V3z"/></svg>'
        body += xlate_msg("AtchLbl", LANG) + "</h6>"
        body += "<input type='file' name='file' >"
        body += "</div>"
        
        
        body += "</form>"
        body += "</div>"


        
        body += "</div>"

        return body         



    """ main part of display_routing """
    
    db = client.routeX
    if thr_list:
        body = display_obj_summary(otype, oid)
    else:
        body = ""
    
    # thread["exc_ID"] = "UndefFlt"
    if thread.get("exc_ID"):
        body += display_exception(thread["exc_ID"], LANG)
        

    if thr_list:
        body += "<div class='row'>"
        body += "<div class='col-xl-4'>"
        # body += "<h5>Yorum / Paylaşımlar:</h5>"
        body += "<h5>" + xlate_msg("RtgsTitle",LANG) +"</h5>"
        body += "<ul class='list-group'>"
        # for thr in db.routings.find({"obj_type": otype,
        #                                 "obj_id": oid}):
        if type(thread["thread_id"]) is str:
            print("********Istıring:", thread["thread_id"], "*********")
        else:
            print("****** Thread_id:", str(thread["thread_id"]), "************")
        for thr in db.routings.find({"tags.id": [otype, oid]}):
            
            unread = False
            if thr["_id"] == thread["thread_id"]:
                thread["audience"] = thr["audience"]
                thread["tags"] = thr["tags"]
                # body += "<li class='list-group-item active-thread'>"
                # body += display_active_thread(thr.get("messages"))
                body += "<li class='list-group-item text-sm'><div class=''>" + aud_list(thr["audience"]) + "-" + thr["messages"][-1]["time"].strftime("%d/%m/%y-%H:%M") + ":"
                body += thr["messages"][0]["message"][:50] + "</div>"
                active_msgs = thr.get("messages")
            else:
                if thr.get("unread") and thread["user"] in thr.get("unread"): 
                    unread = True
    
                if unread:
                    body += "<b>"
    
                if MODAL_DISPLAY:
                    click  = 'showRouting("'  + otype + '","' + str(oid) + '","' + str(thr["_id"]) + '")'
                    body += "<li class='list-group-item text-sm'><div class=''><a class='akv-link' onclick='" + click + "' style='color:SeaGreen;'>" + aud_list(thr["audience"]) + "-" + thr["messages"][-1]["time"].strftime("%d/%m/%y-%H:%M") + ":</a>"
                    body += thr["messages"][0]["message"][:50] + "</div>"  
                else:
                    # link = "/routing_form?otype=" + otype + "&oid=" + str(oid) + "&thread_id=" + str(thr["_id"]) 
                    # link += "&audience=" + str(thr["audience"])  # send array as string, will parse to array when processing
                    link = S4S4_BASE +'/routing_form?otype=' + otype + '&oid=' + str(oid) + '&thread_id=' + str(thr["_id"]) 
                    link += '&audience=[' + ",".join(thr["audience"]) + "]"  # send array as string, will parse to array when processing
                    body += "<li class='list-group-item text-sm'><div class=''><a class='akv-link' href='" + link + "'>" + aud_list(thr["audience"]) + "-" + thr["messages"][-1]["time"].strftime("%d/%m/%y-%H:%M") + ":</a>"
                    body += thr["messages"][0]["message"][:50] + "</div>"  
                    # body += "<div class='pl-2'><a href='" + link + "' style='color:SeaGreen;'>" + str(thr["audience"]) + "</a>"
                
            body += "</li>"
            if unread: 
                body += "</b>"
        body += "</ul>"
        
        if thread["thread_id"] == "0": #if new thread, display at the bottom
            # body += "<li class='list-group-item active-thread'"
            if thread["user"] not in thread["audience"]:
                print(thread["user"], [thread["user"]])
                print("1: ", thread["audience"], type(thread["audience"]))
                print(thread["user"] not in thread["audience"])
                thread["audience"].append(thread["user"])
            if not thread.get("tags"):
                thread["tags"] = [{"id": [otype, oid],
                                  "name": object_name(otype, oid)}]
            print("id: ", thread["thread_id"], "aud:", thread["audience"])
            # body += "<div class='pl-2'><input type='text' name='audience' class='form-control-plaintext' readonly value=" + aud_list(thread["audience"])  + "></div>" #+ "</a>"   thr["router"] + ", " ", ".join(thr["target"])
            # body += "</li>"
            active_msgs = []
    
        elif MODAL_DISPLAY:
            click  = 'showRouting("'  + otype + '","' + str(oid) + '","0")'
            body += "<div><a class='akv-link' href='#' onclick='" + click + "'>" + xlate_msg("NewMsg", LANG) +"</a></div>" 
        else:
            body += "<div><a class='akv-link' href='/routing_form?otype=" + otype + "&oid=" + str(oid) + "&thread_id=0'>" + xlate_msg("NewMsg", LANG) +"</a></div>" 
            # body += "<div><a class='akv-link' href='#' onclick='" + click + "'>Yeni Yorum/Paylaşım</a></div>" 



        body += "</div>" # column
    
        body += "<div class='col-xl-8'>"




    body += display_active_thread(active_msgs)

    if thr_list:
        body += "</div>" # column
        body += "</div>" # row
    
    return body


""" attachment handling """
from gridfs import GridFS
from werkzeug.utils import secure_filename
import os
UPLOADS_FOLDER = "uploads/"

def handle_attachment(rq_files):
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
    db = client.routeX
    # These parts are handled in make_new_thread
    # thr_params["audience"] = aud_str2ary(thr_params["audience"])
    # thr_params["tags"] = json.loads(thr_params["tags"])

    # if thr_params["user"] not in thr_params["audience"]:
    #     print("2: ", thr_params["audience"])
    #     thr_params["audience"].append(thr_params["user"])

    # unread = thr_params["audience"][:] # assign by value
    unread = [x["id"] for x in thr_params["audience"]]
    if thr_params["user"]["userid"] in unread:
        unread.remove(thr_params["user"]["userid"])
   
    
    name = object_name(otype, oid)
    # res = db.routings.insert_one({"obj_type": otype,       
    #                               "obj_id": oid,     
    #                               "obj_name": name,
    #                               "audience": audience,
    #                               "unread": unread,
    #                               "messages": [{"user": user,
    #                                             "message": message,
    #                                             "time": datetime.now()}]})
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

# MSG_SIGN = "&/akvaryum'dan girilen<br>"




def add_rt_message(thr_params, user, message, rq_files, source):
    # add to existing thread

    db = client.routeX
    try: 
        th = db.routings.find_one({"_id": ObjectId(thr_params["_id"])})
        if user not in th["audience"]:
            print("3: ", th["audience"])
            th["audience"].append(user)
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
                    thr_params["exc_ID"] = "AtchFail"
            except:
                thr_params["exc_ID"] = "AtchFail"

        th["messages"].append(msg)
        res = db.routings.update_one({"_id": thr_params["thread_id"]},
                                     {"$set": {"audience": th["audience"],
                                               "unread": unread,
                                               "messages": th["messages"]}})    
        if res.matched_count == 0:
            thr_params["exc_ID"] = "AddMsgFail"
        elif source != "email" and EMAIL_INTEGRATED: # send emails unless the source of message is already email; avoid duplication
            pop_emails(th, message, user)
    except:
        thr_params["exc_ID"] = "AddMsgFail"

    return thr_params
        
        
def remove_from_unread(thread_id, user):
    db = client.routeX
    db.routings.update_one({"_id": thread_id},
                           {"$pull": {"unread": user["userid"]}})


def rtg_list(user):
    db = client.routeX
    body= ""
    if db.routings.count_documents({"audience": user}) == 0:
        body = "Yazışmanız bulunmuyor"
    else:
        for thread in db.routings.aggregate([{"$match": {"audience": user}},
                                              {"$addFields": {"lastm": {"$last": "$messages"}}},
                                              {"$sort": {"lastm.time": -1}}]):    
    
            if MODAL_DISPLAY:
                body += '<div class="rtg-list-item p-2"><a class="rtg-link" href="#"'
                click  = 'showRouting("'  + thread["obj_type"] + '","' + str(thread["obj_id"]) + '","' + str(thread["_id"]) + '")'
                body += " onclick='" + click + "'>" 
            else:
                body += "<div><a class='akv-link' href='/routing_form?otype=" + thread["obj_type"] + "&oid=" + str(thread["obj_id"]) + "&thread_id=" + str(thread["_id"]) + "'>" 

                                                                                                                                                          
                # body += "<div><a class='akv-link' href='#' onclick='" + click + "'>Yeni Yorum/Paylaşım</a></div>" 
    
    
            if thread.get("unread") and user in thread.get("unread"):
                body += "<b>"
            body += "<span class='rtg-list-title'>" +  thread["lastm"]["time"].strftime("%d/%m/%y") + " " + aud_list(thread["audience"]) + "</span>"
            if thread["obj_name"]:
                body += " " + thread["obj_name"] 
            body += ":" + thread["lastm"]["message"][:50]
            if thread.get("unread") and user in thread.get("unread"):
                body += "<b>"
            body += "</a></div>"
       
    return body

from bson import ObjectId

def aud_str2ary(audstr):
    return audstr.replace("[","").replace("]","").replace("'", "").split(",") # convert str - list
       
def add_audience_rtg(thr, aud):
    # dbli = client.linkedin
    # if aud in dbli.cclists.distinct("BU"):
    #     new_aud = []
    #     for prs in dbli.cclists.find({"forBU": False,
    #                                   "BU": aud,
    #                                   "inactive": {"$ne": True}
    #                                   }):
    #         new_aud.append(prs["email"])
    # else:
    # new_aud = [aud]
        
        
    if aud not in thr["audience"]:
        # print("4: ", thr_params["audience"] )
        thr["audience"].append(aud)
    if thr["_id"] != "0":  #new thread

        db = client.routeX
        # if db.routings.find_one({"_id": ObjectId(thread_id),
        #                          "audience": new_aud}):
        #     pass 
        # # return error
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
        # thr_params = {"thread_id": ObjectId(thread_id),
        #           "user": user}
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
            db = client.routeX
            res = db.routings.update_one({"_id": ObjectId(thread["_id"])},
                                         {"$pull": {"audience.id": aud, "unread": aud}})
            if res.matched_count == 0: 
                thread["exc_ID"] = "AudDelFail"
        except:
            thread["exc_ID"] = "AudDelFail"
        
    return thread
    
    
""" add remove tag functions """
def add_tag_rtg(thr_params, added_tagstr):

    # thr_params["tags"] = json.loads(thr_params["tags"])
    thr_params["tags"].append(json.loads(added_tagstr))
    thr_params["tagslist"] = [x["name"] for x in thr_params["tags"]]

    if thr_params["_id"] != "0":

 
        # if type(thr_params["audience"]) == str: # convert the audience parameter as well
        #     thr_params["audience"] = aud_str2ary(thr_params["audience"])
        thr_params["thread_id"] = ObjectId(thr_params["_id"])
        try:
            db = client.routeX
            res = db.routings.update_one({"_id": ObjectId(thr_params["thread_id"])},
                                   {"$push": {"tags": json.loads(added_tagstr)}})        
            if res.matched_count == 0: 
                thr_params["exc_ID"] = "TagAddFail"
        except:
            thr_params["exc_ID"] = "TagAddFail"
            
    return thr_params


def del_tag_rtg(thr_params, del_tagstr):


        # thr_params["tags"] = json.loads(thr_params["tags"])
    thr_params["tags"].remove(json.loads(del_tagstr))
    thr_params["tagslist"] = [x["name"] for x in thr_params["tags"]]

        # if type(thr_params["audience"]) == str: # convert the audience parameter as well
        #     thr_params["audience"] = aud_str2ary(thr_params["audience"])
    if thr_params["_id"] != "0":
        thr_params["thread_id"] = ObjectId(thr_params["_id"])
        try:
            db = client.routeX
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




    
def object_list_html(inp):
    from sampleintfcs import object_list

    body = "<div>"
    # lst = list(db.lgm_accounts.find({"name": re.compile(inp, re.I)}))
    # lst = list(db.lgm_accounts.find({"name": re.compile(inp, re.I)}).collation( {"locale": "en", "strength": 1} ))
    lst = object_list(inp)
    if len(lst) > 10:
        size = 10
    else:
        size = len(lst)
    body += "<select id='slct-obj' onclick='selectTag()' size=" + str(size) + ">"
    for item in lst:
        # body += "<p class='obj-list-item' onclick='selectObj()'>İrtibat:" + item["name"] + "-" + str(item.get("company", "")) 
#        body += "<input class='hidden' id='type' value=" + item["type"]
        # body += "<input type='hidden' id='id' value=" + str(item["_id"]) 
        # body += "<option value=" + str(item["_id"]) + " onclick='selectObj()'>" + item["name"] + "</option>"
        obj_id_str = json.dumps({"id": [item["otype"], item["oid"]], "name": item["oname"]})
        body += "<option value='" + obj_id_str + "'>" + item["otype"] +":" + item["oname"] + "</option>"
        # body += "</p>"
    body += "</select></div>"
    return body

       