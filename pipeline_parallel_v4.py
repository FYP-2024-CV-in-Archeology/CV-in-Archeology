import os
import sys
import time

sys.path.append('../')

from pathlib import Path
import cv2 as cv

import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import pool


import utils
from cropping import detectSherd, crop
from scaling import scaling, calc_scaling_ratio
from color_correction import color_correction, percentile_whitebalance, imresize

# process to read images from file system
def imread(queue_in, queue_out):
    while True:
        path = queue_in.get()
        if path is None:
            queue_out.put(path)
            break

        queue_out.put([path, utils.imread(path)])

    print(f"imread finished {path}")
    print(f"imread Done!")

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
def whitebalance(queue_in, queue_out, num):
    print(f"Whitebalance Started!")

    while True:
        data = queue_in.get()
        if data is None:
            for _ in range(num):
                queue_out.put(data)
            break
        
        path, raw_img, is24, scalin_ratio = data

        white_balance_img = raw_img if is24 else percentile_whitebalance(raw_img, 97.5)            
        sherd_cnt, patch_pos = detectSherd(white_balance_img, is24)
        rotation = utils.detect_rotation(white_balance_img, sherd_cnt, patch_pos)
        queue_out.put([path, white_balance_img, is24, scalin_ratio, sherd_cnt, rotation])
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

        path, white_balance_img, is24, scalin_ratio, sherd_cnt, rotation = data
        detector = cv.mcc.CCheckerDetector_create()
        is24Checker = utils.detect24Checker(cv.cvtColor(white_balance_img, cv.COLOR_RGB2BGR), detector)
        color_correct_img = color_correction(white_balance_img, detector, is24Checker)
        queue_out.put([path, color_correct_img, is24, scalin_ratio, sherd_cnt, rotation])
        print(f"Color Corrected {path}")

    print(f"Color Correction Done!")

# do the last processing of images and write them to file system
def imwrite(queue_in, sizes, num):
    print(f"Whitebalance Started!")
    done = 0
    while done < num:
        data = queue_in.get()
        if data is None:
            done += 1
            continue
        
        path, color_correct_img, is24, scalin_ratio, sherd_cnt, rotation = data
        processed_img = color_correct_img if is24 else cv.add(percentile_whitebalance(color_correct_img, 97.5), (10,10,10,0))
        processed_img = cv.cvtColor(processed_img, cv.COLOR_BGR2RGB)

        for size in sizes:
            cv.imwrite(f'{path.parent}/{path.stem}' + f'-{size}.jpg', imresize(utils.rotate_img(processed_img, rotation), size))

        cropped_img = scaling(crop(processed_img, sherd_cnt, scalin_ratio), scalin_ratio)
        cv.imwrite(f"outputs/{path.parent.parent.name}_{path.stem}.jpg", cropped_img)

        print(f"Write finished {path}")
    print(f"imwrite Done!")

def read_path(input_path, num, manager):
    queue = manager.Queue()   
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
                    queue.put(path)
    for _ in range(num):
        queue.put(None)

    return queue

if __name__ == "__main__":
    start_time = time.time()
    sizes = {1000}

    with multiprocessing.Manager() as manager:
        num = 2
        pathes_queue = read_path('test', num, manager)

        # create pipes
        queues = [manager.Queue() for _ in range(4)]
        # with multiprocessing.Pool(6) as pool:
        imread_pool = pool.Pool(2)
        detect24_pool = pool.Pool(2)
        whitebalance_pool = pool.Pool(2)
        color_correct_pool = pool.Pool(4)
        imwrite_pool = pool.Pool(2)

        imread_pool.starmap_async(imread, [(pathes_queue, queues[0]) for _ in range(2)])
        detect24_pool.starmap_async(detect24, [(queues[0], queues[1]) for _ in range(2)])
        whitebalance_pool.starmap_async(whitebalance, [(queues[1], queues[2], num) for _ in range(2)])
        color_correct_pool.starmap_async(color_correct, [(queues[2], queues[3]) for _ in range(4)])
        imwrite_pool.starmap_async(imwrite, [(queues[3], sizes, num) for _ in range(2)])

        imread_pool.close()
        detect24_pool.close()
        whitebalance_pool.close()
        color_correct_pool.close()
        imwrite_pool.close()
        
        imread_pool.join()
        detect24_pool.join()
        whitebalance_pool.join()
        color_correct_pool.join()
        imwrite_pool.join()
        
    
    print("finished in {} seconds".format(time.time() - start_time))