document.addEventListener('DOMContentLoaded', () => {
    const chatbotBtn = document.getElementById('chatbot-toggle');
    const sidebarChatbotToggle = document.getElementById('sidebar-chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeBtn = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-msg');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    // SAMR-28-US-1.6: Edge AI / offline-first. Guardar localmente los síntomas cuando no hay red y reenviar al reconectar.
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

    // Toggle window
    chatbotBtn.addEventListener('click', () => {
        chatbotWindow.classList.toggle('active');
        if (chatbotWindow.classList.contains('active')) {
            chatInput.focus();
        }
    });

    if (sidebarChatbotToggle) {
        sidebarChatbotToggle.addEventListener('click', (e) => {
            e.preventDefault();
            chatbotWindow.classList.toggle('active');
            if (chatbotWindow.classList.contains('active')) {
                chatInput.focus();
            }
        });
    }

    closeBtn.addEventListener('click', () => {
        chatbotWindow.classList.remove('active');
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
                micBtn.style.color = 'red';
                chatInput.placeholder = "Escuchando...";
            };

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                chatInput.value = speechResult;
                sendMessage();
            };

            recognition.onspeechend = function() {
                recognition.stop();
                micBtn.style.color = '';
                chatInput.placeholder = "Escribe tu mensaje...";
            };

            recognition.onerror = function(event) {
                console.error("Speech recognition error", event.error);
                micBtn.style.color = '';
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
        msgDiv.classList.add('message', sender);
        if (extraClass) {
            msgDiv.classList.add(extraClass);
        }
        msgDiv.style.whiteSpace = 'pre-wrap';
        msgDiv.textContent = text;
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
        }
    };

    socket.onclose = function(e) {
        console.log("[WebSocket] Desconectado del canal del paciente");
    };
});
