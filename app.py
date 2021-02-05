from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from flask_mail import Mail, Message
import smtplib

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='thisissecretkey'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='meghdut1996@gmail.com'
app.config['MAIL_PASSWORD']='Meghdut@_2018'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(db.Model, UserMixin):
    __tablename__='user'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), unique=True)
    password=db.Column(db.String(20))
    email=db.Column(db.String(120), unique=True)
    
    def hash_password(self, password):
        self.password=generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)

    
class Product(db.Model):
    __tablename__='product'
    id=db.Column(db.Integer, primary_key=True)
    code=db.Column(db.String(30), unique=True)
    name=db.Column(db.String(50))
    quantity=db.Column(db.Integer)
    tz_india=pytz.timezone("Asia/Calcutta")
    created_at=db.Column(db.DateTime, default=datetime.now(tz_india))
    updated_at=db.Column(db.DateTime, default=datetime.now(tz_india))
    adjustment_line=db.relationship('AdjustmentDetail', backref='adjustment_detail')
    purchased_line=db.relationship('PurchaseDeatail', backref='purchase_detail')
    
    def check_fields(self, mode):
        error_list=[]
        if self.code== '':
            error_list.append("Invalid Product Code")
        else:
            check_prod=Product.query.filter_by(code=self.code).first()
            if check_prod:
                if mode=='Add':
                    error_list.append(f'{self.code} already exist')
        if self.name== '':
            error_list.append('Invalid Product Name')
        
        if not self.quantity.isdigit():
            error_list.append("Invalid Product Quantity")
        else:
            self.quantity=int(self.quantity)
        return error_list
    
class AdjustmentHeader(db.Model):
    __tablename__='adjustment_header'
    id=db.Column(db.Integer, primary_key=True)
    description=db.Column(db.String(50))
    adjustment_details=db.relationship('AdjustmentDetail', backref='adjustment_reference')
    
class AdjustmentDetail(db.Model):
    __tablename__='adjustment_detail'
    id=db.Column(db.Integer, primary_key=True)
    quantity_adjust=db.Column(db.Integer)
    adjustment_header_id=db.Column(db.Integer, db.ForeignKey('adjustment_header.id'))
    product_id=db.Column(db.Integer, db.ForeignKey('product.id'))

class PurchaseHeader(db.Model):
    __tablename__='purchase_header'
    id=db.Column(db.Integer, primary_key=True)
    description=db.Column(db.String(30))
    status=db.Column(db.String(30))
    purchase_details=db.relationship('PurchaseDeatail', backref='purchase_reference')

class PurchaseDeatail(db.Model):
    __tablename__='purchase_detail'
    id=db.Column(db.Integer, primary_key=True)
    quantity_purchase=db.Column(db.Integer)
    quantity_receieve=db.Column(db.Integer)
    purchase_header_id=db.Column(db.Integer, db.ForeignKey('purchase_header.id'))
    product_id=db.Column(db.Integer, db.ForeignKey('product.id'))

    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def Home():
    return render_template("sign-in.html")

@app.route("/register",methods=['GET','POST'])
def SignUp():
    if request.method=="GET":
        return render_template("register.html")
    if request.method=="POST":
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        existing_mail=User.query.filter_by(email=email).first()
        if existing_mail:
            return render_template("register.html",message="User already registered !")
        else:
            try:
                user=User(username=username, password=password, email=email)
                user.hash_password(password=user.password)
                msg=Message('Registration Confirmation', sender='meghdut1996@gmail.com', recipients=[user.email])
                msg.body="Thanks for joining with us"
                mail.send(msg)
            except smtplib.SMTPAuthenticationError:
                message="Username and Password not accepted !!"
                css_alert_class='alert-warning'
                return render_template("register.html",**locals())
            else:
                db.session.add(user)
                db.session.commit()
                return render_template("register.html",message="Registration Successfull! Confirmation mail sent")

