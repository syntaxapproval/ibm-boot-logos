# IBM boot logos for UEFI PCs

These are retro IBM boot logos that replace the POST/BIOS splash screen on an AMI UEFI board. I used them on ASUS B360 motherboards, but any board that takes a 672×378 24-bit BMP logo can use them.

![ThinkPad X210Ai booting with the Eye-Bee-M logo](photos/thinkpad_x210ai_eye_bee_m.png)

*A ThinkPad X210Ai booting with Paul Rand's Eye-Bee-M rebus logo.*

**Gallery:** see `index.html`, or the GitHub Pages site for this repo. **Help and troubleshooting:** see [HELP.md](HELP.md).

| Logo | File | Notes |
|---|---|---|
| IBM ThinkPad | `logos/ibm-thinkpad/ibm_thinkpad_672x378.bmp` | Tilted rainbow IBM with the ThinkPad wordmark |
| IBM 8-bar (Aptiva BIOS) | `logos/ibm-8bar-aptiva/ibm_8bar_672x378.bmp` | The real bitmap pulled from an IBM Aptiva 2137 BIOS (Acer R05-E0), blue on black, drawn 1:1 |
| Aptiva 2139 boot screen | `logos/aptiva-2139/aptiva2139_672x378.bmp` | A rebuild of the Aptiva 2139-E5Y boot screen, made from photos using the genuine IBM bitmap |
| IBM navy | `logos/ibm-navy/ibm_navy_672x378.bmp` | 8-bar IBM on navy |

Every `.bmp` is **672×378, 24-bit, uncompressed**, which is the size and format the stock ASUS logo uses. Each one has a `.png` preview next to it.

## Using them

**Easiest (no flashing):** many boards accept a custom boot logo through a vendor tool, or through a Windows-side tool such as HackBGRT. That changes the logo Windows shows while it boots. It does not change the firmware.

**Firmware logo (advanced, at your own risk):** `tools/patch_logo.py` swaps the AMI logo FFS file (`7BB28B99-61BB-11D5-9A5D-0090273FC14D`) inside a BIOS-region dump. It recompresses the logo with LZMA and adds a pad file so that every other firmware file stays at the same offset. The script verifies the result and writes:

- a full patched region image
- a small 4K-aligned `.window` file that you flash on its own

```
python -I tools/patch_logo.py region_dump.bin logos/ibm-thinkpad/ibm_thinkpad_672x378.bmp patched.bin
```

> ⚠️ The script has hard-coded offset checks for **ASUS PRIME B360-PLUS, BIOS 3101**. On any other board it refuses to run until you adapt it. Flashing firmware can brick a board. Before you change anything, dump and keep a backup of your own BIOS region. The tool I used for dumping and flashing was Intel FPT, which isn't redistributable, so it isn't included here. Some boards need BIOS Lock turned off before they accept the flash.

**Notes from doing this:**
- The logo usually has to fit in the space the original took up, so plain or flat images compress best.
- The decoder in some firmware handles an LZMA stream that ends with an end marker. On other firmware you need EDK2-style output with no end marker. If you get a blank logo after flashing, that difference is the first thing to check.

## Extra tools

- `tools/acer_unpack.py` unpacks the LZSS format in 1997-era Acer BIOS images, which were the basis for the IBM Aptiva BIOS.
- `tools/acer_logo.py` decodes the `@DAT` RLE logo images in those images. This is how the original IBM 8-bar bitmap was recovered.

## Legal

IBM, ThinkPad and Aptiva are trademarks of IBM and/or Lenovo. This is an unofficial fan project for personal, nostalgic use, and no endorsement is implied. The scripts are released under the MIT License (see `LICENSE`).
