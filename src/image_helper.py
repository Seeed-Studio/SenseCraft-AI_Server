import cv2
import numpy as np

RED = 1
BLUE = 2
GREEN = 3
BLACK = 4
WHITER = 5
COLOR = {
    RED: (0, 0, 255),
    BLUE: (255, 0, 0),
    GREEN: (0, 255, 0),
    BLACK: (0, 0, 0),
    WHITER: (255, 255, 255),
}

RIGHT_TOP = 1
RIGHT_DOWN = 2


def x_y_for_text(img, text, font, font_scale, thickness, way=RIGHT_TOP):
    """
    calculate x,y for text
    - TODO: more custom params
    """
    # get text size for calculate
    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
    if int(way) == RIGHT_DOWN:
        x = img.shape[1] - text_width - 10
        y = img.shape[0] - 2 * text_height
        return (int(x), int(y))
    # RIGHT_TOP
    x = img.shape[1] - text_width - 10
    y = 2 * text_height
    return (int(x), int(y))


def add_text(
    img, text="--", font_scale=1, thickness=3, colorIndex=GREEN, way=RIGHT_TOP
):
    """
    add text on image
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    location = x_y_for_text(img, text, font, font_scale, thickness, way)
    cv2.putText(img, text, location, font, font_scale, COLOR[colorIndex], thickness)


def img_copy(raw):
    return np.copy(raw)
