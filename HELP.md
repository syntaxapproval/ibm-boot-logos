# Help

## Which file do I need?

- **Logo for a UEFI board or a Windows boot-logo tool:** use the `.bmp` from the logo's folder in `logos/`. Every BMP is 672×378, 24-bit and uncompressed.
- **Just looking or sharing:** use the `.png` previews.
- **Boot screens** (the `logos/` folders with five sizes): the `_672x378.bmp` is the 24-bit file for AMI firmware. The PNGs (640×480, 640×360, 1280×960 and 1920×1080) are for other firmware, boot-logo tools or wallpapers. Pick the size closest to your screen's native resolution.
- **ThinkPads with Lenovo's BIOS updater (T430/T530 era):** the update package can apply a custom start-up image. Its `BIOS_LOGO.TXT` gives the limits: `LOGO1` less than 640×480, `LOGO2` less than 1366×768, 30 KB or less each, BMP/JPG/GIF, placed next to `WINUPTP.EXE`. A ready-made T530 kit is in `logos/thinkpad-bee-ibm-tilted/t530/`.

## The safe way: change the Windows boot logo only

Tools such as HackBGRT replace the logo Windows shows while it boots. They never touch the firmware, and you can undo them by uninstalling. If you're unsure which route to take, start here.

## The advanced way: change the firmware POST logo

1. **Back up first.** Dump your BIOS region and keep the file somewhere safe. Without a backup, you have nothing to roll back to.
2. Build a patched image. Use `tools/patch_ami_logo.py` for any AMI Aptio board, or `tools/patch_logo.py` for the ASUS B360-PLUS only:
   ```
   python -I tools/patch_ami_logo.py region_dump.bin logos/ibm-thinkpad/ibm_thinkpad_672x378.bmp patched.bin
   ```
   Along with `patched.bin`, this writes `patched.bin.window` and prints the flash address and length to use.
3. Flash only the window file at the address the script printed, using your board's flashing tool.
4. Fully power off the PC: shut down, switch off the power supply or unplug it, wait about 10 seconds, then boot.

`patch_ami_logo.py` refuses to patch if it cannot find exactly one logo file in the expected layout, or if the new logo is too big. `patch_logo.py` only runs on the **ASUS PRIME B360-PLUS, BIOS 3101**.

## Re-making the boot screens

`tools/ibm_screens.py` draws every boot screen from `tools/screen_assets/`. It needs Pillow and NumPy, plus the Windows fonts `timesbd.ttf` and `arial.ttf` for the ® marks.
```
python -I tools/ibm_screens.py tools/screen_assets out
```

## Troubleshooting

| Problem | What to try |
|---|---|
| `New logo does not fit in the existing space` | Use a simpler image. Flat colours and large solid areas compress best. |
| The logo is blank or the stock logo still shows | Your firmware's LZMA decoder may not accept an end marker. Re-encode without one (EDK2-style), or roll back from your backup. |
| The flash tool refuses to write (for example FPT error 167) | BIOS Lock or flash protection is on. Some boards let you turn it off temporarily. Turn it back on afterwards. |
| A ThinkPad shows a black screen where the logo should be | Set **Startup → Boot Mode** to **Quick**. **Diagnostic** replaces the splash with the POST text screen, so a perfectly good logo never appears. |
| A ThinkPad shows the stock logo after a custom one was applied | The wrong slot is active. **LOGO1** shows when **Restart → OS Optimized Defaults** is *Disabled*, **LOGO2** when it is *Enabled*. Supply both, or match the file to the setting. |
| The board won't POST | Flash your backup back. If that isn't possible, you'll need a hardware programmer or the board's BIOS FlashBack feature. |

## Credits

The logo extraction, rebuilds and patch tools were made with help from **Claude** (Anthropic).

IBM, ThinkPad and Aptiva are trademarks of IBM and/or Lenovo. This is an unofficial fan project.
