# Simple live performance counters in logfmt.

import logging
import os
import signal


logger = logging.getLogger(__name__)
SC_CLK_TCK = os.sysconf('SC_CLK_TCK')


class PerfCounters(dict):
    @classmethod
    def setup(cls, **defaults):
        if 'DEBUG' in os.environ:
            os.environ.setdefault('PERF', '15')
        if 'PERF' not in os.environ:
            return
        return cls(**defaults)

    def __init__(self, **defaults):
        defaults = dict(
            io_rchar=0,
            io_wchar=0,
            stime=0,
            utime=0,
            vsize=0,
            pid=os.getpid(),
            load1=0,
            load5=0,
            load15=0,
            **defaults
        )
        super(PerfCounters, self).__init__(**defaults)

        try:
            self.delay = int(os.environ['PERF'])
        except (KeyError, ValueError):
            self.delay = 60

        self.delay = max(15, self.delay)
        logger.debug("Scheduling perf counters each %s seconds.", self.delay)

    def __str__(self):
        return ' '.join([
            '%s=%s' % i
            for i in sorted(self.items())
        ])

    def run(self):
        try:
            self.snapshot()
        except Exception as e:
            logger.error("Failed to read performances metrics: %s", e)
            return
        logger.debug("%s", self)
        self.schedule()

    def sigalrm_handler(self, *a):
        self.run()

    def schedule(self):
        signal.alarm(self.delay)

    def snapshot(self):
        # I/O
        needles = ['rchar', 'wchar']
        with open('/proc/self/io') as fo:
            for k, v in parse(fo):
                if k not in needles:
                    continue
                self['io_%s' % k] = v
                if not needles:
                    break

        # PROCESS
        with open('/proc/self/stat') as fo:
            stat = fo.read()

        # Fields are documented in proc(5).
        fields = stat.split()

        utime = int(fields[13]) / SC_CLK_TCK
        self['utime'] = utime

        stime = int(fields[14]) / SC_CLK_TCK
        self['stime'] = stime

        vsize = int(fields[22])
        self['vsize'] = vsize

        # GLOBAL LOAD AVG
        with open('/proc/loadavg') as fo:
            loadavg = fo.read()
        self['load1'], self['load5'], self['load15'], _ = loadavg.split(' ', 3)


def parse(lines):
    for line in lines:
        try:
            k, v = line.split(': ')
        except ValueError:
            continue
        yield k, v.strip()
