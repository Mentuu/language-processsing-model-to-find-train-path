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
import TrainIcon from "@mui/icons-material/Train";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

export default function Chat() {
  const [messages, setMessages] = useState<
    {
      sender: "user" | "api";
      itinéraire?: string;
      audioUrl?: string;
      arrayTrain: string[];
      duree?: string;
      next_dep_time?: string;
      error?: boolean;
    }[]
  >([
    {
      sender: "api",
      itinéraire:
        "Bienvenue sur CityTrain ! Je suis là pour vous aider à trouver votre itinéraire en train.",
      arrayTrain: [],
    },
  ]);
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

        setMessages((prev) => [
          ...prev,
          { sender: "user", audioUrl, arrayTrain: [] },
        ]);

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

          if (data.error) {
            setMessages((prev) => [
              ...prev,
              {
                sender: "api",
                itinéraire: data.error,
                arrayTrain: [],
                error: true,
              },
            ]);

            setLoading(false); // End loading
            return;
          }

          if (data.itinéraire) {
            // Séparer les villes pour un affichage plus propre
            const villes = data.itineraire.split(" -> ");

            setMessages((prev) => [
              ...prev,
              {
                sender: "api",
                itinéraire: data.itinéraire,
                arrayTrain: villes,
                duree: data.duree,
                next_dep_time: data.next_dep_time,
              },
            ]);
          }
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

  const handleSend = async () => {
    if (loading || !input.trim()) return; // Prevent actions while loading or empty input

    setMessages((prev) => [
      ...prev,
      { sender: "user", itinéraire: input.trim(), arrayTrain: [] },
    ]);

    setInput("");
    setLoading(true); // Start loading

    try {
      const result = await fetch("http://127.0.0.1:5000/trips", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input.trim() }),
      });

      if (!result.ok) {
        throw new Error("Failed to send message");
      }

      const data = await result.json();
      console.log("API response:", data);

      if (data.error) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "api",
            itinéraire: data.error,
            arrayTrain: [],
            error: true,
          },
        ]);

        setLoading(false); // End loading
        return;
      }

      if (data && data.itineraire) {
        // Séparer les villes pour un affichage plus propre
        const villes = data.itineraire.split(" -> ");

        setMessages((prev) => [
          ...prev,
          {
            sender: "api",
            itinéraire: data.itinéraire,
            arrayTrain: villes,
            duree: data.duree,
            next_dep_time: data.next_dep_time,
          },
        ]);
      }

      setLoading(false); // Start loading
    } catch (error) {
      console.error("Error sending message:", error);

      setLoading(false);
    }
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
            {/* Si un audio est présent */}
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
            ) : message.sender === "api" && message.arrayTrain?.length > 0 ? (
              <Box
                sx={{
                  backgroundColor: "#f5f5f5",
                  color: "#333",
                  padding: "15px",
                  borderRadius: "10px",
                  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                  textAlign: "left",
                  fontSize: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: "10px" }}
                >
                  <TrainIcon sx={{ color: "#1e88e5", fontSize: "24px" }} />
                  <Typography component="span">
                    <strong>Départ :</strong>{" "}
                    {message.arrayTrain[0] || "Inconnu"}
                  </Typography>
                </Box>

                {message.arrayTrain.length > 2 && (
                  <Box
                    sx={{ display: "flex", alignItems: "center", gap: "10px" }}
                  >
                    <ArrowForwardIcon
                      sx={{ color: "#757575", fontSize: "18px" }}
                    />
                    <Typography component="span">
                      {message.arrayTrain
                        .slice(1, message.arrayTrain.length - 1)
                        .join(" → ") || "Aucune escale"}
                    </Typography>
                  </Box>
                )}

                <Box
                  sx={{ display: "flex", alignItems: "center", gap: "10px" }}
                >
                  <TrainIcon sx={{ color: "#d32f2f", fontSize: "24px" }} />
                  <Typography component="span">
                    <strong>Arrivée :</strong>{" "}
                    {message.arrayTrain[message.arrayTrain.length - 1] ||
                      "Inconnu"}
                  </Typography>
                </Box>

                {/* Durée et prochain départ */}
                <Box sx={{ marginTop: "10px" }}>
                  <strong>Durée :</strong> {message.duree || "Non spécifiée"}
                </Box>
                <Box>
                  <strong>Prochain départ :</strong>{" "}
                  {message.next_dep_time || "Non spécifié"}
                </Box>
              </Box>
            ) : (
              /* Message par défaut */
              <Typography
                sx={{
                  backgroundColor:
                    message.sender === "user"
                      ? "#1e88e5"
                      : message.error
                      ? "red"
                      : "#424242",
                  color: "#fff",
                  padding: "10px 15px",
                  borderRadius: "15px",
                  maxWidth: "70%",
                }}
              >
                {message.itinéraire || "Message vide"}
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
