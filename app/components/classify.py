import tensorflow as tf 
import gensim 
from gensim.models import KeyedVectors
import numpy as np 

intents = ['intent_cant_hear','intent_affirm','intent_deny_confirm','intent_provide_phone_number','intent_provide_address',
          'intent_provide_code_customer','intent_provide_name','intent_this_phone']

word2vec_model = KeyedVectors.load_word2vec_format('/home/hoaf13/workspace/web_app/flask/EVNsearch/app/components/pretrained_weights/baomoi.model.bin', binary=True)

def embedding(x, max_length = 25):
    ans = []
    words = x.split(' ')
    while len(words) < max_length:
        words.append('không_biết')
    tmp_X = []
    for word in words:
        tmp = word
        if word not in word2vec_model.vocab:
            tmp = 'không_biết'
        tmp_X.append(word2vec_model.wv[tmp])
    ans.append(tmp_X)  
    return ans 

def build_model(hidden_size = 512):
    # Model architecture
    input = tf.keras.layers.Input(shape=(25,400))
    model = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units=hidden_size, return_sequences=False, recurrent_dropout=0.1))(input)
    out = tf.keras.layers.Dense(8, activation='softmax')(model)

    model = tf.keras.Model(input, out)
    model.compile(optimizer='adam',
                loss = tf.keras.losses.CategoricalCrossentropy(),
                metrics=['accuracy'])
    model.summary()
    return model

model = build_model()
model.load_weights('/home/hoaf13/workspace/web_app/flask/EVNsearch/app/components/pretrained_weights/evn-search-pretrained.hdf5')

class Classifier:
    def __init__(self):
        pass
    
    @staticmethod
    def embedding(message):
        pass

    @staticmethod
    def predict(message):
        embedded = embedding(message)
        embedded = np.array(embedded)
        probs = model.predict(embedded)[0]
        index = np.argmax(probs)
        intent = intents[index]
        prob = probs[index]
        return intent, prob

