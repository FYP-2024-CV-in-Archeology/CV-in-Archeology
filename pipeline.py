import os
import sys
sys.path.append('../')
from pathlib import Path
import rawpy

def run(input_path):
    for dirpath, dirnames, filenames in os.walk(input_path):
        dirnames.sort()
        for file in filenames:
            path = Path(dirpath) / file
            
            dir, filename = path.parent.name, path.stem 
            if dir > '478130_4419430_8_20':
                if 'cr' in path.suffix.lower() and filename == '2':
                    print(path)
                    img = rawpy.imread(path)
                    cropped = 
                    if subImgs != None:
                        for i, sub_img in enumerate(subImgs):
                            imwrite(f'{i}.png', sub_img)
           