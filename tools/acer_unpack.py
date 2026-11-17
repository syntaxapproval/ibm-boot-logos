"""Acer BIOS (1997) LZSS unpacker, format read from the BIOS's own decompressor:
   u16 out_len | 18 raw header bytes (copied to output) | LZSS stream:
   flag byte (LSB first, 0=literal), match = u16: pos = v>>4 (absolute, mod 4096 of output index), len = (v&15)+3"""
def unpack(src, off):
    n = src[off] | (src[off+1] << 8)
    out = bytearray(src[off+2:off+20]); i = off+20
    while len(out) < n:
        flags = src[i]; i += 1
        for b in range(8):
            if len(out) >= n: break
            if not (flags >> b) & 1:
                out.append(src[i]); i += 1
            else:
                v = src[i] | (src[i+1] << 8); i += 2
                pos, ln = v >> 4, (v & 15) + 3
                base = len(out)
                for k in range(ln):
                    # ring of 4096 aligned to output index
                    p = (base & ~0xFFF) + ((pos + k) & 0xFFF)
                    if p >= base + k: p -= 0x1000
                    out.append(out[p] if p >= 0 else 0)
    return bytes(out[:n]), i
if __name__ == '__main__':
    import sys
    src = open(sys.argv[1], 'rb').read()
    for off in sys.argv[2:]:
        o = int(off, 0); out, end = unpack(src, o)
        print(f"block @0x{o:x}: out {len(out)} bytes, consumed 0x{end-o:x}, head {out[:20]}")
        if out[:2] == b'\x55\xaa': print("   option ROM checksum:", sum(out[:out[2]*512]) % 256)
