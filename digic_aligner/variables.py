#!/usr/bin/env python3

import os
METHOD=os.getenv("METHOD", "tfidf")

def get_default_threshold(method):
    if method=="tfidf":
        return "1.7"
    elif method=="bert":
        return "1.07"
    elif method=="laser":
        return "1.1"
    elif method=="sbert":
        return "1.30"
    else:
        raise ValueError("Unknown method")

THRESHOLD=float(os.getenv("THRESHOLD", get_default_threshold(METHOD)))

