import axios from 'axios';
import React, { useContext, useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Navigation_Item, Error_POP_Element, PopUpComponent, Loading_POP_Element, Select_Navigate } from '../../elements/main_elements';

import { ReactComponent as WalletIcon } from '../../media/svg/wallet.svg';
import { ReactComponent as UserIcon } from '../../media/svg/user.svg';

import AuthContext from '../../context/AuthContext';

import {AuthorizationComponent} from '../UserLogin';

import {NotificationBell, BalanceTopUpPopUP, CurrentBalancePopUP, FreeSlotsPurchasePopUP} from './Common_Components';

import ChatController from '../chat/Chat_Components'

import {ReactComponent as AddIcon} from '../../media/svg/add_slots.svg';

import '../../css/header.css';


function Header_Logo() {
    return (
        <div className='logo_container'>
            <Link to='/' className='logo_link'>Главная</Link>
        </div>
    );
}

function NavItems({user}) {
    return (
        <div className='navigation_items'>
            <ul className='row_container'>
                {user.id && <Select_Navigate />}  
                <Navigation_Item item_name='Найти задания' link='/order_tasks' /> 
                <Navigation_Item item_name='Готовые задания' link='/ready_tasks' />
                <Navigation_Item item_name='Исполнители' link='/users' />
            </ul>
        </div>
    );
}

function UserWalletItem() {
    const { user, accessToken } = useContext(AuthContext);
    const [paymentValue, setPaymentValue] = useState({});
    const [displayedPOP, setDisplayedPOP] = useState(null);
    const [isBalanceTopUp, setIsBalanceTopUp] = useState(false);
    const [isCurrentBalancePopup, setIsCurrentBalancePopup] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const [showPopup, setShowPopup] = useState(false);
    const menuRef = useRef(null);

    const requiredKeys = ["amount"];

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    function togglePopUp() {
        setIsBalanceTopUp(prevState => !prevState);
    }

    const handleChange = (event) => {
        if (event?.target) {
            const { name, value } = event.target;

            setPaymentValue(prevState => {
                // очищаем ключ, если значение пустое или 0
                if (value === "" || value == null || Number(value) === 0) {
                    const { [name]: _, ...rest } = prevState;
                    return rest;
                }
                return {
                    ...prevState,
                    [name]: value
                };
            });
        } else if (event?.name) {
            setPaymentValue(prevState => {
                const { [event.name]: _, ...rest } = prevState;
                return rest;
            });
        }
    };

    const isFormValid = () => {
        return requiredKeys.every(key => {
            const val = paymentValue[key];
            return val !== undefined && val !== null && val !== "" && Number(val) > 0;
        });
    };

    const payment_request = async () => {
        if (!isFormValid()) {
            console.warn("Форма невалидна, amount не указан или равен 0");
            return;
        }

        try {
            const response = await axios.post(
                "/api/payments/start_payment/",
                { amount: paymentValue.amount },
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );

            if (response.data?.payment_url) {
                window.location.href = response.data.payment_url;
            }
        } catch (error) {
            const message = error.response?.data?.message || 'Ошибка при оплате';
            setDisplayedPOP(<Error_POP_Element message={message} />);
            setShowPopup(true);
        }
    };

    const withdrawal_request = async (formData) => {
        try {
            const response = await axios.post(
                "/api/payments/withdrawal/",
                {
                    data: formData
                },
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );

            if (response.status === 201 && response.data?.id) {
                setIsCurrentBalancePopup(false);
                setDisplayedPOP(<Loading_POP_Element main_text="Заявка на вывод средств оформлена, средства поступят на счет в течение дня." 
                    sub_text="Если средства не поступят в течение дня, обратитесь в поддержку."/>);
                setShowPopup(true);

            } else {
                throw new Error(response.data?.message || 'Ошибка при выводе средств');
            }
        } catch (error) {
            const message = error.response?.data?.message || error.message || 'Ошибка при выводе средств';
            setDisplayedPOP(<Error_POP_Element message={message} />);
            setShowPopup(true);
        }
    };

    return (
        <>
            {isCurrentBalancePopup && (
                <CurrentBalancePopUP
                    isVisible={isCurrentBalancePopup}
                    onClose={() => setIsCurrentBalancePopup(false)}
                    balance={user?.wallet?.balance}
                    onClick={withdrawal_request}
                />
            )}
            {isBalanceTopUp && (
                <BalanceTopUpPopUP
                    isVisible={true}
                    onClose={() => togglePopUp()}
                    onChange={(e) => handleChange(e)}
                    onClick={() => payment_request()}
                />
            )}
            {showPopup && (
                <PopUpComponent
                    isVisible={showPopup}
                    displayed={displayedPOP}
                    onClose={() => setShowPopup(false)}
                />
            )}
            <div className="user_profile_link_container" ref={menuRef}>
                <div
                    className="user_menu_link"
                    id="user_menu_item"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <WalletIcon id="wallet_svg" style={{ fill: isOpen && "#55ced6" }} />
                </div>
                {isOpen && (
                    <div className="user_menu_dropdown_container" id="dropdown_style">
                        <div className="wallet_balance">
                            <span>Баланс:</span>
                            <span className="balance_amount">{user.wallet.balance}</span>
                            {user.wallet?.frozen != null && (
                                <span className="frozen_amount">Заморожено: {user.wallet.frozen}</span>
                            )}
                        </div>
                        <button className="wallet_action_button" onClick={togglePopUp}>
                            Пополнить
                        </button>
                        <button className="wallet_action_button" onClick={() => setIsCurrentBalancePopup(true)}>Вывести</button>
                    </div>
                )}
            </div>
        </>
    );
}


