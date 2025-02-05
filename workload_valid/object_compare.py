""" Install OCI firstly as the following:
    pip install oci
"""

import oci
import csv

namespace_name = "xxxx"
bucket_name = "upload"
#config = oci.config.from_file()
config = {
    "user": "ocid1.user.oc1..xxxxxxxxxxxxxxxxxxxxxxx",
     "key_file":"/home/opc/xxxx.pem",
     "fingerprint": "xxxx",
    "tenancy": "ocid1.tenancy.oc1..xxxx",
    "region": "uk-london-1"
}
object_storage_client = oci.object_storage.ObjectStorageClient(config)

diff_files = []
with open("judge.txt", newline="") as file:
    reader = csv.reader(file, delimiter=",")
    for row in reader:
        
        #object_name = row["object_key"]
        #content_hash = row["content_hash"]
        object_name = row[0]
        content_hash = row[1]
        print(row[0])
        print(row[1])
        get_object_response = object_storage_client.get_object(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name,
        )

        oss_content_md5 = get_object_response.headers.get('content-md5')
        if content_hash != oss_content_md5:
            diff_files.append(object_name)
            
if diff_files:
    print('######### File-change detected: ########')
    for diff_file in diff_files:
        print(diff_file)
else:
    print('############### ALL GOOD ###############')
