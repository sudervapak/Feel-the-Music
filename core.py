
import os
import serial
import serial.tools.list_ports
import time
import csv
from mido import MidiFile

def find_bluetooth_port(target_names=["HC-05", "Serial", "Bluetooth"]):
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        for name in target_names:
            if name in port.description or name in port.name:
                return port.device
    return None

bt = None
port = find_bluetooth_port()

if port:
    try:
        bt = serial.Serial(port, 9600)
        time.sleep(2)
        print(f"✅ Bluetooth connected on {port}")
    except Exception as e:
        print(f"❌ Failed to connect on {port}: {e}")
else:
    print("⚠️ Bluetooth device not found. Make sure HC-05 is paired and has an assigned COM port.")

# Get base directory of the application
base_folder = os.path.dirname(os.path.abspath(__file__))

# Function to process a MIDI file and send vibration commands over Bluetooth
def process_midi_file(path, stop_flag_callback):
    try:
        midi = MidiFile(path)  # Load the MIDI file
    except Exception as e:
        print("❌ Failed to open MIDI file:", e)
        return

    bpm = 120  # Default BPM if not specified in the MIDI

    # Check if MIDI file specifies a tempo change
    for track in midi.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                bpm = 60000000 / msg.tempo  # Convert tempo to BPM
                break

    ticks_per_beat = midi.ticks_per_beat  # Number of ticks per beat in the MIDI file
    absolute_time = 0  # Total elapsed time in ticks
    note_states = {}  # Track currently active notes
    note_events = []  # List of detected note events

    # Read all MIDI events
    for track in midi.tracks:
        absolute_time = 0
        for msg in track:
            absolute_time += msg.time  # Increment time

            # Detect when a note starts
            if msg.type == 'note_on' and msg.velocity > 0:
                note_states[msg.note] = (absolute_time, msg.velocity)

            # Detect when a note ends
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                note = msg.note
                if note in note_states:
                    start_time, velocity = note_states.pop(note)
                    duration_ticks = absolute_time - start_time
                    duration_sec = (duration_ticks * 60) / (bpm * ticks_per_beat)  # Convert to seconds
                    if duration_sec <= 0:
                        continue  # Ignore invalid durations

                    # Map note to a motor ID and calculate vibration frequency and PWM
                    pwm = int((velocity / 127) * 255)
                    motor_id = 1 if note < 40 else 2 if note < 55 else 3 if note < 70 else 4
                    freq = 50 + (note - 36) * 5  # Simple frequency mapping
                    note_events.append((start_time, motor_id, freq, pwm, round(duration_sec, 3)))

    # Group note events by their start time
    grouped_events = {}
    for ev in note_events:
        timestamp = ev[0]
        grouped_events.setdefault(timestamp, []).append(ev)

    sorted_groups = sorted(grouped_events.items(), key=lambda x: x[0])  # Sort events by time

    # Write vibration events to a CSV file for logging purposes
    with open(os.path.join(base_folder, "vibration_log.csv"), mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "motor_id", "frequency", "pwm", "duration"])

        # Send each group of vibrations over Bluetooth
        for timestamp, group in sorted_groups:
            if stop_flag_callback():
                print("🛑 Playback stopped by user.")
                return

            print(f"\n⏱ Time: {timestamp} ticks")
            max_dur = 0  # Track the maximum duration within this group

            for motor_id, freq, pwm, dur in [(g[1], g[2], g[3], g[4]) for g in group]:
                writer.writerow([timestamp, motor_id, freq, pwm, dur])
                if bt:
                    # Format and send vibration command: motor_id,frequency,pwm,duration\n
                    data = f"{motor_id},{freq},{pwm},{dur:.2f}\n"
                    bt.write(data.encode())
                    print(f"📤 Sent → {data.strip()}")
                if dur > max_dur:
                    max_dur = dur

            # Wait for the longest duration among the parallel notes
            if max_dur > 0:
                time.sleep(max_dur)

        print("✅ Playback completed.")
