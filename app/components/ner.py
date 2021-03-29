from underthesea import ner
import re 

class Recognizer:
    def __init__(self):
        pass
    
    @staticmethod
    def predict(message):
        name = []
        address = []
        phone_number = ""
        code = ""
        tokens = ner(message)
        print("tokens: {}".format(tokens))
        for token in tokens:
            if 'LOC' in token[3] and 'kh' not in token[0].lower():   #location
                address.append(token[0])
            if 'PER' in token[3] and 'kh' not in token[0].lower():   #person
                name.append(token[0])
        if name != []:
            name = ' '.join(name)
        else:
            name = ''
        if address != []:
            address = ' '.join(address)
        else:
            address = ''
        #regex phonenumber
        pattern_phone_number = '0\d{9}|\+84\d{9}'    
        phone_numbers = re.findall(pattern_phone_number, message)
        #regex code customer
        pattern_code = '[Pp].{5}\d{7}'
        codes = re.findall(pattern_code, message)
        if len(phone_numbers) > 0:
            phone_number = phone_numbers[-1]
        if len(codes)> 0:
            code = codes[-1]
        print("ner: ", name, address, phone_number, code)
        return name, address, phone_number, code
        