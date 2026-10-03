

from dataclasses import dataclass


def make_rule_factory(read,save):

    @dataclass
    class Rule:
        def __init__(self):
            # self._read = read
            # self._save = save
            pass
        def update(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        def save(self,*argc,**argv):
            return save(*argc,**argv)
    return Rule
