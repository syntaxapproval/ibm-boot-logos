"""Replace the boot logo in an AMI Aptio (UEFI) firmware image.

Works on a full SPI dump or on a BIOS-region dump. Nothing is written to flash.

    python -I patch_ami_logo.py <dump.bin> <logo.bmp> <out.bin> [--base 0xADDR]

What it does
  * Finds the AMI logo FFS file (GUID 7BB28B99-61BB-11D5-9A5D-0090273FC14D). It has
    to be an LZMA GUIDed section that holds a RAW section (the BMP) and a UI section.
  * Re-packs your 24-bit BMP with the same LZMA settings and the same UI name. It
    recomputes the FFS header checksum and fills the leftover space with a pad
    file, so every other firmware file stays at exactly the same offset.
  * Verifies the result, then writes:
      out.bin          the whole patched image
      out.bin.window   only the changed 4 KB-aligned blocks (the part to flash)
      out.bin.layout   a flashrom layout file for that window (region name "logo")
    --base is the flash address of byte 0 of <dump.bin>. Use 0 for a full SPI dump
    (the default), or the BIOS region start for a region dump (for example 0x300000
    on the ASUS B360 boards). It only changes the addresses that get printed.

Before you flash
  * Keep your original dump somewhere safe.
  * Boot Guard / verified boot: check that the logo volume is NOT covered by the IBB
    hash. On the ThinkPad X210Ai (Meteor Lake, Boot Guard on) it wasn't covered.
    On a board where it is covered, a patched logo will stop the board booting.
  * Stock AMI decoders accept the LZMA end marker this script writes. Some EDK2-based
    builds don't. If the logo comes out blank, that is the first thing to check.
  * The new BMP must compress to fit in the old file's space. Flat colours
    compress best. A smaller image size also helps.

Tested on: ASUS PRIME B360-PLUS BIOS 3101 (the output is byte-identical to tools/patch_logo.py).
The same method was used on the ThinkPad X210Ai (AMI Aptio V, full SPI dump, flashed with flashrom -l layout -i logo).
"""
import sys, lzma, uuid, struct, argparse

LOGO_GUID = uuid.UUID('7BB28B99-61BB-11D5-9A5D-0090273FC14D').bytes_le
LZMA_GUID = uuid.UUID('EE4E5898-3914-4259-9D6E-DC7BD79403CF').bytes_le
PAD_GUID = b'\xff' * 16

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('dump'); ap.add_argument('bmp'); ap.add_argument('out')
ap.add_argument('--base', type=lambda s: int(s, 0), default=0, help='flash address of byte 0 of the dump')
a = ap.parse_args()

dump = bytearray(open(a.dump, 'rb').read())
bmp = open(a.bmp, 'rb').read()
if bmp[:2] != b'BM':
    sys.exit('not a BMP file')
w, h = struct.unpack_from('<ii', bmp, 18); bpp, comp = struct.unpack_from('<HI', bmp, 28)
if bpp != 24 or comp != 0:
    sys.exit(f'BMP must be 24-bit uncompressed (got {bpp}-bit, compression {comp})')
print(f'logo: {w}x{abs(h)} 24-bit, {len(bmp)} bytes')

hits = []
i = dump.find(LOGO_GUID)
while i >= 0:
    # a real FFS header: type 0x02 (freeform), state byte 0xF8, an LZMA GUIDed section right after it
    if dump[i + 18] == 0x02 and dump[i + 23] == 0xF8 and dump[i + 24 + 4:i + 24 + 20] == LZMA_GUID:
        hits.append(i)
    i = dump.find(LOGO_GUID, i + 1)
if len(hits) != 1:
    sys.exit(f'expected exactly one LZMA logo FFS file, found {len(hits)} at {[hex(x) for x in hits]} - not patching')
f = hits[0]
print(f'logo FFS at file offset 0x{f:X} (flash 0x{f + a.base:X})')

old_size = int.from_bytes(dump[f + 20:f + 23], 'little')
attr = dump[f + 19]
if attr != 0x00:
    sys.exit(f'FFS attributes 0x{attr:02X} not supported (expected 0x00) - not patching')
nxt = (f + old_size + 7) & ~7
avail = nxt - f
hdr_old = bytes(dump[f:f + 24])

so = f + 24
old_sec_hdr = bytes(dump[so:so + 24])
data_off = int.from_bytes(old_sec_hdr[20:22], 'little')
old_stream = bytes(dump[so + data_off:so + int.from_bytes(old_sec_hdr[:3], 'little')])
props = old_stream[:5]
try:
    old_inner = lzma.decompress(old_stream[:5] + b'\xff' * 8 + old_stream[13:], format=lzma.FORMAT_ALONE)
except lzma.LZMAError:
    # stock stream without an end marker: decompress with the known size instead
    dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[lzma._decode_filter_properties(lzma.FILTER_LZMA1, props)])
    old_inner = dec.decompress(old_stream[13:], max_length=int.from_bytes(old_stream[5:13], 'little'))