@app.route("/signin/", methods=['POST'])
def signin():
    if request.method=="POST":
        ### get the values from the html form
        username=request.form.get('username')
        password=request.form.get('password')
        #query if the user already exist
        user=User.query.filter_by(username=username).first()
        if user and user.check_password(password=password):
            login_user(user)
            return redirect("/product")
        else:
            return render_template('sign-in.html',message="Invalid Login !")   

                               
@app.route("/product")
@login_required
def product():
    all_products=Product.query.order_by(Product.updated_at.desc()).all()
    return render_template("products.html", all_products=all_products)

@app.route("/add_product",methods=['GET','POST'])
@login_required
def AddProduct():
    #multi line assign
    message, css_alert_class, code, name, quantity=('', '', '', '', '')
    if request.method=="GET":
        return render_template("addnewproduct.html")
    if request.method=="POST":
        code=request.form['code'] 
        name=request.form['name']
        quantity=request.form['quantity']
        new_product=Product(code=code, name=name, quantity=quantity)
        error_list=new_product.check_fields(mode='Add')
        
        if error_list:
            message='[ '+', '.join(error_list)+' ]'
            css_alert_class='alert-warning'
            return render_template('addnewproduct.html',**locals())
        else:
            db.session.add(new_product)
            db.session.commit()
            message=f'{new_product.code} added'
            css_alert_class='alert-success'
            code, name, quantity=('', '', '')
            return render_template('addnewproduct.html', **locals())
          

@app.route("/edit_product/<id>",methods=['POST','GET'])
@login_required
def EditProduct(id):
    message, css_alert_class, code, name, quantity=('', '', '', '', '')
    editproduct=Product.query.filter_by(id=id).first_or_404()
    if editproduct:
        if request.method=="GET":
            code=editproduct.code
            name=editproduct.name 
            quantity=editproduct.quantity
            return render_template('edit_product.html', **locals())
        
        if request.method=="POST":
            ## retrieve values from html form
            code=request.form['code']
            name=request.form['name']
            quantity=request.form['quantity']
            ###query if the product is already existing
            existing_product=Product.query.filter(Product.code==code, Product.id!=editproduct.id).count()
            if existing_product:
                error_list=[f'{editproduct.code} is already taken']
            else:
                #save new values to the new product
                editproduct.code=code
                editproduct.name=name
                editproduct.quantity=quantity
                #validate if fields are blank
                error_list=editproduct.check_fields(mode='Edit')
            
            if error_list:
                message='[ '+', '.join(error_list)+' ]'
                css_alert_class='alert-warning'
                return render_template('edit_product.html',**locals())
            else:
                #save to database
                db.session.commit()
                message=f'{editproduct.code} updated'
                css_alert_class='alert-success'
                return render_template('edit_product.html', **locals())
        
    else:
        return "Invalid Request"

@app.route("/delete_product/<id>", methods=['POST'])
@login_required
def delete_product(id):
    if request.method=="POST":    
        deleteproduct=Product.query.filter_by(id=id).first_or_404()
        if deleteproduct:
            db.session.delete(deleteproduct)
            db.session.commit()
            return redirect("/product")

    
@app.route("/adjustment")
@login_required
def adjustment():
    return render_template("adjustment.html")

@app.route("/purchase")
@login_required
def purchase():
    return render_template("purchase.html")


@app.route("/changepassword", methods=['POST','GET'])
@login_required
def changepassword():
    if request.method=='GET':
        return render_template("changepassword.html")
    
    if request.method=="POST":
        save_status=''
        css_alert_class=''
        username=request.form['username']
        oldpassword=request.form['oldpassword']
        newpassword=request.form['newpassword']
        
        user=User.query.filter_by(username=username).first()
        if user and user.check_password(password=oldpassword) and newpassword!='':
            user.hash_password(password=newpassword)
            db.session.commit()
            save_status='Password change complete!'
            css_alert_class='alert-success'
        else:
            save_status='Password change failed!'
            css_alert_class='alert-warning'
        return render_template("changepassword.html", message=save_status, css_alert_class=css_alert_class)        

    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


    
if __name__=="__main__":
    app.run(debug=True)