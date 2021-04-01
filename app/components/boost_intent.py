from classify import Classifier
import redis
import pika
import time
import os 

red = redis.StrictRedis(host='localhost',port=6379,db=0)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='chatbot_direct_logs', exchange_type='direct')
channel.queue_declare(queue='chatbot_intent_queue', durable=True)

channel.queue_bind(queue='chatbot_intent_queue', exchange='chatbot_direct_logs',routing_key='binding_intent')
print("A consummer in intent Queue was create !")

def callback(ch, method, properties, body):
    print("message go to Boost_intent PID: {} ".format(os.getpid()))
    print("---------------------------------------------------\n")
    response = body.decode("utf-8")
    data = eval(response)
    _id = data['_id']
    message = data['message']
    intent, prob = Classifier.predict(message)
    ans = {
        'intent': intent,
        'prob': prob,
    }
    red.set(_id, str(ans))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='chatbot_intent_queue', on_message_callback=callback)
channel.start_consuming()