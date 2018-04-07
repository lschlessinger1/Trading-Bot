import random

JUMP_SIGMA = 0.2
TRUNCATE_AFTER = True

class BinomialDraws(object):
    def __init__(self, initial_p=None):
        if initial_p is None:
            self._p = random.random()
        else:
            assert 0.0 <= initial_p <= 1.0
            self._p = initial_p
        assert self._p <= 1.0
        assert self._p >= 0.0

    def do_jump(self):
        have_good_p = False
        while not have_good_p:
            delta_p = random.normalvariate(0.0, JUMP_SIGMA)
            new_p = delta_p + self._p
            if TRUNCATE_AFTER:
                new_p = min(max(new_p, 0.0), 1.0)
                have_good_p = True
            else:
                have_good_p = (new_p <= 1.0 and new_p >= 0.0)
        assert new_p <= 1.0 and new_p >= 0.0
        self._p = new_p

    def get_draw(self):
        if random.random() < self._p:
            return 1
        else:
            return 0
