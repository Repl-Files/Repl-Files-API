import pymongo
import os
from flask import Flask, redirect, send_file, request
from werkzeug.utils import secure_filename
import datetime
# from zoneinfo import ZoneInfo

app = Flask(__name__)
clientm = pymongo.MongoClient(os.getenv("clientm"))
database = clientm.Files
collection = database.Files
usersdb = clientm.Users
userscol = usersdb.users

app.config['UPLOAD_FOLDER'] = '/files'
app.config['MAX_CONTENT-PATH'] = 2000000 # Max file size

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
    return 'Hello World'

@app.route("/all")
def all_files():
  return {"files": get_all_files()}

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    data = request.form
    file = request.files['file']
    username = data['username']
    file_name = secure_filename(file.filename)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    if file_size > 2000000:
      return redirect("https://replfiles.dillonb07.studio/dashboard?type=error&msg=This%20file%20is%20over%202MB")
    if get_user(username) != False:
      if get_user(username)['spaceUsed'] > 10000000:
        return redirect("https://replfiles.dillonb07.studio/dashboard?type=error&msg=You%20have%20used%20all%20of%20your%2010MB")
    if not os.path.exists("files/" + username):
      os.makedirs("files/" + username)
    if os.path.exists("files/" + username + "/" + file_name):
      return redirect('https://replfiles.dillonb07.studio/dashboard?type=error&msg=You%20can%20not%20upload%20the%20same%20file%20again')
    file.save("files/" + username + "/" + file_name)
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
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=success&msg=File%20successfully%20uploaded')

@app.route("/download/<username>/<filename>")
def download(username, filename):
  if os.path.exists(f"files/" + username + "/" + filename):
    return send_file(f"files/{username}/" + filename)
  else:
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=error&msg=That%20file%20is%20not%20found')


@app.route("/feedback", methods=['GET','POST'])
def feedback():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    data = request.form

    """
    Incoming data:
    Username - str
    Title - str
    Type - str (type of feedback)
    Content - str    
    """
    username = data['username']
    title = data['title']
    type = data['type']
    content = data['content']
    current_time = datetime.datetime.now.strftime('%d/%m/%Y-%H:%M:%S')

    filename=f'{title}-{current_time}'
    if not os.path.exists(f"feedback/{type}/{username}"):
      os.makedirs(f"feedback/{type}/{username}")

    file = f"{title} ({type}) by @{username} - {current_time}\n\n{content}"
    
    f = open(filename, 'w')
    f.write(file)
    f.close()
    
    return redirect('https://replfiles.dillonb07.studio/dashboard?type=success&msg=Feedback%20successfully%20sent')
  

app.run(host='0.0.0.0', port=8080, debug=True)