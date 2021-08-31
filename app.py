import sys
import os
import json
import re
import time
import datetime
import calendar
import requests
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from waitress import serve

from bson import json_util, ObjectId

from utils.common import *
from utils.connectDB import *
from utils.logger import *
#dir config
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = ROOT_DIR+'/upload/'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = os.environ.get('DEFAULT_MAX_SIZE_UPLOAD') * 1024 * 1024

def app_auth():
    if request.authorization and request.authorization.username and request.authorization.password:
        conditions = {
            'user' : request.authorization.username,
            'password' : request.authorization.password,
            'active' : True
        }
        cdn_db = DBConnection.getInstance()
        clt_user = cdn_db.cdn_user
        user = clt_user.find_one(conditions)
        if user:
            return user
        else:
            raise Exception('Auth fail')

    else:
        raise Exception('Auth is required!')

@app.errorhandler(404)
def not_found(e):
    return render_template('page404.html', title='Page not found', e=e), 404

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title=os.environ.get('APP_NAME'))

@app.route('/add_user', methods=['POST'])
def add_user():
    rCode = 406
    rDesc = "Unknow error"
    rStatus = 'error'
    try:
        user_info = app_auth()

        request_json = request.get_json()
        user = request_json.get('user')
        password = request_json.get('password')
        if user is None:
            raise Exception('user is required!')
        if password is None:
            raise Exception('password is required!')
        
        if len(user) != len(re.findall("[a-z]", user)):
            raise Exception('user only accept lowercase letters')
        max_upload_size = os.environ.get('DEFAULT_MAX_SIZE_UPLOAD')
        if request_json.get('max_upload_size') is not None:
            if isinstance(request_json.get('max_upload_size'), int) == False:
                raise Exception('max_upload_size invalid input')
            max_upload_size = request_json.get('max_upload_size')
        
        try:
            cdn_db = DBConnection.getInstance()
            clt_user = cdn_db.cdn_user #TODO có nên lưu theo user
            user_exist = clt_user.find_one({"user" : user})
            if user_exist:
                raise Exception('user exists')
        except Exception as e:
            raise Exception(e)
        

        gmt = time.gmtime()
        item_user = {
            "user": user,
            "password": password,
            "active": True,
            "max_upload_size": max_upload_size,
            'UCTtime' : datetime.datetime.utcnow(),
            'timeStamp' : calendar.timegm(gmt),
            'created_by' : {
                'user' : user_info['user'],
                'user_agent' : request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
            
        }

        try:
            cdn_db = DBConnection.getInstance()
            clt_user = cdn_db.cdn_user #TODO có nên lưu theo user
            file_id = clt_user.insert_one(item_user).inserted_id
        except Exception as e:
            raise Exception('Error connection')

        rCode = 200
        rStatus = 'success'
        rDesc = {
            'user' : user,
            "password": password,
            "max_upload_size" : max_upload_size
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msg_log = {
            'exc_type' : exc_type,
            'fname' : fname,
            'line_error' : exc_tb.tb_lineno,
            'msg' : str(e)
        }
        log_gray(msg_log,'ERROR', request.authorization.username )
        rDesc = str(e)
        rCode = 400
    finally:
        return {
            'status' : rStatus,
            'desc' : rDesc,
        }, rCode

@app.route('/deactive_user/<user>', methods=['GET', 'POST'])
def deactive_user(user):
    rCode = 406
    rDesc = "Unknow error"
    rStatus = 'error'
    try:
        user_info = app_auth()
        try:
            cdn_db = DBConnection.getInstance()
            clt_user = cdn_db.cdn_user #TODO có nên lưu theo user
            user_exist = clt_user.find_one({"user" : user})
            if user_exist is None:
                raise Exception('user does not exist')
        except Exception as e:
            raise Exception(e)

        #update
        gmt = time.gmtime()
        clt_user.update_one({"user" : user}, { "$set": {
                "active" : False,
                "updated_by" : {
                    "desc" : "deactive_user",
                    "user" : user_info['user'],
                    'user_agent' : request.headers.get('User-Agent'),
                    'ip': request.remote_addr,
                    'UCTtime' : datetime.datetime.utcnow(),
                    'timeStamp' : calendar.timegm(gmt),
                }
            } })

        rCode = 200
        rStatus = 'success'
        rDesc = {
            'user' : user,
            'active' : False
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msg_log = {
            'exc_type' : exc_type,
            'fname' : fname,
            'line_error' : exc_tb.tb_lineno,
            'msg' : str(e)
        }
        log_gray(msg_log,'ERROR', request.authorization.username )
        rDesc = str(e)
        rCode = 400
    finally:
        return {
            'status' : rStatus,
            'desc' : rDesc,
        }, rCode

@app.route('/set_size_upload/<user>/<size>', methods=['GET', 'POST'])
def set_size_upload(user, size):
    rCode = 406
    rDesc = "Unknow error"
    rStatus = 'error'
    try:
        user_info = app_auth()
        try:
            cdn_db = DBConnection.getInstance()
            clt_user = cdn_db.cdn_user #TODO có nên lưu theo user
            user_exist = clt_user.find_one({"user" : user})
            if user_exist is None:
                raise Exception('user does not exist')
        except Exception as e:
            raise Exception(e)
        try:
            size = int(size)
        except Exception as e:
            raise e
        if size is None or size == '' or isinstance(size, int) == False:
            raise Exception("invalid param size")
        #update
        gmt = time.gmtime()
        clt_user.update_one({"user" : user}, { "$set": {
                "max_upload_size" : size,
                "updated_by" : {
                    "desc" : "set_size_upload",
                    "user" : user_info['user'],
                    'user_agent' : request.headers.get('User-Agent'),
                    'ip': request.remote_addr,
                    'UCTtime' : datetime.datetime.utcnow(),
                    'timeStamp' : calendar.timegm(gmt),
                }
            } })

        rCode = 200
        rStatus = 'success'
        rDesc = {
            'user' : user,
            'max_upload_size' : size
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msg_log = {
            'exc_type' : exc_type,
            'fname' : fname,
            'line_error' : exc_tb.tb_lineno,
            'msg' : str(e)
        }
        log_gray(msg_log,'ERROR', request.authorization.username )
        rDesc = str(e)
        rCode = 400
    finally:
        return {
            'status' : rStatus,
            'desc' : rDesc,
        }, rCode

#get file hide url
@app.route('/file/<path:path>')
def download_file(path):
    try:
        #chia 2 nhánh down trực tiếp và down qua link hide
        paths= path.split('/')
        if ObjectId.is_valid(paths[-1]): # check coi path cuối cùng phải là mongoid ko
            cdn_db = DBConnection.getInstance()
            clt_file = cdn_db.cdn_file #TODO có nên lưu theo user
            file_info = clt_file.find_one({"_id": ObjectId(paths[-1])})
            return send_from_directory(UPLOAD_DIR+file_info['user']+file_info['custom_dir'], file_info['save_file_name'])
        else:
            return send_from_directory(UPLOAD_DIR+'/'.join(paths[:-1])+'/', paths[-1])
    except Exception as e:
        #print(e)
        return render_template('404.html', title='File not found', e=e), 404


#upload file
@app.route('/upload', methods=['POST'])
def upload():
    rCode = 406
    rDesc = "Unknow error"
    rStatus = 'error'
    try:
        #auth
        user_info = app_auth()
        app.config.update(
            MAX_CONTENT_LENGTH= user_info['max_upload_size'] * 1024 * 1024
        )

        user_name =  request.authorization.username
        user_path = UPLOAD_DIR+user_name+'/'
        if not os.path.exists(user_path):
            os.makedirs(user_path)

        type_upload = 'file' #default
        if request.form.get('type') is not None:
            type_upload = request.form.get('type')
            if type_upload not in ['file', 'url']:
                raise Exception('type only accept file or url')
        
        is_keep_name = 0
        if request.form.get('is_keep_name') is not None:
            is_keep_name = int(request.form.get('is_keep_name'))
            if isinstance(is_keep_name, int) and is_keep_name not in [0, 1]:
                raise Exception('is_keep_name only accept 0 or 1')

        custom_dir = ''
        if request.form.get('custom_dir') is not None:
            custom_dir = request.form.get('custom_dir')
            custom_dir= custom_dir.strip()
            if custom_dir == "":
                raise Exception('custom_dir is empty')
            #remove "/" path prefix and suffix
            if custom_dir[0] == '/':
                custom_dir = custom_dir[1:]
            if custom_dir[-1] == '/':
                custom_dir = custom_dir[:-1]
            
            if validDir(custom_dir):
                custom_dir = '/'+custom_dir+'/'
                user_path = user_path[:-1]+custom_dir
                if not os.path.exists(user_path):
                    os.makedirs(user_path)
            else:
                raise Exception("invalid custom_dir, only accept [0-9a-zA-Z] and '/'")
        if type_upload == 'file':
            #process file
            if 'file' not in request.files:
                raise Exception('file is required!')
            file = request.files['file']
            if file.filename == '':
                raise Exception('file is required!')
            mimetype = file.content_type
            #size = file.content_length
            raw_file_name = secure_filename(file.filename)
            file_ext =raw_file_name.split('.')[-1]
            if bad_ext_check(file_ext) == False:
                raise Exception('Sorry, what do u want?')
            if is_keep_name == 1:
                save_file_name = raw_file_name
            else:
                save_file_name = random_file_name(8, file_ext)
            file.save(os.path.join(user_path, save_file_name))
            size = os.stat(os.path.join(user_path, save_file_name)).st_size
        else:
            #process url
            if request.form.get('file') is not None:
                file = request.form.get('file')
                if validUrl(file):
                    req = requests.get(file, allow_redirects=True)
                    mimetype = req.headers['content-type']
                    size = req.headers['content-length']
                    raw_file_name = file.split('/')[-1]
                    file_ext =raw_file_name.split('.')[-1]
                    if bad_ext_check(file_ext) == False:
                        raise Exception('Sorry, what do u want?')
                    if is_keep_name == 1:
                        save_file_name = raw_file_name
                    else:
                        save_file_name = random_file_name(8, file_ext)
                    open(user_path+save_file_name, 'wb').write(req.content)
                else:
                    raise Exception('invalid url')
            else:
                raise Exception('file[url] is rerequired!')
        gmt = time.gmtime()
        item_file = {
            'user' : user_name,
            'UCTtime' : datetime.datetime.utcnow(),
            'timeStamp' : calendar.timegm(gmt),
            'raw_file_name' : raw_file_name,
            'save_file_name' : save_file_name,
            'custom_dir' : custom_dir,
            'mimetype': mimetype,
            'file_size' : size,
            'user_agent' : request.headers.get('User-Agent'),
            'ip': request.remote_addr
        }
        try:
            cdn_db = DBConnection.getInstance()
            clt_file = cdn_db.cdn_file #TODO có nên lưu theo user
            file_id = clt_file.insert_one(item_file).inserted_id
        except Exception as e:
            raise Exception('Error connection')

        rCode = 200
        rStatus = 'success'
        #url = 
        if custom_dir == '':
            hide_url = os.environ.get('APP_URL')+'file'+ '/'+str(file_id)
            direct_url = os.environ.get('APP_URL')+'file/'+user_name+ '/' + save_file_name
        else:
            hide_url = os.environ.get('APP_URL')+'file'+ custom_dir +str(file_id)
            direct_url = os.environ.get('APP_URL')+'file/'+user_name+ custom_dir + save_file_name
        rDesc = {
            'raw_file_name' : raw_file_name,
            'save_file_name' : save_file_name,
            'hide_url' : hide_url,
            'direct_url' : direct_url,
            'custom_dir' : custom_dir,
            'mimetype' : mimetype,
            'file_size' : size,
            'is_keep_name': True if is_keep_name == 1 else False
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msg_log = {
            'exc_type' : exc_type,
            'fname' : fname,
            'line_error' : exc_tb.tb_lineno,
            'msg' : str(e),
            'user_agent' : request.headers.get('User-Agent'),
            'ip': request.remote_addr
        }
        log_gray(msg_log,'ERROR', request.authorization.username )
        rDesc = str(e)
        rCode = 400
    finally:
        return {
            'status' : rStatus,
            'desc' : rDesc,
        }, rCode

if __name__ == '__main__':
    if os.environ.get('APP_ENV') == 'product':
        serve(app)
        #app.run(host=os.environ.get('APP_HOST'), port = os.environ.get('APP_PORT'))
    else:
        app.run(host=os.environ.get('APP_HOST'), port = os.environ.get('APP_PORT'), debug=True)