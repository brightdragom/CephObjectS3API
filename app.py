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

#####################################################################
#####################################################################
#####################################################################
# 환경 변수에서 AWS S3 정보 가져오기
HOST = os.getenv("BUCKET_HOST")
PORT = os.getenv("BUCKET_PORT")
RGW_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
RGW_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint="http://{}:{}".format(HOST, PORT)

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=RGW_ACCESS_KEY_ID,
    aws_secret_access_key=RGW_SECRET_ACCESS_KEY
)
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
        "HOST": HOST,
        "PORT": PORT,
        "AccessKey": RGW_ACCESS_KEY_ID,
        "AccessKey_Screts": RGW_SECRET_ACCESS_KEY
    })

@app.route("/createBucket", methods=["POST"])
def createBucketFunction():
    # 요청에서 'name' 파라미터 가져오기
    parameter_ = request.args.to_dict(flat=True)  # flat=True로 단일 값 가져오기
    if "name" not in parameter_:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    bucket_name = parameter_["name"]

    try:
        # S3 버킷 생성
        s3.create_bucket(Bucket=bucket_name)

        return jsonify({"message": f"Bucket '{bucket_name}' created successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getListOfBucketsItems", methods=["GET"])
def getListOfBucketsItemsFunction():
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
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3.delete_object(Bucket=bucket_name, Key=obj["Key"])
        return True
    except Exception as e:
        return str(e)

@app.route("/deleteBucket", methods=["DELETE"])
def deleteBucketFunction():
    parameter_ = request.args.to_dict(flat=True)

    if "name" not in parameter_:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    bucket_name = parameter_["name"]

    try:
        # 버킷 내 모든 객체 삭제
        empty_bucket_result = empty_bucket(bucket_name)
        if empty_bucket_result is not True:
            return jsonify({"error": empty_bucket_result}), 500

        # 버킷 삭제
        s3.delete_bucket(Bucket=bucket_name)
        return jsonify({"message": f"Bucket '{bucket_name}' deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getObjectContent", methods=["GET"])
def getObjectContentFunction():
    parameter_ = request.args.to_dict(flat=True)

    if "bucketName" not in parameter_:
        return jsonify({"error": "Missing 'bucketName' parameter"}), 400
    if "fileName" not in parameter_:
        return jsonify({"error": "Missing 'fileName' parameter"}), 400

    bucket_name = parameter_["bucketName"]
    file_name = parameter_["fileName"]

    try:
        object_content = {}

        local_s3 = boto3.resource(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=RGW_ACCESS_KEY_ID,
                aws_secret_access_key=RGW_SECRET_ACCESS_KEY
                )

        #boto3.resource.Object($Bucketanme, $key)
        obj = local_s3.Object(bucket_name, file_name)
        response = obj.get()
        data = response['Body'].read()
        object_content['Body']=str(data, 'utf-8')

        return jsonify(object_content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/createObject", methods=["POST"])
def createObjectFunction():

    parameter_ = request.args.to_dict(flat=True)

    if "bucketName" not in parameter_:
        return jsonify({"error": "Missing 'bucketName' parameter"}), 400
    if "fileName" not in parameter_:
        return jsonify({"error": "Missing 'fileName' parameter"}), 400
    if "fileContent" not in parameter_:
        return jsonify({"error": "Missing 'fileContent' parameter"}), 400

    bucket_name = parameter_["bucketName"]
    file_name = parameter_["fileName"]
    file_content = parameter_["fileContent"] # 수정 및 코드 업데이트 필요! -> 현재 전달받은 값밖게안됨, 파일등으로 바꾸기위해선 해당 내용도 수용가능하도록 바꿔야

    try:
        local_s3 = boto3.resource(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=RGW_ACCESS_KEY_ID,
            aws_secret_access_key=RGW_SECRET_ACCESS_KEY
        )
        bucket = local_s3.Bucket(bucket_name)
        bucket.put_object(Key=file_name, Body=file_content)

        return jsonify({"message": f"Create Object Success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# react web ui test
@app.route("/createObject_v2", methods=["POST"])
#@app.route("/upload", methods=["POST"])
def createObjectFunction_v2():

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

    #filename = secure_filename(file.filename)  # 보안 처리된 파일 이름 사용
    #file.save(os.path.join(UPLOAD_FOLDER, filename))
    #return jsonify({"message": "File uploaded successfully", "filename": filename}), 201
    try:
        local_s3 = boto3.resource(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=RGW_ACCESS_KEY_ID,
            aws_secret_access_key=RGW_SECRET_ACCESS_KEY
        )
        # bucket = local_s3.Bucket(bucket_name)
        # bucket = local_s3.Bucket("keti-rgw-bucket-newbucket")
        print('bucketname: ', bucket_name)   # 10.0.0.254 - - [28/Feb/2025 09:00:36] "POST /createObject_v2 HTTP/1.1" 404 - 해결 해야됨 2025 02 28
        bucket = local_s3.Bucket(bucket_name)
        bucket.put_object(Key=file.filename, Body=file)

        return jsonify({"message": f"Create Object Success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getDownloadObject", methods=["POST"])
def donwloadObjectFunction():
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



if __name__ == '__main__':
    app.run()

