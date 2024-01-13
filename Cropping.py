## Mathmatics libraries
import numpy as np
import math

## Image Processing libraries
import skimage
from skimage import exposure

import scipy.misc as misc
import cv2 as cv
import rawpy
import imageio

## Visual and plotting libraries
import matplotlib.pyplot as plt

import utils



def Thresholding(img):
    # adaptive thresholding
    thresh = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 31, 3)
    
    # morphological operations
    kernel_size = 6 if max(img.shape) >= 1000 else 5
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_size, kernel_size))
    thresh = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)
    filled = np.zeros_like(thresh)
    cnts, _ = cv.findContours(
    thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        if utils.validCnt(cnt):
            cv.drawContours(filled, [cnt], 0, 255, -1)

    filled = cv.morphologyEx(filled, cv.MORPH_OPEN, kernel)

    return filled

# Guess if a contour is a sherd
def isSherd(cnt, patchPos):
    x, y, w, h = cv.boundingRect(cnt)
    for pos in patchPos.values():
        # Axis-Aligned Bounding Box
        # Test if two bound box not intersect
        if not ((x + w) < pos[0] or x > (pos[0] + pos[2]) or y > (pos[1] + pos[3]) or (y + h) < pos[1]):
            return False
    return True

def getSherdCnt(img, cnts, is24Checker):
    patchPos = utils.getCardsBlackPos(img.copy(), is24Checker)
    cnts = list(filter(lambda cnt: isSherd(cnt, patchPos), cnts))
    # checking if max() arg is empty also filter out the unqualified images (e.g. ones with no colorChecker)
    return max(cnts, key=cv.contourArea)

def getCentroid(cnt):
    M = cv.moments(cnt)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    return [cx, cy]

def cropMinAreaRect(img, cnt):
    rect = cv.minAreaRect(cnt)
    moment = getCentroid(cnt)

    # rotate img
    angle = rect[2] 
    rows,cols = img.shape[0], img.shape[1]
    M = cv.getRotationMatrix2D((rect[0][0],rect[0][1]),angle,1)
    img_rot = cv.warpAffine(img,M,(cols,rows))
    # rotate bounding box
    box = cv.boxPoints(rect)
    moment = [moment]
    pts = np.intp(cv.transform(np.array([box]), M))[0]
    moment_transformed = np.intp(cv.transform(np.array([moment]), M))[0]
    pts[pts < 0] = 0
    img_crop = img_rot[pts[1][1]:pts[0][1], 
                       pts[1][0]:pts[2][0]]
    
    moment_transformed = [moment_transformed[0][0] - pts[1][0], moment_transformed[0][1] - pts[1][1]]
    return img_crop, moment_transformed

def crop_from_moment(img, moment, w, h):
    x, y = moment
    if img.shape[0] < img.shape[1]:
        cropped = img[(y - h//2) : (y + h//2), (x - w//2) : (x + w//2)]
    else:
        cropped = img[(y - w//2) : (y + w//2), (x - h//2) : (x + h//2)]
    return cropped


def Crop(img):
    blur = cv.GaussianBlur(img,(5,5),0)
    img_g = cv.cvtColor(blur, cv.COLOR_BGR2GRAY)
    # thresholding
    thresh = Thresholding(img_g)

    # find contours
    cnts, _ = cv.findContours(
    thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # get the sherd contour
    sherdCnt = getSherdCnt(img, cnts, utils.detect24Checker(img, cv.mcc.CCheckerDetector_create()))
    img_cnt = img.copy()
    cv.drawContours(img_cnt, sherdCnt, -1, (0, 255, 0), 30)

    # crop the minAreaRect
    img_crop, moment = cropMinAreaRect(img, sherdCnt)
    crop = crop_from_moment(img_crop, moment, 1000, 500)

    # rotate img_crop by 90 degree clockwise if it's vertical
    if crop.shape[0] > crop.shape[1]:
        crop = np.rot90(crop, 3)

    utils.showImage(crop)

if __name__ == "__main__":
    img = rawpy.imread('3.CR2')
    assert img is not None, "file could not be read, check with os.path.exists()"
    img = img.postprocess()
    # show the image in a window
    Crop(img)

