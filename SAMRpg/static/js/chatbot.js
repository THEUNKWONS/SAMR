function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-msg');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const voiceToggleBtn = document.getElementById('btn-toggle-voice');
    const voiceIcon = document.getElementById('voice-icon');

    if (!chatMessages) return;

    // TTS Config
    let voiceEnabled = true;
    let synth = window.speechSynthesis;
    
    if (voiceToggleBtn) {
        voiceToggleBtn.addEventListener('click', () => {
            voiceEnabled = !voiceEnabled;
            if (voiceEnabled) {
                voiceIcon.classList.replace('bi-volume-mute-fill', 'bi-volume-up-fill');
                voiceToggleBtn.classList.add('btn-outline-light');
                voiceToggleBtn.classList.remove('btn-secondary');
            } else {
                voiceIcon.classList.replace('bi-volume-up-fill', 'bi-volume-mute-fill');
                voiceToggleBtn.classList.remove('btn-outline-light');
                voiceToggleBtn.classList.add('btn-secondary');
                synth.cancel(); // Stop speaking
            }
        });
    }

    function speakText(text) {
        if (!voiceEnabled || !synth) return;
        
        // Clean text from markdown or emojis before speaking
        let cleanText = text.replace(/[\*\_\[\]\(\)\#\-\>]/g, '').trim();
        cleanText = cleanText.replace(/[🚨🟢🟡✅]/g, '');
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'es-ES';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Find a good Spanish voice
        const voices = synth.getVoices();
        const esVoice = voices.find(v => v.lang.startsWith('es-') && v.name.includes('Google')) || voices.find(v => v.lang.startsWith('es-'));
        if (esVoice) utterance.voice = esVoice;
        
        const avatar = document.querySelector('.bot-avatar');
        
        utterance.onstart = () => {
            if (avatar) avatar.classList.add('bot-speaking');
        };
        
        utterance.onend = () => {
            if (avatar) avatar.classList.remove('bot-speaking');
        };
        
        synth.speak(utterance);
    }

    // Load initial voices (workaround for Chrome bug)
    if (synth) synth.onvoiceschanged = () => synth.getVoices();

    const urlParams = new URLSearchParams(window.location.search);
    const iotBpm = urlParams.get('iot_bpm');
    const iotSpo2 = urlParams.get('iot_spo2');
    
    if (iotBpm && iotSpo2) {
        chatInput.value = `[ALERTA IoT] Ritmo Cardíaco: ${iotBpm} BPM, SpO2: ${iotSpo2}%. Mis síntomas son: `;
        chatInput.focus();
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    const offlineQueueKey = 'samr-offline-symptoms-queue';

    const getOfflineQueue = () => {
        const q = localStorage.getItem(offlineQueueKey);
        return q ? JSON.parse(q) : [];
    };

    const setOfflineQueue = (q) => {
        localStorage.setItem(offlineQueueKey, JSON.stringify(q));
    };

    const enqueueOfflineMessage = (text) => {
        const q = getOfflineQueue();
        q.push({ text: text, timestamp: new Date().toISOString() });
        setOfflineQueue(q);
    };

    const flushOfflineQueue = async () => {
        const q = getOfflineQueue();
        if (q.length === 0) return;

        let remaining = [];
        for (const item of q) {
            try {
                const response = await fetch('/api/chatbot/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ message: item.text + " [ENVIADO OFFLINE]" })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    appendMessage('bot', `Respuesta a tu síntoma guardado: ${data.reply}`);
                } else {
                    remaining.push(item);
                }
            } catch (error) {
                remaining.push(item);
            }
        }
        setOfflineQueue(remaining);
    };

    window.addEventListener('online', () => {
        appendMessage('bot', 'Conexión restaurada. Intentando enviar los síntomas guardados...', 'system-msg');
        flushOfflineQueue();
    });

    window.addEventListener('offline', () => {
        appendMessage('bot', 'Estás sin conexión. Los síntomas se guardarán localmente y se enviarán cuando se recupere internet.', 'system-msg');
    });

    const sendMessage = () => {
        const text = chatInput.value.trim();
        if (text === '') return;

        if (!navigator.onLine) {
            appendMessage('user', text);
            enqueueOfflineMessage(text);
            chatInput.value = '';
            appendMessage('bot', 'Sin conexión. Tus síntomas se han guardado localmente y se enviarán cuando recuperes internet.', 'system-msg');
            return;
        }

        appendMessage('user', text);
        chatInput.value = '';

        appendMessage('bot', '...', 'loading-msg'); 

        fetch('/api/chatbot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: text })
        })
        .then(response => response.json())
        .then(data => {
            const loadingMsg = document.querySelector('.loading-msg');
            if (loadingMsg) loadingMsg.remove();

            if (data.status === 'success') {
                appendMessage('bot', data.reply);
            } else {
                appendMessage('bot', 'Error de conexión con la red neuronal.');
            }
        })
        .catch(error => {
            const loadingMsg = document.querySelector('.loading-msg');
            if (loadingMsg) loadingMsg.remove();
            enqueueOfflineMessage(text);
            appendMessage('bot', 'No se pudo enviar. Tus síntomas se han guardado localmente y se enviarán cuando haya conexión.', 'system-msg');
        });
    };

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            const micIcon = document.getElementById('mic-icon');

            recognition.onstart = function() {
                micIcon.classList.replace('text-light', 'text-danger');
                micBtn.style.animation = 'pulseAvatar 1s infinite';
                chatInput.placeholder = "Escuchando...";
            };

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                chatInput.value = speechResult;
                sendMessage();
            };

            recognition.onspeechend = function() {
                recognition.stop();
                micIcon.classList.replace('text-danger', 'text-light');
                micBtn.style.animation = 'none';
                chatInput.placeholder = "Escribe tu mensaje médico aquí...";
            };

            recognition.onerror = function(event) {
                micIcon.classList.replace('text-danger', 'text-light');
                micBtn.style.animation = 'none';
                chatInput.placeholder = "Escribe tu mensaje médico aquí...";
                appendMessage('bot', 'No pude escucharte bien. ¿Puedes intentarlo de nuevo?');
            };

            micBtn.addEventListener('click', () => {
                recognition.start();
            });
        } else {
            micBtn.style.display = 'none';
        }
    }

    function appendMessage(sender, text, extraClass = null) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        if (extraClass) msgDiv.classList.add(extraClass);

        const isUser = sender === 'user';
        const bubbleClass = isUser ? 'user-bubble' : 'bot-bubble';
        const iconClass = isUser ? 'bi-person-fill' : 'bi-robot';
        const avatarBg = isUser ? 'background: #334155;' : 'background: linear-gradient(135deg, var(--accent-color) 0%, #047857 100%);';

        msgDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="avatar-circle text-white shadow-sm flex-shrink-0 d-flex align-items-center justify-content-center ${isUser ? 'ms-3' : 'me-3 mt-1'}" style="width: 38px; height: 38px; border-radius: 50%; ${avatarBg}">
                    <i class="bi ${iconClass} fs-6"></i>
                </div>
                <div class="p-3 shadow-sm message-bubble ${bubbleClass} text-white content-text" style="white-space: pre-wrap;">
                </div>
            </div>
        `;
        
        msgDiv.querySelector('.content-text').textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (sender === 'bot' && !extraClass) {
            speakText(text);
        }
    }

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = protocol + window.location.host + '/ws/paciente/';
    const socket = new WebSocket(wsUrl);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'medico_conectado') {
            appendMessage('bot', '✅ ' + data.message);
        } else if (data.type === 'emergencia_medica') {
            appendMessage('bot', '🚨 ' + data.message, 'bg-danger');
            alert("🚨 ALERTA CRÍTICA: " + data.message);
        }
    };
});
