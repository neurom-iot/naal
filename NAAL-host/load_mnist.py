import numpy as np

# Requires python image library: pip install pillow
from PIL import Image

import nengo
from nengo_extras.data import load_mnist
from nengo_extras.vision import Gabor, Mask

import nengo_fpga

# ------ MISC HELPER FUNCTIONS -----
def resize_img(img, im_size, im_size_new):
    # Resizes the MNIST images to a smaller size so that they can be processed
    # by the FPGA (the FPGA currently has a limitation on the number of
    # dimensions and neurons that can be built into the network)
    # Note: Requires the python PIL (pillow) library to work
    img = Image.fromarray(img.reshape((im_size, im_size)) * 256, 'F')
    img = img.resize((im_size_new, im_size_new), Image.ANTIALIAS)
    return np.array(img.getdata(), np.float32) / 256.0


def one_hot(labels, c=None):
    # One-hot function. Converts a given class and label list into a vector
    # of 0's (no class match) and 1's (class match)
    assert labels.ndim == 1
    n = labels.shape[0]
    c = len(np.unique(labels)) if c is None else c
    y = np.zeros((n, c))
    y[np.arange(n), labels] = 1
    return y

# ---------------- BOARD SELECT ----------------------- #
# Change this to your desired device name
board = 'pynq'
# ---------------- BOARD SELECT ----------------------- #

# Set the nengo logging level to 'info' to display all of the information
# coming back over the ssh connection.
nengo.utils.logging.log('info')

# Set the rng state (using a fixed seed that works)
rng = np.random.RandomState(9)

# Load the MNIST data
(X_train, y_train), (X_test, y_test) = load_mnist()

X_train = 2 * X_train - 1  # normalize to -1 to 1
X_test = 2 * X_test - 1  # normalize to -1 to 1

# Get information about the image
im_size = int(np.sqrt(X_train.shape[1]))  # Dimension of 1 side of the image

# Resize the images
reduction_factor = 2
                      

if reduction_factor > 1:
    im_size_new = int(im_size // reduction_factor)

    X_train_resized = np.zeros((X_train.shape[0], im_size_new ** 2))
    for i in range(X_train.shape[0]):
        X_train_resized[i, :] = resize_img(X_train[i], im_size, im_size_new)
    X_train = X_train_resized

    X_test_resized = np.zeros((X_test.shape[0], im_size_new ** 2))
    for i in range(X_test.shape[0]):
        X_test_resized[i, :] = resize_img(X_test[i], im_size, im_size_new)
    X_test = X_test_resized

    im_size = im_size_new

# Generate the MNIST training and test data
train_targets = one_hot(y_train, 10)
test_targets = one_hot(y_test, 10)


print(X_train)
print("train_targets!!")
print(X_test)
## Set up the vision network parameters
#n_vis = X_train.shape[1]  # Number of training samples
#n_out = train_targets.shape[1]  # Number of output classes
#n_hid = 16000 // (im_size ** 2)  # Number of neurons to use
## Note: the number of neurons to use is limited such that NxD <= 16000,
##       where D = im_size * im_size, and N is the number of neurons to use
#gabor_size = (int(im_size / 2.5), int(im_size / 2.5))  # Size of the gabor filt

## Generate the encoders for the neural ensemble
#encoders = Gabor().generate(n_hid, gabor_size, rng=rng)
#encoders = Mask((im_size, im_size)).populate(encoders, rng=rng, flatten=True)

## Ensemble parameters
#max_firing_rates = 100
#ens_neuron_type = nengo.neurons.RectifiedLinear()
#ens_intercepts = nengo.dists.Choice([-0.5])
#ens_max_rates = nengo.dists.Choice([max_firing_rates])

## Output connection parameters
#conn_synapse = None
#conn_eval_points = X_train
#conn_function = train_targets
#conn_solver = nengo.solvers.LstsqL2(reg=0.01)

## Visual input process parameters
#presentation_time = 0.25
                                                                            