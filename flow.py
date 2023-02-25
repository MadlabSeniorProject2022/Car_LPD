import cv2
import numpy as np
import pytesseract
from local_utils import detect_lp
from os.path import splitext,basename
from keras.models import model_from_json
from tensorflow.keras.utils import load_img, img_to_array
from keras.applications.mobilenet_v2 import preprocess_input
from sklearn.preprocessing import LabelEncoder
import glob


def load_model(path):
    try:
        path = splitext(path)[0]
        with open('%s.json' % path, 'r') as json_file:
            model_json = json_file.read()
        model = model_from_json(model_json, custom_objects={})
        model.load_weights('%s.h5' % path)
        print("Loading model successfully...")
        return model
    except Exception as e:
        print(e)

wpod_net_path = "wpod-net.json"
wpod_net = load_model(wpod_net_path)
sr = cv2.dnn_superres.DnnSuperResImpl_create()
modelPath = 'LapSRN_x8.pb'
sr.readModel(modelPath)

def upscale(path):
    #modelPath = 'LapSRN_x8.pb'
    img = cv2.imread(path)
    sr.setModel("lapsrn",8)
    img = sr.upsample(img)
    return img

def preprocess_image(image_path,resize=False):
    img = cv2.imread(image_path)
    img = upscale(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255
    if resize:
        img = cv2.resize(img, (224,224))
    return img

def get_plate(image_path, Dmax=608, Dmin = 608):
    vehicle = preprocess_image(image_path)
    ratio = float(max(vehicle.shape[:2])) / min(vehicle.shape[:2])
    side = int(ratio * Dmin)
    bound_dim = min(side, Dmax)
    _ , LpImg, _, cor = detect_lp(wpod_net, vehicle, bound_dim, lp_threshold=0.5)
    return vehicle, LpImg, cor

def segmentation(img):
    vehicle, LpImg,cor = get_plate(img)
    if (len(LpImg)): #check if there is at least one license image
    # Scales, calculates absolute values, and converts the result to 8-bit.
        plate_image = cv2.convertScaleAbs(LpImg[0], alpha=(255.0))
    # convert to grayscale and blur the image
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray,(5,5),0)
    # Applied inversed thresh_binary 
        binary = cv2.threshold(blur, 80, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C)[1]
        kernel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thre_mor = cv2.morphologyEx(binary, cv2.MORPH_DILATE, kernel3)
    fullTempPath ="ocr_result.txt"
    text = pytesseract.image_to_string(thre_mor, config='tessdata-dir /content/drive/MyDrive/Plate_detect_and_recognize/tessdata --psm 6 -oem 1 --dpi 600 -c tessedit_char_whitelist=กขฆงจฉชฌญฎฐธพภวศษสฒณตถบปผยรลนฬอฮทมฟ0123456789')
    
    #uncomment these line to ocr in batch
    '''
    file1 = open(fullTempPath, "a+")
    file1.write("\n")
    file1.write(text+"\n")
    file1.close() 
    '''
