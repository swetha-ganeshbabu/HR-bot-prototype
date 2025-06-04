import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, Avatar } from '@mui/material';
import { Person, SmartToy } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'auto',
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.map((message) => (
        <Box
          key={message.id}
          sx={{
            display: 'flex',
            justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
            alignItems: 'flex-start',
            gap: 1,
          }}
        >
          {message.sender === 'bot' && (
            <Avatar
              sx={{
                bgcolor: 'primary.main',
                width: 32,
                height: 32,
              }}
            >
              <SmartToy fontSize="small" />
            </Avatar>
          )}
          
          <Paper
            elevation={1}
            sx={{
              p: 2,
              maxWidth: '70%',
              bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
              color: message.sender === 'user' ? 'white' : 'text.primary',
            }}
          >
            {message.sender === 'bot' ? (
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <Typography variant="body2" paragraph sx={{ mb: 0 }}>
                      {children}
                    </Typography>
                  ),
                  ul: ({ children }) => (
                    <Box component="ul" sx={{ pl: 2, my: 0 }}>
                      {children}
                    </Box>
                  ),
                  li: ({ children }) => (
                    <Typography component="li" variant="body2">
                      {children}
                    </Typography>
                  ),
                }}
              >
                {message.text}
              </ReactMarkdown>
            ) : (
              <Typography variant="body2">{message.text}</Typography>
            )}
            
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 0.5,
                opacity: 0.7,
                color: message.sender === 'user' ? 'inherit' : 'text.secondary',
              }}
            >
              {message.timestamp.toLocaleTimeString()}
            </Typography>
          </Paper>
          
          {message.sender === 'user' && (
            <Avatar
              sx={{
                bgcolor: 'secondary.main',
                width: 32,
                height: 32,
              }}
            >
              <Person fontSize="small" />
            </Avatar>
          )}
        </Box>
      ))}
      <div ref={messagesEndRef} />
    </Box>
  );
};

export default MessageList;
export type { Message };