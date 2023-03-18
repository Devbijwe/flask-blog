# from crypt import methods
# from crypt import methods
import json
import math
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from threading import local
from unicodedata import name
from xmlrpc.client import DateTime
from flask import Flask, redirect,render_template, request ,session
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Template
from sqlalchemy import false
from flask_mail import Mail
local_server = True
with open("config.json","r") as c:
    params=json.load(c)["params"]

app = Flask(__name__,template_folder='templates')
app.config.update(
MAIL_SERVER ='smtp.gmail.com' ,
MAIL_PORT ='465',
MAIL_USE_SSL=True,
MAIL_USERNAME=params['gmail_user'],
MAIL_PASSWORD=params['gmail_pswd']
)
mail=Mail(app)
app.config['UPLOAD_FOLDER']=params['upload_location']
app.secret_key = 'super-secret-key'
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] =  params['prod_url']
db = SQLAlchemy(app)

class Post(db.Model):
    srNo = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(50),nullable=False )
    tagLine = db.Column(db.String(50),nullable=False )
    img_url = db.Column(db.String(40),nullable=False )
    details = db.Column(db.String(500),nullable=False)
    postedBy = db.Column(db.String(25), nullable=False)
    date = db.Column(db.String(12),nullable=True)

class Contact(db.Model):
    srNo = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    mobile = db.Column(db.String(14),nullable=False )
    email = db.Column(db.String(25),nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(12),nullable=True)


@app.route("/")
def home():
    post=Post.query.filter_by().all()
    # [0:params['no_of_posts']]
    page=request.args.get('page')
    last=math.ceil(len(post)/int(params['no_of_posts']))
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    post=post[(page-1)*params['no_of_posts']:params['no_of_posts']+params['no_of_posts']]
    if(page==1):
        prev="#"
        next="/?page=" +str(page+1)
     
    if(page==last):
        prev="/?page=" +str(page-1)
        next="#"
    else:
        prev="/?page=" +str(page-1)
        next="/?page=" +str(page+1)
    return render_template('index.html',params=params,posts=post,prev=prev,next=next)
@app.route("/contact",methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        nameF=request.form.get("nameF") 
        emailF=request.form.get("emailF")
        mobileF=request.form.get("mobileF") 
        msgF=request.form.get("msgF")
        entry=Contact(name=nameF,email=emailF,mobile=mobileF,msg=msgF,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
        'New message from '+nameF,
        sender=emailF,
        recipients=[params['gmail_user']],
        body=msgF+ "\nMobile no: "+mobileF
        )
    return render_template("contact.html",params=params)
@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=params,post=post)
@app.route("/about")
def about():
    return render_template("about.html",params=params)
@app.route("/index")
def index():
    post=Post.query.filter_by().all()
    return render_template('index.html',params=params,posts=post)

@app.route("/signup",methods=['GET','POST'])
def signUp():
    if "user" in session and session['user']==params['admin_username']:
        post=Post.query.all()
        return render_template('adminEditor.html',params=params, posts=post)

    if(request.method=='POST'):
        username=request.form.get("username") 
        password=request.form.get("password")
        if (username==params['admin_username'] and password==params['admin_password']):
            session['user']=username
            post=Post.query.all()
            return render_template('adminEditor.html',params=params, posts=post)
        else:
            return render_template('signUp.html',params=params)
            
    else:
        return render_template('signUp.html',params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/signUp")
@app.route("/edit/<string:srNo>",methods=['GET','POST'])
def edit(srNo):
    if "user" in session and session['user']==params['admin_username']:
        if (request.method=='POST'):
            slugF=request.form.get("slugF") 
            titleF=request.form.get("titleF")
            tagLineF=request.form.get("tagLineF")
            img_urlF=request.form.get("img_urlF")  
            detailsF=request.form.get("detailsF")  
            postedByF=request.form.get("postedByF")  
            dateF=request.form.get("dateF")

            if srNo=='0':
                post=Post(slug=slugF,title=titleF,tagLine=tagLineF, img_url= img_urlF,details=detailsF, postedBy= postedByF,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post=Post.query.filter_by(srNo=srNo).first()
                post.slug=slugF
                post.title=titleF
                post.tagLine=tagLineF
                post.img_url=img_urlF
                post.details= detailsF
                post.postedBy=postedByF
                post.date=dateF
                db.session.commit()
                return redirect("/edit/"+srNo)
    if srNo=="0":
        post={"srNo":"0"}
    else:
        post=Post.query.filter_by(srNo=srNo).first()
    return render_template("editPost.html",params=params,posts=post,srNo=srNo)
@app.route('/delete/<string:srNo>', methods=['GET','POST'])
def delete(srNo):
    if "user" in session and session['user']==params['admin_username']:
        post=Post.query.filter_by(srNo=srNo).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/signup")

@app.route("/uploader",methods=["GET","POST"]) 
def uploader():
    if "user" in session and session['user']==params['admin_username']:
        if request.method=="POST":
            f=request.files["fileF"]
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return redirect("/signUp")
if __name__== "__main__":
    app.run(debug=True)