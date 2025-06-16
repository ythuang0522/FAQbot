class ChatBot {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.chatForm = document.getElementById('chat-form');
        this.questionInput = document.getElementById('question');
        this.sendButton = document.getElementById('send-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.charCount = document.getElementById('char-count');
        this.conversationId = null;
        
        this.initEventListeners();
        this.addWelcomeMessage();
    }
    
    initEventListeners() {
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.questionInput.addEventListener('input', (e) => this.updateCharCount(e));
        this.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit(e);
            }
        });
    }
    
    updateCharCount(e) {
        const length = e.target.value.length;
        this.charCount.textContent = `${length}/1000`;
        
        if (length > 900) {
            this.charCount.style.color = 'var(--error-color)';
        } else if (length > 700) {
            this.charCount.style.color = 'var(--warning-color)';
        } else {
            this.charCount.style.color = 'var(--secondary-color)';
        }
    }
    
    addWelcomeMessage() {
        this.addMessage('bot', '嗨! 我是亞洲準譯AI助手，可以回答您關於業務、實驗室和報告產出的問題。您想了解什麼？', 'system');
    }
    
    addMessage(type, content, category = null, processingTime = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        let metaInfo = '';
        if (category && category !== 'system') {
            metaInfo = `<div class="message-meta">Source: ${category.toUpperCase()}`;
            if (processingTime) {
                metaInfo += ` | ${processingTime}s`;
            }
            metaInfo += '</div>';
        }
        
        // Convert Markdown formatting to HTML
        const formattedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold** -> <strong>bold</strong>
            .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *italic* -> <em>italic</em>
            .replace(/\n/g, '<br>');                           // newlines -> <br>

        messageDiv.innerHTML = `${formattedContent}${metaInfo}`;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${message}`;
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    setInputState(disabled) {
        this.questionInput.disabled = disabled;
        this.sendButton.disabled = disabled;
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const question = this.questionInput.value.trim();
        if (!question) return;
        
        // Add user message
        this.addMessage('user', question);
        this.questionInput.value = '';
        this.updateCharCount({target: {value: ''}});
        
        // Show loading state
        this.setInputState(true);
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    conversation_id: this.conversationId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.error || 'Failed to get response');
            }
            
            const data = await response.json();
            
            // Store conversation ID for follow-up questions
            this.conversationId = data.conversation_id;
            
            // Add bot response
            this.addMessage(
                'bot', 
                data.answer, 
                data.category, 
                data.processing_time
            );
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addErrorMessage(error.message || 'Something went wrong. Please try again.');
        } finally {
            this.hideTypingIndicator();
            this.setInputState(false);
            this.questionInput.focus();
        }
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatBot();
}); 