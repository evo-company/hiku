def async_wrapper(func):
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
