import React, { useState, useRef, useImperativeHandle, forwardRef } from 'react';
import { Box, TextField, IconButton, CircularProgress } from '@mui/material';
import { Send } from '@mui/icons-material';

interface InputFormProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export interface InputFormRef {
  focus: () => void;
}

const InputForm = forwardRef<InputFormRef, InputFormProps>(({ onSendMessage, isLoading }, ref) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current?.focus();
    }
  }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
        display: 'flex',
        gap: 1,
      }}
    >
      <TextField
        inputRef={inputRef}
        fullWidth
        variant="outlined"
        placeholder="Type your message here..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isLoading}
        size="small"
        multiline
        maxRows={3}
        onKeyPress={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
      />
      <IconButton
        type="submit"
        color="primary"
        disabled={!message.trim() || isLoading}
        sx={{ alignSelf: 'flex-end' }}
      >
        {isLoading ? <CircularProgress size={24} /> : <Send />}
      </IconButton>
    </Box>
  );
});

InputForm.displayName = 'InputForm';

export default InputForm;