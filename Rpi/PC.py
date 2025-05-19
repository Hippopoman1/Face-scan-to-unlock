import face_recognition as face
import numpy as np
import cv2
import requests
import json
import time
import threading
from mock_gpio import GPIO
import logging
from flask import Flask, request, jsonify

logging.basicConfig(
    filename="system.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# === CONFIG ===
RELAY_PIN = 17
DEVICE_ID = 2
API_BASE_URL = "http://192.168.0.104:8000/api"

# User Token ที่ได้รับมาจาก Django REST (ต้องขอ token จาก /api-token-auth/ ก่อน)
API_AUTH_TOKEN = "69046e79dbf663ac70876fea57bb07e8bab0daf9"

# === GPIO SETUP ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)

relay_lock = threading.Lock()
swit_event = threading.Event()

cached_faces = {
    "encodings": [],
    "names": [],
    "emails": [],
    "rooms": []
}

# === FLASK SETUP ===
app = Flask(__name__)

@app.route('/refresh_faces', methods=['POST'])
def refresh_faces():
    logging.info("\ud83d\udd04 รับคำสั่งจาก Mobile ให้โหลดใบหน้าใหม่")
    enc, nam, ema, roo = get_known_faces_from_api()
    cached_faces["encodings"] = enc
    cached_faces["names"] = nam
    cached_faces["emails"] = ema
    cached_faces["rooms"] = roo
    return jsonify({"status": "ok", "message": "face data refreshed"}), 200

@app.route('/refresh_swit', methods=['POST'])
def refresh_swit():
    logging.info("🔄 รับคำสั่งจาก Mobile ให้โหลดข้อมูล Switch ใหม่")
    swit_event.set()  # ✅ สั่งให้ Thread swit_control() ทำงาน
    return jsonify({"status": "ok", "message": "Switch data refresh requested"}), 200

def run_flask_server():
    app.run(host='0.0.0.0', port=9000)

# === ฟังก์ชันรวม Header Token ===
def get_auth_headers():
    return {
        "Authorization": f"Token {API_AUTH_TOKEN}"
    }

# === ฟังก์ชันบันทึก Log ผ่าน API ===
def log_access_to_api(id_student, name, email, access_status, room_name):
    api_url = f"{API_BASE_URL}/access-logs/"
    log_data = {
        "id_student": id_student,
        "name": name,
        "email": email,
        "access_status": access_status,
        "access_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "room_name": room_name,
    }

    try:
        response = requests.post(api_url, json=log_data, headers=get_auth_headers())
        if response.status_code == 201:
            print("Log saved successfully:", response.json())
        else:
            print(f"Failed to save log: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")

# === ฟังก์ชันดึงข้อมูล User จาก API ===
def get_users_from_api():
    api_url = f"{API_BASE_URL}/users/"
    try:
        response = requests.get(api_url, headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            user_mapping = {user["email"]: user for user in data}
            return user_mapping
        else:
            print(f"Failed to fetch users: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return {}

# === ฟังก์ชันดึงข้อมูลใบหน้าที่รู้จักจาก API ===
def get_known_faces_from_api():
    api_url = f"{API_BASE_URL}/access-controls"
    try:
        response = requests.get(api_url, headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            known_face_encodings = []
            known_face_names = []
            known_face_emails = []
            known_face_room_name = []

            for item in data:
                if item.get("device") != DEVICE_ID:
                    continue

                if not item["face_encoding"]:
                    print(f"Skipping user {item.get('name', 'Unknown')} due to missing face_encoding")
                    continue

                known_face_encodings.append(np.array(json.loads(item["face_encoding"])))
                known_face_names.append(item["name"])
                known_face_emails.append(item["email"])
                known_face_room_name.append(item["room_name"])

            return known_face_encodings, known_face_names, known_face_emails, known_face_room_name
        else:
            print(f"Failed to fetch face encodings: {response.status_code}")
            return [], [], [], []
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return [], [], [], []

# === ฟังก์ชันดึงสถานะ swit จาก API ===
def get_swit_status_from_api():
    api_url = f"{API_BASE_URL}/access-controls/"
    try:
        response = requests.get(api_url, headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            logging.info("✅ ดึงข้อมูล Switch สำเร็จจาก API.")
            for item in data:
                if item.get("device") == DEVICE_ID:
                    swit_status = item.get("swit", "0")
                    name = item.get("name", "Unknown")
                    email = item.get("email", "Unknown")
                    room_name = item.get("room_name", "Unknown")
                    return swit_status, name, email, room_name
        else:
            logging.error(f"⚠️ ไม่สามารถดึงข้อมูล Switch ได้: {response.status_code}")
            return None, None, None, None
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ Error connecting to API: {e}")
        return None, None, None, None

# === ฟังก์ชันแสดงผลหน้าจอ ===
def draw_face_info(frame, face_locations, face_names, face_percent):
    for (top, right, bottom, left), name, percent in zip(face_locations, face_names, face_percent):
        top *= 2; right *= 2; bottom *= 2; left *= 2
        color = [46, 2, 209] if name == "UNKNOWN" else [255, 102, 51]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, top - 6), font, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"MATCH: {percent}%", (left + 6, bottom + 23), font, 0.6, (255, 255, 255), 1)
    return frame

# === THREAD: Face Recognition Control ===
def face_recognition_control():
    global video_capture
    while True:
        ret, frame = video_capture.read()
        

        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            smoothed_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
            equalized_frame = cv2.equalizeHist(smoothed_frame)
            rgb_small_frame = cv2.cvtColor(equalized_frame, cv2.COLOR_GRAY2RGB)

            face_locations = face.face_locations(rgb_small_frame, model="hog")
            face_encodings = face.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            face_percent = []

            for face_encoding in face_encodings:
                matches = face.compare_faces(cached_faces["encodings"], face_encoding, tolerance=0.4)
                face_distances = face.face_distance(cached_faces["encodings"], face_encoding)
                
                best_match_index = np.argmin(face_distances)
                
                percent = (1 - face_distances[best_match_index]) * 100
                matched_name = cached_faces["names"][best_match_index]
                print(f"✅ Best Match Index: {best_match_index}, Name: {matched_name}, Percent: {percent:.2f}%")

                if matches[best_match_index] and percent >= 70:
                    name = cached_faces["names"][best_match_index]
                    email = cached_faces["emails"][best_match_index]
                    room_name = cached_faces["rooms"][best_match_index]


                    user = users.get(email)
                    if user:
                        id_student = user["id_student"]
                        print(f"จับคู่ใบหน้าสำเร็จ: {name} (ID: {id_student})")

                        with relay_lock:
                            log_access_to_api(
                                id_student=id_student,
                                name=name,
                                email=email,
                                access_status="in",
                                room_name=room_name,
                            )

                            GPIO.output(RELAY_PIN, GPIO.LOW)
                            logging.info("Relay ปิด (จาก สแกน)")
                            video_capture.release()
                            time.sleep(1)
                            GPIO.output(RELAY_PIN, GPIO.HIGH)
                            logging.info("Relay เปิด (จาก สแกน)")
                            video_capture = cv2.VideoCapture(0)

                    face_names.append(name)
                    face_percent.append(round((1 - face_distances[best_match_index]) * 100, 2))
                else:
                    face_names.append("UNKNOWN")
                    face_percent.append(0)

            frame = draw_face_info(frame, face_locations, face_names, face_percent)
            cv2.imshow("Video", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

# === THREAD: Swit Control ===
def swit_control():
    previous_swit_status = None
    while True:
        swit_event.wait()  # ✅ รอคำสั่งให้ทำงาน
        try:
            swit_status, name, email, room_name = get_swit_status_from_api()
            if swit_status is None:
                logging.error("❌ ไม่สามารถดึงข้อมูล Switch ได้")
                swit_event.clear()
                continue

            logging.info(f"✅ ได้สถานะ Switch: {swit_status}")
            if swit_status != previous_swit_status:
                previous_swit_status = swit_status

                with relay_lock:
                    if swit_status == "1":
                        GPIO.output(RELAY_PIN, GPIO.HIGH)
                        logging.info("Relay เปิด (จาก swit)")

                        # ✅ บันทึก Log เฉพาะเมื่อเปิด
                        user = users.get(email)
                        if user:
                            id_student = user.get("id_student", "Unknown")
                            log_access_to_api(
                                id_student=id_student,
                                name=name,
                                email=email,
                                access_status="in",  # ✅ Log เฉพาะตอนเปิด
                                room_name=room_name,
                            )
                    else:
                        GPIO.output(RELAY_PIN, GPIO.LOW)
                        logging.info("Relay ปิด (จาก swit)")

        except Exception as e:
            logging.error(f"⚠️ Error in swit_control: {e}")
        
        swit_event.clear()  # ✅ รอคำสั่งใหม่


# === Main ===
users = get_users_from_api()
cached_faces["encodings"], cached_faces["names"], cached_faces["emails"], cached_faces["rooms"] = get_known_faces_from_api()


if not cached_faces["encodings"]:
    print("No known faces loaded. Exiting...")
    

video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    exit()

try:
    face_thread = threading.Thread(target=face_recognition_control, daemon=True)
    swit_thread = threading.Thread(target=swit_control, daemon=True)
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)

    face_thread.start()
    swit_thread.start()
    flask_thread.start()

    logging.info("System started successfully.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    logging.info("Program terminated by user.")
finally:
    video_capture.release()
    GPIO.cleanup()
    logging.info("Resources cleaned up. Program exited.")
