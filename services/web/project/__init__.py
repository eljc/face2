import os
import numpy
import cv2
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, select
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
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
#from .api_face import *
import api_face

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
    statement = db.select(Acolhido)    
    acolhidos = db.session.execute(statement).all()    
    print('TIPO ACOLHIDOS> ', type(acolhidos))
    global lista_nomes 
    global lista_imagens
    for aco in acolhidos:        
        for a in aco:
            lista_nomes.append(a.nome)
            lista_imagens.append(a.foto)
    
    return render_template('reconhecer.html')

def registrar_db(nome_acolhido):
    global lista_nomes
    global lista_imagens

    if nome_acolhido:
        resultado = Acolhido.query.filter_by(nome=nome_acolhido).first()
        id_acolhido = resultado.id_acolhido
        registro = Registro(acolhido=id_acolhido, data_e_hora_registro=datetime.utcnow())
        db.session.add(registro)

        try:
            db.session.commit()
            print('lista de nomes: ', lista_nomes)
            indice = lista_nomes.index(nome_acolhido)
            print('remover da lista indice: ', indice, 'Tamnho: ', len(lista_nomes))
            lista_nomes.remove(nome_acolhido)
            valor_remover = lista_imagens[indice]
            lista_imagens.remove(valor_remover)
        except Exception as e:
            print(e)
        else:
            print('OK')

class Registros_class:
    def __init__(self, nome, data, hora):
        self.nome = nome
        self.data = data
        self.hora = hora

@app.route('/video')
def remote():
    return Response(open('./static/video.html').read(), mimetype="text/html")

@app.route('/lista')
def lista():
    statement = db.select(Acolhido.nome, Registro.data_e_hora_registro).join(Registro).order_by(Registro.data_e_hora_registro.desc())
    # list of tuples
    registros  = db.session.execute(statement).all()
    #print(type(registros))
    lista_registros = []
    for reg in registros:
        nome = reg.nome
        data = reg.data_e_hora_registro.strftime('%d/%m/%Y')
        hora = reg.data_e_hora_registro.strftime('%H:%M:%S')
        registro = Registros_class(nome, data, hora)        
        lista_registros.append(registro)
    return render_template('lista.html', registros=lista_registros)

@app.route('/image', methods=['POST'])
def image():
    global lista_nomes 
    global lista_imagens
    nome_acolhido = ''
    faces_codificadas = api_face.obter_imagens_codificadas(lista_imagens)
    #print(faces_codificadas)
    #print('Posicao Lista Geral: ', acolhidos)

    try:
        image_file = request.files['image']  # get the image

        #print("image_file", image_file)

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
        image_object = cv2.imdecode(numpy.frombuffer(image_file.read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
        #response = api_face.predict(image_object, threshold, uploadWidth, uploadHeight)

        response, nome_acolhido = api_face.predict(image_object, threshold, uploadWidth, uploadHeight, faces_codificadas, lista_nomes)

        #print(type(response))        
        #print(response.find('nome_imagem'))
        registrar_db(nome_acolhido)

        #print('response', response)
        return response

    except Exception as e:
        print('POST /image error: %e' % e)
        return e