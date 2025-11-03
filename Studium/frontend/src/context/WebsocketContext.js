import axios from 'axios';
import { createContext, useState, useEffect, useRef, useMemo, useContext } from 'react';
import { formatDistanceToNowStrict, parseISO } from 'date-fns';
import { ru } from "date-fns/locale";

import NotificationPerson from '../media/png/notification_person.png'
import NotificationBriefcase from '../media/png/briefcase.png'
import NotificationWarning from '../media/png/conflict.png'
import AuthContext from './AuthContext';

axios.defaults.withCredentials = true;

const WebSocketContext = createContext()

export default WebSocketContext;

export function WebSocketProvider({children}){
    const [notifications, setNotifications] = useState([]);
    const [messages, setMessages] = useState([]);
    const [currentChat, setCurrentChat] = useState(null);
    const [unreadCount, setUnreadCount] = useState(0);
    const wsRef = useRef(null);
    const { registerLogoutCallback, accessToken } = useContext(AuthContext);

    const shortenTime = (time) => {
        return time
            .replace(/\s?секунд(ы|а|)\s?/g, " с")
            .replace(/\s?минут(ы|ы|а|)\s?/g, " м")
            .replace(/\s?час(а|ов|)\s?/g, " ч")
            .replace(/\s?дней?\s?/g, " д")
            .replace(/\s?месяцев?\s?/g, " мес")
            .replace(/\s?лет?\s?/g, " г");
    };

    const formatNotificationTime = (createdAt) => {
        const timeAgo = formatDistanceToNowStrict(parseISO(createdAt), { locale: ru });
        return shortenTime(timeAgo);
    };

    const clearAll = () => {
        setNotifications([]);
        setMessages([]);
        setCurrentChat(null);
        setUnreadCount(0);
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.close();
        }
    };

    useEffect(() => {
        const unregister = registerLogoutCallback?.(clearAll);
        return () => unregister?.(); 
    }, [registerLogoutCallback]);

    useEffect(() => {
        if (!accessToken) {
            if (wsRef.current) {
                wsRef.current.close();
            }
            return;
        }

        if (wsRef.current) {
            wsRef.current.close();
        }

        const socket = new WebSocket(`/ws/connect/?token=${accessToken}`);
        wsRef.current = socket;

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'notification':
                    handleNotification(data.notification);
                    break;
                case 'chat_message':
                    handleChatMessage(data);
                    break;
                case 'chat_history':
                    handleChatHistory(data.messages);
                    break;
                case 'chat_joined':
                    console.log('Успешно присоединились к чату:', data.chat_id);
                    break;
                case 'chat_left':
                    console.log('Покинули чат:', data.chat_id);
                    if (currentChat?.id === data.chat_id) {
                        setCurrentChat(null);
                        setMessages([]);
                    }
                    break;
                default:
                    console.log('Неизвестный тип сообщения:', data);
            }
        };

        socket.onopen = () => {
            console.log('WebSocket соединение установлено');
        };

        socket.onclose = () => {
            console.log('WebSocket соединение закрыто');
        };

        socket.onerror = (error) => {
            console.error('WebSocket ошибка:', error);
        };

        return () => socket.close();
    }, [accessToken]);

    const handleNotification = (notification) => {
        if (!notification) return;
        
        setNotifications((prev) => {
            const next = prev.some(n => n.id === notification.id)
                ? prev.map(n => (n.id === notification.id ? notification : n))
                : [notification, ...prev];
            return next.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        });
    };

    const handleChatMessage = (data) => {
        if (currentChat?.id === data.chat_id) {
            setMessages(prev => [...prev, data.message]);
        }
    };

    const handleChatHistory = (chatMessages) => {
        setMessages(chatMessages || []);
    };

    useEffect(() => {
        setUnreadCount(notifications.filter(n => !n.is_read).length);
    }, [notifications]);

    useEffect(() => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({ action: "update_token", token: accessToken }));
    }, [accessToken]);

    const markAllAsRead = () => {
        if (unreadCount === 0) return;
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({ action: "mark_all_read", token: accessToken }));
        setNotifications((prev) => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
    };

    const markAsRead = (id) => {
        if (unreadCount === 0) return;
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        
        const notification = notifications.find(n => n.id === id);
        const type_name = notification?.type_name;
        
        wsRef.current.send(JSON.stringify({ action: "mark_read", token: accessToken, id, type_name}));

        setNotifications((prev) =>
            prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
        );
    };

    const joinChat = (chatId) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({ 
            action: "join_chat", 
            token: accessToken,
            chat_id: chatId
        }));
        
        setCurrentChat({ id: chatId });
        setMessages([]); // Очищаем предыдущие сообщения
    };

    const leaveChat = (chatId) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        wsRef.current.send(JSON.stringify({ 
            action: "leave_chat", 
            token: accessToken,
            chat_id: chatId
        }));
        
        if (currentChat?.id === chatId) {
            setCurrentChat(null);
            setMessages([]);
        }
    };

    const sendMessage = (messageText) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !currentChat) return;

        wsRef.current.send(JSON.stringify({ 
            action: "send_message", 
            token: accessToken,
            chat_id: currentChat.id,
            message: messageText
        }));
    };

    const loadChatHistory = async (chatId) => {
        try {
            const response = await axios.get(`/api/chat/${chatId}/messages/`, {
                headers: { 
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            setMessages(response.data);
        } catch (error) {
            console.error('Ошибка загрузки истории чата:', error);
        }
    };

    const contextValue = useMemo(() => ({
        notifications,
        unreadCount,
        markAllAsRead,
        markAsRead,
        formatNotificationTime,
        clearNotifications: clearAll,
        
        messages,
        currentChat,
        setCurrentChat,
        joinChat,
        leaveChat,
        sendMessage,
        loadChatHistory
        
    }), [
        notifications,
        unreadCount,
        messages,
        currentChat,
        accessToken
    ]);

    return(
        <WebSocketContext.Provider value={contextValue}>
            {children}
        </WebSocketContext.Provider>
    );
}

export const notificationConfig = {
    routes: {
        user: (id) => `/user/${id}`,
        ready_task: (id) => `/ready/${id}`,
        message: (id) => `/messages/${id}`,
        purchased_task: (id) => `/ready/${id}`,
    },
    iconMap: [
        { keys: ["user_events", "user_activity"], icon: NotificationPerson },
        { keys: ["ready_task", "task_completed"], icon: NotificationBriefcase },
        { keys: ["moderation", "report"], icon: NotificationWarning }
    ],
    getNotificationLink: (type, id, addData) => {
        if (type === "purchased_task" && addData) {
            return notificationConfig.routes.purchased_task?.(addData) || "#";
        }
        return notificationConfig.routes[type]?.(id) || "#";
    }
};