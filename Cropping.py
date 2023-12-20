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

img = rawpy.imread('test_images/2.CR2')
assert img is not None, "file could not be read, check with os.path.exists()"
img = img.postprocess()

# show the image in a window
cv.imshow('image', img)
cv.waitKey(0)
cv.destroyAllWindows()

