from flask import Flask, render_template, request, redirect, url_for, session
import re
import logging
from logging import FileHandler
import os
import sqlite3
import datetime
from flask import send_from_directory
import csv
import json

UPLOAD_FOLDER = os.getcwd() + '/upload_files/'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
s_key = os.urandom(24)
app.secret_key = s_key


def session_check():
    if len(session) == 0:
        return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def removefile():
    if os.path.isfile(UPLOAD_FOLDER + 'upload.json'):
        os.remove(UPLOAD_FOLDER + 'upload.json')
        print('old JSON file removed')


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
    if len(session) == 0 or session['username'] is None:
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
        sqlstr = "SELECT tech_id, tech_name FROM tech WHERE tech_name = {} AND tech_password = {}".format(username,
                                                                                                          password)
        sqlreturn = sql_query_connection_select(sqlstr)
        if len(sqlreturn) == 0:
            return render_template('login.html', error='Invalid Username or Password, please try again!')
        else:
            session['uid'] = sqlreturn[0][0]
            session['username'] = sqlreturn[0][1]
            print(session)
            return redirect(url_for('index'))


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return 'you have been logged out'


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template("dashboard.html")


@app.route("/part/import", methods=['GET', 'POST'])
def part_import():
    if request.method == "POST":
        if 'file' not in request.files:
            errormsg = "no file attached"
            return render_template("import_part.html", error=errormsg)
        file = request.files['file']
        if file.filename == '':
            errormsg = "no file attached"
            return render_template("import_part.html", error=errormsg)
        if file and allowed_file(file.filename):
            removefile()
            # Takes uploaded CSV file, saves locally, then converts from csv to json
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'upload.csv'))
            logging.info('file successfully uploaded, upload.csv')
            csv_file_path = UPLOAD_FOLDER + 'upload.csv'
            json_file_path = UPLOAD_FOLDER + 'upload.json'
            json_data = {}
            try:
                logging.info('Beginning log of file {}'.format(csv_file_path))

                with open(csv_file_path) as csvFile:
                    csv_reader = csv.DictReader(csvFile)
                    for row in csv_reader:
                        json_id = row['part number']
                        json_data[json_id] = row
                # writes csv file as JSON data
                with open(json_file_path, 'w') as jsonfile:
                    jsonfile.write(json.dumps(json_data, indent=4))
                    logging.info('Successful transfer of csv to json for file {}'.format(csv_file_path))
                os.remove(UPLOAD_FOLDER + 'upload.csv')
                logging.info('removed upload.csv'.format(csv_file_path))
                # json to SQL str and insert per string
                with open(json_file_path, 'r') as jsonfile:
                    data = json.load(jsonfile)
                for aa in data.items():
                    data_list = None
                    try:
                        data_list = list(aa[1].values())
                        print(data_list)
                        data_list[1] = "'" + data_list[1] + "'"
                        if not int(data_list[0]):
                            print('Cannot process sqlstr, skipping line')
                            continue
                        else:
                            sql_str = "INSERT INTO part(part_id,part_description,part_revision) VALUES ({},{},{})" \
                                .format(data_list[0], data_list[1], data_list[2])
                            print(sql_str)
                            sql_query_connection_insert(sql_str)
                    except TypeError as e:
                        print(e)
                        logging.error('{}occurred, unable to write SQL'.format(TypeError))
                        return render_template("import_part.html", error="SQL error.")
                    except ValueError as e:
                        logging.error('{} occurred, items: {}, unable to write values'.format(e, data_list))
                        pass
                return render_template("import_part.html", success="Successful upload!")
            except TypeError as e:
                logging.error('{}, error while uploading file, {} , formatting of SQL error'
                              .format(e, session['username']))
                return render_template("import_part.html", error="JSON formatting error.")
        else:
            print('error')
            errormsg = 'Unacceptable file submitted, file rejected'
            return render_template("import_part.html", error=errormsg)
    return render_template("import_part.html")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/workorder/add', methods=['GET', 'POST'])
