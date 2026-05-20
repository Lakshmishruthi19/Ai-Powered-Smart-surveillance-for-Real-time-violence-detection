import os
import cv2
import json
import datetime
import sqlite3
import threading
import requests   # TELEGRAM ALERT
from flask import Flask, render_template, Response, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from ultralytics import YOLO
from plyer import notification
from twilio.rest import Client
from pygame import mixer
import pyttsx3
from flask import send_file

app = Flask(__name__)
app.secret_key = 'vigilant_ai_secret_key'

# ---------------- GLOBAL USER PHONE ----------------

current_user_phone = None
current_user_telegram = None

# ---------------- ALARM SETUP ----------------

mixer.init()

try:
    siren_sound = mixer.Sound("siren.wav")
except:
    print("⚠ siren.wav not found")
    siren_sound = None

# ---------------- VOICE ALERT ----------------

engine = pyttsx3.init()
engine.setProperty('rate',150)

# ---------------- TWILIO SETUP ----------------

TWILIO_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE = "+1234567890"

# ---------------- TELEGRAM SETUP ----------------

BOT_TOKEN = "8707503285:AAHunNaRXAU4W1s61ybMyOduU82xyA6oJ9U"

# ---------------- DATABASE ----------------

def init_db():

    conn = sqlite3.connect('cameras.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cameras(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        ip_address TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users_db = {
    "admin@vigilant.ai":{
        "password":"password123",
        "phone":"+91XXXXXXXXXX",
        "telegram_chat_id":"123456789"
    }
}

class User(UserMixin):

    def __init__(self,id):
        self.id=id
        self.phone=None

@login_manager.user_loader
def load_user(user_id):

    if user_id in users_db:
        user=User(user_id)
        user.phone=users_db[user_id]["phone"]
        return user

    return None

# ---------------- AI MODEL ----------------

MODEL_PATH = "runs/detect/train/weights/best.pt"
ALERTS_FILE = "detections.json"

if os.path.exists(MODEL_PATH):

    model = YOLO(MODEL_PATH)
    print("Model Loaded")

else:

    print("Model not found")
    model=None

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/features')
def features():
    return render_template("features.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")
@app.route('/demo-video')
def demo_video():
    return send_file("static/output_demo_video.mp4", mimetype='video/mp4')

# ---------------- LOGIN ----------------

@app.route('/login',methods=["GET","POST"])
def login():

    global current_user_phone, current_user_telegram

    if request.method=="POST":

        email=request.form.get("email")
        password=request.form.get("password")

        if email in users_db and users_db[email]["password"]==password:

            user=User(email)
            user.phone=users_db[email]["phone"]

            login_user(user)

            current_user_phone=user.phone
            current_user_telegram = users_db[email]['telegram_chat_id']

            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

# ---------------- SIGNUP ----------------

@app.route('/signup',methods=["GET","POST"])
def signup():

    global current_user_phone,current_user_telegram

    if request.method=="POST":

        email=request.form.get("email")
        password=request.form.get("password")
        phone=request.form.get("phone")
        telegram_id=request.form.get("telegram_chat_id")

        users_db[email]={
            "password":password,
            "phone":phone,
            "telegram_chat_id":telegram_id
        }

        user=User(email)
        user.phone=phone

        login_user(user)

        current_user_phone=phone
        current_user_telegram=telegram_id

        return redirect(url_for("dashboard"))

    return render_template("signup.html")

# ---------------- LOGOUT ----------------

@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(url_for("index"))

# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
@login_required
def dashboard():

    alerts=[]

    if os.path.exists(ALERTS_FILE):

        try:
            with open(ALERTS_FILE,"r") as f:
                alerts=json.load(f)
        except:
            pass

    conn=sqlite3.connect("cameras.db")
    cursor=conn.cursor()

    cursor.execute("SELECT id,name,ip_address,status FROM cameras")

    cameras=cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        name=current_user.id,
        alerts=alerts[-10:],
        cameras=cameras
    )

# ---------------- ADD CAMERA ----------------

@app.route('/add_camera',methods=["POST"])
@login_required
def add_camera():

    name = request.form.get("name")
    ip = request.form.get("ip")

    # Try opening camera
    cap = cv2.VideoCapture(ip)

    if not cap.isOpened():
        flash("❌ Camera not reachable. Enter valid IP")
        return redirect(url_for("dashboard"))

    ret, frame = cap.read()
    cap.release()

    if not ret:
        flash("❌ Camera stream failed")
        return redirect(url_for("dashboard"))

    # Save camera only if working
    conn = sqlite3.connect("cameras.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cameras (name,ip_address) VALUES (?,?)",
        (name,ip)
    )

    conn.commit()
    conn.close()

    flash("✅ Camera added successfully")

    return redirect(url_for("dashboard"))

# ---------------- SMS ALERT ----------------

