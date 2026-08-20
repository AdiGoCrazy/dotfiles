#!/usr/bin/env bash

SAVE_DIR="$HOME/Videos/Recordings"
PID_FILE="/tmp/wf_recorder.pid"
META_FILE="/tmp/wf_recorder.meta"
SOUND_START="/usr/share/sounds/ocean/stereo/service-login.oga"
SOUND_STOP="/usr/share/sounds/ocean/stereo/button-pressed.oga"

mkdir -p "$SAVE_DIR"

is_recording() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

play_sound() {
    if [ -f "$1" ]; then
        paplay "$1" &
    fi
}

start_recording() {
    local geometry="$1"
    local filename="Recording_$(date +'%Y-%m-%d_%H-%M-%S').mp4"
    local filepath="$SAVE_DIR/$filename"
    local start_time=$(date +%s)

    play_sound "$SOUND_START"

    if [ -n "$geometry" ]; then
        wf-recorder --audio -g "$geometry" -f "$filepath" > /dev/null 2>&1 &
    else
        wf-recorder --audio -f "$filepath" > /dev/null 2>&1 &
    fi

    local rec_pid=$!
    echo "$rec_pid" > "$PID_FILE"
    echo "$filepath|$start_time" > "$META_FILE"

    dunstify -u normal -i video-x-generic "📹 Screen Recording Started" "Saving to: $filename"
}

stop_recording() {
    if is_recording; then
        local rec_pid=$(cat "$PID_FILE")
        kill -INT "$rec_pid" > /dev/null 2>&1
        
        # Wait for wf-recorder to finish writing file
        for i in {1..30}; do
            if ! ps -p "$rec_pid" > /dev/null 2>&1; then
                break
            fi
            sleep 0.1
        done

        play_sound "$SOUND_STOP"

        local filepath=""
        local start_time=""
        if [ -f "$META_FILE" ]; then
            filepath=$(cut -d'|' -f1 "$META_FILE")
            start_time=$(cut -d'|' -f2 "$META_FILE")
        fi

        rm -f "$PID_FILE" "$META_FILE"

        if [ -n "$filepath" ] && [ -f "$filepath" ]; then
            local filename=$(basename "$filepath")
            local filesize=$(du -h "$filepath" | cut -f1)
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            local dur_fmt=$(printf '%02dm:%02ds' $((duration/60)) $((duration%60)))

            dunstify -u normal -i video-x-generic "📹 Recording Stopped" "Saved: $filename ($filesize, $dur_fmt)"
        else
            dunstify -u normal -i video-x-generic "📹 Recording Stopped" "File saved in $SAVE_DIR"
        fi
    fi
}

get_status_json() {
    if is_recording; then
        local start_time=$(cut -d'|' -f2 "$META_FILE" 2>/dev/null)
        local now=$(date +%s)
        local elapsed=0
        if [ -n "$start_time" ]; then
            elapsed=$((now - start_time))
        fi
        local timer=$(printf '%02d:%02d' $((elapsed/60)) $((elapsed%60)))
        echo "{\"text\": \"🔴 $timer\", \"class\": \"recording\", \"tooltip\": \"Screen Recording Active ($timer)\\nLeft-Click: Stop Recording\"}"
    else
        echo "{\"text\": \"󰻃 Record\", \"class\": \"idle\", \"tooltip\": \"Screen Recorder\\nLeft-Click: Fullscreen Record\\nRight-Click: Select Region Record\"}"
    fi
}

case "$1" in
    --start-full)
        if is_recording; then stop_recording; else start_recording ""; fi
        ;;
    --region)
        if is_recording; then
            stop_recording
        else
            REGION=$(slurp)
            if [ -n "$REGION" ]; then
                start_recording "$REGION"
            fi
        fi
        ;;
    --stop)
        stop_recording
        ;;
    --status)
        get_status_json
        ;;
    --toggle|*)
        if is_recording; then stop_recording; else start_recording ""; fi
        ;;
esac
