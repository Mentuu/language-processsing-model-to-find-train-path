"use client";

import { useState, useRef } from "react";
import {
  Box,
  TextField,
  Typography,
  IconButton,
  CircularProgress,
} from "@mui/material";
import MicIcon from "@mui/icons-material/Mic";
import StopIcon from "@mui/icons-material/Stop";
import SendIcon from "@mui/icons-material/Send";
import AudiotrackIcon from "@mui/icons-material/Audiotrack";

export default function Chat() {
  const [messages, setMessages] = useState<
    { sender: "user" | "api"; text?: string; audioUrl?: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false); // State for loading
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleStartRecording = async () => {
    if (loading) return; // Prevent actions while loading
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/mp3",
        });
        audioChunksRef.current = []; // Reset chunks for the next recording

        const audioUrl = URL.createObjectURL(audioBlob);

        setMessages((prev) => [...prev, { sender: "user", audioUrl }]);

        // Prepare FormData
        const formData = new FormData();
        formData.append("audio_file", audioBlob, "recording.mp3");

        try {
          setLoading(true); // Start loading
          const response = await fetch("http://127.0.0.1:5000/trips", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            throw new Error("Failed to send audio");
          }

          const data = await response.json();

          console.log("API response:", data);

          setMessages((prev) => [...prev, { sender: "api", text: data.text }]);
        } catch (error) {
          console.error("Error sending audio:", error);
        } finally {
          setLoading(false); // End loading
        }
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const handleStopRecording = () => {
    if (loading) return; // Prevent actions while loading
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
      setRecording(false);
    }
  };

  const handleSend = () => {
    if (loading || !input.trim()) return; // Prevent actions while loading or empty input

    setMessages((prev) => [...prev, { sender: "user", text: input.trim() }]);
    setInput("");

    setLoading(true); // Start loading

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "api", text: `Response to: "${input}"` },
      ]);
      setLoading(false); // End loading
    }, 2000); // Simulate API delay
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
          padding: "20px",
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: message.sender === "user" ? "flex-end" : "flex-start",
              marginBottom: "20px",
            }}
          >
            {message.audioUrl ? (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  backgroundColor: "#f0f0f0",
                  padding: "10px",
                  borderRadius: "15px",
                  boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
                }}
              >
                <AudiotrackIcon color="primary" />
                <audio
                  controls
                  src={message.audioUrl}
                  style={{ width: "200px" }}
                  onError={() => console.error("Audio playback error")}
                />
              </Box>
            ) : (
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
            )}
          </Box>
        ))}

        {loading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              marginTop: "20px",
            }}
          >
            <CircularProgress />
          </Box>
        )}
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "20px 0",
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading} // Disable during loading
          sx={{
            backgroundColor: "#fff",
            borderRadius: "5px",
            color: "#000",
          }}
          color="primary"
          placeholder="Type your message..."
        />
        {recording ? (
          <IconButton
            onClick={handleStopRecording}
            disabled={loading} // Disable during loading
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
            disabled={loading} // Disable during loading
            sx={{
              color: "#fff",
              borderRadius: "50%",
            }}
          >
            <MicIcon />
          </IconButton>
        )}

        <IconButton
          onClick={handleSend}
          disabled={loading} // Disable during loading
          color="primary"
          sx={{
            borderRadius: "50%",
          }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
