from federation.sdl import print_sdl


def print_service_sdl(extend_links, extend_nodes):
    types = map(print_sdl, extend_nodes)
    fields = map(print_sdl, extend_links)

    extend_sdl = "extend type Query {{ {fields} \n}}".format(
        fields='\n'.join(fields)
    )

    return '\n'.join([*types, extend_sdl])
