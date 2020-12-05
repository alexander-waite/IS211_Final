from flask import Flask, render_template, request, redirect, url_for, g, session
from markupsafe import escape
import logging
from logging import FileHandler
import os
import sqlite3
import datetime

app = Flask(__name__)
# TODO: purge db before submission
# todo: change random secret key???
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def logfile_start():
    file_handler = FileHandler(os.getcwd() + "/log.txt")
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    logging.basicConfig(filename='log.txt', level=logging.DEBUG)


def sql_query_connection_select(sqlstr):
    try:
        conn = sqlite3.connect('main.db')
        cursor = conn.execute(sqlstr)
        ret = cursor.fetchall()
        if len(ret) == 0:
            logging.error('SQL Error, {}, Returned empty result'.format(sqlstr))
        return ret
    except TypeError as e:
        print(e)
        logging.error('SQL Error, {}, Returned TypeError'.format(sqlstr))
    return None


def sql_query_connection_insert(sqlstr):
    try:
        conn = sqlite3.connect('main.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sqlstr)
        conn.commit()
        conn.close()
    except TypeError as e:
        print(e)
        print('sql exception has error has occurred')
        return 'error'
    return None


def edit_workorder(sessioninfo):
    sqlstr = 'SELECT * FROM machine WHERE machine_location = {}'.format("'" + sessioninfo['machine_location'] + "'")
    sqlreturn = sql_query_connection_select(sqlstr)
    if len(sqlreturn) is 0:
        logging.error('Game does not exist, Please try again at {}'.format(datetime.datetime.now()))
        return redirect(url_for('workorder_confirm_edit', closeorder=False, confirmedit=True,
                                workorderid=sessioninfo['workorder_id'],
                                error='Game does not exist, Please try again.'))
    else:
        if sessioninfo['part_id'] is not '':
            sqlstr = 'SELECT * FROM part WHERE part_id = {}'.format("'" + str(sessioninfo["part_id"]) + "'")
            sqlreturn = sql_query_connection_select(sqlstr)
            #todo : expect problems here
            if len(sqlreturn) == 0:
                return redirect(url_for('workorder_confirm_edit', closeorder=False, confirmedit=True,
                                        workorderid=sessioninfo['workorder_id'],
                                        error='Invalid part number, Please try again.'))
            else:
                sqlstr = "UPDATE workorder SET workorder_description = {}, machine_location = {},part_id = {} WHERE  \
                         workorder_id = {}".format(
                    "'" + sessioninfo['workorder_description'] + "'",
                    "'" + sessioninfo['machine_location'] + "'",
                    "'" + str(sessioninfo['part_id']) + "'",
                    "'" + str(sessioninfo['workorder_id']) + "'")
                a = sql_query_connection_insert(sqlstr)
                print(a)
                successmsg = 'Successful workorder edit!'
                return render_template("workorder_final_edit.html", confirmedit=True,
                                       workorderid=sessioninfo['workorder_id'], success=successmsg)


@app.route('/', methods=['GET'])
def index():
    if len(session) == 0:
        return redirect(url_for('login'))
    elif session['username'] == 'root':
        return render_template("dashboard.html", session_user=session['username'])
    else:
        return render_template("dashboard.html", session_user=session['username'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html', error=error)
    if request.method == 'POST':
        username = "'" + request.form['username'] + "'"
        password = "'" + request.form['password'] + "'"
        # TODO : perhaps a more secure string
        sqlstr = "SELECT tech_id, tech_name FROM tech WHERE tech_name = {} AND tech_password = {}".format(username,
                                                                                                          password)
        sqlreturn = sql_query_connection_select(sqlstr)
        # Todo: better if statement
        if len(sqlreturn) == 0:
            return render_template('login.html', error='Invalid Username or Password, please try again!')
        else:
            session['uid'] = sqlreturn[0][0]
            session['username'] = sqlreturn[0][1]
            return redirect(url_for('index'))


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return 'you have been logged out'


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template("dashboard.html")


@app.route('/workorder/add', methods=['GET', 'POST'])
#Todo: correct str to uppercase
def workorder_add():
    if request.method == 'POST':
        if request.form.get("Return"):
            return redirect(url_for('index'))
        else:
            pass
    if request.method == 'POST':
        req = request.form
        logging.info('{}, {}, user attempting to create item'.format(session['uid'], req))
        if req["location"] is '' or req["problem"] is '':
            logging.error('Invalid blank item, location:{}, problem{}'.format(req['location'],req['problem']))
            return render_template("workorder.html", neworder=True, editorder=False,
                                   error='Invalid blank item, please try again.')
        else:
            sqlstr = 'SELECT * FROM machine WHERE machine_location = {}'.format("'" + req["location"] + "'")
            sqlreturn = sql_query_connection_select(sqlstr)
            if len(sqlreturn) is 0:
                logging.warning('Game does not exist, Please try again, {}'.format(req['location']))
                return render_template("workorder.html", neworder=True, editorder=False,
                                       error='Game does not exist, Please try again.')
            else:
                if req["part_needed_text"] is not '':
                    sqlstr = 'SELECT * FROM part WHERE part_id = {}'.format("'" + req["part_needed_text"] + "'")
                    sqlreturn = sql_query_connection_select(sqlstr)
                    if len(sqlreturn) == 0:
                        logging.warning('Invalid part number, Please try again., {}'.format(req['part_needed_text']))
                        return render_template("workorder.html", neworder=True, editorder=False,
                                               error='Invalid part number, Please try again.')
                    else:
                        pass
        sqlstr = "SELECT workorder_id FROM workorder WHERE workorder_id=(SELECT max(workorder_id) FROM workorder)"
        int_workorder_id = sql_query_connection_select(sqlstr)[0][0]
        sqlstr = "INSERT INTO workorder(workorder_id,workorder_description,machine_location,part_id) VALUES({}, " \
                 "{}, {}, {})".format(
            int_workorder_id + 1,
            "'" + req["problem"] + "'",
            "'" + req["location"] + "'",
            "'" + req["part_needed_text"] + "'")
        sql_query_connection_insert(sqlstr)
        try:
            sqlstr = "SELECT workorder_id FROM workorder WHERE workorder_id=(SELECT max(workorder_id) FROM workorder)"
            int_workorder_id = sql_query_connection_select(sqlstr)[0][0]
            successmsg = 'Successful workorder creation! Workorder ID {} created!'.format(int_workorder_id)
            return render_template("workorder.html", neworder=True, editorder=False, success=successmsg)
        except:
            print('an error has occurred')
    return render_template("workorder.html", neworder=True, editorder=False)


@app.route('/workorder/edit', methods=['GET', 'POST'])
def workorder_lookup():
    #TODO: html submit button
    if request.method == 'POST':
        req = request.form
        sqlstr = 'SELECT * FROM workorder WHERE workorder_id = {}'.format("'" + req["WorkorderID"] + "'")
        sqlreturn = sql_query_connection_select(sqlstr)
        if len(sqlreturn) == 0:
            logging.error('Workorder ID does not exist, try again. {}'.format(req["WorkorderID"]))
            print('Workorder ID does not exist, try again.')
            return render_template("workorder.html", neworder=False, editorder=True, lookuporder=True,
                                   error='Workorder ID does not exist, try again.')
        else:
            keys = ('workorder_id', 'workorder_description', 'machine_location', 'part_id', 'status')
            session['sqlreturndict'] = dict(zip(keys, sqlreturn[0]))
            return redirect(url_for('workorder_editor', workorderid=session['sqlreturndict']['workorder_id']))
    return render_template("workorder.html", neworder=False, editorder=True, lookuporder=True)


@app.route('/workorder/edit/<workorderid>', methods=['GET', 'POST'])
def workorder_editor(workorderid):
    workorderid = session['sqlreturndict']['workorder_id']
    if request.method == 'POST':
        if request.form.get("Return"):
            return redirect(url_for('index'))
        else:
            pass
        if request.form.get("closeorder"):
            return redirect(url_for('workorder_close', workorderid=workorderid))
        else:
            pass
        if request.form.get('Submit'):
            req = request.form

            if req["location"] is '' or req["problem"] is '':
                print('Invalid blank item, please try again')
                return render_template("workorder.html", neworder=True, editorder=False,
                                       error='Invalid blank item, please try again.')
            keys = ('workorder_id', 'workorder_description', 'machine_location', 'part_id')
            values = (workorderid, req['problem'], req['location'], req['part_needed_text'])
            session['sqlreturndict'] = dict(zip(keys, values))
            return redirect(
                url_for('workorder_confirm_edit', closeorder=False, confirmedit=True, workorderid=workorderid))
        else:
            pass
    if session['sqlreturndict']['part_id'] == '':
        return render_template("workorder_final_edit.html", editorder=True)
    else:
        return render_template("workorder_final_edit.html", partadded=True, editorder=True)


@app.route('/workorder/edit/<workorderid>/close', methods=['GET', 'POST'])
def workorder_close(workorderid):
    if request.method == 'POST':
        if request.form.get("Submit"):
            sessioninfo = session['sqlreturndict']
            sqlstr = "UPDATE workorder SET status = 1 WHERE workorder_id = {}".format(
                "'" + str(sessioninfo['workorder_id']) + "'")
            sql_query_connection_insert(sqlstr)
            successmsg = 'Workorder is closed!'
            return render_template("workorder_final_edit.html", confirmedit=True,
                                   workorderid=sessioninfo['workorder_id'], success=successmsg)
        else:
            pass
        if request.form.get('Return'):
            return redirect(url_for('workorder_editor', workorderid=session['sqlreturndict']['workorder_id']))
        else:
            pass
    if request.method == 'GET':
        if session['sqlreturndict']['part_id'] == '':
            return render_template("workorder_final_edit.html", closeorder=True, workorderid=workorderid)
        else:
            return render_template("workorder_final_edit.html", partadded=True, closeorder=True,
                                   workorderid=workorderid)


@app.route('/workorder/edit/<workorderid>/confirm', methods=['GET', 'POST'])
def workorder_confirm_edit(workorderid):
    if request.method == 'POST':
        if request.form.get('Submit'):
            sessioninfo = session['sqlreturndict']
            sqlstr = 'SELECT * FROM machine WHERE machine_location = {}'.format(
                "'" + sessioninfo['machine_location'] + "'")
            sqlreturn = sql_query_connection_select(sqlstr)
            if len(sqlreturn) is 0:
                print('Game does not exist, Please try again')
                return render_template("workorder_final_edit.html", confirmedit=True,
                                       workorderid=sessioninfo['workorder_id'],
                                       error='Game does not exist, Please try again.')
            else:
                if sessioninfo['part_id'] is not '':
                    sqlstr = 'SELECT * FROM part WHERE part_id = {}'.format("'" + str(sessioninfo["part_id"]) + "'")
                    sqlreturn = sql_query_connection_select(sqlstr)
                    if len(sqlreturn) == 0:
                        return render_template("workorder_final_edit.html", confirmedit=True,
                                               workorderid=sessioninfo['workorder_id'],
                                               error='Invalid part number, Please try again.')
                    else:
                        sqlstr = "UPDATE workorder SET workorder_description = {}, machine_location = {},part_id = {} WHERE  \
                                 workorder_id = {}".format(
                            "'" + sessioninfo["workorder_description"] + "'",
                            "'" + sessioninfo['machine_location'] + "'",
                            "'" + str(sessioninfo['part_id']) + "'",
                            "'" + str(sessioninfo['workorder_id']) + "'")
                        a = sql_query_connection_insert(sqlstr)
                        successmsg = 'Successful workorder edit!'
                        return render_template("workorder_final_edit.html", confirmedit=True,
                                               workorderid=sessioninfo['workorder_id'], success=successmsg)
        else:
            pass
        if request.form.get('Return'):
            return redirect(url_for('workorder_editor', workorderid=session['sqlreturndict']['workorder_id']))
        else:
            pass
    else:
        if session['sqlreturndict']['part_id'] == '':
            return render_template("workorder_final_edit.html", confirmedit=True, workorderid=workorderid)
        else:
            return render_template("workorder_final_edit.html", partadded=True, confirmedit=True,
                                   workorderid=workorderid)


@app.route('/root', methods=['POST'])
def root_add():
    if request.form.get("New User"):
        return redirect(url_for('user_add'))
    if request.form.get("New Part"):
        return redirect(url_for('part_add'))


@app.route('/addpart', methods=['POST', 'GET'])
# todo html return button
def part_add():
    if request.method == 'POST':
        req = request.form
        sqlstr = "INSERT INTO part (part_id,part_description,part_revision) VALUES ({}, {}, {})" \
            .format(str(req[('part_id')]),
                    "'" + str(req['part_description']) + "'",
                    str(req['part_revision']))
        print(sqlstr)
        e = sql_query_connection_insert(sqlstr)
        if e is not None:
            errormsg = 'Error! Please try again'
            return render_template('add_part.html', error=errormsg)
        else:
            successmsg = 'new part added!'
            return render_template('add_part.html', success=successmsg)

    return render_template('add_part.html')


@app.route('/adduser', methods=['POST', 'GET'])
# todo html return button
def user_add():
    if request.method == 'POST':
        req = request.form
        # todo: regex password requirements?
        # todo: regex ensure all str for tech_name
        sqlstr = 'INSERT INTO tech (tech_id, tech_password, tech_name) values ({},{},{})'.format(str(req['tech_id']),
                                                                                                 "'" + req[
                                                                                                     'tech_password'] + "'",
                                                                                                 "'" + req[
                                                                                                     'tech_name'] + "'")
        e = sql_query_connection_insert(sqlstr)
        if e is not None:
            errormsg = 'an error has occured'
            return render_template('add_user.html', error=errormsg)
        else:
            successmsg = 'User successfully added!'
            return render_template('add_user.html', success=successmsg)
    return render_template('add_user.html')


if __name__ == '__main__':
    print('Change has occurred - Flask start again')
    logfile_start()
    logging.info('started at ' + str(datetime.datetime.now()))
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
# root abc123
# bob technician abc123
