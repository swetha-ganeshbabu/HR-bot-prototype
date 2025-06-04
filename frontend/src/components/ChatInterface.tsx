import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, AppBar, Toolbar, IconButton } from '@mui/material';
import { Logout, History } from '@mui/icons-material';
import MessageList, { Message } from './MessageList';
import InputForm, { InputFormRef } from './InputForm';
import api from '../services/api';

interface ChatInterfaceProps {
  onLogout: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onLogout }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const inputFormRef = useRef<InputFormRef>(null);

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        id: 'welcome',
        text: 'Hello! I\'m your HR assistant. How can I help you today? You can ask me about benefits, PTO policies, remote work, or any other HR-related questions.',
        sender: 'bot',
        timestamp: new Date(),
      },
    ]);
    
    // Focus the input after component mounts
    setTimeout(() => {
      inputFormRef.current?.focus();
    }, 100);
  }, []);

  const handleSendMessage = async (messageText: string) => {
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsLoading(true);
    try {
      const response = await api.sendMessage(messageText);
      
      // Add bot response
      const botMessage: Message = {
        id: `bot-${response.message_id || Date.now()}`,
        text: response.response,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: 'I\'m sorry, I encountered an error processing your message. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      // Focus the input after sending message
      setTimeout(() => {
        inputFormRef.current?.focus();
      }, 100);
    }
  };

  const loadHistory = async () => {
    try {
      const history = await api.getConversationHistory(20);
      const historicalMessages: Message[] = [];
      
      history.reverse().forEach((conv) => {
        historicalMessages.push({
          id: `hist-user-${conv.id}`,
          text: conv.message,
          sender: 'user',
          timestamp: new Date(conv.timestamp),
        });
        historicalMessages.push({
          id: `hist-bot-${conv.id}`,
          text: conv.response,
          sender: 'bot',
          timestamp: new Date(conv.timestamp),
        });
      });
      
      setMessages(historicalMessages);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            HR Assistant
          </Typography>
          <IconButton color="inherit" onClick={loadHistory} title="Load History">
            <History />
          </IconButton>
          <IconButton color="inherit" onClick={onLogout} title="Logout">
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          m: 2,
          border: 1,
          borderColor: 'divider',
        }}
      >
        <MessageList messages={messages} />
        <InputForm ref={inputFormRef} onSendMessage={handleSendMessage} isLoading={isLoading} />
      </Paper>
    </Box>
  );
};

export default ChatInterface;