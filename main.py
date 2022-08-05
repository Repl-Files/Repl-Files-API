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

app.config['UPLOAD_FOLDER'] = '/files'
app.config['MAX_CONTENT-PATH'] = 2000000 # Max file size

@app.route('/')
def index():
    return 'Hello World'

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == "GET": return redirect('https://replfiles.dillonb07.studio/dashboard')
    
    data = request.form
    file = request.files['file']
    if not os.path.exists("files/" + data['id']):
      os.makedirs("files/" + data['id'])
    file_name = secure_filename(file.filename)
    file.save("files/" + data['id'] + "/" + file_name)
    print(data)
    image_url = data.get("imageUrl", "")
    document = [{
      "Name": data['name'],
      "Description": data['description'],
      "File": "https://replfiles.api.dillonb07.studio/download/" + data['id'] + "/" + file_name,
      "UserId": data['id'],
      "ImageUrl": image_url
    }]
    collection.insert_many(document)
    response = app.response_class(
        response=json.dumps({"url": "https://replfiles.api.dillonb07.studio/download/" + data['id'] + "/" + file_name}),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route("/download/<username>/<filename>")
def download(username, filename):
  if os.path.exists(f"files/" + username + "/" + filename):
    return send_file(f"files/{username}/" + filename)
  else:
    return redirect('https://replfiles.dillonb07.studio')
  

app.run(host='0.0.0.0', port=8080, debug=True)


"""
/ - Redirect to https://replfiles.dillonb07.studio

/upload - Upload file and return id
        - Check if the user (id will be passed through endpoint) has enough space left (limit of 10MB per user)
        - Check file is under 2MB. This must be checked on the server to stop people directly accessing the endpoint to upload large files and fill the db

Information coming from form:
- File Nickname
- File Description - This may be an empty string
- Image URL - This may be an empty string
- File
- User id

You should be able to get these from the Flask request method (I think that's what it's called)

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