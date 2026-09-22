#!/usr/bin/env python

"""
Manipulate PSARC archives used by Rocksmith 2014.

Usage:
    psarc.py pack DIRECTORY...
    psarc.py unpack FILE...
    psarc.py convert FILE...
"""

from Crypto.Cipher import AES
from Crypto.Util import Counter

import struct
import zlib
import os
import hashlib
import sys
import json
import codecs

print("psarc.py running on Python version %s.%s" % (sys.version_info.major, sys.version_info.minor))

MAGIC = b"PSAR"
VERSION = 65540
COMPRESSION = b"zlib"
ARCHIVE_FLAGS = 4
ENTRY_SIZE = 30
BLOCK_SIZE = 65536

ARC_KEY = 'C53DB23870A1A2F71CAE64061FDD0E1157309DC85204D4C5BFDF25090DF2572C'
ARC_IV = 'E915AA018FEF71FC508132E4BB4CEB42'

MAC_KEY = '9821330E34B91F70D0A48CBD625993126970CEA09192C0E6CDA676CC9838289D'
PC_KEY = 'CB648DF3D12A16BF71701414E69619EC171CCA5D2A142E3E59DE7ADDA18A3A30'

PRF_KEY = '728B369E24ED0134768511021812AFC0A3C25D02065F166B4BCC58CD2644F29E'
CONFIG_KEY = '378B9026EE7DE70B8AF124C1E30978670F9EC8FD5E7285A86442DD73068C0473'


