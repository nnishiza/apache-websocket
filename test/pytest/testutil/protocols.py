import autobahn.twisted.websocket as ws

from twisted.internet import defer

class ProtocolFactory(ws.WebSocketClientFactory):
    """
    An implementation of WebSocketClientFactory that allows the its client code
    to retrieve the first protocol instance that is built using the connected
    callback.
    """
    def __init__(self, uri, protocol):
        ws.WebSocketClientFactory.__init__(self, uri)
        self.proto = None
        self.protocol = protocol
        self.connected = defer.Deferred()

    def buildProtocol(self, addr):
        proto = self.protocol()
        proto.factory = self

        self.connected.callback(proto)
        return proto
