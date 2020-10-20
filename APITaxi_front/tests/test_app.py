import datetime
import json

import APITaxi_front


def test_jinja2_json_filter():
    # Input is a string representing valid json
    ret = APITaxi_front.jinja2_json_filter('{"key":"value"}')
    assert ret == json.dumps({'key': 'value'}, indent=2)

    # Input is a dictionary
    ret = APITaxi_front.jinja2_json_filter({'key': 'value'})
    assert ret == json.dumps({'key': 'value'}, indent=2)

    # Input is invalid json, it is returned as-is
    ret = APITaxi_front.jinja2_json_filter('{{{')
    assert ret == '{{{'


def test_jinja2_str_to_datetime_filter():
    ret = APITaxi_front.jinja2_str_to_datetime_filter('2012-12-21')
    assert ret == datetime.datetime(2012, 12, 21)
