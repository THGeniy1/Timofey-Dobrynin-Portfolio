import axios from 'axios';
import React, {useState, useEffect, useRef, } from 'react';

import { Link } from 'react-router-dom';

import defaultAvatar from '../../media/png/User_avatar.png';

import { ShortPopUpComponent } from '../../elements/main_elements';

import {ReactComponent as StarIcon} from '../../media/svg/star.svg'

function User_Info(props){
    return(
      <div className='max_page_container'>
        <User_Data userData={props.userData} isUserPage={props.isUserPage} isUserAuth={props.isUserAuth}/>
        <User_Description description={props.userData.description}/>
        <User_Educations educations={props.userData.educations}/>
        <User_Reviews userData={props.userData}/>
      </div>
    );
}

function getReviewsText(count) {
  if (count === 1) {
      return `${count} отзыва`;
  } else {
      return `${count} отзывов`;
  }
}

function getReadyTaskText(count) {
  if (count % 10 === 1 && count % 100 !== 11) {
      return `${count} работа`;
  } else if (count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14)) {
      return `${count} работы`;
  } else {
      return `${count} работ`;
  }
}

function User_Data(props){

  const [activePopUp, setActivePopUp] = useState(false);

  const dateJoined = new Date(props.userData.date_joined);
  const formattedDate = dateJoined.toLocaleDateString('ru-RU', {year: 'numeric', month: 'long', day: 'numeric',});

  const conflictPopUpText = "Вы действительно хотите подать жалобу на этого пользователя?"

  const togglePopUp = () => {
      setActivePopUp(prev => !prev);
  };

  return(
    <div className='page_container'>
      <div className='row_top_align_container'>

        {!props.isUserPage && props.isUserAuth && 
        <button 
          className="bought_task_buttons" 
          id='conflict_button' 
          onClick={togglePopUp} 
          type="button">
        </button>}

        {activePopUp && 
        <ShortPopUpComponent isVisible={activePopUp} text={conflictPopUpText} link={`/create_report`} data={{id:props.userData.id, object:"user"}} onClose={togglePopUp}/>}
            

        <div className='user_profile_photo'>
          <img className='user_avatar' id='user_main_avatar' src={props.userData.avatar || defaultAvatar}></img>
        </div>
        <div className='user_profile_container'>
          <div className='left_align_column'>
            <h2 className="main_bold_text">{props.userData.name || "Пользователь №" + props.userData.id}</h2>
            <h3 id='grey_font'>{"На сайте с: " + formattedDate}</h3>
          </div>
          <div className='row_grid'>
            <div className='left_align_column'>
                <h2 className="little_bold_text">Оценка: {props.userData.average_rating}</h2>
                <h3 id='grey_font'>На основе {getReviewsText(props.userData.reviews_count)}</h3>
            </div>
            <div className='left_align_column'>
                <h2 className="little_bold_text">{getReadyTaskText(props.userData.posted_tasks_count)}</h2>
                <h3 id='grey_font'>разместил</h3>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function User_Description(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">О себе</h2>
      <div className='user_description'>{props.description || "Пользователь ничего не написал"}</div>
    </div>
  );
}
  
function User_Educations(props) {
  return (
    <div className='page_container'>
      <h2 className="page_title_text">Образование</h2>
      <ul className='educations_info_container'>
        {props.educations?.length > 0 ? (props.educations.map((education) => (
            <Education_Object education={education} />
          ))
        ) : ( <p>Нет данных об образовании.</p>)}
      </ul>
    </div>
  );
}
  
function Education_Object(props) {
  if (!props.education) {
    return null;
  }

  return (
    <li className='row_container' id='around_border_container'>
      {props.education.active && (
        <div className='indicator' />
      )}
      <div className='row_space_around_container'>
        <div className="left_align_column">
          <Education_Info name="Город:" value={props.education.city}/>
          <Education_Info name="Место учебы:" value={props.education.university}/>
          <Education_Info name="Факультет:" value={props.education.faculty}/>
        </div>
        <div className="left_align_column">
          <Education_Info name="Уровень образования:" value={props.education.level}/>
          <Education_Info name="Направление:" value={props.education.direction}/>
          <Active_Info name="Статус:" value={props.education.active}/>
        </div>
      </div>
    </li>
  );
}

function Education_Info(props){
  return(
    <div className="education_info_container">
      <span className="small_bold_text education_label">{props.name}</span>
      <div className='row_container' id='left_auto_margin_container'>
        <h4 id="education_info" className="education_value">{props.value}</h4>
      </div>
    </div>
  );
}

function Active_Info(props){
  return(
    <div className="education_info_container">
      <span className="small_bold_text active_label">{props.name}</span>
      <div className='row_container' id='left_auto_margin_container'>
        <div id="education_info" className="active_value">{props.value ? 'Получено' : 'В процессе обучения'}</div>
      </div>
    </div>
  );
}

function User_Reviews(props) {
  const [feedbackData, setFeedbackData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const observer = useRef();

  const getUserFeedbacks = async () => {
    if (loading || !hasMore || !props.userData?.id) return;
  
    setLoading(true);
    const url = `/api/rate/usr/${props.userData.id}?page=${page}`;
  
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
    if (!props.userData?.id) return;
    
    setFeedbackData([]);
    setPage(1);
    setHasMore(true);
    getUserFeedbacks();
  }, [props.userData?.id]);


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
      <h2 className="page_title_text">Отзывы о работах пользователя</h2>
      <ul className="reviews_container">
        {feedbackData.length > 0 ? (
          feedbackData.map((review) => <User_Review_Object review={review} key={review.id} />)
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

function User_Review_Object({ review }) {
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
      <div className='left_align_column' id="review_comment_container">
        <span id={review.comment ? "" : "grey_font"}>{review.comment || "Комментария нет"}</span>
      </div>
    </li>
  );
}


export default User_Info;