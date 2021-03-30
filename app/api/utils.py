from . import graph, nodes, edges, Classifier, Recognizer
from app.models import Message
from app import db 
import random
import json
import redis

red = redis.StrictRedis(host='localhost',
                        port=6379,
                        db=0)


def find_entities(sender_id, message):
    print("---------------processing in find_entities------------------")
    last_message = list(Message.query.filter_by(sender_id=sender_id).all())[-1]
    name, address, phone_number, code = Recognizer.predict(message)
    print("find entities name: {}  address: {}  phone_number: {}   code: {}".format(name, address, phone_number, code))
    current_entities = eval(last_message.entities)
    if current_entities['province'] == '':
        current_entities['province'] = address
    else:
        current_entities['address'] = address
    current_entities['name'] = name
    current_entities['phone_number'] = phone_number
    current_entities['code'] = code

    print("current entities: {}".format(current_entities))
    return current_entities



def find_best_intent(sender_id, message, entities):
    def is_a_middle_province(province):
        middle_provinces = ['Thanh Hóa','Nghệ An','Hà Tĩnh','Quảng Bình','Quảng Trị','Thừa Thiên Huế','Đà Nẵng',
            'Quảng Nam','Quảng Ngãi','Bình Định','Phú Yên','Khánh Hòa','Ninh Thuận','Bình Thuận','Kon Tum','Gia Lai',
            'Đắk Lắk','Đắk Nông','Lâm Đồng','Đắc Lắc','Đắc nông','Đắc Lắk','Đắk Lắc']
        middle_provinces = [p.lower() for p in middle_provinces]
        if province.lower() in middle_provinces:
            return True 
        return False

    print("---------------processing in find_best_intent------------------")
    intent = None
    predicted_intent, prob = Classifier.predict(message)  
    last_message = list(Message.query.filter_by(sender_id=sender_id).all())[-1]
    previous_action = last_message.action

    print("predict intent : {} {}".format(predicted_intent, prob))
    if prob < 0.6:
        intent = 'intent_fallback'
        print("find intent: {}".format(intent))
        return intent

    intent = predicted_intent
    
    if previous_action == 'action_start':
        province = entities['province']
        print("province in client message: {}".format(province))
        if entities['province'] == '':
            intent = 'not_existed'
        else:
            if is_a_middle_province(province):
                intent = 'existed'
            else:
                intent = 'out'
        print("find intent from previous action_start: {}".format(intent))
        return intent
    
    if predicted_intent not in graph[previous_action]:
        intent = 'intent_fallback'
        print("find intent not in graph: {}".format(intent))
    

    if entities['phone_number'] == '' and intent in ['intent_this_phone', 'intent_provide_phone_number'] and previous_action == 'action_provide_phone_number':
        intent = 'intent_fallback' 
        print("choose intent from phone: {}".format(intent))
    if entities['code'] == '' and intent in ['intent_provide_code_customer'] and previous_action == 'action_provide_code_customer':
        intent = 'intent_fallback'
        print("choose intent from code: {}".format(intent))
    if entities['address'] == '' and intent in ['intent_provide_address'] and previous_action == 'action_provide_address':
        intent = 'intent_fallback'
        print("choose intent from address: {}".format(intent))
    if entities['name'] == '' and intent in ['intent_provide_name'] and previous_action == 'action_provide_name':
        intent = 'intent_fallback'
        print("choose intent from name: {}".format(intent))

    print("auto intent: {}".format(intent))
    return intent





