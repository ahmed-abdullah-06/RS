// ============================================================
//  R.S. - Red Shirt AI Assistant v2.0
//  renderer.js — Frontend logic + Neural Core animation
// ============================================================

const { ipcRenderer } = require('electron')

const API = 'http://127.0.0.1:5000'

// State
let isThinking    = false
let voiceMode     = false
let lastInput     = ''
let lastResponse  = ''
let tasks         = []
let waveInterval  = null

// ── BOOT ─────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    initNeuralCanvas()
    initWaveform()
    loadStats()
    loadTasks()
    showGreeting()
    setInterval(loadStats, 15000)
})

// ── WINDOW CONTROLS ───────────────────────────────────────
function minimizeWindow() { ipcRenderer.send('minimize-window') }
function maximizeWindow() { ipcRenderer.send('maximize-window') }
function closeWindow()    { ipcRenderer.send('close-window')    }

// ── TABS ──────────────────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'))
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'))
    document.getElementById(`tab-${name}`).classList.add('active')
    document.querySelectorAll('.tab').forEach(t => {
        if (t.textContent.toLowerCase().includes(name)) t.classList.add('active')
    })
    if (name === 'memory')    loadMemories()
    if (name === 'evolution') loadEvolution()
    if (name === 'tasks')     renderTasks()
}

// ── GREETING ──────────────────────────────────────────────
function showGreeting() {
    const h = new Date().getHours()
    const g = h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening'
    fetch(`${API}/stats`)
        .then(r => r.json())
        .then(d => {
            addMessage('ai', `System initialized. Red Shirt v${d.version} online.\n${g}! I have ${d.memories} memories loaded. How can I assist you today?`)
        })
        .catch(() => {
            addMessage('ai', `System initialized. Red Shirt online.\n${g}! How can I assist you today?`)
        })
}

// ── SEND MESSAGE ──────────────────────────────────────────
function handleKey(e) {
    if (e.key === 'Enter') sendMessage()
}

async function sendMessage() {
    if (isThinking) return
    const input = document.getElementById('commandInput')
    const text  = input.value.trim()
    if (!text) return

    input.value = ''
    lastInput   = text
    addMessage('user', text)

    isThinking = true
    setNeuralActive(true)
    const thinking = addMessage('ai', 'Processing...', true)

    try {
        const res  = await fetch(`${API}/chat`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ message: text })
        })
        const data = await res.json()
        lastResponse = data.response

        thinking.remove()
        addMessage('ai', data.response)

        // Speak
        fetch(`${API}/speak`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ text: data.response })
        })

        if (Math.random() < 0.2) setTimeout(showFeedback, 800)
        loadStats()

    } catch (err) {
        thinking.remove()
        addMessage('ai', `Connection error. Make sure Python server is running.`)
    }

    isThinking = false
    setNeuralActive(false)
}

// ── MARKDOWN PARSER ───────────────────────────────────────
function parseMarkdown(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
}

// ── ADD MESSAGE ───────────────────────────────────────────
function addMessage(type, text, thinking = false) {
    const container = document.getElementById('chatMessages')
    const wrapper   = document.createElement('div')
    wrapper.className = `message-wrapper ${type}`

    const div       = document.createElement('div')
    div.className   = `message ${type}${thinking ? ' thinking' : ''}`

    const sender = type === 'ai' ? 'RS' : 'YOU'
    const time   = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit'
    })

    div.innerHTML = `
        <div class="message-sender">${sender}</div>
        <div class="message-text">${parseMarkdown(text)}</div>
        <div class="message-time">${time}</div>
    `

    wrapper.appendChild(div)
    container.appendChild(wrapper)
    container.scrollTop = container.scrollHeight
    return wrapper
}

