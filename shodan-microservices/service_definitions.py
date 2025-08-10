#!/usr/bin/env python3
import json

class PortScannerService:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def scan_port(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except:
            return False

class HostDiscoveryService:
    def __init__(self):
        pass

    def discover_hosts(self):
        # Add your discovery logic here
        return ["example.com", "another.example.com"]

if __name__ == "__main__":
    host_discovery = HostDiscoveryService()
    port_scanner = PortScannerService("example.com", 22)
    print(json.dumps(host_discovery.discover_hosts()))
    print(port_scanner.scan_port())