def workorder_add():
    if request.method == 'POST':
        if request.form.get("Return"):
            return redirect(url_for('index'))
        else:
            pass
    if request.method == 'POST':
        # regex
        r = re.compile('^[.-9A-Za-z\\\ ]{10,}')
        req = request.form
        logging.info('{}, {}, user attempting to create item'.format(session['uid'], req))
        if req["location"] is '' or req["problem"] is '':
            logging.error('Invalid blank item, location:{}, problem{}'.format(req['location'], req['problem']))
            return render_template("workorder.html", neworder=True, editorder=False,
                                   error='Invalid blank item, please try again.')
        elif not r.match(req["problem"]):
            logging.error(
                'Invalid problem description length or invalid character, location:{}, problem:{}'.format(
                    req['location'], req['problem']))
            return render_template("workorder.html", neworder=True, editorder=False,
                                   error='Invalid problem description length or invalid character. Please use text'
                                         ' , spaces, and integers only')
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
        except ValueError as e:
            errormsg = "Error has occurred {}".format(e)
            return render_template("workorder.html", neworder=True, editorder=False, error=errormsg)
    return render_template("workorder.html", neworder=True, editorder=False)


@app.route('/workorder/edit', methods=['GET', 'POST'])
def workorder_lookup():
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
            print(session['sqlreturndict'])
            return redirect(url_for('workorder_editor', workorderid=session['sqlreturndict']['workorder_id']))
    return render_template("workorder.html", neworder=False, editorder=True, lookuporder=True)


@app.route('/workorder/edit/<workorderid>', methods=['GET', 'POST'])
def workorder_editor(workorderid):
    session_check()

    def workorder_lookup_redirect():
        try:
            work_order_id = session['sqlreturndict']['workorder_id']
        except KeyError:
            redirect(url_for('workorder_lookup'))
        else:
            return work_order_id
    work_order_id = workorder_lookup_redirect()
    if request.method == 'POST':
        if request.form.get("Return"):
            redirect(url_for('index'))
        else:
            pass
        if request.form.get("closeorder"):
            return redirect(url_for('workorder_close', workorderid=work_order_id))
        else:
            pass
        if request.form.get('Submit'):
            req = request.form
            if req["location"] is '' or req["problem"] is '':
                print('Invalid blank item, please try again')
                return render_template("workorder.html", neworder=True, editorder=False,
                                       error='Invalid blank item, please try again.')
            keys = ('workorder_id', 'workorder_description', 'machine_location', 'part_id')
            if not request.form.getlist('part_needed_text'):
                values = (work_order_id, req['problem'], req['location'], '')
            else:
                values = (work_order_id, req['problem'], req['location'], req['part_needed_text'])
            session['sqlreturndict'] = dict(zip(keys, values))
            return redirect(
                url_for('workorder_confirm_edit', closeorder=False, confirmedit=True, workorderid=work_order_id))
        else:
            pass
    return render_template("workorder_final_edit.html", editorder=True, partadded=True)


@app.route('/workorder/edit/<workorderid>/close', methods=['GET', 'POST'])
def workorder_close(workorderid):
    if len(session) == 0:
        return redirect(url_for('/'))
    if request.method == 'POST':
        if request.form.get("Submit"):
            # see if order is already closed:
            sessioninfo = session['sqlreturndict']
            sqlstr = "SELECT workorder.status FROM workorder WHERE workorder.workorder_id = {}".format(
                "'" + str(sessioninfo['workorder_id']) + "'")
            c = sql_query_connection_select(sqlstr)
            print(c)
            if c[0][0] == 1:
                logging.warning(
                    "Workorder {} attempted to be closed and was already closed".format(sessioninfo['workorder_id']))
                errormsg = "Error: workorder already closed."
                return render_template("workorder_final_edit.html", closeorder=True,
                                       workorderid=sessioninfo['workorder_id'], error=errormsg, attemptsubmit=True)
            sqlstr = "UPDATE workorder SET status = 1 WHERE workorder_id = {}".format(
                "'" + str(sessioninfo['workorder_id']) + "'")
            sql_query_connection_insert(sqlstr)
            successmsg = 'Workorder is closed!'
            return render_template("workorder_final_edit.html", closeorder=True,
                                   workorderid=sessioninfo['workorder_id'], success=successmsg, attemptsubmit=True)
        if request.form.get('Return'):
            return redirect(url_for('workorder_lookup', workorderid=session['sqlreturndict']['workorder_id']))
        else:
            pass
    if request.method == 'GET':
        if session['sqlreturndict']['part_id'] == '':
            return render_template("workorder_final_edit.html", closeorder=True, workorderid=workorderid,
                                   attemptsubmit=False)
        else:
            return render_template("workorder_final_edit.html", partadded=True, closeorder=True,
                                   workorderid=workorderid, attemptsubmit=False)


