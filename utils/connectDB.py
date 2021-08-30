
import os
from pymongo import MongoClient

def to_mongo_uri(host='127.0.0.1', port='27017', user='root', pass_w='', auth_db=None):
    uri = 'mongodb://'+user+':'+pass_w+'@'+host+':'+port
    if auth_db is not None:
        uri += '/?authSource='+auth_db
    return uri

class DBConnection:
    __instance = None
    
    @classmethod
    def getInstance(cls):
        if not cls.__instance:
            MONGO_HOST = os.environ.get('APP_MONGO_HOST')
            MONGO_PORT = os.environ.get('APP_MONGO_PORT')
            MONGO_USER = os.environ.get('APP_MONGO_USER')
            MONGO_PASS = os.environ.get('APP_MONGO_PASSWORD')
            MONGO_DB = os.environ.get('APP_MONGO_DB')
            MONGO_AUTH_DB = os.environ.get('APP_MONGO_DB')
            connect = MongoClient(to_mongo_uri(MONGO_HOST, MONGO_PORT, MONGO_USER, MONGO_PASS, MONGO_AUTH_DB))
            cls.__instance = connect[MONGO_DB]
        return cls.__instance