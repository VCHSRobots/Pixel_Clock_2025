
function log(msg) {
    // Client side logging now just goes to console, 
    // UI shows persistent server logs.
    console.log(`[Client] ${msg}`);
}

async function def_fetch() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Update Clock
        const h = String(data.time[0]).padStart(2, '0');
        const m = String(data.time[1]).padStart(2, '0');
        const s = String(data.time[2]).padStart(2, '0');
        document.getElementById('clock-preview').innerText = `${h}:${m}:${s}`;

        // Update Date
        if (data.date) {
            const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

            const wdayStr = days[data.date.wday] || "???";
            const monStr = months[data.date.month - 1] || "???";

            document.getElementById('date-preview').innerText =
                `${wdayStr}, ${monStr} ${data.date.day}, ${data.date.year}`;
        } else {
            document.getElementById('date-preview').innerText = "";
        }

        // Update Inputs (only if not recently edited)
        if (Date.now() - lastEditTime > UNSAVED_TIMEOUT) {
            document.getElementById('unsaved-icon').classList.remove('visible');

            if (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
                const briVal = document.getElementById('bri-val');
                if (briVal) briVal.innerText = Math.round(data.brightness * 100) + '%';

                const briInput = document.getElementById('brightness');
                if (briInput) briInput.value = Math.round(data.brightness * 100);

                const colDigits = document.getElementById('color-digits');
                if (colDigits) colDigits.value = data.color;

                const colColon = document.getElementById('color-colon');
                if (colColon) colColon.value = data.colon_color;

                const colSeconds = document.getElementById('color-seconds');
                if (colSeconds && data.seconds_color) {
                    colSeconds.value = data.seconds_color;
                }

                const fmtMode = document.getElementById('format-mode');
                if (fmtMode) fmtMode.value = data.mode;

                const twHour = document.getElementById('twelve-hour');
                if (twHour) twHour.value = data.twelve_hour.toString();

                const tzOff = document.getElementById('timezone-offset');
                if (tzOff && data.timezone_offset !== undefined) {
                    tzOff.value = data.timezone_offset;
                }

                const blnkColon = document.getElementById('blink-colon');
                if (blnkColon && data.blink_mode !== undefined) {
                    blnkColon.checked = (data.blink_mode > 0);
                }

                const rot = document.getElementById('rotation');
                if (rot && data.rotation !== undefined) {
                    rot.checked = data.rotation;
                }
            }
        }

        // Update persistent logs
        if (data.logs) {
            const logEl = document.getElementById('status-log');
            if (logEl) {
                if (data.logs.length > 0) {
                    logEl.innerHTML = data.logs.join('<br>');
                } else {
                    logEl.innerHTML = "[System] No persistent logs found.";
                }
            }
        }

    } catch (e) {
        console.error(e);
    }
}

let lastEditTime = 0;
const UNSAVED_TIMEOUT = 30000;

function markDirty() {
    lastEditTime = Date.now();
    const icon = document.getElementById('unsaved-icon');
    if (icon) icon.classList.add('visible');
}

// Add listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input, select').forEach(el => {
        el.addEventListener('input', markDirty);
        el.addEventListener('change', markDirty);
    });
});


async function saveSettings() {
    const settings = {
        brightness: document.getElementById('brightness').value / 100,
        color: document.getElementById('color-digits').value,
        colon_color: document.getElementById('color-colon').value,
        seconds_color: document.getElementById('color-seconds').value,
        mode: parseInt(document.getElementById('format-mode').value),
        twelve_hour: document.getElementById('twelve-hour').value === 'true',
        twelve_hour: document.getElementById('twelve-hour').value === 'true',
        colon_blink_mode: document.getElementById('blink-colon').checked ? 1 : 0,
        rotation: document.getElementById('rotation').checked,
        timezone_offset: parseInt(document.getElementById('timezone-offset').value)
    };

    log('Saving settings...');
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        log('Settings saved.');
        lastEditTime = 0; // Clear dirty flag
        document.getElementById('unsaved-icon').classList.remove('visible');
        def_fetch(); // Refresh immediately
    } catch (e) {
        log('Error saving settings.');
    }
}

async function playAnim(name) {
    log(`Requesting animation: ${name}`);
    const payload = { name: name };
    if (name === 'scroll_custom') {
        payload.text = document.getElementById('scroll-text').value || "Hello World";
    }

    await fetch('/api/animation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
}

async function stopAnim() {
    log('Stopping animation...');
    await fetch('/api/animation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'stop' })
    });
}

