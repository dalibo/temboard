import errno
import functools
import sys
import time
import uuid
import logging
import os.path
import signal
from ast import literal_eval
from select import select, error as SelectError
from datetime import datetime
from collections import deque
from multiprocessing import AuthenticationError, Process, Queue
from multiprocessing.connection import Listener, Client
from textwrap import dedent

from .services import Service
from .errors import StorageEngineError, UserError
from .perf import PerfCounters
from .pycompat import PY2, Empty


TM_DEF_LISTENER_ADDR = '/tmp/.temboardsched.sock'

# Message types
MSG_TYPE_TASK_NEW = 0
MSG_TYPE_TASK_STATUS = 1
MSG_TYPE_TASK_CANCEL = 2
MSG_TYPE_TASK_ABORT = 3
MSG_TYPE_TASK_LIST = 4
MSG_TYPE_RESP = 5
MSG_TYPE_ERROR = 6
MSG_TYPE_CONTEXT = 7

# Task status
TASK_STATUS_DEFAULT = 1
TASK_STATUS_SCHEDULED = 2
TASK_STATUS_QUEUED = 4
TASK_STATUS_DOING = 8
TASK_STATUS_DONE = 16
TASK_STATUS_FAILED = 32
TASK_STATUS_CANCELED = 64
TASK_STATUS_ABORTED = 128
TASK_STATUS_ABORT = 256

logger = logging.getLogger(__name__)


def ensure_str(value):
    # This code is used to instanciate multiprocessing.connection.Client. It
    # requires a str object in both Python 2 and 3.
    if type(value) is not str:
        if PY2:
            # From unicode to str.
            value = value.encode('utf-8')
        else:
            # From bytes to str.
            value = value.decode('utf-8')
    return value


def make_worker_definition(function, pool_size):
    return {
        'name': function.__name__,
        'pool_size': pool_size,
        'module': function.__module__,
        'function': function.__name__
    }


class Task(object):

    def __init__(self, worker_name=None, options=None, id=None,
                 status=TASK_STATUS_DEFAULT, start_datetime=None,
                 redo_interval=None, stop_datetime=None, output=None,
                 expire=3600):
        self.worker_name = worker_name
        self.options = options
        self.status = status
        self.start_datetime = start_datetime or datetime.utcnow()
        self.redo_interval = redo_interval
        self.stop_datetime = stop_datetime
        self.id = id
        self.output = output
        # Task expiration timeout in seconds.
        # Ended Tasks are removed from memory when current time exceeds
        # self.stop_datetime + self.expire.
        self.expire = expire

    def __repr__(self):
        return str(self.__dict__)


class Message(object):

    def __init__(self, type, content):
        self.type = type,
        self.content = content

    def __repr__(self):
        return str(self.__dict__)


class TaskList(object):

    def __init__(self, engine):
        self.engine = engine

    def recover(self):
        self.engine.recover(
            st_doing=(TASK_STATUS_DOING | TASK_STATUS_QUEUED),
            st_aborted=TASK_STATUS_ABORTED,
            st_scheduled=TASK_STATUS_SCHEDULED,
            st_default=TASK_STATUS_DEFAULT,
            now=datetime.utcnow()
        )

    def push(self, task):
        # Add a new task to the list
        if not task.id:
            task.id = self._gen_task_id()
        # Insert the task
        self.engine.insert(task)
        return task.id

    def get(self, id):
        return self.engine.get(id)

    def update(self, id, **kwargs):
        task = self.engine.get(id)
        if not task:
            raise Exception("Task id=%s not found" % id)

        for k, v in kwargs.items():
            try:
                getattr(task, k)
            except AttributeError:
                raise Exception("Task attribute %s does not exist" % k)
            setattr(task, k, v)
        self.engine.update(task)

    def rm(self, id):
        self.engine.delete(id)

    def _gen_task_id(self):
        id = str(uuid.uuid4())[0:8]

        while self.engine.exists(id):
            # If a task with the same id exists, try with a new random id
            id = str(uuid.uuid4())[0:8]

        return id

    def get_n_todo(self):
        # Return the number of ongoing tasks (QUEUED | DOING)
        return self.engine.count_by_status(
            TASK_STATUS_QUEUED | TASK_STATUS_DOING
        )

    def list(self):
        return self.engine.list()

    def list_to_do(self, status, now, redo=False):
        return self.engine.list_to_do(status, now, redo)

    def purge(self, status, now):
        return self.engine.purge(status, now)


