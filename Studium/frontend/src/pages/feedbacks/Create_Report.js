import axios from 'axios';
import React, {useState, useContext, useEffect} from 'react';

import { useLocation } from 'react-router-dom';

import AuthContext from '../../context/AuthContext';

import { Loading_Spinner, Text_Section, PopUpComponent, Error_POP_Element, Help_Button, Ready_Task_Info, Ready_Task_Link, Right_Button_Mobile_Section, Right_Button_Desktop_Section, BetweenBlocksElement } from '../../elements/main_elements';
import { FileUpload } from '../../elements/FileUpload';

import defaultAvatar from '../../media/png/User_avatar.png';

import {Loading_POP_Element} from '../../elements/main_elements';

function Create_Conflict_Title(props) {
  const titles = {
    ready_task: "Страница подачи жалобы на работу",
    user: "Страница подачи жалобы на пользователя",
  };

  const hints = {
    ready_task: "work_report_hint.json",
    user: "user_report_hint.json",
  };

  const title_text = titles[props.type] || "Страница подачи жалобы или предложения";
  const hint_name = hints[props.type] || "general_report_hint.json";

  return (
    <div className="page_container">
      <div className='left_align_column'>
        <div className='row_container'>
          <h1 className="page_create_conflict_title">{title_text}</h1>
          <Help_Button hint_name={hint_name} />
        </div>
        {props.data.id && <h2 className="conflict_work_id_text" id='grey_font'>id:{props.data.id}</h2>}
      </div>
    </div>
  );
}



