import numpy as np # linear algebra
# import pandas as pd # data processing
import rawpy
import cv2 as cv
import matplotlib.pyplot as plt
import math
import utils
import cropping
from color_correction import color_correction

#get_scaling_ratio for 24 color cards
def get_scaling_ratio(w,h,dpi):
    #directly get scaling ratio by comparing diagonal length
    r = dpi / 900.0
    d = math.sqrt(w**2 + h**2)
    #3245.0 pixels for color card outer diagonal, 
    #2950 pixels for inner diagonal, 2940 for detection inaccuracy
    scaling_ratio = d / (2940.0 * r)
    return scaling_ratio

#get_scaling_ratio for 4 color cards
def get_scaling_ratio4(w,h,dpi):
    #directly get scaling ratio by comparing diagonal length
    r = dpi / 900.0
    d = math.sqrt(w**2 + h**2)
    # 6cm for the distance between red & blue contour, around 2125.99 pixels
    # 2145 for detection inaccuracy
    scaling_ratio = d / (2145.0 * r)
    return scaling_ratio

#get target perspective of picture
def get_perspective(rows,cols,scaling_ratio):
    pers = np.float32([[0,0],
                       [rows/scaling_ratio,0],
                       [0,cols/scaling_ratio],
                       [rows/scaling_ratio,cols/scaling_ratio]])
    return pers

#calculate the scaling ratio
def calc_scaling_ratio(img, is24, dpi, patchPos):
    #rows,cols,ch = img.shape
    if(not is24):
        #4 color card
        #black, black1, green, red, blue 547-731 567-732 544-722 543-722
        #blackw = patchPos['black'][2]       
        #blackh = patchPos['black'][3]
        #blackl1 = max(blackw,blackh)
        #blackl2 = min(blackw,blackh)
        #black1w = patchPos['black1'][2]       
        #black1h = patchPos['black1'][3]
        #black1l1 = max(black1w,black1h)
        #black1l2 = min(black1w,black1h)
        #greenw = patchPos['green'][2]      
        #greenh = patchPos['green'][3]
        #greenl1 = max(greenw,greenh)
        #greenl2 = min(greenw,greenh)
        #bluew = patchPos['blue'][2]       
        #blueh = patchPos['blue'][3]
        #bluel1 = max(bluew,blueh)
        #bluel2 = min(bluew,blueh)
        #redw = patchPos['red'][2]      
        #redh = patchPos['red'][3]
        #redl1 = max(redw,redh)
        #redl2 = min(redw,redh)
        bluex = patchPos['blue'][0]
        bluey = patchPos['blue'][1]
        redx = patchPos['red'][0]
        redy = patchPos['red'][1]
        w = abs(bluex - redx)
        h = abs(bluey - redy)
        l1 = max(w,h)
        l2 = min(w,h)
        scaling_ratio = get_scaling_ratio4(l1,l2,dpi)
    else:
        #24 color card
        w = patchPos['color'][2]
        h = patchPos['color'][3]
        l1 = max(w,h)
        l2 = min(w,h)
        scaling_ratio = get_scaling_ratio(l1,l2,dpi)
    
    return scaling_ratio

#carry out scaling based on scaling ratio
#keep the scaling part after color correction & cropping
#to minimize the impact on other parts
def scaling(img, scaling_ratio):
    #input cropped picture
    #output a 1000 * 500 picture
    #cols,rows = image shape
    cols = 1000 * scaling_ratio
    rows = 500 * scaling_ratio
    original_pers = get_perspective(rows,cols,1.0)
    target_pers = get_perspective(rows,cols,scaling_ratio)
    
    geocal = cv.getPerspectiveTransform(original_pers,target_pers)
    dst = cv.warpPerspective(img,geocal,(int(cols/scaling_ratio),int(rows/scaling_ratio)),cv.INTER_LANCZOS4)
    return dst

#carry out scaling based on scaling ratio
#directly get the whole scaled picture (without cropping)
def scaling_before_cropping(img, scaling_ratio):
    #input original size picture
    #output resized full scale picture
    rows,cols,ch = img.shape
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
