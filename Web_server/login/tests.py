import face_recognition as face
import numpy as np
import cv2
import requests
import json
import time
import lgpio

relay_active = False  # ตัวแปรสถานะของรีเลย์

# ตั้งค่า GPIO
RELAY_PIN = 17
h = lgpio.gpiochip_open(0)  # เปิด gpiochip 0
lgpio.gpio_claim_output(h, RELAY_PIN)  # ตั้งค่า PIN เป็น Output
lgpio.gpio_write(h, RELAY_PIN, 0)  # ตั้งค่าเริ่มต้น LOW

# กำหนดค่า Device ID
DEVICE_ID = 28

# ฟังก์ชันบันทึก Log ผ่าน API
def log_access_to_api(id_student, name, email, access_status, room_name):
    api_url = "http://192.168.0.110:8000/api/access-logs/"
    log_data = {
        "id_student": id_student,
        "name": name,
        "email": email,
        "access_status": access_status,
        "access_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "room_name": room_name,
    }

    try:
        response = requests.post(api_url, json=log_data)
        if response.status_code == 201:
            print("Log saved successfully:", response.json())
        else:
            print(f"Failed to save log: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")

# ฟังก์ชันดึงข้อมูล User และใบหน้า
def get_users_from_api():
    api_url = "http://192.168.0.110:8000/api/users/"
    try:
        response = requests.get(api_url)
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

# ฟังก์ชันดึงข้อมูลใบหน้าที่รู้จักจาก API
def get_known_faces_from_api():
    api_url = "http://192.168.0.110:8000/api/access-controls/"
    try:
        response = requests.get(api_url)
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

# ฟังก์ชันสำหรับแสดงข้อมูลบนหน้าจอ
def draw_face_info(frame, face_locations, face_names, face_percent):
    for (top, right, bottom, left), name, percent in zip(face_locations, face_names, face_percent):
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        color = [46, 2, 209] if name == "UNKNOWN" else [255, 102, 51]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left - 1, top - 30), (right + 1, top), color, cv2.FILLED)
        cv2.rectangle(frame, (left - 1, bottom), (right + 1, bottom + 30), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, top - 6), font, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"MATCH: {name} {percent}%", (left + 6, bottom + 23), font, 0.6, (255, 255, 255), 1)
    return frame

# โหลดข้อมูล User และใบหน้า
users = get_users_from_api()
known_face_encodings, known_face_names, known_face_emails, known_face_room_name = get_known_faces_from_api()

if not known_face_encodings:
    print("No known faces loaded. Exiting...")
    exit()

# เปิดใช้งานกล้อง
video_capture = cv2.VideoCapture(1)
if not video_capture.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    exit()

RELAY_ACTIVATION_DURATION = 5  # Duration of relay activation
frame_skip_count = 0
FRAME_SKIP_PERIOD = 30
    
try:
    while True:
        if frame_skip_count > 0:
            frame_skip_count -= 1
            time.sleep(0.1)
            continue
        # ข้ามการตรวจจับหากรีเลย์กำลังเปิด
        

        ret, frame = video_capture.read()
        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face.face_locations(rgb_small_frame, model="hog")
            face_encodings = face.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            face_percent = []

            for face_encoding in face_encodings:
                matches = face.compare_faces(known_face_encodings, face_encoding, tolerance=0.3)
                face_distances = face.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index] and (1 - face_distances[best_match_index]) >= 0.4:
                    name = known_face_names[best_match_index]
                    email = known_face_emails[best_match_index]
                    room_name = known_face_room_name[best_match_index]

                    user = users.get(email)
                    if user:
                        id_student = user["id_student"]
                        print(f"จับคู่ใบหน้าสำเร็จ: {name} (ID: {id_student})")

                        # บันทึก Log
                        log_access_to_api(id_student, name, email, "in", room_name)
                        relay_active = True
                        lgpio.gpio_write(h, RELAY_PIN, 0)
                        print("Relay ปิด")
                        time.sleep(5)
                        lgpio.gpio_write(h, RELAY_PIN, 1)
                        print("Relay เปิด")
                        relay_active = False
                        
                        # Set frame skip count after relay activation
                        frame_skip_count = FRAME_SKIP_PERIOD
                        break

                    face_names.append(name)
                    face_percent.append(round((1 - face_distances[best_match_index]) * 100, 2))
                else:
                    face_names.append("UNKNOWN")
                    face_percent.append(0)

            frame = draw_face_info(frame, face_locations, face_names, face_percent)
            cv2.imshow("Video", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

except KeyboardInterrupt:
    print("โปรแกรมหยุดการทำงาน")

finally:
    video_capture.release()
    cv2.destroyAllWindows()
    lgpio.gpiochip_close(h)