class TaskManager(object):
    @staticmethod
    def send_message(address, message, authkey=''):
        conn = Client(ensure_str(address), authkey=authkey)
        conn.send(message)
        res = conn.recv()
        conn.close()
        return res


class Scheduler(object):
    trace = False

    def __init__(self, address, authkey):
        # Listener for TM -> Scheduler IPC
        self.listener = None
        # Listener address
        self.address = address
        # Listener authentication key
        self.authkey = authkey
        # Queue used to send Task orders (start, stop) to WorkerPool
        self.task_queue = None
        # Queue used to notify Scheduler about Task status
        self.event_queue = None
        self.task_list = None
        self.context = dict()
        self.worker_pool = None
        self.shutdown = None
        self.task_list_engine = None
        self.last_schedule = 0
        self.last_vacuum = 0
        self.select_timeout = None

    def set_context(self, key, val):
        self.context[key] = val

    def get_context(self):
        return self.context

    def handle_listener_message(self):
        # read message from the listener
        try:
            conn = self.listener.accept()
        except AuthenticationError as e:
            logger.exception(e)
            logger.error("Authentication failed")
            return

        try:
            message = conn.recv()
        except Exception as e:
            conn.close()
            logger.exception(e)
            logger.error("Unable to read the message")
            return

        message.type = message.type[0]
        if self.trace:
            logger.debug("Received Message=%s" % message)

        # handle incoming message and return a response
        conn.send(self.handle_message(message))
        conn.close()

    def handle_event_queue_message(self):
        # read message from the event queue
        try:
            message = self.event_queue.get(False)
        except Empty:
            # should not happen
            logger.error("Event queue empty")
            return

        message.type = message.type[0]
        if self.trace:
            logger.debug("Received Message=%s" % message)

        # handle incoming message
        self.handle_message(message)

    def setup(self):
        # Need to shutdown ?
        self.shutdown = False
        # Instanciate a new Listener
        self.listener = Listener(self.address, family='AF_UNIX',
                                 authkey=self.authkey)
        # TODO
        # self.sync_bootstrap_options()
        self.select_timeout = 1

    def serve1(self):
        # wait for I/O on Listener and event Queue
        try:
            fds, _, _ = select(
                [self.listener._listener._socket.fileno(),
                 self.event_queue._reader.fileno()],
                [],
                [],
                self.select_timeout
            )
        except SelectError as e:
            errno_, message = e.args
            if errno_ == errno.EINTR:
                # Interrupted by e.g. SIGHUP. Just stop.
                return
            else:
                raise

        if len(fds) > 0:
            for fd in fds:
                if fd == self.listener._listener._socket.fileno():
                    if self.shutdown:
                        # during shutdown we don't handle incoming
                        # message anymore
                        continue
                    self.handle_listener_message()
                elif fd == self.event_queue._reader.fileno():
                    self.handle_event_queue_message()

        if self.last_schedule < (time.time() - 1):
            self.schedule()
            self.last_schedule = time.time()

        if self.last_vacuum < (time.time() - 3600):
            self.task_list.engine.vacuum()
            self.last_vacuum = time.time()

    def setup_task_list(self):
        # Instanciate TaskList
        self.task_list = TaskList(self.task_list_engine)
        # Bootstrap storage
        self.task_list.engine.bootstrap()
        # Reset task status
        self.task_list.recover()

    def schedule(self):
        now = datetime.utcnow()

        self.task_list.purge(
            (TASK_STATUS_DONE | TASK_STATUS_FAILED | TASK_STATUS_ABORTED |
             TASK_STATUS_CANCELED),
            now
        )

        if self.shutdown:
            return

        to_do = self.task_list.list_to_do(TASK_STATUS_DEFAULT, now)

        for task in to_do:
            task.status = TASK_STATUS_SCHEDULED

            logger.debug("Pushing task %s to the worker queue.", task.id)

            try:
                self.task_list.update(
                    id=task.id,
                    status=task.status
                )
            except StorageEngineError as e:
                logger.error(str(e))
            else:
                self.task_queue.put(task, False)

        to_redo = self.task_list.list_to_do(
            (TASK_STATUS_DONE | TASK_STATUS_FAILED | TASK_STATUS_ABORTED),
            now,
            redo=True
        )

        for task in to_redo:
            task.status = TASK_STATUS_SCHEDULED
            task.start_datetime = now
            task.stop_datetime = None
            task.output = ''

            logger.debug("Pushing task %s to the worker queue.", task.id)

            try:
                self.task_list.update(
                    id=task.id,
                    status=task.status,
                    start_datetime=task.start_datetime,
                    stop_datetime=task.stop_datetime,
                    output=task.output,
                )
            except StorageEngineError as e:
                logger.error(str(e))
            else:
                self.task_queue.put(task, False)

    def handle_message(self, message):
        if message.type == MSG_TYPE_TASK_NEW:
            # New task
            try:
                task_id = self.task_list.push(message.content)
                return Message(MSG_TYPE_RESP, {'id': task_id})
            except KeyError:
                return Message(MSG_TYPE_ERROR,
                               {'error': 'Task id already exists'})
            except StorageEngineError as e:
                logger.error(str(e))
                return Message(MSG_TYPE_ERROR, {'error': str(e)})

        elif message.type == MSG_TYPE_TASK_STATUS:
            # task status update
            status = message.content['status']
            # special case when task's status is TASK_STATUS_CANCELD, we dont'
            # want to change it's state.
            try:
                t = self.task_list.get(message.content['task_id'])
                if t.status & TASK_STATUS_CANCELED:
                    status = t.status

                self.task_list.update(
                    t.id,
                    status=status,
                    output=message.content.get('output', None),
                    stop_datetime=message.content.get('stop_datetime', None),
                )
            except StorageEngineError as e:
                logger.error(str(e))
                return Message(MSG_TYPE_ERROR, {'error': str(e)})
            else:
                return Message(MSG_TYPE_RESP, {'id': t.id})

        elif message.type == MSG_TYPE_TASK_LIST:
            # task list
            try:
                return list(self.task_list.list())
            except StorageEngineError as e:
                logger.error(str(e))
                return Message(MSG_TYPE_ERROR, {'error': str(e)})

        elif message.type == MSG_TYPE_TASK_ABORT:
            # task abortation
            t = Task(id=message.content['task_id'],
                     status=TASK_STATUS_ABORT)
            self.task_queue.put(t)

        elif message.type == MSG_TYPE_TASK_CANCEL:
            # task cancellation
            # first, we need to change its status and stop_datetime
            try:
                self.task_list.update(
                    message.content['task_id'],
                    status=TASK_STATUS_CANCELED,
                    stop_datetime=datetime.utcnow(),
                )
            except StorageEngineError as e:
                logger.error(str(e))
            else:
                # send the cancelation order to WP
                t = Task(id=message.content['task_id'],
                         status=TASK_STATUS_CANCELED)
                self.task_queue.put(t)
        elif message.type == MSG_TYPE_CONTEXT:
            # context update
            if type(message.content) == dict:
                for k, v in message.content.items():
                    self.set_context(k, v)
                return Message(MSG_TYPE_RESP, self.get_context())
            else:
                return Message(MSG_TYPE_ERROR, 'Unvalid type')


