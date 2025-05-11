import pandas as pd
import json

from utils import read_json

def ratings_read_test(file):
    jds = read_json(file)
    print(jds.loc['2025-05-07 20:00':'2025-05-07 22:59', 'Digi 24'].resample('15min').mean().round(2))
