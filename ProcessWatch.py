import psutil
from pprint import pprint

class ProcessWatch(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    pl = psutil.get_process_list()
    for p in pl:
        if p.name == 'java':
            print p.name, p.cmdline
