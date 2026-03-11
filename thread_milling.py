import math
import re


class ThreadMilling:
    def __init__(
        self,
        tool_description="Thread Mill",
        spindle_speed=12000,
        safe_height=40.0,
        plane="XY",
        direction="top_down",
        thread_hand="right",
    ):
        self.tool_description = tool_description
        self.spindle_speed = spindle_speed
        self.safe_height = safe_height
        self.plane = plane
        self.direction = direction
        self.thread_hand = thread_hand

    @staticmethod
    def generate_metric_thread_data(pitch, diameter):
        h = 0.8660 * pitch
        major_diameter = diameter
        minor_diameter = diameter - 2 * (5 * h / 8)
        cutter_depth_internal = (5 * h / 8) + h / 8
        cutter_depth_external = (5 * h / 8) + h / 4

        return {
            "major_diameter": major_diameter,
            "pitch": pitch,
            "minor_diameter": minor_diameter,
            "cutter_depth_internal": cutter_depth_internal,
            "cutter_depth_external": cutter_depth_external,
        }

    @staticmethod
    def generate_gcode_header(tool_description, spindle_speed, safe_height, plane="XY"):
        axis_3_label = {"XY": "Z", "XZ": "Y", "YZ": "X"}[plane]

        gcode = []
        line = 10

        def nl(cmd):
            nonlocal line
            out = f"N{line}{cmd}"
            line += 10
            return out

        gcode.append("%")
        gcode.append(nl(" G21 G40 G49"))
        gcode.append(nl(" G64 P0.05"))
        gcode.append(nl(f" ( Load tool {tool_description})"))
        gcode.append(nl(" G54"))
        gcode.append(nl(f" G0 {axis_3_label}{safe_height:.3f}"))
        gcode.append(nl(f" G0 X0.000 Y0.000 S{spindle_speed} M3"))
        gcode.append(nl(" G4 P1.0"))

        return gcode, line

    @staticmethod
    def generate_gcode_footer(safe_height, plane="XY", start_line=1000):
        axis_1_label, axis_2_label, axis_3_label = {
            "XY": ("X", "Y", "Z"),
            "XZ": ("X", "Z", "Y"),
            "YZ": ("Y", "Z", "X"),
        }[plane]

        line = start_line

        def nl(cmd):
            nonlocal line
            out = f"N{line}{cmd}"
            line += 10
            return out

        gcode = []
        gcode.append(nl(" M5"))
        gcode.append(nl(" G54"))
        gcode.append(nl(f" G0 {axis_3_label}{safe_height:.3f}"))
        gcode.append(nl(f" G0 {axis_1_label}0.000 {axis_2_label}0.000"))
        gcode.append(nl(" M2"))
        gcode.append("%")

        return gcode

    @staticmethod
    def _resolve_arc_cmd(direction, thread_hand):
        if direction not in ("top_down", "bottom_up"):
            raise ValueError("direction must be 'top_down' or 'bottom_up'.")
        if thread_hand not in ("right", "left"):
            raise ValueError("thread_hand must be 'right' or 'left'.")

        arc_cmd = "G2" if direction == "top_down" else "G3"
        if thread_hand == "left":
            arc_cmd = "G3" if arc_cmd == "G2" else "G2"
        return arc_cmd

    def generate_internal_thread_operation(
        self,
        x,
        y,
        z,
        hole_diameter,
        pitch,
        threaded_length,
        cutter_diameter,
        thread_depth,
        feedrate=200.0,
        plunge_rate=20.0,
        num_passes=2,
        safe_height=6.0,
        plane="XY",
        direction="top_down",
        thread_hand="right",
        start_line=100,
    ):
        cutter_radius = cutter_diameter / 2.0
        min_toolpath_radius = (hole_diameter / 2.0) - cutter_radius

        axis_1_label, axis_2_label, axis_3_label, offset1, offset2, plane_select = {
            "XY": ("X", "Y", "Z", "I", "J", "G17"),
            "XZ": ("X", "Z", "Y", "I", "K", "G18"),
            "YZ": ("Y", "Z", "X", "J", "K", "G19"),
        }[plane]

        axis_1, axis_2, axis_3 = {
            "XY": (x, y, z),
            "XZ": (x, z, y),
            "YZ": (y, z, x),
        }[plane]

        if cutter_diameter >= hole_diameter:
            raise ValueError("Cutter diameter must be smaller than hole diameter.")

        tool_radii = []
        for i in range(1, num_passes + 1):
            radius = min_toolpath_radius + thread_depth * math.sqrt(i / num_passes)
            tool_radii.append(radius)

        arc_cmd = self._resolve_arc_cmd(direction, thread_hand)
        start_z = axis_3 if direction == "top_down" else axis_3 - threaded_length

        num_turns = int(threaded_length / pitch + 0.5)
        if num_turns < 1:
            raise ValueError("Threaded length must be greater than pitch.")

        line = start_line

        def nl(cmd):
            nonlocal line
            out = f"N{line}{cmd}"
            line += 10
            return out

        gcode = []
        gcode.append(nl(" (Internal Thread Milling Operation)"))
        gcode.append(nl(f" (Location: {axis_1_label}{axis_1:.3f} {axis_2_label}{axis_2:.3f})"))
        gcode.append(nl(f" (Hole diameter {hole_diameter:.3f} mm)"))
        gcode.append(nl(f" (Cutter diameter {cutter_diameter:.3f} mm)"))
        gcode.append(nl(f" (Thread pitch {pitch:.3f} mm)"))
        gcode.append(nl(f" (Threaded length {threaded_length:.3f} mm)"))
        gcode.append(nl(f" (Cutter engagement {thread_depth:.3f} mm)"))
        gcode.append(nl(f" (Direction {direction})"))
        gcode.append(nl(f" (Thread hand {thread_hand})"))
        gcode.append(nl(f" {plane_select}"))
        gcode.append(nl(f" G0 {axis_3_label}{safe_height:.3f}"))
        gcode.append(nl(f" G0 {axis_1_label}{axis_1:.3f} {axis_2_label}{axis_2:.3f}"))

        current_radius = min_toolpath_radius
        for i, radius in enumerate(tool_radii):
            gcode.append(nl(f" (Pass {i + 1}: radius {current_radius:.3f} -> {radius:.3f})"))
            gcode.append(nl(f" G0 {axis_1_label}{axis_1:.3f} {axis_2_label}{axis_2:.3f}"))
            gcode.append(nl(f" G0 {axis_3_label}{start_z:.3f}"))
            gcode.append(nl(f" G0 {axis_1_label}{axis_1 + current_radius:.3f} {axis_2_label}{axis_2:.3f}"))
            gcode.append(nl(f" G1 {axis_1_label}{axis_1 + radius:.3f} F{plunge_rate:.3f}"))
            current_radius = radius

            current_z = start_z
            for _ in range(num_turns):
                next_z = current_z - pitch if direction == "top_down" else current_z + pitch
                gcode.append(nl(f" {arc_cmd} {offset1}{-radius:.3f} {offset2}0.000 {axis_3_label}{next_z:.3f} F{feedrate:.1f}"))
                current_z = next_z

        gcode.append(nl(f" G0 {axis_1_label}{axis_1:.3f} {axis_2_label}{axis_2:.3f}"))
        gcode.append(nl(f" G0 {axis_3_label}{safe_height:.3f}"))

        return gcode, line

    def generate_external_thread_operation(
        self,
        x,
        y,
        z,
        boss_diameter,
        pitch,
        threaded_length,
        cutter_diameter,
        thread_depth,
        feedrate=200.0,
        plunge_rate=20.0,
        num_passes=2,
        safe_height=6.0,
        clearance=1.0,
        plane="XY",
        direction="top_down",
        thread_hand="right",
        start_line=100,
    ):
        cutter_radius = cutter_diameter / 2.0
        max_toolpath_radius = (boss_diameter / 2.0) + cutter_radius

        axis_1_label, axis_2_label, axis_3_label, offset1, offset2, plane_select = {
            "XY": ("X", "Y", "Z", "I", "J", "G17"),
            "XZ": ("X", "Z", "Y", "I", "K", "G18"),
            "YZ": ("Y", "Z", "X", "J", "K", "G19"),
        }[plane]

        axis_1, axis_2, axis_3 = {
            "XY": (x, y, z),
            "XZ": (x, z, y),
            "YZ": (y, z, x),
        }[plane]

        tool_radii = []
        for i in range(1, num_passes + 1):
            radius = max_toolpath_radius - thread_depth * math.sqrt(i / num_passes)
            tool_radii.append(radius)

        arc_cmd = self._resolve_arc_cmd(direction, thread_hand)
        start_z = axis_3 if direction == "top_down" else axis_3 - threaded_length

        num_turns = int(threaded_length / pitch + 0.5)
        if num_turns < 1:
            raise ValueError("Threaded length must be greater than pitch.")

        line = start_line

        def nl(cmd):
            nonlocal line
            out = f"N{line}{cmd}"
            line += 10
            return out

        gcode = []
        gcode.append(nl(" (External Thread Milling Operation)"))
        gcode.append(nl(f" (Location: {axis_1_label}{axis_1:.3f} {axis_2_label}{axis_2:.3f})"))
        gcode.append(nl(f" (Boss diameter {boss_diameter:.3f} mm)"))
        gcode.append(nl(f" (Cutter diameter {cutter_diameter:.3f} mm)"))
        gcode.append(nl(f" (Thread pitch {pitch:.3f} mm)"))
        gcode.append(nl(f" (Threaded length {threaded_length:.3f} mm)"))
        gcode.append(nl(f" (Cutter engagement {thread_depth:.3f} mm)"))
        gcode.append(nl(f" (Direction {direction})"))
        gcode.append(nl(f" (Thread hand {thread_hand})"))
        gcode.append(nl(f" {plane_select}"))

        outer_clear_radius = boss_diameter / 2.0 + clearance + cutter_radius

        current_radius = max_toolpath_radius
        for i, radius in enumerate(tool_radii):
            gcode.append(nl(f" (Pass {i + 1}: radius {current_radius:.3f} -> {radius:.3f})"))
            gcode.append(nl(f" G0 {axis_1_label}{axis_1 + outer_clear_radius:.3f} {axis_2_label}{axis_2:.3f}"))
            gcode.append(nl(f" G0 {axis_3_label}{start_z:.3f}"))
            gcode.append(nl(f" G1 {axis_1_label}{axis_1 + radius:.3f} F{plunge_rate:.3f}"))
            current_radius = radius

            current_z = start_z
            for _ in range(num_turns):
                next_z = current_z - pitch if direction == "top_down" else current_z + pitch
                gcode.append(nl(f" {arc_cmd} {offset1}{-radius:.3f} {offset2}0.000 {axis_3_label}{next_z:.3f} F{feedrate:.1f}"))
                current_z = next_z

        gcode.append(nl(f" G0 {axis_1_label}{axis_1 + outer_clear_radius:.3f} {axis_2_label}{axis_2:.3f}"))
        gcode.append(nl(f" G0 {axis_3_label}{safe_height:.3f}"))

        return gcode, line

    def generate_complete_gcode(
        self,
        operations,
        tool_description=None,
        spindle_speed=None,
        safe_height=None,
        plane=None,
    ):
        tool_description = self.tool_description if tool_description is None else tool_description
        spindle_speed = self.spindle_speed if spindle_speed is None else spindle_speed
        safe_height = self.safe_height if safe_height is None else safe_height
        plane = self.plane if plane is None else plane

        gcode_lines = []
        header, line_num = self.generate_gcode_header(tool_description, spindle_speed, safe_height, plane)
        gcode_lines.extend(header)

        for op in operations:
            op_type = op.get("type", "").lower()
            common_params = {
                "x": op["x"],
                "y": op["y"],
                "z": op["z"],
                "pitch": op["pitch"],
                "threaded_length": op["threaded_length"],
                "cutter_diameter": op["cutter_diameter"],
                "thread_depth": op["thread_depth"],
                "num_passes": op.get("num_passes", 2),
                "feedrate": op.get("feedrate", 200.0),
                "plunge_rate": op.get("plunge_rate", 20.0),
                "direction": op.get("direction", self.direction),
                "thread_hand": op.get("thread_hand", self.thread_hand),
                "safe_height": safe_height,
                "plane": plane,
                "start_line": line_num,
            }

            if op_type == "internal":
                common_params["hole_diameter"] = op["diameter"]
                op_gcode, line_num = self.generate_internal_thread_operation(**common_params)
            elif op_type == "external":
                common_params["boss_diameter"] = op["diameter"]
                common_params["clearance"] = op.get("clearance", 1.0)
                op_gcode, line_num = self.generate_external_thread_operation(**common_params)
            else:
                raise ValueError(f"Invalid operation type: {op.get('type')}. Must be 'Internal' or 'External'")

            gcode_lines.extend(op_gcode)

        footer = self.generate_gcode_footer(safe_height, plane, start_line=line_num)
        gcode_lines.extend(footer)

        return "\n".join(gcode_lines)

    @staticmethod
    def parse_hole_file(filename):
        with open(filename, "r", encoding="utf-8") as handle:
            content = handle.read()

        holes = []
        params = {
            "major_diameter": 37.5,
            "pitch": 1.75,
            "cutter_diameter": 10,
            "passes": 2,
        }

        param_patterns = {
            "major_diameter": r"major_diameter\s*=\s*([-\d.]+)",
            "pitch": r"pitch\s*=\s*([-\d.]+)",
            "cutter_diameter": r"cutter_diameter\s*=\s*([-\d.]+)",
            "passes": r"passes\s*=\s*(\d+)",
        }

        for param_name, pattern in param_patterns.items():
            match = re.search(pattern, content)
            if match:
                params[param_name] = float(match.group(1)) if param_name != "passes" else int(match.group(1))

        dict_pattern = r"\{\s*'x':\s*([-\d.]+)\s*,\s*'y':\s*([-\d.]+)\s*,\s*'z':\s*([-\d.]+)\s*,\s*'depth':\s*([-\d.]+)\s*\}"
        dict_matches = re.findall(dict_pattern, content)

        if dict_matches:
            for match in dict_matches:
                holes.append(
                    {
                        "x": float(match[0]),
                        "y": float(match[1]),
                        "z": float(match[2]),
                        "depth": abs(float(match[3])),
                    }
                )
        else:
            centre_pattern = r"Hole Centre:\s*\{\s*X:\s*([-\d.]+)\s*,\s*Y:\s*([-\d.]+)\s*,\s*Z:\s*([-\d.]+)\s*\}"
            depth_pattern = r"Hole Depth:\s*Z:\s*([-\d.]+)"

            lines = content.split("\n")
            current_centre = None

            for line in lines:
                centre_match = re.search(centre_pattern, line)
                if centre_match:
                    x = float(centre_match.group(1))
                    y = float(centre_match.group(2))
                    z = float(centre_match.group(3))
                    current_centre = {"x": x, "y": y, "z": z}
                    continue

                depth_match = re.search(depth_pattern, line)
                if depth_match and current_centre:
                    depth = abs(float(depth_match.group(1)))
                    hole_data = current_centre.copy()
                    hole_data["depth"] = depth
                    holes.append(hole_data)
                    current_centre = None

        return holes, params

    @staticmethod
    def build_operations(holes, thread_data, pitch, cutter_diameter, num_passes, operation_type="Internal", direction="top_down", thread_hand="right"):
        operations = []
        for hole in holes:
            threaded_length = hole["z"] + hole["depth"]
            is_external = operation_type == "External"
            operations.append(
                {
                    "type": operation_type,
                    "x": hole["x"],
                    "y": hole["y"],
                    "z": hole["z"],
                    "diameter": thread_data["major_diameter"] if is_external else thread_data["minor_diameter"],
                    "pitch": pitch,
                    "thread_depth": thread_data["cutter_depth_external"] if is_external else thread_data["cutter_depth_internal"],
                    "threaded_length": threaded_length,
                    "cutter_diameter": cutter_diameter,
                    "num_passes": num_passes,
                    "direction": direction,
                    "thread_hand": thread_hand,
                }
            )
        return operations
