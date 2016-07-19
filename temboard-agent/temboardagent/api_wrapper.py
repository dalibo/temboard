from temboardagent.logger import get_logger
from temboardagent.api import check_sessionid
from temboardagent.errors import HTTPError
from temboardagent.spc import connector, error
from traceback import format_exc
import sys

def api_function_wrapper_pg(config, http_context, sessions, module, function_name):
    """
    Simple API function wrapper in charge of:
        - instanciate a new logger;
        - check the user session id;
        - start a new PostgreSQL connexion;
        - call a function named 'function_name' from 'module_name' module and return its result;
        - close the PG connexion.
    """
    logger = get_logger(config)
    logger.info("%s - %s" % (module.__name__, function_name,))
    username = check_sessionid(http_context['headers'], sessions)

    http_context['username'] = username

    conn = connector(
        host = config.postgresql['host'],
        port = config.postgresql['port'],
        user = config.postgresql['user'],
        password = config.postgresql['password'],
        database = config.postgresql['dbname']
    )
    try:
        conn.connect()
        dm = getattr(module, function_name)(conn, config, http_context)
        conn.close()
        return dm

    except (error, Exception, HTTPError) as e:
        logger.error(format_exc())
        try:
            conn.close()
        except Exception:
            pass
        if isinstance(e, HTTPError):
            raise HTTPError(e.code, e.message['error'])
        else:
            raise HTTPError(500, "Internal error.")

def api_function_wrapper(config, http_context, sessions, module, function_name):
    """
    Simple API function wrapper in charge of:
        - instanciate a new logger;
        - check the user session id;
        - call a function named 'function_name' from 'module_name' module and return its result;
    """
    logger = get_logger(config)
    logger.info("%s - %s" % (module.__name__, function_name,))
    username = check_sessionid(http_context['headers'], sessions)
    
    http_context['username'] = username
    try:
        dm = getattr(module, function_name)(config, http_context)
        return dm
    except HTTPError as e:
        logger.error(format_exc())
        raise HTTPError(e.code, e.message['error'])
    except Exception as e:
        logger.error(format_exc())
        raise HTTPError(500, "Internal error.")
