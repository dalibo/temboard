def remove_passwords(instances):
    clean_instances = []
    for instance in instances:
        clean_instance = {}
        for k in instance.keys():
            if k != 'password':
                clean_instance[k] = instance[k]
        clean_instances.append(clean_instance)
    return clean_instances
