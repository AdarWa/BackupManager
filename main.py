from flask import Flask, render_template, request,redirect # type: ignore
import bkp
import hashlib
import base64
import docker # type: ignore
import os
import time

app = Flask(__name__)
client = docker.from_env()
PASS_FILE = '/app/secrets/pass.txt'

def check_auth_header(cookie_check=False):
    auth_header = None
    if cookie_check:
        auth_header = request.cookies.get('auth')
    else:
        auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    auth = auth_header.split(' ')
    if auth[0] != "Bearer":
        return False
    if not os.path.exists(PASS_FILE):
        with open(PASS_FILE, 'w') as f:
            f.write(hashlib.sha256(base64.b64encode(b'admin:admin')).hexdigest())
    with open(PASS_FILE, 'r') as f:
        return hashlib.sha256(auth[1].encode()).hexdigest() == f.read().strip()

@app.route('/', methods=['GET','POST'])
def home():
    if not check_auth_header() and not check_auth_header(cookie_check=True):
        return render_template("login.html")
    if request.args.get("username") and request.args.get("password"):
        user = request.args.get("username")
        password = request.args.get("password")
        with open(PASS_FILE, 'w') as f:
            f.write(hashlib.sha256(base64.b64encode(str(user+":"+password).encode())).hexdigest())
        return redirect('/')
    
    containers = request.args.getlist('containers')
    if containers:
        with open('/app/secrets/containers.txt', 'w') as f:
            for container in containers:
                f.write(container + '\n')
                
    initail = not os.path.exists('/app/secrets/containers.txt') or request.args.get('initial')
    container_list = []
    if initail:
        container_list = [ cont.name for cont in client.containers.list()]
    return render_template('index.html', backups=bkp.list_backups(), initial=initail, containers=container_list)


def stop_containers():
    with open('/app/secrets/containers.txt', 'r') as f:
        for container in f.readlines():
            container = container.strip()
            try:
                client.containers.get(container).stop()
                client.containers.get(container).wait()
            except:
                print(f'Container {container} not found!')
                
def start_containers():
    with open('/app/secrets/containers.txt', 'r') as f:
        for container in f.readlines():
            container = container.strip()
            try:
                client.containers.get(container).start()
            except:
                print(f'Container {container} not found!')

@app.route('/backup/<action>/<name>/', defaults={'new_name': None}, methods=['GET'])
@app.route('/backup/<action>/<name>/<new_name>/', methods=['GET'])
def backup_action(action, name, new_name):
    if not check_auth_header() and not check_auth_header(cookie_check=True):
        return {'result': "unauthorized", 'detailed': "Authorization header missing or invalid!"}, 401
    if action == "delete":
        rtn = bkp.delete_backup(name)
        if rtn == 'not-found':
            return {'result': "not found", 'detailed': "Requested backup not found!"}, 404
        else:
            return {'result': "success", 'detailed': None}, 200
    elif action == "rename":
        rtn = bkp.rename_backup(name, new_name)
        if rtn == 'not-found':
            return {'result': "not found", 'detailed': "Requested backup not found!"}, 404
        elif rtn == 'already-exists':
            return {'result': "already exists", 'detailed': "A backup with this name already exists!"}, 409
        else:
            return {'result': "success", 'detailed': None}, 200
    elif action == "restore":
        stop_containers()
        time.sleep(2)
        rtn = bkp.restore_backup(name)
        time.sleep(2)
        start_containers()
        if rtn == 'not-found':
            return {'result': "not found", 'detailed': "Requested backup not found!"}, 404
        elif rtn == 'inner-gz-not-found':
            return {'result': "inner gz not found", 'detailed': "Inner tar.gz not found in the backup!"}, 500
        elif rtn == 'data-folder-not-found':
            return {'result': "data folder not found", 'detailed': "Data folder not found in the inner tar.gz of the backup!"}, 500
        else:
            return {'result': "success", 'detailed': None}, 200
    else:
        return {'result': "unknown action"}, 422

if __name__ == '__main__':
    app.run(port=5678)