def kw_only(names, kwargs):
    kwargs = kwargs.copy()
    values = [kwargs.pop(name, None) for name in names]
    if kwargs:
        raise TypeError('Unknown keyword arguments: {}'
                        .format(', '.join(kwargs.keys())))
    else:
        return values