def find_best_action(sender_id, current_intent, entities):
    print("---------------processing in find_best_action------------------")
    action = None
    repeat_count = 0
    previous_message = list(Message.query.filter_by(sender_id=sender_id).all())[-1]
    previous_intent = previous_message.intent
    previous_action = previous_message.action

    print("previous intent: {} - previous action: {}".format(previous_intent, previous_action))
    if previous_intent == 'intent_fallback' or previous_intent == 'not_existed':
        repeat_count += 1
    if current_intent == 'intent_fallback' or current_intent == 'not_existed':
        repeat_count += 1
    
    if repeat_count > 1:
        if previous_action == 'action_start':
            if previous_intent == 'out':
                action = 'not_province_forward'
            if previous_intent == 'not_existed':
                action = 'not_provide_province_forward'
        if previous_action == 'action_provide_province':
            action = 'not_required_forward'
        if previous_action == 'action_start' and current_intent == 'out':
            action = 'not_provide_province_forward'
        if previous_action == 'intent_provide_address' and current_intent == 'out':
            action = 'not_province_forward'
        action = 'not_required_forward'
        print("here in repeat count > 1")
        return action, repeat_count
    
    if repeat_count == 1:
        if current_intent in ['intent_this_phone', 'intent_provide_phone_number'] and previous_intent == 'intent_fallback' and previous_action == 'action_provide_province':
            repeat_count = 0
        if current_intent in ['intent_provide_code_customer'] and previous_intent == 'intent_fallback' and previous_action == 'action_provide_province':
            repeat_count = 0
        if current_intent in ['intent_provide_address'] and previous_intent == 'intent_fallback' and previous_action == 'action_provide_province':
            repeat_count = 0
       

    if previous_intent in ['not_existed','intent_fallback'] and current_intent not in ['not_existed','intent_fallback']:
        repeat_count = 0

    if (current_intent == 'intent_this_phone' or current_intent == 'intent_provide_phone_number') and entities['phone_number'] != '' and previous_action == 'action_provide_province':
        action = 'action_provide_phone_number_confirm'
        repeat_count = 0
        print("provide phone number before ask")
        return action, repeat_count
    if current_intent == 'intent_provide_code_customer' and entities['code'] != '' and previous_action == 'action_provide_province':
        action = 'action_provide_code_customer_confirm'
        repeat_count = 0
        print("provide phone code customer before ask")
        return action, repeat_count
    if current_intent == 'intent_provide_address' and entities['address'] != '' and previous_action == 'action_provide_province':
        action = 'action_provide_address_confirm'
        repeat_count = 0
        print("provide phone address before ask")
        return action, repeat_count

    # loop-branch 
    if len(list(Message.query.filter_by(sender_id=sender_id).all())) > 1:
        print("consider in loop branch")
        previous_messages = list(Message.query.filter_by(sender_id=sender_id).all())[-2:]
        previous2_action = previous_messages[0].action
        previous1_action = previous_messages[1].action
        flag_loop_branch = False
        if current_intent in ['intent_deny_confirm', 'intent_this_phone', 'intent_provide_phone_number'] \
            and ( (previous1_action == 'action_provide_phone_number_confirm' and previous2_action == previous1_action) 
               or (previous1_action == 'action_provide_phone_number_confirm' and previous2_action == 'action_provide_phone_number_repeat') ):
            flag_loop_branch = True
        if current_intent in ['intent_deny_confirm', 'intent_provide_code_customer'] \
            and ( (previous1_action == 'action_provide_code_customer_confirm' and previous2_action == previous1_action) 
               or (previous1_action == 'action_provide_code_customer_confirm' and previous2_action == 'action_provide_code_customer_repeat') ):
            flag_loop_branch = True
        if current_intent in ['intent_deny_confirm', 'intent_provide_address'] \
            and ( (previous1_action == 'action_provide_address_confirm' and previous2_action == previous1_action) 
               or (previous1_action == 'action_provide_address_confirm' and previous2_action == 'action_provide_address_repeat') ):
            flag_loop_branch = True
        if current_intent in ['intent_deny_confirm', 'intent_provide_name'] \
            and ( (previous1_action == 'action_provide_name_confirm' and previous2_action == previous1_action) 
               or (previous1_action == 'action_provide_name_confirm' and previous2_action == 'action_provide_name_repeat') ):
            flag_loop_branch = True
        
        if flag_loop_branch:
            repeat_count = 0
            action = 'action_provide_province_repeat'
            print("go to loop branch")
            return action, repeat_count
        
    print("graph {} {}".format(previous_action, current_intent))
    action = graph[previous_action][current_intent]
    print("action: {}".format(action))
    print("find action: {} - {}".format(action, repeat_count))
    return action, repeat_count



