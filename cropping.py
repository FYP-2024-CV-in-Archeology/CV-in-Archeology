## Mathmatics libraries
import numpy as np

## Image Processing libraries
import cv2 as cv
import rawpy

## Utilities libraries
import utils

# Guess if a contour is a sherd for 4 color cards
def isSherd4(cnt, patchPos):
    x, y, w, h = cv.boundingRect(cnt)

    for pos in patchPos.values():
        if pos == None:
            continue
        # Axis-Aligned Bounding Box
        # Test if two bound box not intersect
        if not ((x + w) < pos[0] or x > (pos[0] + pos[2]) or y > (pos[1] + pos[3]) or (y + h) < pos[1]):
            return False
    return True

# Guess if a contour is a sherd for 24 color cards
def isSherd24(cnt, patchPos):
    color = patchPos['color']
    # eliminate the contour if it's on top of the color patch
    x, y, w, h = cv.boundingRect(cnt)
    
    if color[3] > color[2]:
        if (x + w/2) > color[0] and (x + w/2) < (color[0] + color[2]):
            return False
    else:
        if (y + h/2) > color[1] and (y + h/2) < (color[1] + color[3]):
            return False

    for pos in patchPos.values():
        if not ((x + w) < pos[0] or x > (pos[0] + pos[2]) or y > (pos[1] + pos[3]) or (y + h) < pos[1]):
            return False
    return True

# get the sherd contour out of all coutours found in the binary image
def getSherdCnt4(img, cnts):
    blackPos = utils.getCardsBlackPos(img.copy())
    # for 4 color card, we need to detect each color separately
    colorPos = blackPos
    colorPos['green'] = utils.getColorPos(img.copy(), 'green')
    colorPos['red'] = utils.getColorPos(img.copy(), 'red')
    # colorPos['yellow'] = utils.getColorPos(img.copy(), 'yellow')
    colorPos['blue'] = utils.getColorPos(img.copy(), 'blue')
    # print(colorPos)
    cnts = list(filter(lambda cnt: isSherd4(cnt, colorPos), cnts))
    # checking if max() arg is empty also filter out the unqualified images (e.g. ones with no colorChecker)
    return max(cnts, key=cv.contourArea), blackPos

# get the sherd contour out of all coutours found in the binary image
def getSherdCnt24(img, cnts, detector):
    cardPos = utils.getCardsPos24(detector, img)
    # for 24 color card, we can get the two patches' bounding box directly as all the two cards are enclosed by black
    cnts = list(filter(lambda cnt: isSherd24(cnt, cardPos), cnts))
    # checking if max() arg is empty also filter out the unqualified images (e.g. ones with no colorChecker)
    return max(cnts, key=cv.contourArea), cardPos

# get centroid of a contour using moment
def getCentroid(cnt):
    M = cv.moments(cnt)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    return [cx, cy]

# rotate the image based on the direction of the minimum area rectangle enclosing the sherd
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
    # rotate moment
    moment_transformed = np.intp(cv.transform(np.array([moment]), M))[0]
    pts[pts < 0] = 0
    w = pts[2][0] - pts[1][0]
    h = pts[0][1] - pts[1][1]

    return img_rot, moment_transformed, h > w

# crop the rotated image from the moment
def crop_from_moment(img, moment, w, h, vertical):
    x, y = moment[0]
    if not vertical:
        cropped = img[(y - h//2) : (y + h//2), (x - w//2) : (x + w//2)]
    else:
        cropped = img[(y - w//2) : (y + w//2), (x - h//2) : (x + h//2)]
    return cropped

# detect the sherd contour in the input image
def detectSherd(img, detector, is24=True):

    blur = cv.GaussianBlur(img,(5,5),0)
    img_g = cv.cvtColor(blur, cv.COLOR_BGR2GRAY)
    # thresholding
    thresh = utils.Thresholding(img_g, is24, 101)

    # find contours
    cnts, _ = cv.findContours(
    thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # utils.showImage(img)
    # get the sherd contour
    if is24:
        sherdCnt, patchPos = getSherdCnt24(img_g, cnts, detector)
    else:
        sherdCnt, patchPos = getSherdCnt4(img, cnts)

    return sherdCnt, patchPos

# cropped the sherd from the corrected image
def crop(img, sherdCnt, scalingRatio=1):
    # crop the minAreaRect
    img_crop, moment, vertical = cropMinAreaRect(img, sherdCnt)
    crop = crop_from_moment(img_crop, moment, round(1000 * scalingRatio), round(500 * scalingRatio), vertical)

    # rotate img_crop by 90 degree clockwise if it's vertical
    if crop.shape[0] > crop.shape[1]:
        crop = np.rot90(crop, 3)

    return crop

if __name__ == "__main__":
    img = rawpy.imread(r'e:\Users\yytu\Desktop\test1\4419550\93\4\photos\1.CR3')
    assert img is not None, "file could not be read, check with os.path.exists()"
    img = img.postprocess()
    utils.showImage(img)
    # show the image in a window
    sherdCnt = detectSherd(img, True)
    utils.showImage(crop(img, sherdCnt))