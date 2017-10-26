from hwt.interfaces.std import VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtHls.hls import Hls
from hwt.synthesizer.shortcuts import toRtl


class HlsExample0(Unit):
    def _declr(self):
        self.a = VectSignal(32, signed=False)
        self.b = VectSignal(32, signed=False)

    def _impl(self):
        with Hls(self, freq=int(100e6)) as hls:
            a = hls.read(self.a)
            hls.write(a, self.b)


if __name__ == "__main__":
    u = HlsExample0()
    print(toRtl(u))