def update_entities(sender_id, intent, entities):
    previous_message = list(Message.query.filter_by(sender_id=sender_id).all())[-1]
    previous_action = previous_message.action
    previous_entities = eval(previous_message.entities)
    previous_intent = previous_message.intent
    updated_entities = previous_entities

    previous_message = list(Message.query.filter_by(sender_id=sender_id).all())[-1]
    previous_action = previous_message.action
    if previous_action == 'action_provide_province':
        updated_entities["code"] = ""
        updated_entities["phone_number"] = ""
        updated_entities["address"] = ""
        updated_entities["name"] = ""
        
        
    if intent == 'intent_deny_confirm':
        if previous_action == 'action_provide_phone_number_confirm':
            updated_entities['phone_number'] = ''
        if previous_action == 'action_provide_code_customer_confirm':
            updated_entities['code'] = ''
        if previous_action == 'action_provide_address_confirm':
            updated_entities['address'] = ''
        if previous_action == 'action_provide_name_confirm':
            updated_entities['name'] = ''
        print("update entities intent_deny_confirm")
        return updated_entities

    if intent == 'intent_affirm' or (intent in ['intent_this_phone','intent_provide_phone_number'\
        ,'intent_provide_code_customer','intent_provide_address','intent_provide_name'] and \
            previous_action in ['action_provide_phone_number','action_provide_code_customer','action_provide_address',\
                                'action_provide_phone_number_repeat','action_provide_code_customer_repeat','action_provide_address_repeat','action_provide_name_repeat',\
                                'action_provide_phone_number_confirm','action_provide_code_customer_confirm','action_provide_address_confirm','action_provide_name_confirm'
                                ]):
        if previous_action in ['action_provide_phone_number','action_provide_phone_number_repeat','action_provide_phone_number_confirm']:
            if entities['phone_number'] != '':
                updated_entities['phone_number'] = entities['phone_number'] 
        if previous_action in ['action_provide_code_customer','action_provide_code_customer_repeat','action_provide_code_customer_confirm']:
            if entities['code'] != '':
                updated_entities['code'] = entities['code']
        if previous_action in ['action_provide_address','action_provide_address_repeat','action_provide_address_confirm']:
            if entities['address'] != '':
                updated_entities['address'] = entities['address']
        if previous_action in ['action_provide_name','action_provide_name_repeat','action_provide_name_confirm']:
            if entities['name'] != '':
                updated_entities['name'] = entities['name']
        print("update entities intent_affirm or re-type last intent")
        return updated_entities

    if entities['code'] != '':
        updated_entities['code'] = entities['code']
    if entities['name'] != '':
        updated_entities['name'] = entities['name']
    if entities['address'] != '':
        updated_entities['address'] = entities['address']
    if entities['phone_number'] != '':
        updated_entities['phone_number'] = entities['phone_number']    
    if entities['province'] != '':
        updated_entities['province'] = entities['province']
    print("update entities by this client message: {}".format(updated_entities))
    return updated_entities

    













