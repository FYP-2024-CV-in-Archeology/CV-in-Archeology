import numpy as np
import cv2 as cv
# define range of colors in HSV
lower_blue = np.array([120, 50, 20])
upper_blue = np.array([158, 255, 255])
lower_green = np.array([40, 52, 70])
upper_green = np.array([82, 255, 255])  # TOFIX
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])

lower_red = np.array([0, 100, 100])
upper_red = np.array([10, 255, 255])
lower_red2 = np.array([170, 100, 100])
upper_red2 = np.array([179, 255, 255])

lower_black = np.array([0, 0, 0])
upper_black = np.array([179, 255, 75])
lower_white = np.array([0, 0, 180])  # TOFIX
upper_white = np.array([0, 0, 255])  # TOFIX
# Create an array specify lower and upper range of colours
COLOR_RANGE = {'blue': [lower_blue, upper_blue],
                'green': [lower_green, upper_green],
                'yellow': [lower_yellow, upper_yellow],
                'red': [[lower_red, upper_red], [lower_red2, upper_red2]],
                'black': [lower_black, upper_black]}

def validCnt(cnt):
    (width, height)= cv.minAreaRect(cnt)[1]
    if width > 100 and height > 100 and cv.contourArea(cnt) > 500:
        return True

def showImage(img):
    # show RGB image
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    cv.imshow('image',img)
    cv.waitKey(0)
    cv.destroyAllWindows()

# Detect the black region to guess the positions of 24checker and scaling card in an image 
def getCardsBlackPos(img, is24Checker = True):
    patchPos = {}
    
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)  # Convert BGR to HSV
    black_mask = cv.inRange(
        img_hsv, COLOR_RANGE['black'][0], COLOR_RANGE['black'][1])
    
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))
    mask = cv.morphologyEx(black_mask.copy(), cv.MORPH_CLOSE, kernel)
    
    cnts, _ = cv.findContours(
        mask.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    
    # Fill the black color to get the card
    if is24Checker is True: 
        cv.drawContours(mask, cnts, -1, 255, -1)

    # Get rectangle only
    cnts = list(filter(lambda x: len(cv.approxPolyDP(
            x, 0.05*cv.arcLength(x, True), True)) == 4, cnts))

    cnts = sorted(cnts, reverse=True, key=cv.contourArea)
   

    if len(cnts) < 2: 
        raise Exception("No black squares detected.")
    if is24Checker is True: 
        _, _, w, h = cv.boundingRect(cnts[1])
        if w/h > 2 or h/w > 2: # Determine if is scale card
            patchPos['black'] = cv.boundingRect(cnts[1]) 
            patchPos['black2'] = cv.boundingRect(cnts[0])
        else: 
            patchPos['black'] = cv.boundingRect(cnts[0]) # Second largest is the scale card 
            patchPos['black2'] = cv.boundingRect(cnts[1])
    else: 
        patchPos['black'] = cv.boundingRect(cnts[1]) # The largest may be the blue patch
        
    return patchPos

# detect if 24-patch color card exists
def detect24Checker(img, detector, kernel_size=5):
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    closing = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)
    processParams = cv.mcc.DetectorParameters_create()
    processParams.maxError = 0.05
    if not detector.process(closing, cv.mcc.MCC24, 1, params=processParams):
        return False
    return True

def drawPatchPos(img, patchPos): 
    for color in patchPos:
        # rect_color = (0, 0, 255) if color == 'black' else (0, 255, 0)
        x, y, w, h = patchPos[color]
        cv.rectangle(img, (x,y), (x+w, y+h), (0, 255, 0), 50)
    showImage(img)