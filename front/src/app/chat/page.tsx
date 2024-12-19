"use client";

import { useState, useRef } from "react";
import { Box, TextField, Button, Typography, IconButton } from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";
import StopIcon from "@mui/icons-material/Stop";

export default function Chat() {
  const [messages, setMessages] = useState<
    { sender: "user" | "api"; text: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        audioChunksRef.current = []; // Reset chunks for the next recording

        // Send the audioBlob to an API
        await sendAudioToAPI(audioBlob);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
      setRecording(false);
    }
  };

  const sendAudioToAPI = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
      const response = await fetch("https://your-api-endpoint.com/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log("API Response:", result);
        setMessages((prev) => [
          ...prev,
          { sender: "api", text: `API Response: ${JSON.stringify(result)}` },
        ]);
      } else {
        console.error("Error sending audio to API:", response.statusText);
      }
    } catch (error) {
      console.error("Error sending audio to API:", error);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: { sender: "user" | "api"; text: string } = {
      sender: "user",
      text: input.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Simulate API response
    const apiMessage: { sender: "user" | "api"; text: string } = {
      sender: "api",
      text: `Response to: "${input}"`,
    };
    setMessages((prev) => [...prev, apiMessage]);
  };

  return (
    <Box
      sx={{
        marginLeft: "80px",
        marginRight: "80px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        height: "100vh",
      }}
    >
      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              justifyContent:
                message.sender === "user" ? "flex-end" : "flex-start",
              marginBottom: "10px",
            }}
          >
            <Typography
              sx={{
                backgroundColor:
                  message.sender === "user" ? "#1e88e5" : "#424242",
                color: "#fff",
                padding: "10px 15px",
                borderRadius: "15px",
                maxWidth: "70%",
              }}
            >
              {message.text}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "40px 0",
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          sx={{
            backgroundColor: "#fff",
            borderRadius: "5px",
          }}
          placeholder="Type your message..."
        />
        {recording ? (
          <IconButton
            onClick={handleStopRecording}
            sx={{
              backgroundColor: "red",
              color: "#fff",
              borderRadius: "50%",
            }}
          >
            <StopIcon />
          </IconButton>
        ) : (
          <IconButton
            onClick={handleStartRecording}
            sx={{
              backgroundColor: "#1e88e5",
              color: "#fff",
              borderRadius: "50%",
            }}
          >
            <MicIcon />
          </IconButton>
        )}
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          sx={{
            borderRadius: "5px",
          }}
        >
          Send
        </Button>
      </Box>
    </Box>
  );
}
