import importlib


ThreadMilling = importlib.import_module("thread_milling").ThreadMilling


def prompt_positive_float(prompt_text, default_value):
    while True:
        raw = input(f"{prompt_text} [{default_value}]: ").strip()
        if not raw:
            return float(default_value)
        try:
            value = float(raw)
            if value <= 0:
                print("Please enter a value greater than 0.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")


def prompt_thread_type(default_value="internal"):
    while True:
        raw = input(f"Thread type (internal/external) [{default_value}]: ").strip().lower()
        if not raw:
            return default_value
        if raw in ("internal", "i"):
            return "internal"
        if raw in ("external", "e"):
            return "external"
        print("Please enter 'internal' or 'external'.")


def prompt_direction(default_value="top_down"):
    while True:
        raw = input(f"Thread direction (top_down/bottom_up) [{default_value}]: ").strip().lower()
        if not raw:
            return default_value
        if raw in ("top_down", "top", "t"):
            return "top_down"
        if raw in ("bottom_up", "bottom", "b"):
            return "bottom_up"
        print("Please enter 'top_down' or 'bottom_up'.")


def main():
    milling = ThreadMilling()

    hole_file = input("Enter hole position file path: ").strip()
    operation_type = "Internal"
    direction = "top_down"
    thread_hand = "right"

    if not hole_file:
        print("\nNo hole file provided. Let's set up a single hole at X0 Y0 Z0.")
        selected_thread_type = prompt_thread_type("internal")
        operation_type = "External" if selected_thread_type == "external" else "Internal"
        direction = prompt_direction("top_down")
        depth = prompt_positive_float("Hole depth (mm)", 10.0)
        major_diameter = prompt_positive_float("Thread major diameter (mm)", 37.5)
        pitch = prompt_positive_float("Thread pitch (mm)", 1.75)
        cutter_diameter = prompt_positive_float("Cutter diameter (mm)", 10.0)

        holes = [{"x": 0.0, "y": 0.0, "z": 0.0, "depth": depth}]
        params = {
            "major_diameter": major_diameter,
            "pitch": pitch,
            "cutter_diameter": cutter_diameter,
            "passes": 2,
        }
        print(f"\nℹ️ Using single hole at X0 Y0 Z0 with depth {depth} mm")
    else:
        try:
            holes, params = milling.parse_hole_file(hole_file)
            print(f"\n✅ Found {len(holes)} holes in file")
        except FileNotFoundError:
            print(f"❌ Error: File '{hole_file}' not found")
            return 1
        except Exception as exc:
            print(f"❌ Error reading file: {exc}")
            return 1

    major_diameter = params["major_diameter"]
    pitch = params["pitch"]
    cutter_diameter = params["cutter_diameter"]
    num_passes = params["passes"]

    thread_data = milling.generate_metric_thread_data(pitch, major_diameter)

    print("\nThread Data:")
    print(f"Major Diameter: {thread_data['major_diameter']} mm")
    print(f"Minor Diameter: {thread_data['minor_diameter']} mm")
    print(f"Cutter Depth Internal: {thread_data['cutter_depth_internal']} mm")
    print(f"Cutter Depth External: {thread_data['cutter_depth_external']} mm")
    print(f"Pitch: {thread_data['pitch']} mm")

    operations = milling.build_operations(
        holes=holes,
        thread_data=thread_data,
        pitch=pitch,
        cutter_diameter=cutter_diameter,
        num_passes=num_passes,
        operation_type=operation_type,
        direction=direction,
        thread_hand=thread_hand,
    )

    print(f"\n🔧 Generating G-code for {len(operations)} threading operations...")

    gcode = milling.generate_complete_gcode(operations)

    output_file = input("\nEnter output G-code file path: ").strip()

    try:
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(gcode)
        print(f"✅ G-code written to '{output_file}'")
    except Exception as exc:
        print(f"❌ Error writing file: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
