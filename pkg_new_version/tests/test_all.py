import pytest
from pkg_new_version import pkg_new_version as pkgnv

TEST_URL = 'https://data.eawag.ch/dataset/hardwald'
@pytest.fixture(scope='module')
def get_test_pkg():
    conn = pkgnv._getconn(TEST_URL)
    return(conn)

def test_all():
    print(get_test_pkg)
    
