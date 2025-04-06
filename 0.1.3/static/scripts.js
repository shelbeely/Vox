// Vox - Client-Side JavaScript
// Crafted with pride by Shelbeely (https://github.com/shelbeely), a trans woman developer
// This script brings Vox to life in your browser, making voice training interactive and affirming
// Licensed under GPL-3.0 - Open source, trans-powered!

// Get cookie value - Vox remembers your session
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

const sessionId = getCookie('session_id') || 'default';
const socket = io({ query: { sessionId: sessionId } });
let isRecording = false;
let audioContext;
let analyser;
let source;
let stream;
let pitchDetector;
let pitchSmoother;
let volumeMeter;
let fft;
let targetOscillator = null;
let recorder = null;
let recordingBlob = null;
const MAX_RECORDING_TIME = 5 * 60 * 1000;
const CHUNK = 2048;
const AUDIO_BUFFER_INTERVAL = 100;
const PITCH_STABILITY_WINDOW = 5;
let pitchHistory = [];

// Pitch chart
const pitchChart = new Chart(document.getElementById('pitchChart').getContext('2d'), {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Pitch (Hz)', data: [], borderColor: '#5BCEFA', borderWidth: 2, pointRadius: 0, fill: false }] },
    options: {
        animation: { duration: 500, easing: 'easeOutQuad' },
        scales: {
            x: { title: { display: true, text: 'Time', color: '#E8ECEF' } },
            y: { title: { display: true, text: 'Pitch (Hz)', color: '#E8ECEF' }, min: 0, max: 500, grid: { color: '#424242' } }
        },
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#E8ECEF' } }, tooltip: { enabled: true } }
    }
});

// Pitch gauge
const pitchGauge = new JustGage({
    id: "pitchGauge",
    value: 0,
    min: 50,
    max: 400,
    title: "Pitch",
    label: "Hz",
    gaugeWidthScale: 0.6,
    customSectors: {
        ranges: [
            { from: 50, to: 85, color: "#F5A9B8" },
            { from: 85, to: 400, color: "#5BCEFA" }
        ]
    },
    levelColors: ["#F5A9B8", "#5BCEFA"],
    pointer: true,
    pointerOptions: { toplength: 10, bottomlength: 10, bottomwidth: 2 },
    decimals: 1
});

// HNR gauge
const hnrGauge = new JustGage({
    id: "hnrGauge",
    value: 0,
    min: -10,
    max: 40,
    title: "HNR",
    label: "dB",
    gaugeWidthScale: 0.6,
    customSectors: {
        ranges: [
            { from: -10, to: 10, color: "#F5A9B8" },
            { from: 10, to: 40, color: "#5BCEFA" }
        ]
    },
    levelColors: ["#F5A9B8", "#5BCEFA"],
    pointer: true,
    pointerOptions: { toplength: 10, bottomlength: 10, bottomwidth: 2 },
    decimals: 1
});

// Pitch stability chart
const pitchStabilityChart = new Chart(document.getElementById('pitchStabilityChart').getContext('2d'), {
    type: 'doughnut',
    data: {
        labels: ['Stability'],
        datasets: [{
            data: [0, 100],
            backgroundColor: ['#5BCEFA', '#424242'],
            borderWidth: 0
        }]
    },
    options: {
        animation: { duration: 500, easing: 'easeOutQuad' },
        cutout: '70%',
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
            title: {
                display: true,
                text: 'Pitch Stability (%)',
                color: '#E8ECEF',
                font: { size: 14 }
            }
        },
        maintainAspectRatio: false
    }
});

// Harmonics chart
const harmonicsChart = new Chart(document.getElementById('harmonicsChart').getContext('2d'), {
    type: 'bar',
    data: { labels: ['H1', 'H2', 'H3', 'H4', 'H5'], datasets: [{ label: 'Amplitude', data: [0, 0, 0, 0, 0], backgroundColor: '#F5A9B8' }] },
    options: {
        animation: { duration: 500, easing: 'easeOutQuad' },
        scales: { y: { title: { display: true, text: 'Amplitude', color: '#E8ECEF' }, beginAtZero: true, grid: { color: '#424242' } } },
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#E8ECEF' } }, tooltip: { enabled: true } }
    }
});