// ── STATS ─────────────────────────────────────────────────
async function loadStats() {
    try {
        const res  = await fetch(`${API}/stats`)
        const data = await res.json()

        document.getElementById('statMemory').textContent    = `${data.memories} Active`
        document.getElementById('statFeedback').textContent  = `${(data.feedback_score * 10).toFixed(1)}%`
        document.getElementById('statEvolution').textContent = `${data.storage_pct}% (Level ${data.version})`
        document.getElementById('neuralActivity').textContent = `${(data.feedback_score * 10).toFixed(1)}%`

        const memPct = Math.min(data.storage_pct, 100)
        document.getElementById('memBar').style.width = `${memPct}%`
        document.getElementById('fbBar').style.width  = `${Math.min(data.feedback_score * 10, 100)}%`
        document.getElementById('evoBar').style.width = `${data.storage_pct}%`

        const sv = document.getElementById('settingVersion')
        if (sv) sv.textContent = data.version

    } catch (e) {}
}

// ── MEMORIES TAB ──────────────────────────────────────────
async function loadMemories() {
    const list = document.getElementById('memoryList')
    list.innerHTML = '<div class="loading">Loading...</div>'
    try {
        const res  = await fetch(`${API}/memories`)
        const data = await res.json()
        const mems = data.memories.reverse()

        if (!mems.length) {
            list.innerHTML = '<div class="loading">No memories yet.</div>'
            return
        }

        list.innerHTML = ''
        mems.forEach(m => {
            const card = document.createElement('div')
            card.className = 'memory-card'
            card.innerHTML = `
                <div class="memory-time">${m.timestamp || ''}</div>
                <div class="memory-user">You: ${m.user || ''}</div>
                <div class="memory-rs">RS: ${(m.rs || '').substring(0, 120)}...</div>
            `
            list.appendChild(card)
        })
    } catch (e) {
        list.innerHTML = '<div class="loading">Could not load memories.</div>'
    }
}

// ── EVOLUTION TAB ─────────────────────────────────────────
async function loadEvolution() {
    try {
        const res  = await fetch(`${API}/stats`)
        const data = await res.json()

        document.getElementById('evoVersion').textContent  = data.version
        document.getElementById('evoMemories').textContent = data.memories
        document.getElementById('evoFeedback').textContent = data.feedback_score
        document.getElementById('evoStorage').textContent  = `${data.storage_pct}%`

        const pList = document.getElementById('evoPatterns')
        pList.innerHTML = ''
        const maxCount = data.patterns.length ? data.patterns[0].count : 1
        data.patterns.forEach(p => {
            const pct = Math.round((p.count / maxCount) * 100)
            const row = document.createElement('div')
            row.className = 'pattern-row'
            row.innerHTML = `
                <span class="pattern-word">${p.word}</span>
                <div class="pattern-bar-wrap">
                    <div class="pattern-bar-fill" style="width:${pct}%"></div>
                </div>
                <span class="pattern-count">${p.count}</span>
            `
            pList.appendChild(row)
        })
    } catch (e) {}
}

// ── TASKS ─────────────────────────────────────────────────
async function loadTasks() {
    try {
        const res  = await fetch(`${API}/tasks`)
        const data = await res.json()
        tasks = data.tasks
        renderTasks()
    } catch (e) {}
}

function renderTasks() {
    const list = document.getElementById('taskList')
    if (!tasks.length) {
        list.innerHTML = '<div class="loading">No tasks yet. Click + Add Task.</div>'
        return
    }
    list.innerHTML = ''
    tasks.forEach((task, i) => {
        const item = document.createElement('div')
        item.className = 'task-item'
        item.innerHTML = `
            <div class="task-check ${task.done ? 'done' : ''}"
                 onclick="toggleTask(${i})">${task.done ? '✓' : ''}</div>
            <span class="task-text ${task.done ? 'done' : ''}">${task.text}</span>
            <span class="task-time">${task.time || ''}</span>
            <button class="task-del" onclick="deleteTask(${i})">✕</button>
        `
        list.appendChild(item)
    })
}

function showAddTask()  { document.getElementById('taskDialog').style.display = 'flex' }
function hideAddTask()  { document.getElementById('taskDialog').style.display = 'none'  }

async function addTask() {
    const input = document.getElementById('taskInput')
    const text  = input.value.trim()
    if (!text) return
    await fetch(`${API}/tasks`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text, done: false })
    })
    input.value = ''
    hideAddTask()
    loadTasks()
}

