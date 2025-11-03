import React, {useContext, useState, useEffect} from 'react';
import AuthContext from '../context/AuthContext';

import ToolbarHeader from './headers/Header';
import MobileHeader from './headers/MobileHeader';

import { PopUpComponent} from '../elements/main_elements';

const popupMessages = {
  mobile: [
    "Привет, если ты читаешь это, значит ты зашел на наш сайт с телефона.",
    "Мы только недавно запустили сайт, и сейчас активно работаем над его адаптацией под мобильные устройства и планшеты. На некоторых устройствах могут временно возникать проблемы с отображением интерфейса.",
    "Спасибо за понимание! Если ты заметил баг — напиши нам, мы обязательно всё поправим 😊",
    "Присоединяйся к нашему Telegram-каналу: https://t.me/studiumchannel"
  ],
  general: [
    "Привет! Мы рады видеть тебя на нашем сайте.",
    "Проект только недавно запустился, и мы продолжаем активно его развивать. Некоторые функции или страницы могут работать нестабильно или быть временно недоступны.",
    "Мы постоянно улучшаем интерфейс, добавляем новые возможности и исправляем баги. Поэтому не удивляйся, если что-то внезапно изменится 😊",
    "Если у тебя есть предложения или ты нашёл ошибку — обязательно дай знать! Спасибо, что с нами 🙌",
    "Следи за новостями в нашем Telegram-канале: https://t.me/studiumchannel"
  ]
};

  
function PopUpMessage({ isMobileOrTablet }) {
    const messages = isMobileOrTablet ? popupMessages.mobile : popupMessages.general;
  
    return (
      <div className="popup_message_wrapper">
        <div className="popup_message_scroll">
          {messages.map((text, idx) => (
            <p className="info_text" key={idx}>
              {text}
            </p>
          ))}
        </div>
      </div>
    );
  }
  

  function ResponsiveHeader() {
    const { isMobileOrTablet, authData } = useContext(AuthContext);

    const [showPopup, setShowPopup] = useState(true);

    useEffect(() => {
        if (authData.authType === 'recovery') {
            setShowPopup(false);
        }
    }, [authData]);
    
    return (
      <>
        {isMobileOrTablet ? <MobileHeader /> : <ToolbarHeader />}
        {showPopup && (
          <PopUpComponent
            isVisible={showPopup}
            id="information_pop_up_element"
            onClose={() => setShowPopup(false)}
            displayed={
              <div style={{ position: 'relative' }}>
                <PopUpMessage isMobileOrTablet={isMobileOrTablet} />
              </div>
            }
          />
        )}
      </>
    );
  }

export default ResponsiveHeader;
