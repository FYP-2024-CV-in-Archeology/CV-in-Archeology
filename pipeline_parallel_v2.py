import os
import sys
import traceback
import cProfile

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

def read_path(input_path, start=0, end=0):
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
                if 'cr' in path.suffix.lower():
                    if start == 0 and end == 0:
                        paths.append(path)
                    elif (int(path.parent.parent.name) >= int(start)) and (int(path.parent.parent.name) <= int(end)):
                        paths.append(path)

    return paths

def write(path, img, overwrite):
    # return
    # if path exists, prompt user to overwrite
    jpg_quality = 100
    if overwrite or not os.path.exists(path):
        cv.imwrite(path, img, [int(cv.IMWRITE_JPEG_QUALITY), jpg_quality])
        queue.put(f"Wrote {path}")
    else:
        queue.put(f"Did not overwrite {path}")

def run_color_correct_only(path, dpi=1200, sizes={1000}, overwrite=False, output_tif=False):
    print("Color Correcting", path)
    queue.put(f"Color Correcting {path}...")
    try:
        # read image
        raw_data = utils.imread(path)
        raw_img = raw_data.postprocess()

        # detect if 24 or 4 color checker
        detector = cv.mcc.CCheckerDetector_create()
        is24 = utils.detect24Checker(cv.cvtColor(raw_img, cv.COLOR_RGB2BGR), detector)  # must be bgr
        if is24:
            raw_img =  raw_data.postprocess(use_camera_wb=True)

        # initial white balance
        # white_balance_img = raw_img if is24 else percentile_whitebalance(raw_img, 97.5)        

        # color correction
        color_correct_img = color_correction(raw_img, detector, is24)

        # final processing
        processed_img = color_correct_img if is24 else cv.add(percentile_whitebalance(color_correct_img, 97.5), (15,15,10,0))

        # convert to RGB
        processed_img = cv.cvtColor(processed_img, cv.COLOR_BGR2RGB)

        # write scaled images to file system
        filename = int(path.stem)

        # rotate image 90 degrees counter-clockwise if vertical
        if processed_img.shape[0] > processed_img.shape[1]:
            processed_img = cv.rotate(processed_img, cv.ROTATE_90_COUNTERCLOCKWISE)

        write(f'{path.parent}/{filename}' + '-original.jpg', processed_img, overwrite)

        for size in sizes:
            if size == 450:
                write(f'{path.parent}/{filename}' + '.jpg', imresize(processed_img, size), overwrite)
            else:
                write(f'{path.parent}/{filename}' + f'-{size}.jpg', imresize(processed_img, size), overwrite)

        queue.put(f"Finished {path}")
        print("Finished", path)
    except Exception as e:
        queue.put(f"Cannot process {path}! Error: {e}")
        print(traceback.format_exc())
             
def run(path, dpi=1200, sizes={1000}, overwrite=False, output_tif=False):
    print("Processing", path)
    queue.put(f"Processing {path}...")
    try:
        # read image
        raw_data = utils.imread(path)
        raw_img = raw_data.postprocess()

        # detect if 24 or 4 color checker
        detector = cv.mcc.CCheckerDetector_create()
        is24 = utils.detect24Checker(cv.cvtColor(raw_img, cv.COLOR_RGB2BGR), detector)  # must be bgr
        if is24:
            raw_img =  raw_data.postprocess(use_camera_wb=True)

        # detect sherd on original image
        sherd_cnt, patch_pos = detectSherd(raw_img, detector, is24)

        # calculate the scaling ratio
        scaling_ratio = calc_scaling_ratio(raw_img, is24, dpi, patch_pos)
            
        # initial white balance
        # white_balance_img = raw_img if is24 else percentile_whitebalance(raw_img, 97.5)        

        # detect rotation
        rotation = utils.detect_rotation(raw_img, sherd_cnt, patch_pos)

        # color correction
        color_correct_img = color_correction(raw_img, detector, is24)

        # final processing
        processed_img = color_correct_img if is24 else cv.add(percentile_whitebalance(color_correct_img, 97.5), (15,15,10,0))

        # convert to RGB
        processed_img = cv.cvtColor(processed_img, cv.COLOR_BGR2RGB)

        # write scaled images to file system
        filename = int(path.stem)
        
        for size in sizes:
            if size == 450:
                write(f'{path.parent}/{filename}' + '.jpg', imresize(utils.rotate_img(processed_img, rotation, is24), size), overwrite)
                # cv.imwrite(f"E:/Users/lxzhu/Desktop/tests/24/{path.parent.parent.name}_{path.stem}.jpg", imresize(utils.rotate_img(processed_img, rotation, is24), size))
            else:
                write(f'{path.parent}/{filename}' + f'-{size}.jpg', imresize(utils.rotate_img(processed_img, rotation, is24), size), overwrite)
                # jpg_quality = 100
                # cv.imwrite(f"E:/Users/lxzhu/Desktop/tests/24/{path.parent.parent.name}_{path.stem}" + f"-{size}.jpg",utils.rotate_img(processed_img, rotation, is24), [int(cv.IMWRITE_JPEG_QUALITY), jpg_quality])

        # write scaled and color corrected tif to file system
        if output_tif:
            write(f'{path.parent}/{filename}' + '.tif', scaling_before_cropping(utils.rotate_img(processed_img, rotation, is24), scaling_ratio), overwrite)
            # cv.imwrite(f"E:/Users/lxzhu/Desktop/tests/24/{path.parent.parent.name}_{path.stem}.tif", scaling_before_cropping(utils.rotate_img(processed_img, rotation, is24), scaling_ratio))
                        
        # write cropped image to file system
        cropped_img = scaling(crop(processed_img, sherd_cnt, scaling_ratio), scaling_ratio)
        write(f'{path.parent}/{filename}' + '-fabric.tif', cropped_img, overwrite)
        write(f'{path.parent}/{filename}' + '-fabric.jpg', cropped_img, overwrite)
        # cv.imwrite(f"E:/Users/lxzhu/Desktop/tests/24/{path.parent.parent.name}_{path.stem}.jpg", cropped_img)

        queue.put(f"Finished {path}")
        print("Finished", path)
    except Exception as e:
        queue.put(f"Cannot process {path}! Error: {e}")
        print(traceback.format_exc())

