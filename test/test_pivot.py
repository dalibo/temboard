import pytest
from StringIO import StringIO

def test_pivot():
    from temboardui.plugins.monitoring.pivot import pivot_timeserie

    in_ = StringIO(
            "i,k,v\n"
            "1,a,1\n"
            "1,b,2\n"
            "2,a,3\n"
            "4,b,5\n"
            "100,z,100\n"
            )
    expected = "i,a,b,z\n"\
               "1,1,2,\n"\
               "2,3,,\n"\
               "4,,5,\n"\
               "100,,,100\n"
    out_ = StringIO()
    pivot_timeserie(
        in_,
        index='i',
        key='k',
        value='v',
        output=out_
    )
    assert out_.getvalue() == expected
