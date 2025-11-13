from io import StringIO


def test_pivot():
    from temboardui.plugins.monitoring.pivot import pivot_timeserie

    in_ = StringIO("i,k,v\n1,a,1\n1,b,2\n2,a,3\n4,b,5\n100,z,100\n")
    expected = "i,a,b,z\n1,1,2,\n2,3,,\n4,,5,\n100,,,100\n"
    out_ = StringIO()
    pivot_timeserie(in_, index="i", key="k", value="v", output=out_)
    assert out_.getvalue() == expected
