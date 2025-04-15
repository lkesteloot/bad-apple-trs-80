# Bad Apple TRS-80

This repo takes frames from the famous Bad Apple music video
and converts them to assembly language code for the TRS-80
Model III that will show the video. Currently only 490 frames
will fit in 48k of RAM (about 100 bytes each). There's no audio.

To use this, run (on a Mac):

```sh
python3 process_image.py | pbcopy
```

and paste into the [My TRS-80 IDE](https://www.my-trs-80.com/ide/)
webapp.

![Animation](animation.mov)