async function forceNTPSync() {
    if (!confirm('Force NTP sync? This will update the clock time regardless of the current time difference.')) {
        return;
    }
    
    try {
        const res = await fetch('/api/force_ntp_sync', {
            method: 'POST'
        });
        const data = await res.json();
        
        if (data.status === 'ok') {
            alert('NTP sync initiated successfully. Check system logs for results.');
            log('Force NTP sync requested');
        } else {
            alert('Failed to sync: ' + (data.message || 'Unknown error'));
        }
    } catch (e) {
        console.error(e);
        alert('Error initiating NTP sync');
    }
}

setInterval(def_fetch, 1000);
def_fetch();

/* --- TABS & ALARMS LOGIC --- */

function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(`tab-${tab}`).classList.add('active');
    document.getElementById(`btn-tab-${tab}`).classList.add('active');

    if (tab === 'alarms') {
        fetchAlarms();
    }
}

/* --- ALARM MANAGER --- */
let alarms = [];
let currentAlarmId = null;
let selectedDays = [];

async function fetchAlarms() {
    try {
        const res = await fetch('/api/alarms');
        alarms = await res.json();
        renderAlarms();
    } catch (e) {
        console.error("Fetch Alarms Error", e);
    }
}

function renderAlarms() {
    const list = document.getElementById('alarm-list');
    if (!list) return;
    list.innerHTML = "";

    if (alarms.length === 0) {
        list.innerHTML = '<div style="text-align:center; color:#666; padding:20px;">No alarms set</div>';
        return;
    }

    alarms.forEach(alarm => {
        const div = document.createElement('div');
        div.className = 'alarm-item';

        let info = `<strong>${alarm.schedule.time}</strong>`;
        if (alarm.type === 'repetitive') {
            if (alarm.schedule.frequency === 'daily') {
                // Show days
                const d = alarm.schedule.days || [];
                if (d.length === 0 || d.length === 7) info += " (Every day)";
                else info += " (" + d.map(i => ["M", "T", "W", "T", "F", "S", "S"][i]).join(" ") + ")";
            } else {
                info += ` (${alarm.schedule.frequency})`;
            }
        } else {
            info += ` (${alarm.schedule.date})`;
        }

        // Status indicator
        const status = alarm.enabled ? '<span style="color:#03dac6">ON</span>' : '<span style="color:#666">OFF</span>';

        const enabledText = alarm.enabled ? "Disable" : "Enable";

        div.innerHTML = `
            <div class="alarm-info">
                <h3>${alarm.name || "Alarm"} ${status}</h3>
                <p>${info}</p>
            </div>
            <div class="alarm-actions">
                <button onclick="toggleAlarmEnabled('${alarm.id}', ${!alarm.enabled})">${enabledText}</button>
                <button onclick="openAlarmModal('${alarm.id}')">Edit</button>
            </div>
        `;
        list.appendChild(div);
    });
}

function toggleAlarmEnabled(id, state) {
    const alarm = alarms.find(a => a.id === id);
    if (alarm) {
        alarm.enabled = state;
        // Optimization: Optimistic update
        saveAlarmRequest('update', alarm).then(fetchAlarms);
    }
}

