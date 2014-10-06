import psutil
from ConsoleColors import cc
import time
import re

class ProcDto(object):
    def __init__(self, proc=None, isFakeRoot=False):
        self.procAttributes = ['pid', 'ppid', 'create_time', 'name', 'cmdline']

        self.rootDto = None
        self.childDtoList = list()

        self.isFakeRoot = isFakeRoot

        if not isFakeRoot:
            self.proc = proc
            self._requestAttributeData(proc)

    def _requestAttributeData(self, proc):
        for attr in self.procAttributes:
            setattr(self, attr, getattr(self.proc, attr))
        self.isRunning = proc.is_running()

    def __repr__(self):
        if not self.isFakeRoot:
            return '%d %d %s %s' % (self.pid, self.ppid, self.name, self.cmdline if len(self.cmdline) else '')
        else:
            return 'FAKEROOT'

    def __eq__(self, other):
        return self.pid == other.pid and \
               self.ppid == other.ppid and \
               self.create_time == other.create_time

class ProcWatch(object):
    def __init__(self):
        self.procData = dict()
        self.fakeRoot = ProcDto(isFakeRoot=True)
        self.newTime = 2

    def acquireProcessList(self):
        procList = psutil.process_iter()

        map(self._attachProc, procList)
        self._mapChilds()


    def _attachProc(self, proc):
        if isinstance(proc, list):
            if not len(proc):
                return
            map(self._attachProc, proc)
            return

        pidBoundDict = self.procData.get(proc.pid, dict())
        pidBoundDict[proc.create_time] = ProcDto(proc)
        self.procData.update({proc.pid: pidBoundDict})

    def getNewestProc(self, pid):
        if not pid in self.procData:
            return None

        if len(self.procData[pid]) == 1:
            return self.procData[pid].values()[0]
        else:
            raise NotImplementedError('need to find the newest child...')

    def _mapChilds(self):
        for pid in self.procData:
            childProcDto = self.getNewestProc(pid)
            rootProcDto = self.getNewestProc(childProcDto.ppid)

            if not rootProcDto:  # suppose we need an fakeRoot
                rootProcDto = self.fakeRoot

            if childProcDto not in rootProcDto.childDtoList:
                rootProcDto.childDtoList.append(childProcDto)
            childProcDto.rootDto = rootProcDto

    def isPidChildOfPid(self, cpid, rpid):
        cproc = self.getNewestProc(cpid)

        #print 'check if', cpid, 'is child of', rpid
        while True:

            if cproc.rootDto.isFakeRoot:
                return False

            if cproc.pid == rpid:
                return False
            if cproc.rootDto.pid == rpid:
                return True
            cproc = cproc.rootDto

    def findByRegEx(self, regex):
        foundPids = set()
        for pid, cpids in self.procData.items():
            for ctime, proc in cpids.items():
                procstr = proc.name + ' ' + ' '.join(proc.cmdline)
                result = re.findall(regex, procstr)
                if len(result):
                    foundPids.add(pid)
        return foundPids

class ProcWatchViz(object):
    def __init__(self):
        self.starttime = time.time()
        self.procWatch = ProcWatch()

    def doViz2(self):
        while True:
            print '\033[2J'
            self.procWatch.acquireProcessList()
            pids = self.procWatch.findByRegEx('sshd: jenkins \\[priv\\]')
            for pid in pids:
                self.printChilds(self.procWatch.getNewestProc(pid))

            for x in range(10):
                time.sleep(0.1)
                self.procWatch.acquireProcessList()




    def doViz(self):
        isFirstrun = True
        while isFirstrun or True:#raw_input('refresh?') != 'q':
            print '='*100
            print '\033[2J',
            isFirstrun = False
            self.procWatch.acquireProcessList()

            pidCache = list()
            for pid in self.procWatch.procData:
                proc = self.procWatch.getNewestProc(pid)
                if proc.create_time > self.starttime:
                    pidCache.append(pid)

            rootPids = set()
            for pid in pidCache:
                for rpid in pidCache:
                    if pid == rpid:
                        break
                    if self.procWatch.isPidChildOfPid(pid, rpid):
                        rootPids.add(rpid)

            for rpid in rootPids:
                self.printChilds(self.procWatch.getNewestProc(rpid))

    def printChilds(self, procDto, indent=0, indentstr='    '):
        if procDto.proc.is_running():
            if time.time() - procDto.create_time < 5:
                color = cc.c.green
            else:
                color = cc.c.blue
        else:
            color = cc.c.red

        print cc.w('%s%s'% (indentstr * indent, procDto if color != cc.c.red else procDto.name), color=color, mode=cc.m.fg)
        for childDto in procDto.childDtoList:
            self.printChilds(childDto, indent+1)

if __name__ == '__main__':
    pwv = ProcWatchViz()
    pwv.doViz2()