// HNR chart
const hnrChart = new Chart(document.getElementById('hnrChart').getContext('2d'), {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'HNR (dB)', data: [], borderColor: '#5BCEFA', borderWidth: 2, pointRadius: 0, fill: false }] },
    options: {
        animation: { duration: 500, easing: 'easeOutQuad' },
        scales: {
            x: { title: { display: true, text: 'Time', color: '#E8ECEF' } },
            y: { title: { display: true, text: 'HNR (dB)', color: '#E8ECEF' }, min: -10, max: 40, grid: { color: '#424242' } }
        },
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#E8ECEF' } }, tooltip: { enabled: true } }
    }
});

// Formants chart
const formantsChart = new Chart(document.getElementById('formantsChart').getContext('2d'), {
    type: 'bar',
    data: { labels: ['F1', 'F2', 'F3'], datasets: [
        { label: 'Frequency (Hz)', data: [0, 0, 0], backgroundColor: '#5BCEFA' },
        { label: 'Bandwidth (Hz)', data: [0, 0, 0], backgroundColor: '#F5A9B8' }
    ]},
    options: {
        animation: { duration: 500, easing: 'easeOutQuad' },
        scales: { y: { title: { display: true, text: 'Hz', color: '#E8ECEF' }, min: 0, max: 3000, grid: { color: '#424242' } } },
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#E8ECEF' } }, tooltip: { enabled: true } }
    }
});

// Convert Hz to musical note
function hzToNote(hz) {
    if (hz <= 0) return "N/A";
    const A4 = 440;
    const semitonesFromA4 = 12 * Math.log2(hz / A4);
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(semitonesFromA4 / 12) + 4;
    const semitone = Math.round(semitonesFromA4 % 12 + 12) % 12;
    return `${noteNames[semitone]}${octave}`;
}

// Calculate pitch stability
function calculatePitchStability(pitch) {
    pitchHistory.push(pitch);
    if (pitchHistory.length > PITCH_STABILITY_WINDOW * 10) pitchHistory.shift();
    if (pitchHistory.length < 2) return 0;
    const mean = pitchHistory.reduce((a, b) => a + b, 0) / pitchHistory.length;
    const variance = pitchHistory.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / pitchHistory.length;
    const stdDev = Math.sqrt(variance);
    const stability = Math.max(0, 100 - (stdDev / mean) * 100);
    return Math.min(100, stability);
}

// Start recording
async function startRecording() {
    if (!isRecording) {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = CHUNK;
            source.connect(analyser);

            pitchDetector = new Tone.PitchDetect();
            pitchSmoother = new Tone.Meter({ smoothing: 0.05 });
            volumeMeter = new Tone.Meter();
            fft = new Tone.FFT(2048);
            recorder = new Tone.Recorder();

            await Tone.start();
            source.connect(pitchDetector);
            pitchDetector.connect(pitchSmoother);
            source.connect(volumeMeter);
            source.connect(fft);
            source.connect(recorder);
            await recorder.start();

            pitchDetector.on('pitch', (pitch) => {
                if (pitch > 20) {
                    const smoothedPitch = pitchSmoother.getValue() * pitch;
                    const note = hzToNote(smoothedPitch);
                    const display = document.getElementById("pitchDisplay");
                    display.innerText = `Pitch (real-time): ${smoothedPitch.toFixed(2)} Hz (${note})`;
                    display.className = "pitch-display " + (smoothedPitch > 85 && smoothedPitch < 400 ? "in-range" : "out-of-range");
                    display.classList.remove('update-anim');
                    void display.offsetWidth;
                    display.classList.add('update-anim');
                }
            });

            setInterval(() => {
                const volume = volumeMeter.getValue();
                if (volume > -30) {
                    document.getElementById("volumeDisplay").innerText = `Volume: ${volume.toFixed(2)} dB`;
                }
                const spectrum = fft.getValue();
                const f1Range = spectrum.slice(300, 1000).reduce((max, val, i) => val > max.val ? {val, i: i + 300} : max, {val: -Infinity, i: 0});
                const f2Range = spectrum.slice(1000, 2000).reduce((max, val, i) => val > max.val ? {val, i: i + 1000} : max, {val: -Infinity, i: 0});
                document.getElementById("resonanceDisplay").innerText = `F1: ${f1Range.i} Hz, F2: ${f2Range.i} Hz`;
            }, 100);

            isRecording = true;
            socket.emit("start_recording");
            sendAudioChunks();

            setTimeout(() => {
                if (isRecording) stopRecording();
            }, MAX_RECORDING_TIME);
        } catch (err) {
            console.error('Error starting recording:', err);
            showError(`Failed to access microphone: ${err.name} - ${err.message}`);
            isRecording = false;
        }
    }
}

