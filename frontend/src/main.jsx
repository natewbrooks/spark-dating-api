// src/main.jsx
import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import { AuthProvider } from "@contexts/AuthContext.jsx";
import { SocketProvider } from './contexts/SocketContext.jsx'

const container = document.getElementById("root");

createRoot(container).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider> {/* Used for the AuthContext */}
        <SocketProvider>  {/* Used for the SocketContext */}
          <App /> 
        </SocketProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
