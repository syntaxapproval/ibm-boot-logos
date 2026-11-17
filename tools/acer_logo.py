"""Decode Acer '@DAT' RLE images: header ... u16 a, u16 b, u16 datalen, 16x3 VGA palette (6-bit), then bytes (count-1)<<4 | color."""
import sys, struct, zlib, os
def png(path, w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb[y*w*3:(y+1)*w*3]) for y in range(h))
    ch = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))
def decode_at(d, o):
    # o points at '@DAT'
    a, b, n = struct.unpack_from('<HHH', d, o + 8)
    pal = [tuple(c * 255 // 63 for c in d[o+14+i*3:o+17+i*3]) for i in range(16)]
    data = d[o+62:o+62+n]
    pix = bytearray()
    for byte in data: pix += bytes([byte & 15]) * ((byte >> 4) + 1)
    return a, b, n, pal, pix, o + 62 + n
d = open(sys.argv[1], 'rb').read(); outdir = sys.argv[2]
o = d.find(b'@DAT'); k = 0
while o >= 0:
    a, b, n, pal, pix, end = decode_at(d, o)
    print(f"@DAT at 0x{o:x}: a={a} b={b} datalen={n} pixels={len(pix)}")
    for w in (560, 640, 520, 400, 200, 100, 80, 64, 48, 32, 24, 16):
        if len(pix) % w == 0 and 8 <= len(pix)//w <= 480:
            h = len(pix)//w; rgb = bytearray()
            for v in pix: rgb += bytes(pal[v])
            path = os.path.join(outdir, f"acer_logo_{k}_{w}x{h}.png"); png(path, w, h, rgb); print("   wrote", path); break
    k += 1; o = d.find(b'@DAT', end)
