import numpy as np
import cv2 as cv
import rawpy
# define range of colors in HSV
lower_blue = np.array([135, 65, 35])
upper_blue = np.array([165, 255, 255])
lower_green = np.array([40, 52, 70])
upper_green = np.array([82, 255, 255]) 
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])

lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

lower_black = np.array([0, 0, 0])
upper_black = np.array([179, 255, 75])
lower_white = np.array([0, 0, 180]) 
upper_white = np.array([0, 0, 255]) 

# Create an array specify lower and upper range of colours
COLOUR_RANGE = {
    'blue': (lower_blue, upper_blue),
    'green': (lower_green, upper_green),
    'yellow': (lower_yellow, upper_yellow),
    'red': (lower_red, upper_red),
    'black': (lower_black, upper_black),
    'white': (lower_white, upper_white)
}

COLOURS = ('blue', 'green', 'yellow', 'red', 'black', 'white')

kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))

TARGETS = {
    'blue': np.array([26,0,165]),
    'green': np.array([30,187,22]),
    'yellow': np.array([252,220,10]),
    'red': np.array([240,0,22]),
    'black': np.array([0,0,0]),
    'white': np.array([255,255,255])
}

TARGETS_NORM = {
    'blue': np.array([26,0,165]) / 255.0,
    'green': np.array([30,187,22]) / 255.0,
    'yellow': np.array([252,220,10]) / 255.0,
    'red': np.array([240,0,22]) / 255.0,
    'black': np.array([0,0,0]) / 255.0,
    'white': np.array([255,255,255]) / 255.0
}

