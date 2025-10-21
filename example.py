"""This module is meant so serve as an introduction to creating the image itself"""

import numpy as np
import numpy.polynomial.polynomial as np_poly
from PIL import Image
import matplotlib.pyplot as plt

def simple_example():
    x = np.linspace(-250, 250, 15000)
    y = np.linspace(-250, 250, 15000)
    X, Y = np.meshgrid(x, y)
    color_values = X * Y

    # Visualize the array directly, seems to be working even for 15000 * 15000 points
    cmap = plt.cm.viridis
    color_norm = (color_values - color_values.min()) / (color_values.max() - color_values.min())
    img_array = (cmap(color_norm)[:, :, :3] * 255).astype(np.uint8)
    Image.fromarray(img_array).save('output.png')


simple_example()
