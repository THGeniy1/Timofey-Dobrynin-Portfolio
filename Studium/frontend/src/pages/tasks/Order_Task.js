import axios from 'axios';
import React, {useState, useEffect, useContext, useRef} from 'react';

import AuthContext from '../../context/AuthContext';

import { useParams, Link } from 'react-router-dom';

import { Loading_Spinner, Help_Button, PopUpComponent, Ready_Task_Info, 
    Error_POP_Element, BetweenBlocksElement, ShortPopUpComponent } from '../../elements/main_elements';
import Choose_Payment_Method_Controller from '../../elements/payment/payment_method';

import {ReactComponent as StarIcon} from '../../media/svg/star.svg'

import PDFIcon from '../../media/png/upload_files/pdf.png'
import DOCIcon from '../../media/png/upload_files/doc.png'
import PPTIcon from '../../media/png/upload_files/ppt.png'
import XLSIcon from '../../media/png/upload_files/xls.png'
import ZIPIcon from '../../media/png/upload_files/zip.png'

import LOCKIcon from '../../media/png/upload_files/grey_lock.png'

import defaultAvatar from '../../media/png/User_avatar.png';

function Ready_Task_Main_Info(props){
    return(
        <div className="page_container">
            <div className='column_container' id='task_info_container'>
                <span id='grey_font'>№ работы:{props.data.id}</span>
                <div className='row_container'>
                    <h2 className="page_title_text">{props.data.name}</h2>
                    <Help_Button hint_name='purchase_ready_task_hint.json'/>
                </div>
                <div className='page_container'>
                    <Ready_Task_Info name="Город: " value={props.data.city}/>
                    <Ready_Task_Info name="Место учебы: " value={props.data.university}/>
                    <Ready_Task_Info name="Факультет: " value={props.data.faculty}/>
                    <Ready_Task_Info name="Направление: " value={props.data.direction}/>
                </div>
                <div className='page_container'>
                    <Ready_Task_Info name="Предмет: " value={props.data.discipline}/>
                    <Ready_Task_Info name="Преподаватель: " value={props.data.tutor}/>
                    <Ready_Task_Info name="Тип задания: " value={props.data.type}/>
                    <Ready_Task_Info name="Оценка: " value={props.data.score}/>
                </div>
            </div>
        </div>
    );
}

function Ready_Task_Media(props){
    const [fileLinks, setFileLinks] = useState([]);
    useEffect(() => {
        if (props.data.files) {
            setFileLinks(props.data.files);
        }
    }, [props.data.files]);

    return(
      <div className='page_container'>
        <h2 className="medium_bold_text">Фотографии и файлы</h2>
        <div className="row_container">
            <div className='grid_container' id='upload_grid'>
                {fileLinks.map((file) => (
                    <FileComponent value={file} />
                ))}
            </div>
        </div>
      </div>
    );
}

const getIconByFormat = (format) => {
  switch (format) {
    case 'pdf':
      return PDFIcon;
    
    // Word
    case 'doc':
    case 'docm':
    case 'docx':
    case 'rtf':
      return DOCIcon;
    
    // Excel
    case 'xls':
    case 'xlsm':
    case 'xlsx':
    case 'csv':
      return XLSIcon;
    
    // PowerPoint
    case 'ppt':
    case 'pptm':
    case 'pptx':
      return PPTIcon;
    
    // Архивы
    case 'zip':
    case 'rar':
    case '7z':
      return ZIPIcon;
    
    default:
      return null;
  }
};

const getFileIcon = (file, fileName) => {
  const format = fileName ? fileName.split('.').pop() : null;
  const isFileLink = typeof file === 'string' && file.startsWith('http');
  const isImageFile = !isFileLink && file && file.type.startsWith('image/');
  
  if (isImageFile) {
    return URL.createObjectURL(file);
  }

  if (isFileLink) {
    const icon = getIconByFormat(format);
    if(icon){
      return icon
    }
    return file;
  }

  return getIconByFormat(format);
};

function formatFileSize(bytes) {
    if (!bytes && bytes !== 0) return '';
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = bytes / Math.pow(1024, i);
    return `${size.toFixed(1)} ${sizes[i]}`;
}

function FileComponent(props) {
    const value = props.value;
    const fileName = value.file?.name || value.name;
    const file = value.file || value.url;

    const icon = value.is_locked ? LOCKIcon : getFileIcon(file, fileName);

    return (
        <a href={value.url} download={value.url}>
            <div className='upload_item'>
                <div className='column_container'>
                    <img className='upload_image' src={icon} />
                    <div className='column_container' id='image_container'>
                        <p className='upload_text'>{value.name}</p>
                        <p className='upload_text'>{formatFileSize(value.size)}</p>
                    </div>
                </div>
            </div>
        </a>
    );
}

function Ready_Task_Description(props){
    return(
      <div className='page_container'>
        <h2 className="medium_bold_text">Описание</h2>
        <div className='ready_task_description'>{props.data.description}</div>
      </div>
    );
}

