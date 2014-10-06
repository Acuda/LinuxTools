import psutil
from ConsoleColors import cc
import time

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
            return '%s %s %s' % (self.isRunning, self.name, self.cmdline)
        else:
            return 'FAKEROOT'

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

            rootProcDto.childDtoList.append(childProcDto)
            childProcDto.rootDto = rootProcDto

def printChilds(procDto, indent=1, indentstr='    '):
    for childDto in procDto.childDtoList:
        if childDto.proc.is_running():
            if time.time() - childDto.create_time <= 10:
                color = cc.c.green
            else:
                color = cc.c.blue
        else:
            color = cc.c.red

        print cc.w('#%s%s'% (indentstr * indent, childDto), color=color, mode=cc.m.fg)
        printChilds(childDto, indent+1)

if __name__ == '__main__':


    pw = ProcWatch()

    isFirstrun = True
    while isFirstrun or raw_input('refresh?') != 'q':
        isFirstrun = False
        pw.acquireProcessList()

        printChilds(pw.fakeRoot)
        #printChilds(pw.getNewestProc(20916))










    #pprint(pw.procData)
    #print 'length', len(pw.procData)
    #raw_input('waiting....')
    #pw.acquireProcessList()
    #pprint(pw.procData)

    #for pid in pw.procData.values():
    #    for tme in pid.values():
    #        print tme.pid, tme.name, tme.cmdline

    #print 'length', len(pw.procData)

