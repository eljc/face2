import os
import numpy
import cv2
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, select
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    redirect,
    url_for,
    render_template,
    Response,
    flash
)
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from .api_face import *

app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)
app.secret_key = "chave_secreta"

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    def __init__(self, email):
        self.email = email

class Acolhido(db.Model):
    __tablename__ = 'acolhido'
    id_acolhido=db.Column(db.Integer,primary_key=True)
    nome=db.Column(db.String(50),nullable=False)
    nome_foto = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.Text, nullable=False)
    def __init__(self, nome, nome_foto, foto):
        self.nome = nome
        self.nome_foto = nome_foto
        self.foto = foto

class Registro(db.Model):
    __tablename__ = 'registros'
    id_registro = db.Column(db.Integer, primary_key=True)
    acolhido = db.Column(db.Integer, ForeignKey("acolhido.id_acolhido"))
    data_e_hora_registro = db.Column(db.DateTime)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    # Put any other methods you need here
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():

    nome = request.form['nome']
    print(nome)

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Nenhuma imagem selecionada')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = nome+'.jpg'
        #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(os.path.join(app.config["MEDIA_FOLDER"], nome+'.jpg'))        
        # print('upload_image filename: ' + filename)
        flash('Imagem enviada com sucesso')
        print('filename', filename)
        print(app.config["MEDIA_FOLDER"])
        arquivo = app.config["MEDIA_FOLDER"]+'/'+filename
        acolhido = Acolhido(nome=nome, nome_foto=filename, foto=arquivo)
        db.session.add(acolhido)
        db.session.commit()
        return render_template('index.html', filename=filename)
    else:
        flash('Imagens válidas: - png, jpg, jpeg, gif')
        return redirect(request.url)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/display/<filename>', methods=['GET'])
def display_image(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)

@app.route('/reconhecer')
def local():
    return render_template('local.html')

@app.route('/video')
def remote():
    return Response(open('./static/video.html').read(), mimetype="text/html")

@app.route('/lista')
def lista():
    print('busca por registros')
    return render_template('lista.html')

@app.route('/image', methods=['POST'])
def image():
    try:
        image_file = request.files['image']  # get the image

        print("image_file", image_file)

        # Set an image confidence threshold value to limit returned data
        threshold = request.form.get('threshold')
        if threshold is None:
            threshold = 0.5
        else:
            threshold = float(threshold)

        uploadWidth = request.form.get('uploadWidth')
        if uploadWidth is None:
            uploadWidth = 800.0
        else:
            uploadWidth = float(uploadWidth)

        uploadHeight = request.form.get('uploadHeight')
        if uploadHeight is None:
            uploadHeight = 600.0
        else:
            uploadHeight = float(uploadHeight)
        # finally run the image through tensor flow object detection`
        # image_object = cv2.imread('face-images/mike/tuan.jpg')
        image_object = cv2.imdecode(numpy.fromstring(image_file.read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
        response = api_face.predict(image_object, threshold, uploadWidth, uploadHeight)

        print('response', response)
        return response

    except Exception as e:
        print('POST /image error: %e' % e)
        return e