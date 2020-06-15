#!/usr/bin/env python3

import os
METHOD=os.getenv("METHOD", "tfidf")

def get_default_threshold(method):
    if method=="tfidf":
        return "2.0"
    elif method=="bert":
        return "1.05"
    elif method=="laser":
        return "1.1"
    else:
        raise ValueError("Unknown method")

THRESHOLD=float(os.getenv("THRESHOLD", get_default_threshold(METHOD)))

