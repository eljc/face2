import numpy as np
import cv2
import json
import face_recognition
import os

eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades+'haarcascade_eye_tree_eyeglasses.xml')


def predict(test_image, threshold, uploadWidth, uploadHeight, faces_codificadas, lista_nomes):
    texto_imagem = ''
    piscou = False
    nome_acolhido = ''
    if(lista_nomes == None):
        print('lista vazia')
    else:
        print('Lista atual: ', lista_nomes)
    #print('faces_codificadas', faces_codificadas)
    #nomeImagens = ['Elder', 'Aline']

    imgS = cv2.resize(test_image, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    output = []

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    item = Object()
    item.version = "0.0.1"
    item.numObjects = len(facesCurFrame)
    item.threshold = threshold
    output.append(item)
    
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        #matches = face_recognition.compare_faces(listaEncodeConhecido, encodeFace)
        #faceDis = face_recognition.face_distance(listaEncodeConhecido, encodeFace)
        matches = face_recognition.compare_faces(faces_codificadas, encodeFace)
        faceDis = face_recognition.face_distance(faces_codificadas, encodeFace)
        # print(faceDis)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            #name = nomeImagens[matchIndex].upper()
            #print('Posicao: ', matchIndex)
            nome = lista_nomes[matchIndex]
            top, right, bottom, left = faceLoc
            texto_imagem = nome
            #nome_acolhido = 'Elder' #str(nome)
#            nome_acolhido = str(nome)           
            #print('Reconhecido: ', name)
            #print('variaveis: ',top, right, bottom, left)
            
            eyes = eye_cascade.detectMultiScale(test_image, scaleFactor=1.2, minNeighbors=4)
            #print('olhos: ',len(eyes))
            if(len(eyes)==2 and piscou==False):
                texto_imagem = 'Pisque por favor'

            if(len(eyes)==0 and piscou==False):
                #print('piscou')
                piscou = True
                nome_acolhido = str(nome)
                texto_imagem = 'Presenca registrada'

            elif piscou :
                 texto_imagem = 'Presenca registrada'    

            top, right, bottom, left = top*4, right*4, bottom*4, left*4

            # Add some metadata to the output
            item = Object()
            item.class_name = "{}".format(texto_imagem)
            item.nome = texto_imagem
            item.score = 1
            item.x = left
            item.y = top
            item.height = bottom - top
            item.width = right - left

            output.append(item)

    outputJson = json.dumps([ob.__dict__ for ob in output])
    return outputJson, nome_acolhido


def obter_imagens_codificadas(imagens):
    lista_codificada = []
    for foto in imagens:
        image = face_recognition.load_image_file(foto)
        face_encoding = face_recognition.face_encodings(image)[0]
        lista_codificada.append(face_encoding)
    return lista_codificada


# added to put object in JSON
class Object(object):
    def __init__(self):
        self.name = "Reconhecimento Facial"

    def toJSON(self):
        return json.dumps(self.__dict__)
