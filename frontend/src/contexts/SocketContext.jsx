import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext.jsx'; 

const SocketContext = createContext(null);

export function SocketProvider({ children, sessionId, currentUserId }) {
    const { isAuthenticated, session } = useAuth();
    const [socket, setSocket] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [status, setStatus] = useState('Initializing...');
    const apiUrl = typeof __API_URL__ !== "undefined" ? __API_URL__ : ""; // use api url env variable defined in vite.config.js

    // Connect/Disconnect based on Auth status
    useEffect(() => {
        let newSocket;

        if (isAuthenticated && session?.access_token) {
            setStatus('Attempting connection...');
            console.log("Attempting socket connection")
            
            // Create the socket instance with authentication token
            newSocket = io(apiUrl, {
                auth: {
                    token: session.access_token,
                },
                transports: ['websocket']
            });

            newSocket.on('connect', () => {
                setIsConnected(true);
                setStatus('Connected');
                console.log('Socket connected successfully.');
            });

            newSocket.on('disconnect', (reason) => {
                setIsConnected(false);
                setStatus(`Disconnected: ${reason}`);
                console.log('Socket disconnected:', reason);
            });
            
            newSocket.on('connect_error', (err) => {
                setStatus(`Connection Error: ${err.message}`);
                console.error('Socket connection error:', err);
            });

            newSocket.on('error', (data) => {
                setStatus(`Error: ${data.message || 'Server Error'}`);
                console.error('Server emitted error:', data);
                newSocket.close();
            });

            setSocket(newSocket);

        } else if (socket) {
            // User signed out or token expired
            socket.close();
            setSocket(null);
            setIsConnected(false);
            setStatus('Disconnected (Not Authenticated)');
        }

        // Cleanup function
        return () => {
            if (newSocket) {
                newSocket.off('connect');
                newSocket.off('disconnect');
                newSocket.off('error');
                newSocket.off('connect_error');
                newSocket.close();
            }
        };
    }, [isAuthenticated, session?.access_token]);

    // Function to subscribe to a specific event
    const subscribe = useCallback((event, handler) => {
        if (socket) {
            socket.on(event, handler);
        }
    }, [socket]);

    // Function to unsubscribe from a specific event
    const unsubscribe = useCallback((event, handler) => {
        if (socket) {
            socket.off(event, handler);
        }
    }, [socket]);

    // Function to emit messages
    const emit = useCallback((event, data) => {
        if (socket && isConnected) {
            socket.emit(event, data);
            return true;
        }
        console.warn('Socket not connected. Cannot emit event:', event);
        return false;
    }, [socket, isConnected]);


    const value = useMemo(() => ({
        socket,
        isConnected,
        status,
        emit,
        subscribe,
        unsubscribe,
    }), [socket, isConnected, status, emit, subscribe, unsubscribe]);

    return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
}

export function useSocket() {
    const context = useContext(SocketContext);
    if (!context) {
        throw new Error('useSocket must be used within a SocketProvider');
    }
    return context;
}