import { useEffect, useContext } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import Rejected_Icon from '../media/png/Rejecter_Icon.png';
import AuthContext from '../context/AuthContext';

function ContextErrorPopUpComponent() {
    const { error, setError } = useContext(AuthContext);
    const navigate = useNavigate();

    useEffect(() => {
        document.body.style.overflow = error ? 'hidden' : 'unset';
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [error]);

    if (!error) return null;

    const handleClose = () => {
      setError(null);
      navigate('/');
    };

    return createPortal(
        <div
            className="pop_up_element_shadow"
            onClick={handleClose}
        >
            <div className="pop_up_element" onClick={(e) => e.stopPropagation()}>
                <button className="popup_close_button" onClick={handleClose}>
                    &times;
                </button>
                <div className="pop_up_body">
                    <div className="status_pop_up_container">
                        <img src={Rejected_Icon} alt="Ошибка" className="Error_Pop_Icon" />
                        <span className="main_text">
                            {error || 'Что-то пошло не так!'}
                        </span>
                    </div>
                </div>
            </div>
        </div>,
        document.getElementById('portal')
    );
}

export default ContextErrorPopUpComponent;
