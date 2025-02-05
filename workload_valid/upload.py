import boto3
import base64
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import requests
import os
import io
import warnings
import random
import time
warnings.filterwarnings("ignore")


namespace = "    "

file_name = './pexels-rfera-2286895.jpg'
write_file_name = './judge.txt'

config = {
    "sa":{"bucket_name":"xxxx",
            "region_name":"uk-london-1",
            "aws_access_key_id":"xxxx",
            "aws_secret_access_key":"xxxx",
            "lb":"",
            "vm":["xxxx"]}
    }

def md5_base64_from_bytes(data):
    """Creates an MD5 hash of the given bytes and encodes it in Base64."""

    # Calculate the MD5 hash
    md5_hash = hashlib.md5(data).digest()

    # Encode the hash in Base64
    base64_encoded = base64.b64encode(md5_hash).decode('utf-8')

    return base64_encoded

def generate_par_data(boto,object_name):
    putUrl = boto.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket_name, 'Key': object_name},
        ExpiresIn=3600)

    print("boto.generate_presigned_url:", putUrl)

    expiration_date = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    policy_document = {
        "expiration": expiration_date,
        "conditions": [
            {"bucket": bucket_name},
            ["starts-with", "$key", ""],
            {"acl": "public-read"},
            ["content-length-range", 0, 1048576]
         ]
    }

    policy = base64.b64encode(json.dumps(policy_document).encode()).decode()
    signature = base64.b64encode(
        hmac.new(aws_secret_access_key.encode(), policy.encode(), hashlib.sha1).digest()).decode()
    encoded_url = base64.b64encode(putUrl.encode()).decode()

    data = {
        'policy': policy,
        'signature': signature,
        'access_key_id': aws_access_key_id,
        'bucket_name': bucket_name,
        'putUrl': encoded_url
    }

    return data

def send_request(proxy_url, par_data):
    #with open(filepath, 'rb') as file:
    #   files = {'file': file}
    #   res = requests.post(proxy_url, data=par_data, files=files, verify=False)
    # return res
        bytes = os.urandom(5*1024*1024)
        result = md5_base64_from_bytes(bytes)
        print("md5base64:", result)
        file = io.BytesIO(bytes)
        files = {'file': file}
        res = requests.post(proxy_url, data=par_data, files=files, verify=False)
        return res,result
        
def upload_file_to_s3(boto,proxy_ip):
    proxy_url = f"https://{proxy_ip}:443"
    print("proxy_url:",proxy_url)
    object_name = f"test20-{str(random.randint(1000000, 9999999))}-{proxy_ip}-{datetime.utcnow().strftime('%Y-%m-%dT%H:%M%S%f')}.data"
    par_data = generate_par_data(boto,object_name)
    response,hashstr = send_request(proxy_url,par_data)
    if response.status_code == 200 and "error" not in response.text.lower():
        print("Response:", response.text)
        #写文件
        with open(write_file_name, "a") as f:
        # Write a string to the file
            f.write(object_name + ","+ hashstr+ "\n")
        print(f"文件 {file_name} 已成功上传到存储桶 {bucket_name}，对象名为 {object_name}")        
    else:
        print("出错：", response.text)
    print("\n\n")

scope = ["sa"]
mode = "vm"

for k in scope:
    v = config[k]
    print("======== region:",k,"========")
    bucket_name = v["bucket_name"]
    region_name = v["region_name"]
    aws_access_key_id = v["aws_access_key_id"]
    aws_secret_access_key = v["aws_secret_access_key"]
    endpoint_url = f"https://{namespace}.compat.objectstorage.{region_name}.oraclecloud.com"
    


    print("region name: ",region_name)
    print("endpoint_url: ",endpoint_url)
    print("Bucket name: ",bucket_name)
    
    # 测试连接  
    """
    s3 = boto3.resource(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
        endpoint_url=endpoint_url
        )
    print("--------查看文件列表--------")
    for object in s3.Bucket(bucket_name).objects.limit(count=3):
        print(object.key)
    print("--------------------------")
     """
    # 连接
    boto = boto3.client(
        's3',
        use_ssl=True,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        endpoint_url=endpoint_url
    )
    
    for x in range(1000):
        if mode == "lb" or mode == "all":
            print("测试lb上传:",v["lb"])
            upload_file_to_s3(boto,v["lb"])

        if mode == "vm" or mode == "all":
            for proxy_ip in v["vm"]:
                    print("测试vm上传:",proxy_ip)
                    upload_file_to_s3(boto,proxy_ip)
        x=x+1