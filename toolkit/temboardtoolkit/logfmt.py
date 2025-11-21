def format(**kw):
    return " ".join([format_attribute(*i) for i in sorted(flatten(**kw))])


def format_attribute(key, value):
    if " " in str(value):
        value = '"%s"' % value
    return "%s=%s" % (key, value)


def flatten(**kw):
    for k, v in kw.items():
        if isinstance(v, dict):
            for kk, vv in flatten(**v):
                yield "%s.%s" % (k, kk), vv
        else:
            yield k, v
