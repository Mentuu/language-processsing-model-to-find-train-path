// src/app/page.tsx
import Link from "next/link";
import { Box, Button, Typography } from "@mui/material";

export default function Home() {
  return (
    <Box
      sx={{
        height: "100vh",
        flexDirection: "column",
        backgroundColor: "#000",
        color: "#fff",
      }}
    >
      <Typography variant="h5" color="primary">
        CityTrain
      </Typography>

      <Box
        sx={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: "#000",
          color: "#fff",
        }}
      >
        <Typography variant="h3" gutterBottom>
          WELCOME !!!
        </Typography>

        <Link href="/chat">
          <Button variant="contained" color="primary">
            Accéder au Chat
          </Button>
        </Link>
      </Box>
    </Box>
  );
}
