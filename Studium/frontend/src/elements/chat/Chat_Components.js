import React, { useState, useRef, useEffect, useContext, use } from 'react';
import axios from 'axios';
import WebSocketContext from '../../context/WebsocketContext.js';
import AuthContext from '../../context/AuthContext.js';
import { PopUpComponent } from '../main_elements.js';

import { ReactComponent as ChatIcon } from '../../media/svg/chat.svg';

function ChatController() {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);


    return (
        <div className="chat_icon" ref={menuRef}>
            <div className="user_menu_link" id="user_menu_item" onClick={() => setIsOpen(!isOpen)}>
                <ChatIcon id="bell_svg" style={{ fill: isOpen && "#55ced6" }} />
            </div>

            {isOpen && (
                <PopUpComponent isVisible={isOpen} displayed={<ChatPopUp/>} onClose={() => {setIsOpen(false)}}/>
            )}
        </div>
    );
}

function ChatPopUp(){
    const { accessToken } = useContext(AuthContext);
    const { joinChat, leaveChat } = useContext(WebSocketContext);

    const [chats, setChats] = useState([]);
    const [isError, setIsError] = useState(false);
    const [currentChat, setCurrentChat] = useState(null);

    useEffect(() => {
        const getChats = async () => {
            try {
                const { data } = await axios.get('/api/chat/all/', {
                    headers: { 
                        'Authorization': `Bearer ${accessToken}` 
                    }
                });   
                setChats(data);
            } catch (error) {      
                setIsError(true);
                console.error('Ошибка загрузки чатов:', error);
            }
        };

        getChats();
    }, [accessToken]);

    useEffect(() => {
        return () => {
            if (currentChat) {
                leaveChat(currentChat.id);
            }
        };
    }, [currentChat, leaveChat]);

    const handleChatSelect = (chat) => {
        if (currentChat?.id === chat.id) return;

        if (currentChat) {
            leaveChat(currentChat.id);
        }

        joinChat(chat.id);
        setCurrentChat(chat);
    };

    return(
        <div>
            {!isError ? (
                <div>
                    <ChatList 
                        chats={chats} 
                        chatSelect={handleChatSelect}
                        currentChat={currentChat}
                    />
                    {currentChat ? (
                        <ChatMessageElement />
                    ) : (
                        <p>Выберите чат кому хотите написать</p>
                    )}
                </div>
            ) : (
                <div>Ошибка загрузки чатов</div>
            )}
        </div>
    );
}

function ChatList({ chats, chatSelect, currentChat }){
    return(
        <div className='column_container' id='chat_list'>
            {chats.length > 0 ? (
                chats.map((data) => (
                    <ChatItem
                        key={data.id}
                        data={data}
                        onClick={() => chatSelect(data)}
                        isActive={currentChat?.id === data.id}
                    />
                ))
            ) : (
                <li className="notification_empty">У вас нет чатов</li>
            )}
        </div>
    );
}

function ChatItem({ data, onClick, isActive }) {
    return (
        <li className={isActive ? 'chat_item active' : 'chat_item'}>
            <div className="chat_link" onClick={onClick} style={{cursor: 'pointer'}}>
                {data.icon && <img className="chat_icon" src={data.icon} alt="icon" />}
                <div className="chat_information">
                    <span className="chat_interlocutor">
                        {data.name || `Пользователь № ${data.id || '?'}`}
                    </span>
                </div>
            </div>
        </li>
    );
}

function ChatMessageElement({onClick, onChange}){
    const {messages} = useContext(WebSocketContext)
    return(
        <div>
            <div className='column_container'>
                { messages.length > 0 ? (
                    messages.map((data)=>(
                        <MessageItem data={data}/>
                    ))
                ):(
                    <li className="notification_empty">В этом чате нет сообщений</li>
                )}
            </div>
            <div className='row_container' id='message_input_wrapper'>
                <input className='section_input' onChange={onChange}/>
                <button className='send_message_button' onClick={onClick}/>
            </div>
        </div>
    );
}

function MessageItem(props){
    const {user} = useContext(AuthContext)
    const isOwnMessage = user?.id === props.sender?.id;
    
    return(
        <div className={`column_container ${isOwnMessage ? 'message_own' : 'message_other'}`}>
            <div className='message_header'>
                {props.sender.name}
            </div>
            <div className='message_text'>
                {props.text}
            </div>
        </div>
    );
}

export default ChatController;