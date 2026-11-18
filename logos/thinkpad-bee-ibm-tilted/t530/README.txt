ThinkPad T530 custom start-up logo kit (ThinkPad x Rand bee, tilted IBM)

Lenovo's BIOS update package for the T530 (G4UJ41US, BIOS 2.77) has its own
custom-logo option, explained in its BIOS_LOGO.TXT. No FPT or hardware is needed.

  LOGO1.GIF  639x479, 13 KB   shown when "OS Optimized Defaults" is Disabled (must be less than 640x480)
  LOGO2.GIF  1360x766, 25 KB  shown when "OS Optimized Defaults" is Enabled (must be less than 1366x768)

Limits from BIOS_LOGO.TXT: 30 KB or less per file; BMP, JPG or GIF; named LOGO1.* / LOGO2.*.

1. Extract the Lenovo package (don't install it).
2. Copy LOGO1.GIF and LOGO2.GIF into the folder that contains WINUPTP.EXE.
3. Plug in AC power and charge the battery, then run WINUPTP.EXE. It needs .NET;
   chklogo.exe in the package checks the images. Run it from its own folder:
   a wrong working directory gives "Flash Module cannot be found".
4. In BIOS setup, set Startup -> Boot Mode to Quick. Diagnostic shows the POST
   text screen instead of the splash, which looks exactly like a failed logo.
   LOGO1 shows when Restart -> OS Optimized Defaults is Disabled, LOGO2 when
   it is Enabled.

Both GIFs are drawn directly at their size by tools/ibm_screens.py (the design
plus 7 blend shades against the background, 73 colours), not downscaled.
