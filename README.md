# Ceph RGW S3 API with Flask

This project provides a Flask-based API to interact with Ceph RGW's S3-compatible storage.

## 🚀 Features
- **List Buckets**: Retrieve a list of all available buckets.
- **Create Bucket**: Create a new S3 bucket.
- **Delete Bucket**: Delete a specified bucket (including its objects).
- **List Bucket Items**: Retrieve all objects stored in all available buckets.
- **Get Environment Variables**: Retrieve the configured S3 credentials and endpoint.
- **Retrieve Object Content**: Fetch the content of a specified object.

---

## 📌 Requirements
- **Python 3.8+**
- **Flask**
- **Boto3** (AWS SDK for Python)
- **Ceph RGW configured with S3 API**

---

## 🔧 Installation
### 1️⃣ Clone the Repository
```bash
git clone <repository_url>
cd <project_directory>
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Set Environment Variables
```bash
export BUCKET_HOST="<Your_Ceph_RGW_Host>"
export BUCKET_PORT="<Your_Ceph_RGW_Port>"
export AWS_ACCESS_KEY_ID="<Your_AWS_Access_Key>"
export AWS_SECRET_ACCESS_KEY="<Your_AWS_Secret_Key>"
```

---

## 🚀 Running the Application
```bash
python app.py
```
The Flask application will start at `http://127.0.0.1:5000/`

---

## 📢 API Endpoints

### **1️⃣ List All Buckets**
- **Endpoint:** `GET /list_buckets`
- **Example Response:**
```json
{
    "buckets": ["bucket1", "bucket2", "bucket3"]
}
```

### **2️⃣ Create a New Bucket**
- **Endpoint:** `POST /createBucket?name=<bucket_name>`
- **Example Response:**
```json
{
    "message": "Bucket '<bucket_name>' created successfully!"
}
```

### **3️⃣ Delete a Bucket**
- **Endpoint:** `DELETE /deleteBucket?name=<bucket_name>`
- **Example Response:**
```json
{
    "message": "Bucket '<bucket_name>' deleted successfully!"
}
```

### **4️⃣ List All Objects in Buckets**
- **Endpoint:** `GET /list_buckets_items`
- **Example Response:**
```json
[
    {
        "bucket": "bucket1",
        "name": "file1.txt",
        "size": 1024,
        "modified": "2024-02-24T12:00:00Z"
    }
]
```

### **5️⃣ Retrieve S3 Configuration Details**
- **Endpoint:** `GET /getEnv`
- **Example Response:**
```json
{
    "HOST": "your-host",
    "PORT": "your-port",
    "AccessKey": "your-access-key",
    "AccessKey_Secrets": "your-secret-key"
}
```

### **6️⃣ Retrieve Object Content**
- **Endpoint:** `GET /get_object_content`
- **Example Response:**
```json
{
    "object_content": "data from the object"
}
```

---

## 🛠 Troubleshooting
### **Invalid Endpoint Error**
If you encounter the error:
```
ValueError: Invalid endpoint: http://"10.0.2.190":"30910"
```
Ensure your `BUCKET_HOST` and `BUCKET_PORT` environment variables are correctly formatted:
```bash
export BUCKET_HOST="10.0.2.190"
export BUCKET_PORT="30910"
```

---

## 📜 License
This project is licensed under the **MIT License**.

---