// Stop recording
function stopRecording() {
    if (isRecording) {
        isRecording = false;
        stream.getTracks().forEach(track => track.stop());
        audioContext.close();
        pitchDetector.dispose();
        pitchSmoother.dispose();
        volumeMeter.dispose();
        fft.dispose();
        stopTargetPitch();
        saveAndStopRecording();
        socket.emit("stop_recording");
    }
}

// Send audio chunks
function sendAudioChunks() {
    if (!isRecording) return;
    const dataArray = new Float32Array(CHUNK);
    analyser.getFloatTimeDomainData(dataArray);
    socket.emit('raw_audio', {
        audio: Array.from(dataArray),
        timestamp: new Date().toISOString()
    });
    setTimeout(sendAudioChunks, AUDIO_BUFFER_INTERVAL);
}

// Start target pitch
function startTargetPitch(hz) {
    if (!targetOscillator) {
        targetOscillator = new Tone.Oscillator(hz, 'sine').toDestination();
        targetOscillator.volume.value = -20;
        targetOscillator.start();
    }
}

// Stop target pitch
function stopTargetPitch() {
    if (targetOscillator) {
        targetOscillator.stop();
        targetOscillator.dispose();
        targetOscillator = null;
    }
}

// Save and stop recording
async function saveAndStopRecording() {
    if (recorder) {
        recordingBlob = await recorder.stop();
        const formData = new FormData();
        formData.append('recording', recordingBlob, 'recording.wav');
        formData.append('timestamp', new Date().toISOString());

        fetch('/save_recording', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                socket.emit('save_recording', {
                    timestamp: formData.get('timestamp'),
                    recording_path: data.recording_path,
                    pitch: pitchChart.data.datasets[0].data.slice(-1)[0] || 0,
                    hnr: hnrChart.data.datasets[0].data.slice(-1)[0] || 0,
                    harmonics: JSON.parse(document.getElementById("historyList").firstChild?.dataset.harmonics || '[]'),
                    formants: JSON.parse(document.getElementById("historyList").firstChild?.dataset.formants || '[]')
                });
            }
        })
        .catch(error => console.error('Error saving recording:', error));
        recorder.dispose();
        recorder = null;
    }
}

// Play recording
function playRecording(path) {
    const player = new Tone.Player(path).toDestination();
    player.start();
}

// SocketIO event handlers
socket.on('connect', () => console.log('SocketIO connected with session ID:', sessionId));
socket.on('connect_error', (error) => {
    console.error('SocketIO connection error:', error);
    showError('Failed to connect to server. Please refresh.');
});

socket.on("audio_analysis", (data) => {
    const now = new Date().toLocaleTimeString();
    const pitch = data.pitch;
    const hnr = data.hnr;
    const harmonics = data.harmonics;
    const formants = data.formants;
    const stability = calculatePitchStability(pitch);

    const display = document.getElementById("pitchDisplay");
    display.innerText = `Pitch: ${pitch.toFixed(2)} Hz (${hzToNote(pitch)})\nHNR: ${hnr.toFixed(2)} dB\nStability: ${stability.toFixed(1)}%`;
    display.className = "pitch-display " + (pitch > 85 && pitch < 400 ? "in-range" : "out-of-range");
    display.setAttribute('aria-label', `Current pitch: ${pitch.toFixed(2)} Hz, HNR: ${hnr.toFixed(2)} dB, Stability: ${stability.toFixed(1)}%`);
    display.classList.remove('update-anim');
    void display.offsetWidth;
    display.classList.add('update-anim');

    pitchChart.data.labels.push(now);
    pitchChart.data.datasets[0].data.push(pitch);
    if (pitchChart.data.labels.length > 20) {
        pitchChart.data.labels.shift();
        pitchChart.data.datasets[0].data.shift();
    }
    pitchChart.update('active');
    pitchGauge.refresh(pitch);
    hnrGauge.refresh(hnr);
    pitchStabilityChart.data.datasets[0].data = [stability, 100 - stability];
    pitchStabilityChart.update('active');
    hnrChart.data.labels.push(now);
    hnrChart.data.datasets[0].data.push(hnr);
    if (hnrChart.data.labels.length > 20) {
        hnrChart.data.labels.shift();
        hnrChart.data.datasets[0].data.shift();
    }
    hnrChart.update('active');
    const paddedHarmonics = harmonics.concat(Array(5 - harmonics.length).fill({amp: 0}));
    harmonicsChart.data.datasets[0].data = paddedHarmonics.map(h => h.amp);
    harmonicsChart.update('active');
    const paddedFormants = formants.concat(Array(3 - formants.length).fill({freq: 0, bw: 0}));
    formantsChart.data.datasets[0].data = paddedFormants.map(f => f.freq);
    formantsChart.data.datasets[1].data = paddedFormants.map(f => f.bw);
    formantsChart.update('active');
});

