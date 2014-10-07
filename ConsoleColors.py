class cc(object):

    code = '\033[%d;%d%dm'

    class m(object):
        reset = 0
        fg = 3
        bg = 4
        hifg = 9
        hibg = 10

    class d(object):
        regular = 0
        bold = 1
        underline = 4

    class c(object):
        black = 0
        red = 1
        green = 2
        yellow = 3
        blue = 4
        purple = 5
        cyan = 6
        white = 7

    @staticmethod
    def s(color=c.white, decorator=d.regular, mode=m.hifg):
        return cc.code % (decorator, mode, color)

    @staticmethod
    def r():
        return cc.code % (cc.m.reset, cc.m.reset, cc.m.reset)

    @staticmethod
    def w(text, color=c.white, decorator=d.regular, mode=m.hifg):
        return cc.s(color, decorator, mode) + str(text) + cc.r()
