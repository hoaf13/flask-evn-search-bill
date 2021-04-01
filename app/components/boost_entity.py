from ner import Recognizer
import pika
import time
import redis 
import os

red = redis.StrictRedis(host='localhost',port=6379,db=0)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='chatbot_direct_logs', exchange_type='direct')
channel.queue_declare(queue='chatbot_entity_queue', durable=True)

channel.queue_bind(queue='chatbot_entity_queue', exchange='chatbot_direct_logs',routing_key='binding_entity')
print("A consummer in entity Queue was create !")

def callback(ch, method, properties, body):
    print("message go to Boost_entity PID: {} ".format(os.getpid()))
    print("---------------------------------------------------\n")
    response = body.decode("utf-8")
    data = eval(response)
    _id = data['_id']
    message = data['message']
    name, address, phone_number, code = Recognizer.predict(message)
    ans = {
        'name': name,
        'address': address,
        'phone_number': phone_number,
        'code': code 
    }
    red.set(_id, str(ans))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='chatbot_entity_queue', on_message_callback=callback)
channel.start_consuming()