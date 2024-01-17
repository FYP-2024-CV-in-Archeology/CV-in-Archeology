import numpy as np
import pandas as pd
import cv2 as cv
import matplotlib.pyplot as plt
import utils

img = cv.imread('/picture/2.jpg')

pos = utils.getCardsBlackPos(img)

### Detect color bar & scalr bar
is24Checker = True
lower_black = np.array([0, 0, 0])
upper_black = np.array([179, 255, 75])
COLOR_RANGE = {'black': [lower_black, upper_black]}
patchPos = {}

img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)  # Convert BGR to HSV
img_hsv = cv.blur(img_hsv, (10,10)) #Smoothens the sharp edges and cover highlights
black_mask = cv.inRange(
    img_hsv, COLOR_RANGE['black'][0], COLOR_RANGE['black'][1])

kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))
mask = cv.morphologyEx(black_mask.copy(), cv.MORPH_OPEN, kernel)

cnts, _ = cv.findContours(
    mask.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

# Fill the black color to get the card
if is24Checker is True: 
    cv.drawContours(mask, cnts, -1, 255, -1)

# Get Rectangles
cnts = list(filter(lambda x: len(cv.approxPolyDP(
        x, 0.05*cv.arcLength(x, True), True) == 4), cnts))

cnts = sorted(cnts, reverse=True, key=cv.contourArea)

if len(cnts) < 2: 
    raise Exception("No black squares detected.")
else:
    print(len(cnts))

# Put corners in right order for perspective transformation

color_para = cv.arcLength(cnts[0], True)
color_corners = cv.approxPolyDP(cnts[0], 0.04 * peri, True)
if(color_corners[1][0][1] < color_corners[0][0][1]):
    color_corners[1][0][1],color_corners[0][0][1] = color_corners[0][0][1],color_corners[1][0][1]
    color_corners[1][0][0],color_corners[0][0][0] = color_corners[0][0][0],color_corners[1][0][0]
if(color_corners[3][0][1] < color_corners[2][0][1]):
    color_corners[3][0][1],color_corners[2][0][1] = color_corners[2][0][1],color_corners[3][0][1]
    color_corners[3][0][0],color_corners[2][0][0] = color_corners[2][0][0],color_corners[3][0][0]
print(color_corners)

scale_para = cv.arcLength(cnts[0], True)
scale_corners = cv.approxPolyDP(cnts[1], 0.04 * peri, True)
if(scale_corners[1][0][1] < scale_corners[0][0][1]):
    scale_corners[1][0][1],scale_corners[0][0][1] = scale_corners[0][0][1],scale_corners[1][0][1]
    scale_corners[1][0][0],scale_corners[0][0][0] = scale_corners[0][0][0],scale_corners[1][0][0]
if(scale_corners[3][0][1] < scale_corners[2][0][1]):
    scale_corners[3][0][1],scale_corners[2][0][1] = scale_corners[2][0][1],scale_corners[3][0][1]
    scale_corners[3][0][0],scale_corners[2][0][0] = scale_corners[2][0][0],scale_corners[3][0][0]
print(scale_corners)

# Original & Target perspective
original_pers = np.float32([[color_corners[0][0][0],color_corners[0][0][1]],
                        [color_corners[2][0][0],color_corners[2][0][1]],
                        [color_corners[1][0][0],color_corners[1][0][1]],
                        [color_corners[3][0][0],color_corners[3][0][1]]])

target_pers = np.float32([[color_corners[0][0][0],color_corners[0][0][1]],
                        [color_corners[0][0][0]+1780.86,color_corners[0][0][1]],
                        [color_corners[0][0][0],color_corners[0][0][1]+2648.25],
                        [color_corners[0][0][0]+1780.86,color_corners[0][0][1]+2648.25]])

#scale bar is 5cm * 2 cm, 1 cm <-> 354.330 pixels under 900 dpi
#color bar is around 5.0260cm * 7.4740cm 1780.86*2648.25 pixels

rows,cols,ch = img.shape
geocal = cv.getPerspectiveTransform(original_pers,target_pers)
dst = cv.warpPerspective(img,geocal,(5000,3500))
plt.subplot(121),plt.imshow(img),plt.title('Input')
plt.subplot(122),plt.imshow(dst),plt.title('Output')
plt.show()

#output processed image
cv.imwrite('output.jpg', dst, [cv.IMWRITE_JPEG_QUALITY, 90])