def send_sms_alert(camera):

    global current_user_phone

    try:

        if not current_user_phone:
            return

        client=Client(TWILIO_SID,TWILIO_AUTH_TOKEN)

        client.messages.create(
            body=f"🚨 Violence detected at {camera}",
            from_=TWILIO_PHONE,
            to=current_user_phone
        )

        print("SMS sent")

    except Exception as e:

        print("SMS failed:",e)

# ---------------- TELEGRAM ALERT ----------------

def send_telegram_alert(camera, frame):

    global current_user_telegram

    try:

        if not current_user_telegram:
            print("No Telegram chat ID found")
            return

        message = f"🚨 Violence detected at {camera}"

        # -------- SEND TEXT MESSAGE --------
        url_message = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data_message = {
            "chat_id": current_user_telegram,
            "text": message
        }

        requests.post(url_message, data=data_message)

        # -------- SEND PHOTO --------
        image_path = "alert.jpg"
        cv2.imwrite(image_path, frame)

        url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        files = {
            "photo": open(image_path, "rb")
        }

        data_photo = {
            "chat_id": current_user_telegram
        }

        requests.post(url_photo, data=data_photo, files=files)

        print("Telegram message and photo sent")

    except Exception as e:
        print("Telegram failed:", e)

# ---------------- NOTIFICATION ----------------

def show_notification():

    try:
        notification.notify(
            title="Violence Alert",
            message="Violence detected on camera",
            timeout=5
        )

    except:
        pass


def clahe_enhancement(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    merged = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    return enhanced

# ---------------- FRAME GENERATOR ----------------

def gen_frames(source, camera_name):

    cap = cv2.VideoCapture(source)

    last_status = "Non-Violence"
    violence_counter = 0
    frame_count = 0
    violence_conf = 0

    while True:

        success, frame = cap.read()

        if not success:
            break
      

        frame_count += 1

        annotated_frame = frame.copy()
        violence_detected = False

        # -------- SKIP FRAMES FOR PERFORMANCE --------
        if frame_count % 3 != 0:

            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            continue

        # -------- YOLO DETECTION --------
        if model:
  
             frame = cv2.resize(frame, (640, 480))
             frame = clahe_enhancement(frame)

             results = model(frame, conf=0.8)

             for r in results:

                for box in r.boxes:

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    width = x2 - x1
                    height = y2 - y1

                    # Ignore very small boxes (reduces false detection)
                    if width < 80 or height < 80:
                        continue

                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])

                    label = model.names[cls_id]

                    is_violence = label.lower() == "violence"

                    color = (0,0,255) if is_violence else (0,255,0)

                    # -------- DRAW BOX --------
                    cv2.rectangle(
                        annotated_frame,
                        (x1,y1),
                        (x2,y2),
                        color,
                        2
                    )

                    # -------- LABEL --------
                    cv2.putText(
                        annotated_frame,
                        f"{label} {conf:.2f}",
                        (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )

                    # -------- VIOLENCE CHECK --------
                    if is_violence:
                        violence_counter += 1
                        violence_conf = conf
                    else:
                        violence_counter = 0

                    # Require multiple frames to confirm violence
                    if violence_counter >= 3:
                        violence_detected = True

        # -------- ALERT TRIGGER --------
        if violence_detected:

            if last_status != "Violence":

                save_alert(camera_name, violence_conf, "Violence")

                send_sms_alert(camera_name)

                threading.Thread(
                    target=send_telegram_alert,
                    args=(camera_name, annotated_frame)
                ).start()

                if siren_sound:
                    siren_sound.play()

                threading.Thread(target=show_notification).start()

                def speak():
                    engine.say("Warning violence detected")
                    engine.runAndWait()

                threading.Thread(target=speak).start()

                last_status = "Violence"

        else:
            last_status = "Non-Violence"

        # -------- STREAM FRAME --------
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

# ---------------- ALERT STORAGE ----------------

def save_alert(camera,conf,status):

    new_alert={
        "camera":camera,
        "time":datetime.datetime.now().strftime("%H:%M:%S"),
        "confidence":conf,
        "status":status
    }

    alerts=[]

    if os.path.exists(ALERTS_FILE):

        try:
            with open(ALERTS_FILE,"r") as f:
                alerts=json.load(f)
        except:
            pass

    alerts.append(new_alert)

    with open(ALERTS_FILE,"w") as f:
        json.dump(alerts[-10:],f,indent=2)

# ---------------- VIDEO FEED ----------------

@app.route('/video_feed')
@login_required
def video_feed():

    return Response(
        gen_frames(0, "Webcam"),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# MULTI CAMERA FIX

@app.route('/video_feed/<camera_name>')
@login_required
def video_feed_multiple(camera_name):

    conn=sqlite3.connect("cameras.db")
    cursor=conn.cursor()

    cursor.execute(
        "SELECT ip_address FROM cameras WHERE name=?",
        (camera_name,)
    )

    camera=cursor.fetchone()

    conn.close()

    if not camera:
        return "Camera not found",404

    return Response(
        gen_frames(camera[0], camera_name),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ---------------- RUN APP ----------------

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True
    )