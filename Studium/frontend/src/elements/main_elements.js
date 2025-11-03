import axios from 'axios';
import React, {useEffect, useState, useContext, useRef} from 'react';
import {createPortal} from 'react-dom'
import { Link } from 'react-router-dom';

import { ReactComponent as QuestionIcon } from "../media/svg/question-mark.svg";

import AuthContext from '../context/AuthContext';

import Rejected_Icon from '../media/png/Rejecter_Icon.png'
import Loading_Icon from '../media/png/Loading_Icon.png'

function Navigation_Item(props){
    return(
        <li className='navigation_item'>
            <Link to={props.link} className={props.class || 'navigation_link'} id={props.id}>{props.item_name}</Link>
        </li>
    );
}

function Select_Navigate() {
    const [open, setOpen] = useState(false);
  
    const options = [
        { name: "Разместить заказ", link: "/create_order" },
        { name: "Готовое задание", link: "/create_ready" },
    ];
  
    const toggleOpen = () => setOpen(!open);
  
    const handleSelect = (option) => {
      setOpen(false);
    };
  
    // Закрытие селекта при клике вне его
    const ref = useRef();
    useEffect(() => {
      const handleClickOutside = (event) => {
        if (ref.current && !ref.current.contains(event.target)) {
          setOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);
  
    return (
      <div className="navigation_item" ref={ref}>
        <div className="navigation_link" onClick={toggleOpen}>
          {"Разместить задание"}
        </div>
        {open && (
          <ul className="custom-select-options">
            {options.map((option, index) => (
              <li key={index} className="custom-select-option">
                <Link to={option.link} onClick={() => handleSelect(option)}>
                  {option.name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }


function Input_Section (props){
    return (
        <div className={'section_container ' + (props.className || '')} id={props.id || 'main_section_container'}>
            <input className="section_input" name={props.value_name || ''} value={props.value} type={props.type} onChange={props.onChange} placeholder={props.placeholder || ''} required={props.required}/>
        </div>
    );
}

function Select_Section(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const optionsMap = {
        withdraw: jsons["withdraw_bank_data.json"] || [],
        categories: jsons["categories.json"] || [],
        types: jsons["types.json"] || [],
        sorting: jsons["sorting.json"] || [],
    };

    const options = optionsMap[props.fileName] || [];
    const hasData = options.length > 0;
    
    // Проверяем, есть ли переданное value в списке доступных опций
    const isValidValue = props.value && options.some(option => option.name === props.value);
    const [selected, setSelected] = useState(isValidValue ? props.value : "");
    const [open, setOpen] = useState(false);
    const selectRef = useRef(null);

    // Обновляем selected, если props.value изменился и он допустим
    useEffect(() => {
        const isValid = props.value && options.some(option => option.name === props.value);
        if (isValid && props.value !== selected) {
            setSelected(props.value);
        } else if (!isValid && selected !== "") {
            setSelected("");
        }
    }, [props.value, options]);

    // Закрытие при клике вне
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (selectRef.current && !selectRef.current.contains(event.target)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const handleSelect = (value) => {
        setSelected(value);
        setOpen(false);

        if (props.onChange) {
            props.onChange({
                target: { name: props.value_name || "", value },
            });
        }
    };

    return (
        <div 
            className={"section_container " + (props.className || "")} 
            id={props.id || 'main_section_container'}
            ref={selectRef}
        >
            <div
                className="custom_select__selected"
                onClick={() => hasData && setOpen((prev) => !prev)}
                style={{ color: selected !== "" ? "#000" : "" }}
            >
                {selected || (hasData ? props.title : "Нет данных")}
            </div>

            {open && hasData && (
                <div className="custom_select__options">
                    {options.map((option) => (
                        <div
                            key={option.name}
                            className="custom_select__option"
                            onClick={() => handleSelect(option.name)}
                        >
                            {option.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function City_Input(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const places_study = jsons['place_study.json'] || {};

    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [prevCity, setPrevCity] = useState(props.data.city);

    const cityInstitutions = Object.keys(places_study);

    useEffect(() => {
        if (props.data.city && prevCity !== props.data.city) {
            const newSuggestions = cityInstitutions.filter(cityName =>
                cityName.toLowerCase().includes(props.data.city.toLowerCase()));

            setSuggestions(newSuggestions);
            setShowSuggestions(newSuggestions.length > 0);
            setPrevCity(props.data.city); 
        }
        }, [props.data.city, places_study]);

    return (
        <Suggestion_Input
            id={props.id}
            value={props.data.city}
            onChange={(e) => {props.setData({ target: { name: 'city', value: e.target.value } })}}
            placeholder="Город"
            targetName ='city'
            setData={props.setData}
            suggestions={suggestions}
            showSuggestions = {showSuggestions}
            setShowSuggestions = {setShowSuggestions}
        />
    );
}

function Place_Study_Input(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const places_study = jsons['place_study.json'] || {};

    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [prevUniversity, setPrevUniversity] = useState(props.data.university);

    const Institutions = props.data.city && places_study[props.data.city] 
        ? Object.keys(places_study[props.data.city]) 
        : [];

    useEffect(() => {
        if (props.data.city) {
            if (props.data.university && prevUniversity != props.data.university){
                const newSuggestions = Institutions.filter(instName =>
                    instName.toLowerCase().includes(props.data.university.toLowerCase()));

                setSuggestions(newSuggestions);
                setShowSuggestions(newSuggestions.length > 0); 
                setPrevUniversity(props.data.university);
            }
        } else {
            setSuggestions([]);
            setShowSuggestions(false);
        }
    }, [props.data.university, places_study]);

    return (
        <Suggestion_Input   
            id={props.id}
            value={props.data.university}
            onChange={(e) => {props.setData({ target: { name: 'university', value: e.target.value }})}}
            placeholder="Место учебы"
            disabled={!props.data.city || !places_study[props.data.city]}
            targetName ='university'
            setData={props.setData}
            suggestions={suggestions}
            showSuggestions = {showSuggestions}
            setShowSuggestions = {setShowSuggestions}
        />
    );
}

function Faculty_Input(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const places_study = jsons['place_study.json'] || {};
    
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [prevFaculty, setPrevFaculty] = useState(props.data.faculty);

    const Faculties = Object.keys(places_study?.[props.data.city]?.[props.data.university] || {});
    useEffect(() => {
        if (props.data.university) {
            if (props.data.faculty && prevFaculty !== props.data.faculty) {

                const newSuggestions = Faculties.filter(faclName => 
                    faclName.toLowerCase().includes(props.data.faculty.toLowerCase()));

                setSuggestions(newSuggestions);
                setShowSuggestions(newSuggestions.length > 0);
                setPrevFaculty(props.data.faculty);
            }
        } else {
            setSuggestions([]);
            setShowSuggestions(false);
        }
    }, [props.data.faculty, places_study]);

    return (
        <Suggestion_Input
            id={props.id}
            value={props.data.faculty}
            onChange={(e) => props.setData({ target: { name: 'faculty', value: e.target.value } })}
            placeholder="Факультет"
            disabled={!props.data.university || !Faculties}
            targetName="faculty"
            setData={props.setData}
            suggestions={suggestions}
            showSuggestions={showSuggestions}
            setShowSuggestions={setShowSuggestions}
        />
    );
}

function Direction_Input(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const places_study = jsons['place_study.json'] || {};

    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [prevDirection, setPrevDirection] = useState(props.data.direction);

    const universityData = places_study[props.data.city]?.[props.data.university]?.[props.data.faculty];
    const Directions = universityData?.[props.data.level] || [];

    useEffect(() => {
        if (props.data.level) {
            if (props.data.direction && prevDirection !== props.data.direction) {
                const newSuggestions = Directions.filter(directName => 
                    directName.toLowerCase().includes(props.data.direction.toLowerCase()));
                    
                setSuggestions(newSuggestions);
                setShowSuggestions(newSuggestions.length > 0);
                setPrevDirection(props.data.direction);
            }
        } else {
            setSuggestions([]);
            setShowSuggestions(false);
        }
    }, [props.data.direction, places_study]);

    return (
        <Suggestion_Input
            id={props.id}
            value={props.data.direction}
            onChange={(e) => props.setData({ target: { name: 'direction', value: e.target.value } })}
            placeholder="Направление"
            disabled={!props.data.level || !universityData?.[props.data.level]}
            targetName="direction"
            setData={props.setData}
            suggestions={suggestions}
            showSuggestions={showSuggestions}
            setShowSuggestions={setShowSuggestions}
        />
    );
}

function LevelSelect(props) {
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const places_study = jsons['place_study.json'] || {};

    const [levels, setLevels] = useState([]);

    useEffect(() => {
        const universityData = places_study[props.data.city]?.[props.data.university];
        
        if (props.data.faculty && universityData?.[props.data.faculty]) {
            const newLevels = Object.keys(universityData[props.data.faculty]);
            setLevels(newLevels);
        } else {
            setLevels([]);
        }
    }, [props.data.city, props.data.university, props.data.faculty, places_study]);

    useEffect(() => {
        if (!props.data.level && levels.length > 0) {
            props.setData({ target: { name: 'level', value: levels[0] } });
        }
    }, [props.data.level, levels]);

    return (
        <div className="section_container" id={props.id || 'main_section_container'}>
            <select
                value={props.data.level || ""}
                onChange={(e) => props.setData({ target: { name: 'level', value: e.target.value } })}
                disabled={!props.data.faculty || levels.length === 0}>
                <option value="" disabled>Уровень образования</option>
                {levels.map((option) => (
                    <option key={option} value={option}>
                        {option}
                    </option>
                ))}
            </select>
        </div>
    );
}
function Suggestion_Input(props){
    const [isFocused, setIsFocused] = useState(false);

    const handleFocus = () => {
        setIsFocused(true);
    };

    const handleBlur = () => {
        props.setShowSuggestions(false);
    };

    return(
        <div className='section_container' id={props.id || 'main_section_container'}>
            <input 
                className="section_input"
                type="text" 
                name="name" 
                value={props.value} 
                onChange={props.onChange} 
                onFocus={handleFocus}
                onBlur={handleBlur} 
                placeholder={props.placeholder} 
                disabled={props.disabled} 
                />
                {isFocused && props.showSuggestions && 
                (<HintElement 
                    suggestions={props.suggestions} 
                    targetName={props.targetName} 
                    setData={props.setData}
                    setShowSuggestions={props.setShowSuggestions}/>)
                }
        </div>
    );
}

function HintElement(props){

    const handleSuggestionClick = (suggested) => { 
        props.setData({ target: { name: props.targetName, value: suggested}}); 
        props.setShowSuggestions(false);
    };

    return(
        <ul className="suggestions_list">
            {props.suggestions.map(suggested=> (
                <li key={suggested} onMouseDown={() => handleSuggestionClick(suggested)}>
                    {suggested}
                </li>
            ))}
        </ul>
    );
}

function Education_Select(props) {
    const { user } = useContext(AuthContext);

    const [options, setOptions] = useState([]);
    const [selectedValue, setSelectedValue] = useState("");
    const [open, setOpen] = useState(false);
    const selectRef = useRef(null);

    // Закрытие при клике вне
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (selectRef.current && !selectRef.current.contains(event.target)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    // Формируем список образований
    useEffect(() => {
        if (user?.educations) {
            const formattedEducations = user.educations.map((education, index) => ({
                id: index,
                name: `${education.university} - ${education.level} - ${education.direction}`,
                educationData: education // Сохраняем все данные образования
            }));
            setOptions(formattedEducations);
        } else {
            setOptions([]);
        }
    }, [user]);

    // Сброс значения
    useEffect(() => {
        if (props.reset) {
            setSelectedValue("");
        }
    }, [props.reset]);

    // Автовыбор по props.education
    useEffect(() => {
        if (props.education) {
            const matchingEducation = user?.educations?.findIndex(
                (education) =>
                    education.university === props.education.university &&
                    education.level === props.education.level &&
                    education.direction === props.education.direction
            );

            if (matchingEducation !== -1) {
                setSelectedValue(matchingEducation);
                if (props.onChange) {
                    props.onChange({
                        target: { name: "education", value: user.educations[matchingEducation] },
                    });
                }
            }
        }
    }, [props.education, user?.educations]);

    const handleSelect = (id) => {
        setSelectedValue(id);
        setOpen(false);

        if (props.onChange) {
            // Возвращаем полный объект образования вместо just id
            props.onChange({
                target: { 
                    name: "education", 
                    value: id
                },
            });
        }
    };

    const selectedOption = options.find((opt) => opt.id === selectedValue);

    return (
        <div 
            className={`section_container${props.className ? " " + props.className : ""}`} 
            id="main_section_container"
            ref={selectRef}
        >
            <div 
                className="custom_select__selected" 
                onClick={() => options.length && setOpen((prev) => !prev)}
                style={{ color: selectedValue !== "" ? "#000" : "" }}
            >
                {selectedOption?.name || (options.length ? "Ваше образование" : "Нет данных")}
            </div>

            {open && options.length > 0 && (
                <div className="custom_select__options">
                    {options.map((option) => (
                        <div
                            key={option.id}
                            className="custom_select__option"
                            onClick={() => handleSelect(option.id)}
                        >
                            {option.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function Text_Section(props){
    return(
        <div className="row_container">
            <textarea 
                className='text_section' 
                placeholder={props.placeholder}
                name={props.name} 
                value={props.value}
                onChange={props.onChange}/>
        </div>
    );
}

function POP_Element(props){
    return(
        <div className='column_container' id='gap_container'>
            <img className='Pop_Icon' src={props.image_src}/>
            <div className='page_container'>
                <span className='main_text'>{props.main_text}</span>
            </div>
            <div className='page_container'>
                <span id='grey_font'>{props.sub_text}</span>
            </div>
        </div>
    );
}

function Error_POP_Element(props){
    return(
        <div className='status_pop_up_container'>
            <img className='Error_Pop_Icon' src={Rejected_Icon}/>
            <span className='main_text'>{props.message || "Что-то пошло не так, попробуйте позже!"}</span>
        </div>
    );
}

function Loading_POP_Element(props){
    return(
        <div className='status_pop_up_container'>
            <img className='Error_Pop_Icon' src={Loading_Icon}/>
            <span className='main_text'>{props.main_text || "Загрузка..."}</span>
            {props.sub_text && (
                <span id='grey_font'>{props.sub_text}</span>
            )}
        </div>
    );
}

function ShortPopUpComponent(props) {    
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
                            <div className='short_pop_up_container'>
                                <span className='main_text'>{props.text}</span>
                                <div className='reg_form'>
                                    <Link className='pop_up_button' id='confirm_pop_up_button' to={props.link} state={{data: {object: props.data.object, id:props.data.id}}}>Да</Link>
                                    <button className='pop_up_button' id='deciline_pop_up_button' onClick={props.onClose}>Нет</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function DeletePopUpComponent(props) {
    const { accessToken } = useContext(AuthContext);

    const [isLoading, setIsLoading] = useState(false);
    const [showError, setShowError] = useState(false);
    
    useEffect(() => {
        document.body.style.overflow = props.isVisible ? 'hidden' : 'unset';
        
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [props.isVisible]);

    const handleDelete = async () => {
        setIsLoading(true);
        try {
            await axios.put(
                `/api/rt/hide/${props.id}/`,
                {}, 
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );
            props.onClose();
            window.location.reload();
        } catch (error) {
            setShowError(true);
            setTimeout(() => setShowError(false), 3000);
        } finally {
            setIsLoading(false);
        }
    };    
    
    return (
        <>
            {createPortal(
                <div className='pop_up_element_shadow' onClick={props.onClose}>
                    <div className='pop_up_element' id='short_pop_up_element' onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            <div className='short_pop_up_container'>
                                <span className='main_text'>{props.text}</span>
                                <div className='reg_form'>
                                    <button 
                                        className='pop_up_button' 
                                        id='confirm_pop_up_button' 
                                        onClick={handleDelete}
                                        disabled={isLoading}
                                    >
                                        {isLoading ? 'Удаление...' : 'Да'}
                                    </button>
                                    <button 
                                        className='pop_up_button' 
                                        id='deciline_pop_up_button' 
                                        onClick={props.onClose}
                                        disabled={isLoading}
                                    >
                                        Нет
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

function PopUpComponent(props) {
    
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
                    <div className='pop_up_element' id={props.id} onClick={(e) => e.stopPropagation()}>
                        <button className="popup_close_button" onClick={props.onClose}>&times;</button>
                        <div className="pop_up_body">
                            {props.displayed}
                        </div>
                    </div>
                </div>, document.getElementById("portal")
            )}
        </>
    );
}

function Head_Searchbar(props){
    return (
        <div className='head_searchbar_wrapper'>
            <div className='row_container' id='head_searchbar'>
                <div className="search_form">
                    <div className='searchbar_input_wrapper'>
                        <input  className="search_input" id='head_searchbar_input' placeholder={props.placeholder} value={props.data?.name || ""}
                                name="name" onChange={props.onChange}></input>
                    </div>
                    <button className="search_button" id='head_searchbar_button' onClick={props.onClick}>Найти</button>
                </div>
            </div>
        </div>
    );
}

function Loading_Spinner(){
    return (
        
        <>
            {createPortal(
                <div className="loading-spinner">
                    <div className="loading-spinner-inner"></div>
                </div>,
                document.getElementById("portal")
            )}
        </>
    );
}

function Ready_Task_Info(props){
    return(
        <div className='task_value_container'>
            <h3 className='task_info'>
                <span className='task_info' id='grey_font'>{props.name}</span> 
                {props.value}
            </h3>
        </div>
    );
}

function Ready_Task_Link(props){
    return(
        <div className='task_value_container'>
            <h3 className='task_info'>
                <span className='task_info' id='grey_font'>{props.name}</span> 
                <Link to={props.link}>{props.value}</Link>
            </h3>
        </div>
    );
}

function Help_Button({ hint_name }) {
    const [hint, setHint] = useState(null);
    const [isPopupVisible, setPopupVisible] = useState(false);
    const [showError, setShowError] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const togglePopup = () => {
        setPopupVisible((prev) => !prev);
    };

    const getHint = async () => {
        try {
            const response = await axios.get(`/api/jsons/hints/${hint_name}`);
            setHint(response.data.jsons);
        } catch (error) {
            const message = error.response?.data?.message || "Не удалось получить подсказку";
            setErrorMessage(message);
            setShowError(true);
        }
    };

    useEffect(() => {
        if(isPopupVisible){
            getHint();
        }
    }, [isPopupVisible]);

    return (
        <>
            <button className="help_button" type="button" onClick={togglePopup}>
                <QuestionIcon id="help_button_svg" />
            </button>

            {isPopupVisible && hint && (
                <HelpPopUpComponent
                    isVisible={isPopupVisible}
                    hint={hint}
                    onClose={() => setPopupVisible(false)}
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

function HelpPopUpComponent({ isVisible, hint, onClose }) {
    useEffect(() => {
        if (isVisible) {
            document.body.style.overflow = "hidden";

            const handleEsc = (e) => {
                if (e.key === "Escape") onClose();
            };
            document.addEventListener("keydown", handleEsc);

            return () => {
                document.body.style.overflow = "unset";
                document.removeEventListener("keydown", handleEsc);
            };
        }
    }, [isVisible, onClose]);

    const portalElement = document.getElementById("portal");

    const hints = hint?.hint || {};
    const hintsExist = Object.keys(hints).length > 0;

    return createPortal(
        <div className="pop_up_element_shadow" onClick={onClose}>
            <div className="hints_popup_container">
                <button className="popup_close_button" onClick={onClose}>&times;</button>
                <div className="hints_popup_body" onClick={e => e.stopPropagation()}>
                    {hintsExist ? (
                        <div className="hints_scroll_area">
                            {Object.entries(hints).map(([key, item]) => (
                                <div key={key} className="hint_block">
                                    {item.label && <h3 className="hint_title">{item.label}</h3>}
                                    {item.text && <div className="hint_text">{item.text}</div>}
                                    {item.description && (
                                        <p className="hint_description">{item.description}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="no_hints_message">Подсказка не найдена</p>
                    )}
                </div>
            </div>
        </div>,
        portalElement
    );
}

function Right_Button_Section(props){
    return(
        <div className="side_sticky_container">
            <div className='column_container' id='sticky_container'>
                <button className={props.disabled ? 'right_button' : 'unactivate_button'} onClick={props.onClick} type={props.type} disabled={!props.disabled}>
                    {props.name}</button>
            </div>
        </div>
    );
}

function Right_Button_Mobile_Section(props){
    return(
        <div className='page_container'>
            <div className='mobile_button_section'>
                <Right_Button_Section name={props.name} disabled={props.disabled} onClick={props.onClick} type={props.type}/>
            </div>
        </div>
    );
}

function Right_Button_Desktop_Section(props){
    return(
        <div className='desktop_button_section'>
            <Right_Button_Section name={props.name} disabled={props.disabled} onClick={props.onClick} type={props.type}/>
        </div>
    );
}

function BetweenBlocksElement(props) {
    return (
        <div style={{ height: props.height }}></div>
    );
}

function Row_Input_Section(props){
    return(
      <div className='row_space_between_container'>
        <h3 className="main_text">{props.name}</h3>
        <div className="form_control_wide">
          <Input_Section placeholder={props.placeholder} value={props.value} value_name={props.value_name} type={props.type} onChange={props.onChange}/>
        </div>
      </div>
    );
  }

export {
    Navigation_Item,
    Select_Section,
    Input_Section,
    Text_Section,
    Head_Searchbar,
    POP_Element,
    PopUpComponent,
    ShortPopUpComponent,
    Error_POP_Element,
    Loading_POP_Element,
    Education_Select,
    Suggestion_Input,
    Ready_Task_Info,
    Ready_Task_Link,
    City_Input,
    Place_Study_Input,
    Faculty_Input,
    Direction_Input,
    LevelSelect,
    Loading_Spinner,
    Help_Button,
    HelpPopUpComponent,
    DeletePopUpComponent,
    Right_Button_Mobile_Section,
    Right_Button_Desktop_Section,
    BetweenBlocksElement,
    Row_Input_Section,
    Select_Navigate,
  };