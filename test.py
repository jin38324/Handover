import boto3
import base64
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import requests

proxy_url = "https://<YOUR_OPENRESTY_SERVER>:443"


def get_data(key_name):
    region_name = "ap-chuncheon-1"
    aws_access_key_id = "<YOUR-Customer secret keys>-Access Key"
    aws_secret_access_key = "<YOUR-Customer secret keys>-Password"
    endpoint_url = "https://axzbt3kupcxb.compat.objectstorage.ap-chuncheon-1.oraclecloud.com"

    bucket_name = 'my-bucket'
    key_name = key_name

    s3 = boto3.client(
        's3',
        use_ssl=True,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        endpoint_url=endpoint_url
    )

    putUrl = s3.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket_name, 'Key': key_name},
        ExpiresIn=3600)
    print(putUrl)

    expiration_date = (datetime.utcnow() + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

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


def upload_file_to_s3(params, filepath):
    with open(filepath, 'rb') as file:
        files = {'file': file}
        res = requests.post(proxy_url, data=params, files=files, verify=False)
    return res


file_path = r'C:\Users\loren\PycharmProjects\pythonProject31\hello2.txt'
for i in range(1, 10):
    data = get_data('test%d.txt' % i)
    response = upload_file_to_s3(data, file_path)
    print(response.status_code)
# print(response.text)
