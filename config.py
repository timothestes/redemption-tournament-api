def str_to_bool(value):
    return str(value).strip().lower() in {"true", "1", "t", "yes", "True"}
