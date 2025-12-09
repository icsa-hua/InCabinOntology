import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# 1. RAW DATA INPUT (Based on the Ontology Consistency Report)
# Reorganize the raw data into a structured list of dictionaries
validation_data = [
    # Category: Identity and Integrity Checks
    {"Category": "Identity", "Check": "[Identity] Duplicate keys", "Value": 0},
    {"Category": "Identity", "Check": "[Identity] Missing actor links", "Value": 16},
    {"Category": "Identity", "Check": "[Identity] Missing timestamps", "Value": 0},
    {"Category": "Identity", "Check": "[Identity] Orphan states", "Value": 16},
    {"Category": "Identity", "Check": "[Reuse] Physio reused", "Value": 0},
    
    # Category: Time and Alignment
    {"Category": "Time/Alignment", "Check": "[Time] Misaligned timestamps", "Value": 0},
    
    # Category: Consistency and Partition Checks
    {"Category": "Consistency", "Check": "[Categorization] Unclassified HR", "Value": 0},
    {"Category": "Consistency", "Check": "[Categorization] Unclassified SpO2", "Value": 0},
    {"Category": "Consistency", "Check": "[Partitions] Multi-membership in HR", "Value": 0},
    {"Category": "Consistency", "Check": "[Partitions] Multi-membership in RR", "Value": 0},
    {"Category": "Consistency", "Check": "[Per-state channels] Issues", "Value": 0},
    
    # Category: State Completeness (Fatigue, Attention, Unresponsiveness)
    {"Category": "Completeness", "Check": "[Fatigue] per-state issues", "Value": 2},
    {"Category": "Completeness", "Check": "[Fatigue] Is-values issues", "Value": 14},
    {"Category": "Completeness", "Check": "[Attention] per-state issues", "Value": 2},
    {"Category": "Completeness", "Check": "[Attention] Is-values issues", "Value": 14},
    {"Category": "Completeness", "Check": "[Unresponsiveness] Is-values issues", "Value": 0},
    
    # Category: Accessory Linkage
    {"Category": "Accessories", "Check": "[Accessories] Untyped accessories", "Value": 0},
    {"Category": "Accessories", "Check": "[Accessories] Group→Temp multiple", "Value": 0},
    {"Category": "Accessories", "Check": "[Accessories] without temp link", "Value": 0},
]

# 2. DATA PROCESSING
df = pd.DataFrame(validation_data)
# Add a status column: 'Pass' if Value == 0, 'Fail' otherwise
df['Status'] = np.where(df['Value'] == 0, 'Pass', 'Fail')
# Reverse the order for plotting (categories at the top)
df = df.iloc[::-1] 

# Calculate position for category separators
category_indices = df.groupby('Category').apply(lambda x: x.index.max())
category_heights = [df.index.max() - idx for idx in category_indices]

# 3. VISUALIZATION (Creating the Checkpoint Diagram)
plt.style.use('default') # Use default style for better control
fig, ax = plt.subplots(figsize=(8, 10))

# --- Plotting the Bars (The "Checkpoint Lines") ---
# Use the index as the y-coordinate
y_pos = np.arange(len(df))

# Plot bars to represent the status (Green for Pass, Red for Fail)
# The width is constant for visual uniformity
bar_width = 0.5 
ax.barh(y_pos[df['Status'] == 'Pass'], bar_width, left=0, 
        color='#4CAF50', alpha=0.8, align='center', label='Pass (Value = 0)') # Green
ax.barh(y_pos[df['Status'] == 'Fail'], bar_width, left=0, 
        color='#F44336', alpha=0.8,align='center', label='Fail (Value > 0)') # Red

# --- Annotations and Labels ---
# Set Y-axis labels to the check names
ax.set_yticks(y_pos)
ax.set_yticklabels(df['Check'], fontsize=10, ha='right')
ax.tick_params(axis='y', length=0) # Hide y-ticks

# Add the Value/Status text on the right side of the bar
for i, row in df.iterrows():
    label = 'PASS' if row['Value'] == 0 else str(row['Value'])
    color = '#2E7D32' if row['Value'] == 0 else '#B71C1C' # Darker shades
    
    # Adjust position: right of the bar (bar_width)
    ax.text(bar_width + 0.05, i, label, 
            ha='left', va='center', fontsize=10, 
            fontweight='bold', color=color)

# --- Category Separators and Labels ---
y_height = len(df)
current_y = 0
for category, idx in category_indices.sort_values(ascending=False).items():
    # Draw horizontal line separators
    if current_y > 0:
        ax.axhline(y=current_y - 0.5, color='gray', linestyle='--', linewidth=0.7)
    
    # Add category label (e.g., "Identity")
    # Position: vertically centered within its section
    next_y = idx + 1
    category_center = (current_y + next_y - 1) / 2
    
    # Add a colored rectangle/patch for the category background
    rect = patches.Rectangle(
        (-0.1, next_y - 0.5), # (x, y) starting point
        bar_width + 1.2,       # width
        (current_y - next_y + 1), # height
        facecolor='#EEEEEE', alpha=0.5, clip_on=False,
    )
    ax.add_patch(rect)
    
    ax.text(0.0, next_y - 0.3, category.upper(), 
            ha='left', va='center', fontsize=11, 
            fontweight='bold', color='black')
    
    current_y = next_y

# --- Final Plot Adjustments ---
ax.set_xlim(-0.1, bar_width + 0.5)
ax.set_ylim(-0.5, y_height - 0.5)

# Hide axis spines and x-axis
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.set_xticks([])
ax.set_title("Ontology Consistency Checkpoint Diagram", fontsize=14, fontweight='bold', pad=20)
ax.text(bar_width + 0.05, y_height - 0.5, "Value/Status", ha='left', va='center', fontsize=10, fontweight='bold')


plt.tight_layout()
plt.show()