raw_len = int.from_bytes(old_inner[:3], 'little')
if old_inner[3] != 0x19:
    sys.exit('first inner section is not RAW - unexpected layout, not patching')
ui = old_inner[(raw_len + 3) & ~3:]
if ui[3] != 0x15:
    sys.exit('second inner section is not UI - unexpected layout, not patching')
old_bmp = old_inner[4:raw_len]
if old_bmp[:2] == b'BM':
    ow, oh = struct.unpack_from('<ii', old_bmp, 18)
    print(f'stock logo: {ow}x{abs(oh)}, UI name "{ui[4:].decode("utf-16-le", "replace").rstrip(chr(0))}"')

raw = (len(bmp) + 4).to_bytes(3, 'little') + b'\x19' + bmp
inner = raw + b'\x00' * (((len(raw) + 3) & ~3) - len(raw)) + ui

lc_lp_pb = props[0]
lc, rest = lc_lp_pb % 9, lc_lp_pb // 9
lp, pb = rest % 5, rest // 5
dict_size = int.from_bytes(props[1:5], 'little')
filt = [{'id': lzma.FILTER_LZMA1, 'dict_size': dict_size, 'lc': lc, 'lp': lp, 'pb': pb, 'preset': 9 | lzma.PRESET_EXTREME}]
alone = lzma.compress(inner, format=lzma.FORMAT_ALONE, filters=filt)
assert alone[:5] == props, (alone[:5].hex(), props.hex())
comp = alone[:5] + len(inner).to_bytes(8, 'little') + alone[13:]
assert lzma.decompress(alone, format=lzma.FORMAT_ALONE) == inner

sec = bytearray(old_sec_hdr)
sec_len = 24 + len(comp)
sec[0:3] = sec_len.to_bytes(3, 'little')
sec = bytes(sec) + comp

ffs_size = 24 + len(sec)
ffs_alloc = (ffs_size + 7) & ~7
print(f'new FFS {ffs_size} bytes, space available {avail} (stock {old_size})')
if ffs_alloc > avail:
    sys.exit(f'New logo is {ffs_alloc - avail} bytes too big for the existing space - not patching. '
             'Use a smaller or flatter image.')

def ffs_header(guid, ftype, attr, size):
    hd = bytearray(guid + b'\x00\x00' + bytes([ftype, attr]) + size.to_bytes(3, 'little') + b'\x00')
    hd[17] = 0xAA
    s = sum(hd[:16]) + hd[18] + hd[19] + sum(hd[20:23])
    hd[16] = (-s) & 0xFF
    hd[23] = 0xF8
    return bytes(hd)

if ffs_header(LOGO_GUID, 0x02, 0x00, old_size) != hdr_old:
    sys.exit('rebuilding the stock FFS header did not reproduce it - checksum scheme differs, not patching')

block = ffs_header(LOGO_GUID, 0x02, 0x00, ffs_size) + sec + b'\xff' * (ffs_alloc - ffs_size)
gap = avail - ffs_alloc
if gap:
    if gap < 24:
        sys.exit(f'leftover gap {gap} bytes is too small for a pad file - not patching')
    block += ffs_header(PAD_GUID, 0xF0, 0x00, gap) + b'\xff' * (gap - 24)
assert len(block) == avail
out = bytearray(dump)
out[f:nxt] = block

changed = [i for i in range(f, nxt) if out[i] != dump[i]]
if not changed:
    sys.exit('the new logo is identical to the stock one - nothing to do')
lo, hi = changed[0], changed[-1]
assert out[:f] == dump[:f] and out[nxt:] == dump[nxt:]
blk_lo, blk_hi = lo & ~0xFFF, (hi | 0xFFF) + 1
stored = bytes(out[so + data_off:so + sec_len])
assert lzma.decompress(stored[:5] + b'\xff' * 8 + stored[13:], format=lzma.FORMAT_ALONE)[4:4 + len(bmp)] == bmp

open(a.out, 'wb').write(out)
open(a.out + '.window', 'wb').write(out[blk_lo:blk_hi])
open(a.out + '.layout', 'w').write(f'{blk_lo + a.base:08x}:{blk_hi + a.base - 1:08x} logo\n')
print(f'{len(changed)} bytes changed; everything outside the logo file is untouched')
print(f'write window: flash 0x{blk_lo + a.base:X}, length 0x{blk_hi - blk_lo:X}')
print(f'  FPT:      fptw64 -f {a.out}.window -a 0x{blk_lo + a.base:X} -l 0x{blk_hi - blk_lo:X}')
print(f'  flashrom: flashrom -p internal -l {a.out}.layout -i logo -w {a.out}   (full-SPI dumps, --base 0)')
print('verified: the new section decompresses back to your BMP')
