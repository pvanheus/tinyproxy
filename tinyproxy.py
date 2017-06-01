#!/usr/bin/env python

"""tinyproxy - a tiny proxy for Neo4j.

A tiny Flask proxy for connecting a browser to a
Neo4j server running in a Docker container while rewriting
the Neo4j browser configuration on the fly. Used as
a testing platform for Galaxy Interactive Environment
development.
"""

from __future__ import print_function

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO
import shlex
import subprocess
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import requests
from flask import Flask, Response, stream_with_context, request, redirect

app = Flask(__name__)
log = app.logger


@app.route('/')
def root():
    """Handle / url.

    The Neo4j browser accesses the root ('/') twice, once at start,
    where it is redirected to '/browser', and then, using
    'Content-Type: application/json' in its request. This
    second time it expects browser configuration to be
    returned in JSON, which gives the proxy an opportunity
    to alter the browser config.
    """
    bolt_port = port_mapping[7687]
    content_type = request.headers.get('Content-Type', 'text/html')
    if content_type == 'application/json':
        results = {
            "management": "http://localhost:5000/app/db/manage/",
            "data": "http://localhost:5000/app/db/data/",
            "bolt": "bolt://localhost:{}".format(bolt_port)
        }
        return Response(
            json.dumps(results),
            mimetype='application/json',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    else:
        return redirect('/app/browser', code=302)


@app.route('/app/<path:anything>')
def proxy(anything):
    """Proxy requests to Neo4j HTTP port.

    Catch requests from the Neo4j browser app and
    direct them to the Docker container
    """
    http_port = port_mapping[7474]
    if anything == 'browser':
        url = anything
    else:
        url = 'browser/' + anything
    req = requests.get('http://localhost:{}/{}'.format(http_port, url),
                       stream=True)
    return Response(stream_with_context(req.iter_content(chunk_size=32768)),
                    content_type=req.headers.get('Content-Type', 'text/html'))


if __name__ == '__main__':
    port = int(os.environ.get('PROXY_PORT', 5000))
    docker_container_name = os.environ.get('NEO4J_DOCKER_CONTAINER', 'test')

    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # initialize the log handler
    logHandler = RotatingFileHandler('logs/info.log', maxBytes=1000,
                                     backupCount=1)

    # set the log handler level
    logHandler.setLevel(logging.DEBUG)
    logHandler.setFormatter(formatter)

    # set the app logger level
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logHandler)

    docker_run = subprocess.run(
        shlex.split('/usr/bin/docker port test'.format(docker_container_name)),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if docker_run.returncode != 0:
        exit("failed to get docker port info: {} {}".format(
            docker_run.returncode, docker_run.stderr))
    docker_ports = StringIO(docker_run.stdout.decode('utf-8'))
    port_mapping = dict()
    for line in docker_ports:
        # print(line)
        (dest_str, src_str) = line.split(' -> ')
        # print(dest_str.split('/'))
        dest_port = int(dest_str.split('/')[0])
        src_port = int(src_str.split(':')[1])
        port_mapping[dest_port] = src_port
    assert 7474 in port_mapping.keys() and 7687 in port_mapping.keys(), "Failed to find necessary ports in 'docker port test' output: {}".format(docker_run.stdout)
    app.run(port=port, debug=True, processes=5)
