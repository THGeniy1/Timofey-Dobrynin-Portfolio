import React, {useContext} from 'react';
import { useNavigate } from 'react-router-dom';

import how_work_img_1 from "../../media/png/How work - 1.png";
import how_work_img_2 from "../../media/png/How work - 2.png";
import how_work_img_3 from "../../media/png/How work - 3.png";

import course_work from "../../media/png/Курсовая работа.png";
import semestr_work from "../../media/png/Семестровая.png";
import research_work from "../../media/png/НИР.png";
import laboratory_work from "../../media/png/Лабораторная работа.png";
import project_work from "../../media/png/Проектная работа.png";
import report_work from "../../media/png/Реферат.png";
import presentation_work from "../../media/png/Доклад.png";
import essay_work from "../../media/png/Эссе.png";
import practice_report from "../../media/png/Отчет по практике.png";
import practical_work from "../../media/png/Практическая работа.png";
import task_solution from "../../media/png/Решение задач.png";
import lections from "../../media/png/Лекция.png";
import summary from "../../media/png/Конспект.png";
import text_translate from "../../media/png/Перевод текста.png";
import banner_main from "../../media/png/Баннер.png";

import { Link } from 'react-router-dom';

import AuthContext from '../../context/AuthContext';

import {BetweenBlocksElement} from '../../elements/main_elements'

