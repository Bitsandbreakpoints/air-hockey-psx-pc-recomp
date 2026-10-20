# Air Hockey: PC port (source)

A native Windows version of the PlayStation game *Air Hockey* (SLUS-01467,
SUCCESS / Mud Duck Productions, 2002). No emulator and no BIOS: the game's
own MIPS code is translated to C (static recompilation) and compiled for
x86, and Sony's libraries for graphics, CD-ROM, controllers and interrupts
are replaced by PC code.

The whole game plays: title, options, player select, the story scenes with
their dialogue, the matches and the ranking, with music and sound effects,
keyboard or XInput controllers (two players) and graphics at up to 4× the
internal resolution with precise vertices and smooth 3D textures, bilinear,
CRT or soft-TV filters. F1 (or Select+Start) pauses and opens a menu with
the settings and Resume, Back to launcher and Quit game; Tab fast-forwards
and Esc goes back to the launcher.

## You need your own disc
Neither the source nor the program contains graphics, sound, text or other
data from the game. Everything is read from your own disc of *Air Hockey
(USA)* (`.chd`, `.bin`/`.cue` or `.iso`) while the game runs. Choose it in
the launcher with CHOOSE DISC or drop the file on the window; the launcher
checks that it is the release the port was made from.

The build needs the disc too: the code is translated from the disc's
programs (`SLUS_014.67`, `MAIN.EXE`), and the translated code only ever
lands in `build/`, never in the source.

## Building
Needs Windows 10/11 and Python 3.
```bat
build.bat --disc "D:\Games\Air Hockey (USA).chd"
```
The first time, the compiler (llvm-mingw) and ninja are downloaded to
`tools/` (SHA256-checked). The disc's path is remembered, so `build.bat` is
enough after that. The result is `build/air_hockey.exe`. `run.bat` builds
and starts it; `build.bat --debug` makes a debug build. A disc image named
`Air Hockey*.chd` (or `.cue`, `.iso`) in this folder is found without
`--disc`.

A package for players: `python tools/package.py` makes
`build/package/air-hockey-pc.zip` (exe, README.txt, licences), after
checking that the exe contains nothing from the disc.

## How it works
| Part | Where | What |
|---|---|---|
| Recompiler | `recomp/` | Python: MIPS R3000A + GTE → C, one C function per function of the game, jump tables as `switch` |
| Configuration | `recomp/config/*.cfg` | per program: its SHA1, which of Sony's functions are replaced (`hle`) |
| Run-time | `src/runtime/` | CPU registers, memory, interrupts/VSync, the BIOS functions, the GPU/CD/controller replacements, the hardware registers of the sound |
| PS1 hardware in software | `src/psx/` | GPU (with a high-resolution copy), GTE, SPU |
| PC | `src/platform/`, `src/launcher/`, `src/disc/` | window, Direct3D 11, XInput, XAudio2, launcher, disc reader (bin/cue/chd/iso) |

The recompiler follows the code from the entry point: every `jal` target,
function pointers built with `lui`/`addiu` or stored in the data, and the
config's `func` lines. Delay slots run before the jump (the condition is
computed first), backward jumps check for interrupts, and jumps through a
register become a `switch` when their table is found (its entries are read
from PS1 memory at run time), otherwise a call by address.

The game's RAM lies at its own address (0x80000000) in a 32-bit process, so
a PS1 address is a plain pointer. Interrupts are taken where the code checks
for them (loops) and in VSync(); the game's callbacks run with the registers
saved around them. The sound libraries (LIBSND/LIBSPU) run as recompiled
code against an emulated SPU. The dialogue text, which the original prints
with the BIOS's font, is drawn with a Windows font.

## Tests
None of the tests use the global keyboard, so the PC can be used while they
run.

- `python tests/play.py <name> <frames> "<buttons>" <frames…>`: a scripted
  run with a montage of pictures in `build/test/<name>/`.
- `python tests/compare_duckstation.py`: the same screens in the port and in
  the original game in DuckStation (put a portable DuckStation in
  `tools/emulator/duckstation` with a BIOS in its `bios` folder), with
  difference pictures.
- `python tests/window_shot.py build/test/launcher.png`: the launcher's
  window.

Debugging with environment variables: `AH_AUTOSTART=1`, `AH_QUIT=1`,
`AH_INPUT=<frame>[-<last>]:<button>,…`, `AH_LEAVE=<frame>`,
`AH_VRAM_DUMP=<frame>,…`, `AH_WAV_DUMP=<file>`, `AH_MUTE=1`, `AH_NATIVE=1`,
`AH_FAST=1`, `AH_SPU_TRACE=1` (see `src/main_pc.cpp`).

See `THIRD_PARTY.md` for the licences.
