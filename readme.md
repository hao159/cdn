# CDN
###### _Upload and access file using python🐍 and flask 🚀🚀🚀_
###### _Author: [hao.nguyen](https://haonguyen96.net)_

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install.
```bash
cd project dir
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```
`⚠️⚠️️⚠️Note:  if  get  any error when install requirements |  remove pkg_resources==0.0.0 in  requirements.txt and try again    `
- Rename `.envexample` to `.env`
- Change config app in `.env`
- Change `APP_ENV` to `dev` for test and `product` for product

#### Run

- Normal
    ```
    python3 app.py
    ```
- With [Gunicorn](https://github.com/benoitc/gunicorn)
    ```
    gunicorn --bind=<your_ip>:<your_port> --workers=2 --threads=3 app:app
    ```
## Features

- Upload file from `direct url` or `form/data`
- Access file `direct` or `hide url`
- Block bad extensions file
- Manage file size upload for each accout
- Upload with custom dir
- Keep name of file upload `may be overide old file same name`
- Logging to graylog

## Usage
Input field:
- `file`: file or url  | _(rerequired)_
- `type`: type of file default `file` | accept `file` or direct `url` | _(optional)_
- `is_keep_name`: default when upload file app will rename file | for keep original file name when upload, option this field `1` | accept `0` or `1` | _(optional)_
- `custom_dir`: input your directory want to upload | default file will upload into root directory of account | accept multiple subdirectories and name valid this regex `[0-9a-zA-Z]` 

Response:
- `status`: `success` or `error`
- `desc` : Descreption of error `or` Descreption of file upload if success

Example Request:
- cURL:
    ```console
    curl --location --request POST 'http://localhost:9999/upload' \
    --header 'Authorization: Basic YWRtaW46aGFvQDEyMw==' \
    --form 'file=@"/C:/Users/haong/OneDrive/Desktop/My Recycle Bin/file gui/qcdongtesttrung.xlsx"'
    ```
- PHP cURL:
    ```php
    <?php
    $curl = curl_init();
    
    curl_setopt_array($curl, array(
      CURLOPT_URL => 'http://localhost:9999/upload',
      CURLOPT_RETURNTRANSFER => true,
      CURLOPT_ENCODING => '',
      CURLOPT_MAXREDIRS => 10,
      CURLOPT_TIMEOUT => 0,
      CURLOPT_FOLLOWLOCATION => true,
      CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
      CURLOPT_CUSTOMREQUEST => 'POST',
      CURLOPT_POSTFIELDS => array('file'=> new CURLFILE('/C:/Users/haong/OneDrive/Desktop/My Recycle Bin/file gui/qcdongtesttrung.xlsx')),
      CURLOPT_HTTPHEADER => array(
        'Authorization: Basic YWRtaW46aGFvQDEyMw=='
      ),
    ));
    
    $response = curl_exec($curl);
    
    curl_close($curl);
    echo $response;
    ```
- Python request
    ```python
    import requests

    url = "http://localhost:9999/upload"
    
    payload={}
    files=[
      ('file',('qcdongtesttrung.xlsx',open('/C:/Users/haong/OneDrive/Desktop/My Recycle Bin/file gui/qcdongtesttrung.xlsx','rb'),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    headers = {
      'Authorization': 'Basic YWRtaW46aGFvQDEyMw=='
    }
    
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    
    print(response.text)
    ```
Example Response:
- Success:
    ```json
        {
            "desc": {
                "custom_dir": "/hao/exel/",
                "direct_url": "http://localhost:9999/file/admin/hao/exel/5M84N38X_30082021175602.xlsx",
                "file_size": 244872,
                "hide_url": "http://localhost:9999/file/hao/exel/612cb9423e5509492a8ed009",
                "is_keep_name": false,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "raw_file_name": "qcdongtesttrung.xlsx",
                "save_file_name": "5M84N38X_30082021175602.xlsx",
                "user_name": "admin"
            },
            "status": "success"
        }
    ```
- Error:
    ```json
    {
        "desc": "invalid custom_dir, only accept [a-zA-Z] and '/'",
        "status": "error"
    }
    ```