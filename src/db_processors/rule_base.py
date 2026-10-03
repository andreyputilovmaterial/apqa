

from dataclasses import dataclass


def make_rule_factory(read,save):

    @dataclass
    class Rule:

        name: str

        def run(self):
            print('ok')
            return None

        def update(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def save(self,*argc,**argv):
            return save(*argc,**argv)
        
    return Rule
