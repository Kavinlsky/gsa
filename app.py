from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

from wtforms import Form, StringField, PasswordField, DateTimeField, SelectField, validators

from passlib.hash import sha256_crypt
import pymysql

app = Flask(__name__)
app.secret_key = 'supersecretkey'


class ConnectDB:
    def __init__(self):
        self.db_connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            db='gsa',
            autocommit=True,
            port=3306
        )
        self.mycursor = self.db_connection.cursor()

    def create_connection(self):
        return self.mycursor



users = []


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=100)])
    email = StringField('Email', [validators.Length(min=6, max=100)])
    mobile = StringField('Mobile', [validators.Length(min=10, max=15)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    address = StringField('Address', [validators.Length(min=1, max=200)])



class TaskForm(Form):
    task_name = StringField('Task Name', [validators.Length(min=1, max=255)])
    task_date = DateTimeField('Date and Time', format='%Y-%m-%d %H:%M:%S')
    assigned_to = SelectField('Assigned To', coerce=int)




@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        address = request.form['address']

        cursor = ConnectDB().create_connection()
        cursor.execute("INSERT INTO users(name, email, mobile, password, address) VALUES(%s, %s, %s, %s, %s)",
                    (name, email, mobile, password, address))
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_form = request.form['password']

        cursor = ConnectDB().create_connection()
        result = cursor.execute("SELECT * FROM users WHERE email = %s", [email])

        if result > 0:
            data = cursor.fetchone()
            password = data[4]

            # print(password_form,"---",password)

            if password_form == password:
                session['logged_in'] = True
                session['username'] = data[1]
                session['user_id'] = data[0]
                return redirect(url_for('dashboard'))
        cursor.close()

    return render_template('login.html')


@app.route('/dashboard' ,methods=['POST', 'GET'])
def dashboard():
    if 'logged_in' in session:
        user_id = session['user_id']
        cursor = ConnectDB().create_connection()

        # Fetch all users for the task assignment dropdown
        cursor.execute("SELECT id, name FROM users")
        users = cursor.fetchall()

        # Fetch tasks assigned by or to the logged-in user
        cursor.execute(
            "SELECT t.id, t.task_name, t.task_date, u1.name as assigned_to_name, u2.name as assigned_by_name, t.status FROM tasks t LEFT JOIN users u1 ON t.assigned_to = u1.id LEFT JOIN users u2 ON t.assigned_by = u2.id WHERE t.assigned_to = %s OR t.assigned_by = %s",
            (user_id, user_id))
        tasks = cursor.fetchall()

        form = TaskForm(request.form)
        form.assigned_to.choices = [(user[0], user[1]) for user in users]
        # print(form)
        # print(tasks)
        # print("--------------------")

        if request.method == 'POST':
            task_name = form.task_name.data
            task_date = form.task_date.data
            assigned_to = form.assigned_to.data


            cursor.execute("INSERT INTO tasks(task_name, task_date, assigned_to, assigned_by) VALUES(%s, %s, %s, %s)",
                        (task_name, task_date, assigned_to, user_id))

            return redirect(url_for('dashboard', form=form, tasks=tasks))

        cursor.close()
        print(tasks)
        print("===============")
        print(form)
        print("------------------------------------------------------------------")
        return render_template('dashboard.html', form=TaskForm(), tasks=tasks)

    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
