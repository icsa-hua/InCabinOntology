from src.scripts.test_parser import main 
import threading
import psutil
import os
import time

# Global list to store CPU usage samples
cpu_samples = []
monitor_running = threading.Event()
monitor_running.set() # Set the event to running state
PID = os.getpid()

def cpu_monitor_thread(pid, sample_interval=0.1):
    """Samples the CPU usage of the process at regular intervals."""
    process = psutil.Process(pid)
    
    # Prime the first call (as in Method 1)
    process.cpu_percent(interval=None) 
    
    while monitor_running.is_set():
        try:
            # Get the process-specific CPU percentage
            # We use 0.0 as interval here because the thread handles the sleep/interval
            cpu_percent = process.cpu_percent(interval=0.0)
            cpu_samples.append(cpu_percent)
            time.sleep(sample_interval)
        except psutil.NoSuchProcess:
            break
        except Exception:
            # Handle thread interruption gracefully
            break

# 1. Start the monitoring thread
monitor = threading.Thread(target=cpu_monitor_thread, args=(PID,))
monitor.start()

main()

# 2. Run your inference function (from Method 1) pv
# You would replace this with your actual reasoner call
print("Starting Reasoner Inference with Real-time Monitoring...")
# --- Start of Inference Logic ---
start_time = time.time()
while time.time() - start_time < 5:  # Run for 5 seconds
    _ = 2**200000 
print("Inference Complete.")
# --- End of Inference Logic ---

# 3. Stop the monitor and wait for the thread to join
monitor_running.clear()
monitor.join()

# --- Reporting ---
if cpu_samples:
    avg_cpu = sum(cpu_samples) / len(cpu_samples)
    peak_cpu = max(cpu_samples)
    print(f"\n--- Real-Time CPU Utilization Results (Sample Interval: {0.1}s) ---")
    print(f"Average CPU Utilization: {avg_cpu:.2f}%")
    print(f"Peak CPU Utilization: {peak_cpu:.2f}%")
    print(f"Total Samples Collected: {len(cpu_samples)}")
else:
    print("Error: No CPU samples were collected.")
