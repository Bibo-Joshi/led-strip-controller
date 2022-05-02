# LED-Strip Controller

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Bibo-Joshi/led-strip-controller/main.svg)](https://results.pre-commit.ci/latest/github/Bibo-Joshi/led-strip-controller/main)

This repository provides a controller for RGB+Warm-White LED strips, tailored to my needs.
Simultaneously, I used it to try out some things that I haven't worked with before (more on that below).

## Main features

- Allows to control either RGB or RGBWW strips.
- Provides a restful API
- GUI available
  <details> <summary>Click to view demo</summary>

  ![Demo](demo.mp4)

  </details>

- Strong focus on setting alarms to wake up with the light going on slowly

## Limitations:

- Currently, only designed to set all LEDs to the same color.
- Adding, deleting & editing the alarm through the GUI is work in progress

## Extending

I've tried to make sure that the structure is easy to adapt to different use cases.
The following interface classes allow implementing custom functionality.

- `BasePersistence`: Interface class for persisting color values & alarms across restarts. Currently, an implementation via the `pickle` module is available.
- `BaseEffect`: Interface class for providing pre-defined sequences of colors. Currently, only `AlarmEffect` is available for the light alarm.
- `BaseBridge`: Interface class for communicating with the LED strip. A bridge based on the `RPI.GPIO` module is available. If `RPI.GPIO` is not installed, the current fallback is `MuteBridge` which just does nothing.

## Used Tools & Some Comments

This project uses the following tools/languages/packages:

- Python for the backend, specifically
  - [starlette](https://www.starlette.io/) for hosting the GUI
  - [fastapi](https://fastapi.tiangolo.com) for the API
  - [APScheduler](https://apscheduler.readthedocs.io/) for scheduling the alarms
  - [RPi.GPIO](https://sourceforge.net/projects/raspberry-gpio-python/) for an implementation of `BaseBridge`
- for the frontend
  - [Jinja2](https://palletsprojects.com/p/jinja/) templating
  - (Mostly) Vanilla JavaScript
  - Vanilla CSS
  - Vanilla HTML
  - [iro.js](https://iro.js.org) for the color pickers

I'm rather comfortable with Python and have already used `APScheduler` to some extent.
I've also played around with the others _a bit_, but not as much as in this project.
Specifically I have little experience with web development, which is why I wanted to try around a bit with _vanilla_ HTML, JS & CSS instead of diving into Vue/Angular/React.
As such, code & code structure are probably gruesome to look at for everyone who has some idea of it.
I warned you 😉.

## Used resources

As mentioned above, I don't have much experience with web development.
So it should come at no surprise that I borrowed heavily from existing resources.
This projects uses code from

- [This pen](https://codepen.io/jkantner/pen/xxXmVKw) for the fixed color picker (Copyright included in the corresponding file)
- [This pen](https://codepen.io/rakujira/pen/WZOeNq) for integrating `iro.js` into the GUI (Copyright included in the corresponding file)
- [This pen](https://codepen.io/jkantner/pen/XEzWGr) for the on-off toggles for the alarms (Copyright included in the corresponding file)
- [This pen](https://codepen.io/milanraring/pen/KKwRBQp) for the big on-off toggle (Copyright included in the corresponding file)
- [Mono icons](https://icons.mono.company) for some icons ([MIT License](https://github.com/mono-company/mono-icons/blob/master/LICENSE.md))

and draws inspiration from [the `iro.js` website](https://github.com/jaames/iro.js) for the overall layout of the GUI.

## Scope, Support, Stability & Contributing

I consider this mostly a private project for my personal usage (and education).
As such, I won't put particular effort in maintaining a stability policy.
I will also most likely not accept feature requests (until I like them myself) or offer support.
If you coded some extension of or fix for this project you're however welcome to send a pull request.
