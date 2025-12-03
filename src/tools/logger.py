from src.tools.common import get_assets_path
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

    assets_dir = get_assets_path()
    log_dir = assets_dir + "/" + log_dir
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


def list_loggers(show_handlers=False): 
    reg = logging.Logger.manager.loggerDict 
    rows = [] 
    for name, obj in reg.items(): 
        if not isinstance(obj, logging.Logger): 
            continue 

        level = logging.getLevelName(obj.level) if obj.level else "NOTSET" 
        eff = logging.getLevelName(obj.getEffectiveLevel()) 
        hs = [type(h).__name__ for h in obj.handlers] 
        rows.append((name, level, eff, obj.propagate, hs)) 
    rows.sort() 
    for name, level, eff, prop, hs in rows: 
        line = f"{name:40} level={level:7} effective={eff:7}, propagate={prop:7}"
        if show_handlers: 
            line += f" handlers={hs}" 
        print(line) 

    for n in logging.Logger.manager.loggerDict: 
        if n.startswith(("owl")): 
            print(n) 

list_loggers(False)
setup_logging(level=logging.DEBUG)
