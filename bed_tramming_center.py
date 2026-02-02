# ~/klipper/klippy/extras/bed_tramming_center.py
# Center-reference bed tramming for Elegoo Neptune 4 Max
# Copyright (C) 2025 SilentAxis
# This file may be distributed under the terms of the GNU GPLv3 license.

class BedTrammingCenter:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.center_z = None
        self.screw_pitch = config.getfloat('screw_pitch', 0.8)
        self.samples = config.getint('samples', 6)
        self.lift_height = config.getfloat('lift_height', 20.0)
        self.probe_speed = config.getfloat('probe_speed', 6000.0)
        
        # Screw positions - nozzle coordinates
        self.screw_positions = {
            'center': {'x': 230.0, 'y': 210.0, 'name': 'Center'},
            'front_left': {'x': 45.0, 'y': 10.0, 'name': 'Front Left'},
            'front_right': {'x': 419.0, 'y': 10.0, 'name': 'Front Right'},
            'back_left': {'x': 45.0, 'y': 400.0, 'name': 'Back Left'},
            'back_right': {'x': 419.0, 'y': 400.0, 'name': 'Back Right'},
            'left_middle': {'x': 45.0, 'y': 210.0, 'name': 'Left Middle'},
            'right_middle': {'x': 419.0, 'y': 210.0, 'name': 'Right Middle'},
        }
        
        # Register commands
        self.gcode.register_command('PROBE_CENTER',
                                   self.cmd_PROBE_CENTER,
                                   desc=self.cmd_PROBE_CENTER_help)
        self.gcode.register_command('PROBE_SCREW_FL',
                                   self.cmd_PROBE_SCREW_FL,
                                   desc="Probe front left screw")
        self.gcode.register_command('PROBE_SCREW_FR',
                                   self.cmd_PROBE_SCREW_FR,
                                   desc="Probe front right screw")
        self.gcode.register_command('PROBE_SCREW_BL',
                                   self.cmd_PROBE_SCREW_BL,
                                   desc="Probe back left screw")
        self.gcode.register_command('PROBE_SCREW_BR',
                                   self.cmd_PROBE_SCREW_BR,
                                   desc="Probe back right screw")
        self.gcode.register_command('PROBE_SCREW_LM',
                                   self.cmd_PROBE_SCREW_LM,
                                   desc="Probe left middle screw")
        self.gcode.register_command('PROBE_SCREW_RM',
                                   self.cmd_PROBE_SCREW_RM,
                                   desc="Probe right middle screw")
        self.gcode.register_command('PROBE_ALL_SCREWS',
                                   self.cmd_PROBE_ALL_SCREWS,
                                   desc="Probe all screw positions in sequence")
    
    def _probe_position(self, gcmd, x, y, name):
        """Probe a specific position and return Z value"""
        try:
            toolhead = self.printer.lookup_object('toolhead')
            
            # Wait for any pending moves
            toolhead.wait_moves()
            
            # Move Z up 5mm relative for safety
            self.gcode.run_script_from_command("G91")
            self.gcode.run_script_from_command("G1 Z5 F600")
            self.gcode.run_script_from_command("G90")
            toolhead.wait_moves()
            
            # Move to XY position
            gcmd.respond_info("Moving to %s (X%.1f Y%.1f)" % (name, x, y))
            self.gcode.run_script_from_command("G1 X%.3f Y%.3f F%.1f" % (x, y, self.probe_speed))
            toolhead.wait_moves()
            
            # Perform probe with multiple samples
            gcmd.respond_info("Probing %s (%d samples)..." % (name, self.samples))
            
            samples = []
            for i in range(self.samples):
                # Run PROBE command
                self.gcode.run_script_from_command("PROBE")
                toolhead.wait_moves()
                
                # Get the Z position after probe
                pos = toolhead.get_position()
                samples.append(pos[2])
                gcmd.respond_info("Sample %d: Z=%.4f" % (i + 1, pos[2]))
                
                # Retract between samples (except on last sample)
                if i < self.samples - 1:
                    self.gcode.run_script_from_command("G91")
                    self.gcode.run_script_from_command("G1 Z3 F600")
                    self.gcode.run_script_from_command("G90")
                    toolhead.wait_moves()
            
            # Calculate median
            samples.sort()
            if self.samples % 2 == 0:
                median_z = (samples[self.samples // 2 - 1] + samples[self.samples // 2]) / 2.0
            else:
                median_z = samples[self.samples // 2]
            
            gcmd.respond_info("Median result: Z=%.4f" % median_z)
            
            # Lift after probe
            self.gcode.run_script_from_command("G91")
            self.gcode.run_script_from_command("G1 Z%.3f F600" % self.lift_height)
            self.gcode.run_script_from_command("G90")
            toolhead.wait_moves()
            
            return median_z
            
        except Exception as e:
            raise gcmd.error("Probe failed: %s" % str(e))
    
    def _calculate_adjustment(self, gcmd, location_name, current_z):
        """Calculate and report screw adjustment needed"""
        if self.center_z is None:
            raise gcmd.error("Center reference not set. Run PROBE_CENTER first.")
        
        diff = current_z - self.center_z
        turns = abs(diff) / self.screw_pitch
        
        gcmd.respond_info("%s Z=%.4f (Center: %.4f, diff: %.4fmm)" % 
                         (location_name, current_z, self.center_z, diff))
        
        if abs(diff) < 0.01:
            gcmd.respond_info("%s: Perfect! No adjustment needed" % location_name)
        elif diff > 0:
            gcmd.respond_info("%s: LOOSEN (CCW) %.2f turns (%.3fmm low - raise bed)" % 
                            (location_name, turns, diff))
        else:
            gcmd.respond_info("%s: TIGHTEN (CW) %.2f turns (%.3fmm high - lower bed)" % 
                            (location_name, turns, abs(diff)))
    
    cmd_PROBE_CENTER_help = "Probe bed center and store as reference"
    def cmd_PROBE_CENTER(self, gcmd):
        """Probe the center of the bed and store as reference"""
        center = self.screw_positions['center']
        gcmd.respond_info("Probing center reference point...")
        
        self.center_z = self._probe_position(gcmd, center['x'], center['y'], center['name'])
        gcmd.respond_info("=" * 50)
        gcmd.respond_info("Center reference set to Z=%.4f" % self.center_z)
        gcmd.respond_info("You can now probe individual screws or use PROBE_ALL_SCREWS")
        gcmd.respond_info("=" * 50)
    
    def cmd_PROBE_SCREW_FL(self, gcmd):
        """Probe front left screw"""
        pos = self.screw_positions['front_left']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_SCREW_FR(self, gcmd):
        """Probe front right screw"""
        pos = self.screw_positions['front_right']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_SCREW_BL(self, gcmd):
        """Probe back left screw"""
        pos = self.screw_positions['back_left']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_SCREW_BR(self, gcmd):
        """Probe back right screw"""
        pos = self.screw_positions['back_right']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_SCREW_LM(self, gcmd):
        """Probe left middle screw"""
        pos = self.screw_positions['left_middle']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_SCREW_RM(self, gcmd):
        """Probe right middle screw"""
        pos = self.screw_positions['right_middle']
        z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
        self._calculate_adjustment(gcmd, pos['name'], z)
    
    def cmd_PROBE_ALL_SCREWS(self, gcmd):
        """Probe all screw positions in sequence"""
        if self.center_z is None:
            raise gcmd.error("Center reference not set. Run PROBE_CENTER first.")
        
        screw_order = ['front_left', 'front_right', 'left_middle', 
                      'right_middle', 'back_left', 'back_right']
        
        gcmd.respond_info("=" * 50)
        gcmd.respond_info("Probing all screw positions...")
        gcmd.respond_info("=" * 50)
        
        for screw_key in screw_order:
            pos = self.screw_positions[screw_key]
            z = self._probe_position(gcmd, pos['x'], pos['y'], pos['name'])
            self._calculate_adjustment(gcmd, pos['name'], z)
            gcmd.respond_info("-" * 50)
        
        gcmd.respond_info("=" * 50)
        gcmd.respond_info("All screws probed. Adjust as indicated and re-probe to verify.")
        gcmd.respond_info("=" * 50)

def load_config(config):
    return BedTrammingCenter(config)
