#!/usr/bin/env python3
"""
Analyze QEMU process vcpu scheduling data and create pie chart for individual threads
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set font and style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('default')

def load_json_data(file_path):
    """Load JSON file data"""
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_thread_data():
    """Analyze thread data from all JSON files - treat each thread as independent"""
    data_dir = Path('.')
    json_files = list(data_dir.glob('trace_vcpu_sched-*.json'))
    
    thread_data = {}
    
    for json_file in sorted(json_files):
        print(f"Processing file: {json_file.name}")
        data = load_json_data(json_file)
        
        # Extract process ID from filename as instance identifier
        instance_id = json_file.stem.split('-')[1]
        
        # Process each thread individually
        for thread_id, thread_info in data.items():
            vcpu = thread_info.get('vcpu', 0)
            scheds = thread_info.get('scheds', {})
            
            # Create unique identifier for each thread
            thread_key = f"Instance-{instance_id}-Thread-{thread_id}"
            
            # Calculate total scheduling events for this thread
            total_scheds = scheds["0"]
            
            thread_data[thread_key] = {
                'instance_id': instance_id,
                'thread_id': thread_id,
                'vcpu': vcpu,
                'total_scheds': total_scheds,
                'scheds': scheds
            }
            
            print(f"  Thread {thread_id} (vcpu {vcpu}): {total_scheds} total scheduling events")
    
    return thread_data

def create_pie_chart(thread_data):
    """Create pie chart for individual threads"""
    # Prepare data for pie chart
    labels = []
    sizes = []
    colors = []
    
    # Color palette
    color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    for i, (thread_key, data) in enumerate(thread_data.items()):
        instance_id = data['instance_id']
        thread_id = data['thread_id']
        vcpu = data['vcpu']
        total_scheds = data['total_scheds']
        
        # Create label with instance, thread, and vcpu info
        label = f"Instance-{instance_id}\nThread-{thread_id} (vcpu{vcpu})"
        labels.append(label)
        sizes.append(total_scheds)
        colors.append(color_palette[i % len(color_palette)])
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create explosion effect for better visual separation
    explode = [0.05] * len(labels)
    
    # Draw pie chart
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                     startangle=90, explode=explode, shadow=True)
    
    # Beautify text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)
        autotext.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
    
    for text in texts:
        text.set_fontsize(11)
        text.set_fontweight('bold')
        text.set_color('#2C3E50')
    
    # Add title
    ax.set_title('QEMU Process Thread Scheduling Distribution\n(Individual Thread Scheduling Events)', 
                fontsize=18, fontweight='bold', pad=30, color='#2C3E50')
    
    # Add legend with detailed information
    legend_labels = [f"{thread_key}: {data['total_scheds']:,} events" 
                    for thread_key, data in thread_data.items()]
    legend = ax.legend(wedges, legend_labels, title="Thread Details", 
                      loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                      fontsize=10, title_fontsize=12)
    legend.get_title().set_fontweight('bold')
    legend.get_title().set_color('#2C3E50')
    
    # Ensure pie chart is circular
    ax.axis('equal')
    
    # Add a subtle background
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#FFFFFF')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save high-quality image
    plt.savefig('thread_scheduling_distribution.png', dpi=300, bbox_inches='tight', 
                facecolor='#F8F9FA', edgecolor='none')
    plt.show()
    
    return thread_data

def create_detailed_analysis(thread_data):
    """Create detailed scheduling analysis for each thread"""
    print("\n=== Individual Thread Scheduling Analysis ===")
    
    for thread_key, data in thread_data.items():
        instance_id = data['instance_id']
        thread_id = data['thread_id']
        vcpu = data['vcpu']
        total_scheds = data['total_scheds']
        scheds = data['scheds']
        
        print(f"\n{thread_key}:")
        print(f"  Instance: {instance_id}")
        print(f"  Thread ID: {thread_id}")
        print(f"  vCPU: {vcpu}")
        print(f"  Total scheduling events: {total_scheds:,}")
        print("  CPU scheduling distribution:")
        for cpu, count in sorted(scheds.items()):
            percentage = (count / total_scheds) * 100 if total_scheds > 0 else 0
            print(f"    CPU{cpu}: {count:,} events ({percentage:.1f}%)")

def main():
    """Main function"""
    print("Starting analysis of QEMU process thread scheduling data...")
    print("Each thread is treated as an independent vCPU")
    
    # Analyze data
    thread_data = analyze_thread_data()
    
    # Create pie chart
    create_pie_chart(thread_data)
    
    # Detailed analysis
    create_detailed_analysis(thread_data)
    
    print(f"\nPie chart saved as: thread_scheduling_distribution.png")
    print("Analysis completed!")

if __name__ == "__main__":
    main()