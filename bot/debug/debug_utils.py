import time
import inspect

# Use as function decorator for printing the execution time of a function
# eg.
#   @PrintExecutionTime
#   async def on_step(self, iteration):
#       ...
#
# will print
#   on_step: 0.495ms
# whenever on_step is called

def PrintExecutionTime(func):
    def calculate_execution_time(start):
        return (time.time() - start) * 1000
    def print_execution_time(func_name, time):
        print(f'{func_name}: {round(time, 3)}ms')

    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        execution_time = calculate_execution_time(start)
        print_execution_time(f'{get_class_that_defined_method(func)} : {func.__name__}', execution_time)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        await func(*args, **kwargs)
        execution_time = calculate_execution_time(start)
        print_execution_time(f'{get_class_that_defined_method(func)} : {func.__name__}', execution_time)
    
    if (inspect.iscoroutinefunction(func)):
        return async_wrapper
    return wrapper

def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects