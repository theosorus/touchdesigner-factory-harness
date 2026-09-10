# Mouse rotation of the brain, inside the render window only.
#   left click + horizontal drag : turn around the brain
#   wheel                        : move closer or further away
# The eye height is fixed: it is deliberately not adjustable.
#
# A drag that starts over the control panel is ignored. Without that guard, moving a
# slider also rotated the brain.
#
# After a few seconds of no input, the camera resumes its automatic sweep between
# three-quarter and profile, and the manual offset fades out.
#
# This DAT writes camx / camy / camz into the cam_state Constant CHOP; cam_orbit's
# translate parameters do nothing but read those channels.

import math

DRAG_GAIN = 4.2              # radians per window width dragged
CAM_HEIGHT = 3.0             # fixed eye height
DIST_BASE = 7.4
DIST_MIN, DIST_MAX = 4.2, 13.0
IDLE_BEFORE_AUTO = 2.5       # seconds of idleness before the automatic sweep resumes
BLEND_SPEED = 0.55           # speed of the return to automatic
DECAY = 0.965                # decay of the manual offset once back on automatic

# Interaction state. Reset when this DAT reloads, which is harmless: the camera simply
# starts again from its automatic angle.
_state = {'az': 0.0, 'auto': 1.0, 'idle': 99.0, 'lastu': 0.0,
          'down': False, 'dragok': False, 'wheelref': None}


def onFrameStart(frame):
    comp = parent()                                  # the render stage
    out = comp.op('cam_state')
    ui = comp.parent().op('ui_control')               # the render window
    if out is None or ui is None:
        return

    panel = ui.op('panel_params')
    over_ui = float(ui.panel.inside) > 0.5
    over_panel = panel is not None and float(panel.panel.inside) > 0.5
    down = float(ui.panel.lselect) > 0.5 and over_ui
    u = float(ui.panel.u)

    dt = 1.0 / max(project.cookRate, 1.0)

    if down and not _state['down']:
        # Start of the drag: decide here, once and for all, whether this drag drives the
        # camera. A click that started on the panel never will, even if the cursor later
        # moves over the render.
        _state['dragok'] = not over_panel
        _state['lastu'] = u

    if down and _state['dragok']:
        _state['az'] += (u - _state['lastu']) * DRAG_GAIN
        _state['lastu'] = u
        _state['idle'] = 0.0
        _state['auto'] = 0.0
    else:
        _state['idle'] += dt
        if _state['idle'] > IDLE_BEFORE_AUTO:
            _state['auto'] = min(1.0, _state['auto'] + BLEND_SPEED * dt)
            if _state['auto'] >= 1.0:                # the manual offset decays
                _state['az'] *= DECAY
    _state['down'] = down

    # The wheel only acts while the cursor is over the render, never over the panel.
    # The panel's wheel value accumulates, so it is referenced against its first-seen
    # value; otherwise the distance starts pinned at its ceiling.
    raw_wheel = float(ui.panel.wheel)
    if _state['wheelref'] is None:
        _state['wheelref'] = raw_wheel
    if over_panel:
        _state['wheelref'] = raw_wheel               # ignore scrolling that happens elsewhere
    wheel = raw_wheel - _state['wheelref']

    # Automatic sweep between three-quarter and profile, damped while dragging.
    speed = comp.par.Orbitspeed.eval()
    swing = 0.35 * math.sin(absTime.seconds * speed * 0.55) * _state['auto']
    angle = 1.25 + swing + _state['az']
    dist = min(DIST_MAX, max(DIST_MIN, DIST_BASE - wheel * 1.5))

    out.par.const0value = dist * math.sin(angle)
    out.par.const1value = CAM_HEIGHT
    out.par.const2value = dist * math.cos(angle)
    return
