import picamera
from time import sleep

for i in range(0,10):
    cam = picamera.PiCamera()
    cam.rotation = 180
    cam.resolution = (112,112)
    cam.color_effects = (128, 128)
    cam.start_preview()
    sleep(4) # 5sec
    image_name = str(i) + '_test_img.png'
#    image_name ='9_' + str(i) + '_train_img.png'
    cam.capture(image_name)
    cam.stop_preview()
    cam.close()

