def list_spliter_by_batch_size(my_list, batch_size):
    return [my_list[i * batch_size:(i + 1) * batch_size] for i in range((len(my_list) + batch_size - 1) // batch_size)]
