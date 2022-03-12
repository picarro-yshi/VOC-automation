#!/usr/bin/python3
#
# File Name: StringPickler.py
# Purpose: Converts ctypes objects to and from raw binary strings
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-07-12 russ  Removed * import from ctypes; upgraded deprecated c_buffer call; reformat
# 06-10-30 russ  Arbitrary object serialization support for
# Broadcaster/Listener usage

import binascii
import pickle
import struct
from ctypes import (Structure, _SimpleCData, addressof, c_char,
                    create_string_buffer, memmove, sizeof)
from typing import Any, Tuple


def object_as_bytes(obj: Any)->bytes:
    """Takes a ctypes object (works on structures too) and returns it as a string"""
    # There is probably a better way, but this seems to work ok
    sz = sizeof(obj)
    rawType = c_char * sz
    ptr = rawType.from_address(addressof(obj))
    return ptr.raw[:sz]


def bytes_as_object(aString: bytes, ObjType: Any)->Any:
    """Takes a string and returns it as a ctypes object"""
    z = create_string_buffer(aString)
    x = ObjType()
    memmove(addressof(x), addressof(z), sizeof(x))
    # x = ObjType.from_address(addressof(z))
    # x.__internal = z #ugly hack - save a ref to the buffer!
    del z
    return x


ID_COOKIE = b"\x52\x00\x57\x00"


class ArbitraryObjectErr(Exception):
    "Base class for erros in Arbitrary Object processing."


class IncompletePacket(ArbitraryObjectErr):
    "Bytes being unpacked is not a complete packet."


class ChecksumErr(ArbitraryObjectErr):
    "Checksum does not match."


class InvalidHeader(ArbitraryObjectErr):
    "First 4 bytes are not the expected cookie."


class BadDataBlock(ArbitraryObjectErr):
    "Data block does not unpickle (but checksum matches!?)"


class ArbitraryObject(object):
    """ID class for indicating when arbitrary object serialization should be used.

    Send this class (or one derived from this) to the elementType argument of
    the Listener constructor.

    There is no actual code for this class.  Support code is functional. Use
    pack_arbitrary_object() or unpack_arbitrary_object().

    Serialized objects will be sent and received like this:
      <ID_COOKIE><DataLength><Data><DataChecksum>

    Where:
      <ID_COOKIE>  - a 4 byte constant identifying the start of a serialized obj
      <DataLength> - a 4 byte unsigned int indicating the total # of bytes in the
                     packet, including (cookie + len + data + checksum)
      <Data> - the data block (a binary pickle of the object)
      <DataChecksum> - the 4 byte crc32 checksum of the data block.

    """


def pack_arbitrary_object(obj: Any) -> bytes:
    """Creates the full byte string output (length + data + checksum).

    See ArbitraryObject docstring for more detail.

    """
    data = pickle.dumps(obj, -1)
    data_checksum = binascii.crc32(data)
    # print "checkSum = %r  data = %r" % (data_checksum, data)
    # including cookie & len prefixes and crc suffix
    data_len = 4 + 4 + len(data) + 4
    packet_bytes = ID_COOKIE + \
        struct.pack("=L", data_len) + data + struct.pack("=L", data_checksum)
    return packet_bytes


def unpack_arbitrary_object(byte_str: bytes) -> Any:
    """Strips a packed arbitrary object from the head of the byte string, returning
    the object and the residual (the incoming byte string without the leading
    packet).

    Returns a tuple: (object, string_residual), where:
      object is the unpickled object
      string_residual is the remaining bytes in the provided byte string.

    Raises IncompletePacket if there are not enough bytes in the packet.
    Raises ChecksumErr if the checksum does not match the data.
    Raises InvalidHeader if the magic cookie header is not found (mid-tx read?)
    Raises BadDataBlock if a supposedly valid data block won't unpickle.

    Note that the length is NOT included in the input byte string (it has presumably
    been stripped off by the caller).

    See ArbitraryObject docstring for more detail.

    """
    length = len(byte_str)  # type: int
    # print "Length = %s" % length
    if length < 8:
        if length < 4:
            # No cookie yet
            raise IncompletePacket
        elif byte_str[:4] != ID_COOKIE:
            raise InvalidHeader
        else:
            # Don't have the length yet
            raise IncompletePacket
    else:
        packet_len = struct.unpack("=L", byte_str[4:8])[0]  # type: int
        # print "packet_len = %r" % packet_len
        if length < packet_len:
            raise IncompletePacket
        packet = byte_str[:packet_len]  # type: bytes
        # print "packet = %r" % packet
        cookie = packet[:4]  # type: bytes
        if cookie != ID_COOKIE:
            raise InvalidHeader
        data = packet[8:-4]   # type: bytes
        # print "data = %r" % data
        checksum = struct.unpack("=L", packet[-4:])[0]  # type: int
        # print "checksum = %r" % checksum
        if binascii.crc32(data) != checksum:
            raise ChecksumErr
        # If we get here, we have a good data block... time to unpickle...
        try:
            obj = pickle.loads(data, encoding="latin1")  # type: Any
        except:
            import sys
            print(repr(sys.exc_info()))
            raise BadDataBlock
        residual = byte_str[packet_len:]  # type: bytes
        ret = (obj, residual)  # type: Tuple[Any, bytes]
        return ret