# klipper-bed-tramming
"Center-reference bed tramming for Klipper - manual bed leveling made easy(ish)"
# Klipper Bed Tramming Center

A center-reference bed tramming system for Klipper that allows manual bed leveling by probing a center reference point and comparing all screw positions against it. Originally designed for the Elegoo Neptune 4 Max but adaptable to other printers.

## Features

- **Center-reference leveling**: Probe center once, then compare all screws to that reference
- **Individual screw control**: Probe screws one at a time for iterative adjustments
- **Multiple samples with median**: 6 samples per probe with median calculation for accuracy
- **Clear adjustment instructions**: Shows whether to tighten/loosen and by how many turns
- **Automatic lift**: Z-axis lifts between samples and after probing for safety
- **Configurable parameters**: Screw pitch, sample count, lift height, and probe speed

## Why This Instead of SCREWS_TILT_CALCULATE?

While Klipper's built-in `SCREWS_TILT_CALCULATE` is excellent, this tool offers:
- More control over the workflow (probe screws in any order)
- Immediate re-probing of individual screws to verify adjustments
- Better for iterative fine-tuning
- Configurable screw positions without editing core configs

## Installation

1. **Copy the Python file:**
```bash
   wget -O ~/klipper/klippy/extras/bed_tramming_center.py https://raw.githubusercontent.com/YOUR_USERNAME/klipper-bed-tramming/main/bed_tramming_center.py
```

2. **Add configuration to printer.cfg:**
```ini
   [bed_tramming_center]
   screw_pitch: 0.8          # Thread pitch in mm (M4 = 0.8mm)
   samples: 6                 # Number of probe samples per position
   lift_height: 20.0          # mm to lift after probing
   probe_speed: 6000          # XY travel speed in mm/min
```

3. **Restart Klipper:**
```bash
   sudo service klipper restart
```

## Usage

### Basic Workflow

1. **Home the printer:**
```
   G28
```

2. **Establish center reference:**
```
   PROBE_CENTER
```

3. **Probe individual screws:**
```
   PROBE_SCREW_FL    # Front left
   PROBE_SCREW_FR    # Front right
   PROBE_SCREW_BL    # Back left
   PROBE_SCREW_BR    # Back right
   PROBE_SCREW_LM    # Left middle
   PROBE_SCREW_RM    # Right middle
```

4. **Adjust screws as indicated**

5. **Re-probe to verify:**
```
   PROBE_SCREW_FL    # Re-check the screw you just adjusted
```

### Example Output
```
Front Left Z=-0.850 (Center: -0.125, diff: -0.725mm)
Front Left: TIGHTEN (CW) 0.91 turns (-0.725mm high - lower bed)
```

This tells you:
- The probe measured -0.850mm at front left
- Center reference is -0.125mm
- Front left is 0.725mm too high
- Turn the screw clockwise ~0.91 turns to lower it

### Optional: Probe All Screws
```
PROBE_ALL_SCREWS
```

This probes all 6 screws in sequence and reports adjustments needed for each.

## Configuration

### Screw Positions

Default positions are for Neptune 4 Max (420x420mm bed):
- Center: X230 Y210
- Front Left: X45 Y10
- Front Right: X419 Y10
- Back Left: X45 Y400
- Back Right: X419 Y400
- Left Middle: X45 Y210
- Right Middle: X419 Y210

To customize for your printer, edit the `self.screw_positions` dictionary in the Python file.

### Screw Direction

On Neptune 4 Max:
- **TIGHTEN (CW)** = compress spring = **lower** bed
- **LOOSEN (CCW)** = extend spring = **raise** bed

If your printer is different, you may need to swap the instructions in the `_calculate_adjustment` method.

## Requirements

- Klipper firmware
- Probe configured in printer.cfg
- Tested on Klipper v0.10.0-530 (Neptune 4 Max) but should work on newer versions

## Troubleshooting

### "Probe triggered prior to movement"

The probe needs time to retract between samples. The code includes automatic 3mm retracts between samples, but if you still see this error, increase the retract distance in the `_probe_position` method.

### Positions are off the bed

Check your probe offset in `[probe]` section. The code uses nozzle coordinates, and Klipper automatically adjusts for probe offset. If positions are still wrong, edit `self.screw_positions` in the Python file.

### Commands not found

Make sure you've added `[bed_tramming_center]` to your printer.cfg and restarted Klipper completely:
```bash
sudo service klipper restart
```

## Contributing

Contributions welcome! Please open an issue or pull request.

## License

GNU General Public License v3.0 - see LICENSE file

## Credits

Created by Mike Repko for the Elegoo Neptune 4 Max
```

**LICENSE (GNU GPLv3):**
```
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007



This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
