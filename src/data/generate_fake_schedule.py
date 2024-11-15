import pandas as pd
from datetime import datetime, timedelta

# Function to create the schedule with task names
def create_schedule(dealers, start_time, end_time, num_tasks, task_names):
    # Calculate the time interval for each task
    total_duration = end_time - start_time
    task_duration = total_duration / num_tasks

    # Create the list of tasks with specified intervals
    task_entries = []
    for i in range(num_tasks):
        task_start = start_time + i * task_duration
        task_end = task_start + task_duration

        # Cycle through the list of dealers
        dealer = dealers[i % len(dealers)]  # Modulo ensures dealers cycle

        # Generate task name (e.g., Roulette1, Poker2)
        task_name = f"{task_names[i % len(task_names)]}"

        task_entries.append({
            "Game": task_name,
            "Start_Time": task_start,
            "End_Time": task_end,
            "Dealer": dealer
        })

    # Convert to DataFrame
    df = pd.DataFrame(task_entries)
    return df

# Input parameters
dealers = ["Victor", "Augustin", "Nicolas", "Anaelle", "Pablo"]  # List of dealers
start_time = datetime(2024, 11, 30, 0, 0)  # Start time of the event
end_time = datetime(2024, 11, 30, 23, 0)  # End time of the event
num_tasks = 10  # Total number of tasks
task_names = ["Roulette", "Poker", "Blackjack", "Dices", "Bar", "Bank"]  # Task names

# Generate the schedule
schedule_df = create_schedule(dealers, start_time, end_time, num_tasks, task_names)

# Print the schedule
print(schedule_df)

# Optionally, save the schedule to a CSV file
schedule_df.to_csv("gdealer_schedule.csv", index=False, sep="\t")