function Ready_Task_Feedbacks(props){
    const [feedbackData, setFeedbackData] = useState([]);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const observer = useRef();

    const getUserFeedbacks = async () => {
        if (loading || !hasMore || !props.data?.id) return;
      
        setLoading(true);
        const url = `/api/rate/rt/${props.data.id}?page=${page}`;
      
        try {
          const response = await axios.get(url);
          setFeedbackData((prev) => [...prev, ...response.data.feedback]);
          setHasMore(response.data.has_next);
          setPage((prev) => prev + 1);
        } finally {
          setLoading(false);
        }
    };
      
    useEffect(() => {
        setFeedbackData([]);
        setPage(1);
        setHasMore(true);
        getUserFeedbacks();
    }, [props.data.id]);


    useEffect(() => {
        if (!hasMore || loading) return;

        const observerCallback = (entries) => {
        if (entries[0].isIntersecting) {
            getUserFeedbacks();
        }
        };

        observer.current = new IntersectionObserver(observerCallback, { threshold: 1.0 });

        const target = document.querySelector("#load-more-trigger");
        if (target) {
        observer.current.observe(target);
        }

        return () => {
        if (observer.current && target) {
            observer.current.unobserve(target);
        }
        };
    }, [hasMore, loading]);

    return (
        <div className="page_container">
            <h2 className="medium_bold_text">Отзывы покупателей</h2>
                <ul className="reviews_container">
                    {feedbackData.length > 0 ? (
                        feedbackData.map((review) => <Ready_Task_Review_Object review={review} key={review.id} />)
                    ) : (
                    <p>{loading ? "Загрузка..." : "Нет отзывов"}</p>
                    )}
                </ul>
            <div id="load-more-trigger" style={{ height: "1px" }}></div>
        </div>
    );
}

function StarRating({ rating }) {
  return (
    <div className="star_rate_container">
      {[...Array(5)].map((_, index) => {
        const starIndex = index + 1;
        return (
          <StarIcon
            key={starIndex}
            className="small_star"
            id={starIndex <= rating ? "star_filled" : ""}
          />
        );
      })}
    </div>
  );
}

function Ready_Task_Review_Object({ review }) {
  if (!review) return null;

  const dateCreate = new Date(review.created_at);
  const formattedDate = dateCreate.toLocaleDateString('ru-RU', {year: 'numeric', month: 'long', day: 'numeric',});

  return (
    <li className="column_container" id="around_border_container">
      <div className="review_header_container">
        <Link to={`/user/${review.user?.id}`}>
          {review.user?.name || `Пользователь № ${review.user?.id}`}
        </Link>
        <div className="review_main_container">
          <p id='light_grey_font'>{formattedDate}</p>
          <StarRating rating={review.rating} />
        </div>
      </div>
      <div className='column_container' id="review_comment_container">
        <span id={review.comment ? "" : "grey_font"}>{review.comment || "Комментария нет"}</span>
      </div>
    </li>
  );
}

function Left_Menu_Desktop_Task_Section(props){
    const avatar = props.data.avatar || defaultAvatar;

    const link_to = `/user/${props.data.owner_id}`

    return(
        <div className="side_sticky_container">
            <div className='column_container' id='sticky_container'>
                <Link to={link_to} className='user_search_photo'>
                    <img 
                        className='user_avatar'
                        id='user_search_avatar'
                        src={avatar} 
                        alt="User Avatar" 
                    />
                </Link>
                <Link to={link_to} className='main_text'>
                    {props.data.owner_name ? props.data.owner_name : 'Пользователь № ' + props.data.owner_id}
                </Link>
                <div id='grey_font'>Рейтинг пользователя: {props.data.owner_rating}</div>
            </div>
        </div>
    );
}

