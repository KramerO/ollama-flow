#!/usr/bin/env python3
from .port_scanner import PortScannerService

class PortScannerApplication:
    def __init__(self):
        pass

    def start(self):
        port_scanner = PortScannerService("example.com", 22)
        print(port_scanner.scan_port())

if __name__ == "__main__":
    app = PortScannerApplication()
    app.start()
