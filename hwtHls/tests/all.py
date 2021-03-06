#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestLoader, TextTestRunner, TestSuite

from hwt.simulator.hdlSimConfig import HdlSimConfig
from hwt.simulator.hdlSimulator import HdlSimulator
from hwt.simulator.simTestCase import SimTestCase
from hwtHls.examples.alapAsapDiffExample import AlapAsapDiffExample_TC
from hwtHls.examples.bitonicSort import BitonicSorterHLS_TC,\
    BitonicSorterHLS_large_TC
from hwtHls.examples.hls_expr_tree3 import HlsExprTree3_example_TC
from hwtHls.examples.mac import HlsMAC_example_TC
from hwtHls.tests.connection import HlsSlicingTC
from hwtHls.scheduler.list_schedueling_test import ListSchedueling_TC


def doSimWithoutLog(self, until, name=None, config=None):
    sim = HdlSimulator()
    # dummy config
    sim.config = HdlSimConfig()
    # run simulation, stimul processes are register after initial
    # initialization
    sim.simUnit(self.model, until=until, extraProcesses=self.procs)
    return sim


def testSuiteFromTCs(*tcs):
    loader = TestLoader()
    for tc in tcs:
        if issubclass(tc, SimTestCase):
            tc.doSim = doSimWithoutLog
        tc._multiprocess_can_split_ = True
    loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
    suite = TestSuite(loadedTcs)
    return suite


suite = testSuiteFromTCs(
    HlsSlicingTC,
    HlsMAC_example_TC,
    BitonicSorterHLS_TC,
    BitonicSorterHLS_large_TC,
    HlsExprTree3_example_TC,
    AlapAsapDiffExample_TC,
    ListSchedueling_TC,
)


if __name__ == '__main__':
    runner = TextTestRunner(verbosity=2)

    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallerlTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallerlTest = False

    if useParallerlTest:
        # Run same tests across 4 processes
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests())
        runner.run(concurrent_suite)
    else:
        runner.run(suite)
