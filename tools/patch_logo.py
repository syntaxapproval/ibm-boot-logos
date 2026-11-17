"""Replace the AMI logo FFS in a BIOS-region dump (ASUS PRIME B360-PLUS 3101).
Usage: python -I patch_logo.py <region_dump.bin> <new_logo.bmp> <out.bin>
Writes nothing to flash. Keeps every other byte identical and the next file at the same offset."""
import sys, lzma, uuid, struct

REGION_BASE = 0x300000
LOGO_GUID = uuid.UUID('7BB28B99-61BB-11D5-9A5D-0090273FC14D').bytes_le
LZMA_GUID = uuid.UUID('ee4e5898-3914-4259-9d6e-dc7bd79403cf').bytes_le
PAD_GUID = b'\xff' * 16

dump = bytearray(open(sys.argv[1], 'rb').read())
bmp = open(sys.argv[2], 'rb').read()
assert bmp[:2] == b'BM'
w, h, bpp = struct.unpack_from('<iiH', bmp, 18)[0], struct.unpack_from('<i', bmp, 22)[0], struct.unpack_from('<H', bmp, 28)[0]
assert (w, h, bpp) == (672, 378, 24), (w, h, bpp)

f = dump.find(LOGO_GUID)
assert f == 0x111120 and dump.find(LOGO_GUID, f + 1) == -1, hex(f)
old_size = int.from_bytes(dump[f + 20:f + 23], 'little')
nxt = (f + old_size + 7) & ~7
avail = nxt - f
hdr_old = bytes(dump[f:f + 24])
assert dump[f + 18] == 0x02 and dump[f + 19] == 0x00 and dump[f + 23] == 0xF8

# --- inner sections (decompressed payload): RAW(BMP) + UI("Logo")
so = f + 24
old_sec_hdr = bytes(dump[so:so + 24])
assert old_sec_hdr[3] == 0x02 and old_sec_hdr[4:20] == LZMA_GUID
data_off = int.from_bytes(old_sec_hdr[20:22], 'little')
old_inner = lzma.decompress(bytes(dump[so + data_off:so + int.from_bytes(old_sec_hdr[:3], 'little')]), format=lzma.FORMAT_ALONE)
raw_len = int.from_bytes(old_inner[:3], 'little')
ui = old_inner[(raw_len + 3) & ~3:]
assert old_inner[3] == 0x19 and ui[3] == 0x15

raw = (len(bmp) + 4).to_bytes(3, 'little') + b'\x19' + bmp
inner = raw + b'\x00' * (((len(raw) + 3) & ~3) - len(raw)) + ui

# --- LZMA with stock props (lc3 lp0 pb2, dict 16MB) and an explicit size header
filt = [{'id': lzma.FILTER_LZMA1, 'dict_size': 1 << 24, 'lc': 3, 'lp': 0, 'pb': 2, 'preset': 9 | lzma.PRESET_EXTREME}]
alone = lzma.compress(inner, format=lzma.FORMAT_ALONE, filters=filt)
assert alone[:5] == bytes([0x5D]) + (1 << 24).to_bytes(4, 'little'), alone[:5].hex()
# replace "unknown size" (-1) with the real size, like the stock section; stream keeps its end marker
comp = alone[:5] + len(inner).to_bytes(8, 'little') + alone[13:]
# liblzma refuses "known size + end marker"; the LZMA SDK decoder used by UEFI accepts it.
# Verify the payload through the unknown-size form, which is byte-identical apart from the size field.
assert lzma.decompress(alone, format=lzma.FORMAT_ALONE) == inner
assert comp[13:] == alone[13:]

sec = bytearray(old_sec_hdr)
sec_len = 24 + len(comp)
sec[0:3] = sec_len.to_bytes(3, 'little')
sec = bytes(sec) + comp

ffs_size = 24 + len(sec)
ffs_alloc = (ffs_size + 7) & ~7
print(f"new FFS {ffs_size} bytes, space available {avail}, old {old_size}")
if ffs_alloc > avail:
    sys.exit("New logo does not fit in the existing space - not patching.")

def ffs_header(guid, ftype, attr, size):
    hd = bytearray(guid + b'\x00\x00' + bytes([ftype, attr]) + size.to_bytes(3, 'little') + b'\x00')
    hd[17] = 0xAA                         # file checksum when FFS_ATTRIB_CHECKSUM is clear
    s = sum(hd[:16]) + hd[18] + hd[19] + sum(hd[20:23])   # excludes State and File checksum
    hd[16] = (-s) & 0xFF
    hd[23] = 0xF8                         # state: header+data valid (erase polarity 1)
    return bytes(hd)

new_hdr = ffs_header(LOGO_GUID, 0x02, 0x00, ffs_size)
# sanity: rebuilding the ORIGINAL header the same way must give identical bytes
assert ffs_header(LOGO_GUID, 0x02, 0x00, old_size) == hdr_old, "header checksum method mismatch"

block = new_hdr + sec + b'\xff' * (ffs_alloc - ffs_size)
gap = avail - ffs_alloc
if gap:
    assert gap >= 24, f"gap {gap} too small for a pad file"
    block += ffs_header(PAD_GUID, 0xF0, 0x00, gap) + b'\xff' * (gap - 24)
assert len(block) == avail
out = bytearray(dump)
out[f:nxt] = block
open(sys.argv[3], 'wb').write(out)

# --- verification
assert len(out) == len(dump)
changed = [i for i in range(len(dump)) if out[i] != dump[i]]
lo, hi = min(changed), max(changed)
print(f"changed bytes {len(changed)} within region 0x{lo:x}-0x{hi:x} (flash 0x{lo+REGION_BASE:x}-0x{hi+REGION_BASE:x})")
assert f <= lo and hi < nxt
blk_lo, blk_hi = lo & ~0xFFF, (hi | 0xFFF) + 1
print(f"4K-aligned write window: flash 0x{blk_lo+REGION_BASE:X}, length 0x{blk_hi-blk_lo:X}")
open(sys.argv[3] + '.window', 'wb').write(out[blk_lo:blk_hi])
stored = bytes(out[so + data_off:so + sec_len])
dec = lzma.decompress(stored[:5] + b'\xff' * 8 + stored[13:], format=lzma.FORMAT_ALONE)
assert dec == inner and int.from_bytes(stored[5:13], 'little') == len(inner)
assert dec[4:4 + len(bmp)] == bmp
print("verified: decompresses to new BMP, next file untouched at", hex(nxt))
