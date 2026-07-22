document.addEventListener('DOMContentLoaded', () => {
    const chatbotBtn = document.getElementById('chatbot-toggle');
    const sidebarChatbotToggle = document.getElementById('sidebar-chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeBtn = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-msg');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    // Toggle window
    if (chatbotBtn) {
        chatbotBtn.addEventListener('click', () => {
            chatbotWindow.classList.toggle('active');
            if (chatbotWindow.classList.contains('active')) {
                chatInput.focus();
            }
        });
    }

    if (sidebarChatbotToggle) {
        sidebarChatbotToggle.addEventListener('click', (e) => {
            e.preventDefault();
            chatbotWindow.classList.toggle('active');
            if (chatbotWindow.classList.contains('active')) {
                chatInput.focus();
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            chatbotWindow.classList.remove('active');
        });
    }

    // Send message (Mockup)
    const sendMessage = () => {
        const text = chatInput.value.trim();
        if (text === '') return;

        // User message
        appendMessage('user', text);
        chatInput.value = '';

        // Bot response (API Fetch)
        appendMessage('bot', '...', 'loading-msg'); // Loading indicator

        // Extract CSRF token from cookies
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
            appendMessage('bot', 'Error de red.');
        });
    };

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

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
        if (!chatMessages) return;
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
            if (chatbotWindow && !chatbotWindow.classList.contains('active')) {
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
