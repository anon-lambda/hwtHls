from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtHls.hls import Hls
from hwtHls.platform.virtual import VirtualHlsPlatform


class HlsConnection(Unit):
    def _declr(self):
        self.a = VectSignal(32, signed=False)
        self.b = VectSignal(32, signed=False)

    def _impl(self):
        with Hls(self, freq=int(100e6)) as hls:
            a = hls.read(self.a)
            hls.write(a, self.b)


if __name__ == "__main__":
    u = HlsConnection()
    print(toRtl(u, targetPlatform=VirtualHlsPlatform()))