def gernerate_text(sender_id, intent, action, repeat_count, entities):
    print("---------------processing in generate_text------------------")
    text = ""

    print("action: {}   repeatcount: {}".format(action, repeat_count))
    
    if action == 'action_start':
        if repeat_count==0:
            text = "Xin chào, đây là tổng đài tra cứu tiền điện. Xin hỏi quý khách thuộc tỉnh thành nào vậy?"
        else: 
            text = "Quý khách vui lòng đọc lại tên tỉnh thành chính xác giúp em"
    
    if action == 'action_provide_province_repeat':
        field_sender_id = 'field_' + str(sender_id)
        count_sender_id = 'count_' + str(sender_id)
        used_field = red.get(field_sender_id)
        print("used_field: {}".format(used_field))
        used_field = used_field.decode("utf-8") 
        repeat_count = int(red.get(count_sender_id).decode("utf-8"))
        print("provide_province_repeat repeat_count: {}".format(repeat_count))
        fields = ['phone_number', 'code', 'address']
        en2vn = {
            'phone_number':'số điện thoại',
            'code':'mã khách hàng',
            'address':'địa chỉ'
        }
        fields.remove(used_field)
        print("used field: {} -> {}".format(used_field, fields))
        if repeat_count==0:
            red.set(count_sender_id, repeat_count+1)
            text = 'Dạ rất tiếc là em chưa rõ yêu cầu của quý khách. Quý khách có muốn tra cứu lại theo {}, hay theo {} không ạ ?'.format(en2vn[fields[0]],en2vn[fields[1]])
        else:
            if intent == 'intent_fallback' and  repeat_count == 1:
                text = 'Một lần nữa em xin hỏi, Quý khách có muốn tra cứu lại theo {}, hay theo {} không ạ ?'.format(en2vn[fields[0]],en2vn[fields[1]]) 
            else:
                action = 'not_required_forward'
                red.set(count_sender_id, 0)

    if action == 'action_provide_province':
        if repeat_count==0:
            text = 'Đầu tiên, quý khách muốn tra cứu theo mã khách hàng, theo số điện thoại hay theo địa chỉ vậy?'
        else:
            text = 'Một lần nữa em xin hỏi lại, quý khách muốn tra cứu theo mã khách hàng, theo số điện thoại hay theo địa chỉ vậy?'

    if action == 'action_provide_phone_number':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'phone_number')
        print("get redis: ", red.get(field_sender_id))
        if repeat_count==0:
            text = 'Quý khách vui lòng đọc số điện thoại trên hợp đồng điện để em tra cứu.'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách vui lòng đọc số điện thoại trên hợp đồng điện giúp em.'

    if action == 'action_provide_phone_number_confirm':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'phone_number')
        print("get redis: ", red.get(field_sender_id))
        phone_number = entities['phone_number']
        if repeat_count==0:
            text = 'Em xin xác nhận số điện thoại {} có phải không ?'.format(phone_number)
        else:
            text = 'Một lần nữa, em xin xác nhận có phải sô điện thoại {} đúng không ạ ?'.format(phone_number)

    if action == 'action_provide_phone_number_repeat':
        if repeat_count==0:
            text = 'Vậy quý khách đọc lại số điện thoại trên hợp đồng điện giúp em'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách nhập lại số điện thoại giúp em.'
    
    if action == 'action_provide_code_customer':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'code')
        if repeat_count==0:
            text = 'Quý khách vui lòng đọc mã khách hàng để em tra cứu'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách vui lòng đọc mã khách hàng giúp em.'

    if action == 'action_provide_code_customer_confirm':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'code')
        code = entities['code'] 
        if repeat_count==0:
            text = 'Em xin xác nhận mã khách hàng {} phải không vậy ?'.format(code)
        else:
            text = 'Một lần nữa, em xin xác nhận có phải mã khách hàng là {} phải không ?'.format(code)      

    if action == 'action_provide_code_customer_repeat':
        if repeat_count==0:
            text = 'Vậy quý khách đọc lại mã khách hàng chính xác giúp em'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách vui lòng đọc mã khách hàng giúp em.'

    if action == 'action_provide_address':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'address')
        if repeat_count==0:
            text = 'Quý khách vui lòng đọc địa chỉ trên hợp đồng điện giúp em'
        else:
            text = 'Xin lỗi em vẫn chưa nhận được địa chỉ, anh chị viết lại địa chỉ giúp em '
    
    if action == 'action_provide_address_confirm':
        field_sender_id = 'field_' + str(sender_id)
        red.set(field_sender_id, 'address')
        address = entities['address']
        if repeat_count==0:
            text = 'Em xin xác nhận địa chỉ {} đúng không vậy'.format(address)
        else:
            text = 'Một lần nữa, em xin xác nhận có phải địa chỉ {} đúng không ?'.format(address)

    if action == 'action_provide_address_repeat':
        if repeat_count==0:
            text = 'Vậy quý khách đọc lại địa chỉ trên hợp đồng điện giúp em'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách đọc lại địa chỉ trên hợp đồng điện giúp em.'

    if action == 'action_provide_name':
        if repeat_count==0:
            text = 'Quý khách vui lòng đọc họ tên đầy đủ trên hợp đồng điện'
        else:
            text = 'Xin lỗi em vẫn chưa nhận dạng được tên anh chị, mời quý khách nhập lại tên rõ ràng.'
    
    if action == 'action_provide_name_confirm':
        name = entities['name']
        if repeat_count==0:
            text = 'Em xin xác nhận tên quý khách là {} phải không vậy'.format(name)
        else:
            text = 'Một lần nữa, em xin xác nhận tên quý khách là {} phải không vậy'.format(name)
    
    if action == 'action_search':
        text = 'Hệ thống đang thực hiện tra cứu, quý khách vui lòng đợi giấy lát ...'    

    if action == 'action_provide_name_repeat':
        if repeat_count==0:
            text = 'Vậy quý khách đọc lại họ tên trên hợp đồng điện chính xác giúp em'
        else:
            text = 'Xin lỗi em vẫn chưa hiểu, quý khách có thể đọc lại họ tên được không ạ.'

    if action == 'not_province_forward':
        province = entities['province']
        text = "Rất xin lỗi, hiện tại điện lực chưa hỗ trợ tra cứu cho khách hàng thuộc tỉnh/thành phố {}. Tạm biệt quý khách.".format(province)
    if action == 'not_provide_province_forward':
        text = "Xin lỗi em chưa rõ tỉnh thành. Vui lòng chờ giây lát, cuộc gọi đang được chuyển cho điện thoại viên hỗ trợ."
    if action == 'not_required_forward':
        text = "Xin lỗi em chưa rõ yêu cầu. Vui lòng chờ giây lát, cuộc gọi đang được chuyển cho điện thoại viên hỗ trợ chi tiết hơn."
    if action == 'supported_forward':
        text = "Em rất tiếc không tìm thấy thông tin tiền điện của quý khách. Vui lòng chờ giây lát, cuộc gọi đang được chuyển cho điện thoại viên hỗ trợ."   
    
    print(text)
    return text


def save_to_database(sender_id, intent, action, entities, client_message, bot_message):
    message = Message(sender_id=sender_id, intent=intent, action=action, entities=entities, client_message=client_message, bot_message=bot_message)
    db.session.add(message)
    db.session.commit()
    print("\nsave {}. {} to db successfully !".format(sender_id, action))
    return message