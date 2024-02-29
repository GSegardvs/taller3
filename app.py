import os

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy

#application init
app = Flask(__name__)
app.secret_key = 'any random string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

INSTALLED_APPS = [
    'django_bootstrap_icons'
]


UPLOAD_FOLDER = './static/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


#database init 
db = SQLAlchemy(app)
def create_app():

#create the Flask application


    #initialize SQLAlchemy with this Flask application
    db.init_app(app)
    


    with app.app_context():
        db.create_all()
        db.session.commit()

    return app


app.config['products'] = []
app.config['user'] = None


#database tables

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200))

   

#route
@app.route('/')
def home():
    productos = db.session.query(Product).all()
    return render_template('home.html', products=productos, adminUser = app.config['user'])

def serialize(obj) :
    return  {'id': obj.id, 'title': obj.title, 'description': obj.description, 'price': obj.price}

@app.route('/borrar',  methods=('GET', 'POST'))
def borrar():
    prod = db.session.query(Product).get(request.args.get('product'))
    db.session.delete(prod)
    db.session.commit()
    products = db.session.query(Product).all()
    return render_template('home.html', products=products,  adminUser = app.config['user'])

@app.route('/comprar',  methods=('GET', 'POST'))
def comprar():
    
     if request.method == 'POST':
          prodId = request.form['prod']
          productDB = db.session.query(Product).get(prodId)
          productJson = {'id': productDB.id, 'title': productDB.title, 'description': productDB.description, 'price': productDB.price, 'image': productDB.image}
          if (app.config['products'] is None) :
              app.config['products'] = []
          app.config['products'].append(productJson)  
          if not app.config['user']:
              app.config['user']= 'user'
          return render_template('confirmacion.html', adminUser = app.config['user'])
     else:
        prod =db.session.query(Product).get(request.args.get('product'))
        return render_template('comprar.html', producto= prod, adminUser = app.config['user'])

@app.route('/remover',  methods=('GET', 'POST'))
def remover():
     if request.method == 'POST':
          prodId = request.form['prod']
          productDB =db.session.query(Product).get(prodId)
        #   productJson = {'id': productDB.id, 'title': productDB.title, 'description': productDB.description, 'price': productDB.price}
          app.config['products'].append(productDB)
          return render_template('confirmacion.html', adminUser = app.config['user'])
     else:
        prodId = request.args.get('product')
        if app.config['products'] is None:
            app.config['products'] = []
        for element in app.config['products']:
            result = app.config['products'].remove(element)
        return render_template('cart.html', products=app.config['products'], adminUser = app.config['user'])
     


def serialize_sqlalchemy_obj(obj):
    if isinstance(obj, Product):
        # Convert the SQLAlchemy model object to a dictionary
        return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
    raise TypeError(f"Object of type {type(obj)} is not serializable")


@app.route('/cart',  methods=('GET', 'POST'))
def cart():
        
        if request.method == 'POST':
            app.config['products'] = None
            return render_template('confirmacion.html', message="Gracias por su compra", adminUser = app.config['user'])
        else : 
            total_price = 0
            if app.config['products'] is None:
                app.config['products'] = []
            for element in app.config['products']: 
                if 'price' in element:
                    total_price += element['price']
            return render_template('cart.html', total= total_price,  products = app.config['products'], adminUser = app.config['user'])

@app.route('/registro',  methods=('GET', 'POST'))
def registro():
    if request.method == 'POST':
        user1 = request.form['user']
        password1 = request.form['password']

        new_user = User(user=user1, password=password1)
        
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))
    else:
        return render_template('registro.html', adminUser = app.config['user'])

@app.route('/iniciosesion', methods=('GET', 'POST'))
def iniciosesion():
    if request.method == 'POST':
        user1 = request.form['username']
        password = request.form['password']
        if user1 == 'admin' and password == 'admin':
            app.config['user'] = 'admin'
            products = db.session.query(Product).all()
            return render_template('home.html', products=products,  adminUser = app.config['user'])
             
        userdb = db.session.query(User).filter(User.user==user1, User.password==password).first()
        if userdb :
             products = db.session.query(Product).all()
             app.config['user'] = user1
             return render_template('home.html', products=products, adminUser = app.config['user'])

        else:
            return render_template("iniciosesion.html", message = 'Credenciales invalidas') 
    else:
        return render_template('iniciosesion.html')

@app.route('/cierre', methods=['GET','POST'])
def cierre():
    app.config['user'] = None
    return render_template('iniciosesion.html')

#products routes
@app.route('/products', methods=['GET','POST'])
def create_product():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])


        if 'file1' not in request.files:
            return redirect(request.url)
        file = request.files['file1']

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))




        new_product = Product(title=title, description=description, price=price, image=file.filename)
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('home'))
    else:
        return render_template('create_product.html', adminUser = app.config['user'])


@app.route('/delete_product/<int:id>')
def delete_product(id):
    product = db.session.query(Product).get(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('home'))


#run application
if __name__ == '__main__':
    app.run(debug=True)
