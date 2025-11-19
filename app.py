from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector as conector
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

login_manager = LoginManager(app)
login_manager.login_view = 'sesion'

class User(UserMixin):
    def __init__(self, idSesion,emailSesion,nombreSesion):
        self.id = idSesion
        self.email = emailSesion
        self.nombre = nombreSesion

    def get_id(self):
        return self.id

@login_manager.user_loader
def cargar_usuario(user_id):
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    sql_user = "SELECT id_user, correo,contrasena,nombre FROM login WHERE id_user=%s"
    cursor.execute(sql_user, (user_id,))
    res_user = cursor.fetchone()
    cursor.close()
    conectar_bd.close()

    if res_user:
        return User(res_user[0],res_user[1], res_user[3])
    
    return None

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/vistgen')
def vistgen():
    conectar_bd = conector.connect(host='localhost', user='root',password='', database='proyecto')
    cursor= conectar_bd.cursor()
    cursor.execute("SELECT Precio,Imagen,Descripcion FROM sillas")
    itemsil = cursor.fetchall()
    conectar_bd.close
    
    return render_template('vistgen.html',itemsil=itemsil)

@app.route('/registra', methods=['GET', 'POST'])
def registra():
    if request.method == 'POST':
        u_name = request.form['user_name']
        u_apell = request.form['user_apell']
        u_correo = request.form['user_correo']
        u_contra = request.form['user_contra']

        uhash = generate_password_hash(u_contra, method='pbkdf2', salt_length=16)

        conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
        cursor = conectar_bd.cursor()
        sql = "INSERT INTO login (nombre, apellido, correo, contrasena) VALUES (%s, %s, %s, %s)"
        values = (u_name, u_apell, u_correo, uhash)

        cursor.execute(sql, values)
        conectar_bd.commit()
        cursor.close()
        conectar_bd.close()

        flash("Usuario agregado correctamente")
        return redirect(url_for('index'))

    return render_template('registra.html')

@app.route('/sesion', methods=['GET', 'POST'])
def sesion():
    msjo=""
    if request.method == 'POST':
        correo_user = request.form['com_correo']        
        pass_user = request.form['com_contra']
        conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
        cursor = conectar_bd.cursor()
        sql_sesion = "SELECT id_user,correo,contrasena,nombre FROM login WHERE correo=%s"
        cursor.execute(sql_sesion, (correo_user,))
        resultSesion = cursor.fetchone()
        cursor.close()
        conectar_bd.close()

        if resultSesion:
            idResid = resultSesion[0]
            passRespass = resultSesion[2]

            if check_password_hash(passRespass, pass_user):
                logguser = User(idResid, correo_user, resultSesion[3])
                login_user(logguser)
                return redirect(url_for('vistgen'))
            else:
                msjo= "Correo o contraseña incorrectos"
        else:
            msjo= "Correo o contraseña incorrectos"

    return render_template('sesion.html', msjo=msjo)

@app.route('/logout', methods=['GET','POST'])
def logout():
   if request.method == 'POST':
      return redirect(url_for('index'))

   return render_template('logout.html')

@app.route('/chat', methods=['GET','POST'])
def chat():
   return render_template('chat.html')

@app.route('/borrarcu',methods=['GET','POST'])
@login_required
def borrarcu():
    user_id =current_user.id
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    sqlEliminar = "DELETE FROM login WHERE id_user=%s"
    cursor.execute(sqlEliminar, (user_id,))
    conectar_bd.commit()
    cursor.close()
    conectar_bd.close()
    logout_user()
    flash(f"Cuenta eliminada.")
    return redirect(url_for('index'))

