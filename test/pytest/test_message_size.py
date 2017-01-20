import autobahn.twisted.websocket as ws
import pytest
import struct

from twisted.internet import defer

from testutil.fixtures import fixture_connect
from testutil.protocols import SimpleProtocol
from testutil.websocket import make_root, SCHEME

CLOSE_CODE_NORMAL_CLOSURE  = 1000
CLOSE_CODE_MESSAGE_TOO_BIG = 1009

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT         = 0x1

ROOT = make_root("wss" if (SCHEME == "https") else "ws")

#
# Fixtures
#

def connect(uri):
    """Helper wrapper for fixture_connect."""
    return fixture_connect(uri, SimpleProtocol)

@pytest.fixture
def proto():
    """
    A fixture that returns a WebSocket protocol connection to an endpoint with a
    MaxMessageSize of 4.
    """
    return connect(ROOT + "/size-limit")

#
# Tests
#

@pytest.inlineCallbacks
def test_overlarge_single_messages_are_rejected_when_using_MaxMessageSize(proto):
    proto.sendMessage('12345')
    response = yield proto.closed
    assert response == CLOSE_CODE_MESSAGE_TOO_BIG

@pytest.inlineCallbacks
def test_overlarge_fragmented_messages_are_rejected_when_using_MaxMessageSize(proto):
    proto.sendFrame(opcode=OPCODE_TEXT, payload='x', fin=False)

    for _ in range(4):
        proto.sendFrame(opcode=OPCODE_CONTINUATION, payload='x', fin=False)

    response = yield proto.closed
    assert response == CLOSE_CODE_MESSAGE_TOO_BIG

@pytest.inlineCallbacks
def test_overlarge_fragmented_messages_are_still_rejected_with_interleaved_control_frames(proto):
    proto.sendFrame(opcode=OPCODE_TEXT, payload='x', fin=False)
    proto.sendPing() # send a control frame to split up the text message

    for _ in range(4):
        proto.sendFrame(opcode=OPCODE_CONTINUATION, payload='x', fin=False)

    response = yield proto.closed
    assert response == CLOSE_CODE_MESSAGE_TOO_BIG

@pytest.inlineCallbacks
def test_overflowing_fragmented_messages_are_rejected_when_using_MaxMessageSize(proto):
    # For a signed 64-bit internal implementation, a fragment of one byte plus a
    # fragment of (2^63 - 1) bytes will overflow into a negative size. The
    # server needs to deal with this case gracefully.
    proto.sendFrame(opcode=OPCODE_TEXT, payload='x', fin=False)

    # Unfortunately we can't call sendFrame() with our desired length, because
    # it'll actually attempt to buffer a payload in memory and die. Manually
    # construct a (partial) frame ourselves.
    frame = b''.join([
        b'\x80', # FIN bit set, no RSVx bits, opcode 0 (continuation)
        b'\xFF', # MASK bit set, length of "127" (the 8-byte flag value)
        struct.pack("!Q", 0x7FFFFFFFFFFFFFFFL) # largest possible length

        # We don't need the rest of the frame header; the server should reject
        # it at this point.
    ])
    proto.sendData(frame)

    response = yield proto.closed
    assert response == CLOSE_CODE_MESSAGE_TOO_BIG

@pytest.inlineCallbacks
def test_several_messages_under_the_MaxMessageSize_are_allowed(proto):
    proto.sendMessage('1234')
    proto.sendMessage('1234')
    proto.sendMessage('1234')
    proto.sendMessage('1234')

    proto.sendClose(CLOSE_CODE_NORMAL_CLOSURE)
    response = yield proto.closed
    assert response == CLOSE_CODE_NORMAL_CLOSURE

@pytest.inlineCallbacks
def test_control_frames_are_also_affected_by_MaxMessageSize(proto):
    # Two-byte close code, three-byte payload: five bytes total
    proto.sendClose(CLOSE_CODE_NORMAL_CLOSURE, "123")

    response = yield proto.closed
    assert response == CLOSE_CODE_MESSAGE_TOO_BIG

@pytest.inlineCallbacks
def test_several_control_frames_under_the_MaxMessageSize_are_allowed(proto):
    proto.sendPing('1234')
    proto.sendPing('1234')
    proto.sendPing('1234')
    proto.sendPing('1234')

    proto.sendClose(CLOSE_CODE_NORMAL_CLOSURE)
    response = yield proto.closed
    assert response == CLOSE_CODE_NORMAL_CLOSURE
