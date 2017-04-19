import sys
import time
import json
import fcntl
from multiprocessing import Process, Queue, Lock
from multiprocessing.sharedctypes import Array
from ctypes import Structure, c_char, c_int, c_wchar, c_short

# List of workers, filled by the decorator add_worker()
__WORKERS = []
# List of task scheduler, filled by the decorator add_scheduler()
__SCHEDULERS = []

# Worker name size
T_WORKERNAME_SIZE = 32
# Task id size
T_TASKID_SIZE = 32
# Size of task parameters passed to the worker
T_PARAMETERS_SIZE = 2048
# Worker's output buffer size
T_OUTPUT_SIZE = 4096

# Task states
S_TASK_TODO = 1
S_TASK_DOING = 2
S_TASK_DONE = 3
S_TASK_FAILED = 4
S_TASK_SUSPENDED = 5


def serialize_task_parameters(parameters):
    """
    Serialization function used to store Task parameters dict
    into Tasks shared array (ctype).
    """
    return json.dumps(parameters).decode('utf-8')


def unserialize_task_parameters(s_parameters):
    """
    Unserialization function for Task parameters.
    """
    return json.loads(s_parameters)


def add_worker(name, pool_size):
    """
    Decorator for adding new workers.
    """

    def func_wrapper(function):
        global __WORKERS
        __WORKERS.append({
            'name': name,
            'pool_size': pool_size,
            'module': function.__module__,
            'function': function.__name__
        })
        return function

    return func_wrapper


def get_worker_pool_size(worker_name):
    """
    Returns the worker pool size.
    """
    global __WORKERS
    for w in __WORKERS:
        if w['name'] == worker_name:
            return w['pool_size']
    return 0


def add_scheduler(name):
    """
    Decorator for adding Task scheduling functions.
    """

    def func_wrapper(function):
        global __SCHEDULERS
        __SCHEDULERS.append({
            'name': name,
            'module': function.__module__,
            'function': function.__name__
        })
        return function

    return func_wrapper


def get_all_scheduler_func():
    """
    Returns Task scheduling functions from the global list.
    """
    return __SCHEDULERS


def get_all_worker_func():
    """
    Returns Worker functions from the global list.
    """
    return __WORKERS


class Task(Structure):
    """
    Task structure (ctypes).
    """
    _fields_ = [
        # Worker name in charge to handle this task
        ('worker_name', c_char * T_WORKERNAME_SIZE),
        # Task identifier
        ('taskid', c_char * T_TASKID_SIZE),
        # Parameters passed to the worker
        ('parameters', c_wchar * T_PARAMETERS_SIZE),
        # Task state
        ('state', c_short),
        # Repeat task after 'repeat' seconds.
        ('repeat', c_int),
        # Worker output
        ('output', c_wchar * T_OUTPUT_SIZE),
        # Creation timestamp
        ('creation_time', c_int),
        # Last update timestamp
        ('update_time', c_int),
        # Due timestamp
        ('due_time', c_int)
    ]

    def __repr__(self):
        return json.dumps({
            'worker_name':
            self.worker_name,
            'taskid':
            self.taskid,
            'parameters':
            unserialize_task_parameters(self.parameters),
            'state':
            self.state,
            'repeat':
            self.repeat,
            'output':
            self.output,
            'creation_time':
            self.creation_time,
            'update_time':
            self.update_time,
            'due_time':
            self.due_time
        })