class SchedulerService(Service):
    # Adapter from taskmanager.Scheduler to Service

    def __init__(self, task_queue, event_queue, **kw):
        super(SchedulerService, self).__init__(**kw)
        self.task_queue = task_queue
        self.event_queue = event_queue
        self.scheduler = None
        self.task_list_engine = None

    def apply_config(self):
        # Setup scheduler as soon as configuration is loaded, before
        # plugins, so that tasklist is created before plugins.
        if not self.scheduler:
            self.scheduler = Scheduler(
                address=os.path.join(
                    self.app.config.temboard.home, '.tm.socket'),
                authkey=None)
            self.scheduler.task_queue = self.task_queue
            self.scheduler.event_queue = self.event_queue
            self.scheduler.task_list_engine = self.task_list_engine
            self.scheduler.setup_task_list()

    def setup(self):
        if os.path.exists(self.scheduler.address):
            os.unlink(self.scheduler.address)

        self.scheduler.setup()

    def serve1(self):
        self.scheduler.serve1()

    def add(self, workerset):
        if not self.is_my_process:
            return

        for task in workerset.list_tasks():
            try:
                task_from_db = self.scheduler.task_list.get(task.id)

                if task_from_db:
                    # If we've found the task in the DB, we'd keep its
                    # stop_datetime and status before overwriting it because
                    # we do not want this task to be re scheduled if it's not
                    # necessary.
                    task.stop_datetime = task_from_db.stop_datetime
                    task.status = task_from_db.status

                    self.scheduler.task_list.rm(task.id)
                    logger.debug("Overwriting task %s.", task.id)

                self.scheduler.task_list.push(task)
            except StorageEngineError as e:
                logger.error(str(e))

    def remove(self, workerset):
        if not self.is_my_process:
            return

        for task in workerset.list_tasks():
            try:
                self.scheduler.task_list.rm(task.id)
            except StorageEngineError as e:
                logger.error(str(e))

    def schedule_task(
            self, worker_name, id=None, options=None, start=None,
            redo_interval=None, expire=3600):
        message = Message(MSG_TYPE_TASK_NEW, Task(
            id=id,
            worker_name=worker_name,
            options=options,
            start_datetime=start or datetime.utcnow(),
            redo_interval=redo_interval,
            expire=expire,
        ))

        conn = Client(
            ensure_str(self.scheduler.address), self.scheduler.authkey)
        conn.send(message)
        res = conn.recv()
        conn.close()
        return res

    def can_schedule(self):
        return os.path.exists(self.scheduler.address)


