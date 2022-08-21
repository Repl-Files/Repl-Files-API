import json
import pymongo
import os
from flask import Flask, redirect, send_file, request
from werkzeug.utils import secure_filename
import datetime
# from zoneinfo import ZoneInfo # py 3.9 and later. argh!!!!

app = Flask(__name__)
clientm = pymongo.MongoClient(os.getenv("clientm"))
database = clientm.Files
collection = database.Files
usersdb = clientm.Users
userscol = usersdb.users

app.config['UPLOAD_FOLDER'] = '/files'
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # Max file size

@app.after_request
def apply_caching(response):
    response.headers["Access-Control-Allow-Origin"] = "https://replfiles.dillonb07.studio"
    return response


@app.errorhandler(413)
def request_entity_too_large(error):
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=error&msg=File%20is%20over%2015MB')


def get_all_files():
  files = []
  for user in userscol.find():
    for file in user['files']:
      files.append(file)
  return files

def get_user(username):
  myquery = {"username": username}
  mydoc = userscol.find(myquery)
  for x in mydoc:
    return x
  return False

def create_user(username, count):
  doc = [{
    "username": username,
    "count": count
  }]
  userscol.insert_many(doc)

def modify_user(username, count):
  userdoc = get_user(username)
  now_count = userdoc['spaceUsed']
  new_count = now_count + count
  del userdoc['spaceUsed']
  userdoc['spaceUsed'] = new_count
  userscol.delete_one({"_id": userdoc['_id']})
  userscol.insert_many([userdoc])

@app.route('/')
def index():
    # return redirect('https://replfiles.dillonb07.studio')
    return 'No'

@app.route("/all")
def all_files():
  return {"files": get_all_files()}

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    data = request.form
    file = request.files['file']
    username = data['username']
    file_name = secure_filename(f'{username}-{file.filename}')
    if os.path.exists("files/" + file_name):
      return redirect('https://replfiles.dillonb07.studio/dashboard?type=error&msg=You%20can%20not%20upload%20the%20same%20file%20again')
    # file.seek(os.SEEK_END)
    # file_size = file.tell()
    # file.seek(0, 0)/
    # f = request.files['file'].read()
    file.save(f'files/{file_name}')
    
    # file_size = os.stat(f'files/{username}/{file_name}').st_size
    file_size = os.path.getsize("files/" + file_name)
    if file_size > (2*1024*1024):
      os.remove(f"files/{file_name}")
      return redirect("https://replfiles.dillonb07.studio/dashboard?type=error&msg=File%20is%20over%202MB")
    for f in get_user(username)['files']:
        if f['name'] == data['name']:
            os.remove(f'files/{file_name}')
            return redirect('https://replfiles.dillonb07.studio/dasboard?type=error&msg=Files%20must%20have%20unique%20names')
    if get_user(username) != False:
      if get_user(username)['spaceUsed'] > (15*1024*1024):
        os.remove(f"files/{file_name}")
        return redirect("https://replfiles.dillonb07.studio/dashboard?type=error&msg=You%20have%20used%20all%20of%20your%2015MB")
    if get_user(username) == False:
      create_user(username, file_size)
    else:
      modify_user(username, file_size)
    user = get_user(username)
    image_url = data.get("imageUrl", "")
    file2 = {
      "name": data['name'],
      "description": data['description'],
      "filename": secure_filename(file.filename),
      "file": "https://replfiles.api.dillonb07.studio/download/" + username + '/' + secure_filename(file.filename),
      "username": username,
      "imageUrl": image_url,
      "fileSize": file_size
    }
    files = user['files']
    files.append(file2)
    del user['files']
    user['files'] = files
    userscol.delete_one({"_id": user['_id']})
    userscol.insert_many([user])
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=success&msg=File%20successfully%20uploaded')

@app.route("/download/<username>/<filename>")
def download(username, filename):
  if os.path.exists(f"files/{username}-{filename}"):
    return send_file(f"files/{username}-{filename}")
  else:
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=error&msg=That%20file%20is%20not%20found')


@app.route("/feedback", methods=['GET','POST'])
def feedback():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    data = request.form
    username = data['username']
    title = data['title']
    type = data['type']
    content = data['content']
    current_time = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')

    folder = f'feedback/{type}/{username}'
    filename = secure_filename(f'{title}-{current_time}')
    if not os.path.exists(folder):
      os.makedirs(folder)

    file = f"{title} ({type}) by @{username} - {current_time} UTC\n\n{content}"
    
    f = open(f'{folder}/{filename}.txt', 'w')
    f.write(file)
    f.close()
    
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=success&msg=Feedback%20successfully%20submitted')
  


@app.route('/delete', methods=['POST'])
def delete():
    # Return errors as a JSON object like this : {'error': {'msg': 'ERROR MESSAGE'}}. Otherwise, return {'success': {'msg': 'SUCCESS MESSAGE'}}
    data = request.get_json()
    username = data['username']
    filename = username + '-' + data['file']
    if os.path.exists("files/" + filename):
      file_size = os.path.getsize("files/" + filename)
      modify_user(username ,(-1*file_size))
      os.remove(f"files/{filename}")
      user = get_user(username)
      new_user = user
      for file in new_user['files']:
          if file['filename'] == data['file']:
              index = new_user['files'].index(file)
              del new_user['files'][index]
              break
      userscol.delete_one({"_id": new_user['_id']})
      userscol.insert_many([new_user])
  
      response = app.response_class(
          response=json.dumps({"type": 'success', 'msg': f'Successfully deleted {filename}'}),
          status=200,
          mimetype='application/json'
      )
      return response
    else:
      response = app.response_class(
          response=json.dumps({"type": 'error', 'msg': f"{filename} doesn't exist"}),
          status=404,
          mimetype='application/json'
      )
      return response

@app.route('/get/<username>/<file>')
def get_file(username, file):
    user = get_user(username)
    for f in user['files']:
        if f['name'] == file:
            return json.dumps(f)
    return {'type': 'error', 'msg':'File not found'}

# app.run(host='0.0.0.0', port=8080)