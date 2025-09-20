// contexts/MessageContext.jsx
import React, { createContext, useContext, useState } from 'react';
import { Snackbar, Alert } from '@mui/material';

const MessageContext = createContext(null);

export const MessageProvider = ({ children }) => {
    const [messages, setMessages] = useState([]);
    const [open, setOpen] = useState(false);
    const [currentMessage, setCurrentMessage] = useState(null);

    const formatErrorMessage = (message) => {
        if (message instanceof Error) {
            return message.message;
        }
        try {
            const parsed = JSON.parse(message);
            return typeof parsed === 'object'
                ? JSON.stringify(parsed, null, 2)
                : message;
        } catch {
            return message;
        }
    };

    const addMessage = (message, severity = 'info') => {
        const formattedMessage = formatErrorMessage(message);
        const newMessage = {
            id: Date.now(),
            text: formattedMessage,
            severity,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, newMessage]);
        setCurrentMessage(newMessage);
        setOpen(true);
    };

    const handleClose = () => setOpen(false);

    return (
        <MessageContext.Provider value={{ messages, addMessage }}>
            {children}
            <Snackbar
                open={open}
                autoHideDuration={6000}
                onClose={handleClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
            >
                <Alert
                    onClose={handleClose}
                    severity={currentMessage?.severity}
                >
                    {currentMessage?.text}
                </Alert>
            </Snackbar>
        </MessageContext.Provider>
    );
};

// hooks/useMessage.js
export const useMessage = () => {
    const context = useContext(MessageContext);
    if (!context)
        throw new Error('useMessage must be used within MessageProvider');
    return {
        showSuccess: (msg) => context.addMessage(msg, 'success'),
        showError: (msg) => context.addMessage(msg, 'error'),
        showInfo: (msg) => context.addMessage(msg, 'info'),
        showWarning: (msg) => context.addMessage(msg, 'warning'),
        messages: context.messages,
    };
};