function Create_Conflict_Ready_Task_Info(props) {
    return (
        <div className="page_container">
            <div className='left_align_column' id='task_info_container'>
                <h2 className="page_title_text">Информация</h2>
                <div className='page_container'>
                    <Ready_Task_Info name="Название: " value={props.data.name}/>
                    <Ready_Task_Info name="Предмет: " value={props.data.discipline}/>
                    <Ready_Task_Info name="Тип задания: " value={props.data.type}/>
                    <Ready_Task_Info name="Преподаватель: " value={props.data.tutor}/>
                </div>
                <div className='page_container'>
                    <Ready_Task_Info name="Оценка: " value={props.data.score}/>
                    <Ready_Task_Info name="Стоимость: " value={props.data.price}/>
                    <Ready_Task_Link name="Владелец: " value={props.data.owner_name} link={`/user/${encodeURI(props.data.owner_id)}/`}/>
                </div>
            </div>
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

function Create_Conflict_User_Info(props) {
  const dateJoined = new Date(props.data.date_joined);
  const formattedDate = dateJoined.toLocaleDateString('ru-RU', {year: 'numeric', month: 'long', day: 'numeric',});

  return(
    <div className='page_container'>
      <div className='row_container'>
        <div className='user_report_photo'>
          <img className='user_avatar' id='user_search_avatar' src={props.data.avatar || defaultAvatar}></img>
        </div>
        <div className='user_profile_container'>
          <div className='left_align_column'>
            <h2 className="main_bold_text">{props.data.name || "Пользователь №" + props.data.id}</h2>
            <h3 id='grey_font'>{"На сайте с: " + formattedDate}</h3>
          </div>
          <div className='row_grid'>
            <div className='left_align_column'>
                <div className='row_container'>
                    <h2 className="little_bold_text">Оценка: {props.data.average_rating}</h2>
                </div>
                <div className='row_container'>
                    <h2 id='grey_font'>На основе {getReviewsText(props.data.reviews_count)}</h2>
                </div>
            </div>
            <div className='left_align_column'>
                <h2 className="little_bold_text">{getReadyTaskText(props.data.posted_tasks_count)}</h2>
                <h2 id='grey_font'>разместил</h2>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Create_Conflict_General_Info(props) {
  return (
      <div className="page_container">
          <h2 className="page_title_text">Выбор темы обращения</h2>
          <div className='row_space_between_container' >
            <h3 className="main_text">Тема обращения</h3>
            <div className='section_container' id='main_section_container'>
                <select onChange={props.onChange} name='category'>
                    <option selected disabled>Выберите тип обращения</option>
                    <option value={'report'}>Жалоба</option>
                    <option value={'offer'}>Предложение</option>
                </select>
            </div>
          </div>
      </div>
  );
}

function Create_Conflict_Description(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Описание</h2>
      <Text_Section onChange={props.onChange} name={'comment'}/>
    </div>
  );
}

function Create_Conflict_Media(props){
  return(
    <div className='page_container'>
      <div className='left_align_column'>
        <h2 className="page_title_text">Фотографии и файлы</h2>
      </div>
      <div className="row_container">
        <FileUpload 
          onChange={props.onChange} 
          onError={props.onError}
          maxFiles={15}
          showPublicCheckbox={false}
        />
      </div>
    </div>
  );
}

function Get_Info_Object(props){
  const componentsMap = {
    ready_task: <Create_Conflict_Ready_Task_Info data={props.data} />,
    user: <Create_Conflict_User_Info data={props.data}/>,
    general: <Create_Conflict_General_Info onChange={props.onChange}/>,
  };
  
  const component = componentsMap[props.type];

  if (!component) {
    return null;
  }

  return component; 

}

function Create_Conflict() {
    const { accessToken } = useContext(AuthContext);
    const location = useLocation();

    const [objectData, setObjectData] = useState({});
    const [reportValue, setReportValue] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadData, setIsLoadData] = useState(true);
    const [displayedPOP, setDisplayedPOP] = useState(null);
    const [errors, setErrors] = useState([]);

    const objectType = location.state?.data.object === "ready_task" ? "ready_task" : (location.state?.data.object ? "user" : "general");
  
    const requiredKeys = objectType === "general" ? ["comment", "category"] : ["comment"];

    const handleError = (message) => {
        setErrors(prev => [...prev, message]);
        setTimeout(() => setErrors(prev => prev.slice(1)), 5000);
    };

    useEffect(() => {
        const getTaskData = async () => {
          if(location.state?.data){
            setIsLoadData(false);
            
            const url = location.state.data.object === "ready_task" ? `/api/rt/${encodeURIComponent(location.state.data.id)}/` : `/api/up/${encodeURIComponent(location.state.data.id)}/`;
            
            try {
              const response = await axios.get(url);
              setObjectData(response.data);
            } catch (error) {
              const errorMessage = error.response?.data?.message || "Ошибка при загрузке данных";
              setDisplayedPOP(<Error_POP_Element message={errorMessage}/>);
              setIsLoading(true);
            } finally {
              setIsLoadData(true);
            }
          }
        }
        
        getTaskData();

    }, []);

    const createNewConflict = async (event) => {
      event.preventDefault();

      let formData = new FormData();
      const objectId = location.state?.data.object ? objectData['id'] : null;

      formData.append("object", objectType);

      if (objectId) {
          formData.append("object_id", objectId);
      }

      Object.entries(reportValue).forEach(([key, value]) => {
        if (key === "files" && reportValue['files']) {
            value.forEach(item => {
              formData.append('file_names', item.name);
              formData.append('file_paths', item.path);
            });
        } else {
            formData.append(key, value);
        }
      });

      try {
        await axios.post("/api/re/cr/", formData, { 
            headers: {'Authorization': `Bearer ${accessToken}`, } 
        });
        setDisplayedPOP(
            <Loading_POP_Element 
                main_text="Ваша жалоба будет скоро размещена." 
                sub_text="После размещения вы получите уведомление."
            />
          );
      } catch (error) {
          const errorMessage =error.response?.data?.message || "Ошибка при отправке обращения";
          setDisplayedPOP(<Error_POP_Element message={errorMessage} />);
      } finally {
          setIsLoading(true);
      }
    };

    const handleChange = (event) => {      
      if (event?.target) {
          const { name, value } = event.target;
  
          setReportValue(prevState => {
              if (value === "" || value == null) {
                  const { [name]: _, ...rest } = prevState;
                  return rest;
              }
              return {
                  ...prevState,
                  [name]: value
              };
          });
      } else if (event?.name) {
        setReportValue(prevState => {
              const { [event.name]: _, ...rest } = prevState;
              return rest;
          });
      }
    };

    const isFormValid = () => {
        const hasRequiredKeys = requiredKeys.every(key => key in reportValue);
        const hasValidFiles = reportValue.files ? reportValue.files.every(file => file.is_load) : true;
        
        return hasRequiredKeys && hasValidFiles;
    };

    return (
      <div className="column_container">
        {!isLoadData && <Loading_Spinner />} 
        {isLoading && <PopUpComponent isVisible={isLoading} displayed={displayedPOP} onClose={() => {{window.history.back();}}} />}
        
        {errors.length > 0 && (
          <div className="error-notifications">
            {errors.map((error, index) => (
              <div key={index} className="error-notification">
                {error}
              </div>
            ))}
          </div>
        )}

        <form className="sides_container">
          <div className="border_container">
              <div className="column_container">
                  <Create_Conflict_Title type={objectType} data={objectData}/>
                  <Get_Info_Object onChange={handleChange} type={objectType} data={objectData}/>
                  <Create_Conflict_Description onChange={handleChange}/>
                  <Create_Conflict_Media onChange={handleChange} onError={handleError}/>
                  <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                  <Right_Button_Mobile_Section name="Создать" onClick={createNewConflict} disabled={isFormValid()} />
              </div>
          </div>
          <Right_Button_Desktop_Section name="Создать" onClick={createNewConflict} disabled={isFormValid()} />
        </form>
      </div>
    );
}

export default Create_Conflict;