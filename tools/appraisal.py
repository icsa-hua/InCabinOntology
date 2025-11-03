from tools.logger import get_logger 

import time 
import traceback 

logger = get_logger("aiq_onto")


class SetupError(RuntimeError): 
    def __init__(self, step, exc_value): 
        super().__init__(f"[{step}]: failed: {exc_value}")
        self.step = step 
        self.original = exc_value


class StepContext(): 

    def __init__(self, name, *, catch=(Exception, ), verbose=False, supress=False, on_error=None): 
        self.name = name 
        self.catch = catch 
        self.__verbose = verbose
        self.supress = supress 
        self.on_error = on_error 

        self.t0: float = 0.0 
        self.elapsed_time: float = 0.0
        self.no_exception_found = None


    def __enter__(self): 
        if not self.__verbose: 
            logger.debug(f"[checked] SCM ==> {self.name}...") 
        else: 
            logger.info(f"[checked] SCM ==> {self.name}...")
        self.t0 = time.perf_counter() 
        return self 


    def __exit__(self, exc_type, exc_value, exc_tb): 
        self.elapsed_time = (time.perf_counter() - self.t0) *1e3 
        if exc_value is None:
            self.no_exception_found = True 
            logger.info(f"[{self.name}] took {self.elapsed_time:.2f} ms") 
            return False 

        self.no_exception_found = False 
        if not isinstance(exc_value, self.catch): 
            logger.debug(f"Unnexpected Error [{self.name}]: {self.elapsed_time:.2f}ms")
            return False 

        trace_back_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb)) 
        if self.on_error: 
            self.on_error(self.name, exc_value, trace_back_str) 

        if self.supress: 
            logger.debug(f"[!] [{self.name}] failed but optional: {exc_value}({self.elapsed_time:.2f}) ms")
        else: 
            raise SetupError(self.name, exc_value) 
