# import test
# import io
import ast
import pymongo
# import gridfs
from bson.objectid import ObjectId
import dns
import os
import json
from flask import Flask, redirect, send_file, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
clientm = pymongo.MongoClient(os.getenv("clientm"))
database = clientm.Files
collection = database.Files
usersdb = clientm.Users
userscol = usersdb.users

app.config['UPLOAD_FOLDER'] = '/files'
app.config['MAX_CONTENT-PATH'] = 2000000 # Max file size

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
    return 'Hello World'

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    data = request.form
    file = request.files['file']
    username = data['username']
    if get_user(username) != False:
      if get_user(username)['spaceUsed'] > 10000000:
        return {'error': 'All space has been used.'}
    if not os.path.exists("files/" + username):
      os.makedirs("files/" + username)
    file_name = secure_filename(file.filename)
    if os.path.exists("files/" + username + "/" + file_name):
      return {"Error": "A file with this name already exists"}
    file.save("files/" + username + "/" + file_name)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    if get_user(username) == False:
      create_user(username, file_size)
    else:
      modify_user(username, file_size)
    user = get_user(username)
    image_url = data.get("imageUrl", "")
    file = {
      "name": data['name'],
      "description": data['description'],
      "filename": file_name,
      "file": "https://replfiles.api.dillonb07.studio/download/" + username + "/" + file_name,
      "username": username,
      "imageUrl": image_url,
      "fileSize": file_size
    }
    files = user['files']
    files.append(file)
    del user['files']
    user['files'] = files
    userscol.delete_one({"_id": user['_id']})
    userscol.insert_many([user])
    response = app.response_class(
        response=json.dumps({"url": "https://replfiles.api.dillonb07.studio/download/" + username + "/" + file_name}),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route("/download/<username>/<filename>")
def download(username, filename):
  if os.path.exists(f"files/" + username + "/" + filename):
    return send_file(f"files/{username}/" + filename)
  else:
    return {'error': 'File not found'}
  

app.run(host='0.0.0.0', port=8080, debug=True)


"""
/ - Redirect to https://replfiles.dillonb07.studio

/upload - Upload file and return id
        - Check if the user (id will be passed through endpoint) has enough space left (limit of 10MB per user)

This also needs to add the file as a JSON object/dict to an array in the User object. Here's an example:

[{
    "id" : 1,
    "name": "Test",
    "description": "Description",
    "file": "", # preferably a URL here, but however you manage to store the file.
    "user": 1,
    "image": "https://storage.googleapis.com/replit/images/1659623175957_1b73bc274040fc62a1d8187144aa17c8.png"
}, {
    "id" : 2,
    "name": "Test 2",
    "description": "Description 2",
    "file": "", # preferably a URL here, but however you manage to store the file.
    "user": 1,
    "image": "https://storage.googleapis.com/replit/images/1650209136478_ddae1a1e79240cefc81560ad52e2dc00.png"
}]

/download - Return the file from id

This could just be a URL for the file

/all - Return all files. Preferably in JSON format. This will be used for the moderation page.

NOTE: File can be anything. Not a specific format. If it's easier, we could compress it to a .zip and then store it. Or, should I change it to image-only hosting which should be much easier.
"""