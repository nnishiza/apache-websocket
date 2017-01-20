import autobahn.twisted.websocket as ws

from twisted.internet import defer

class ProtocolFactory(ws.WebSocketClientFactory):
    """
    An implementation of WebSocketClientFactory that allows its client code to
    retrieve the first protocol instance that is built using the connected
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

    def clientConnectionFailed(self, connector, reason):
        self.connected.errback(reason)

class SimpleProtocol(ws.WebSocketClientProtocol):
    """
    Implements WebSocketClientProtocol for simple connection tests.

    The opened and closed attributes are Deferreds that can be waited on. The
    closed Deferred is None until the connection is opened; it will return the
    received close code in its callback.
    """
    def __init__(self):
        ws.WebSocketClientProtocol.__init__(self)

        self.opened = defer.Deferred()
        self.closed = None

    def onOpen(self):
        self.closed = defer.Deferred()
        self.opened.callback(None)

    def onClose(self, wasClean, code, reason):
        if wasClean:
            self.closed.callback(code)
        elif not self.opened.called:
            self.opened.errback(RuntimeError(
                "handshake failed (possible timeout?)"
            ))
        else:
            self.closed.errback(RuntimeError(
                "connection was dropped uncleanly (code {})".format(code)
            ))
