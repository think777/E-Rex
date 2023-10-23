from . import *

def getSecret(keyList:list):
    try:
        with open(SECRETS_PATH) as f:
            data=json.load(f)
            temp=data
            for key in keyList:
                temp=temp[key]
            return temp
    except Exception as e:
        print("Error: ",e)