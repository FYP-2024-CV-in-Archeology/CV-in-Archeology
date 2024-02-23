import os
import sys
sys.path.append('../')
from pathlib import Path
import cv2 as cv
import utils
import rawpy
import cropping
from scaling import scaling, calc_scaling_ratio, scaling_before_cropping
import color_correction
import numpy as np
import tkinter as tk

def write(path, img):
    # if path exists, prompt user to overwrite
    if os.path.exists(path):
        # write a messageBox to ask user if they want to overwrite
        overwrite = tk.messagebox.askyesno("Overwrite", f"File {path} already exists. Do you want to overwrite it?")
        if overwrite:
            cv.imwrite(path, img)
    else:
        cv.imwrite(path, img)

def run(input_path, output_tif=False, log=None, done_btn=None, process_btn=None, skip_files_start=0, skip_files_end=0, sizes=None):
    print(sizes)
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames.sort()
        for file in filenames:
            path = Path(dirpath) / file
            
            dir, filename = path.parent.name, path.stem

            if '.DS_Store' in filename:
                continue

            if 'pxrf' in filename:
                continue

            filename = int(filename[0])
            
            if dir > '478130_4419430_8_20':
                if 'cr' in path.suffix.lower() and (filename == 2 or filename == 1):
                    try:
                        # read img
                        print(path)
                        img = utils.imread(path)
                        img_orig = img.copy()

                        # if bones and stones
                        if (int(path.parent.parent.name) >= skip_files_start.get()) and (int(path.parent.parent.name) <= skip_files_end.get()):
                            log.insert(tk.END, f'Color Correcting {path}...\n')

                            colorCorrection, _ = color_correction.color_correction(img_orig)
                            colorCorrection = cv.cvtColor(colorCorrection, cv.COLOR_BGR2RGB)

                            if output_tif:
                                write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(colorCorrection, scalingRatio))
                            for size in sizes:
                                write(f'{path.parent}/{filename}' + f'-{size}.jpg', color_correction.imresize(colorCorrection, is24Checker, size))
                
                            continue
                        
                        log.insert(tk.END, f'Processing {path}...\n')
                        bgr = cv.cvtColor(img, cv.COLOR_RGB2BGR)
                        bgr = color_correction.percentile_whitebalance(bgr, 97.5)

                        detector = cv.mcc.CCheckerDetector_create()
                        is24Checker = utils.detect24Checker(bgr.copy(), detector)  # must be bgr
                        # print(is24Checker)
                        #scaling part with no geocali
                        scalingRatio = calc_scaling_ratio(img_orig, is24Checker, 900)
                        
                        # calculate the dpi of img_scal

                        colorCorrection, _ = color_correction.color_correction(img_orig)
                        # print(img_scal.shape)
                        # utils.showImage(colorCorrection)
                        # print(is24Checker)

                        ########## img_scaled = scaling_before_cropping(colorCorrection, scalingRatio)
                        
                        sherdCnt = cropping.detectSherd(img_orig, is24Checker)
                        # draw contours
                        # img_cnt = img.copy()
                        # cv.drawContours(img_cnt, sherdCnt, -1, (0, 255, 0), 30)
                        # utils.showImage(img_cnt)
                        cropped = cropping.crop(colorCorrection, sherdCnt, scalingRatio)
                        cropped = scaling(cropped, scalingRatio)
                        # print(cropped.shape)
                        # utils.showImage(cropped)
                    except Exception as e:
                        print(f'Cannot process image: {path}. Exception: {e}. Try no scaling.')
                        log.insert(tk.END, f'Cannot process image: {path}. Exception: {e}. Try no scaling.\n')
                        img_copy = img.copy()
                        colorCorrection_2, _ = color_correction.color_correction(img_copy)
                        sherdCnt = cropping.detectSherd(img_copy, is24Checker)
                        cropped = cropping.crop(colorCorrection_2, sherdCnt)

                    if not cropped.any():
                        print(f'No output for {path}')
                        log.insert(tk.END, f'No crop for {path}!\n')
                    else:
                        # utils.showImage(cropped)
                        # convert to RGB and write into current folder
                        cropped = cv.cvtColor(cropped, cv.COLOR_BGR2RGB)
                        colorCorrection = cv.cvtColor(colorCorrection, cv.COLOR_BGR2RGB)
                        # cv.imwrite(f'outputs/{path.parent.parent.name}_{filename}'.replace(' ', '') + '.jpg', cropped)
                        # print(f'{path.parent}/{filename}')
                        if output_tif:
                            write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(colorCorrection, scalingRatio))
                        for size in sizes:
                            write(f'{path.parent}/{filename}' + f'-{size}.jpg', color_correction.imresize(colorCorrection, is24Checker, size))
                        write(f'{path.parent}/{filename + 2}' + '.tif', cropped)
                        write(f'{path.parent}/{filename + 2}' + '.jpg', cropped)
                        log.insert(tk.END, f'Done!\n')
    done_btn.config(state=tk.NORMAL)
    process_btn.config(state=tk.NORMAL)
if __name__ == "__main__":
    run("test_images")
