from flask import Flask, render_template, request, redirect, url_for, g, session
from markupsafe import escape
import logging
from logging import FileHandler
import os
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def sql_query_connection(sqlstr):
    try:
        conn = sqlite3.connect('main.db')
        cursor = conn.execute(sqlstr)
        ret = cursor.fetchall()
        if len(ret) == 0:
            print('None value has been returned')
            # TODO if time institute a logger here
            return ret
        else:
            return ret
    except:
        print('an error has occurred')
        # TODO if time institute a logger here
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html', error=error)
    if request.method == 'POST':
        username = "'" + request.form['username'] + "'"
        password = "'" + request.form['password'] + "'"
        sqlstr = "SELECT * FROM tech WHERE tech_name = {} AND tech_password = {}".format(username, password)
        a = sql_query_connection(sqlstr)
        # Todo: better if statement
        if len(a) < 3:
            return render_template('login.html', error='Invalid Username or Password, please try again!')
        else:
            session['username'] = request.form['username']
            return redirect(url_for('index'))


@app.route('/', methods=['GET'])
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    con = sqlite3.connect('main.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select student.student_id, student.student_first_name, student.student_last_name from student")
    con.commit()
    rows = cur.fetchall()
    cur.execute(
        "select quizzes.quiz_id, quizzes.quiz_subject, quizzes.quiz_question_amount, quizzes.quiz_date from quizzes")
    con.commit()
    rows2 = cur.fetchall()
    con.close()
    return render_template("dashboard.html", rows=rows, rows2=rows2)


@app.route('/student/add', methods=['GET', 'POST'])
def add():
    con = sqlite3.connect('main.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT student_id FROM student WHERE student_id=(SELECT max(student_id) FROM student)")
    sid = [dict(id=row[0]) for row in cur.fetchall()][0]["id"] + 1
    con.close()
    if request.method == 'POST':
        if request.form['student_name'] is not None:
            try:
                student_name = request.form['student_name']
                student_name = student_name.split(' ')
                sfn, sln = '"' + student_name[0].strip() + '"', '"' + student_name[1].strip() + '"'
                con = sqlite3.connect('main.db')
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO student (student_id, student_first_name, student_last_name) VALUES ({}, {}, {})".format(
                        sid, sfn, sln))
                con.commit()
                con.close()
                return redirect('/dashboard')
            except:
                error = 'Invalid Name. Please try again.'
                return render_template('studentadd.html', error=error)
        else:
            return redirect(url_for('dashboard'))
    else:
        return render_template("studentadd.html")


@app.route('/quiz/add', methods=['GET', 'POST'])
def quizadd():
    con = sqlite3.connect('main.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT quiz_id FROM quizzes WHERE quiz_id=(SELECT max(quiz_id) FROM quizzes)")
    quiz_id = [dict(id=row[0]) for row in cur.fetchall()][0]["id"] + 1
    con.close()
    if request.method == 'POST':
        if request.form['quiz_subject'] is not None:
            try:
                subject = '"' + request.form['quiz_subject'].strip() + '"'
                q_amt = request.form['quiz_question_amount'].strip()
                q_date = request.form['quiz_date'].strip()
                q_date = '"' + datetime.datetime.strptime(q_date, '%Y-%m-%d').strftime('%B %d,%Y') + '"'
                q_date = q_date
                print('quiz_id {}, subject {}, q_amt {} q_date {}'.format(quiz_id, subject, q_amt, q_date))
                con = sqlite3.connect('main.db')
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO quizzes (quiz_id, quiz_subject, quiz_question_amount, quiz_date) VALUES ({}, {}, {}, {})".format(
                        quiz_id, subject, q_amt, q_date))
                con.commit()
                con.close()
                return redirect('/dashboard')
            except:
                error = 'Invalid Name. Please try again.'
                return render_template('quizadd.html', error=error)
        else:
            return redirect(url_for('dashboard'))
    else:
        return render_template("quizadd.html")


@app.route('/student/<studentid>', methods=['GET', 'POST'])
def studentidpass(studentid=None):
    print(studentid)
    error = 'Error, user not found'
    con = sqlite3.connect('main.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT score_id,score_total FROM score WHERE student_id= {}".format(studentid))
    con.commit()
    rowscur = cur.fetchall()
    con.close()

    return render_template("studentsearch.html", rows=rowscur, error=error)


if __name__ == '__main__':
    app.run(debug=True)

# \/\/\/ Linux
# export FLASK_APP=main.py
# export FLASK_ENV=development
# flask run
# \/\/\/ Windows
# set FLASK_APP=main.py
# set FLASK_ENV=development
# python -m flask run
#
#

"""def logfile_start():
    file_handler = FileHandler(os.getcwd() + "/log.txt")
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)"""
