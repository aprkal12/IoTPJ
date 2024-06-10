from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Flask 애플리케이션 생성
app = Flask(__name__)

# Firebase 설정
try:
    # 서비스 계정 키 파일의 경로
    cred_path = "iotpj-b5968-firebase-adminsdk-ito8f-7eceec2f32.json"
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Service account key file not found at: {cred_path}")
    
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iotpj-b5968.firebaseio.com'
    })
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# Firestore 리스너 설정
db = firestore.client()
data_list = []

def on_snapshot(doc_snapshot, changes, read_time):
    global data_list
    data_list = []
    for doc in doc_snapshot:
        data_list.append(doc.to_dict())
    print("Received document snapshot: ", data_list)

col_query = db.collection('sensor_data')
col_query.on_snapshot(on_snapshot)

@app.route('/')
def index():
    return render_template('index.html', data=data_list)

@app.route('/get_data')
def get_data():
    return jsonify(data_list)

if __name__ == '__main__':
    app.run('0.0.0.0', port=12220)