@app.route('/workorder/edit/<workorderid>/confirm', methods=['GET', 'POST'])
def workorder_confirm_edit(workorderid):
    session_check()
    if len(session) == 0:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if request.form.get('Submit'):
            sessioninfo = session['sqlreturndict']
            sqlstr = 'SELECT * FROM machine WHERE machine_location = {}'.format(
                "'" + sessioninfo['machine_location'] + "'")
            sqlreturn = sql_query_connection_select(sqlstr)
            if len(sqlreturn) is 0:
                logging.warning(
                    'Error in editing workorder, Game does not exist, Please try again, {}, {} '.format(session['uid'],
                                                                                                        sessioninfo[
                                                                                                            'workorder_id']))
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
                        sqlstr = "UPDATE workorder SET workorder_description = {}, machine_location = {},part_id = " \
                                 "{} WHERE workorder_id = {}".format(
                            "'" + sessioninfo["workorder_description"] + "'",
                            "'" + sessioninfo['machine_location'] + "'",
                            "'" + str(sessioninfo['part_id']) + "'",
                            "'" + str(sessioninfo['workorder_id']) + "'")
                        sql_query_connection_insert(sqlstr)
                        successmsg = 'Successful workorder edit!'
                        return render_template("workorder_final_edit.html", confirmedit=True,
                                               workorderid=sessioninfo['workorder_id'], success=successmsg)
                else:
                    sqlstr = "UPDATE workorder SET workorder_description = {}, machine_location = " \
                             "{},part_id = '' WHERE workorder_id = {}".format(
                        "'" + sessioninfo["workorder_description"] + "'",
                        "'" + sessioninfo['machine_location'] + "'",
                        "'" + str(sessioninfo['workorder_id']) + "'")
                    sql_query_connection_insert(sqlstr)
                    successmsg = 'Successful workorder edit!'
                    return render_template("workorder_final_edit.html", confirmedit=True,
                                           workorderid=sessioninfo['workorder_id'], success=successmsg)
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


@app.route('/part/add', methods=['POST', 'GET'])
def part_add():
    if request.method == 'POST':
        req = request.form
        if req['part_id'] == '' or req['part_description'] == '' or  req['part_revision'] == '':
            errormsg = 'Blank input. Please ensure all parts are filled out'
            return render_template('add_part.html', error=errormsg)
        sqlstr = "INSERT INTO part (part_id,part_description,part_revision) VALUES ({}, {}, {})" \
            .format(str(req['part_id']),
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
def user_add():
    if request.method == 'POST':
        req = request.form

        sqlstr = "SELECT tech_id FROM tech WHERE tech_id=(SELECT max(tech_id) FROM tech)"
        tech_id = sql_query_connection_select(sqlstr)
        tech_id = tech_id[0][0] + 1
        if req['tech_password'] and req['tech_name']:
            sqlstr = 'INSERT INTO tech (tech_id, tech_password, tech_name) VALUES ({},{},{})'.format(str(tech_id),
                                                                                                     "'" + req[
                                                                                                         'tech_password']
                                                                                                     + "'", "'" + req[
                                                                                                         'tech_name'] + "'")
            try:
                sql_query_connection_insert(sqlstr)
                successmsg = 'User successfully added!'
                return render_template('add_user.html', success=successmsg)
            except ValueError as e:
                logging.error('{}, an error has occurred, {}'.format(e, sqlstr))
                errormsg = 'an error has occurred'
                return render_template('add_user.html', error=errormsg)
        else:
            errormsg = 'blank value detected, please ensure both name and password are filled'
            return render_template('add_user.html', error=errormsg)
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
