import psutil
from ConsoleColors import cc
import time
import re
import operator
import atexit
import pickle

class ProcDto(object):
    def __init__(self, proc=None, isFakeRoot=False):
        self.procAttributes = ['pid', 'ppid', 'create_time', 'name', 'cmdline']

        self.rootDto = None
        self.childDtoList = list()

        self.isFakeRoot = isFakeRoot
        self.lastSeen = time.time()

        if not isFakeRoot:
            self.proc = proc
            self.pid = proc.pid
            self.ppid = proc.ppid
            self.create_time = proc.create_time
            self.name = proc.name
            self.cmdline = proc.cmdline

    def is_running(self):
        if self.proc.is_running():
            self.lastSeen = time.time()
        return self.proc.is_running()

    def _requestAttributeData(self, proc):
        if self.is_running():
            for attr in self.procAttributes:
                setattr(self, attr, getattr(self.proc, attr))

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

        procDto = ProcDto(proc)
        if procDto.create_time not in pidBoundDict:
            pidBoundDict[procDto.create_time] = procDto
            self.procData.update({proc.pid: pidBoundDict})
        else:
            pidBoundDict[procDto.create_time].is_running()

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

        atexit.register(self.saveStuff)

    def saveStuff(self):



        with open('procData.pickle', 'w') as f:
            print 'dump'
            pickle.dump(self.procWatch.procData, f, -1)
            f.flush()

        print 'jeeeeeep'

    def doViz2(self):
        while True:
            print '\033[2J'
            self.procWatch.acquireProcessList()
            #pids = self.procWatch.findByRegEx('update_chroot_tarballs\\.py')
            #pids = self.procWatch.findByRegEx('hudson[0-9]{10}')
            pids = self.procWatch.findByRegEx('sshd: jenkins \\[priv\\]')

            for pid in pids:
                self.printChilds(self.procWatch.getNewestProc(pid))

            for x in range(5):
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

    def printChilds(self, procDto, indent=0, indentstr='  '):


        if procDto.is_running():
            if time.time() - procDto.create_time < 1:
                color = cc.c.green
            else:
                color = cc.c.blue


            if procDto.proc.status == psutil.STATUS_ZOMBIE:
                try:
                    tmpstr = 'try killing zombie...'
                    tmpstr = cc.w(tmpstr, color=cc.c.black, mode=cc.m.hifg, decorator=cc.d.bold)
                    tmpstr = cc.w(tmpstr, color=cc.c.red, mode=cc.m.bg)
                    print tmpstr
                    procDto.proc.kill()
                except:
                    tmpstr = 'cant kill proc...'
                    tmpstr = cc.w(tmpstr, color=cc.c.black, mode=cc.m.hifg, decorator=cc.d.bold)
                    tmpstr = cc.w(tmpstr, color=cc.c.red, mode=cc.m.bg)
                    print tmpstr


            if procDto.name == 'pbuilder_calls.':
                color = cc.c.yellow
                print cc.w(procDto.proc.get_open_files(), color=cc.c.cyan, mode=cc.m.hifg)
                print cc.w(procDto.proc.get_connections(), color=cc.c.purple, mode=cc.m.hifg)
                #psutil.Process().get_connections()
        else:
            color = cc.c.red

            if time.time() - procDto.lastSeen > 7:
                return


        print cc.w('%s %s' % (indentstr * indent, procDto.pid), color=color, mode=cc.m.fg),
        print cc.w(procDto.name, color=color, mode=cc.m.hifg, decorator=cc.d.bold),
        print cc.w('(%s)'%procDto.proc.status if procDto.is_running() else 'dead', color=color, mode=cc.m.hifg, decorator=cc.d.underline),
        cmdl = ' '.join(procDto.cmdline).replace('\n', '\n' + indentstr * (indent+4))
        if len(cmdl) < 150:
            print cc.w('[%s]' % cmdl, color=color, mode=cc.m.fg)
        else:
            print cc.w('[%s' % cmdl[:150], color=color, mode=cc.m.fg),
            print cc.w('...', color=color, mode=cc.m.hifg, decorator=cc.d.bold),
            print cc.w(']', color=color, mode=cc.m.fg)

        procDto.childDtoList.sort(key=operator.attrgetter('create_time'))
        for childDto in procDto.childDtoList:
            self.printChilds(childDto, indent+1)


def load():


    with open('procData_save.pickle', 'r') as f:
        data = pickle.load(f)

    dataList = list()

    for k, v in data.items():
        dataList.append(v.items()[0][1])


    dataList.sort(key=operator.attrgetter('lastSeen'))
    for procDto in dataList:
        if procDto.pid == 1:
            rootNode = procDto



if __name__ == '__main__':

    pwv = ProcWatchViz()
    pwv.doViz2()
    #load()




