import axios from 'axios';
import React, {useState, useContext, useEffect} from 'react';

import { useLocation } from 'react-router-dom';

import AuthContext from '../../context/AuthContext';

import { Loading_Spinner, Text_Section, PopUpComponent, Error_POP_Element, Help_Button, Ready_Task_Info, 
  Right_Button_Mobile_Section, Right_Button_Desktop_Section, BetweenBlocksElement, Row_Input_Section } from '../../elements/main_elements';
import { FileUpload } from '../../elements/FileUpload';

import {Loading_POP_Element} from '../../elements/main_elements';

function Create_Refund_Title(props) {
  return (
    <div className="page_container">
      <div className='left_align_column'>
        <div className='row_container'>
            <h1 className="page_main_title_text">Оформить возврат на работу</h1>
          <Help_Button hint_name='refund_hint.json'/>
        </div>
        <h2 className="conflict_work_id_text" id='grey_font'>id:{props.data.id}</h2>
      </div>
    </div>
  );
}

function Create_Refund_Ready_Task_Info(props) {
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
                </div>
            </div>
        </div>
    );
}

function Create_Refund_Comment(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Причина отказа</h2>
      <Text_Section onChange={props.onChange} name={'reason'}/>
    </div>
  );
}

function Create_Refund_Contact_Info(props){
    return(
        <div className="page_container">
          <h2 className="page_title_text">Контактная информация</h2>
          <Row_Input_Section name="Ваша почта:" placeholder='Ваша почта' value_name="email" onChange={props.onChange}/>
          <Row_Input_Section name="Номер телефона" placeholder='Номер телефона' value_name="phone" onChange={props.onChange}/>
        </div>
    );
  }

function Create_Refund_Media(props){
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

function Create_Refund() {
    const { accessToken } = useContext(AuthContext);
    const location = useLocation();

    const [objectData, setObjectData] = useState({});
    const [refundValue, setRefundValue] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadData, setIsLoadData] = useState(true);
    const [displayedPOP, setDisplayedPOP] = useState(null);
    const [errors, setErrors] = useState([]);

    const requiredKeys = ["reason", "email", "phone"];

    const handleError = (message) => {
        setErrors(prev => [...prev, message]);
        setTimeout(() => setErrors(prev => prev.slice(1)), 5000);
    };

    useEffect(() => {
        const getTaskData = async () => {
          if(location.state?.data){
            setIsLoadData(false);
            
            const url =  `/api/rt/${encodeURIComponent(location.state.data.id)}/`;
            
            try {
                const response = await axios.get(url);
                setObjectData(response.data);
                setIsLoadData(true);
            } catch (error) {
                const errorMessage = error.response?.data?.message || 'Произошла ошибка при загрузке данных задачи';
                setDisplayedPOP(<Error_POP_Element message={errorMessage}/>);
                setIsLoading(true);
            }
          }
        }
        
        getTaskData();

    }, []);

    const createNewRefund = async (event) => {
      event.preventDefault();

      let formData = new FormData();     
      
      if (objectData?.id) {
          formData.append("object_id", objectData.id);
      }

      Object.entries(refundValue).forEach(([key, value]) => {
        if (key === "files" && refundValue['files']) {
            value.forEach(item => {
              formData.append('file_names', item.name);
              formData.append('file_paths', item.path);
            });
        } else {
            formData.append(key, value);
        }
      });

      try {        
        await axios.post("/api/refund/cr/", formData, { 
            headers: {'Authorization': `Bearer ${accessToken}`, } 
        });
        setDisplayedPOP(
            <Loading_POP_Element 
                main_text="Мы рассмотрим вашу завявку на возврат в течение 3 рабочих дней."
                sub_text="По результатам вы получите уведомление."
            />
          );
      } catch (error) {
          const errorMessage = error.response?.data?.message || 'Произошла ошибка при создании возврата';
          setDisplayedPOP(<Error_POP_Element message={errorMessage} />);
      } finally {
          setIsLoading(true);
      }
    };

    const handleChange = (event) => {      
      if (event?.target) {
          const { name, value } = event.target;
  
          setRefundValue(prevState => {
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
          setRefundValue(prevState => {
              const { [event.name]: _, ...rest } = prevState;
              return rest;
          });
      }
    };
  
    const isFormValid = () => {
        const hasRequiredKeys = requiredKeys.every(key => key in refundValue);
        const hasValidFiles = refundValue.files ? refundValue.files.every(file => file.is_load) : true;
        
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
                  <Create_Refund_Title data={objectData}/>
                  <Create_Refund_Ready_Task_Info data={objectData}/>
                  <Create_Refund_Comment onChange={handleChange}/>
                  <Create_Refund_Contact_Info onChange={handleChange}/>
                  <Create_Refund_Media onChange={handleChange} onError={handleError}/>
                  <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                  <Right_Button_Mobile_Section name="Создать" onClick={createNewRefund} disabled={isFormValid()} />
              </div>
          </div>
          <Right_Button_Desktop_Section name="Создать" onClick={createNewRefund} disabled={isFormValid()} />
        </form>
      </div>
    );
}

export default Create_Refund;