# a function to perform thresholding on the image, use otsu for 4 color and adaptive for 24 color cards
def Thresholding(img, is24, block_size=31):
    # adaptive thresholding
    if is24:
        thresh = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, block_size, 3)
    else:
        _,thresh = cv.threshold(img,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)

    # morphological operations
    # resize image
    if max(img.shape) >= 1000:
        kernel_size = 6
    else:
        kernel_size = 5

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_size, kernel_size))
    thresh = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)
    filled = np.zeros_like(thresh)
    cnts, _ = cv.findContours(
    thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        if validCnt(cnt):
            cv.drawContours(filled, [cnt], 0, 255, -1)

    filled = cv.morphologyEx(filled, cv.MORPH_OPEN, kernel)
    return filled

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

def getColorPos(img, color):
    img = cv.cvtColor(img, cv.COLOR_RGB2HSV)
    mask = cv.inRange(img, COLOUR_RANGE[color][0], COLOUR_RANGE[color][1])
    mask_updated = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
    contours, _ = cv.findContours(mask_updated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    contours = list(filter(lambda x: len(cv.approxPolyDP(x, 0.02 * cv.arcLength(x, True), True)) == 4
                           and
                           cv.contourArea(x)/(cv.boundingRect(x)[2]*cv.boundingRect(x)[3]) > 0.9
                           , contours))
    contours = sorted(contours, key=cv.contourArea, reverse=True)
    if len(contours) > 0:
        bounding_rect = cv.boundingRect(contours[0])
        return bounding_rect
    else:
        return None
    

# Guess if a contour is a sherd for 4 color cards
def collision(cnt, pos):
    x1, y1, w1, h1 = cv.boundingRect(cnt)
    x2, y2, w2, h2 = pos
 
    # Check if one rectangle is to the left of the other
    if x1 + w1 <= x2 or x2 + w2 <= x1:
        return False
    
    # Check if one rectangle is above the other
    if y1 + h1 <= y2 or y2 + h2 <= y1:
        return False
    
    return True

# function to detect the position of the color card and the scale card in the 24 color image
def getCardsPos24(detector, img):
    shape = img.shape
    patchPos = {}
    # get the color card position stored in the detector
    CC = detector.getBestColorChecker().getBox()

    # get the top left and bottom right corner of the 24 color card, by the maximum and minimum x and y coordinates
    top_left = [min(CC[0][0], CC[2][0]), min(CC[0][1], CC[2][1])]
    bottom_right = [max(CC[0][0], CC[2][0]), max(CC[0][1], CC[2][1])]

    # get the color card position in bounding box format
    x, y = top_left
    w, h = bottom_right[0]-top_left[0], bottom_right[1]-top_left[1]
    patchPos['color'] = (int(x), int(y), int(w), int(h))
    
    # thresholding the image again with a smaller block size to highlight the scale card
    thresh = Thresholding(img, True, 15)
    cnts, _ = cv.findContours(
    thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # scale bar detection machenism:
    # 1. No collision with the color card
    # 2. The scale bar should be near the edge of the image
    # 3. The scale bar should be a rectangle
    # 4. The aspect ratio of the scale bar should be around 2.5

    if shape[0] > shape[1]:
        # vertical image
        _, Y = shape
        scaleCnt = max(list(filter(lambda x: 
                    (not collision(x, patchPos['color']))
                    and
                    ((cv.boundingRect(x)[0]) < Y/5
                    or
                    (cv.boundingRect(x)[0] + cv.boundingRect(x)[2]) > (Y * 4/5))
                    and 
                    len(cv.approxPolyDP(x, 0.01*cv.arcLength(x, True), True)) == 4
                    and 
                    cv.contourArea(x)/(cv.boundingRect(x)[2]*cv.boundingRect(x)[3]) > 0.9
                    and
                    cv.contourArea(x) > 100
                    , cnts)), key=cv.contourArea)
                    
    else:
        # horizontal image
        Y, _ = shape
        scaleCnt = max(list(filter(lambda x: 
                    (cv.boundingRect(x)[1] + cv.boundingRect(x)[3]) > Y *4/5
                    and
                    (not collision(x, patchPos['color']))
                    and
                    len(cv.approxPolyDP(x, 0.01*cv.arcLength(x, True), True)) == 4
                    and
                    cv.contourArea(x)/(cv.boundingRect(x)[2]*cv.boundingRect(x)[3]) > 0.9
                    and
                    cv.contourArea(x) > 100
                    , cnts)), key=cv.contourArea)
    patchPos['scale'] = cv.boundingRect(scaleCnt)
    return patchPos



# Detect the black region to guess the positions of the 4 color cards
def getCardsBlackPos(img, is24Checker = False):
    patchPos = {}
    # showImage(img)
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)  # Convert BGR to HSV
    
    black_mask = cv.inRange(
        img_hsv, COLOUR_RANGE['black'][0], COLOUR_RANGE['black'][1])
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))

    mask = cv.morphologyEx(black_mask.copy(), cv.MORPH_OPEN, kernel)
    
    cnts, _ = cv.findContours(
        mask.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    
    # Fill the black color to get the card
    cnts = list(filter(lambda x: 
                       len(cv.approxPolyDP(x, 0.02*cv.arcLength(x, True), True)) == 4
                       and 
                       cv.contourArea(x)/(cv.boundingRect(x)[2]*cv.boundingRect(x)[3]) > 0.90
                       , cnts))       
    cnts = sorted(cnts, reverse=True, key=cv.contourArea)
    if len(cnts) < 2: 
        patchPos['black'] = cv.boundingRect(cnts[0])
    else: 
        patchPos['black'] = cv.boundingRect(cnts[0])
        patchPos['black1'] = cv.boundingRect(cnts[1])
        
    return patchPos

def detect_rotation(img, sherdCnt, patchPos):
    sherd_bounding = cv.boundingRect(sherdCnt)
    x, y, _, _ = sherd_bounding
    if 'black' in patchPos:
        x_scale, y_scale, _, _ = patchPos['black']
    else:
        x_scale, y_scale, _, _ = patchPos['scale']

    rotate = 0
    if img.shape[0] < img.shape[1] and y < y_scale:
        return 0
    else:
        if x > x_scale:
            rotate = 1
        elif x < x_scale:
            rotate = -1
        elif y > y_scale:
            rotate = 180
    return rotate

def rotate_img(img, rotate):
    if rotate == 1:
        return cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
    elif rotate == -1:
        return cv.rotate(img, cv.ROTATE_90_CLOCKWISE)
    elif rotate == 180:
        return cv.rotate(img, cv.ROTATE_180)

    return img

# detect if 24-patch color card exists
def detect24Checker(img, detector, kernel_size=5):
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    closing = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
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

# Read a raw image
def imread(path, scaling_factor=1):
    if 'cr' in path.suffix.lower():
        img = rawpy.imread(str(path)).postprocess()  # access to the RAW image to a numpy RGB array
        # img = cv.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv.INTER_LINEAR)
    else:
        img = cv.imread(str(path))
    return img
 