@app.route('/editar', methods=['GET', 'POST'])
@login_required
def editar():
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    cursor.execute("SELECT nombre, apellido, correo FROM login WHERE id_user=%s", (current_user.id,))
    user_data = cursor.fetchone()
    if not user_data:
        flash("No se pudo encontrar el usuario.")
        return redirect(url_for('index'))
    if request.method == 'POST':
        ac_name = request.form['up_name']
        ac_apell = request.form['up_apell']
        ac_correo = request.form['up_correo']
        ac_contra = request.form['up_contra']


        cursor.execute("SELECT * FROM login WHERE correo=%s AND id_user != %s", (ac_correo, current_user.id))
        if cursor.fetchone():
            flash("Este correo ya está en uso por otro usuario.")
            cursor.close()
            conectar_bd.close()
            return redirect(url_for('editar'))


        if ac_contra:
            uhash = generate_password_hash(ac_contra, method='pbkdf2', salt_length=16)
        else:
            uhash = user_data[3] 
        sql_update = "UPDATE login SET nombre=%s, apellido=%s, correo=%s, contrasena=%s WHERE id_user=%s"
        values = (ac_name, ac_apell, ac_correo, uhash, current_user.id)

        cursor.execute(sql_update, values)
        conectar_bd.commit()

        cursor.close()
        conectar_bd.close()

        flash("Datos actualizados correctamente.")
        return redirect(url_for('index'))
    return render_template('editarcue.html', user_data=user_data)
    
@app.route('/agregar_al_carrito', methods=['POST','GET'])
def agregar_al_carrito():

    producto_precio = request.form.get('producto_precio')
    producto_imagen = request.form.get('producto_imagen')
    producto_descripcion = request.form.get('producto_descripcion')
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    cursor.execute("""INSERT INTO carrito (Precio, Imagen, Descripcion)VALUES (%s, %s, %s)""", (producto_precio, producto_imagen, producto_descripcion))
    conectar_bd.commit()
    conectar_bd.close()
    
    return redirect(url_for('ver_carrito'))

@app.route('/ver_carrito', methods=['GET','POST'])
def ver_carrito():
    
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    
    # Seleccionar los productos del carrito con sus detalles (sin 'ID')
    cursor.execute("""SELECT precio, imagen, descripcion,id_carrito FROM carrito""")
    carrito_items = cursor.fetchall()
    cursor.execute("SELECT SUM(precio) FROM carrito")
    total = cursor.fetchone()[0]  # Obtiene el valor de la suma total
    
    conectar_bd.close()
    
    return render_template('carrito.html', items=carrito_items, total=total)

@app.route('/eliminar/<int:id_carrito>', methods=['GET','POST'])
def eliminar(id_carrito):
    conectar_bd = conector.connect(host='localhost', user='root', password='', database='proyecto')
    cursor = conectar_bd.cursor()
    
    # Eliminar el producto del carrito usando su ID
    cursor.execute("DELETE FROM carrito WHERE id_carrito = %s", (id_carrito,))
    conectar_bd.commit()
    conectar_bd.close()
    return redirect(url_for('ver_carrito'))


# Rutas para sillas, mesas, sofas, cuadros y plantas

@app.route('/mesas')
def mesas():
    conectar_bd = conector.connect(host='localhost', user='root',password='', database='proyecto')
    cursor= conectar_bd.cursor()
    cursor.execute("SELECT Precio,Imagen,Descripcion FROM mesas")
    itemsi= cursor.fetchall()
    conectar_bd.close
    return render_template('mesas.html',itemsi=itemsi)

@app.route('/sofas')
def sofas():    
    conectar_bd = conector.connect(host='localhost', user='root',password='', database='proyecto')
    cursor= conectar_bd.cursor()
    cursor.execute("SELECT Precio,Imagen,Descripcion FROM sofas")
    itemsi = cursor.fetchall()
    conectar_bd.close
    return render_template('sofas.html',itemsi=itemsi)

@app.route('/cuadros')
def cuadros():
    conectar_bd = conector.connect(host='localhost', user='root',password='', database='proyecto')
    cursor= conectar_bd.cursor()
    cursor.execute("SELECT Precio,Imagen,Descripcion FROM cuadros")
    itemsi = cursor.fetchall()
    conectar_bd.close
    return render_template('cuadros.html',itemsi=itemsi)

@app.route('/plantas')
def plantas():
    conectar_bd = conector.connect(host='localhost', user='root',password='', database='proyecto')
    cursor= conectar_bd.cursor()
    cursor.execute("SELECT Precio,Imagen,Descripcion FROM plantas")
    itemsi = cursor.fetchall()
    conectar_bd.close
    return render_template('plantas.html',itemsi=itemsi)

@app.route("/footer")
def footer():
    return render_template('footer.html')

if __name__ == '__main__':
    app.run(debug=True)



