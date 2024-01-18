import numpy as np # linear algebra
import pandas as pd # data processing
import rawpy
import cv2 as cv
import matplotlib.pyplot as plt
import math
#import utils

def get_black_color_range():
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([179, 255, 75])
    black_color_range = {'black': [lower_black, upper_black]}
    return black_color_range

def get_contours(img,is24Checker):
    #is24Checker = True
    COLOR_RANGE = get_black_color_range()
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)  # Convert BGR to HSV
    img_hsv = cv.blur(img_hsv, (5,5)) #Smoothens the sharp edges and cover highlights
    black_mask = cv.inRange(
        img_hsv, COLOR_RANGE['black'][0], COLOR_RANGE['black'][1])

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))
    mask = cv.morphologyEx(black_mask.copy(), cv.MORPH_OPEN, kernel)

    cnts, _ = cv.findContours(
        mask.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    #Fill the black color to get the card
    #Get Rectangles
    cnts = list(filter(lambda x: len(cv.approxPolyDP(
            x, 0.05*cv.arcLength(x, True), True) == 4), cnts))
    cnts = sorted(cnts, reverse=True, key=cv.contourArea)
    #sort contours based on size
    return cnts

def get_scaling_ratio(w,h):
    #directly get scaling ratio by comparing diagonal length
    d = math.sqrt(w**2 + h**2)
    #3191.34617~3245.0 pixels for diagonal
    scaling_ratio = d / 3191.347    
    return scaling_ratio

def rotate_coordinates(crd):
    if(crd[1][0][1] < crd[0][0][1]):
        crd[1][0][1],crd[0][0][1] = crd[0][0][1],crd[1][0][1]
        crd[1][0][0],crd[0][0][0] = crd[0][0][0],crd[1][0][0]
    if(crd[3][0][1] < crd[2][0][1]):
        crd[3][0][1],crd[2][0][1] = crd[2][0][1],crd[3][0][1]
        crd[3][0][0],crd[2][0][0] = crd[2][0][0],crd[3][0][0]
    return crd

def get_perspective(rows,cols,scaling_ratio):
    pers = np.float32([[0,0],
                       [rows/scaling_ratio,0],
                       [0,cols/scaling_ratio],
                       [rows/scaling_ratio,cols/scaling_ratio]])
    return pers

def scaling(img):
    rows,cols,ch = img.shape

    cnts = get_contours(img,True)
    
    #if is24Checker is True: 
    #    cv.drawContours(mask, cnts, -1, 255, -1)
    #else:
    #    return img
    
    if len(cnts) < 2: 
        raise Exception("No black squares detected.")
        
    color_para = cv.arcLength(cnts[0], True)
    #largest area refers to color card
    #color card used, since the size of color card is known
    color_corners = cv.approxPolyDP(cnts[0], 0.04 * color_para, True)
    color_corners = rotate_coordinates(color_corners)
    
    l1 = color_corners[3][0][1] - color_corners[0][0][1]
    l2 = color_corners[3][0][0] - color_corners[0][0][0]
    scaling_ratio = get_scaling_ratio(l1,l2)
    
    original_pers = get_perspective(rows,cols,1.0)
    
    target_pers = get_perspective(rows,cols,scaling_ratio)

    geocal = cv.getPerspectiveTransform(original_pers,target_pers)
    dst = cv.warpPerspective(img,geocal,(int(cols/scaling_ratio),int(rows/scaling_ratio)),cv.INTER_LANCZOS4)
    return dst
    
if __name__ == "__main__":
    img = rawpy.imread('/Users/ryan/Desktop/CV-in-Archeology/test_images/1/photos/2.CR3')
    assert img is not None, "file could not be read, check with os.path.exists()"
    img = img.postprocess()
    # show the image in a window
    utils.showImage(color_correction(img))