class TaskList(object):
    """
    Todo Task list implementing a ctype shared (multiprocess) array.
    Each new Task must be added using add() method before being handled by the
    worker.
    """

    def __init__(self, filepath=None, size=100):
        # Lock handler
        self.lock = Lock()
        # Maximum number of task
        self.size = size
        # Shared Array of Task
        self.tasks = Array(Task, self.size, lock=self.lock)
        # File path, if None, task_list is not sync'ed to file
        self.filepath = None

    def add(self, task):
        """
        Add a new task
        """
        # We need to verify if there's no other Task with the same
        # couple worker_name/taskid
        for i in range(0, self.size):
            if self.tasks[i].taskid == task.taskid \
               and self.tasks[i].worker_name == task.worker_name:
                raise Exception('Task {1}/{2} already exists.'.format(
                    task.worker_name, task.taskid))

        # Let's found a free slot in the Task array where the new Task
        # will be inserted.
        for i in range(0, self.size):
            if self.tasks[i].taskid == b'':
                # Copy the task in the free slot.
                self.tasks[i] = task
                return
        raise Exception('Task list full')

    def get(self, worker_name, taskid):
        """
        Return a Task from the shared array, based on worker_name and taskid
        """
        # Loop through each Task and compair worker_name/taskid
        for i in range(0, self.size):
            if self.tasks[i].taskid == taskid \
               and self.tasks[i].worker_name == worker_name:
                return self.tasks[i]
        raise Exception('Task not found')

    def update(self, task):
        """
        Update a Task in the shared array.
        """
        # Loop through each Task to find the one we are looking for.
        for i in range(0, self.size):
            if self.tasks[i].taskid == task.taskid \
               and self.tasks[i].worker_name == task.worker_name:
                self.tasks[i] = task
                return
        raise Exception('Task not found')

    def delete(self, worker_name, taskid):
        """
        Remove a Task from the shared array
        """
        # Loop through each Task to find the one we are looking for.
        for i in range(0, self.size):
            if self.tasks[i].taskid == taskid \
               and self.tasks[i].worker_name == worker_name:
                # To remove a existing Task, we replace it with an empty one
                self.tasks[i] = Task()
                return
        raise Exception('Task not found')

    def save(self):
        """
        Save Task list content into the on-disk image file, file path is
        defined by self.filepath.
        """
        if not self.filepath:
            return
        with open(self.filepath, 'w') as fd:
            # Hold an exclusive lock on the file
            fcntl.flock(fd, fcntl.LOCK_EX)
            for i in range(0, self.size):
                if self.tasks[i].worker_name != b'':
                    fd.write('{0}\n'.format(str(self.tasks[i])))
            # Unhold fd lock
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

    def load_at_boot(self):
        """
        Loads Task list from the on-disk image file. This method should be
        called only once: during boot time. During Task list recovering, we can
        overwrite the Task state in one case: when the state is set to
        S_TASK_DOING, meaning the main process have been stopped while a worker
        was still working on that Task. In this cas, we overwrite Task state to
        S_TASK_FAILED, thus, we can re-process this Task later if needed.
        """
        # If filepath is not set, nothing to do.
        if not self.filepath:
            return

        with open(self.filepath, 'r') as fd:
            # Hold a shared lock on the file
            fcntl.flock(fd, fcntl.LOCK_SH)
            for line in fd.readlines():
                # Unserialize
                d_task = json.loads(line)
                # Change Task state to S_TASK_FAILED if we meet a uncomplete
                # Task.
                if d_task['state'] == S_TASK_DOING:
                    d_task['state'] = S_TASK_FAILED
                # Create a new Task
                task = Task(
                    worker_name=d_task['worker_name'],
                    taskid=d_task['taskid'],
                    parameters=serialize_task_parameters(d_task['parameters']),
                    state=d_task['state'],
                    repeat=d_task['repeat'],
                    creation_time=d_task['creation_time'],
                    update_time=d_task['update_time'],
                    due_time=d_task['due_time'])
                # Add Task to the shared Array
                self.add(task)

            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()


