document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-msg');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (!chatMessages) return; // Si no estamos en la página del chat, no ejecutar nada.

    // Leer parámetros IoT de la URL (si venimos del Dashboard de Triaje)
    const urlParams = new URLSearchParams(window.location.search);
    const iotBpm = urlParams.get('iot_bpm');
    const iotSpo2 = urlParams.get('iot_spo2');
    
    if (iotBpm && iotSpo2) {
        chatInput.value = `[ALERTA IoT] Ritmo Cardíaco: ${iotBpm} BPM, SpO2: ${iotSpo2}%. Mis síntomas son: `;
        chatInput.focus();
        
        // Limpiar la URL para que si recarga no vuelva a inyectarlo
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // SAMR-28-US-1.6: Edge AI/offline-first. Guardar localmente los síntomas cuando no hay red y reenviar al reconectar.
    const offlineQueueKey = 'samr-offline-symptoms-queue';

    const getOfflineQueue = () => {
        try {
            const queueJson = localStorage.getItem(offlineQueueKey);
            return queueJson ? JSON.parse(queueJson) : [];
        } catch (err) {
            console.error('Error leyendo cola offline:', err);
            return [];
        }
    };

    const setOfflineQueue = (queue) => {
        localStorage.setItem(offlineQueueKey, JSON.stringify(queue));
    };

    const enqueueOfflineMessage = (message) => {
        const queue = getOfflineQueue();
        queue.push({ message, timestamp: new Date().toISOString() });
        setOfflineQueue(queue);
    };

    const getCookie = (name) => {
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
    };

    const flushOfflineQueue = async () => {
        const queue = getOfflineQueue();
        if (!queue.length) return;

        appendMessage('bot', `Restablecida la conexión. Enviando ${queue.length} síntoma(s) guardado(s) localmente...`, 'system-msg');
        const remaining = [];

        for (const item of queue) {
            try {
                const response = await fetch('/api/chatbot/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ message: item.message })
                });
                const data = await response.json();

                if (data.status === 'success') {
                    appendMessage('bot', `✅ Síntomas previamente guardados enviados correctamente.`, 'system-msg');
                } else {
                    remaining.push(item);
                    console.warn('No se pudo reenviar mensaje offline:', data);
                }
            } catch (error) {
                remaining.push(item);
                console.warn('Error reenviando cola offline:', error);
            }
        }

        setOfflineQueue(remaining);
        if (remaining.length > 0) {
            appendMessage('bot', 'Algunos síntomas siguen pendientes. Se reenviarán cuando la conexión sea estable.', 'system-msg');
        } else {
            appendMessage('bot', 'Todos los síntomas locales fueron enviados al servidor.', 'system-msg');
        }
    };

    window.addEventListener('online', () => {
        appendMessage('bot', 'Conexión restaurada. Intentando enviar los síntomas guardados...', 'system-msg');
        flushOfflineQueue();
    });

    window.addEventListener('offline', () => {
        appendMessage('bot', 'Estás sin conexión. Los síntomas se guardarán localmente y se enviarán cuando se recupere internet.', 'system-msg');
    });

    // Send message (Mockup)
    const sendMessage = () => {
        const text = chatInput.value.trim();
        if (text === '') return;

        // If the user is offline, queue the symptom report locally and avoid calling the API.
        if (!navigator.onLine) {
            appendMessage('user', text);
            enqueueOfflineMessage(text);
            chatInput.value = '';
            appendMessage('bot', 'Sin conexión. Tus síntomas se han guardado localmente y se enviarán cuando recuperes internet.', 'system-msg');
            return;
        }

        // User message
        appendMessage('user', text);
        chatInput.value = '';

        // SAMR-32-US-2.4: En la arquitectura, este cliente debe empaquetar la telemetría inmediata de los sensores IoT
        // junto con los síntomas antes de invocar al motor LLM / endpoint de triaje. Es una responsabilidad de Edge
        // AI conectar datos locales de IoT con el mensaje clínico para mejorar la inferencia y el contexto.
        // Bot response (API Fetch)
        appendMessage('bot', '...', 'loading-msg'); // Loading indicator

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
            // Remove loading msg
            const loadingMsg = document.querySelector('.loading-msg');
            if (loadingMsg) loadingMsg.remove();

            if (data.status === 'success') {
                appendMessage('bot', data.reply);
            } else {
                appendMessage('bot', 'Error de conexión con la red neuronal.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
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

    // Web Speech API para Voicebot
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = function() {
                micBtn.classList.remove('text-light');
                micBtn.classList.add('text-danger');
                chatInput.placeholder = "Escuchando...";
            };

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                chatInput.value = speechResult;
                sendMessage();
            };

            recognition.onspeechend = function() {
                recognition.stop();
                micBtn.classList.remove('text-danger');
                micBtn.classList.add('text-light');
                chatInput.placeholder = "Escribe tu mensaje...";
            };

            recognition.onerror = function(event) {
                console.error("Speech recognition error", event.error);
                micBtn.classList.remove('text-danger');
                micBtn.classList.add('text-light');
                chatInput.placeholder = "Escribe tu mensaje...";
                appendMessage('bot', 'No pude escucharte bien. ¿Puedes intentarlo de nuevo?');
            };

            micBtn.addEventListener('click', () => {
                recognition.start();
            });
        } else {
            micBtn.style.display = 'none';
            console.log("Speech Recognition not supported in this browser.");
        }
    }

    function appendMessage(sender, text, extraClass = null) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender, 'mb-4');
        if (extraClass) {
            msgDiv.classList.add(extraClass);
        }

        const iconClass = sender === 'user' ? 'bi-person-fill' : 'bi-robot';
        
        msgDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="avatar-circle text-white me-2 mt-1 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 32px; height: 32px; border-radius: 50%; ${sender === 'bot' ? 'background-color: var(--accent-color);' : ''}">
                    <i class="bi ${iconClass} fs-6"></i>
                </div>
                <div class="p-3 rounded-4 bg-dark bg-opacity-75 text-white content-text" style="border-top-left-radius: 0 !important; max-width: 80%; white-space: pre-wrap;">
                </div>
            </div>
        `;
        
        // Asignar el texto de forma segura para evitar XSS
        msgDiv.querySelector('.content-text').textContent = text;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Configurar WebSocket del Paciente para notificaciones en tiempo real
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = protocol + window.location.host + '/ws/paciente/';
    const socket = new WebSocket(wsUrl);

    socket.onopen = function(e) {
        console.log("[WebSocket] Conectado al canal del paciente");
    };

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'medico_conectado') {
            appendMessage('bot', '✅ ' + data.message);
            // Abrir el chat si está cerrado
            if (!chatbotWindow.classList.contains('active')) {
                chatbotWindow.classList.add('active');
            }
        } else if (data.type === 'emergencia_medica') {
            // Mostrar modal de emergencia visualmente llamativo
            appendMessage('bot', '🚨 ' + data.message, 'bg-danger');
            alert("🚨 ALERTA CRÍTICA: " + data.message);
            document.body.style.animation = "pulse 1s infinite alternate";
            document.body.style.backgroundColor = "rgba(255,0,0,0.2)";
            setTimeout(() => {
                document.body.style.animation = "";
                document.body.style.backgroundColor = "";
            }, 10000);
        }
    };

    socket.onclose = function(e) {
        console.log("[WebSocket] Desconectado del canal del paciente");
    };
});
