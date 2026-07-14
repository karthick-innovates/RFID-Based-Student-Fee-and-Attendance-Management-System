from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient("mongodb://localhost:27017/")
db = client['studentdb']
scans_collection = db['scans']

# Global variable to store last UID scanned
last_scanned_uid = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan():
    global last_scanned_uid
    data = request.get_json()
    uid = data.get('uid')
    if uid:
        last_scanned_uid = uid
        print("Scanned UID:", uid)
        return jsonify({'status': 'received'})
    return jsonify({'status': 'no uid provided'}), 400


@app.route('/live')
def live():
    global last_scanned_uid
    student = None
    if last_scanned_uid:
        student = scans_collection.find_one({"uid": last_scanned_uid})
    return render_template("live.html", student=student)


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            student = scans_collection.find_one({'username': username})

            if student and student['password'] == password:
                session['student_id'] = str(student['_id'])  # Convert ObjectId to string before storing in session
                return redirect(url_for('student_dashboard'))
            else:
                return "Invalid username or password"
        else:
            return "Username and password are required"

    return render_template('student_login.html')


@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' in session:
        student = scans_collection.find_one({'_id': ObjectId(session['student_id'])})
        student['id'] = str(student['_id'])  # Convert ObjectId to string for rendering
        return render_template('student_dashboard.html', student=student)
    return redirect(url_for('student_login'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        return "Invalid admin credentials"
    return render_template('admin_login.html')


@app.route('/admin_panel')
def admin_panel():
    if 'admin' in session:
        students = scans_collection.find()  # Get all students
        students_list = []
        for student in students:
            student['id'] = str(student['_id'])  # Convert ObjectId to string for rendering
            students_list.append(student)
        return render_template('admin_panel.html', students=students_list)
    return redirect(url_for('admin_login'))


@app.route('/update_student/<uid>', methods=['GET', 'POST'])
def update_student(uid):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    student = scans_collection.find_one({'uid': uid})

    if request.method == 'POST':
        new_name = request.form['name']
        new_fee_status = request.form['fee_status']
        new_attendance = int(request.form['attendance'])
        new_password = request.form['password']

        # Update the student details in MongoDB
        result = scans_collection.update_one(
            {'uid': uid},
            {"$set": {
                "name": new_name,
                "fee_status": new_fee_status,
                "attendance": new_attendance,
                "password": new_password
            }}
        )

        if result.modified_count > 0:
            return redirect(url_for('admin_panel'))
        else:
            return "Update failed, please try again."

    return render_template('update_student.html', student=student)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
