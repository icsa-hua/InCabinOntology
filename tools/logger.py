import logging 
import datetime 
import os 


def remove_logger(name=None): 
    logr = logging.getLogger(name) 
    logr.propagate = True 
    logr.handlers.clear() 
    logr.setLevel(logging.WARNING)

def setup_logging(level=logging.DEBUG, log_dir="logs"): 
    root = logging.getLogger("aiq_onto")
    root.setLevel(level) 

    parent_dir = os.getcwd()
    log_dir = parent_dir + "/" + log_dir
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ) 
    
    fh = logging.FileHandler(log_file, encoding="utf-8", mode="w")
    fh.setLevel(level)
    fh.setFormatter(fmt)

    root.addHandler(fh)
    root.propagate = True 

def get_logger(name=None): 
    return logging.getLogger(name)

setup_logging(level=logging.DEBUG)
