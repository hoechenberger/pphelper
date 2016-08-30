# -*- coding: utf-8 -*-

from __future__ import division

import pytest
from pphelper.hardware import (Gustometer, Olfactometer, Trigger)


class TestGustometer():
    def test_Gustometer_without_threads(self):
        self.g = Gustometer(use_threads=False, test_mode=True)
        self._test()

    def test_Gustometer_with_threads(self):
        self.g = Gustometer(use_threads=True, test_mode=True)
        self._test()

    def test_Gustometer_set_mode(self):
        self.g = Gustometer(use_threads=False, test_mode=True)

        self.g.set_mode('edit')
        assert self.g._mode == 'edit'

        self.g.set_mode('experiment')
        assert self.g._mode == 'experiment'

        self.g.set_mode('exp')
        assert self.g._mode == 'experiment'

        with pytest.raises(ValueError):
            self.g.set_mode('foobar')

    def _test(self):
        self.g.add_stimulus('Water', 0)
        self.g.select_stimulus('Water')
        self.g.stimulate()

    def teardown(self):
        del self.g


class TestOlfactometer():
    def test_Olfactometer_without_threads(self):
        self.o = Olfactometer(use_threads=False, test_mode=True)
        self._test()

    def test_Olfactometer_with_threads(self):
        self.o = Olfactometer(use_threads=True, test_mode=True)
        self._test()

    def _test(self):
        self.o.add_stimulus('Smell', bitmask=[1, 0, 0, 0, 0, 0, 0, 0])
        self.o.select_stimulus('Smell')
        self.o.stimulate()


class TestTrigger():
    def test_Trigger_without_threads(self):
        self.t = Trigger(use_threads=False, test_mode=True)
        self._test()

    def test_Trigger_with_threads(self):
        self.t = Trigger(use_threads=True, test_mode=True)
        self._test()

    def _test(self):
        self.t.add_stimulus('Onset', 128)
        self.t.select_stimulus('Onset')
        self.t.stimulate()