function UserProfileLink({ user }) {
    const { logout } = useContext(AuthContext);
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);

    const handleLogout = () => {
        logout();
    };

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    return (
        <div className="user_profile_link_container" ref={menuRef}>
            <div className="user_menu_link" id='user_profile_link' onClick={() => setIsOpen(!isOpen)}>
                <UserIcon id="user_svg" style={{ fill: isOpen && "#55ced6"}}/>
            </div>
            {isOpen && (
                <div className="user_menu_dropdown_container" id="dropdown_style">
                    <Link to={`/user/${user.id}`}>Профиль</Link>
                    <button onClick={handleLogout}>Выйти</button>
                </div>
            )}
        </div>
    );
}


function FreeSlotsManager({ user }) {
    const { refreshUserData } = useContext(AuthContext);
    const [isFreeSlotsPopup, setIsFreeSlotsPopup] = useState(false);
    const [showError, setShowError] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    // Обработчик ошибки при покупке слотов
    const handlePurchaseError = (error) => {
        setErrorMessage(error.response?.data?.message || "Ошибка при покупке");
        setShowError(true);
    };

    // Обработчик успешной покупки слотов
    const handlePurchaseSuccess = async () => {
        setIsFreeSlotsPopup(false);
        await refreshUserData();
    };

    // Открытие попапа покупки слотов
    const handleOpenSlotsPopup = () => {
        setIsFreeSlotsPopup(true);
    };

    // Закрытие попапа покупки слотов
    const handleCloseSlotsPopup = () => {
        setIsFreeSlotsPopup(false);
    };

    // Закрытие попапа с ошибкой
    const handleCloseError = () => {
        setShowError(false);
    };

    return (
        <>
            <div className="free_space_container">
                <span>Кол-во размещений: {user.free_slots}</span>
                <div className="user_menu_link" id="user_menu_item_small" onClick={handleOpenSlotsPopup}>
                    <AddIcon id='add_slots_svg' style={{ fill: isFreeSlotsPopup && "#55ced6"}}/>
                </div>
            </div>

            {isFreeSlotsPopup && (
                <FreeSlotsPurchasePopUP
                    isVisible={isFreeSlotsPopup}
                    onClose={handleCloseSlotsPopup}
                    onError={handlePurchaseError}
                    onSuccess={handlePurchaseSuccess}
                />
            )}

            {showError && (
                <PopUpComponent
                    isVisible={showError}
                    displayed={<Error_POP_Element message={errorMessage} />}
                    onClose={handleCloseError}
                />
            )}
        </>
    );
}

function UserMenuItems({ user, onOpenRegistration }) {
    return (
        <div className='user_menu_items_container'>
            {user.id && <FreeSlotsManager user={user} />}
            {user.id && <ChatController/>}
            {user.id && <NotificationBell/>}
            {user.id && <UserWalletItem />}
            {user.id && <UserProfileLink user={user} />}
            {!user.id && <a onClick={onOpenRegistration}>Войти</a>}
        </div>
    );
}

   
function ToolbarHeader() {
    const [isAuthVisible, setIsAuthVisible] = useState(false);
    const { user, authData } = useContext(AuthContext);

    useEffect(() => {
        if (authData.authType === 'recovery') {
            setIsAuthVisible(true);
        }
    }, [authData]);


    const onOpenRegistration = () => {
        setIsAuthVisible(prevState => !prevState);
        if (authData.authType === 'recovery') {
            authData.authType = 'login';
        }
    };

    return (
        <header className='toolbar'>
            {isAuthVisible && <AuthorizationComponent isAuthVisible={isAuthVisible} authData={authData.authType} onOpenRegistration={onOpenRegistration}/>}
            <div className='toolbar_inner_container'>
                <Header_Logo />
                <NavItems user={user}/>
                <UserMenuItems user={user} onOpenRegistration={onOpenRegistration} />
            </div>
        </header>
    );
}


  export default ToolbarHeader;