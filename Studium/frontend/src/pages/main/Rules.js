import axios from 'axios';
import React, {useState, useEffect} from 'react';

import { Loading_Spinner, PopUpComponent, Error_POP_Element } from '../../elements/main_elements';



function Rules_Page_Main({ data }) {
    return (
        <div className="page_container">
            <div className='row_container'>
                <h1 className="page_main_title_text">Правила сервиса</h1>
            </div>
            <div className="rules_grid">
                {data.map((item, index) => (
                    <Grid_Element
                        key={index}
                        title={item.title}
                        currentLink={item.currentLink}
                        previousLinks={item.previousLinks}
                    />
                ))}
            </div>
        </div>
    );
}

function Grid_Element({ title, currentLink, previousLinks }) {
    return (
        <div className="column_container grid_element">
            <h2 className="rules_header_text">{title}</h2>

            <div className="column_container rules_grid_main_container">
                <div className="column_container">
                    <h3 className="version_title">Актуальная версия</h3>
                    <a
                        href={currentLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rules_link"
                    >
                        Перейти к актуальной версии
                    </a>
                </div>

                {previousLinks.length > 0 && (
                    <div className="column_container">
                        <h3 className="version_title">Предыдущие версии</h3>
                        <ul className="rules_previous_list">
                            {previousLinks.map((link, idx) => (
                                <li key={idx}>
                                    <a
                                        href={link.href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="rules_link"
                                    >
                                        {link.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}


function Rules_Page_Requisites() {
    return (
        <div className='page_container'>
            <div className='left_align_column' id='requisites_container'>
                <h2 className='main_bold_text'>Реквизиты</h2>
                <p><strong>ФИО:</strong> Добрынин Тимофей Даниилович</p>
                <p><strong>ИНН:</strong> 663102805653</p>
                <p><strong>ОГРНИП:</strong> 325665800106076</p>
                <p><strong>Адрес:</strong> 624480, 66 - Свердловская область, СЕВЕРОУРАЛЬСК Г, ОКТЯБРЬСКАЯ УЛ, 31, 150</p>
                <p><strong>Email:</strong> <a href="mailto:studiuminfo@yandex.ru">studiuminfo@yandex.ru</a></p>
            </div>
        </div>
    );
}


function Rules_Page_Element(props){
    return(
        <div className="column_container">
            <div className='border_container'>
                <div className="column_container">
                    <Rules_Page_Main data={props.data}/>
                    <Rules_Page_Requisites />
                </div>
            </div>
        </div>
    );
}


function Rules_Page(){
    const [rulesData, setRulesData] = useState([]);

    const [loadError, setLoadError] = useState(false);
    
    const [loading, setLoading] = useState(true);

    const [displayedPOP, setDisplayedPOP] = useState(null);

    const getRulesData = async () => {
        const url = `/api/rules/get_all/`;

        try {
            const response = await axios.get(url);
            setRulesData(response.data);
        } catch (error) {
            const message = error.response?.data?.message || "Что-то пошло не так, попробуйте позже!";
            setLoadError(true);
            setDisplayedPOP(<Error_POP_Element message={message}/>);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
            getRulesData();
    
        }, []);

    return(
        <>  
            {loading && <Loading_Spinner />}
            {loadError && <PopUpComponent isVisible={loadError} displayed={displayedPOP} onClose={() => {setLoadError(false); window.history.back();}}/>}
            <Rules_Page_Element data={rulesData}/>
        </>
    );
}

export default Rules_Page;