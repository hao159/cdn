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

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    print(os.environ.get('APP_GRAYLOG_HOST'))
    print(os.environ.get('APP_GRAYLOG_PORT'))
    #log_gray_debug({"status" : 200, "desc" : "SMS Đây là log full msg"})
    return render_template('index.html', title='CDN of SMS team')

@app.route('/test')
def test():
    log_gray({
        "msg" : 'SMS Logging from Graypy lv CRITICAL',
        'level' : 'CRITICAL'
    }
        , 'CRITICAL')
    log_gray('SMS Logging from Graypy lv ERROR', 'ERROR')
    return{
        'status' : 200,
        'desc' : "this is log"
    }, 200

#get file hide url
@app.route('/file/<path:path>')
def download_file(path):
    try:
        #chia 2 nhánh down trực tiếp và down qua link hide
        paths= path.split('/')
        if bson.objectid.ObjectId.is_valid(paths[-1]): # check coi path cuối cùng phải là mongoid ko
            cdn_db = DBConnection.getInstance()
            clt_file = cdn_db.cdn_file #TODO có nên lưu theo user
            file_info = clt_file.find_one({"_id": ObjectId(paths[-1])})
            return send_from_directory(UPLOAD_DIR+file_info['user']+file_info['custom_dir'], file_info['save_file_name'])
        else:
            return send_from_directory(UPLOAD_DIR+'/'.join(paths[:-1])+'/', paths[-1])
    except Exception as e:
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
                raise Exception("invalid custom_dir, only accept [a-zA-Z] and '/'")
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
            'file_size' : size
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
            'user_name': user_name,
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

if __name__ == '__main__':
    if os.environ.get('APP_ENV') == 'product':
        serve(app)
        #app.run(host=os.environ.get('APP_HOST'), port = os.environ.get('APP_PORT'))
    else:
        app.run(host=os.environ.get('APP_HOST'), port = os.environ.get('APP_PORT'), debug=True)