/* --- MODAL --- */
function openAlarmModal(id = null) {
    currentAlarmId = id;
    const modal = document.getElementById('alarm-modal');
    const deleteBtn = document.getElementById('btn-delete-alarm');

    // Reset Fields
    selectedDays = [];
    document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('alarm-name').value = "";
    document.getElementById('alarm-time').value = "07:00";
    document.getElementById('alarm-freq').value = "daily";
    // Default date today
    document.getElementById('alarm-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('action-type').value = "scroll";
    document.getElementById('action-text').value = "";
    document.getElementById('action-color').value = "#ff0000";
    document.getElementById('action-duration').value = 60;

    // Reset New Fields
    document.getElementById('action-brightness').value = 1.0;
    document.getElementById('action-bri-val').innerText = "1.0";
    document.getElementById('action-dur-type').value = "seconds";

    if (id) {
        const alarm = alarms.find(a => a.id === id);
        if (alarm) {
            document.getElementById('modal-title').innerText = "Edit Alarm";
            if (deleteBtn) deleteBtn.style.display = "inline-block";

            // Populate
            document.getElementById('alarm-name').value = alarm.name || "";
            document.getElementById('alarm-time').value = alarm.schedule.time || "07:00";
            document.getElementById('alarm-freq').value = alarm.type === 'oneshot' ? 'oneshot' : (alarm.schedule.frequency || 'daily');

            if (alarm.schedule.days) {
                selectedDays = [...alarm.schedule.days];
                selectedDays.forEach(d => {
                    const el = document.getElementById(`day-${d}`);
                    if (el) el.classList.add('selected');
                });
            }
            if (alarm.schedule.date) {
                document.getElementById('alarm-date').value = alarm.schedule.date;
            }

            // Action
            if (alarm.action) {
                document.getElementById('action-type').value = alarm.action.type;
                if (alarm.action.payload) {
                    document.getElementById('action-text').value = alarm.action.payload.text || "";
                    document.getElementById('action-color').value = alarm.action.payload.color || "#ff0000";
                    let bri = alarm.action.payload.brightness || 1.0;
                    document.getElementById('action-brightness').value = bri;
                    document.getElementById('action-bri-val').innerText = bri;
                }

                document.getElementById('action-dur-type').value = alarm.action.duration_type || 'seconds';
                document.getElementById('action-duration').value = alarm.action.duration_sec || 60;
            }
        }
    } else {
        document.getElementById('modal-title').innerText = "New Alarm";
        if (deleteBtn) deleteBtn.style.display = "none";
        // Default Days = Mon-Fri
        [0, 1, 2, 3, 4].forEach(d => toggleDay(d));
    }

    toggleAlarmType();
    toggleActionType();
    toggleDurationType();
    modal.classList.add('visible');
}

function closeModal() {
    document.getElementById('alarm-modal').classList.remove('visible');
}

function toggleDay(day) {
    if (selectedDays.includes(day)) {
        selectedDays = selectedDays.filter(d => d !== day);
        document.getElementById(`day-${day}`).classList.remove('selected');
    } else {
        selectedDays.push(day);
        document.getElementById(`day-${day}`).classList.add('selected');
    }
}

function toggleAlarmType() {
    const type = document.getElementById('alarm-freq').value;
    const daySec = document.getElementById('section-days');
    const dateSec = document.getElementById('section-date');

    if (type === 'oneshot') {
        daySec.style.display = 'none';
        dateSec.style.display = 'block';
    } else {
        daySec.style.display = 'block';
        dateSec.style.display = 'none';
    }
}

function toggleActionType() {
    const type = document.getElementById('action-type').value;
    const textSec = document.getElementById('section-text');
    if (type === 'scroll') {
        textSec.style.display = 'block';
    } else {
        textSec.style.display = 'none';
    }
}

function toggleDurationType() {
    const type = document.getElementById('action-dur-type').value;
    const lbl = document.getElementById('lbl-duration');
    if (type === 'loops') {
        lbl.innerText = "Count (Loops)";
    } else {
        lbl.innerText = "Value (Sec)";
    }
}

async function saveAlarm() {
    // Validation
    const textVal = document.getElementById('action-text').value;
    if (textVal.length > 250) {
        alert("Text too long (Max 250 chars). Current: " + textVal.length);
        return;
    }

    const name = document.getElementById('alarm-name').value || "Alarm";
    const timeVal = document.getElementById('alarm-time').value;
    const freqType = document.getElementById('alarm-freq').value;

    const alarm = {
        enabled: true,
        name: name,
        type: freqType === 'oneshot' ? 'oneshot' : 'repetitive',
        schedule: {
            time: timeVal,
            frequency: freqType === 'oneshot' ? undefined : freqType,
            days: freqType === 'daily' ? selectedDays : undefined,
            date: freqType === 'oneshot' ? document.getElementById('alarm-date').value : undefined
        },
        action: {
            type: document.getElementById('action-type').value,
            duration_type: document.getElementById('action-dur-type').value,
            duration_sec: parseInt(document.getElementById('action-duration').value),
            payload: {
                text: document.getElementById('action-text').value,
                color: document.getElementById('action-color').value,
                brightness: parseFloat(document.getElementById('action-brightness').value)
            }
        }
    };

    try {
        if (currentAlarmId) {
            alarm.id = currentAlarmId;
            await saveAlarmRequest('update', alarm);
        } else {
            await saveAlarmRequest('add', alarm);
        }

        closeModal();
        fetchAlarms();
    } catch (e) {
        // Error alert shown in saveAlarmRequest
    }
}

async function deleteAlarm() {
    if (currentAlarmId && confirm("Delete this alarm?")) {
        await saveAlarmRequest('delete', { id: currentAlarmId });
        closeModal();
        fetchAlarms();
    }
}

async function saveAlarmRequest(cmd, alarmData) {
    try {
        const payload = { cmd: cmd };
        if (cmd === 'delete') {
            payload.id = alarmData.id;
        } else {
            payload.alarm = alarmData;
            if (cmd === 'update') payload.id = alarmData.id;
        }

        const res = await fetch('/api/alarms', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok || data.status === 'error') {
            alert("Error: " + (data.message || "Operation failed"));
            throw new Error(data.message);
        }

    } catch (e) {
        console.error(e);
        if (!e.message) alert("Network/Server Error");
        throw e;
    }
}
