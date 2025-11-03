import React, { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { PopUpComponent } from './main_elements';

function RecoveryInfo(props) {
    const [copied, setCopied] = useState(false);
    const email = "studiuminfo@yandex.ru";

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(email);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Ошибка копирования:", err);
            alert("Не удалось скопировать email");
        }
    };

    return (
        <div className="recovery_info">
            <h2 className="login_title">Восстановление пароля</h2>
            <p className="recovery_text">
                Для восстановления пароля, пожалуйста, напишите на почту:<br/>
                <strong
                    onClick={handleCopy}
                    className={`email-text ${copied ? "copied" : ""}`}
                    title="Кликните, чтобы скопировать"
                >
                    {email}
                </strong>
            </p>
            {copied && <div className="copy-notification">Скопировано в буфер обмена!</div>}
        </div>
    );
}

function Password_Recovery(props) {
    const { authData } = useContext(AuthContext);

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');
    const [canSubmit, setCanSubmit] = useState(false);

    const [checks, setChecks] = useState({
        length: false,
        upper: false,
        digit: false,
        special: false,
        match: false,
    });

    useEffect(() => {
        const newChecks = {
            length: password.length >= 8,
            upper: /[A-ZА-Я]/.test(password),
            digit: /[0-9]/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>_\-\=+`~;]/.test(password),
            match: password && password === confirmPassword,
        };

        setChecks(newChecks);

        const allPassed = Object.values(newChecks).every(Boolean);
        setCanSubmit(allPassed);
    }, [password, confirmPassword]);

    const handleSubmit = async (event) => {
        event.preventDefault();

        try {
            const response = await axios.post('/api/auth/reset_password/', {
                password: password,
                token: authData.token});

            if (response.status === 200) {
                setError('');
                setSuccess('Пароль успешно изменен');
                setTimeout(() => {
                    props.onOpenRegistration('login');
                }, 2000);
            }
        } catch (error) {
            setSuccess('');
            setError(error.message|| 'Произошла ошибка при смене пароля');
        }
    };

    const renderCheck = (passed, text) => (
        <div style={{ color: passed ? 'green' : 'red', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>{passed ? '✔️' : '❌'}</span>
            <span>{text}</span>
        </div>
    );

    return (
        <form className="login_form" onSubmit={handleSubmit}>
            <h2 className="login_title">Восстановление пароля</h2>

            <label className="login_label">Новый пароль</label>
            <input
                className="login_input"
                type="password"
                placeholder="Введите новый пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />

            <label className="login_label">Подтверждение пароля</label>
            <input
                className="login_input"
                type="password"
                placeholder="Повторите новый пароль"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
            />

            <div className="password_checks" style={{ marginTop: '10px', fontSize: '14px' }}>
                {renderCheck(checks.length, 'Не менее 8 символов')}
                {renderCheck(checks.upper, 'Хотя бы одна заглавная буква')}
                {renderCheck(checks.digit, 'Хотя бы одна цифра')}
                {renderCheck(checks.special, 'Хотя бы один спецсимвол')}
                {renderCheck(checks.match, 'Пароли совпадают')}
            </div>

            {success && <div className="login_success">{success}</div>}
            {error && <div className="login_error">{error}</div>}

            <div className="login_agreement" style={{ marginBottom: '15px', fontSize: '14px', textAlign: 'center' }}>
                Нажимая кнопку "Изменить пароль", вы соглашаетесь с <a href="/rules" target="_blank" style={{ color: '#007bff', textDecoration: 'underline' }}>правилами пользования</a>
            </div>

            <button className="login_button" type="submit" disabled={!canSubmit}>
                Изменить пароль
            </button>
        </form>
    );
}

function User_Login(props) {
    const { login, error, user, setError } = useContext(AuthContext);

    const handleSuccess = (event) => {
        event.preventDefault();
        login(event);
    };

    const handleAgreementClick = () => {
        props.onClose(false);
    };

    useEffect(() => {
        if (user.id) {
            props.onClose(false);
        }
    }, [user]);

    useEffect(() => {
        if (!props.isAuthVisible) {
            setError(null);
        }
    }, [props.isAuthVisible]);

    return (
        <form className="login_form" onSubmit={handleSuccess}>
            <h2 className="login_title">Вход в аккаунт</h2>

            <label className="login_label">Email</label>
            <input
                className="login_input"
                type="email"
                name="email"
                placeholder="Введите ваш email"
                required
            />

            <label className="login_label">Пароль</label>
            <input
                className="login_input"
                type="password"
                name="password"
                placeholder="Введите пароль"
                required
            />

            {error && <div className="login_error">{error.message}</div>}

            <p className="login_agreement">
                Нажимая кнопку "Войти", вы соглашаетесь с <Link to="/rules" className="login_agreement_link" onClick={handleAgreementClick}>правилами сервиса</Link>
            </p>

            <button className="login_button recovery_button" type="button" onClick={() => {
                props.onOpenRegistration('recovery_info');
            }}>
                Забыли пароль?
            </button>

            <button className="login_button" type="submit">Войти</button>
        </form>
    );
}

function AuthorizationComponent(props) {
    const [authType, setAuthType] = useState(props.authData || 'login');

    const handleAuthTypeChange = (type) => {
        setAuthType(type);
        renderAuthForm();
    };

    const renderAuthForm = () => {
        switch (authType) {
            case 'recovery':
                return <Password_Recovery onOpenRegistration={handleAuthTypeChange} />;
            case 'recovery_info':
                return <RecoveryInfo onClose={() => handleAuthTypeChange('login')} />;
            default:
                return <User_Login onClose={props.onOpenRegistration} onOpenRegistration={handleAuthTypeChange} />;
        }
    };
    
    return (
        <PopUpComponent 
            displayed={
                <div style={{ position: 'relative' }}>
                    {renderAuthForm()}
                </div>
            } 
            id={authType === 'login' ? 'login_pop_up_element' : authType === 'recovery_info' ? 'recovery_info_pop_up_element' : 'recovery_pop_up_element'}
            isVisible={props.isAuthVisible} 
            onClose={props.onOpenRegistration} 
        />
    );
}

export {AuthorizationComponent};