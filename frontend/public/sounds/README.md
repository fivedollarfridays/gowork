# GoWork Wall — Sound Assets (T1.57)

This directory hosts the audio cues used by the Wall narrative.
At W1 commit time, every file is a **104-byte silent MPEG-1 Layer III
placeholder** — they exist so `sound.ts` can resolve the asset URLs
without 404s in dev. Real audio is sourced in W2/W3.

## Asset Manifest

| File                    | SoundId            | Used by (sprint)                |
|-------------------------|--------------------|---------------------------------|
| `footstep.mp3`          | `footstep`         | W2 Chapter 4 — Carlos walking   |
| `paper-rustle.mp3`      | `paper-rustle`     | W3 Chapter 6 — document review  |
| `calculator-click.mp3`  | `calculator-click` | W3 Chapter 7 — childcare math   |
| `chime.mp3`             | `chime`            | W4 idle-state nudge             |
| `wind-ambient.mp3`      | `wind-ambient`     | W2 Chapter 1 — overhead camera  |

## Replacement requirements

When swapping in real audio:

1. **Format** — MP3, 44.1 kHz, mono.
2. **Bitrate** — 96–128 kbps.
3. **Size budget** — **<50 KB per file.** Hard cap. Larger means trimmed
   to fit. Footsteps/click/chime should be sub-1-second; wind-ambient is
   the only file that may run longer (loop-friendly, <50 KB still).
4. **License** — must be CC0 / public domain or properly attributed
   (kept in `frontend/public/sounds/ATTRIBUTIONS.md` when added).
5. **Loudness** — peak normalize to −3 dBFS so the `setVolume()` 0..1
   master maps linearly to perceived loudness.

## Why silent placeholders?

- Default app state is **muted** (`gowork.muted` localStorage default
  = `true`). The placeholder MP3 is loaded by Howler only after the user
  unmutes — so most users never hit the network for audio at all.
- During dev, the silent placeholder lets `sound.ts` mount + lazy-load
  without console errors.
- Replacing a placeholder with a real audio file in the same name is
  zero-code-change.

## Adding new sound IDs

1. Add the new id to the `SoundId` union in `frontend/src/lib/wall/sound.ts`.
2. Add the file path to `SOUND_FILES`.
3. Drop the placeholder MP3 in this directory.
4. Update this manifest table.
