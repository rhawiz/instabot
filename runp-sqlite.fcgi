#!/usr/bin/python
from flipflop import WSGIServer
from app import app

WSGIServer(app).run()