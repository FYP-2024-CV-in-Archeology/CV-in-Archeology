import os
import sys
sys.path.append('../')
from pathlib import Path
import cv2 as cv
import utils
import rawpy
import cropping
from scaling import scaling
import color_correction
import numpy as np

def run(input_path):
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames.sort()
        for file in filenames:
            path = Path(dirpath) / file
            
            dir, filename = path.parent.name, path.stem
            if dir > '478130_4419430_8_20':
                if 'cr' in path.suffix.lower() and (filename == '2' or filename == '1'):
                    print(path)
                    try:
                        img = utils.imread(path)
                        img_orig = img.copy()
                        bgr = cv.cvtColor(img, cv.COLOR_RGB2BGR)
                        bgr = color_correction.percentile_whitebalance(bgr, 97.5)

                        detector = cv.mcc.CCheckerDetector_create()
                        is24Checker = utils.detect24Checker(bgr.copy(), detector)  # must be bgr
                        # print(is24Checker)
                        #scaling part with no geocali
                        img_scal= scaling(img_orig, is24Checker)
                        # calculate the dpi of img_scal

                        colorCorrection, _ = color_correction.color_correction(img_scal)
                        # print(img_scal.shape)
                        # utils.showImage(colorCorrection)
                        if is24Checker:
                            sherdCnt = cropping.detectSherd(colorCorrection, is24Checker)
                        else:
                            sherdCnt = cropping.detectSherd(img_scal, is24Checker)
                        # draw contours
                        # img_cnt = img.copy()
                        # cv.drawContours(img_cnt, sherdCnt, -1, (0, 255, 0), 30)
                        # utils.showImage(img_cnt)
                        cropped = cropping.crop(colorCorrection, sherdCnt)
                        
                        # utils.showImage(cropped)
                    except Exception as e:
                        print(f'Cannot process image: {path}. Exception: {e}. Try no scaling.')
                        img_copy = img.copy()
                        colorCorrection_2, _ = color_correction.color_correction(img_copy)
                        sherdCnt = cropping.detectSherd(img_copy, is24Checker)
                        cropped = cropping.crop(colorCorrection_2, sherdCnt)

                    if not cropped.any():
                        print(f'No output for {path}')
                        img_copy2 = img.copy()
                        colorCorrection_3, _ = color_correction.color_correction(img_copy2)
                        sherdCnt = cropping.detectSherd(img_copy2, is24Checker)
                        cropped = cropping.crop(colorCorrection_3, sherdCnt)

                    # utils.showImage(cropped)
                    # convert to RGB and write into current folder
                    cropped = cv.cvtColor(cropped, cv.COLOR_BGR2RGB)
                    cv.imwrite(f'outputs/{path.parent.parent.name}_{filename}'.replace(' ', '') + '.jpg', cropped)
                    # exit the program
                    # exit(0)
if __name__ == "__main__":
    run("test_images")
