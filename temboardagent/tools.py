import hashlib
import time
import re
from temboardagent.errors import HTTPError

def hash_id(id):
    """
    Hash (MD5) and returns a string built from the given id aimed to be used as
    an ID.
    """
    strid = 'id%s%d' % (id, time.time() * 1000)
    m = hashlib.md5()
    m.update(strid.encode('utf-8'))
    return m.hexdigest()

def validate_parameters(values, types):
    """
    Verify that each value of dict 'values' is valid. For doing that, we have
    to loop over all 'types' elements which are tuples: ('values' key,
    validation regexp, if the value item currently checked is a list of thing
    to check).
    If values[key] (or each element of it when it's a list) does not match 
    with the regexp then we trow an error.
    """
    for (key, typ, is_list) in types:
        try:
            if not is_list:
                # If 'typ' is a string, it must be considered as a regexp pattern.
                if type(typ) == str  and re.match(typ, str(values[key])) is None:
                    raise HTTPError(406, "Parameter '%s' is malformed." % (key,))
                if type(typ) != str and typ != type(values[key]):
                    raise HTTPError(406, "Parameter '%s' is malformed." % (key,))
            if is_list:
                for value in values[key]:
                    if type(typ) == str and re.match(typ, str(value)) is None:
                        raise HTTPError(406, "Parameter '%s' is malformed."
                                                % (key,))
                    if type(typ) != str and typ != type(value):
                        raise HTTPError(406, "Parameter '%s' is malformed."
                                                % (key,))
        except KeyError as e:
            raise HTTPError(406, "Parameter '%s' not sent." % (key,))
        except Exception as e:
            raise HTTPError(406, "Parameter '%s' is malformed." % (key,))
