    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 113:40 2022

@author: cem
"""

from flask import Flask, render_template, request, session, redirect, url_for, send_file, abort

# from sampleintfcs import object_list, object_name, authorized_users
from cp_interfaces import object_list, object_name, authorized_users
# from config import session["user"]["username"]# from demopageintfcs import object_list, session["user"]["username"]

from config import MODAL_DISPLAY

from flask_socketio import SocketIO, join_room, leave_room, emit


import json

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'

# from flask_cors import CORS
# cors = CORS(app,resources={r"/*":{"origins":"*"}})


from flask_session import Session  # https://pythonhosted.org/Flask-Session
Session(app)


def rtg_object_id(id):
    return str(id)

# socketio = SocketIO(app)
socketio = SocketIO(app, async_handlers=True, cors_allowed_origins="*")

from bson import ObjectId




from routings import create_rt_thread, add_rt_message, remove_from_unread, add_audience_rtg, del_audience_rtg, get_all_labels, get_threads, get_active_thread, aud_str2ary, make_new_thread, json_dumps, LANG, get_label, get_error_message

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
    

def err_return(e):
    return render_templata('error.html',
                            errormsg=e,
                            gobackmsg=get_label("ClickBack", LANG))



@app.route('/routing_form', methods = ["GET", "POST"])
# main sharesfor route; displays the related objects threads and activethread
def routing_form():
    try:
        if request.method == "GET": # request coming from listed threads
            action = "display routing" #for logging

            # session["user"] comes from the application 
            if not session.get("user") or not session["user"].get("username"):
                abort(401)

            otype = request.args.get("otype")
            oid = str(request.args.get("oid"))
            print("oid: ", oid)

            # thread_id == 0 means new (not yet stored in db) thread
            if request.args.get("thread_id") not in ["0", None]:
                active_thr = get_active_thread(request.args.get("thread_id"))
                # remove user from the unread list since user views this thread 
                remove_from_unread(active_thr["_id"], session["user"])
            else: 
                active_thr = make_new_thread(request.args, session["user"])
            
        else: #POST: request from an application

            # session["user"] comes from the application 
            session.pop("user", None)
            session["user"] = {"userid": request.form.get("userid"),
                               "username": request.form.get("username"),
                               "email": request.form.get("email")}

            otype = request.form.get("otype")
            oid = str(request.form.get("oid"))
            # from an application call the new thread is displayed; 
            # the existing threads are displayed by GET calls
            active_thr = make_new_thread(request.form, session["user"])
        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(active_thr),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)

@app.route('/add_message', methods=["POST"])
def add_message():
# add a new message to the thread        

    try:
        otype = request.form["otype"]
        oid = request.form["oid"]

        if request.form["thread_id"] == "0":  # create new thread
            thread = make_new_thread(request.form, session["user"])
            action = "route object" # for logging purpose

            thr_params = create_rt_thread(request.form["otype"], 
                                          rtg_object_id(request.form["oid"]),
                                          thread,
                                          request.form["message"],
                                          request.files
                                          )
        
        else:
            action = "add message"
            thread = get_active_thread(request.form["thread_id"])
            thr_params = add_rt_message(thr_params, 
                                        session["user"]["username"], 
                                          request.form["message"],
                                          request.files,
                                          "sharesfor")
                                        # signed_msg)
            socketio.emit("refresh", to=str(thr_params["_id"]))

        if thr_params.get("exc_ID"):
            return render_templata('error.html',
                                    errormsg=get_error_message(thr_params["exc_ID"], LANG),
                                    gobackmsg=get_label("ClickBack", LANG))

        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(get_active_thread(thr_params["_id"])),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)

    
    
 

""" audience format as on the DB
    [{"id": <user_id>, "name": <user_name}]
