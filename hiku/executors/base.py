def process_wait_list(wait_list, futures):
    for fut_set, callback in wait_list:
        fut_set.difference_update(futures)
        if fut_set:
            yield fut_set, callback
        else:
            callback()
