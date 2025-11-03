import React, { useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useNavigate, useLocation } from 'react-router-dom';

import { ReactComponent as UserIcon } from '../../media/svg/user.svg';
import { ReactComponent as BurgerMenuIcon } from '../../media/svg/burger_menu.svg';

import AuthContext from '../../context/AuthContext';
import WebSocketContext from '../../context/WebsocketContext.js';

import { AuthorizationComponent } from '../UserLogin';
import { Navigation_Item, PopUpComponent, Error_POP_Element, Loading_POP_Element, Select_Navigate } from '../main_elements';
import { BalanceTopUpPopUP, CurrentBalancePopUP, FreeSlotsPurchasePopUP } from './Common_Components';

import Logo55 from '../../media/png/Logo 55.png';

import '../../css/mobile_header.css';

function MobileSideMenu({ showMenu, setShowMenu, user }) {
    if (!showMenu) return null;
    return (
        <div className="mobile_menu_overlay">
            <div className="mobile_menu_background" onClick={() => setShowMenu(false)} />
            <div className="mobile_menu_container">
                <div className="mobile_menu_header">
                    <div className="mobile_menu_logo">
                        <img src={Logo55} alt="logo" className="mobile_menu_logo_img" />
                        <span className="mobile_menu_logo_text">Studium</span>
                    </div>
                    <button onClick={() => setShowMenu(false)} className="mobile_menu_close_btn">&times;</button>
                </div>
                <nav className="mobile_menu_nav">
                    <Navigation_Item class="side_menu_text" item_name="Главная" link="/" />
                    {user.id && <Select_Navigate class="side_menu_text"/>}
                    <Navigation_Item class="side_menu_text" item_name="Готовые задания" link="/ready_tasks" />
                    <Navigation_Item class="side_menu_text" item_name="Исполнители" link="/users" />
                </nav>
                <nav className="mobile_menu_nav_secondary">
                    <Navigation_Item class="side_menu_text" item_name="Помощь" link="/create_report" />
                    <Navigation_Item class="side_menu_text" item_name="О нас" link="/about_us" />
                    <Navigation_Item class="side_menu_text" item_name="Правила сервиса" link="/rules" />
                </nav>
            </div>
        </div>
    );
}

function MobileNotificationsMenu({ show, setShow, setUnreadCount }) {
    const { notifications, unreadCount, markAllAsRead, markAsRead, formatNotificationTime} = WebSocketContext();

    useEffect(() => {
        if (setUnreadCount) {
            setUnreadCount(unreadCount);
        }
    }, [unreadCount, setUnreadCount]);

    if (!show) return null;

    return (
        <div className="notifications_overlay" onClick={() => setShow(false)}>
            <div className="notifications_container" onClick={(e) => e.stopPropagation()}>
                <button className="popup_close_button" onClick={() => setShow(false)}>&times;</button>
                <div className="notifications_header">
                    <span className="notifications_header_text">Уведомления</span>
                </div>
                <div className="notifications_scroll_container">
                    <ul className="notifications_list">
                        {notifications.length > 0 ? notifications.map((data) => (
                            <li
                                key={data.id}
                                className={`notifications_item ${data.is_read ? 'read' : 'unread'}`}
                                onClick={() => markAsRead(data.id)}
                            >
                                <div className={`notifications_message ${data.is_read ? 'read' : 'unread'}`}>
                                    {data.message}
                                </div>
                                <div className="notifications_timestamp">
                                    {formatNotificationTime(data.created_at)}
                                </div>
                            </li>
                        )) : (
                            <li className="notifications_empty">Нет новых уведомлений</li>
                        )}
                    </ul>
                </div>
                <button onClick={markAllAsRead} className="notifications_mark_all_button">
                    Отметить все как прочитанные
                </button>
            </div>
        </div>
    );
}

