import React, {useState} from 'react';
import { Link } from 'react-router-dom';

import { City_Input, Place_Study_Input, Faculty_Input, Direction_Input, LevelSelect, Education_Select} from '../../elements/main_elements';

import { Search_Function } from './Common_Components';

import defaultAvatar from '../../media/png/User_avatar.png';

function Right_Menu_User_Section(props){
    const [isShowUserEducation, setIsShowUserEducation] = useState(true);

    return(
        <div className="side_sticky_container">
            <div className='space_container'>
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

function User_Element(props){
    return(
        <li className="menu_element">
            <div className='menu_element_container'>
                <Link to={`/user/${props.data.id}`} className='menu_element_link'>
                    <div className='user_search_photo'>
                        <img className='user_avatar' id='user_main_avatar' src={props.data.avatar || defaultAvatar}></img>
                    </div>
                </Link>
                <div className='menu_element_wrapper_container'>
                    <div className='menu_element_main_container'>
                        <div className='search_page_name_object'>
                            <Link id='menu_element_name_link' to={`/user/${props.data.id}`}>{props.data.name || "Пользователь №" + props.data.id}</Link>
                        </div>
                        <div className='search_page_description_object'>{props.data.description || "Нет описания"}</div>
                    </div>
                    <div className='menu_element_rate_container'>
                        <div className='little_text'>Рейтинг: {props.data.average_rating}</div>
                        <div id='grey_font'>Отзывов: {props.data.reviews_count}</div>
                    </div>
                </div>
            </div>
        </li>
    );
}

function Users_Search() {

    return (
        <Search_Function searchURL="/api/up/gu/" addData={{ isTaskSearch:false, searchText:"исполнителей" }} searchElement={User_Element} rightSection={Right_Menu_User_Section}/>
    );
}
  
  export default Users_Search;