from PIL import Image
import numpy as np

for i in range(10):

    image_file = Image.open(str(i)+"_test_img.png")
    image_file = image_file.convert('L')
    tmp_np = np.array(image_file)
    print(tmp_np.shape)
    image_file = Image.fromarray(tmp_np)
    image_file.save(str(i) + '_test_img.png')

#    for j in range(10,16):
#        image_file = Image.open(str(i)+ "_"+str(j)+"_test_img.png")
#        image_file = image_file.convert('L')
#        tmp_np = np.array(image_file)
#        print(tmp_np.shape)
#        image_file = Image.fromarray(tmp_np)
#        image_file.save(str(i) + "_" + str(j) + '_train_img.png')