function Main_Searchbar(props) {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = React.useState('');

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/ready_tasks?name=${encodeURIComponent(searchQuery.trim())}`);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        navigate(`/ready_tasks?name=${encodeURIComponent(suggestion)}`);
    };

    return (
        <>
            <div id="main_page_searchbar">
                <form className="search_form" onSubmit={handleSearch}>
                    <div className="searchbar_input_wrapper">
                        <input
                            id="main_searchbar_input"
                            type="text"
                            name="q"
                            placeholder={props.placeholder || "Название работы"}
                            autoComplete="off"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <button id="main_searchbar_button" type="submit">Найти</button>
                </form>
            </div>
            {/* <span id="searchbar_sub_title">
                Например, <a 
                    id="searchbar_sub_title_link" 
                    onClick={() => handleSuggestionClick('курсовая работа по сопромату')}
                    style={{ cursor: 'pointer' }}
                >
                    курсовая работа по сопромату
                </a>
            </span> */}
        </>
    );
}

function FirstBlockElement(){
    const [isBanner, setIsBanner] = React.useState(window.innerWidth <= 1024);

    React.useEffect(() => {
        const handleResize = () => {
            setIsBanner(window.innerWidth <= 1024);
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className='row_container main_page_hero_container'>
            <div id='main_page_title_container'>
                <h1 id='main_page_title'>Облегчим ваше обучение</h1>
                <h2 id='main_page_sub_title'>Поможем найти выполненную работу по учебе</h2>
                <div className="main_page_searchbar_banner_wrapper">
                    <Main_Searchbar placeholder='Название работы'/>
                    {isBanner && (
                        <img
                            src={banner_main}
                            alt="Studium Banner"
                            className="main_page_banner"
                        />
                    )}
                </div>
            </div>
            {!isBanner && <img className='main_page_image' alt="" />}
        </div>
    );
}

function WorkType(props) {
    const hasParam = props.param_data && String(props.param_data).trim().length > 0;
    const queryParam = hasParam ? encodeURIComponent(props.param_data) : '';
    const to = hasParam ? `/ready_tasks?work_type=${queryParam}` : `/ready_tasks`;

    return (
        <Link to={to} className='row_space_between_container' id='work_type'>
            <img className='work_type_logo' src={props.image_src} alt={props.work_name} />
            <span className='small_bold_text' id='work_type_title'>{props.work_name}</span>
        </Link>
    );
}

function SecondBlockElement(){
    const { cachedFiles } = useContext(AuthContext);
    const jsons = cachedFiles?.jsons || {};

    const types = jsons['types.json'] || {};

    return (
        <div className='column_container'>
            <div className='column_container'>
                <h2 className='page_title_text'>У нас находят</h2>
            </div>
            <div className='grid_container' id='work_types_container'>
                <WorkType work_name='Курсовые' image_src={course_work} param_data={types[0]?.name}/>
                <WorkType work_name='Семестровые' image_src={semestr_work} param_data={types[1]?.name}/>
                <WorkType work_name='НИР' image_src={research_work} param_data={types[2]?.name}/>
                <WorkType work_name='Лабораторные' image_src={laboratory_work} param_data={types[3]?.name}/>
                <WorkType work_name='Проектные' image_src={project_work} param_data={types[4]?.name}/>
                <WorkType work_name='Рефераты' image_src={report_work} param_data={types[5]?.name}/>
                <WorkType work_name='Доклады' image_src={presentation_work} param_data={types[6]?.name}/>
                <WorkType work_name='Эссе' image_src={essay_work} param_data={types[7]?.name}/>
                <WorkType work_name='Отчеты' image_src={practice_report} param_data={types[8]?.name}/>
                <WorkType work_name='Практические' image_src={practical_work} param_data={types[9]?.name}/>
                <WorkType work_name='Решения задач' image_src={task_solution} param_data={types[10]?.name}/>
                <WorkType work_name='Лекции' image_src={lections} param_data={types[11]?.name}/>
                <WorkType work_name='Конспекты' image_src={summary} param_data={types[12]?.name}/>
                <WorkType work_name='Переводы' image_src={text_translate} param_data={types[13]?.name}/>
            </div>
        </div>
    );
}


function ThirdBlockElement(){
    return(
        <div className='column_container'>
            <h2 className='page_title_text'>Как работает Studium?</h2>
            <div className='wrap_container'>
                <HowWorkElement src_img = 'first_img' image_src={how_work_img_1} margin_right={'45px'}/>
                <HowWorkElement src_img = 'first_img' image_src={how_work_img_2} margin_right={'45px'}/>
                <HowWorkElement src_img = 'first_img' image_src={how_work_img_3} margin_right={'0px'}/>
            </div>
        </div>
    );
}

function HowWorkElement(props){
    return(
        <div className='how_work_element' style={{ marginRight: props.margin_right }}>
            <img className='how_work_image' src={props.image_src}/>
        </div>
    );
}

function FourthBlockElement(){
    return(
        <div className='column_container'>
            <h2 className='page_title_text'>О нас</h2>
            <div id='about_us_container'>
                <p className='main_text'><span className="studium-brand">Studium</span> - это молодой проект, созданый студентами для студентов. Здесь вы сможете найти готовые работы по учебе из различных ВУЗов и ССУЗов, а размещают эти работы студенты, которые их выполняли!</p>
                <p className='main_text'>Мы стремимся создать удобное пространство для обмена знаниями и опытом между студентами, чтобы помочь им успешно справиться с учебными заданиями. Наша цель - поддерживать образовательное сообщество, способствовать обмену знаниями и помогать студентам достигать успеха в своей учебе.</p>
                <p className='main_text'>Наш проект постоянно развивается и растет, добавляя новые возможности и инструменты, чтобы улучшить опыт обучения для всех участников. Мы стремимся к тому, чтобы <span className="studium-brand">Studium</span> стал неотъемлемой частью мира студентов.</p>
            </div>
        </div>
    );
}


function MainPage(){
    return(
        <div className='column_container'>
            <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
            <FirstBlockElement/>
            <BetweenBlocksElement height='clamp(40px, 10vw, 100px)'/>
            <SecondBlockElement/>
            <BetweenBlocksElement height='clamp(60px, 12vw, 125px)'/>
            <ThirdBlockElement/>
            <BetweenBlocksElement height='clamp(60px, 12vw, 125px)'/>
            <FourthBlockElement/>
            <BetweenBlocksElement height='clamp(30px, 6vw, 60px)'/>
        </div>
    );
}

export default MainPage;