class WorkerPool(object):
    trace = False

    def __init__(self, task_queue, event_queue, setproctitle=None):
        self.thread = None
        self.task_queue = task_queue
        self.event_queue = event_queue
        self.workers = {}
        self.setproctitle = setproctitle
        self.perf = None

    def _abort_job(self, task_id):
        for workername in self.workers:
            for job in self.workers[workername]['pool']:
                if job['id'] == task_id:
                    logger.debug("Process pid=%s is going to be killed"
                                 % job['process'])
                    job['process'].terminate()
                    return True
        return False

    def _rm_task_worker_queue(self, task_id):
        for workername in self.workers:
            for t in self.workers[workername]['queue']:
                if t.id == task_id:
                    self.workers[workername]['queue'].remove(t)
                    logger.debug("Task %s removed from queue" % t.id)
                    return True
        return False

    def setup(self):
        if self.perf:
            self.perf['fork'] = 0

    def add(self, worker):
        if worker['name'] in self.workers:
            raise Exception("Worker %s already registered." % worker['name'])

        self.workers[worker['name']] = {
            'queue': deque(),
            'pool_size': worker['pool_size'],
            'module': worker['module'],
            'function': worker['function'],
            'pool': []
        }

    def serve1(self):
        # check running jobs state
        self.check_jobs()
        # start new jobs
        self.start_jobs()

        try:
            t = self.task_queue.get(timeout=0.1)
        except Empty:
            return

        if t.status & TASK_STATUS_SCHEDULED:
            logger.debug("Got task %s for worker '%s' queue"
                         % (t.id, t.worker_name))
            self.workers[t.worker_name]['queue'].appendleft(t)
            # Update task status
            self.event_queue.put(
                Message(
                    MSG_TYPE_TASK_STATUS,
                    {
                        'task_id': t.id,
                        'status': TASK_STATUS_QUEUED,
                    }
                )
            )
        if t.status & TASK_STATUS_ABORT:
            self._abort_job(t.id)
        if t.status & TASK_STATUS_CANCELED:
            # Task cancellation includes 2 things:
            # - remove the task from workers queue if present (job not
            # yet running)
            # - abort running job executing the task if any

            # Looking up into workers jobs first, there is more chance
            # to find the task here.
            if not self._abort_job(t.id):
                # If not aborted, task has been queued
                self._rm_task_worker_queue(t.id)

    def exec_worker(self, module, function, out, *args, **kws):
        # Function wrapper around worker function
        try:
            # Reset signal handlers.
            signal.signal(signal.SIGABRT, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            fun = getattr(sys.modules[module], function)

            modfun = "%s.%s" % (module, fun.__name__)
            logger.debug("Starting new job for %s", modfun)
            if self.setproctitle:
                self.setproctitle('task %s' % (modfun))
            perf = PerfCounters.setup(service='task', task=modfun)
            if perf:
                perf.schedule()

            res = fun(*args, **kws)
            # Put function result into output queue as a Message
            out.put(Message(MSG_TYPE_RESP, res))
        except UserError as e:
            logger.critical("%s", e)
        except Exception as e:
            e = Exception("%s: %s" % (type(e), e))
            out.put(Message(MSG_TYPE_ERROR, e))
            logger.exception(e)
        except KeyboardInterrupt:
            logger.error("KeyboardInterrupt")
        if perf:
            perf.run()

    def start_jobs(self):
        # Execute Tasks
        for name, worker in self.workers.items():
            while len(self.workers[name]['pool']) < worker['pool_size']:
                try:
                    t = worker['queue'].pop()
                    # Queue used to get worker function return
                    out = Queue()
                    p = Process(
                            target=self.exec_worker,
                            args=(worker['module'], worker['function'], out),
                            kwargs=t.options,
                        )
                    p.start()

                    if self.perf:
                        self.perf['fork'] += 1

                    self.workers[name]['pool'].append(
                            {'id': t.id, 'process': p, 'out': out}
                    )
                    # Update task status
                    self.event_queue.put(
                        Message(
                            MSG_TYPE_TASK_STATUS,
                            {
                                'task_id': t.id,
                                'status': TASK_STATUS_DOING,
                            }
                        )
                    )
                except IndexError:
                    break

    def check_jobs(self):
        # Check jobs process state for each worker
        for name, worker in self.workers.items():
            for job in worker['pool']:
                if not job['process'].is_alive():
                    # Dead process case
                    logger.debug("Job %s terminated.", job['id'])
                    try:
                        # Fetch the message from job's output queue
                        message_out = job['out'].get(False)
                    except Empty:
                        message_out = None
                    if self.trace:
                        logger.debug("Job output : %s" % message_out)
                    # Close job's output queue
                    job['out'].close()
                    # join the process
                    job['process'].join()

                    # Let's build the message we'll have to send to scheduler
                    # for the update of task's status.
                    task_stop_dt = datetime.utcnow()
                    if job['process'].exitcode == 0:
                        if message_out and \
                                message_out.type[0] == MSG_TYPE_RESP:
                            task_status = TASK_STATUS_DONE
                        else:
                            # when an exception is raised from the worker
                            # function
                            task_status = TASK_STATUS_FAILED
                    elif job['process'].exitcode < 0:
                        # process killed
                        task_status = TASK_STATUS_ABORTED
                    else:
                        task_status = TASK_STATUS_FAILED
                    task_output = None
                    if message_out:
                        task_output = message_out.content

                    # Update task status
                    self.event_queue.put(
                        Message(
                            MSG_TYPE_TASK_STATUS,
                            {
                                'task_id': job['id'],
                                'status': task_status,
                                'output': task_output,
                                'stop_datetime': task_stop_dt
                            }
                        )
                    )

                    # Finally, remove the job from the pool
                    self.workers[name]['pool'].remove(job)

    def abort_jobs(self):
        # abort all running jobs
        for name, worker in self.workers.items():
            for job in worker['pool']:
                process = job.get('process')
                if process.is_alive():
                    process.terminate()
                    logger.debug("Job %s has been terminated" % job['id'])
                    # Close job's output queue
                    job['out'].close()
                    # join the process
                    process.join()
                    self.workers[name]['pool'].remove(job)


class WorkerSet(list):
    def register(self, pool_size=1):
        def register(f):
            def defer(app, **kw):
                logger.debug("Scheduling %s.", f.__name__)
                return app.scheduler.schedule_task(
                    f.__name__, options=kw, expire=0)
            f.defer = defer

            f._tm_worker = make_worker_definition(f, pool_size)
            if f not in self:
                self.append(f)
            return f
        return register

    def schedule(self, id=None, redo_interval=None, **options):
        def register(f):
            if f not in self:
                self.append(f)
            f._tm_task = Task(
                id=id,
                options=options,
                redo_interval=redo_interval,
                worker_name=f.__name__,
            )
            return f
        return register

    def list_tasks(self):
        for function in self:
            task = getattr(function, '_tm_task', None)
            if task:
                yield task


class WorkerPoolService(Service):
    # Adapter from taskmanager.WorkerPool to Service

    def __init__(self, task_queue, event_queue, **kw):
        super(WorkerPoolService, self).__init__(**kw)
        self.worker_pool = WorkerPool(
            task_queue, event_queue, self.setproctitle)

    def setup(self):
        self.worker_pool.perf = self.perf
        self.worker_pool.setup()

    def serve1(self):
        try:
            self.worker_pool.serve1()
        except Exception:
            logger.exception("Unhandled error in worker:")
            logger.error("Not stopping worker process.")

    def create_task_function_app_wrapper(self, function):
        @functools.wraps(function)
        def wrapper(*a, **kw):
            return function(self.app, *a, **kw)
        wrapper._tm_function = function
        return wrapper

    def add(self, workerset):
        if not self.is_my_process:
            return

        for function in workerset:
            conf = function._tm_worker
            wrapper = self.create_task_function_app_wrapper(function)

            # Inject wrapper in module so taskmanager will find it.
            mod = sys.modules[conf['module']]
            wrapper_name = '_tm_wrapper_' + function.__name__
            setattr(mod, wrapper_name, wrapper)
            conf['function'] = wrapper_name

            # Add to current workers
            logger.debug("Register worker %s", conf['name'])
            self.worker_pool.add(conf)

    def remove(self, workerset):
        if not self.is_my_process:
            return

        for function in workerset:
            conf = function._tm_worker
            logger.debug("Disable worker %s", conf['name'])
            self.worker_pool.workers.pop(conf['name'], None)

    def sigterm_handler(self, *a):
        logger.info("Aborting jobs on SIGTERM.")
        self.worker_pool.abort_jobs()
        super(WorkerPoolService, self).sigterm_handler(*a)


class FlushTasksMixin(object):
    # Shared code for flush-task command

    def define_arguments(self, parser):
        parser.add_argument(
            "--force",
            action='store_true', default=False,
            help="Force overwriting existing files.",
        )

    def main(self, args):
        if self.app.scheduler.can_schedule():
            if args.force:
                logger.warning(
                    "Scheduler socket exists. Is temBoard scheduler running?")
            else:
                logger.error("Scheduler socket exists. Use --force to bypass.")
                raise UserError("You must stop temBoard before flushing tasks")

        count = self.app.scheduler.task_list_engine.flush()
        logger.info("Flushed %s tasks.", count)
        return 0


class RunTaskMixin(object):
    # Shared code to execute a single task, for runtask commands.
    #
    # To combines with toolkit.app.SubCommand

    def define_arguments(self, parser):
        parser.description = dedent("""\

        Run a task foreground. Some tasks won't work foreground because they
        requires task manager processes.

        Use this only for testing, debugging and development.

        Note that our home-made background task implementation uses a different
        semantic that state of the art background task implementation:

        - a task function is called a worker
        - a worker process is called workerpool
        - a message is called a task
        - the message broker is called taskmanager

        """)

        parser.add_argument(
            'worker_name',
            metavar='WORKER',
            help=(
                "Global name of the worker function name to execute."
                " Use ? to list available workers."),
        )

        parser.add_argument(
            'worker_args', nargs='*',
            metavar='ARG',
            default=[],
            help="Worker arguments as Python literals.",
        )

    def iter_workers(self):
        for name, config in self.app.worker_pool.worker_pool.workers.items():
            mod = sys.modules[config['module']]
            fn = getattr(mod, config['function'])
            yield fn

    def compute_worker_args(self, workers, args):
        needles = (args.worker_name, args.worker_name + '_worker')
        for worker in workers:
            if worker.__name__ in needles:
                break
        else:
            raise UserError("Unknown worker %s." % args.worker_name)

        worker_args = []
        for arg in args.worker_args:
            try:
                arg = literal_eval(arg)
            except Exception:
                logger.debug("Unknown literal %s, using as raw string.", arg)
            worker_args.append(arg)

        return worker, worker_args

    def print_workers(self, workers):
        for name in sorted(fn.__name__ for fn in workers):
            print(name)
