    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 113:40 2022

@author: cem
"""

from flask import Flask, render_template, request, session, redirect, url_for, send_file, abort

from sampleintfcs import object_list
# from config import session["user"]["username"]# from demopageintfcs import object_list, session["user"]["username"]

from config import MODAL_DISPLAY

from flask_socketio import SocketIO, join_room, leave_room, emit


app = Flask(__name__)
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'

# from flask_cors import CORS
# cors = CORS(app,resources={r"/*":{"origins":"*"}})


from flask_session import Session  # https://pythonhosted.org/Flask-Session
Session(app)


def rtg_object_id(id):
    return int(id)

# socketio = SocketIO(app)
socketio = SocketIO(app, async_handlers=True, cors_allowed_origins="*")

from bson import ObjectId




from routings import display_routing, create_rt_thread, add_rt_message, rtg_list, remove_from_unread, add_audience_rtg, del_audience_rtg

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    print("Joined room:", room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    print("Left room:", room)
    



@app.route('/routing_form', methods = ["GET", "POST"])
def routing_form():


    thr_list = True #show threadlist on the left unless called from focusModal
    if request.method == "GET":
        
        
        action = "display routing"
        print(request.args)

        if not session.get("user") or not session["user"].get("username"):
            abort(401)

        otype = request.args.get("otype")
        oid = request.args.get("oid")
        if request.args.get("thread_id") not in ["0", None]:
            thr_params = {"thread_id": ObjectId(request.args.get("thread_id"))}
            remove_from_unread(thr_params["thread_id"], session["user"]["username"])
        else: 
            thr_params = {"thread_id": "0"}
        
        # GET calls are  only self requested, therefore session parameter should be set
        thr_params["user"] = session["user"]["username"]
        
        if request.args.get("audience"):
            thr_params["audience"] = request.args.get("audience").replace("[","").replace("]","").replace("'", "").split(",") # convert string of emails to array
        else:
            print("r.g.a: ", request.args.get("audience"))
            thr_params["audience"] = []
        # thread["user"] =  session["user"]["username"]
        if request.args.get("activeonly"):
            thr_list = False

    else: #POST: request from an application
        session.pop("user", None)
        session["user"] = {"username": request.form.get("username"),
                               "email": request.form.get("email")}
        thr_params = {"thread_id": "0",
                      "user": session["user"]["username"]}
        otype = request.form.get("otype")
        oid = request.form.get("oid")
        if request.form.get("audience"): # for requests to a specific audience - like admin, etc.
            thr_params["audience"] = request.form.get("audience").replace("[","").replace("]","").replace("'", "").split(",") # convert string of emails to array
        else:
            thr_params["audience"] = []

    print(thr_params)    
    rtg = display_routing(otype, rtg_object_id(oid), thr_params, thr_list)

    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])

        
@app.route('/add_message', methods=["POST"])
def add_message():
        
    #create routing thread or add message
    
    thr_list = True
    if request.form.get("activeonly"):
        thr_list = False
    
    print("request.files: ", list(request.files))
    if "file" in request.files: 
        print(request.files["file"].filename)
    print("request.form: ", list(request.form))
    
    if request.form["thread_id"] != "0":
        thr_params = {"thread_id": ObjectId(request.form["thread_id"]),
                      "user": session["user"]["username"]}
    else:
        thr_params = {"thread_id": "0",
                      "user": session["user"]["username"]}
        
    otype = request.form["otype"]
    oid = request.form["oid"]
    # signed_msg = MSG_SIGN + request.form["message"] 

    if thr_params["thread_id"] == "0":  # create new thread
        thr_params["audience"] = request.form["audience"]
        thr_params["tags"] = request.form["tags"]
        # aud = request.form["audience"].replace("[","").replace("]","").replace("'", "").split(",") # convert str - list
        action = "route object"
        print(request.files)
        thr_params = create_rt_thread(request.form["otype"], 
                                      rtg_object_id(request.form["oid"]),
                                      thr_params,
                                      request.form["message"],
                                      request.files
                                      )
    
    else:
        action = "add message"
        thr_params = add_rt_message(thr_params, 
                                    session["user"]["username"], 
                                      request.form["message"],
                                      request.files,
                                      "akvaryum")
                                    # signed_msg)
        socketio.emit("refresh", to=str(thr_params["thread_id"]))

    rtg = display_routing(otype, rtg_object_id(oid), thr_params, thr_list)
    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])

    
    
@app.route('/add_audience', methods = [ "POST"])
def add_audience():
    
    thr_list = True
    if request.form.get("activeonly"):
        thr_list = False
    
    
    thr_params = {"thread_id": request.form["thread_id"],
                  "user": session["user"]["username"]}
    
    if thr_params ["thread_id"] == "0": 
        thr_params["audience"] = request.form["audience"]
        thr_params["tags"] = request.form["tags"]
    otype = request.form["otype"]
    oid = request.form["oid"]
    aud = request.form["slct-aud"]
    # dbli = client.linkedin
    # if aud in dbli.cclists.distinct("BU"):
    #     new_aud = []
    #     for prs in dbli.cclists.find({"forBU": False,
    #                                   "BU": aud,
    #                                   "inactive": {"$ne": True}
    #                                   }):
    #         new_aud.append(prs["email"])
    # else:
    #     new_aud = [aud]
        
        
    # if thread_id == "0":  #new thread
    #     old_aud = request.form["audience"].replace("[","").replace("]","").replace("'", "").split(",") # convert str - list

    #     for n in new_aud:
    #         if n not in old_aud:
    #             old_aud.append(n)
    #         else:
    #             pass
    #             # return error

    #     thread = {"thread_id": "0",
    #               "audience": old_aud,
    #               "user": session["user"]["preferred_username"]}
                  
    # else:

    #     db = client.akvaryum
    #     # if db.routings.find_one({"_id": ObjectId(thread_id),
    #     #                          "audience": new_aud}):
    #     #     pass 
    #     # # return error
    #     doc = db.routings.find_one({"_id": ObjectId(thread_id)})
    #     if doc: 
    #         old_aud = doc.get("audience")
    #         old_unread = doc.get("unread")
    #         if not old_unread:
    #             old_unread = []
    #     else: 
    #         old_aud = []            
    #         old_unread = []
    #         # should actually return error
            
    #     for n in new_aud:
    #         if n not in old_aud:
    #             old_aud.append(n)
    #         if n not in old_unread:
    #             old_unread.append(n)

    #     db.routings.update_one({"_id": ObjectId(thread_id)},
    #                             {"$set": {"audience": old_aud, "unread": old_unread}})

    #     thread = {"thread_id": ObjectId(thread_id),
    #               "user": session["user"]["preferred_username"]}

    thread = add_audience_rtg(thr_params, aud)   


    rtg = display_routing(otype, rtg_object_id(oid), thread, thr_list)
    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])


@app.route('/del_audience', methods = [ "POST"])
def del_audience():

    thr_list = True
    if request.form.get("activeonly"):
        thr_list = False

    thread_id = request.form["thread_id"]
    otype = request.form["otype"]
    oid = request.form["oid"]
    aud = request.form["slct-del-aud"]
    # dbli = client.linkedin
    # if aud in dbli.cclists.distinct("BU"):
    #     new_aud = []
    #     for prs in dbli.cclists.find({"forBU": False,
    #                                   "BU": aud,
    #                                   "inactive": {"$ne": True}
    #                                   }):
    #         new_aud.append(prs["email"])
    # else:
    #     new_aud = [aud]
        
        
    # if thread_id == "0":  #new thread
    #     old_aud = request.form["audience"].replace("[","").replace("]","").replace("'", "").split(",") # convert str - list

    #     for n in new_aud:
    #         if n not in old_aud:
    #             old_aud.append(n)
    #         else:
    #             pass
    #             # return error

    #     thread = {"thread_id": "0",
    #               "audience": old_aud,
    #               "user": session["user"]["preferred_username"]}
                  
    # else:

    # db = client.akvaryum
    #     # if db.routings.find_one({"_id": ObjectId(thread_id),
    #     #                          "audience": new_aud}):
    #     #     pass 
    #     # # return error
    #     doc = db.routings.find_one({"_id": ObjectId(thread_id)})
    #     if doc: 
    #         old_aud = doc.get("audience")
    #         old_unread = doc.get("unread")
    #         if not old_unread:
    #             old_unread = []
    #     else: 
    #         old_aud = []            
    #         old_unread = []
    #         # should actually return error
            
    #     for n in new_aud:
    #         if n not in old_aud:
    #             old_aud.append(n)
    #         if n not in old_unread:
    #             old_unread.append(n)



    # db.routings.update_one({"_id": ObjectId(thread_id)},
    #                        {"$pull": {"audience": aud, "unread": aud}})
    thr_params = {"thread_id": ObjectId(thread_id),
                  "user": session["user"]["username"]}
    thr_params = del_audience_rtg(thr_params, aud)

    rtg = display_routing(otype, rtg_object_id(oid), thr_params, thr_list)
    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])



from routings import add_tag_rtg, del_tag_rtg
@app.route('/add_tag', methods = [ "POST"])
def add_tag():
    thr_list = True
    if request.form.get("activeonly"):
        thr_list = False


    thr_params = {"thread_id": request.form["thread_id"]}
    thr_params["user"] = session["user"]["username"]
    
    if thr_params["thread_id"] == "0":
        thr_params["audience"] = request.form["audience"]
        thr_params["tags"] = request.form["tags"]
    otype = request.form["otype"]
    oid = request.form["oid"]
    thr_params = add_tag_rtg(thr_params, request.form["tagid"])
    rtg = display_routing(otype, rtg_object_id(oid), thr_params, thr_list)
    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])


@app.route('/del_tag', methods = [ "POST"])
def del_tag():
    thr_list = True
    if request.form.get("activeonly"):
        thr_list = False
        print("Activeonly received")

    
    thr_params = {"thread_id": request.form["thread_id"]}
    thr_params["user"] = session["user"]["username"]
    
    if thr_params["thread_id"] == "0":
        thr_params["audience"] = request.form["audience"]
        thr_params["tags"] = request.form["tags"]        
    otype = request.form["otype"]
    oid = request.form["oid"]
    thr_params = del_tag_rtg(thr_params, request.form["slct-del-tag"])
    rtg = display_routing(otype, rtg_object_id(oid), thr_params, thr_list)
    if MODAL_DISPLAY or not thr_list:
        return rtg # for modal type display
    else:
        return render_template('routing_form.html', objroutings=rtg, otype=otype, oid=oid) #, thread_id=thread["thread_id"])

    

@app.route('/obj_list', methods=["POST"])
def obj_list():
    from routings import object_list_html
    return object_list_html(request.form.get("name"))


from routings import file_response
@app.route('/download_file', methods= ["GET"])
def download_file():
    obj_id = request.args.get("file_id")
    file_name = request.args.get("file_name")
    return file_response(obj_id, file_name )

@app.context_processor
def xlated_msg():
    from routings import xlate_msg, LANG
    return xlate_msg(None, LANG)

@app.context_processor
def inject_skin():
    from config import STYLE_SHEET
    return {"style_sheet": STYLE_SHEET}


if __name__ == '__main__':
    # app.run(debug = True, host = "0.0.0.0", port=5010)
    socketio.run(app, debug = True, host = "0.0.0.0", port=5010)   
