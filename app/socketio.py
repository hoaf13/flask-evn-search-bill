from flask_socketio import SocketIO, send, emit, join_room, leave_room, close_room, rooms, disconnect
from flask import request
from app import app 
import requests
import json
from app.models import Message
from app import db
import time

socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('client-start-chat')
def handle_start_chat(sender_id):

    Message.query.delete()
    db.session.commit()
    response = "Xin chào anh chị {}, đây là tổng đài tra cứu tiền điện. Xin hỏi quý khách thuộc tỉnh thành nào vậy?".format(sender_id)
    Message.query.delete()
    message = Message(sender_id=sender_id, intent='', action='action_start', bot_message=response)
    db.session.add(message)
    db.session.commit()
    print("{} create action start!!!\n".format(sender_id))
    emit("server-start-chat", response, broadcast=False)



@socketio.on('client-send-msg')
def handle_client_send_msg(msg):
    message = msg['message']
    sender_id = msg['sender_id']
    print("socketio: client-send-msg: {} - sender: {}".format(message, sender_id))
    url = request.url_root + 'api/messages/'
    myobj = {
        "sender_id": sender_id,
        "message": message
    }
    headers = {'content-type': 'application/json'}
    x = requests.post(url, data = json.dumps(myobj), headers=headers)
    response = json.loads(x.text)
    print("response api: {}".format(response))
    emit("server-send-msg", response['bot_message'], broadcast=False)
    if response['action'] == 'action_search':
        message = list(Message.query.all())[-1]
        entities = message.entities
        flag = message.action
        url = request.url_root + 'api/searchs/'
        myobj = {
            "entities": entities,
            "flag": flag
        }
        headers = {'content-type': 'application/json'}
        x = requests.post(url, data = json.dumps(myobj), headers=headers)
        response = json.loads(x.text)
        print("response api: {}".format(response))  
        time.sleep(1)  
        emit("server-send-msg",response['bot_message'], broadcast=False)
