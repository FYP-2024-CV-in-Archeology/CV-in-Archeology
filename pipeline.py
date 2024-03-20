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
import cProfile
import logging
from time import sleep
from threading import Thread
from queue import Queue



def write(path, img):
    # if path exists, prompt user to overwrite
    if os.path.exists(path):
        # write a messageBox to ask user if they want to overwrite
        # overwrite = tk.messagebox.askyesno("Overwrite", f"File {path} already exists. Do you want to overwrite it?")
        overwrite = True
        if overwrite:
            cv.imwrite(path, img)
    else:
        cv.imwrite(path, img)

def imread_thread(input_path, queue_out):
    logging.info(f"Started!")
    
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames.sort()
        for file in filenames:
            path = Path(dirpath) / file
            dir, filename = path.parent.name, path.stem
            
            if '.DS_Store' in filename or 'pxrf' in filename:
                continue
            filename = filename[0]

            if dir > '478130_4419430_8_20':
                if 'cr' in path.suffix.lower() and (filename == '2' or filename == '1'):
                    queue_out.put(utils.imread(path))
                    logging.info(f"Added {path}")
                    # sleep(999999.9999)

    logging.info(f"Done!")
    queue_out.put(None)

def detect24_thread(queue_in, queue_out):
    logging.info(f"Started!")
    while True:
        raw_img = queue_in.get()
        # logging.info(f"Got img")
        if raw_img is None:
            queue_out.put(raw_img)
            break

        detector = cv.mcc.CCheckerDetector_create()
        is24Checker = utils.detect24Checker(cv.cvtColor(raw_img.copy(), cv.COLOR_RGB2BGR), detector)  # must be bgr
        scalingRatio = calc_scaling_ratio(raw_img.copy(), is24Checker, 900)

        # out = [raw_img, is24Checker, scalingRatio, False]
        out = [raw_img, is24Checker, scalingRatio]
        queue_out.put(out) 
        logging.info(f"Added {[is24Checker, scalingRatio]}")

    logging.info(f"Done!")

def whitebalance_thread(queue_in, queue_out):
    logging.info(f"Started!")
    while True:
        input = queue_in.get()
        # raw_img, is24Checker, scalingRatio, flag = None, None, None, False
        raw_img, is24Checker, scalingRatio = None, None, None
        if input is None:
            queue_out.put(raw_img)
            break
        else:
            # raw_img, is24Checker, scalingRatio, flag = input
            raw_img, is24Checker, scalingRatio = input
        # logging.info(f"Got img")

        if not is24Checker:
            whiteBalancedImg = color_correction.percentile_whitebalance(raw_img, 97.5)
            # if flag:
            #     whiteBalancedImg = cv.add(whiteBalancedImg, (10,10,10,0))

        out = [whiteBalancedImg, is24Checker, scalingRatio]
        queue_out.put(out)
        logging.info(f"Added {[is24Checker, scalingRatio]}")

    logging.info(f"Done!")

def color_correction_thread(queue_in, queue_out):
    logging.info(f"Started!")
    while True:
        input = queue_in.get()
        whiteBalancedImg, is24Checker, scalingRatio = None, None, None
        if input is None:
            queue_out.put(whiteBalancedImg)
            break
        else:
            whiteBalancedImg, is24Checker, scalingRatio = input
        # logging.info(f"Got img")

        colorCorrection = color_correction.color_correction(whiteBalancedImg, detector, is24Checker)
        # out = [colorCorrection, is24Checker, scalingRatio, True]
        out = [colorCorrection, is24Checker, scalingRatio]
        queue_out.put(out)
        logging.info(f"Added {[is24Checker, scalingRatio]}")

    logging.info(f"Done!")

def whitebalance_thread2(queue_in, queue_out):
    logging.info(f"Started!")
    while True:
        input = queue_in.get()
        colorCorrection, is24Checker, scalingRatio = None, None, None
        # logging.info(f"Got img")
        if input is None:
            queue_out.put(colorCorrection)
            break
        else:
            colorCorrection, is24Checker, scalingRatio = input

        if not is24Checker:
            colorCorrection = color_correction.percentile_whitebalance(colorCorrection, 97.5)
            colorCorrection = cv.add(colorCorrection, (10,10,10,0))
        out = [colorCorrection, is24Checker, scalingRatio]
        queue_out.put(out)
        logging.info(f"Added {[is24Checker, scalingRatio]}")

    logging.info(f"Done!")
    
def cropping_thread(queue_in):
    logging.info(f"Started!")
    while True:
        input = queue_in.get()
        logging.info(f"Got img")
        if input is None:
            break

    logging.info(f"Done!")


        

