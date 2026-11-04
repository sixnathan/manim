# The Geometry of Adding

An original animated guide to Stewart's chapter 15, **Multiple Integrals**.
Section numbers follow *Calculus: Early Transcendentals*, eighth edition; the user's edition is unconfirmed.

Open `output/index.html` for the local player, chapter navigation, transcript, source links, and practice questions. Or play `output/chapter15_multiple_integrals.mp4` directly.

The video develops double integrals, iterated integration, general regions and reversed bounds, polar area, mass and balance, probability density, surface area, triple integrals, cylindrical and spherical coordinates, and the Jacobian. It is a conceptual chapter guide with selected worked examples, rather than a replacement for every textbook example and exercise.

## Files

- `lesson.py`: original narration and mathematical formulas.
- `render.py`: editable animation, narration, caption, and video renderer.
- `package.py`: local player and transcript builder.
- `assets/audio/`: synthetic narration, one MP3 per scene.
- `assets/references/`: two downloaded MIT reference PDFs.
- `output/`: final video, individual scenes, storyboard, stills, captions, and chapter data.

## Rebuild

All dependencies are in `.venv/`; caches and temporary files are directed into `.cache/`. No system installations are required. The renderer uses Pillow and mathematical typesetting from Matplotlib, with the FFmpeg executable bundled inside the local Python environment. It does not require Manim or LaTeX.

```bash
.venv/bin/python render.py --audio
.venv/bin/python render.py --stills
.venv/bin/python render.py
.venv/bin/python package.py
```

Audio generation requires internet access to Microsoft Edge TTS and sends only the original narration text. The rendering and packaging steps work offline after audio exists. Existing `output/scene_XX.mp4` files are reused, so move the affected scene files aside before rebuilding edited scenes. Audio is likewise reused by scene name; move an affected narration MP3 aside after changing its script.

The captions are timed proportionally within each scene, not force-aligned word by word. They are burned into the picture and supplied as SRT, WebVTT, and an embedded MP4 subtitle track.

## Sources and attribution

- [University of Minnesota: Stewart eighth-edition contents](https://advise.chem.umn.edu/sites/advise.chem.umn.edu/files/files/math_1271-1272-2263_text_toc_stewart_calculus_early_transcendentals_8th_ed.pdf). Used to check section names and numbering. The direct download returned HTTP 403; the contents were verified through the web reader instead.
- [MIT OpenCourseWare: Gilbert Strang, Calculus, chapter 14](https://ocw.mit.edu/courses/res-18-001-calculus-fall-2023/mitres_18_001_f17_ch14.pdf). Downloaded unchanged as `assets/references/mit_strang_multiple_integrals.pdf`.
- [MIT OpenCourseWare, 18.02, Fall 2007: Changing Variables in Multiple Integrals](https://ocw.mit.edu/courses/18-02-multivariable-calculus-fall-2007/05f51f37ac3bb5801af56e6879728f68_multipl_integrls.pdf). Downloaded unchanged as `assets/references/mit_change_of_variables.pdf`.
- [MIT: Determining the Area or Volume Element](https://ocw.mit.edu/ans7870/18/18.013a/textbook/HTML/chapter31/section04.html). Supplemental check of determinant geometry.

Reference PDFs retain their original rights and attribution; see [MIT OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/). No textbook pages or third-party artwork are reproduced in the video. All video diagrams, prose, and example presentations are original. Synthetic narration uses `en-GB-RyanNeural`, with no voice imitation. The project is unaffiliated with 3Blue1Brown, Stewart, MIT, or Cengage.
