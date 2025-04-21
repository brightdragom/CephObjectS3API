from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import boto3
import datetime
app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return 'Hello'

def printLog(level, msg):
    print(f"[{level}] :: {msg}")

#####################################################################
#####################################################################
#####################################################################
# 환경 변수에서 AWS S3 정보 가져오기
# 📌 전역 S3 설정용 딕셔너리
s3Argument = {
    "HOST": "",
    "PORT": "",
    "RGW_ACCESS_KEY_ID": "",
    "RGW_SECRET_ACCESS_KEY": "",
    "ENDPOINT": ""
}

# 📌 환경 변수 기반 초기화 함수
def initialize_s3_argument():
    s3Argument["HOST"] = os.getenv("BUCKET_HOST", "")
    s3Argument["PORT"] = os.getenv("BUCKET_PORT", "")
    s3Argument["RGW_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "")
    s3Argument["RGW_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3Argument["ENDPOINT"] = f"http://{s3Argument['HOST']}:{s3Argument['PORT']}"
    printLog("INFO", f"S3 환경 초기화 완료: {s3Argument}")

initialize_s3_argument()

def s3_object_init(s3_mode):
    if s3_mode == "client":
        return boto3.client(
            "s3",
            endpoint_url=s3Argument["ENDPOINT"],
            aws_access_key_id=s3Argument["RGW_ACCESS_KEY_ID"],
            aws_secret_access_key=s3Argument["RGW_SECRET_ACCESS_KEY"]
        )
    elif s3_mode == "resource":
        return boto3.resource(
            "s3",
            endpoint_url=s3Argument["ENDPOINT"],
            aws_access_key_id=s3Argument["RGW_ACCESS_KEY_ID"],
            aws_secret_access_key=s3Argument["RGW_SECRET_ACCESS_KEY"]
        )

@app.route("/s3ApiChange", methods=["POST"])
def s3_api_chagne():

    #s3 = s3_object_init("resource")
    #parameter_ = request.args.to_dict(flat=True)
    #bucket_name = request.form["bucket"]
    parameter_ = request.form
    print(f"[s3_api_change] parameter_: {parameter_}", flush=True)
    
    # 필수 파라미터 체크
    required_fields = ["host", "port", "rgw_access_key_id", "rgw_secret_access_key"]
    for field in required_fields:
        if field not in parameter_:
            return jsonify({"error": f"Missing '{field}' parameter"}), 400

    try:
        # os.environ은 함수가 아니라 dict처럼 사용해야 합니다
        os.environ["BUCKET_HOST"] = parameter_.get("host")
        os.environ["BUCKET_PORT"] = parameter_.get("port")
        os.environ["AWS_ACCESS_KEY_ID"] = parameter_.get("rgw_access_key_id")
        os.environ["AWS_SECRET_ACCESS_KEY"] = parameter_.get("rgw_secret_access_key")
        
        initialize_s3_argument()

        return jsonify({"msg": "S3 API ENV Change Successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/s3Check", methods=["GET"])
def s3_now_connected():
    flag = False
    if HOST is None:
        flag = True
    elif PORT is None:
        flag = True
    elif RGW_ACCESS_KEY_ID is None:
        flag = True
    elif RGW_SECRET_ACCESS_KEY is None:
        flag = True
    elif endpoint is None:
        flag = True
    else:
        flag = False

    if flag:
        return jsonify({"msg":"no"}), 403
    else:
        return jsonify({"msg": "yes"}), 200
#####################################################################
#####################################################################
#####################################################################
UPLOAD_FOLDER = "nas_storage"  # 저장할 폴더 지정
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/listOfBuckets", methods=["GET"])
def listOfBucketsFunction():
    """
    Ceph RGW의 S3 API를 사용하여 버킷 목록을 가져오는 API
    """
    try:
        s3 = s3_object_init("client")
        # 버킷 목록 가져오기
        buckets = s3.list_buckets()
        return jsonify({
            "buckets": [bucket["Name"] for bucket in buckets.get("Buckets", [])]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test funcion
@app.route("/getEnv", methods=["GET"])
def getEnvFunction():
    return jsonify({
        "HOST": s3Argument["HOST"],
        "PORT": s3Argument["PORT"],
        "AccessKey": s3Argument["RGW_ACCESS_KEY_ID"],
        "AccessKey_Screts": s3Argument["RGW_SECRET_ACCESS_KEY"]
    })

#@app.route("/createBucket", methods=["POST"])
#def createBucketFunction():
#    # 요청에서 'name' 파라미터 가져오기
#    parameter_ = request.args.to_dict(flat=True)  # flat=True로 단일 값 가져오기
#    if "name" not in parameter_:
#        return jsonify({"error": "Missing 'name' parameter"}), 400
#
#    bucket_name = parameter_["name"]
#
#    try:
#        s3 = s3_object_init("client")
#        # S3 버킷 생성
#        s3.create_bucket(Bucket=bucket_name)
#
#        return jsonify({"message": f"Bucket '{bucket_name}' created successfully!"}), 200
#    except Exception as e:
#        return jsonify({"error": str(e)}), 500

@app.route("/getListOfBucketsItems", methods=["GET"])
def getListOfBucketsItemsFunction():
    s3 = s3_object_init("client")
    # S3 버킷 목록 가져오기
    buckets = s3.list_buckets()["Buckets"]

    all_items = []
    for bucket in buckets:
        bucket_name = bucket["Name"]

        # 해당 버킷의 객체 목록 가져오기
        objects = s3.list_objects_v2(Bucket=bucket_name)

        if "Contents" in objects:
            for obj in objects["Contents"]:
                item = {
                    "bucket": bucket_name,
                    "name": obj["Key"],
                    "size": obj["Size"],
                    "modified": obj["LastModified"].isoformat()
                }
                all_items.append(item)

    return jsonify(all_items)


def empty_bucket(bucket_name):
    """버킷 내 모든 객체 삭제"""
    try:
        s3 = s3_object_init("client")
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
        return True
    except Exception as e:
        return str(e)

#@app.route("/deleteBucket", methods=["DELETE"])
#def deleteBucketFunction():
#    s3 = s3_object_init("client")
#    
#    parameter_ = request.args.to_dict(flat=True)
#
#    if "name" not in parameter_:
#        return jsonify({"error": "Missing 'name' parameter"}), 400
#
#    bucket_name = parameter_["name"]
#
#    try:
#        # 버킷 내 모든 객체 삭제
#        empty_bucket_result = empty_bucket(bucket_name)
#        if empty_bucket_result is not True:
#            return jsonify({"error": empty_bucket_result}), 500
#
#        # 버킷 삭제
#        s3.delete_bucket(Bucket=bucket_name)
#        return jsonify({"message": f"Bucket '{bucket_name}' deleted successfully!"}), 200
#    except Exception as e:
#        return jsonify({"error": str(e)}), 500

@app.route("/getObjectContent", methods=["GET"])
def getObjectContentFunction():
    s3 = s3_object_init("resource")
    parameter_ = request.args.to_dict(flat=True)

    if "bucketName" not in parameter_:
        return jsonify({"error": "Missing 'bucketName' parameter"}), 400
    if "fileName" not in parameter_:
        return jsonify({"error": "Missing 'fileName' parameter"}), 400

    bucket_name = parameter_["bucketName"]
    file_name = parameter_["fileName"]

    try:
        object_content = {}

        obj = s3.Object(bucket_name, file_name)
        response = obj.get()
        data = response['Body'].read()
        object_content['Body']=str(data, 'utf-8')

        return jsonify(object_content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#@app.route("/createObject", methods=["POST"])
#def createObjectFunction():
#    s3 = s3_object_init("resource")
#    parameter_ = request.args.to_dict(flat=True)
#
#    if "bucketName" not in parameter_:
#        return jsonify({"error": "Missing 'bucketName' parameter"}), 400
#    if "fileName" not in parameter_:
#        return jsonify({"error": "Missing 'fileName' parameter"}), 400
#    if "fileContent" not in parameter_:
#        return jsonify({"error": "Missing 'fileContent' parameter"}), 400
#
#    bucket_name = parameter_["bucketName"]
#    file_name = parameter_["fileName"]
#    file_content = parameter_["fileContent"] 
#
#    try:
#        bucket = s3.Bucket(bucket_name)
#        bucket.put_object(Key=file_name, Body=file_content)
#
#        return jsonify({"message": f"Create Object Success"}), 200
#    except Exception as e:
#        return jsonify({"error": str(e)}), 500

@app.route("/createObject_v2", methods=["POST"])
def createObjectFunction_v2():
    s3 = s3_object_init("resource")

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if "bucket" not in request.form:
        return jsonify({"error": "No bucket part"}), 400
    bucket_name = request.form["bucket"]
    if bucket_name == "":
        return jsonify({"error": "No selected bucket"}), 400

    try:
        bucket = s3.Bucket(bucket_name)
        bucket.put_object(Key=file.filename, Body=file)

        return jsonify({"message": f"Create Object Success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getDownloadObject", methods=["POST"])
def donwloadObjectFunction():
    s3 = s3_object_init("client")
    if "bucket" not in request.form:
        return jsonify({"error": "No select bucket"}), 400
    bucket_name = request.form["bucket"]
    if bucket_name == "":
        return jsonify({"error": "empty bucket_name"}), 400

    if "obj" not in request.form:
        return jsonify({"error": "No select object"}), 400
    obj_name = request.form["obj"]
    if obj_name == "":
        return jsonify({"error": "No select object"}), 400

    try:
        print('downloadObject')

        download_link = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    'Bucket': bucket_name,
                    'Key': obj_name,
                    },
                ExpiresIn=30
                #ExpiresIn=datetime.timedelta(seconds=30)
                );
        print("Create Download Link URL Success!!")

        #return jsonify({"message": f"Test Message: Download Object"}), 200
        return jsonify({"link": download_link}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/deleteObject", methods=["DELETE"])
def delete_object_function():
    s3 = s3_object_init("client")
    if "bucket" not in request.form:
        return jsonify({"error": "No select bucket"}), 400
    bucket_name = request.form["bucket"]
    if bucket_name == "":
        return jsonify({"error": "empty bucket_name"}), 400

    if "obj" not in request.form:
        return jsonify({"error": "No select object"}), 400
    obj_name = request.form["obj"]
    if obj_name == "":
        return jsonify({"error": "No select object"}), 400

    try:
        response = s3.delete_object(
                Bucket=bucket_name,
                Key=obj_name,
                )
        
        return jsonify({"result": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/createNewBucket", methods=["POST"])
def create_new_bucket_function():
    s3 = s3_object_init("client")
    if "newBucket" not in request.form:
        return jsonify({"error": "No input new bucket name"}), 400
    new_bucket_name = request.form["newBucket"]
    if new_bucket_name == "":
        return jsonify({"error": "empty new bucket name"}), 400

    if not new_bucket_name.islower():
        return jsonify({"error": "Bucket names cannot contain uppercase letters"}), 400

    try:
        response = s3.create_bucket(
                Bucket=new_bucket_name,
                )
        print('new Bucket name: ', new_bucket_name)
        print('response: ', response)
        return jsonify({"result": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/selectObjectPreviewContent", methods=["POST"])
def select_object_preview_content_function():
    s3 = s3_object_init("client")

    if "bucket" not in request.form:
        return jsonify({"error": "No select bucket"}), 400
    bucket_name = request.form["bucket"]
    if bucket_name == "":
        return jsonify({"error": "empty bucket_name"}), 400

    if "obj" not in request.form:
        return jsonify({"error": "No select object"}), 400
    obj_name = request.form["obj"]
    if obj_name == "":
        return jsonify({"error": "No select object"}), 400

    try:
        response = s3.get_object(Bucket=bucket_name, Key=obj_name)
        file_content = response["Body"].read().decode("utf-8")
        return jsonify({"content": file_content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/deleteBucket", methods=["DELETE"])
def deleteBucketFunction():
    s3 = s3_object_init("client")

    if "bucket" not in request.form:
        return jsonify({"error": "No select bucket"}), 400
    bucket_name = request.form["bucket"]
    if bucket_name == "":
        return jsonify({"error": "empty bucket_name"}), 400

    try:
        # 버킷 내 모든 객체 삭제
        empty_bucket_result = empty_bucket(bucket_name)
        if empty_bucket_result is not True:
            return jsonify({"error": "Failed clear in bucket"}), 500

        # 버킷 삭제
        s3.delete_bucket(Bucket=bucket_name)
        return jsonify({"message": f"Bucket '{bucket_name}' deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#==================================================
#==================================================

#@app.route("/pushContainerImage", methods=["POST"])
#def push_container_image_function():
    

if __name__ == '__main__':
    app.run()

