import React, {useState} from 'react';
import { Link } from 'react-router-dom';

import {Input_Section, Select_Section, Education_Select, City_Input, 
        Place_Study_Input, Faculty_Input, Direction_Input, LevelSelect} from '../../elements/main_elements';

import { Search_Function } from './Common_Components';

import { ReactComponent as course_work} from "../../media/svg/Курсовая работа.svg";
import { ReactComponent as semestr_work} from "../../media/svg/Семестровая.svg";
import { ReactComponent as research_work} from "../../media/svg/НИР.svg";
import { ReactComponent as laboratory_work} from "../../media/svg/Лабораторная работа.svg";
import { ReactComponent as project_work} from "../../media/svg/Проектная работа.svg";
import { ReactComponent as report_work} from "../../media/svg/Реферат.svg";
import { ReactComponent as presentation_work} from "../../media/svg/Доклад.svg";
import { ReactComponent as essay_work} from "../../media/svg/Эссе.svg";
import { ReactComponent as practice_report} from "../../media/svg/Отчет по практике.svg";
import { ReactComponent as practical_work} from "../../media/svg/Практическая работа.svg";
import { ReactComponent as task_solution} from "../../media/svg/Решение задач.svg";
import { ReactComponent as lections} from "../../media/svg//Лекция.svg";
import { ReactComponent as tutors} from "../../media/svg/Репетитор.svg";
import { ReactComponent as summary} from "../../media/svg/Конспект.svg";
import { ReactComponent as text_translate} from "../../media/svg/Перевод текста.svg";


function Right_Menu_Task_Section(props) {
    const [isShowUserEducation, setIsShowUserEducation] = useState(true);

    return (
        <div className="side_sticky_container">
            <div className='space_container'>
                <Select_Section fileName="sorting" value_name="sort" value ={props.data?.sorting} title="Упорядочить" onChange={props.handleChange} />
                <Input_Section required={false} placeholder="Название предмета" value_name="discipline" onChange={props.handleChange} />
                <Select_Section fileName="types" value_name="type" value ={props.data?.type} title="Тип задания" onChange={props.handleChange} />
                <Input_Section required={false} placeholder="Преподаватель" value_name="tutor" onChange={props.handleChange} />
                {isShowUserEducation && (
                    <>
                        <Education_Select reset={props.reset} setCheck={setIsShowUserEducation} onChange={props.educationSelect} />
                    </>
                )}
                <City_Input data={props.data} setData={props.handleChange} />
                <Place_Study_Input data={props.data} setData={props.handleChange} />
                <Faculty_Input data={props.data} setData={props.handleChange} />
                <Direction_Input data={props.data} setData={props.handleChange} />
                <LevelSelect data={props.data} setData={props.handleChange} />
                <button className='right_sort_button' onClick={props.onClick}>Показать</button>
            </div>
        </div>
    );
}

function Order_Task_Element(props) {
    const deadline = new Date(props.data.deadline);
    const now = new Date();
  
    const diffMs = deadline - now;
    let deadlineText = "";
  
    if (diffMs <= 0) {
      deadlineText = "Просрочено";
    } else {
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      deadlineText = `Осталось ${diffDays} дн.`;
    }
  
    return (
      <li className="menu_element">
        <div className="menu_element_container">
          <Link to={`/order/${props.data.id}`} className="menu_element_link">
            <Icon_Selecter type={props.data.type} />
          </Link>
          <div className="menu_element_wrapper_container">
            <div className="menu_element_main_container">
              <div className="search_page_name_object">
                <Link id="menu_element_name_link" to={`/order/${props.data.id}`}>
                  {props.data.name}
                </Link>
              </div>
              <div className="left_align_colummn_container">
                <div className="menu_element_additional_container">
                  <div className="search_page_short_info_object">{props.data.type}</div>
                  <div className="search_page_short_info_object">{props.data.discipline}</div>
                </div>
                <div className="search_page_short_info_object">
                  {deadlineText}
                </div>
              </div>
            </div>
            <div className="menu_element_side_container">
              <div className="main_text">{props.data.price}₽</div>
              <Link className="menu_element_author_link" to={`/user/${props.data.owner}`}>
                <div className="menu_element_author" id="grey_font">
                  {props.data.author || `Пользователь ${props.data.owner}`}
                </div>
              </Link>
            </div>
          </div>
        </div>
      </li>
    );
  }
  

function Icon_Selecter(props) {
    const iconValues = {
        "Доклад": ['#807bf7', presentation_work],
        "Конспект": ['#f78e70', summary],
        "Курсовая работа": ['#ffaf64', course_work],
        "Лабораторная работа": ['#007f00', laboratory_work],
        "Лекция": ['#5dca0c', lections],
        "НИР": ['#ff5235', research_work],
        "Научная работа": ['#ff5235', research_work],
        "Научно исследовательская работа": ['#ff5235', research_work],
        "Отчет": ['#19d7d7', practice_report],
        "Перевод текста": ['#3272ff', text_translate],
        "Практическая работа": ['#ff722f', practical_work],
        "Проектная работа": ['#970e0b', project_work],
        "Репетитор": ['#024905', tutors],
        "Реферат": ['#ca29ff', report_work],
        "Решение задач": ['#c004c0', task_solution],
        "Семестровая": ['#ff8104', semestr_work],
        "Семестровая работа": ['#ff8104', semestr_work],
        "Эссе": ["#030382", essay_work]
    };

    const iconData = iconValues[props.type] || iconValues[Object.keys(iconValues).find(key => 
        key.toLowerCase() === props.type.toLowerCase()
    )];

    if (!iconData) {
        return null;
    }

    const IconComponent = iconData[1];

    return (
        <div className='menu_element_background_container'>
            <IconComponent className="menu_element_icon" fill={iconData[0]}/>
        </div>
    );
}


function Ready_Tasks_Search() {

    return (
        <Search_Function searchURL="/api/ot/all/" addData={{ isTaskSearch:true, searchText:"работ для выполения" }} 
                        searchElement={Order_Task_Element} rightSection={Right_Menu_Task_Section}/>
    );
}
  
  export default Ready_Tasks_Search;