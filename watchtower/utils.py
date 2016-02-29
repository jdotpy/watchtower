from importlib import import_module

def import_class(path):
    parts = path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]
    m = import_module(module_path)
    obj = getattr(m, class_name)
    return obj

def extract(item, attr, default=None):
    if hasattr(item, '__getitem__'):
        try:
            return item.__getitem__(attr)
        except KeyError:
            pass
    return getattr(item, attr, default)

def index_queryset(queryset, key_field='id', value_field=None, multiple=False):
    index = {} 
    for item in queryset:
        key = extract(item, key_field, None)
        if value_field is None:
            value = item
        else:
            value = extract(item, value_field, None)
        if multiple:
            if key not in index:
                index[key] = [value]
            else:
                index[key].append(value)
        else:
            index[key] = value
    return index