function Left_Menu_Mobile_Task_Section(props){
    const avatar = props.data.avatar || defaultAvatar;

    const link_to = `/user/${props.data.owner_id}`
    return(
        <div className='page_container'>
            <div className="left_section_mobile">
                <div className='ready_task_mobile_user_container'>
                    <Link to={link_to} className='user_profile_photo'>
                        <img 
                            className='user_avatar'
                            id='user_main_avatar'
                            src={avatar} 
                            alt="User Avatar" 
                        />
                    </Link>
                    <div className='menu_element_main_container'>
                        <Link to={link_to} className='main_text'>
                            {props.data.owner_name ? props.data.owner_name : 'Пользователь № ' + props.data.owner_id}
                        </Link>
                        <div id='grey_font'>Рейтинг пользователя: {props.data.owner_rating}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
function Right_Button_Desktop_Section({ data, taskId, onClick }) {
    if (!data) return null;

    return (
        <div className="desktop_button_section">
            {data.is_owner ? (
                <Right_Button_Correct_Section data={taskId} />
            ) : data.is_purchased ? (
                <Already_Buy_Section taskId={taskId}/>
            ) : (
                <Right_Button_Buy_Section 
                    price={data.price} 
                    taskId={taskId} 
                    onClick={onClick}
                />
            )}
        </div>
    );
}

function Right_Button_Mobile_Section({ data, taskId, onClick }) {
    if (!data) return null;

    return (
        <div className="page_container">
            <div className="mobile_button_section">
                {data.is_owner ? (
                    <Right_Button_Correct_Section data={taskId} />
                ) : data.is_purchased ? (
                    <Already_Buy_Section taskId={taskId}/>
                ) : (
                    <Right_Button_Buy_Mobile_Section 
                        price={data.price} 
                        taskId={taskId} 
                        onClick={onClick}
                    />
                )}
            </div>
        </div>
    );
}

function Right_Button_Buy_Section(props){
    return(
        <div className="side_sticky_container">
            <div className='column_container' id='sticky_container'>
                <h3 className="main_text">{props.price} ₽</h3>
                <Choose_Payment_Method_Controller taskId={props.taskId}/>
            </div>
        </div>
    );
}

function Right_Button_Correct_Section(props) {
    return (
        <div className="side_sticky_container">
            <div className='column_container' id='sticky_container'>
                <Link to="/create" state={{data: props.data}} className='right_button' id='correct_button'>Редактировать</Link>
            </div>
        </div>
    );
}

function Already_Buy_Section(props){
    const [activePopUp, setActivePopUp] = useState(null);

    const ratePopUpText = "Вы действительно хотите оценить работу?";
    const refundPopUpText = "Вы действительно хотите оформить возврат работы?";
    
    const togglePopUp = ({ popUpId = null } = {}) => {
        setActivePopUp(prev => (prev === popUpId ? null : popUpId));
    };

    return(
        <>
            {activePopUp === 'ratePop' && 
                <ShortPopUpComponent 
                    isVisible={true} 
                    text={ratePopUpText} 
                    link={`/rate_task`} 
                    data={{id: props.taskId}} 
                    onClose={() => togglePopUp()} 
                />
            }

            {activePopUp === 'refundPop' && 
                <ShortPopUpComponent 
                    isVisible={true} 
                    text={refundPopUpText} 
                    link={`/create_refund`} 
                    data={{id: props.taskId}} 
                    onClose={() => togglePopUp()} 
                />
            }
            <div className="side_sticky_container">
                <div className='column_container' id='sticky_container'>
                    <button className='right_button' id='feedback_button' onClick={() => togglePopUp({ popUpId: 'ratePop'})}>Оценить</button>
                    <button className='right_button' id='refund_button' onClick={() => togglePopUp({ popUpId: 'refundPop'})} >Возврат</button>
                </div>
            </div>
        </>
    );
}

function Right_Button_Buy_Mobile_Section(props){
    return(
        <div className="side_sticky_container">
            <div className='column_container' id='gap_container'>
                <h3 className="main_text">Цена: {props.price}₽</h3>
                <Choose_Payment_Method_Controller taskId={props.taskId}/>
            </div>
        </div>
    );
}

function Order_Task_Element(props){
    return(
        <div className="column_container">
            <div className='sides_container'>
                <div className="left_section_desktop">
                    <Left_Menu_Desktop_Task_Section data={props.data}/>
                </div>
                
                <div className='border_container'>
                    <div className='column_container'>
                        <Ready_Task_Main_Info data={props.data}/>
                        <Ready_Task_Description data={props.data}/>
                        <Ready_Task_Media data={props.data}/>

                        <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                        <Right_Button_Mobile_Section data={props.data} taskId={props.taskId} onClick={props.onClick}/>
                        <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                        <Left_Menu_Mobile_Task_Section data={props.data}/>
                        <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                        <Ready_Task_Feedbacks data={props.data} onClick={props.onClick}/>
                    </div>
                </div>
                <Right_Button_Desktop_Section data={props.data} taskId={props.taskId} onClick={props.onClick}/>
            </div>
        </div>
    );
}

function Order_Task() {
    const { accessToken } = useContext(AuthContext);

    const [taskData, setTaskData] = useState([]);

    const [loadError, setLoadError] = useState(false);
    
    const [loading, setLoading] = useState(true);

    const [displayedPOP, setDisplayedPOP] = useState(null);

    const { taskId: taskdString } = useParams();

    const taskId = parseInt(taskdString, 10);

    const getTaskData = async () => {
        try {
            setLoading(true);
            const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
            const response = await axios.get(`/api/rt/${encodeURIComponent(taskId)}`, { headers });
            setTaskData(response.data);
            setLoadError(false);
        } catch (error) {
            setLoadError(true);
            setDisplayedPOP(<Error_POP_Element />);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        getTaskData();
    
        const interval = setInterval(() => {
            getTaskData();
        }, 60 * 1000);
    
        return () => clearInterval(interval);
    }, [accessToken]); 
    
    return (
        <>  
            {loading && <Loading_Spinner />}
            {loadError && <PopUpComponent isVisible={loadError} displayed={displayedPOP} onClose={() => {setLoadError(false); window.history.back();}}/>}
            <Order_Task_Element data={taskData} taskId={taskId} />
        </>
    );
  }
  
  export default Order_Task;