"""


@app.route('/add_audience', methods = [ "POST"])
def add_audience():
# add an authorized user to the audience

    try:    
        if request.form["thread_id"] == "0": 
            activethr = make_new_thread(request.form, session["user"])
        else:
           activethr = get_active_thread(request.form["thread_id"])
           
        otype = request.form["otype"]
        oid = request.form["oid"]

        # the user to be added comes in concatenated id||name||email form
        aud = request.form["slct-aud"].split("||")
        aud = {"id": aud[0], "name": aud[1], "email": aud[2]}


        thread = add_audience_rtg(activethr, aud)   
        if thread.get("exc_ID"):
            return render_templata('error.html',
                                    errormsg=get_error_message(thread["exc_ID"], LANG),
                                    gobackmsg=get_label("ClickBack", LANG))


        activethr["authorized_users"] = authorized_users(otype, oid)

        # audlist contains only names (to display)
        # audience is a list of dicts {id, name} 
        activethr["audlist"] = [x["name"] for x in thread["audience"]] 
        # activethr["audience"] = json.dumps(thread["audience"])
        activethr["audience"] = thread["audience"] # using |tojson filter in the template

        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(activethr),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)


@app.route('/del_audience', methods = [ "POST"])
def del_audience():
    # delete the selected user from the audience
    try:
        thread_id = request.form["thread_id"]
        otype = request.form["otype"]
        oid = request.form["oid"]
        aud = request.form["slct-del-aud"]
        if thread_id == "0":
            activethr = make_new_thread(request.form, session["user"])
        else:
            activethr = get_active_thread(thread_id)

        thread = del_audience_rtg(activethr, aud)   
        if thread.get("exc_ID"):
            return render_templata('error.html',
                                    errormsg=get_error_message(thread["exc_ID"], LANG),
                                    gobackmsg=get_label("ClickBack", LANG))

        activethr["authorized_users"] = authorized_users(otype, oid)
        activethr["audlist"] = [x["name"] for x in thread["audience"]] 
        # activethr["audience"] = json.dumps(thread["audience"])
        activethr["audience"] = thread["audience"] # using |tojson filter in the template

        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(activethr),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)
    

""" tag format as on DB

    [{"id": [<object_type>, <object_id>],
      "name": <object_name>}]
"""

from routings import add_tag_rtg, del_tag_rtg
@app.route('/add_tag', methods = [ "POST"])
def add_tag():
# add the selected tag to the thread

    try:
        oid = request.form["oid"]
        
        if request.form["thread_id"] == "0":
            activethr = make_new_thread(request.form, session["user"])
        else:
            activethr = get_active_thread(request.form["thread_id"])


        activethr = add_tag_rtg(activethr, request.form["obj_id"])

        if activethr.get("exc_ID"):
            return render_templata('error.html',
                                    errormsg=get_error_message(activethr["exc_ID"], LANG),
                                    gobackmsg=get_label("ClickBack", LANG))

        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(activethr),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)


@app.route('/del_tag', methods = [ "POST"])
def del_tag():
#remove a tag from the tagslist

    try:
        otype = request.form["otype"]
        oid = request.form["oid"]
        otype = request.form["otype"]
        oid = request.form["oid"]
        
        if request.form["thread_id"] == "0":
            activethr = make_new_thread(request.form, session["user"])
        else:
            activethr = get_active_thread(request.form["thread_id"])

        activethr = del_tag_rtg(activethr, request.form["slct-del-tag"])
        if activethr.get("exc_ID"):
            return render_templata('error.html',
                                    errormsg=get_error_message(activethr["exc_ID"], LANG),
                                    gobackmsg=get_label("ClickBack", LANG))



        return render_template('s4s4.html', 
                               obj={"type": otype,
                                    "oid": oid,
                                    "name": object_name(otype, oid)},
                               threads=get_threads(otype, oid),
                               activethr=json_dumps(activethr),
                               labels=get_all_labels(LANG))
    except Exception as e:
        return error_return(e)

    

@app.route('/obj_list', methods=["POST"])
def obj_list():
# returns a list of objects in JSON format
# {id: {id: [otype, oid], 
#       name: obj_name},
#  name: display_name}


#    from sampleintfcs import object_list
#    from routings import object_list_html
#    return object_list_html(request.form.get("name"))
    return json.dumps(object_list(request.form.get("name"), session["user"]))


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

""" for development tests

@app.route('/error_test', methods=["GET"])
def test_error():
    return render_template("error.html", 
                            errormsg="Bu hatayı görmezden gelemezsiniz",
                            gobackmsg="Önceki sayfaya dönmek için tıklayınız")


@app.route('/json_test', methods=['GET', 'POST'])
def json_test():
    if request.method == "GET":
        yason = [{"id": 123, "name": "elefan"},
                 {"id": 232, "name": "meto"}]
    else:
        yason = json.loads(request.form["yason"])
        print(yason)
    return render_template("jsontest.html", yason=json.dumps(yason))

"""

if __name__ == '__main__':
    # app.run(debug = True, host = "0.0.0.0", port=5010)
    socketio.run(app, debug = True, host = "0.0.0.0", port=5010)   
