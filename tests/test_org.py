import reporanger as rr

class TestOrg:
    def test_init(self):
        org = rr.Org(name="test_org")
        assert org.name == "test_org"

    def test_repr(self):
        org = rr.Org(name="test_org")
        assert repr(org) == "Org(name='test_org')"