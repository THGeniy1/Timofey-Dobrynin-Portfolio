import React, {useEffect, useState, useContext} from 'react';
import axios from 'axios';
import {createPortal} from 'react-dom'
import { Link } from 'react-router-dom';

import Accept_Icon from '../../media/png/Accept_Icon.png'

import AuthContext from '../../context/AuthContext';
import { PopUpComponent, Error_POP_Element } from '../../elements/main_elements';


function Need_Login(props) {
    
    useEffect(() => {
        document.body.style.overflow = props.isVisible ? 'hidden' : 'unset';
        
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [props.isVisible]);
    
    return (
        <>
            {createPortal(
                <div className='pop_up_element_shadow' onClick={props.onClose}>
                    <div className='pop_up_element' id='short_pop_up_element' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='status_pop_up_container'>
                                <span className="main_text"><br/>Авторизуйтесь, чтобы оформить покупку и получить доступ к материалам.</span>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}


function Payment_PopUp(props) {
    
    useEffect(() => {
        document.body.style.overflow = props.isVisible ? 'hidden' : 'unset';
        
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [props.isVisible]);
    
    return (
        <>
            {createPortal(
                <div className='pop_up_element_shadow' onClick={props.onClose}>
                    <div className='pop_up_element' id='short_pop_up_element' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='status_pop_up_container'>
                                <img className='Error_Pop_Icon' src={Accept_Icon}/>
                                <span className="main_text">
                                    Покупка успешно совершена!
                                </span>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function Choose_Payment_Method_Controller(props) {
    const {accessToken} = useContext(AuthContext);
    const [showLoginPopup, setShowLoginPopup] = useState(false);
    const [showSuccessPopup, setShowSuccessPopup] = useState(false);
    const [showError, setShowError] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    const handlePaymentClick = () => {
        if (!accessToken) {
            setShowLoginPopup(true);
            return;
        }
        payment_request();
    };

    const handleSuccessPopupClose = () => {
        setShowSuccessPopup(false);
        window.location.reload();
    };

    const payment_request = async () => {
        try {
            await axios.post('/api/payments/buy_ready_task/', {task_id: props.taskId,
                currency: 'RUB'}, {headers: {'Authorization': `Bearer ${accessToken}`}});

            setShowSuccessPopup(true)

        } catch (error) {
            const message = error.response?.data?.message || error.message || 'Ошибка при оплате';
            setErrorMessage(message);
            setShowError(true);
        }
    };

    return (
        <>
            <button className='right_button' onClick={handlePaymentClick}>
                Оплатить
            </button>
            {showSuccessPopup && (
                <Payment_PopUp 
                isVisible={showSuccessPopup} 
                onClose={() => handleSuccessPopupClose()} />
            )}
            {showLoginPopup && (
                <Need_Login 
                    isVisible={showLoginPopup} 
                    onClose={() => setShowLoginPopup(false)} 
                />
            )}
            {showError && (
                <PopUpComponent
                    isVisible={showError}
                    displayed={<Error_POP_Element message={errorMessage} />}
                    onClose={() => setShowError(false)}
                />
            )}
        </>
    );
}

export default Choose_Payment_Method_Controller;