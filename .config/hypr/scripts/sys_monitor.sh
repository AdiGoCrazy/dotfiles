#!/usr/bin/env bash

# Set your trigger thresholds (%)
CPU_THRESHOLD=90
RAM_THRESHOLD=90
GPU_THRESHOLD=90

while true; do
    # 1. CPU Usage Calculation
    cpu_usage=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print int(usage)}')
    
    # 2. RAM Usage Calculation
    ram_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    
    # 3. GPU Usage Calculation (Nvidia)
    if command -v nvidia-smi &> /dev/null; then
        gpu_usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{print int($1)}')
    else
        gpu_usage=0
    fi

    # Trigger Dunst warnings if metrics exceed safe limits
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        dunstify -u critical "🔥 High CPU Load" "CPU usage is currently at ${cpu_usage}%" -h string:x-dunst-stack-tag:sys-cpu
    fi

    if [ "$ram_usage" -gt "$RAM_THRESHOLD" ]; then
        dunstify -u critical "🧠 Memory Exhaustion Warning" "RAM usage has spiked to ${ram_usage}%" -h string:x-dunst-stack-tag:sys-ram
    fi

    if [ "$gpu_usage" -gt "$GPU_THRESHOLD" ]; then
        dunstify -u critical "⚡ High GPU Load" "GPU utilization is peaking at ${gpu_usage}%" -h string:x-dunst-stack-tag:sys-gpu
    fi

    sleep 30  # Check stats every 30 seconds
done
