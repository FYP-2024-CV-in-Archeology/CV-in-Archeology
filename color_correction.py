import utils
import numpy as np
import rawpy
import cv2 as cv
# import matplotlib.pyplot as plt
from skimage import img_as_ubyte


# def white_bal(img):
#     result = cv.cvtColor(img, cv.COLOR_BGR2LAB)
#     avg_a = np.average(result[:, :, 1])
#     avg_b = np.average(result[:, :, 2])
#     result[:, :, 1] = result[:, :, 1] - \
#         ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
#     result[:, :, 2] = result[:, :, 2] - \
#         ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
#     result = cv.cvtColor(result, cv.COLOR_LAB2BGR)
#     return result


def percentile_whitebalance(image, percentile_value):
        whitebalanced = img_as_ubyte(
                (image*1.0 / np.percentile(image, 
                percentile_value, axis=(0, 1))).clip(0, 1))
        return whitebalanced


def toOpenCVU8(img):
    out = img * 255
    out[out < 0] = 0
    out[out > 255] = 255
    out = out.astype(np.uint8)
    return out

def imresize(img, size=1500):
    # if is24Checker:
    #     img = np.rot90(img)
    if max(img.shape[1], img.shape[0]) >= size:
        if img.shape[1] >= img.shape[0]:
            width = size
            height = int(img.shape[0] * size / img.shape[1])
        elif img.shape[0] >= img.shape[1]:
            width = int(img.shape[1] * size / img.shape[0])
            height = size
        dim = (width, height)
        img = cv.resize(img, dim)
    return img

def get_target_colour_matrix(targets):
    list_of_targets = []
    for target in targets:
        list_of_targets.append(targets[target])
    target_matrix = np.vstack(list_of_targets)
    return target_matrix

def get_avg_colour_matrix(avgs):
    list_of_avgs = []
    for avg in avgs:
        list_of_avgs.append(avgs[avg])
    avg_matrix = np.vstack(list_of_avgs)
    return avg_matrix

def getCardsGreenPos(img):
    mask = cv.inRange()

def color_correction(img, detector, is24Checker): # img is rgb
    # bgrImg = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    # brgImg = percentile_whitebalance(bgrImg, 97.5)

    rgb = img.copy().astype(np.float64) / 255.0 # can be ignored?

    # detector = cv.mcc.CCheckerDetector_create()

    # is24Checker = utils.detect24Checker(bgrImg.copy(), detector)

    if is24Checker:
        chartsRGB = [
            [[115, 83, 68]],
            [[196, 147, 127]],
            [[91, 122, 155]],
            [[94, 108, 66]],
            [[129, 128, 176]],
            [[98, 190, 168]],
            [[223, 124, 47]],
            [[72, 92, 174]],
            [[194, 82, 96]],
            [[93, 60, 103]],
            [[162, 190, 62]],
            [[229, 158, 41]],
            [[49, 66, 147]],
            [[77, 153, 71]],
            [[173, 57, 60]],
            [[241, 201, 25]],
            [[190, 85, 150]],
            [[0, 135, 166]],
            [[242, 243, 245]],
            [[203, 203, 204]],
            [[162, 163, 162]],
            [[120, 120, 120]],
            [[84, 84, 84]],
            [[50, 50, 52]],
        ]

        chartsRGB_np = np.array(chartsRGB).astype(float) / 255.0
        
        checker = detector.getBestColorChecker()
        chartsRGB = checker.getChartsRGB()

        src = chartsRGB[:, 1].copy().reshape(24, 1, 3) / 255.0

        model = cv.ccm_ColorCorrectionModel(
            src, chartsRGB_np, cv.ccm.COLOR_SPACE_sRGB)

        model.setWeightCoeff(1)

        model.run()

        calibrated = model.infer(rgb)

        calibrated = toOpenCVU8(calibrated.copy())

        return calibrated


    img = img.astype(np.uint8)

    AVG = { # to be extracted from the images
        'blue': np.array([0.0, 0.0, 0.0]),
        'green': np.array([0.0, 0.0, 0.0]),
        'yellow': np.array([0.0, 0.0, 0.0]),
        'red': np.array([0.0, 0.0, 0.0]),
        'black': np.array([0.0, 0.0, 0.0]),
        'white': np.array([0.0, 0.0, 0.0])
    }

    white_balanced = img.copy()
    hsv_image = cv.cvtColor(white_balanced, cv.COLOR_RGB2HSV)

    for colour in utils.COLOURS:
        mask = cv.inRange(hsv_image, utils.COLOUR_RANGE[colour][0], utils.COLOUR_RANGE[colour][1])
        mask_updated = cv.morphologyEx(mask, cv.MORPH_CLOSE, utils.kernel)
        contours, _ = cv.findContours(mask_updated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        contours = list(filter(lambda x: len(cv.approxPolyDP(x, 0.02 * cv.arcLength(x, True), True)) == 4
                           and
                           cv.contourArea(x)/(cv.boundingRect(x)[2]*cv.boundingRect(x)[3]) > 0.9
                           , contours))
        contours = sorted(contours, key=cv.contourArea, reverse=True)

        if len(contours) > 0:
            bounding_rect = cv.boundingRect(contours[0])
            roi = img[bounding_rect[1]:bounding_rect[1] + bounding_rect[3], 
                    bounding_rect[0]:bounding_rect[0] + bounding_rect[2]]
        
        avg = np.mean(roi, axis=(0, 1))

        AVG[colour] = avg

    target_matrix = get_target_colour_matrix(utils.TARGETS)

    avg_matrix = get_avg_colour_matrix(AVG)

    U, s, Vt = np.linalg.svd(avg_matrix.T @ target_matrix)
    color_correction_matrix = U @ Vt
    corrected_image_svd = cv.transform(img, color_correction_matrix)

    #to_return = cv.cvtColor(corrected_image_svd, cv.COLOR_RGB2BGR)
    # to_return_white_balanced = percentile_whitebalance(corrected_image_svd, 97.5)

    # to_return_white_balanced = cv.add(to_return_white_balanced, (10, 10, 10, 0)) # add brightness
    
    return corrected_image_svd


if __name__ == "__main__":
    img = rawpy.imread(r'd:\ararat\data\files\N\38\478130\4419430\33\finds\individual\45\photos\2.CR3')
    assert img is not None, "file could not be read, check with os.path.exists()"
    detector = cv.mcc.CCheckerDetector_create()

    # is24Checker = utils.detect24Checker(bgrImg.copy(), detector)
    img = img.postprocess()
    # show the image in a window
    utils.showImage(color_correction(img, detector, False))