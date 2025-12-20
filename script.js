
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

        // Update Inputs (only if not recently edited)
        if (Date.now() - lastEditTime > UNSAVED_TIMEOUT) {
            document.getElementById('unsaved-icon').classList.remove('visible');

            if (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
                document.getElementById('bri-val').innerText = Math.round(data.brightness * 100) + '%';
                document.getElementById('brightness').value = Math.round(data.brightness * 100);
                document.getElementById('color-digits').value = data.color;
                document.getElementById('color-colon').value = data.colon_color;
                if (data.seconds_color) {
                    document.getElementById('color-seconds').value = data.seconds_color;
                }
                document.getElementById('format-mode').value = data.mode;
                document.getElementById('twelve-hour').value = data.twelve_hour.toString();
                if (data.timezone_offset !== undefined) {
                    document.getElementById('timezone-offset').value = data.timezone_offset;
                }
            }
        }

        // Update persistent logs
        if (data.logs) {
            const logEl = document.getElementById('status-log');
            if (data.logs.length > 0) {
                logEl.innerHTML = data.logs.join('<br>');
            } else {
                logEl.innerHTML = "[System] No persistent logs found.";
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
    document.getElementById('unsaved-icon').classList.add('visible');
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

setInterval(def_fetch, 1000);
def_fetch();
