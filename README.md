# IBM boot logos for UEFI PCs

These are retro IBM boot logos, plus the tools to put them into AMI Aptio UEFI firmware. They've been tested on ThinkPads and ASUS desktop boards.

![ThinkPad X210Ai booting with the Eye-Bee-M logo](photos/thinkpad_x210ai_eye_bee_m.png)

*A ThinkPad X210Ai booting with Paul Rand's Eye-Bee-M rebus logo, flashed into its firmware.*

**Gallery:** https://syntaxapproval.github.io/ibm-boot-logos/ · **Help and troubleshooting:** [HELP.md](HELP.md)

## Logos

| Logo | Files | Notes |
|---|---|---|
| Eye-Bee-M | `logos/eye-bee-m/` (580×156, 1160×312, 672×378) | Paul Rand's 1981 rebus. The 580×156 version matches the X210Ai's stock logo size, and 1160×312 is an exact 2× scale for high-resolution screens. |
| IBM ThinkPad | `logos/ibm-thinkpad/ibm_thinkpad_672x378.bmp` | Tilted rainbow IBM with the ThinkPad wordmark |
| IBM 8-bar (Aptiva BIOS) | `logos/ibm-8bar-aptiva/ibm_8bar_672x378.bmp` | The real bitmap pulled from an IBM Aptiva 2137 BIOS (Acer R05-E0), drawn 1:1 |
| Aptiva 2139 boot screen | `logos/aptiva-2139/aptiva2139_672x378.bmp` | A rebuild of the Aptiva 2139-E5Y boot screen, made using the genuine IBM bitmap |
| IBM navy | `logos/ibm-navy/ibm_navy_672x378.bmp` | 8-bar IBM on navy |

All of these are 24-bit uncompressed BMPs, and each one has a `.png` preview next to it.

## Machines

| Machine | Status | Notes |
|---|---|---|
| ThinkPad X210Ai | ✅ done | AMI Aptio V (Meteor Lake) with Boot Guard on. The logo file is outside the Boot Guard–protected area. I dumped the flash with flashrom, patched it, and flashed only the changed 4 KB blocks (`flashrom -l layout -i logo`). The stock logo is 580×156. |
| ASUS PRIME B360-PLUS / B360M-A | ✅ done | Flashed with Intel FPT, writing only the logo window. The stock logo is 672×378. Eye-Bee-M is about 11 KB too big for the B360-PLUS logo space. The other logos fit. |
| ThinkPad T530 | 🔜 coming soon | |
| ThinkPad T480s | 🔜 coming soon | |

## Tools

- **`tools/patch_ami_logo.py`**: the general patcher. It works on a full SPI dump or a BIOS-region dump from any AMI Aptio board. It:
  1. finds the AMI logo FFS file (`7BB28B99-61BB-11D5-9A5D-0090273FC14D`)
  2. re-packs your BMP with the stock LZMA settings
  3. recomputes the FFS header checksum and pads, so every other firmware file stays where it was
  4. verifies the result
  5. writes the patched image, a small 4K-aligned `.window` file and a flashrom `.layout` file, and prints ready-to-use FPT and flashrom commands

  On the B360-PLUS it gives byte-identical output to the board-specific script.
  ```
  python -I tools/patch_ami_logo.py spi_dump.bin logos/eye-bee-m/eye_bee_m_580x156.bmp patched.bin
  python -I tools/patch_ami_logo.py region_dump.bin logos/ibm-navy/ibm_navy_672x378.bmp patched.bin --base 0x300000
  ```
- **`tools/patch_logo.py`**: the original script for the ASUS PRIME B360-PLUS BIOS 3101 only.
- **`tools/acer_unpack.py`** and **`tools/acer_logo.py`**: unpack 1997-era Acer/IBM Aptiva BIOS images and decode their `@DAT` RLE logos. This is how the original IBM 8-bar bitmap was recovered.

> ⚠️ Flashing firmware can brick a board. Before you change anything, dump and keep a backup of your own flash. On Boot Guard machines, check that the logo volume isn't covered by the IBB hash. Intel FPT and vendor flashing tools aren't redistributable, so they aren't included here.

**If you'd rather not flash anything:** HackBGRT replaces the logo Windows shows while it boots. It never touches the firmware.

## Legal

IBM, ThinkPad and Aptiva are trademarks of IBM and/or Lenovo. This is an unofficial fan project for personal, nostalgic use, and no endorsement is implied. The Eye-Bee-M artwork is by Paul Rand, via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Eye_Bee_M_Rebus_Logo.jpg) (public domain, trademarked). The scripts are released under the MIT License (see `LICENSE`).
