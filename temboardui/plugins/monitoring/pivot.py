import csv
import operator


def get_csv_data(fd):
    # CSV parser as generator
    for r in csv.DictReader(fd):
        yield r


def pivot_timeserie(fd, index, key, value, output):
    # Simple pivot table implementation.
    # Beware, input data *MUST* be ordered by index value.
    fd.seek(0)
    keys = {}
    p = 1
    # We need to get the keys first
    for r in get_csv_data(fd):
        if r[key] not in keys:
            keys[r[key]] = p
            p += 1
    sk = sorted(keys.items(), key=operator.itemgetter(1))
    # CSV Header
    line = [index] + [x[0] for x in sk]
    p_index = ''
    fd.seek(0)
    for r in get_csv_data(fd):
        if r[index] != p_index:
            # As data are ordered if we meet a new index value then the current
            # line is complete.
            output.write(','.join(line)+'\n')
            # And start a new line
            line = [''] * (len(keys)+1)
            line[0] = r[index]
        # Append value to the current line
        line[keys[r[key]]] = r[value]
        # Keep a track of the index value
        p_index = r[index]
    # Write the last line
    output.write(','.join(line)+'\n')