socket.on("history_update", (data) => {
    const listItem = document.createElement("li");
    const timestamp = new Date(data.timestamp).toLocaleString();
    listItem.innerHTML = `
        <span class="material-icons">history</span> 
        ${timestamp}: Pitch=${data.pitch.toFixed(2)} Hz, HNR=${data.hnr.toFixed(2)} dB, Harmonics=${data.harmonics.length}, Formants=${data.formants.map(f => `${f.freq.toFixed(0)} Hz`).join(', ')}
        ${data.recording_path ? `<button class="media-button" onclick="playRecording('${data.recording_path}')" aria-label="Play Recording"><span class="material-icons">play_arrow</span></button>` : ''}
    `;
    listItem.dataset.harmonics = JSON.stringify(data.harmonics);
    listItem.dataset.formants = JSON.stringify(data.formants);
    document.getElementById("historyList").prepend(listItem);
});

socket.on("history_cleared", () => {
    document.getElementById("historyList").innerHTML = "";
});

socket.on("llm_feedback", (data) => {
    const listItem = document.createElement("li");
    listItem.innerHTML = `<span class="material-icons">comment</span> Feedback (${new Date().toLocaleTimeString()}): ${data.feedback}`;
    document.getElementById("llmOutput").prepend(listItem);
});

socket.on("chat_response", (data) => {
    const listItem = document.createElement("li");
    listItem.innerHTML = `<span class="material-icons">chat</span> Vox: ${data.message}`;
    document.getElementById("llmOutput").prepend(listItem);
});

socket.on("recording_status", (data) => {
    const recordButton = document.getElementById("recordButton");
    const stopButton = document.getElementById("stopButton");
    if (data.status === "started") {
        recordButton.style.display = "none";
        stopButton.style.display = "inline-flex";
        showError(data.message);
    } else if (data.status === "stopped") {
        isRecording = false;
        recordButton.style.display = "inline-flex";
        stopButton.style.display = "none";
        hideError();
    }
});

fetch('/get_performances')
    .then(response => response.json())
    .then(data => {
        data.forEach(performance => {
            const listItem = document.createElement("li");
            const timestamp = new Date(performance.timestamp).toLocaleString();
            listItem.innerHTML = `
                <span class="material-icons">history</span> 
                ${timestamp}: Pitch=${performance.pitch.toFixed(2)} Hz, HNR=${performance.hnr.toFixed(2)} dB, Harmonics=${performance.harmonics.length}, Formants=${performance.formants.map(f => `${f.freq.toFixed(0)} Hz`).join(', ')}
                ${performance.recording_path ? `<button class="media-button" onclick="playRecording('${performance.recording_path}')" aria-label="Play Recording"><span class="material-icons">play_arrow</span></button>` : ''}
            `;
            listItem.dataset.harmonics = JSON.stringify(performance.harmonics);
            listItem.dataset.formants = JSON.stringify(performance.formants);
            document.getElementById("historyList").appendChild(listItem);
        });
    })
    .catch(error => {
        console.error('Error fetching performances:', error);
        showError('Failed to load history.');
    });

function clearHistory() {
    fetch('/clear_history', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status !== "success") showError('Failed to clear history.');
        })
        .catch(error => {
            console.error('Error clearing history:', error);
            showError('Failed to clear history.');
        });
}