def pad(data, blocksize=16):
    """Zeros padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    padding = (blocksize - len(data)) % blocksize
    return data + bytes(padding)


def path2dict(path):
    """Reads a path into a dictionary"""
    output = {}
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            fullpath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(fullpath, path).replace('\\', '/')

            with open(fullpath, 'rb') as fstream:
                output[relpath] = fstream.read()

    return output


def decrypt_profile(stream):
    """For *_prfldb, crd and profile.json files"""
    s = stream.read()
    size = struct.unpack('<L', s[16:20])[0]

    cipher = AES.new(codecs.decode(PRF_KEY, 'hex'))
    x = zlib.decompress(cipher.decrypt(pad(s[20:])))
    assert(size == len(x))

    return json.loads(x[:-1].decode('utf-8'))


def stdout_same_line(line):
    """Prepend carriage return and output to stdout"""
    sys.stdout.write('\r' + line[:80])
    sys.stdout.flush()


def aes_ctr(data, key, ivector, encrypt=True):
    """AES CTR Mode"""
    ctr = Counter.new(64, initial_value=ivector)
    cipher = AES.new(codecs.decode(key, 'hex'), mode=AES.MODE_CTR, counter=ctr)

    if encrypt:
        return cipher.encrypt(pad(data))
    else:
        return cipher.decrypt(pad(data))


def decrypt_sng(data, key):
    """Decrypt SNG."""
    decrypted = aes_ctr(data[24:], key, int(codecs.encode(data[8:24], 'hex'), 16), encrypt=False)
    length = struct.unpack('<L', decrypted[:4])[0]
    try:
        payload = zlib.decompress(decrypted[4:])
        assert len(payload) == length
    except Exception:
        payload = decrypted

    return payload


def encrypt_sng(data, key):
    """Encrypt SNG"""
    output = struct.pack('<LL', 0x4a, 3)
    payload = struct.pack('<L', len(data))
    payload += zlib.compress(data, zlib.Z_BEST_COMPRESSION)

    ivector = bytes(16)
    output += ivector
    output += aes_ctr(payload, key, int(codecs.encode(ivector, 'hex'), 16) if ivector else 0)
    return output + bytes(56)


def read_entry(filestream, entry):
    """Extract zlib for one entry"""
    data = bytearray()
    length = entry['length']
    zlength = entry['zlength']
    filestream.seek(entry['offset'])

    i = 0
    while len(data) < length:
        if zlength[i] == 0:
            data += filestream.read(BLOCK_SIZE)
        else:
            chunk = filestream.read(zlength[i])
            try:
                data += zlib.decompress(chunk)
            except zlib.error:
                data += chunk
        i += 1

    data = bytes(data)

    if entry['filepath'].find('songs/bin/macos/') > -1:
        data = decrypt_sng(data, MAC_KEY)
    elif entry['filepath'].find('songs/bin/generic/') > -1:
        data = decrypt_sng(data, PC_KEY)

    return data


def create_entry(name, data):
    """Chunk a file"""
    if isinstance(data, str):
        data = data.encode('utf-8')

    if name.find('songs/bin/macos/') > -1:
        data = encrypt_sng(data, MAC_KEY)
    elif name.find('songs/bin/generic/') > -1:
        data = encrypt_sng(data, PC_KEY)

    zlength = []
    output = bytearray()

    i = 0
    while i < len(data):
        raw = data[i:i + BLOCK_SIZE]
        i += BLOCK_SIZE

        compressed = zlib.compress(raw, zlib.Z_BEST_COMPRESSION)
        if len(compressed) < len(raw):
            output += compressed
            zlength.append(len(compressed))
        else:
            output += raw
            zlength.append(len(raw) % BLOCK_SIZE)

    md5_hash = hashlib.md5(name.encode('utf-8') if isinstance(name, str) else name).digest() if name else bytes(16)

    return {
        'filepath': name,
        'zlength': zlength,
        'length': len(data),
        'data': bytes(output),
        'md5': md5_hash
    }


def cipher_toc():
    """AES CFB Mode"""
    return AES.new(codecs.decode(ARC_KEY, 'hex'), mode=AES.MODE_CFB,
                   IV=codecs.decode(ARC_IV, 'hex'), segment_size=128)


def read_toc(filestream):
    """Read entry list and Z-fragments."""
    entries = []
    zlength = []

    filestream.seek(0)
    header = struct.unpack('>4sL4sLLLLL', filestream.read(32))

    toc_size = header[3] - 32
    n_entries = header[5]
    toc = cipher_toc().decrypt(pad(filestream.read(toc_size)))
    toc_position = 0

    idx = 0
    while idx < n_entries:
        data = toc[toc_position:toc_position + ENTRY_SIZE]

        entries.append({
            'md5': data[:16],
            'zindex': struct.unpack('>L', data[16:20])[0],
            'length': struct.unpack('>Q', b'\x00'*3 + data[20:25])[0],
            'offset': struct.unpack('>Q', b'\x00'*3 + data[25:30])[0]
        })
        toc_position += ENTRY_SIZE
        idx += 1

    idx = 0
    total_z_chunks = int((toc_size - ENTRY_SIZE * n_entries) / 2)
    while idx < total_z_chunks:
        data = toc[toc_position:toc_position + 2]
        zlength.append(struct.unpack('>H', data)[0])
        toc_position += 2
        idx += 1

    for entry in entries:
        entry['zlength'] = zlength[entry['zindex']:]

    entries[0]['filepath'] = ''
    raw_names = read_entry(filestream, entries[0])
    filepaths = raw_names.split()
    for entry, filepath in zip(entries[1:], filepaths):
        entry['filepath'] = filepath.decode('utf-8', errors='ignore')

    return entries[1:]


def create_toc(entries):
    """Build an encrypted TOC for a given list of entries."""
    offset = 0
    zindex = 0
    zlength = []
    for entry in entries:
        entry['offset'] = offset
        offset += len(entry['data'])

        entry['zindex'] = zindex
        zindex += len(entry['zlength'])

        zlength += entry['zlength']

    toc_size = 32 + ENTRY_SIZE * len(entries) + 2 * len(zlength)

    header = struct.pack('>4sL4sLLLLL', MAGIC, VERSION, COMPRESSION,
                         toc_size, ENTRY_SIZE, len(entries),
                         BLOCK_SIZE, ARCHIVE_FLAGS)

    toc = bytearray()
    for entry in entries:
        toc += entry['md5']
        toc += struct.pack('>L', entry['zindex'])
        toc += struct.pack('>Q', entry['length'])[-5:]
        toc += struct.pack('>Q', entry['offset'] + toc_size)[-5:]

    for i in zlength:
        toc += struct.pack('>H', i)

    encrypted_toc = cipher_toc().encrypt(pad(bytes(toc)))
    return (header + encrypted_toc)[:toc_size]


def extract_psarc(filename):
    """Extract a PSARC to disk"""
    basepath = os.path.basename(filename)
    if basepath.lower().endswith('.psarc'):
        basepath = basepath[:-6]

    with open(filename, 'rb') as psarc:
        entries = read_toc(psarc)
        logmsg = 'Extracting ' + basepath + ' {0}/' + str(len(entries))

        for idx, entry in enumerate(entries):
            stdout_same_line(logmsg.format(idx + 1))
            fname = os.path.join(basepath, entry['filepath'])
            data = read_entry(psarc, entry)
            path = os.path.dirname(fname)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            with open(fname, 'wb') as fstream:
                fstream.write(data)
    print("\nExtração concluída com sucesso!")


def create_psarc(files, filename):
    """Writes a dictionary filepath -> data to a PSARC file"""
    filenames = sorted(files.keys(), reverse=True)
    manifest_data = '\n'.join(filenames).encode('utf-8')
    entries = [create_entry('', manifest_data)]

    logmsg = 'Creating ' + filename + ' {0}/' + str(len(files))
    for idx, name in enumerate(filenames):
        stdout_same_line(logmsg.format(idx + 1))
        entries.append(create_entry(name, files[name]))

    with open(filename, 'wb') as fstream:
        fstream.write(create_toc(entries))
        for entry in entries:
            fstream.write(entry['data'])
    print("\nEmpacotamento concluído com sucesso!")


def change_path(data, osx2pc):
    """Changing path"""
    if isinstance(data, bytes):
        if osx2pc:
            data = data.replace(b'audio/mac', b'audio/windows')
            data = data.replace(b'bin/macos', b'bin/generic')
        else:
            data = data.replace(b'audio/windows', b'audio/mac')
            data = data.replace(b'bin/generic', b'bin/macos')
    else:
        if osx2pc:
            data = data.replace('audio/mac', 'audio/windows')
            data = data.replace('bin/macos', 'bin/generic')
        else:
            data = data.replace('audio/windows', 'audio/mac')
            data = data.replace('bin/generic', 'bin/macos')
    return data


def convert(filename):
    """Convert between PC and Mac PSARC"""
    content = {}

    osx2pc = False
    if filename.endswith('_m.psarc'):
        outname = filename.replace('_m.psarc', '_p.psarc')
        osx2pc = True
    else:
        outname = filename.replace('_p.psarc', '_m.psarc')

    with open(filename, 'rb') as psarc:
        entries = read_toc(psarc)
        for entry in entries:
            data = read_entry(psarc, entry)

            if entry['filepath'].endswith('aggregategraph.nt'):
                data = change_path(data, osx2pc)
                if osx2pc:
                    data = data.replace(b'macos', b'dx9') if isinstance(data, bytes) else data.replace('macos', 'dx9')
                else:
                    data = data.replace(b'dx9', b'macos') if isinstance(data, bytes) else data.replace('dx9', 'macos')

            content[change_path(entry['filepath'], osx2pc)] = data

    create_psarc(content, outname)


if __name__ == '__main__':
    from docopt import docopt
    args = docopt(__doc__)

    if args['unpack']:
        for f in args['FILE']:
            extract_psarc(f)
    elif args['pack']:
        for d in args['DIRECTORY']:
            d = os.path.normpath(d)
            create_psarc(path2dict(d), d + '.psarc')
    elif args['convert']:
        for f in args['FILE']:
            convert(f)