async function toggleTask(i) {
    tasks[i].done = !tasks[i].done
    renderTasks()
}

async function deleteTask(i) {
    await fetch(`${API}/tasks`, {
        method:  'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ index: i })
    })
    loadTasks()
}

// ── FEEDBACK ──────────────────────────────────────────────
function showFeedback() {
    document.getElementById('feedbackDialog').style.display = 'flex'
}

async function submitFeedback(rating) {
    document.getElementById('feedbackDialog').style.display = 'none'
    await fetch(`${API}/feedback`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ rating, user: lastInput, rs: lastResponse })
    })
    loadStats()
}

// ── VOICE ─────────────────────────────────────────────────
function toggleVoice() {
    voiceMode = !voiceMode
    const btn = document.getElementById('micBtn')
    if (voiceMode) {
        btn.classList.add('active')
        startWaveAnimation()
        addMessage('ai', 'Voice mode activated. Listening...')
    } else {
        btn.classList.remove('active')
        stopWaveAnimation()
        addMessage('ai', 'Voice mode deactivated.')
    }
}

// ── WAVEFORM ──────────────────────────────────────────────
function initWaveform() {
    const container = document.getElementById('waveBars')
    for (let i = 0; i < 28; i++) {
        const bar = document.createElement('div')
        bar.className = 'wave-bar'
        bar.style.height = '3px'
        container.appendChild(bar)
    }
}

function startWaveAnimation() {
    waveInterval = setInterval(() => {
        document.querySelectorAll('.wave-bar').forEach(bar => {
            const h = Math.random() * 26 + 3
            bar.style.height  = `${h}px`
            bar.style.opacity = (Math.random() * 0.5 + 0.5).toString()
        })
    }, 90)
}

function stopWaveAnimation() {
    if (waveInterval) { clearInterval(waveInterval); waveInterval = null }
    document.querySelectorAll('.wave-bar').forEach(bar => {
        bar.style.height  = '3px'
        bar.style.opacity = '0.25'
    })
}

// ── NEURAL CANVAS ─────────────────────────────────────────
let neuralActive = false
let angle        = 0
let pulsePhase   = 0

function setNeuralActive(state) { neuralActive = state }

