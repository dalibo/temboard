from temboardagent.logger import get_logger, get_tb
from temboardagent.api import check_sessionid
from temboardagent.errors import HTTPError
from temboardagent.spc import connector, error


def api_function_wrapper_pg(config, http_context, sessions, module,
                            function_name):
    """
    API function wrapper in charge of:
        - instanciating a new logger;
        - check the user session id;
        - start a new PostgreSQL connection;
        - call the function 'function_name' from 'module_name' module and
          return its result;
        - close PG connection.
    """
    logger = get_logger(config)
    logger.debug("Calling %s.%s()." % (module.__name__, function_name,))
    logger.debug(http_context)

    try:
        username = check_sessionid(http_context['headers'], sessions)
        http_context['username'] = username
        conn = connector(
            host=config.postgresql['host'],
            port=config.postgresql['port'],
            user=config.postgresql['user'],
            password=config.postgresql['password'],
            database=config.postgresql['dbname']
        )
        conn.connect()
        dm = getattr(module, function_name)(conn, config, http_context)
        conn.close()
        logger.debug("Done.")
        return dm

    except (error, Exception, HTTPError) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        try:
            conn.close()
        except Exception:
            pass
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")


def api_function_wrapper(config, http_context, sessions, module,
                         function_name):
    """
    API function wrapper in charge of:
        - instanciating a new logger;
        - check the user session id;
        - call the function 'function_name' from 'module_name' module and
          return its result;
    """
    logger = get_logger(config)
    logger.debug("Calling %s.%s()." % (module.__name__, function_name,))
    logger.debug(http_context)

    try:
        username = check_sessionid(http_context['headers'], sessions)
        http_context['username'] = username
        dm = getattr(module, function_name)(config, http_context)
        logger.debug("Done.")
        return dm

    except (Exception, HTTPError) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.debug("Failed.")
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")
