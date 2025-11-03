import React from "react";


function Task_Element(props){

    let renderComponent = {
        posted: <div className='menu_element_additional' id='menu_element_author'>Удалить</div>,
        purchased: <div className='menu_element_additional' id='menu_element_author'>Имя автора</div>
    }[props.parent];

    return (
        <li className="menu_element">
            <div className='row_container' id='menu_element_container'>
                <a className='menu_element_link' href='/rt'>
                    <div className='menu_element_background_container'>
                    <div className='menu_element_logo_container'></div></div>
                </a>
                <div className='menu_element_main_container'>
                    <div className='main_text'>
                        <a id='menu_element_name_link' href='/rt'>Название работы</a>
                    </div>
                    <div className='menu_element_additional_container'>
                        <div id='grey_font'>Категория работы</div>
                        <div id='grey_font'>Тип работы</div>
                    </div>
                </div>
                <div className='column_container' id='gap_container'>
                    <div className='main_text'>2500</div>
                    <a className='menu_element_author_link' href='/a'>
                        <div className='menu_element_author' id='grey_font'>{renderComponent}</div>
                    </a>
                </div>
            </div>
        </li>
    );
}

export {Task_Element};