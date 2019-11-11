from PIL import Image

for i in range(10):
    image = Image.open(str(i)+"_test_img.png")
    resize_img = image.resize((14,14))
    resize_img.save(str(i)+'_test_img.png')

#    for j in range(10, 16):
#        image = Image.open(str(i)+ "_" + str(j)+"_train_img.png")
#        resize_img = image.resize((14,14))
#        resize_img.save(str(i)+"_"+str(j)+'_train_img.png')

