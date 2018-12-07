import time

# Label returned when the data is not available
NotAvailableLabel = 'N/A'


def bytes2human(num):
    """
    Convert a size into a human readable format.
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    nume = ''
    if num < 0:
        num = num * -1
        nume = '-'
    for pos, sym in enumerate(symbols):
        prefix[sym] = 1 << (pos + 1) * 10
    for sym in reversed(symbols):
        if num >= prefix[sym]:
            value = "%.2f" % float(float(num) / float(prefix[sym]))
            return "%s%s%s" % (nume, value, sym)
    return "%s%.2fB" % (nume, num)


def memory_total_size():
    """
    Get the total amount of memory from /proc/meminfo.
    """
    try:
        with open('/proc/meminfo', 'r') as fd:
            for line in fd.readlines():
                items = line.split()
                if len(items) > 0:
                    if items[0][:-1] == 'MemTotal':
                        mem_total = int(items[1])
                        if items[2] == 'kB':
                            return mem_total * 1024
                        else:
                            return mem_total
            fd.close()
    except Exception:
        pass
    return


class Process(object):
    """
    Process class aimed to retreive process informations such CPU usage, memory
    usage, waiting in uninterruptible disk sleep (IO wait), disk read and write
    rates.
    """

    def __init__(self, pid, mem_total, page_size):
        """
        Constructor.
        """
        self.pid = pid
        self.iow = False
        self.rss = 0
        self.cpu_time = 0
        self.cpu_time_capture = 0
        self.page_size = page_size
        self.mem_total = mem_total
        self.read_bytes = 0
        self.write_bytes = 0
        self.io_capture = 0
        if self.pid:
            self.__init_stat()
            self.__parse_proc_io()

    def __parse_proc_stat(self,):
        """
        /proc/<pid>/stat parser for getting CPU times, RSS and IOW.
        """
        iow = 'N'
        cpu_time = 0
        cpu_time_capture = 0
        rss = 0
        try:
            with open('/proc/%s/stat' % (self.pid), 'r') as fd:
                lines = fd.read()
                infos = lines[:-1].split()
                # IO wait
                if infos[2] == 'D':
                    iow = 'Y'
                # RSS
                rss = infos[23]
                # CPU time
                cpu_time = (float(infos[13]) + float(infos[14]) +
                            float(infos[15]) + float(infos[16]))
                cpu_time_capture = time.time()
            return (iow, rss, cpu_time, cpu_time_capture)
        except Exception:
            # Case when /proc/<pid>/stat can be read/parsed
            return (NotAvailableLabel, None, None, None)

    def __parse_proc_io(self,):
        """
        /proc/<pid>/io parser for getting read_bytes and write_bytes.
        """
        read_bytes = 0
        write_bytes = 0
        io_capture = 0
        try:
            with open('/proc/%s/io' % (self.pid), 'r') as fd:
                io_capture = time.time()
                for line in fd.readlines():
                    infos = line.split()
                    if infos[0][:-1] == 'read_bytes':
                        read_bytes = int(infos[1])
                    if infos[0][:-1] == 'write_bytes':
                        write_bytes = int(infos[1])
            return (read_bytes, write_bytes, io_capture)
        except Exception:
            # Case when /proc/<pid>/io can be read/parsed
            return (None, None, None)

    def __init_stat(self, ):
        (self.iow, self.rss, self.cpu_time,
         self.cpu_time_capture) = self.__parse_proc_stat()

        (self.read_bytes, self.write_bytes,
         self.io_capture) = self.__parse_proc_io()

    def cpu_usage(self, ):
        """
        Calculates and returns CPU usage based on CPU time
        """
        (_, _, new_cpu_time, new_cpu_time_capture) = self.__parse_proc_stat()
        if new_cpu_time is not None and new_cpu_time_capture is not None:
            cpu_usage = float("%.2f" % (round(
                float(
                    float(new_cpu_time - self.cpu_time) /
                    float(new_cpu_time_capture - self.cpu_time_capture)), 2)))
            self.cpu_time = new_cpu_time
            self.cpu_time_capture = new_cpu_time_capture
            return cpu_usage
        else:
            return NotAvailableLabel

    def mem_usage(self, new_capture=False):
        """
        Calculates and returns memory usage.
        """
        if new_capture is True:
            self.__init_stat()
        if self.rss is not None and self.mem_total is not None:
            return float("%.2f" % (round(
                float(float(self.rss) * self.page_size) /
                float(self.mem_total) * 100, 2)))
        else:
            return NotAvailableLabel

    def io_usage(self, ):
        """
        Calculates and returns I/O disk rates.
        """
        (new_read_bytes, new_write_bytes,
         new_io_capture) = self.__parse_proc_io()
        if new_read_bytes is not None and new_write_bytes is not None \
           and new_io_capture is not None:
            read_rate = float("%.2f" % (round(
                float(
                    float(new_read_bytes - self.read_bytes) /
                    float(new_io_capture - self.io_capture)), 2)))
            write_rate = float("%.2f" % (round(
                float(
                    float(new_write_bytes - self.write_bytes) /
                    float(new_io_capture - self.io_capture)), 2)))
            self.read_bytes = new_read_bytes
            self.write_bytes = new_write_bytes
            self.io_capture = new_io_capture
            return (bytes2human(read_rate), bytes2human(write_rate))
        else:
            return (NotAvailableLabel, NotAvailableLabel)