class TaskManager(object):
    """
    TaskManager is in charge of:
     * scheduling a list of Task according to their properties
     * starting a worker when a Task need to be processed immediately
    """

    def __init__(self):
        """
        Constructor
        """
        # List of running jobs
        self.running_jobs = []
        # Task Scheduler Process
        self.scheduler = None
        # Main Process
        self.process = None
        # Task Queue used to run immediate jobs
        self.queue = Queue()
        # Task List
        self.task_list = TaskList()
        # Logger
        self.logger = None

    def set_logger(self, logger):
        """
        Change the logger
        """
        self.logger = logger

    def exec_scheduler_func(self, name):
        """
        Returns a scheduling function based on its name.
        """
        for s in get_all_scheduler_func():
            if s['name'] == name:
                return getattr(sys.modules[s['module']], s['function'])
        raise Exception('Scheduler {name} not found.'.format(name=name))

    def exec_worker_func(self, name):
        """
        Returns a worker function based on its name.
        """
        for w in get_all_worker_func():
            if w['name'] == name:
                return getattr(sys.modules[w['module']], w['function'])
        raise Exception('Worker {name} not found.'.format(name=name))

    def count_running_worker(self, worker_name):
        """
        Returns the number of running jobs, based on worker_name
        """
        c = 0
        for w in self.running_jobs:
            if w['task'].worker_name == worker_name:
                c += 1
        return c

    def run_scheduler(self, parameters):
        """
        Runs scheduling functions once and maintains the Task list.
        When Task state is set to S_TASK_TODO, puts this Task in the
        "ready-to-run" job queue.
        """
        tl_loaded = False
        if self.task_list.filepath:
            try:
                self.task_list.load_at_boot()
                tl_loaded = True
            except Exception as e:
                self.logger.error(e)
        if not tl_loaded:
            for s in get_all_scheduler_func():
                try:
                    # Execute each scheduling function
                    self.exec_scheduler_func(s['name'])(self.task_list,
                                                        parameters)
                except Exception as e:
                    self.logger.error(e)

        while True:
            # TaskList maintenance
            for task in self.task_list.tasks:
                if task.state in (S_TASK_DONE, S_TASK_FAILED) \
                   and task.repeat > 0 \
                   and task.update_time + task.repeat <= int(time.time()):
                    # Case when a Task need be repeated.
                    task.state = S_TASK_TODO

                if task.state in (S_TASK_DONE, S_TASK_FAILED) \
                   and task.due_time > 0 \
                   and task.due_time <= int(time.time()):
                    # Case when the due time is reached.
                    task.state = S_TASK_TODO

                # Check Task state is S_TASK_TODO
                if task.state == S_TASK_TODO:
                    # Task can be scheduled immediately
                    # Put it in the Task queue
                    self.queue.put(task)
                    # Flag it as DOING
                    task.state = S_TASK_DOING
                    # Update update_time with current timestamp
                    task.update_time = int(time.time())
                    # Update the Task
                    try:
                        self.task_list.update(task)
                        self.task_list.save()
                    except Exception as e:
                        self.logger.error(e)

            # Sleep for a while until the next iteration
            time.sleep(1)

    def start_worker(self, task):
        """
        Execute worker function.
        """
        self.exec_worker_func(task.worker_name)(task)

    def run(self):
        """
        Main process in charge of polling the job Queue every 0.5 second max,
        if it finds a new Task, it starts a new worker to handle this Task
        in a child process.
        """
        # Tunning jobs list init.
        self.running_jobs = []
        while True:
            try:
                # Get a new Task from the Queue with a 0.5s timeout.
                task = self.queue.get(True, 0.5)
            except Exception as e:
                pass
            else:
                try:
                    if get_worker_pool_size(
                            task.worker_name) > self.count_running_worker(
                                task.worker_name):
                        # If we got a new Task, let's start a new worker in a
                        # child process.
                        new_worker = Process(
                            target=self.start_worker, args=(task, ))
                        # Keep a track of the running jobs.
                        self.running_jobs.append({
                            'task': task,
                            'worker': new_worker
                        })
                        # Start the worker.
                        new_worker.start()
                        self.logger.info(
                            '[{wn}] New worker started with pid={pid}'.format(
                                wn=task.worker_name, pid=new_worker.pid))
                    else:
                        self.logger.info('[{wn}] Worker pool size full.'.
                                         format(wn=task.worker_name))
                        task.state = S_TASK_TODO
                        self.task_list.update(task)
                        self.task_list.save()
                except Exception as e:
                    self.logger.error(e)

            for running_job in self.running_jobs:
                # We need to loop through each running job and check if the
                # process is still alive.
                if not running_job['worker'].is_alive():
                    # Process is not alive.
                    self.logger.info(
                        '[{wn}] Worker job with pid={pid} done.'.format(
                            wn=running_job['task'].worker_name,
                            pid=running_job['worker'].pid))
                    # Join the process
                    running_job['worker'].join()
                    try:
                        # Get the Task from memory
                        task = self.task_list.get(
                            running_job['task'].worker_name,
                            running_job['task'].taskid)
                        if task.repeat > 0:
                            # Task must be rescheduled
                            if running_job['worker'].exitcode != 0:
                                task.state = S_TASK_FAILED
                            else:
                                task.state = S_TASK_DONE
                            task.update_time = int(time.time())
                            self.task_list.update(task)
                            self.task_list.save()
                        else:
                            # We remove it from the Task list
                            self.task_list.delete(task.worker_name,
                                                  task.taskid)
                            self.task_list.save()
                    except Exception as e:
                        self.logger.error(e)
                    # We remove the job from running_jobs list
                    self.running_jobs.remove(running_job)

    def start(self, parameters):
        """
        Start both scheduler and main processes.
        """
        self.scheduler = Process(
            target=self.run_scheduler, args=(parameters, ))
        self.scheduler.start()
        self.process = Process(target=self.run)
        self.process.start()
