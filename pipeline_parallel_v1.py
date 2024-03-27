import os
import sys
import time
import cProfile

sys.path.append('../')

import numpy as np
import tkinter as tk
from pathlib import Path
import cv2 as cv
import rawpy

import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Pipe

import utils
from cropping import detectSherd, crop
from scaling import scaling, calc_scaling_ratio
from color_correction import color_correction, percentile_whitebalance

# process to read images from file system
def imread(input_path, queue_out):
    print(f"imread Started!")
    
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
                    queue_out.put([path, utils.imread(path)])
                    print(f"imread finished {path}")
                    # sleep(999999.9999)

    print(f"imread Done!")
    queue_out.put(None)
    queue_out.put(None)

# process to detect 24 or 4 color checker
def detect24(queue_in, queue_out):
    print(f"detect24 Started!")

    while True:
        data = queue_in.get()
        if data is None:
            queue_out.put(data)
            break
        
        path, raw_img = data
        
        detector = cv.mcc.CCheckerDetector_create()
        is24Checker = utils.detect24Checker(cv.cvtColor(raw_img, cv.COLOR_RGB2BGR), detector)  # must be bgr
        scaling_ratio = calc_scaling_ratio(raw_img, is24Checker, 900)

        queue_out.put([path, raw_img, is24Checker, scaling_ratio]) 
        print(f"detect24 finished {path}")
    print(f"detect24 Done!")

# process to whitebalance images and also detect sherd contour
def whitebalance(queue_in, queue_out):
    print(f"Whitebalance Started!")

    while True:
        data = queue_in.get()
        if data is None:
            queue_out.put(data)
            break
        
        path, raw_img, is24, scalin_ratio = data

        white_balance_img = raw_img if is24 else percentile_whitebalance(raw_img, 97.5)            
        sherd_cnt = detectSherd(white_balance_img, is24)
        queue_out.put([path, white_balance_img, is24, scalin_ratio, sherd_cnt])
        print(f"Whitebalance finished {path}")

    print(f"Whitebalance Done!")

# process to color correct images
def color_correct(queue_in, queue_out):
    print(f"Color Correction Started!")

    while True:
        data = queue_in.get()
        if data is None:
            queue_out.put(data)
            break

        path, white_balance_img, is24, scalin_ratio, sherd_cnt = data
        print(f"Color Correcting {path}")
        detector = cv.mcc.CCheckerDetector_create()
        is24Checker = utils.detect24Checker(cv.cvtColor(white_balance_img, cv.COLOR_RGB2BGR), detector)
        color_correct_img = color_correction(white_balance_img, detector, is24Checker)
        
        queue_out.put([path, color_correct_img, is24, scalin_ratio, sherd_cnt])
        print(f"Color Corrected {path}")

    print(f"Color Correction Done!")

# process to whitebalance images and also detect sherd contour
def whitebalance2(queue_in, queue_out):
    print(f"Whitebalance Started!")

    while True:
        data = queue_in.get()
        if data is None:
            queue_out.put(data)
            break
        
        path, color_correct_img, is24, scalin_ratio, sherd_cnt = data

        white_balance_img = color_correct_img if is24 else cv.add(percentile_whitebalance(color_correct_img, 97.5), (10,10,10,0))
        queue_out.put([path, white_balance_img, is24, scalin_ratio, sherd_cnt])
        print(f"Whitebalance2 finished {path}")

    print(f"Whitebalance2 Done!")


# process to crop and write images
def imwrite(queue_in, sizes):
    print(f"Write Started!")

    while True:
        data = queue_in.get()
        if data is None:
            break

        path, color_correct_img, _, scalin_ratio, sherd_cnt = data

        cropped_img_bgr = scaling(crop(color_correct_img, sherd_cnt, scalin_ratio), scalin_ratio)
        cropped_img = cv.cvtColor(cropped_img_bgr, cv.COLOR_BGR2RGB)
        cv.imwrite(f"outputs/{path.parent.parent.name}_{path.stem}.jpg", cropped_img)

        print(f"Write finished {path}")
        
    print(f"Write Done!")

if __name__ == "__main__":
    start_time = time.time()
    # create pipes
    queues = [Queue(maxsize=3) for _ in range(5)]
    lock = multiprocessing.Lock()
    # create processes
    processes = [
        Process(target=imread, args=('test', queues[0])),
        Process(target=detect24, args=(queues[0], queues[1])),
        Process(target=whitebalance, args=(queues[1], queues[2])),
        Process(target=color_correct, args=(queues[2], queues[3])),
        Process(target=whitebalance2, args=(queues[3], queues[4])),
        Process(target=imwrite, args=(queues[4], {1000},))
    ]
   
    for process in processes:
        process.start()

    # see if a process is done
    for process in processes:
        process.join()

    print("finished in {} seconds".format(time.time() - start_time))

   
