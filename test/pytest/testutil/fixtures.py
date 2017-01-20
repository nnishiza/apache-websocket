import autobahn.twisted.websocket as ws
import pytest
import urlparse

from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.web import client

from .protocols import ProtocolFactory

class _UnsecureClientContextFactory(ClientContextFactory):
    """An SSL context factory that performs no cert checks."""
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)

_context_factory = _UnsecureClientContextFactory()

class _HTTP10Agent:
    """
    A hacky attempt at an HTTP/1.0 version of t.w.c.Agent.  Unfortunately
    t.w.c.Agent only supports HTTP/1.1, so we have to create this ourselves. It
    uses the old HTTPClientFactory implementation in Twisted.

    Note that this only sort of implements Agent (it doesn't callback until the
    response is received, and it doesn't even return the full response from
    request()) and is really only useful for the purposes of these tests.
    """
    def __init__(self, reactor):
        self._reactor = reactor

    class _FakeResponse:
        def __init__(self, code):
            self.code = code

    def request(self, method, uri, headers=None, bodyProducer=None):
        url = urlparse.urlparse(uri, scheme='http')
        host = url.hostname
        port = url.port

        if port is None:
            port = 443 if (url.scheme == 'https') else 80

        # Translate from Agent's Headers object back into a dict.
        if headers is not None:
            old_headers = {}
            for name, value_list in headers.getAllRawHeaders():
                old_headers[name] = value_list[0]
            headers = old_headers

        f = client.HTTPClientFactory(uri, method=method, headers=headers,
                                     timeout=2)

        def gotResponse(page):
            return _HTTP10Agent._FakeResponse(int(f.status))
        f.deferred.addBoth(gotResponse)

        if url.scheme == 'https':
            self._reactor.connectSSL(host, port, f, ClientContextFactory())
        else:
            self._reactor.connectTCP(host, port, f)

        return f.deferred

#
# Fixture Helper Functions
#

def fixture_connect(uri, protocol):
    """
    Connects to the given WebSocket URI using an instance of the provided
    WebSocketClientProtocol subclass.

    This is intended to be called by pytest fixtures; it will block until a
    connection is made and return the protocol instance that wraps the
    connection.
    """
    factory = ProtocolFactory(uri, protocol)
    factory.setProtocolOptions(failByDrop=False, openHandshakeTimeout=1)

    ws.connectWS(factory, timeout=1)
    protocol = pytest.blockon(factory.connected)

    pytest.blockon(protocol.opened)
    return protocol

#
# Fixtures
#

@pytest.fixture
def agent():
    """Returns a t.w.c.Agent for use by tests."""
    return client.Agent(reactor, _context_factory)

@pytest.fixture
def agent_10():
    """Returns an HTTP/1.0 "Agent"."""
    return _HTTP10Agent(reactor)
