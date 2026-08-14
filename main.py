from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import json

load_dotenv()
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

with open('templates/config.json', 'r') as c:
    para = json.load(c)["para"] 
    
app = Flask(__name__)


app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')  # Use an environment variable for the secret


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/blog')


app.config['UPLOAD_FOLDER'] = os.getenv(
    'UPLOAD_FOLDER',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
)



app.config.update( 
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'), 
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
)

db = SQLAlchemy(app)
mail = Mail(app)



class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable = False )
    email = db.Column(db.String(100), nullable = False)
    phone_num = db.Column(db.String(15), nullable = False ) 
    msg = db.Column(db.String(200), nullable = False )
    date = db.Column(db.String(20), nullable = True )

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable = False )
    content = db.Column(db.String(1500), nullable = False ) 
    date = db.Column(db.String(20), nullable = True )
    slug = db.Column(db.String(25), nullable = False)
    img_file = db.Column(db.String(30), nullable = True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()[0:para["no_of_posts"]]
    return render_template("index.html", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/post")
def post():
    posts = Posts.query.filter_by().all()
    return render_template("/all_posts.html", posts=posts )

    

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", post=post)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        msg = request.form.get('msg')
        entry = Contact(name=name, email=email, phone_num=phone_num, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                        sender=email,
                        recipients=[os.getenv('MAIL_USERNAME')],
                        body=msg + "\n" + phone_num
                        )
        
    return render_template("contact.html")

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == ADMIN_USER:
        posts = Posts.query.all()
        return render_template("dashboard.html", para=para, posts=posts)
    
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == ADMIN_USER and password == ADMIN_PASS):
            session['user']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", para=para, posts=posts )

    return render_template("login.html") 

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == ADMIN_USER:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_content = request.form.get('content')
            box_slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, content=box_content, slug=box_slug, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.content = box_content
                post.slug = box_slug
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", para=para, post=post , sno=sno)


@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == ADMIN_USER:
        if request.method == 'POST':
            f = request.files['img_file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



if __name__ == '__main__':
    app.run(debug=True)