function MobileUserMenu({ show, onClose, user, setShowNotifications, unreadCount }) {
    const { logout, accessToken, refreshUserData } = useContext(AuthContext);

    const [isBalanceTopUp, setIsBalanceTopUp] = useState(false);
    const [isCurrentBalancePopup, setIsCurrentBalancePopup] = useState(false);
    const [isFreeSlotsPopup, setIsFreeSlotsPopup] = useState(false);
    const [displayedPOP, setDisplayedPOP] = useState(null);
    const [showPopup, setShowPopup] = useState(false);
    const [paymentValue, setPaymentValue] = useState({});

    const requiredKeys = ["amount"];

    const toggleTopUpPopup = () => setIsBalanceTopUp(prev => !prev);
    const openWithdrawPopup = () => setIsCurrentBalancePopup(true);
    const closeWithdrawPopup = () => setIsCurrentBalancePopup(false);

    const handleChange = (event) => {
        if (event?.target) {
            const { name, value } = event.target;
            setPaymentValue(prevState => {
                if (value === "" || value == null || Number(value) === 0) {
                    const { [name]: _, ...rest } = prevState;
                    return rest;
                }
                return { ...prevState, [name]: value };
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
        if (!isFormValid()) return;
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
                    owner_name: formData.full_name,
                    bic: formData.bik,
                    account_number: formData.account_number,
                    amount: formData.amount
                },
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );
            if (response.status === 201 && response.data?.id) {
                setIsCurrentBalancePopup(false);
                setDisplayedPOP(<Loading_POP_Element main_text="Заявка на вывод средств оформлена, средства поступят на счет в течение дня." sub_text="Если средства не поступят в течение дня, обратитесь в поддержку."/>);
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

    const handleOpenSlotsPopup = () => setIsFreeSlotsPopup(true);
    const handleCloseSlotsPopup = () => setIsFreeSlotsPopup(false);
    const handlePurchaseError = (error) => {
        setDisplayedPOP(<Error_POP_Element message={error.message || "Ошибка при покупке"} />);
        setShowPopup(true);
    };
    const handlePurchaseSuccess = async () => {
        setIsFreeSlotsPopup(false);
        await refreshUserData();
    };

    const handleShowNotifications = () => {
        setShowNotifications(true);
        onClose();
    };

    const handleLogout = () => {
        logout();
        onClose();
    };

    if (!show) return null;

    return (
        <div className="user_menu_overlay">
            <div className="user_menu_background" onClick={onClose} />
            <div className="user_menu_container">
                {isCurrentBalancePopup && (
                    <CurrentBalancePopUP
                        isVisible={isCurrentBalancePopup}
                        onClose={closeWithdrawPopup}
                        balance={user?.wallet?.balance}
                        onClick={withdrawal_request}
                    />
                )}
                {isBalanceTopUp && (
                    <BalanceTopUpPopUP
                        isVisible={true}
                        onClose={toggleTopUpPopup}
                        onChange={handleChange}
                        onClick={payment_request}
                    />
                )}
                {isFreeSlotsPopup && (
                    <FreeSlotsPurchasePopUP
                        isVisible={isFreeSlotsPopup}
                        onClose={handleCloseSlotsPopup}
                        onError={handlePurchaseError}
                        onSuccess={handlePurchaseSuccess}
                    />
                )}
                {showPopup && (
                    <PopUpComponent
                        isVisible={showPopup}
                        displayed={displayedPOP}
                        onClose={() => setShowPopup(false)}
                    />
                )}
                <nav className="user_menu_nav">
                    <div className="user_menu_balance_block">
                        <span className="user_menu_balance_text">Баланс: {user?.wallet?.balance ?? 0} ₽</span>
                        {user?.wallet?.frozen != null && (
                            <span className="user_menu_frozen_text">Заморожено: {user.wallet.frozen} ₽</span>
                        )}
                        <div className="user_menu_balance_buttons">
                            <button className="user_menu_btn_fill" onClick={toggleTopUpPopup}>Пополнить</button>
                            <button className="user_menu_btn_withdraw" onClick={openWithdrawPopup}>Вывести</button>
                        </div>
                    </div>
                    <div className="user_menu_slots_block">
                        <div className="user_menu_slots_header">
                            <span className="user_menu_slots_text">Кол-во размещений: {user.free_slots}</span>
                        </div>
                        <div className="user_menu_slots_buttons">
                            <button className="user_menu_btn_buy_slots" onClick={handleOpenSlotsPopup}>
                                Купить размещения
                            </button>
                        </div>
                    </div>
                    <span className="side_menu_text" onClick={handleShowNotifications}>
                        Уведомления
                        {unreadCount > 0 && (
                            <span className="notification_badge_mobile">{unreadCount}</span>
                        )}
                    </span>
                    <Link to={`/user/${user.id}`} className="side_menu_text">
                        Профиль
                    </Link>
                    <button
                        onClick={handleLogout}
                        className="user_menu_logout_button side_menu_text"
                    >
                        Выйти
                    </button>
                </nav>
            </div>
        </div>
    );
}

function MobileHeader() {
    const { user, authData } = useContext(AuthContext);
    const [isAuthVisible, setIsAuthVisible] = useState(false);
    const navigate = useNavigate();
    const [showMenu, setShowMenu] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const location = useLocation();

    useEffect(() => {
        setShowMenu(false);
        setShowUserMenu(false);
        setShowNotifications(false);
    }, [location]);

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
        <header className="mobile_toolbar mobile_toolbar_border">
            {isAuthVisible && (
                <AuthorizationComponent
                    isAuthVisible={isAuthVisible}
                    authData={authData.authType}
                    onOpenRegistration={onOpenRegistration}
                />
            )}
            <div className="mobile_toolbar_top">
                <div className="mobile_menu_icon" onClick={() => setShowMenu(true)}>
                    <BurgerMenuIcon className="mobile_menu_icon_svg" />
                </div>
                <div className="mobile_logo_center" onClick={() => navigate('/')}>
                    <span className="mobile_logo_text">Studium</span>
                </div>
                {!user.id ? (
                    <div className="mobile_user_icon" onClick={onOpenRegistration}>
                        <span className="mobile_login_text">Войти</span>
                    </div>
                ) : (
                    <div className="mobile_user_icon" onClick={() => setShowUserMenu(true)}>
                        <UserIcon className="mobile_user_icon_svg" />
                    </div>
                )}
            </div>

            <MobileSideMenu showMenu={showMenu} setShowMenu={setShowMenu} user={user} />
            {showUserMenu && (
                <MobileUserMenu
                    show={showUserMenu}
                    onClose={() => setShowUserMenu(false)}
                    user={user}
                    showNotifications={showNotifications}
                    setShowNotifications={setShowNotifications}
                    unreadCount={unreadCount}
                    setUnreadCount={setUnreadCount}
                />
            )}
            <MobileNotificationsMenu
                show={showNotifications}
                setShow={setShowNotifications}
                setUnreadCount={setUnreadCount}
            />
        </header>
    );
}


export default MobileHeader;
