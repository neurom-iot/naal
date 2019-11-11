import numpy as np
import os
from PIL import Image

def get_max_value(img_to_np):
    return img_to_np.max()

def get_chroma(img_to_np):
    sum_np=0
    for i in range(14):
        for j in range(14):
            sum_np += img_to_np[i][j]
    chroma = sum_np / 196.0
    if(chroma<75):
        chroma += 30
    elif(chroma<80):
        chroma += 25
    elif(chroma<85):
        chroma += 23
    elif(chroma<90):
        chroma += 20
    elif(chroma<95):
        chroma += 16
    elif(chroma<100):
        chroma += 11
    chroma=110
    return chroma

def get_background(img_np):
    white_bg = 1
    black_bg = 0

    sum_np = 0
    for i in range(14):
        for j in range(14):
            sum_np += img_np[i][j]

    print("sum : " + str(sum_np))
    print("avg : " + str(sum_np/196.0))
    if(sum_np/196.0 > 115):
        return white_bg
    else:
        return black_bg

def load_test_img():
    global chroma
    first = True
    image_num = 0
    for file in os.listdir("./test_img/"):
        if file.endswith(".png"):
          image_num += 1

    test_y = np.zeros(image_num, dtype='i')
    for img_n in range(0, image_num):
        img_name = "test_img/" + str(img_n) + "_test_img.png"
        img = Image.open(open(img_name, 'rb'))
        
        img_to_np = np.array(img, dtype=float)
        print(img_to_np)
        bg = get_background(img_to_np)
        img_to_np = img_to_np / get_chroma(img_to_np)
        img_to_np = img_to_np / get_max_value(img_to_np)
        img_size = np.sqrt(len(img_to_np.flatten()))
        img_size = int(img_size)
        print(img_to_np)

        print("bg : " + str(bg))
        if(bg):
            for i in range(0, img_size):
                for j in range(0, img_size):
                    if(img_to_np[i][j]<0.4):
                        img_to_np[i][j] = 1.0
                    else:
                        img_to_np[i][j] = 0
        else:
            for i in range(0, img_size):
                for j in range(0, img_size):
                    if(img_to_np[i][j]<0.5):
                        img_to_np[i][j] = 0
                    else:
                        img_to_np[i][j] = 1.0
        
        print(img_to_np)
        if(first):
            test_mnist_np = img_to_np.flatten()
            first = False
        else:
            test_mnist_np = np.hstack([test_mnist_np, img_to_np.flatten()])
        test_y[img_n] = img_n % 10

    test_mnist_np = test_mnist_np.reshape(image_num, img_size**2)        
    return test_mnist_np, test_y

def load_train_img():
    global chroma
    first = True
    image_num = 0
    for file in os.listdir("./train_img/"):
        if file.endswith(".png"):
          image_num += 1
    
    train_y = np.zeros(image_num, dtype='i')
    for img_n in range(0, image_num//10):
        for n in range(0, 10): 
            img_name ='train_img/' + str(n) + '_' + str(img_n) + '_train_img.png'
            img = Image.open(img_name)

            img_to_np = np.array(img, dtype=float)
            img_to_np = img_to_np / get_max_value(img_to_np) 

            img_size = np.sqrt(len(img_to_np.flatten()))
            img_size = int(img_size)
            for i in range(0, img_size):
                for j in range(0, img_size):
                    if(img_to_np[i][j]<0.5):
                        img_to_np[i][j] = 0
                    else:
                        img_to_np[i][j] = 1.0

            if(first):
                train_mnist_np = img_to_np.flatten()
                first = False
            else:
                train_mnist_np = np.hstack([train_mnist_np, img_to_np.flatten()])
            train_y[img_n * 10 + n] = n

    train_mnist_np = train_mnist_np.reshape(image_num, img_size**2)
    return train_mnist_np, train_y
