import os
import sys
import traceback

sys.path.append('../')

from pathlib import Path
import cv2 as cv

import utils
from cropping import detectSherd, crop
from scaling import scaling, calc_scaling_ratio, scaling_before_cropping
from color_correction import color_correction, percentile_whitebalance, imresize

def init_worker(q):
    global queue
    queue = q

def read_path(input_path, start, end):
    paths = []    
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
                    if start == 0 and end == 0:
                        paths.append(path)
                    elif (int(path.parent.parent.name) >= int(start)) and (int(path.parent.parent.name) <= int(end)):
                        paths.append(path)

    return paths

def write(path, img, overwrite):
    return
    # if path exists, prompt user to overwrite
    # if overwrite or not os.path.exists(path):
    #     cv.imwrite(path, img)
    #     queue.put(f"Overwrote {path}")
    # else:
    #     queue.put(f"Did not overwrite {path}")
 
             
def run(path, dpi, output_tif, sizes, overwrite):
    print("Processing", path)
    queue.put(f"Processing {path}...")
    try:
        # read image
        raw_img = utils.imread(path)

        # detect if 24 or 4 color checker
        detector = cv.mcc.CCheckerDetector_create()
        is24 = utils.detect24Checker(cv.cvtColor(raw_img, cv.COLOR_RGB2BGR), detector)  # must be bgr

        # calculate the scaling ratio

        # detect sherd on original image
        sherd_cnt, patch_pos = detectSherd(raw_img, detector, is24)

        scaling_ratio = calc_scaling_ratio(raw_img, is24, dpi, patch_pos)

        # initial white balance
        white_balance_img = raw_img if is24 else percentile_whitebalance(raw_img, 97.5)        

        # detect rotation
        rotation = utils.detect_rotation(white_balance_img, sherd_cnt, patch_pos)

        # color correction
        color_correct_img = color_correction(white_balance_img, detector, is24)

        # final processing
        processed_img = color_correct_img if is24 else cv.add(percentile_whitebalance(color_correct_img, 97.5), (10,10,10,0))
        processed_img = cv.cvtColor(processed_img, cv.COLOR_BGR2RGB)

        # write scaled images to file system
        filename = int(path.stem)
        
        for size in sizes:
            if size == 450:
                write(f'{path.parent}/{filename}' + '.jpg', imresize(utils.rotate_img(processed_img, rotation, is24), size), overwrite)
            else:
                write(f'{path.parent}/{filename}' + f'-{size}.jpg', imresize(utils.rotate_img(processed_img, rotation, is24), size), overwrite)
        if output_tif:
            write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(utils.rotate_img(processed_img, rotation, is24), scaling_ratio), overwrite)
            cv.imwrite(f"test_out/{path.parent.parent.name}_{path.stem}.tif", scaling_before_cropping(utils.rotate_img(processed_img, rotation, is24), scaling_ratio))
                        
        # write cropped image to file system
        cropped_img = scaling(crop(processed_img, sherd_cnt, scaling_ratio), scaling_ratio)
        write(f'{path.parent}/{filename}' + '-fabric.tif', cropped_img, overwrite)
        write(f'{path.parent}/{filename}' + '-fabric.jpg', cropped_img, overwrite)
        cv.imwrite(f"test_out/{path.parent.parent.name}_{path.stem}.jpg", cropped_img)

        queue.put(f"Finished {path}")
        print("Finished", path)
    except Exception as e:
        queue.put(f"Cannot process {path}! Error: {e}")
        print(traceback.format_exc())

