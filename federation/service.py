from federation.sdl import print_sdl


def resolve_service(extend_links, extend_nodes):
    types = map(print_sdl, extend_nodes)
    fields = map(print_sdl, extend_links)

    extend_sdl = "extend type Query {{ {fields} \n}}".format(
        fields='\n'.join(fields)
    )

    sdl = '\n'.join([*types, extend_sdl])
    return [
        dict(sdl=sdl)
    ]
