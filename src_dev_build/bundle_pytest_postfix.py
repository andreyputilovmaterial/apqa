# code for pytest (appended by build.sh to the end of dist/apqa_bundle.py)

import pytest
from src import tstsuite

tst_load_error = None
tst_cases = []
try:
    tst_cases = [ t for t in tstsuite.load_case_params() ]
except Exception as e:
    tst_load_error = e

@pytest.mark.parametrize('case', tst_cases)
def test_run_case(case):
    return tstsuite.run_tst_case(case)


# When the bundle is imported (pytest), fail early if the rules could not be
# loaded. When run directly (`python apqa_bundle.py --program ...`), pinliner's
# --main entry point already ran launcher.main(), so there is nothing to raise.
if __name__ != '__main__':
    if tst_load_error:
        raise tst_load_error
