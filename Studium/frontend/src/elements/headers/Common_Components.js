import React, { useState, useRef, useEffect, useContext } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import {createPortal} from 'react-dom'
import WebSocketContext, { notificationConfig } from '../../context/WebsocketContext.js';
import AuthContext from '../../context/AuthContext.js';
import { Input_Section, Select_Section } from '../main_elements.js';

import { ReactComponent as BellIcon } from '../../media/svg/bell.svg';

function NotificationBell() {
    const { notifications, unreadCount, markAllAsRead, markAsRead, formatNotificationTime } = useContext(WebSocketContext);

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

    useEffect(() => {
        if (!isOpen) {
            markAllAsRead();
        }
    }, [isOpen]);

    const categoryIcons = Object.fromEntries(
        notificationConfig.iconMap.flatMap(({ keys, icon }) => keys.map(key => [key, icon]))
    );

    return (
        <div className="notification_bell" ref={menuRef}>
            <div className="user_menu_link" id="user_menu_item" onClick={() => setIsOpen(!isOpen)}>
                <BellIcon id="bell_svg" style={{ fill: isOpen && "#55ced6" }} />
                {unreadCount > 0 && <span className="notification_badge">{unreadCount}</span>}
            </div>

            {isOpen && (
                <div className="notification_dropdown">
                    <div className="notification_header">
                        <h4>Уведомления</h4>
                    </div>
                    <ul className="notification_list">
                        {notifications.length > 0 ? (
                            notifications.map((data) => (
                                <NotificationItem
                                    key={data.id}
                                    icon={categoryIcons[data.content]}
                                    message={data.message}
                                    time={formatNotificationTime(data.created_at)}
                                    link={notificationConfig.getNotificationLink(data.content, data.object_id, data.add_data)}
                                    isRead={data.is_read}
                                    onClick={() => markAsRead(data.id)}
                                />
                            ))
                        ) : (
                            <li className="notification_empty">Нет новых уведомлений</li>
                        )}
                    </ul>
                </div>
            )}
        </div>
    );
}

function NotificationItem({ icon, message, time, link, isRead, onClick }) {
    return (
        <li>
            <Link className="notification_item" id={!isRead && "unread_notification"} onClick={onClick} to={link}>
                {icon && <img className="notification_icon" src={icon} alt="icon" />}
                <div className="notification_text">
                    <span className="notification_main_text">{message}</span>
                    <span className="notification_time">{time}</span>
                </div>
            </Link>
        </li>
    );
}