function initNeuralCanvas() {
    const canvas = document.getElementById('neuralCanvas')
    const ctx    = canvas.getContext('2d')

    function resize() {
        canvas.width  = canvas.offsetWidth
        canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    function draw() {
        const W  = canvas.width
        const H  = canvas.height
        const cx = W / 2
        const cy = H / 2

        ctx.clearRect(0, 0, W, H)

        // Deep background glow
        const bgG = ctx.createRadialGradient(cx, cy, 0, cx, cy, H * 0.7)
        bgG.addColorStop(0, neuralActive ? 'rgba(160,0,0,0.22)' : 'rgba(80,0,0,0.14)')
        bgG.addColorStop(0.5, neuralActive ? 'rgba(60,0,0,0.10)' : 'rgba(30,0,0,0.07)')
        bgG.addColorStop(1, 'transparent')
        ctx.fillStyle = bgG
        ctx.fillRect(0, 0, W, H)

        angle      += neuralActive ? 0.7 : 0.35
        pulsePhase += 0.045
        const pulse = Math.sin(pulsePhase)
        const minDim = Math.min(W, H)

        // Ring definitions
        const rings = [
            { r: minDim * 0.44, speed: 1,    dots: 18, dsize: 2.5, lw: 1.2 },
            { r: minDim * 0.35, speed: -1.6, dots: 14, dsize: 2,   lw: 1.0 },
            { r: minDim * 0.26, speed: 2.2,  dots: 10, dsize: 1.8, lw: 0.9 },
            { r: minDim * 0.18, speed: -3,   dots: 7,  dsize: 1.5, lw: 0.7 },
            { r: minDim * 0.10, speed: 4,    dots: 4,  dsize: 1.2, lw: 0.5 },
        ]

        rings.forEach((ring, idx) => {
            const a     = neuralActive ? 0.55 + 0.25 * pulse : 0.25 + 0.1 * pulse
            const rSize = ring.r + pulse * 2.5

            // Ring glow shadow
            ctx.shadowColor = neuralActive ? '#ff2200' : '#880000'
            ctx.shadowBlur  = neuralActive ? 22 : 10

            // Draw ring arc
            ctx.beginPath()
            ctx.arc(cx, cy, rSize, 0, Math.PI * 2)
            ctx.strokeStyle = neuralActive
                ? `rgba(255, ${20 + idx * 8}, 0, ${a})`
                : `rgba(200, 0, 0, ${a})`
            ctx.lineWidth = ring.lw
            ctx.stroke()

            // Dots on ring
            for (let i = 0; i < ring.dots; i++) {
                const ang = ((angle * ring.speed + i * (360 / ring.dots)) * Math.PI) / 180
                const x   = cx + rSize * Math.cos(ang)
                const y   = cy + rSize * Math.sin(ang)
                const ds  = i % 4 === 0 ? ring.dsize * 1.5 : ring.dsize

                ctx.beginPath()
                ctx.arc(x, y, ds, 0, Math.PI * 2)
                ctx.fillStyle   = neuralActive ? '#ff3300' : '#dd0000'
                ctx.shadowColor = neuralActive ? '#ff0000' : '#880000'
                ctx.shadowBlur  = neuralActive ? 14 : 7
                ctx.fill()
            }

            // Lines between rings
            if (idx < rings.length - 1) {
                for (let i = 0; i < 4; i++) {
                    const a1  = ((angle * ring.speed + i * 90) * Math.PI) / 180
                    const a2  = ((angle * rings[idx+1].speed + i * 90) * Math.PI) / 180
                    const x1  = cx + rSize * Math.cos(a1)
                    const y1  = cy + rSize * Math.sin(a1)
                    const x2  = cx + rings[idx+1].r * Math.cos(a2)
                    const y2  = cy + rings[idx+1].r * Math.sin(a2)
                    ctx.beginPath()
                    ctx.moveTo(x1, y1)
                    ctx.lineTo(x2, y2)
                    ctx.strokeStyle = `rgba(180, 0, 0, ${0.18 + 0.08 * pulse})`
                    ctx.lineWidth   = 0.5
                    ctx.shadowBlur  = 0
                    ctx.stroke()
                }
            }
        })

        // Core glow layers
        const coreR = 30 + pulse * 7
        for (let i = 3; i >= 0; i--) {
            const gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * (1.5 + i * 0.8))
            gr.addColorStop(0, neuralActive
                ? `rgba(255, 60, 0, ${0.9 - i * 0.2})`
                : `rgba(200, 0, 0, ${0.7 - i * 0.15})`)
            gr.addColorStop(0.5, neuralActive
                ? `rgba(255, 0, 0, ${0.4 - i * 0.08})`
                : `rgba(150, 0, 0, ${0.3 - i * 0.06})`)
            gr.addColorStop(1, 'transparent')
            ctx.shadowBlur = 0
            ctx.beginPath()
            ctx.arc(cx, cy, coreR * (1.5 + i * 0.8), 0, Math.PI * 2)
            ctx.fillStyle = gr
            ctx.fill()
        }

        // Core circle border
        ctx.beginPath()
        ctx.arc(cx, cy, coreR, 0, Math.PI * 2)
        ctx.strokeStyle = neuralActive ? '#ff6600' : '#ff2200'
        ctx.lineWidth   = 2
        ctx.shadowColor = '#ff0000'
        ctx.shadowBlur  = neuralActive ? 30 : 15
        ctx.stroke()

        // RS text
        ctx.shadowBlur   = 0
        ctx.fillStyle    = '#ffffff'
        ctx.font         = `bold 15px Courier New`
        ctx.textAlign    = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('RS', cx, cy)

        // Status text
        ctx.font      = '8px Courier New'
        ctx.fillStyle = neuralActive ? '#ff4400' : '#880000'
        ctx.fillText(neuralActive ? 'PROCESSING' : 'STANDBY', cx, cy + coreR + 14)

        ctx.shadowBlur = 0
        requestAnimationFrame(draw)
    }

    draw()
}