# -*- coding: utf-8 -*-
#import numpy as np
#import datetime
#from dateutil import tz
#import io
#import os
#import math
#import codecs
#import matplotlib.pyplot as plt
##import matplotlib.gridspec as gridspec
#import matplotlib.image as mpimg
def LinReg(x1,y1,x2,y2,x):
    #lineáris regresszió: x1,y1 és x2,y2 pontokkal megadott egyenes x pontjához
    #y-t számol
    if x1 == x2:
        return y1
    else:
        return (y2 - y1) * (x - x1) / (x2 - x1) + y1