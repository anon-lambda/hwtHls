from copy import copy

from hwt.hdl.operator import Operator
from hwt.hdl.value import Value
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwt.synthesizer.unit import Unit
from hwtHls.codeOps import HlsRead, HlsWrite, HlsOperation,\
    HlsConst, AbstractHlsOp
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.hdl.assignment import Assignment


def link_nodes(parent, child):
    child.dependsOn.append(parent)
    parent.usedBy.append(child)


class Hls():
    """
    High level synthesiser context.
    Convert sequential code to RTL.

    :ivar parentUnit: parent unit where RTL should be instantiated
    :ivar platform: platform with configuration of this HLS context
    :ivar freq: target frequency for RTL
    :ivar maxLatency: optional maximum allowed latency of circut
    :ivar resources: optional resource constrains
    :ivar inputs: list of HlsRead in this context
    :ivar outputs: list of HlsWrite in this context
    :ivar ctx: RtlNetlist (contarner of RTL signals for this HLS context)
    """

    def __init__(self, parentUnit: Unit,
                 freq, maxLatency=None, resources=None):
        self.parentUnit = parentUnit
        self.platform = parentUnit._targetPlatform
        if self.platform is None:
            raise Exception("HLS requires platform to be specified")

        self.clk_period = 1 / int(freq)
        self.maxLatency = maxLatency
        self.resources = resources
        self.inputs = []
        self.outputs = []
        self.ctx = RtlNetlist()

        self.scheduler = self.platform.scheduler(self)
        self.allocator = self.platform.allocator(self)
        # (still float div)
        self.platform.onHlsInit(self)

    def var(self, name, dtype=BIT, defVal=None):
        if isinstance(dtype, HStruct):
            if defVal is not None:
                raise NotImplementedError()
            container = dtype.fromPy(None)
            for f in dtype.fields:
                if f.name is not None:
                    r = self._var("%s_%s" % (name, f.name), f.dtype)
                    setattr(container, f.name, r)

            return container

        return self.ctx.sig(name, dtype=dtype, defVal=defVal)

    def read(self, intf, latency=0):
        """
        Scheduele read operation
        """
        return HlsRead(self, intf, latency)

    def write(self, what, where, latency=0):
        """
        Scheduele write operation
        """
        return HlsWrite(self, what, where, latency)

    def _discoverAllNodes(self):
        """
        Walk signals and extract operations as AbstractHlsOp

        (convert from representation with signals
         to directed graph of operations)
        """
        nodes = []
        nodeToHlsNode = {}

        def operator2HlsOperation(operator: Operator) -> HlsOperation:
            """
            Recursively convert operator and it's inputs to HLS representation

            :return: instance of HlsOperation representing of this operator
            """
            assert isinstance(operator, Operator), operator
            try:
                return nodeToHlsNode[operator]
            except KeyError:
                pass

            op_node = HlsOperation(self, operator.operator)
            nodeToHlsNode[operator] = op_node

            for op in operator.operands:
                op = hldObj2Hls(op)
                link_nodes(op, op_node)

            return op_node

        def hldObj2Hls(obj) -> AbstractHlsOp:
            """
            Convert RtlObject to HlsObject, register it and link it wit parent

            :note: parent is who provides values to operation
            """
            if isinstance(obj, Value) or obj._const:
                _obj = HlsConst(obj)
                nodes.append(_obj)
            elif len(obj.drivers) > 1:
                raise NotImplementedError()
            else:
                # parent is just RtlSignal, we needs operation
                # it is drivern from
                origin = obj.origin
                if isinstance(origin, HlsRead):
                    _obj = origin
                    nodes.append(_obj)
                elif isinstance(origin, Operator):
                    _obj = operator2HlsOperation(origin)
                elif isinstance(origin, Assignment):
                    raise NotImplementedError()
                else:
                    raise NotImplementedError(origin)

            return _obj

        nodes.extend(self.outputs)
        for out in self.outputs:
            driver = out.what
            driver = hldObj2Hls(driver)
            link_nodes(driver, out)

        nodes.extend(nodeToHlsNode.values())
        return nodes

    def synthesise(self):
        self.nodes = self._discoverAllNodes()
        self.scheduler.schedule()
        self.allocator.allocate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.synthesise()
