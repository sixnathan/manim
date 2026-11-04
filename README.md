# Stewart chapter 15 — the geometry of multiple integrals

The revised film is an original **Manim animation** covering Stewart’s chapter 15, Multiple Integrals. It uses growing columns, moving cross sections, integration strips, a grid bending into polar coordinates, lifted surface patches, spherical shell blocks, and a deformed coordinate grid to motivate the Jacobian.

Section numbering follows *Calculus: Early Transcendentals*, eighth edition. The user’s edition has not been confirmed. This is a conceptual chapter guide with selected worked examples, rather than a treatment of every exercise.

## Watch on a Mac

After cloning or pulling this repository, run these commands from the repository folder:

```bash
git pull origin main
open output/chapter15_multiple_integrals.mp4
```

To sample the opening before watching the full film:

```bash
open output/chapter15_preview.mp4
```

For the local player with section navigation:

```bash
open output/index.html
```

Watching needs no Python, Manim, or other project dependencies. Captions are available as an optional embedded subtitle track, SRT, and WebVTT. Narration is synthetic (`en-US-AndrewNeural`) and is synchronized to individual visual passages; caption sentences are paced within those passages.

## Editable source

- `v2/film.py`: actual Manim scenes and editable vector equations.
- `v2/script.py`: original narration in short visual passages.
- `v2/audio.py`: narration generation and duration measurements.
- `v2/assemble.py`: final video, section metadata, captions, transcript, and player.
- `v2/environment.yml`: reproducible Manim environment specification.
- `output/`: the watchable MP4, opening preview, player, storyboard, captions, and transcript.
- `assets/references/`: unchanged downloaded reference PDFs.

The earlier prototype’s `lesson.py`, `render.py`, and `package.py` are retained for reference. The current film is produced by the `v2/` sources.

## Render locally

Use the dependencies in `v2/environment.yml` (Manim Community 0.22.1, Matplotlib 3.11.2, and FFmpeg). The existing local environment is `.manim-env/`. Native dependencies, caches, and tools for this build are entirely inside this repository directory and are excluded from Git.

Narration generation also needs `edge-tts` from `requirements.txt`; the existing `.venv/` provides it. Only this generation step needs internet access. It sends the original narration text to Microsoft Edge TTS.

```bash
.venv/bin/python v2/audio.py
PATH="$PWD/.manim-env/bin:$PATH" XDG_CACHE_HOME="$PWD/.cache" \
  .manim-env/bin/manim -qh --fps 30 --media_dir v2/media \
  v2/film.py Volume Slices Bounds Polar Density SurfaceArea Solids Spherical Jacobian
.manim-env/bin/python v2/assemble.py
```

Intermediate renders, native environments, and narration MP3s are excluded from Git. The finished MP4 is committed directly and can be watched after an ordinary clone or pull. Equations are editable SVG vector paths generated with Computer Modern math fonts; no system LaTeX installation is needed.

## Sources

- [University of Minnesota: Stewart eighth-edition contents](https://advise.chem.umn.edu/sites/advise.chem.umn.edu/files/files/math_1271-1272-2263_text_toc_stewart_calculus_early_transcendentals_8th_ed.pdf): section alignment.
- [MIT OpenCourseWare: Gilbert Strang, Calculus, chapter 14, Multiple Integrals](https://ocw.mit.edu/courses/res-18-001-calculus-fall-2023/mitres_18_001_f17_ch14.pdf): downloaded as `assets/references/mit_strang_multiple_integrals.pdf`. Its chapter number belongs to Strang’s book; the topic corresponds to Stewart chapter 15.
- [MIT OpenCourseWare, 18.02, Fall 2007: Changing Variables in Multiple Integrals](https://ocw.mit.edu/courses/18-02-multivariable-calculus-fall-2007/05f51f37ac3bb5801af56e6879728f68_multipl_integrls.pdf): downloaded as `assets/references/mit_change_of_variables.pdf`.
- [MIT: Determining the Area or Volume Element](https://ocw.mit.edu/ans7870/18/18.013a/textbook/HTML/chapter31/section04.html): supplemental reference for determinant geometry.

Reference PDFs retain their original rights and attribution; see [MIT OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/). The film’s diagrams, prose, animations, and example presentations are original. The project is unaffiliated with 3Blue1Brown, Stewart, MIT, or Cengage.
