from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='flask_mongo_crud_alumnos/templates')
app.secret_key = "clave_secreta_segura"

# 🔹 URI de MongoDB (local o Atlas)
# Para Atlas: mongodb+srv://usuario:contraseña@cluster0.xxxxx.mongodb.net/cleto_reyes
app.config["MONGO_URI"] = "mongodb+srv://cleto:G123456789@cluster0.lchkp7j.mongodb.net/cleto_reyes"
mongo = PyMongo(app)

# ------------------- RUTAS PRINCIPALES -------------------

@app.route('/')
def inicio():
    productos = list(mongo.db.productos.find())
    usuario = session.get('usuario')
    return render_template('inicio.html', productos=productos, usuario=usuario)

# ------------------- REGISTRO -------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if mongo.db.usuarios.find_one({'email': email}):
            flash("⚠️ Este correo ya está registrado.")
            return redirect(url_for('register'))

        mongo.db.usuarios.insert_one({'nombre': nombre, 'email': email, 'password': password})
        flash("✅ Registro exitoso. Inicia sesión.")
        return redirect(url_for('login'))

    return render_template('register.html')

# ------------------- LOGIN -------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        usuario = mongo.db.usuarios.find_one({'email': email})
        if usuario and check_password_hash(usuario['password'], password):
            session['usuario'] = usuario['nombre']
            session['usuario_id'] = str(usuario['_id'])
            session['carrito'] = []
            return redirect(url_for('inicio'))
        else:
            flash("❌ Usuario o contraseña incorrectos.")
            return redirect(url_for('login'))

    return render_template('login.html')

# ------------------- LOGOUT -------------------

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Has cerrado sesión correctamente.")
    return redirect(url_for('inicio'))

# ------------------- AGREGAR AL CARRITO -------------------

@app.route('/agregar_carrito/<producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    producto = mongo.db.productos.find_one({'_id': ObjectId(producto_id)})
    if not producto:
        flash("⚠️ Producto no encontrado.")
        return redirect(url_for('inicio'))

    carrito = session.get('carrito', [])

    # Buscar si el producto ya está en el carrito
    for item in carrito:
        if item['producto_id'] == str(producto['_id']):
            item['cantidad'] += 1
            break
    else:
        carrito.append({
            'producto_id': str(producto['_id']),
            'nombre': producto['nombre'],
            'precio': producto['precio'],
            'imagen': producto['imagen'],
            'cantidad': 1
        })

    session['carrito'] = carrito
    flash(f"🛒 {producto['nombre']} se agregó al carrito.")
    return redirect(url_for('carrito'))

# ------------------- MOSTRAR CARRITO -------------------

@app.route('/carrito')
def carrito():
    carrito = session.get('carrito', [])
    usuario = session.get('usuario')
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    return render_template('carrito.html', carrito=carrito, total=total, usuario=usuario)

# ------------------- ACTUALIZAR CANTIDAD -------------------

@app.route('/actualizar_carrito/<producto_id>', methods=['POST'])
def actualizar_carrito(producto_id):
    nueva_cantidad = int(request.form['cantidad'])
    carrito = session.get('carrito', [])

    for item in carrito:
        if item['producto_id'] == producto_id:
            item['cantidad'] = nueva_cantidad
            break

    session['carrito'] = carrito
    flash("✅ Carrito actualizado correctamente.")
    return redirect(url_for('carrito'))

# ------------------- ELIMINAR DEL CARRITO -------------------

@app.route('/eliminar_del_carrito/<producto_id>', methods=['POST'])
def eliminar_del_carrito(producto_id):
    carrito = session.get('carrito', [])
    carrito = [item for item in carrito if item['producto_id'] != producto_id]
    session['carrito'] = carrito
    flash("🗑️ Producto eliminado del carrito.")
    return redirect(url_for('carrito'))

# ------------------- PAGO (GET) -------------------

@app.route('/pago', methods=['GET'])
def pago():
    carrito = session.get('carrito', [])
    usuario = session.get('usuario')

    if not usuario:
        flash("Debes iniciar sesión para continuar con el pago.")
        return redirect(url_for('login'))

    if not carrito:
        flash("Tu carrito está vacío.")
        return redirect(url_for('inicio'))

    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    return render_template('pago.html', carrito=carrito, total=total, usuario=usuario)

# ------------------- PROCESAR PAGO (POST) -------------------

@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    usuario = session.get('usuario')
    usuario_id = session.get('usuario_id')
    carrito = session.get('carrito', [])

    if not usuario or not carrito:
        flash("⚠️ Error: no hay usuario o el carrito está vacío.")
        return redirect(url_for('inicio'))

    total = sum(float(item['precio']) * item['cantidad'] for item in carrito)

    # Guardar el pedido en MongoDB
    mongo.db.pedidos.insert_one({
        'usuario': usuario,
        'usuario_id': usuario_id,
        'productos': carrito,
        'total': total,
        'estado': 'Pagado'
    })

    # Vaciar carrito
    session['carrito'] = []

    flash("✅ Pago procesado con éxito. ¡Gracias por tu compra!")
    return redirect(url_for('inicio'))

# ------------------- MAIN -------------------

if __name__ == '__main__':
    app.run(debug=True)
5
