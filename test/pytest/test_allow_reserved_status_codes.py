import autobahn.twisted.websocket as ws
import pytest

from twisted.internet import defer

from testutil.fixtures import fixture_connect
from testutil.protocols import SimpleProtocol
from testutil.websocket import make_root, SCHEME

CLOSE_CODE_PROTOCOL_ERROR = 1002

ROOT = make_root("wss" if (SCHEME == "https") else "ws")

#
# Autobahn Subclasses
#

class CloseTestProtocol(SimpleProtocol):
    """
    A version of SimpleProtocol that allows invalid close codes to be sent.
    """
    # XXX Monkey-patch sendClose() to allow invalid codes on the wire.
    def sendClose(self, code=None, reason=None):
        self.sendCloseFrame(code=code, isReply=False)

#
# Helpers
#

def succeeded(code):
    return code != CLOSE_CODE_PROTOCOL_ERROR

def failed(code):
    return not succeeded(code)

#
# Fixtures
#

def connect(uri):
    """Helper wrapper for fixture_connect."""
    return fixture_connect(uri, CloseTestProtocol)

@pytest.fixture
def default_proto():
    """A fixture that returns a WebSocket protocol connection to an endpoint
    that has no WebSocketAllowReservedStatusCodes directive."""
    return connect(ROOT + "/echo")

@pytest.fixture
def allow_proto():
    """A fixture that returns a WebSocket protocol connection to an endpoint
    that has WebSocketAllowReservedStatusCodes enabled."""
    return connect(ROOT + "/echo-allow-reserved")

#
# Tests
#

@pytest.inlineCallbacks
def test_1000_is_always_allowed(allow_proto):
    allow_proto.sendClose(1000)
    response = yield allow_proto.closed
    assert succeeded(response)

@pytest.inlineCallbacks
def test_1004_is_rejected_by_default(default_proto):
    default_proto.sendClose(1004)
    response = yield default_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1004_is_allowed_when_allowing_reserved(allow_proto):
    allow_proto.sendClose(1004)
    response = yield allow_proto.closed
    assert succeeded(response)

@pytest.inlineCallbacks
def test_1005_is_never_allowed(allow_proto):
    allow_proto.sendClose(1005)
    response = yield allow_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1006_is_never_allowed(allow_proto):
    allow_proto.sendClose(1006)
    response = yield allow_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1014_is_rejected_by_default(default_proto):
    default_proto.sendClose(1014)
    response = yield default_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1014_is_allowed_when_allowing_reserved(allow_proto):
    allow_proto.sendClose(1014)
    response = yield allow_proto.closed
    assert succeeded(response)

@pytest.inlineCallbacks
def test_1015_is_never_allowed(allow_proto):
    allow_proto.sendClose(1015)
    response = yield allow_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1016_is_rejected_by_default(default_proto):
    default_proto.sendClose(1016)
    response = yield default_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_1016_is_allowed_when_allowing_reserved(allow_proto):
    allow_proto.sendClose(1016)
    response = yield allow_proto.closed
    assert succeeded(response)

@pytest.inlineCallbacks
def test_2000_is_rejected_by_default(default_proto):
    default_proto.sendClose(2000)
    response = yield default_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_2000_is_allowed_when_allowing_reserved(allow_proto):
    allow_proto.sendClose(2000)
    response = yield allow_proto.closed
    assert succeeded(response)

@pytest.inlineCallbacks
def test_2999_is_rejected_by_default(default_proto):
    default_proto.sendClose(2999)
    response = yield default_proto.closed
    assert failed(response)

@pytest.inlineCallbacks
def test_2999_is_allowed_when_allowing_reserved(allow_proto):
    allow_proto.sendClose(2999)
    response = yield allow_proto.closed
    assert succeeded(response)
