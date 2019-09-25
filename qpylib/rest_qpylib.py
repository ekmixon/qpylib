# Copyright 2019 IBM Corporation All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

from flask import request, has_request_context
import os
import requests
from socket import gethostbyname, gethostname
from . import app_qpylib

QRADAR_CSRF = 'QRadarCSRF'
SEC_HEADER = 'SEC'
SEC_ADMIN_TOKEN = 'SEC_ADMIN_TOKEN'

def live_rest(rest_action, request_url, version, headers, data,
              params, json_body, verify, timeout):

    if os.path.isfile('/store/consolecert.pem'):
        verify = '/store/consolecert.pem'
    elif not isinstance(verify, str):
        verify = _get_cert_filepath()

    return _rest(rest_action, request_url, version, headers, data,
                 params, json_body, verify, timeout)

def sdk_rest(rest_action, request_url, version, headers, data,
             params, json_body, verify, timeout):

    if not isinstance(verify, str):
        # To be completed
        verify = False

    return _rest(rest_action, request_url, version, headers, data,
                 params, json_body, verify, timeout)

def _rest(rest_action, request_url, version, headers, data,
          params, json_body, verify, timeout):

    rest_func = _choose_rest_function(rest_action)
    full_url = _generate_full_url(request_url)
    rest_headers = _add_headers(headers, version)
    proxies = _add_proxies()

    return rest_func(full_url, headers=rest_headers, data=data, params=params,
                     json=json_body, verify=verify, timeout=timeout, proxies=proxies)

def _get_cert_filepath():
    with open('/proc/mounts') as mounts:
        if '/etc/qradar_pki' in mounts.read():
            return '/etc/pki/tls/certs/ca-bundle.crt'
    return False

def _add_headers(headers, version=None):
    if headers is None:
        headers = {}

    if version is not None:
        headers['Version'] = version

    if headers.get('Host') is None:
        headers['Host'] = gethostbyname(gethostname())

    if has_request_context():
        if QRADAR_CSRF in request.cookies.keys():
            headers[QRADAR_CSRF] = request.cookies.get(QRADAR_CSRF)
        if SEC_HEADER in request.cookies.keys() \
            and SEC_HEADER not in headers.keys():
            headers[SEC_HEADER] = request.cookies.get(SEC_HEADER)

    sec_admin_token = os.getenv(SEC_ADMIN_TOKEN)
    if sec_admin_token is not None:
        headers[SEC_HEADER] = sec_admin_token

    return headers

def _add_proxies():
    qradar_rest_proxy = os.getenv('QRADAR_REST_PROXY')
    if qradar_rest_proxy is None:
        return {}
    return {'https': qradar_rest_proxy}

def _generate_full_url(request_url):
    return "https://{0}/{1}".format(app_qpylib.get_console_fqdn(), request_url)

def _choose_rest_function(rest_action):
    return {
        'GET': requests.get,
        'PUT': requests.put,
        'POST': requests.post,
        'DELETE': requests.delete,
    }.get(rest_action.upper(), _unsupported_REST)

def _unsupported_REST(*args, **kw_args):
    raise ValueError('Unsupported REST action was requested')
