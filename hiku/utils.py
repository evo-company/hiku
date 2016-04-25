_undefined = object()


def kw_only(mapping, required, optional=None):
    d = mapping.copy()
    result = []
    for arg in required:
        value = d.pop(arg, _undefined)
        if value is _undefined:
            raise TypeError('Required keyword argument {!r} not specified'
                            .format(arg))
        result.append(value)
    if optional is not None:
        for key in optional:
            value = d.pop(key, None)
            result.append(value)
    if d:
        raise TypeError('Unknown keyword arguments: {}'
                        .format(', '.join(d.keys())))
    return result
