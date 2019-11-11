from PIL import Image
import numpy as np

for i in range(0, 10):
    for j in range(0, 20):
        image_file = Image.open(str(i) + "_" + str(j)+"_train_img.png")
        tmp_np = np.array(image_file)
        tmp_np = tmp_np + 20
        image_file = Image.fromarray(tmp_np)
        image_file.save(str(i) + "_" + str(20 + j) + '_train_img.png')

for i in range(0, 10):
    for j in range(0, 20):
        image_file = Image.open(str(i) + "_" + str(j)+"_train_img.png")
        tmp_np = np.array(image_file)
        tmp_np = tmp_np - 10
        image_file = Image.fromarray(tmp_np)
        image_file.save(str(i) + "_" + str(40 + j) + '_train_img.png')