function BalanceTopUpPopUP(props) {    
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
                    <div className='pop_up_element' id='balans_top_up_pop_up_elements' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='short_pop_up_container' id='top_up_pop_up_container'>
                                <span className='main_text'>На какую сумму хотите пополнить кошелек?</span>
                                <Input_Section placeholder='Сумма пополнения' value_name="amount" onChange={props.onChange}/>
                                <button className='pop_up_button' id='confirm_pop_up_button' onClick={props.onClick}>Пополнить</button>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function WithdrawTabs({ activeTab, onChange }) {
    return (
        <div className='menu_element_main_container'>
            <div className='row_container withdraw_tabs' style={{ gap: '8px' }}>
                <button
                    className='pop_up_button'
                    id={activeTab === 'sbp' ? 'confirm_pop_up_button' : undefined}
                    onClick={() => onChange('sbp')}
                >
                    По СБП
                </button>
                <button
                    className='pop_up_button'
                    id={activeTab === 'card' ? 'confirm_pop_up_button' : undefined}
                    onClick={() => onChange('card')}
                >
                    По номеру карты
                </button>
            </div>
        </div>
    );
}


function PhoneInput({ value, onChange, placeholder }) {
  const [phone, setPhone] = useState(value || "");
  const inputRef = useRef(null);

  const formatPhone = (value) => {
    const digits = value.replace(/\D/g, "").slice(0, 11);
    let formatted = "";

    if (digits.length > 0) formatted += "+7 ";
    if (digits.length > 1) formatted += "(" + digits.slice(1, 4);
    if (digits.length >= 4) formatted += ") " + digits.slice(4, 7);
    if (digits.length >= 7) formatted += "-" + digits.slice(7, 9);
    if (digits.length >= 9) formatted += "-" + digits.slice(9, 11);

    return formatted;
  };

  const handleChange = (e) => {
    const input = e.target;
    const rawValue = input.value;
    const selectionStart = input.selectionStart;

    const digitsBeforeCursor = rawValue
      .slice(0, selectionStart)
      .replace(/\D/g, "").length;

    const formattedValue = formatPhone(rawValue);
    setPhone(formattedValue);
    onChange({ target: { name: "phone_number", value: formattedValue } });

    // Коррекция позиции курсора
    let cursorPosition = 0;
    let digitsCount = 0;
    while (digitsCount < digitsBeforeCursor && cursorPosition < formattedValue.length) {
      if (/\d/.test(formattedValue[cursorPosition])) digitsCount++;
      cursorPosition++;
    }

    setTimeout(() => {
      input.setSelectionRange(cursorPosition, cursorPosition);
    }, 0);
  };

  useEffect(() => {
    setPhone(value || "");
  }, [value]);

  return (
    <div className='section_container 'id='pop_up_section_container'>
        <input
            className='section_input'
            ref={inputRef}
            type="text"
            value={phone}
            onChange={handleChange}
            placeholder={placeholder}
            maxLength={18}
        />
    </div>
  );
}

function SBPWithdrawForm({ formData, errors, onChange }) {
  return (
    <div className='withdraw_form_grid'>
      <div className='menu_element_main_container'>
        <span className='main_text'>Фамилия:</span>
        <div className='column_container'>
          <Input_Section placeholder='Фамилия' value_name="last_name" value={formData.last_name} onChange={onChange} id='pop_up_section_container' />
          {errors.last_name && <span className='error_text'>{errors.last_name}</span>}
        </div>
      </div>
      <div className='menu_element_main_container'>
        <span className='main_text'>Имя:</span>
        <div className='column_container'>
          <Input_Section placeholder='Имя' value_name="first_name" value={formData.first_name} onChange={onChange} id='pop_up_section_container' />
          {errors.first_name && <span className='error_text'>{errors.first_name}</span>}
        </div>
      </div>
      <div className='menu_element_main_container'>
        <span className='main_text'>Банк:</span>
        <div className='column_container'>
          <Select_Section fileName='withdraw' value={formData.bank_id} title='Название Банка' value_name='bank_id' onChange={onChange} id='pop_up_section_container' />
          {errors.bank_id && <span className='error_text'>{errors.bank_id}</span>}
        </div>
      </div>
      <div className='menu_element_main_container'>
        <span className='main_text'>Телефон:</span>
        <div className='column_container'>
          <PhoneInput value={formData.phone_number} onChange={onChange} placeholder='+7 (999) 123-45-67'/>
          {errors.phone_number && <span className='error_text'>{errors.phone_number}</span>}
        </div>
      </div>
      <div className='menu_element_main_container'>
        <span className='main_text'>Сумма вывода:</span>
        <div className='column_container'>
          <Input_Section placeholder='Сумма' value_name="amount" value={formData.amount} onChange={onChange} id='pop_up_section_container' />
          {errors.amount && <span className='error_text'>{errors.amount}</span>}
        </div>
      </div>
    </div>
  );
}


function CardInput({ value, onChange, placeholder }) {
  const [card, setCard] = useState(value || "");
  const inputRef = useRef(null);

  const formatCard = (value) => {
    const digits = value.replace(/\D/g, "").slice(0, 16);
    return digits.replace(/(.{4})/g, "$1 ").trim();
  };

  const handleChange = (e) => {
    const input = e.target;
    const rawValue = input.value;
    const selectionStart = input.selectionStart;

    const digitsBeforeCursor = rawValue.slice(0, selectionStart).replace(/\D/g, "").length;

    const formattedValue = formatCard(rawValue);
    setCard(formattedValue);

    // Передаем значение наружу
    onChange({ target: { name: "card_number", value: formattedValue } });

    // Коррекция позиции курсора
    let cursorPosition = 0;
    let digitsCount = 0;
    while (digitsCount < digitsBeforeCursor && cursorPosition < formattedValue.length) {
      if (/\d/.test(formattedValue[cursorPosition])) digitsCount++;
      cursorPosition++;
    }

    setTimeout(() => {
      input.setSelectionRange(cursorPosition, cursorPosition);
    }, 0);
  };

  // Если value извне изменяется (например reset формы)
  useEffect(() => {
    setCard(value || "");
  }, [value]);

  return (
    <div className='section_container 'id='pop_up_section_container'>
        <input
            className='section_input'
            ref={inputRef}
            type="text"
            value={card}
            onChange={handleChange}
            placeholder={placeholder}
            maxLength={19} // 16 цифр + 3 пробела
        />
    </div>
  );
}

function CardWithdrawForm({ formData, errors, onChange }) {
  return (
    <div className='withdraw_form_grid'>
      <div className='menu_element_main_container'>
        <span className='main_text'>Фамилия:</span>
        <div className='column_container'>
          <Input_Section placeholder='Фамилия' value_name="last_name" value={formData.last_name} onChange={onChange} id='pop_up_section_container' />
          {errors.last_name && <span className='error_text'>{errors.last_name}</span>}
        </div>
      </div>

      <div className='menu_element_main_container'>
        <span className='main_text'>Имя:</span>
        <div className='column_container'>
          <Input_Section placeholder='Имя' value_name="first_name" value={formData.first_name} onChange={onChange} id='pop_up_section_container' />
          {errors.first_name && <span className='error_text'>{errors.first_name}</span>}
        </div>
      </div>

      <div className='menu_element_main_container'>
        <span className='main_text'>Банк:</span>
        <div className='column_container'>
            <Select_Section fileName='withdraw' value={formData.bank_id} title='Название Банка' value_name='bank_id' onChange={onChange} id='pop_up_section_container' />
            {errors.bank_id && <span className='error_text'>{errors.bank_id}</span>}
        </div>
      </div>

      <div className='menu_element_main_container'>
        <span className='main_text'>Номер карты:</span>
        <div className='column_container'>
          <CardInput value={formData.card_number} onChange={onChange} placeholder='0000 0000 0000 0000' />
          {errors.card_number && <span className='error_text'>{errors.card_number}</span>}
        </div>
      </div>

      <div className='menu_element_main_container'>
        <span className='main_text'>Сумма вывода:</span>
        <div className='column_container'>
          <Input_Section placeholder='Сумма' value_name="amount" value={formData.amount} onChange={onChange} id='pop_up_section_container' />
          {errors.amount && <span className='error_text'>{errors.amount}</span>}
        </div>
      </div>
    </div>
  );
}

function CurrentBalancePopUP(props) {
    const [activeTab, setActiveTab] = useState('sbp'); // 'sbp' | 'card'
    const [formData, setFormData] = useState({
        // Общие поля
        last_name: '',
        first_name: '',
        amount: '',
        bank_id: '',
        // Для СБП
        phone_number: '',
        // Для карты
        card_number: ''
    });
    const [errors, setErrors] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        document.body.style.overflow = props.isVisible ? 'hidden' : 'unset';
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [props.isVisible]);

    useEffect(() => {
        if (props.isVisible) {
            setActiveTab('sbp');
            setFormData({
                last_name: '',
                first_name: '',
                amount: '',
                bank_id: '',
                phone_number: '',
                card_number: ''
            });
            setErrors({});
        }
    }, [props.isVisible]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        
        // Очищаем ошибку для данного поля при изменении
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
    
        // Общие проверки
        if (!formData.last_name.trim()) {
            newErrors.last_name = 'Введите фамилию';
        }
        if (!formData.first_name.trim()) {
            newErrors.first_name = 'Введите имя';
        }
        if (!`${formData.bank_id}`.trim()) {
            newErrors.bank_id = 'Выберите банк';
        }
        if (!formData.amount.trim()) {
            newErrors.amount = 'Введите сумму для вывода';
        } else {
            const amount = parseFloat(formData.amount);
            if (isNaN(amount) || amount <= 0) {
                newErrors.amount = 'Сумма должна быть положительным числом';
            } else if (amount < 1000) {
                newErrors.amount = 'Сумма вывода должна быть не меньше 1000₽';
            } else if (amount > props.balance) {
                newErrors.amount = `Сумма вывода не может превышать баланс (${props.balance}₽)`;
            }
        }
    
        if (activeTab === 'sbp') {
            // Телефон (минимум 10 цифр)
            const digits = formData.phone_number.replace(/\D/g, '');
            if (!digits) {
                newErrors.phone_number = 'Введите номер телефона';
            } else if (digits.length < 10 || digits.length > 15) {
                newErrors.phone_number = 'Введите корректный номер телефона';
            }
        } else if (activeTab === 'card') {
            // Номер карты (16-19 цифр)
            const digits = formData.card_number.replace(/\D/g, '');
            if (!digits) {
                newErrors.card_number = 'Введите номер карты';
            } else if (digits.length < 16 || digits.length > 19) {
                newErrors.card_number = 'Введите корректный номер карты';
            }
        }
    
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };
    

    const handleSubmit = async () => {
        if (!validateForm()) {
            return;
        }

        if (!props.onClick) {
            console.warn('Обработчик onClick не передан в CurrentBalancePopUP');
            return;
        }

        const enhancedPayload = {
            ...formData,
            method: activeTab,
        };

        setIsSubmitting(true);
        try {
            await props.onClick(enhancedPayload);
        } catch (error) {
            console.error('Ошибка при выводе средств:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            {createPortal(
                <div className='pop_up_element_shadow' onClick={props.onClose}>
                    <div className='pop_up_element' id='withdraw_pop_up_elements' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='short_pop_up_container'>
                                <div className='column_container' id='gap_container'>
                                    <div className='menu_element_main_container'>
                                        <span className='main_text'>Текущий баланс:</span>
                                        <span className='auth_required_highlight'>
                                            {props.balance}₽
                                        </span>
                                    </div>
                                    <WithdrawTabs activeTab={activeTab} onChange={setActiveTab} />

                                    {activeTab === 'sbp' && (
                                        <SBPWithdrawForm formData={formData} errors={errors} onChange={handleInputChange}/>
                                    )}

                                    {activeTab === 'card' && (
                                        <CardWithdrawForm formData={formData} errors={errors} onChange={handleInputChange}/>
                                    )}

                                    <button 
                                        className='pop_up_button' 
                                        id='confirm_pop_up_button' 
                                        onClick={handleSubmit}
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? 'Обработка...' : 'Вывести'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function FreeSlotsPurchasePopUP(props) {    
    const [packages, setPackages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        document.body.style.overflow = props.isVisible ? 'hidden' : 'unset';
        
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [props.isVisible]);

    useEffect(() => {
        if (!props.isVisible) return;
        const controller = new AbortController();
        setIsLoading(true);
        setError(null);
        (async () => {
            try {
                const response = await axios.get('/api/payments/slot_packages/', { signal: controller.signal });
                const data = response?.data;
                setPackages(Array.isArray(data) ? data : []);
            } catch (e) {
                if (controller.signal.aborted || e.name === 'CanceledError') return;
                const message = e.message || 'Не удалось загрузить данные';
                setError(message);
            } finally {
                setIsLoading(false);
            }
        })();

        return () => controller.abort();
    }, [props.isVisible]);
    
    return (
        <>
            {createPortal(
                <div className='pop_up_element_shadow' onClick={props.onClose}>
                    <div className='pop_up_element' id='free_slots_pop_up_element' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='status_pop_up_container'>
                                <span className='main_text'>Сколько слотов размещения хотите купить?</span>
                                {isLoading && <span className='main_text'>Загрузка...</span>}
                                {error && <span className='error_text'>{error}</span>}
                                <ul className='free_slots_menu_container'>
                                    {packages.map((p) => (
                                        <FreeSpaceOffer
                                            key={p.id}
                                            id={p.id}
                                            count_buy={p.slots_count}
                                            amount={p.price}
                                            old_amount={p.old_price}
                                            description={p.description}
                                            onClose={props.onClose}
                                            onError={props.onError}
                                            onSuccess={props.onSuccess}
                                        />
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function FreeSpaceOffer(props){
    const { accessToken } = useContext(AuthContext);
    const [isLoading, setIsLoading] = useState(false);

    const handlePurchase = async () => {
        if (isLoading) return;
        setIsLoading(true);
        try {
            await axios.post('/api/payments/buy_slot_package/', { package_id: props.id }, { headers: { ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}) } });
            
            if (props.onSuccess) {
                props.onSuccess();
            } else {
                props.onClose();
            }
        } catch (error) {
            props.onError(error);
            props.onClose();
        } finally {
            setIsLoading(false);
        }
    };

    return(
        <li className='row_space_between_container'>
            <div className='column_container'>
                <span className='main_text'>Купить: {props.count_buy} сл. <span className='price_new'>{props.amount}₽</span></span>
                {props.description && <span className='muted_text'>{props.description}</span>}
            </div>
            <button className='pop_up_button' id='free_space_pop_up_button' onClick={handlePurchase} disabled={isLoading}>
                {isLoading ? 'Покупка...' : 'Купить'}
            </button>
        </li>
    );
}

export {NotificationBell, BalanceTopUpPopUP, CurrentBalancePopUP, FreeSlotsPurchasePopUP};