import flask
from flask import jsonify, Blueprint, flash, render_template, request, session, abort, \
                  redirect, url_for
import requests
import os
from app import app
from flask.views import MethodView
import random 
from . import graph
from app import db
from app.models import Message
from app.api.utils import find_entities, find_best_intent, find_best_action, gernerate_text,\
    save_to_database, update_entities

api = Blueprint('api', __name__, url_prefix='/api')
endpoint = '/api/messages/'



class MessageAPI(MethodView):
    def get(self):
        response = dict()
        url = flask.request.url_root + endpoint
        response['status_code'] = "200_ok"
        return jsonify(response), 200

    def post(self):
        messages = list(Message.query.all())
        print(messages, end='\n\n')

        sender_id = request.json.get('sender_id')
        message = request.json.get('message')
        print("request: {} - {}".format(sender_id, message))

        entities = find_entities(sender_id, message)
        intent = find_best_intent(sender_id, message, entities)
        entities = update_entities(sender_id, intent, entities)
        action, repeat_count = find_best_action(sender_id, intent, entities)
        text = gernerate_text(sender_id, intent, action, repeat_count, entities)
        instance = save_to_database(sender_id, intent, action, str(entities), message, text)
        
        return jsonify(instance.to_dict())

MessageAPI_view = MessageAPI.as_view('MessageAPI_view')
app.add_url_rule(endpoint, view_func=MessageAPI_view, methods=['GET','POST'])



class EVNSearcher(MethodView):
    def post(self):
        entities = request.json.get('entities')
        flag = request.json.get('flag')
        action = random.choice(['action_have_just_paid','action_not_deadline','action_not_deadline','action_available'])

        if action == 'action_have_just_paid':
            text = "Rất tiếc hiện tại chưa có thông tin tiền điện. Điện lực sẽ kiểm tra và phản hồi lại sau một ngày làm việc."

        if action == 'action_not_deadline':
            text = "Rất tiếc hiện tại vẫn chưa đến ngày phát hành hóa đơn, quý khách vui lòng gọi lại sau."

        if action == 'action_available':
            month = random.randint(1,12)
            year = 2021
            cost = random.randint(100,999) * 1000
            text = 'Em xin thông báo, tiền điện của quý khách trong tháng {} năm {} là {} đồng.'.format(month, year, cost)

        if action == 'supported_forward':
            text = 'Em rất tiếc không tìm thấy thông tin tiền điện của quý khách. Vui lòng chờ giây lát, cuộc gọi đang được chuyển cho điện thoại viên hỗ trợ.'
        
        return jsonify({
            'bot_message':text,
            'action': action
        })

EVNSearcher_view = EVNSearcher.as_view('EVNSearcher')
app.add_url_rule('/api/searchs/', view_func=EVNSearcher_view, methods=['POST'])