function updateUserInfo() {
    const userName = document.getElementById("userName").value;
    const userPronouns = document.getElementById("userPronouns").value;
    const targetGender = document.getElementById("targetGender").value;
    if (userName) {
        fetch('/set_user_info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: userName, pronouns: userPronouns })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                updateTargetGender(targetGender);
                const inputDiv = document.getElementById("userInfoInput");
                const summaryDiv = document.getElementById("userInfoSummary");
                inputDiv.classList.add('slide-out');
                setTimeout(() => {
                    inputDiv.style.display = "none";
                    inputDiv.classList.remove('slide-out');
                    summaryDiv.style.display = "flex";
                    summaryDiv.classList.add('slide-in');
                    document.getElementById("summaryText").textContent = `${userName} (${userPronouns.split('/')[0]}, ${targetGender})`;
                    setTimeout(() => summaryDiv.classList.remove('slide-in'), 300);
                }, 300);
            } else {
                showError(data.message || 'Failed to update info.');
            }
        })
        .catch(error => {
            console.error('Error updating user info:', error);
            showError('Failed to update info.');
        });
    } else {
        showError("Please enter a name.");
    }
}

function editUserInfo() {
    const inputDiv = document.getElementById("userInfoInput");
    const summaryDiv = document.getElementById("userInfoSummary");
    summaryDiv.classList.add('slide-out');
    setTimeout(() => {
        summaryDiv.style.display = "none";
        summaryDiv.classList.remove('slide-out');
        inputDiv.style.display = "flex";
        inputDiv.classList.add('slide-in');
        setTimeout(() => inputDiv.classList.remove('slide-in'), 300);
    }, 300);
}

function updateTargetGender(targetGender) {
    fetch('/set_target_gender', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: targetGender })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const targetHz = targetGender === "feminine" ? 200 : targetGender === "masculine" ? 120 : 150;
            stopTargetPitch();
            startTargetPitch(targetHz);
            const ranges = targetGender === "feminine"
                ? [{ from: 50, to: 180, color: "#F5A9B8" }, { from: 180, to: 400, color: "#5BCEFA" }]
                : targetGender === "masculine" ? [{ from: 50, to: 100, color: "#5BCEFA" }, { from: 100, to: 400, color: "#F5A9B8" }]
                : [{ from: 50, to: 85, color: "#F5A9B8" }, { from: 85, to: 400, color: "#5BCEFA" }];
            pitchGauge.config.customSectors.ranges = ranges;
            pitchGauge.refresh(pitchGauge.config.value);
        } else {
            showError(data.message || 'Failed to update target gender.');
        }
    })
    .catch(error => {
        console.error('Error updating target gender:', error);
        showError('Failed to update target gender.');
    });
}

function sendChat() {
    const message = document.getElementById("chatInput").value;
    if (message) {
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                document.getElementById("chatInput").value = "";
            } else {
                showError(data.message || 'Failed to send chat.');
            }
        })
        .catch(error => {
            console.error('Error sending chat:', error);
            showError('Failed to send chat.');
        });
    }
}

function showError(msg) {
    const errorBox = document.getElementById("errorBox");
    errorBox.innerHTML = `<span class="material-icons">error_outline</span> ${msg}`;
    errorBox.style.display = "block";
    errorBox.classList.remove('fade-in');
    void errorBox.offsetWidth;
    errorBox.classList.add('fade-in');
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add('fade-out');
    setTimeout(() => {
        errorBox.style.display = "none";
        errorBox.classList.remove('fade-out');
    }, 300);
}

document.getElementById("recordButton").addEventListener("click", startRecording);
document.getElementById("stopButton").addEventListener("click", stopRecording);
document.getElementById("startTargetButton").addEventListener("click", () => {
    const hz = parseFloat(document.getElementById("targetPitch").value);
    stopTargetPitch();
    startTargetPitch(hz);
});
document.getElementById("stopTargetButton").addEventListener("click", stopTargetPitch);
document.getElementById("targetGender").addEventListener("change", () => updateTargetGender(document.getElementById("targetGender").value));

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement === document.getElementById("chatInput")) sendChat();
    if (e.key === 'r' && !isRecording) startRecording();
    if (e.key === 's' && isRecording) stopRecording();
});
