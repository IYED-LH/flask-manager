from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
from bson import ObjectId
from flask_mail import Mail, Message
import json
import bcrypt



#Connexion to database

connection_string = "mongodb+srv://crudcluster:123456crud@cluster0.pliqw.mongodb.net/?retryWrites=true"
client = MongoClient(connection_string)

db = client.appdb

app = Flask(__name__)
app.secret_key = "Secret Key"
mail = Mail(app) 

#Json encoder 

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)

app.json_encoder = MyEncoder

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'crudapptest@gmail.com'
app.config['MAIL_PASSWORD'] = '12303bbvv'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


#homepage route & diplay data in table

@app.route('/', methods=["GET", "POST"])
def index():
    
    all_data = db.appData.find()
   
    if 'username' in session:
        return render_template("index.html", taskdata = all_data)
    else:
        return render_template ("login.html",)


#create task in dataabase

@app.route('/insert/', methods=["GET", "POST"])
def insert():
    create_data = {}
    if request.method == "POST":
        create_data['task'] = request.form['task']
        create_data['owner'] = request.form['owner']
        create_data['email'] = request.form['email']
    
        db.appData.insert_one(create_data)
        
        flash("Task added Successfully")

    return redirect ('/')

#update task in dataabase

@app.route('/update/', methods=['POST', 'GET'])
def update():  
     
    if request.method == 'POST':
        
        id = request.values.get("_id")
        
        db.appData.update_one({"_id": ObjectId(id)},
                 {
                     "$set": {"task": request.form.get('task'),
                              "owner": request.form.get('owner'),
                              "email": request.form.get('email')
                              
                              }
                 })
        
    flash("Task Updated Successfully")
    
    return redirect(url_for('index'))


#delete task from dataabase

@app.route('/delete/', methods = ['GET', 'POST'])
def delete():

    if request.method == 'POST':
        
        id = request.values.get("_id")
        db.appData.delete_one ({"_id": ObjectId(id)})
    
    flash("Task Deleted Successfully")
 
    return redirect(url_for('index'))

#Send email

@app.route('/email/<email>/', methods = ['GET', 'POST'])
def email(email):

    notify_id = db.appData.find_one ({'email' : email}, {'_id': 1})
    notify_email = db.appData.find_one ({'email' : email}, {'email': 1, '_id':0})
    notify_owner = db.appData.find_one ({'email' : email}, {'owner': 1, '_id':0})
    notify_task = db.appData.find_one ({'email' : email}, {'task': 1, '_id':0})
    
    notify_id_value = notify_id['_id']
    notify_email_value = notify_email['email']
    notify_owner_value = notify_owner['owner']
    notify_task_value = notify_task['task']

    msg = Message(
                'You have a New Task',
                sender ='crudapptest@gmail.com',
                recipients = [notify_email_value]
               )
    msg.body = f'''Hello { notify_owner_value },

    

    A new task has been assigned to you

    **********************************************
    - {notify_task_value}
    - Task ID:{notify_id_value}
    
    **********************************************
    Regards,
    Task Manager APP
    
    '''
    
    mail.send(msg)
    
    
    flash("Task Owner has been notified")
    
 
    
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    
    if request.method == 'POST':
        existing_user = db.users.find_one({'name' : request.form ['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            db.users.insert_one({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('login'))
        
        flash("This user already exists")

    return render_template('register.html')



@app.route('/login/', methods=['POST','GET'])
def login():
        
    if request.method == 'POST':
        
        login_user = db.users.find_one({'name' : request.form['username']})

        if login_user:
            hashed_password = login_user['password'].decode("utf8")
            if bcrypt.checkpw(request.form['pass'].encode('utf-8'), hashed_password.encode('utf-8')):
                session['username'] = request.form['username']
                return redirect(url_for('index'))

        flash("Unvalid username/password")
        
    return render_template ('login.html')


@app.route('/logout/', methods=['POST','GET'])
def logout():
    session.clear()
    
    return redirect(url_for('login'))

    

if __name__ == "__main__":
    app.run(debug=True)

    