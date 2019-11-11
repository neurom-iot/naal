import picamera
from time import sleep
from PIL import Image
import numpy as np

#capture image
def capture_image(image_num, capture_size):
    for i in range(0,image_num):
        cam = picamera.PiCamera()
        cam.rotation = 180
        cam.resolution = (capture_size, capture_size)
        cam.color_effects = (128, 128)
        cam.start_preview()
        input()
        image_name = str(i) + '_test_img.png'
        cam.capture(image_name)
        cam.stop_preview()
        cam.close()

#gray_scale
def gray_scale(image_num):
    for i in range(0, image_num):
        image_file = Image.open(str(i)+"_test_img.png")
        image_file = image_file.convert('L')
        tmp_np = np.array(image_file)
        image_file = Image.fromarray(tmp_np)
        image_file.save(str(i) + '_test_img.png')

#image_resize
def image_resize(image_num, image_size):
    for i in range(0, image_num):
        image = Image.open(str(i)+"_test_img.png")
        resize_img = image.resize((image_size, image_size))
        resize_img.save('test_img/' + str(i) + '_test_img.png')


image_num = 1
capture_size = 112
image_size = 14
capture_image(image_num, capture_size)
gray_scale(image_num)
image_resize(image_num, image_size)
