import os
import sys
sys.path.append('../')
from pathlib import Path
import cv2 as cv
import utils
from cropping import Crop

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
                        cropped = Crop(img, False)
                    except Exception as e:
                        print(f'Cannot process image: {path}. Exception: {e}')
                        continue
                    if cropped.any():
                        # utils.showImage(cropped)
                        # convert to RGB and write into current folder
                        cropped = cv.cvtColor(cropped, cv.COLOR_BGR2RGB)
                        cv.imwrite(f'outputs/{path.parent.parent.name}_{filename}.jpg', cropped)
                        # exit the program
                        # exit(0)

if __name__ == "__main__":
    run("test_images")