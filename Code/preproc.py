from xml.dom import minidom
import numpy as np
import re
from scipy import ndimage
from matplotlib.path import Path
from matplotlib import pyplot as plt
from matplotlib import image
import os
from skimage import filters
import pickle
#Based on https://stackoverflow.com/questions/21566610/crop-out-partial-image-using-numpy-or-scipy



def masking(number, img_fold, doc_fold):
    
    img = image.imread(os.path.join(img_fold, '%d.jpg' % number))

    doc = minidom.parse(os.path.join(doc_fold, '%d.svg' % number))

    masks = {}
    result = {}
    for path in doc.getElementsByTagName('path'):
        _d = path.getAttribute('d')
        _d = re.sub('[MLSZ]', '', _d)
        d = np.fromstring(_d, dtype=float, sep=' ')
        d = np.reshape(d, (int(len(d)/2), 2))
        masks[path.getAttribute('id')] = d
    doc.unlink()

    for i in masks:
        cell = masks[i]
        pth = Path(cell, closed=False)

        xc = cell[:, 0]
        yc = cell[:, 1]

        nr, nc = img.shape
        ygrid, xgrid = np.mgrid[:nr, :nc]
        xypix = np.vstack((xgrid.ravel(), ygrid.ravel())).T

        mask = pth.contains_points(xypix)

        mask = mask.reshape(img.shape)

        masked = np.ma.masked_array(img, ~mask)

        xmin, xmax = int(xc.min()), int(np.ceil(xc.max()))
        ymin, ymax = int(yc.min()), int(np.ceil(yc.max()))
        trimmed = masked[ymin:ymax, xmin:xmax]
        result[i] = trimmed

        # testing print the different words
        # imgplot = plt.imshow(trimmed, cmap=plt.cm.gray)
        # plt.show()
    return result

def bin(data):
    
    results = {}
    
    for i in data:
        word = data[i].filled(255)
        #Only keep the dark parts
        tresh = filters.threshold_otsu(word)
        results[i] = word<tresh
    return results

def norm(data):
    height = max([x.shape[0] for x in data.values()])
    width = max([x.shape[1] for x in data.values()])
    
    results = {}
    for i in data:
        foo = data[i]
        target = np.zeros((height, width))
        target[:foo.shape[0], :foo.shape[1]] = foo
        results[i] = target
    return results


def main():
    dataset = os.path.join('..', 'dataset')
    img_fold = os.path.join(dataset, 'images')
    doc_fold = os.path.join(dataset, 'ground-truth', 'locations')
    
    numbers = []
    for file in os.listdir(doc_fold):
        number = int(file.replace('.svg',''))
        numbers.append(number)
    print(numbers)
    _binarised = []
    binarised = {}
    print('starting masking and binarisation')
    for number in numbers:
        masked = masking(number, img_fold, doc_fold)
        _binarised.append(bin(masked))
        print('Page %d done'%number)
    print('Data binarized')
    for d in _binarised:
        binarised.update(d)
    print('dictionary fusionned')
    
    results = norm(binarised)
    print(results['270-01-01'])
    
    # pkl = os.path.join(dataset, 'pkl')
    # with open(pkl,'preprocess data','wb') as f:
    #     pickle.dump(results, f, pickle.HIGHEST_PROTOCOL)
    # print('preprocessing done')
    return(results)
    