def run(input_path, output_tif=False, log=None, done_btn=None, process_btn=None, skip_files_start=0, skip_files_end=0, sizes=None):
    print(sizes)
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames.sort()
        for file in filenames:
            path = Path(dirpath) / file
            dir, filename = path.parent.name, path.stem
            if '.DS_Store' in filename or 'pxrf' in filename:
                continue
            filename = filename[0]
            
            if dir > '478130_4419430_8_20':
                if 'cr' in path.suffix.lower() and (filename == '2' or filename == '1'):
                    filename = int(filename)

                    try:
                        # read img
                        print(path)
                        img = utils.imread(path)
                        img_orig = img.copy()

                        # if bones and stones
                        if (int(path.parent.parent.name) >= skip_files_start) and (int(path.parent.parent.name) <= skip_files_end):
                            if log:
                                log.insert(tk.END, f'Color Correcting {path}...\n')

                            colorCorrection, _ = color_correction.color_correction(img_orig)
                            colorCorrection = cv.cvtColor(colorCorrection, cv.COLOR_BGR2RGB)

                            if output_tif:
                                write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(colorCorrection, scalingRatio))
                            for size in sizes:
                                write(f'{path.parent}/{filename}' + f'-{size}.jpg', color_correction.imresize(colorCorrection, is24Checker, size))
                
                            continue
                        if log:
                            log.insert(tk.END, f'Processing {path}...\n')

                        detector = cv.mcc.CCheckerDetector_create()
                        is24Checker = utils.detect24Checker(cv.cvtColor(img, cv.COLOR_RGB2BGR), detector)  # must be bgr
                        # print(is24Checker)
                        #scaling part with no geocali
                        scalingRatio = calc_scaling_ratio(img_orig, is24Checker, 900)
                        
                        # calculate the dpi of img_scal
                        if not is24Checker:
                            img_orig = color_correction.percentile_whitebalance(img_orig, 97.5)
                        colorCorrection = color_correction.color_correction(img_orig, detector, is24Checker) # detector and 24checker reused

                        if not is24Checker:
                            colorCorrection = color_correction.percentile_whitebalance(colorCorrection, 97.5)
                            colorCorrection = cv.add(colorCorrection, (10,10,10,0))

                        ########## img_scaled = scaling_before_cropping(colorCorrection, scalingRatio)
                        
                        sherdCnt = cropping.detectSherd(img_orig, is24Checker)

                        rotate = 0
                        sherd_bounding = cv.boundingRect(sherdCnt)
                        x, y, w, h = sherd_bounding
                        x_scale, y_scale, w_scale, h_scale = utils.getCardsBlackPos(img_orig)['black'] # !!!! can be optimized

                        if img_orig.shape[0] < img_orig.shape[1] and y < y_scale:
                            rotate = 0
                        else:
                            if x > x_scale:
                                rotate = 1
                            elif x < x_scale:
                                rotate = -1
                            elif y > y_scale:
                                rotate = 180

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
                        if log:
                            log.insert(tk.END, f'Cannot process image: {path}. Exception: {e}. Try no scaling.\n')
                        img_copy = img.copy()
                        colorCorrection_2, _ = color_correction.color_correction(img_copy)
                        sherdCnt = cropping.detectSherd(img_copy, is24Checker)
                        cropped = cropping.crop(colorCorrection_2, sherdCnt)

                    if not cropped.any():
                        print(f'No output for {path}')
                        if log:
                            log.insert(tk.END, f'No crop for {path}!\n')
                    else:
                        # utils.showImage(cropped)
                        # convert to RGB and write into current folder
                        cropped = cv.cvtColor(cropped, cv.COLOR_BGR2RGB)
                        colorCorrection = cv.cvtColor(colorCorrection, cv.COLOR_BGR2RGB)
                       
                        if rotate != 0:
                            if rotate == 1:
                                colorCorrection = cv.rotate(colorCorrection, cv.ROTATE_90_COUNTERCLOCKWISE)
                            elif rotate == -1:
                                colorCorrection = cv.rotate(colorCorrection, cv.ROTATE_90_CLOCKWISE)
                            elif rotate == 180:
                                colorCorrection = cv.rotate(colorCorrection, cv.ROTATE_180)
                    if output_tif:
                            write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(colorCorrection, scalingRatio))
                    for size in sizes:
                        write(f'{path.parent}/{filename}' + f'-{size}.jpg', color_correction.imresize(colorCorrection, is24Checker, size))
                    write(f'{path.parent}/{filename + 2}' + '.tif', cropped)
                    write(f'{path.parent}/{filename + 2}' + '.jpg', cropped)

                    if log:
                        log.insert(tk.END, f'Done!\n')

    if (done_btn and process_btn):
        done_btn.config(state=tk.NORMAL)
        process_btn.config(state=tk.NORMAL)
if __name__ == "__main__":
    # cProfile.run("run(r'e:\\Users\\yytu\\Desktop\\Test', sizes={1000})")
    # configure the log handler
    detector = cv.mcc.CCheckerDetector_create()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('[%(levelname)s] [%(threadName)s] %(message)s'))
    # add the log handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


    # create queue between first two tasks
    queue1_2 = Queue()
    # create thread for first task
    thread1 = Thread(target=imread_thread, args=("/Users/allenz/Desktop/CV-in-Archeology/test", queue1_2), name='Task1')
    thread1.start()
    # create queue between second and third tasks
    queue2_3 = Queue()
    # create thread for second task
    thread2 = Thread(target=detect24_thread, args=(queue1_2,queue2_3), name='Task2')
    thread2.start()

    queue3_4 = Queue()
    thread3_whitebalance1 = Thread(target=whitebalance_thread, args=(queue2_3,queue3_4), name='Task3')
    thread3_whitebalance1.start()

    queue4_5 = Queue()
    thread4_color_correction = Thread(target=color_correction_thread, args=(queue3_4,queue4_5), name='Task4')
    thread4_color_correction.start()

    queue5_6 = Queue()
    thread5_whitebalance2 = Thread(target=whitebalance_thread2, args=(queue4_5,queue5_6), name='Task5')
    thread5_whitebalance2.start()

    thread6_cropping = Thread(target=cropping_thread, args=(queue5_6,), name='Task6')
    thread6_cropping.start()

    # wait for all threads to finish
    thread1.join()
    thread2.join()
    thread3_whitebalance1.join()
    thread4_color_correction.join()
    thread5_whitebalance2.join()
    thread6_cropping.join()

