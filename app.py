from flask import Flask, jsonify, request
import os
import boto3
app = Flask(__name__)

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


@app.route("/list_buckets", methods=["GET"])
def list_buckets():
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

# 의도처럼 동작 X, 아직 미완성 Function
@app.route("/getObjectContent", methods=["GET"])
def getObjectContentFunction():
    object_content = s3.select_object_content(Bucket="keti-rgw-bucket-newbucket3", key="rookObj")

    print("object_content: ", object_content)
    return object_content

@app.route("/createObject", methods=["POST"])
def createObjectFunction():
    #alert("This Function is createObjectFunction")
    
    return 200

if __name__ == '__main__':
    app.run()

