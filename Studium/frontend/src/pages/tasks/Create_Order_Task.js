import axios from 'axios';
import React, {useState, useEffect, useContext} from 'react';

import { useLocation } from 'react-router-dom';

import { Loading_Spinner, Input_Section, Select_Section, Education_Select, City_Input, 
  Place_Study_Input, Faculty_Input, Direction_Input, LevelSelect, Text_Section, PopUpComponent, BetweenBlocksElement,
  Loading_POP_Element, Error_POP_Element, Help_Button, Right_Button_Desktop_Section, Right_Button_Mobile_Section, Row_Input_Section } from '../../elements/main_elements';
import { FileUpload } from '../../elements/FileUpload';

import AuthContext from '../../context/AuthContext';


function Row_Select_Section(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">{props.name}</h3>
      <div className="form_control_wide">
        <Select_Section fileName={props.fileName} value={props.value} value_name={props.value_name} title={props.title} onChange={props.onChange}/>
      </div>
    </div>
  );
}

function Create_Task_Title() {
  return (
    <div className="page_container">
      <div className='title_help_row'>
          <h1 className="page_main_title_text">Разместить заказ на выполнение задания</h1>
          <Help_Button hint_name='create_task_hint.json'/>
      </div>
    </div>
  );
}

function Create_Task_Details(props) {
  return (
    <div className="page_container">
      <h2 className="page_title_text">Подробности</h2>
      <Row_Input_Section name="Название работы:" placeholder='Название работы'  value_name="name" onChange={props.onChange} value={props.value.name}/>
      <Row_Input_Section name="Название предмета:" placeholder='Название предмета' value_name="discipline" onChange={props.onChange} value={props.value.discipline}/>
      <Row_Select_Section name="Тип задания:" fileName="types" value_name="type" title="Тип задания" onChange={props.onChange} value={props.value.type}/>
    </div>
  );
}

function Create_Task_Description(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Описание</h2>
      <Text_Section onChange={props.onChange} placeholder="Опишите задание: что нужно сделать, требования к выполнению, важные детали и нюансы" name={'description'} value={props.value.description}/>
    </div>
  );
}

function Create_Task_Media(props){
  return(
    <div className='page_container'>
      <div className='left_align_column'>
        <h2 className="page_title_text">Фотографии и файлы</h2>
      </div>
      <div className="row_container">
        <FileUpload 
          onChange={props.onChange} 
          value={props.value.files}
          onError={props.onError}
          maxFiles={15}
          showPublicCheckbox={true}
        />
      </div>
    </div>
  );
}

function Create_Task_Education(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Образование</h2>
      <div className='row_space_between_container'>
        <h3 className="main_text">Ваше образование:</h3>
        <Education_Select className="form_control_wide" onChange={props.onChange} education={props.value.education}/>
      </div>
    </div>
  );

}

function Recreate_Education_Select(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Ваше образование</h3>
      <Education_Select className="form_control_wide" onChange={props.onChange} education={props.education}/>
    </div>
  );
}

function Recreate_City_Input(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Город</h3>
      <div className="form_control_wide">
        <City_Input data={props.data} setData={props.setData} />
      </div>
    </div>
  );
}

function Recreate_Place_Study_Input(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Место учебы</h3>
      <div className="form_control_wide">
        <Place_Study_Input data={props.data} setData={props.setData} />
      </div>
    </div>
  );
}

function Recreate_Faculty_Input(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Факультет</h3>
      <div className="form_control_wide">
        <Faculty_Input data={props.data} setData={props.setData} />
      </div>
    </div>
  );
}

function Recreate_Direction_Input(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Направление обучения</h3>
      <div className="form_control_wide">
        <Direction_Input data={props.data} setData={props.setData} />
      </div>
    </div>
  );
}

function Recreate_Level_Select(props){
  return(
    <div className='row_space_between_container' >
      <h3 className="main_text">Уровень образования</h3>
      <div className="form_control_wide">
        <LevelSelect data={props.data} setData={props.setData} />
      </div>
    </div>
  );
}

function Recreate_Task_Education(props){
  const { user } = useContext(AuthContext);
  const [educationData, setEducationData] = useState(props.value.education || {});
  const resetFieldsMap = {
    city: ["university", "faculty", "level", "direction"],
    university: ["faculty", "level", "direction"],
    faculty: ["level", "direction"],
    level: ["direction"],
};

  useEffect(() => {
    props.onChange({
      target: {
        name: "education",
        value: educationData
      }
    });
  }, [educationData]);

  const handleChange = (event) => {
      const { name, value } = event.target;

      setEducationData((prevData) => {
          const updatedData = { ...prevData, [name]: value };

          if (resetFieldsMap[name]) {
              resetFieldsMap[name].forEach((field) => {
                  updatedData[field] = "";
              });
          }

          return updatedData;
      });
  };

  const educationSelect = (e) => {
      const selectedIndex = e.target.value;
      if (user && user.educations && user.educations[selectedIndex]) {
          const education = user.educations[selectedIndex];
          setEducationData((prevData) => ({
              ...prevData,
              city: education.city,
              university: education.university,
              faculty: education.faculty,
              direction: education.direction,
              level: education.level,
          }));
      }
  };

  return(
    <div className='page_container'>
      <h2 className='page_title_text'>Образование</h2>
      <Recreate_Education_Select onChange={educationSelect} education={props.value.education}/>
      <Recreate_City_Input data={educationData} setData={handleChange} />
      <Recreate_Place_Study_Input data={educationData} setData={handleChange} />
      <Recreate_Faculty_Input data={educationData} setData={handleChange} />
      <Recreate_Direction_Input data={educationData} setData={handleChange} />
      <Recreate_Level_Select data={educationData} setData={handleChange} />
    </div>
  );
}

function Create_Task_Price_Input(props) {
  const [price, setPrice] = useState(props.price || '');
  
  const handleChange = (e) => {
    const newValue = e.target.value;
    setPrice(newValue);
    props.onChange(e);
  };

  return (
    <div className='left_align_column'>
      <div className='row_space_between_container'>
        <h3 className="main_text">Цена:</h3>
        <div className='form_control_wide'>
          <Input_Section placeholder='₽' value={price} value_name="price" type="number" onChange={handleChange}/>
        </div>
      </div>
      <h2 id='grey_font'>Которую вы гоотовы заплатить за выполнение задания</h2>
    </div>
  );
}

function Row_Date_Section(props) {
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="row_space_between_container">
      <h3 className="main_text">Срок выполения задания:</h3>
      <div className="form_control_wide">
        <div className='section_container' id='main_section_container'>
          <input className="section_input" name='deadline' value={props.value} min={today} type="date" onChange={props.onChange} required/>
        </div>
      </div>
    </div>
  );
}

function Create_Task_Additionally(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Дополнительно</h2>
      <Row_Input_Section name="Преподаватель:" placeholder='ФИО преподавателя' value_name = "tutor" type={'text'} onChange={props.onChange} value={props.value.tutor}/>
      <Row_Date_Section value={props.value.deadline}  onChange={props.onChange}/>
      <Create_Task_Price_Input onChange={props.onChange} price={props.value.price}/>
    </div>
  );
}

function Create_Task_Information_POP_UP() {
    return (
      <div className='status_pop_up_container'>
        <span className='main_text'>
          Чтобы разместить задание, потребуется дополнительная информация.
          <br /><br />
          Пожалуйста, укажите в вашем профиле:
          <br />
          • Сведения об образовании
          <br /><br />
          Это займет всего минуту.
        </span>
      </div>
    );
  }
  
function Create_Order_Task() {
  const { accessToken, user } = useContext(AuthContext);

  const location = useLocation();
  const [taskValue, setTaskValue] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadData, setIsLoadData] = useState(true);
  const [displayedPOP, setDisplayedPOP] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [errors, setErrors] = useState([]);

  const requiredKeys = ["name", "type", "discipline", "description", "education", "tutor", "price", "deadline"];
  
  useEffect(() => {
    if (!user?.educations || user.educations.length === 0) {
      setDisplayedPOP(<Create_Task_Information_POP_UP />);
      setShowPopup(true);
    }
  }, [user]);

  const handleError = (message) => {
    setErrors(prev => [...prev, message]);
    setTimeout(() => setErrors(prev => prev.slice(1)), 5000);
  };

  useEffect(() => {
    const getTaskData = async () => {
      if (location.state?.data) {
        setIsLoadData(false);
        
        try {
          const response = await axios.get(`/api/ot/rcr/${location.state.data}/`, {headers: {'Authorization': `Bearer ${accessToken}`}});       
          setTaskValue(response.data);
        } catch (error) {
          setDisplayedPOP(<Error_POP_Element message={error.response?.data?.message || "Ошибка при загрузке данных"}/>);
          setIsLoading(true);
        } finally {
          setIsLoadData(true);
        }
      }
    }
    
    getTaskData();
  }, [location.state]);

  const validateTaskData = (data) => {
    const validationErrors = [];
    
    if (!data.name || data.name.trim().length < 5) {
      validationErrors.push("Название работы должно содержать минимум 5 символов");
    }
    
    if (data.price <= 0) {
      validationErrors.push("Цена должна быть положительной");
    }
    
    if (!data.description || data.description.trim().length < 20) {
      validationErrors.push("Описание должно содержать минимум 20 символов");
    }

    return validationErrors;
  };

  const createNewTask = async (event) => {
    event.preventDefault();
    
    const validationErrors = validateTaskData(taskValue);
    if (validationErrors.length > 0) {
      validationErrors.forEach(error => handleError(error));
      return;
    }

    setIsLoading(true);
    
    try {
      const formData = new FormData();
      
      Object.entries(taskValue).forEach(([key, value]) => {
        if (value === undefined || value === null) {
          return;
        }

        if (key === "files") {
          value?.forEach((item) => {
            formData.append('file_names', item.name);
            formData.append('file_paths', item.path);
            formData.append('file_sizes', item.size);
            formData.append('file_is_public', item.is_public); 
          });
        } else if (key === 'education') {
          formData.append('education', JSON.stringify(value));
        } else {
          formData.append(key, value);
        }
      });
      
      await axios.post("/api/ot/cr/", formData, {headers: {'Authorization': `Bearer ${accessToken}`}});  

      setDisplayedPOP(<Loading_POP_Element main_text="Ваше задание будет скоро размещено!" sub_text="После размещения вы получите уведомления."/>);
      setShowPopup(true);
    
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || "Произошла ошибка при размещении работы";
      handleError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (event) => {      
    if (event?.target) {
        const { name, value } = event.target;

        setTaskValue(prevState => {
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
        setTaskValue(prevState => {
            const { [event.name]: _, ...rest } = prevState;
            return rest;
        });
    }
  };

  const isFormValid = () => {
    const { files, education } = taskValue;
    const hasRequiredKeys = requiredKeys.every(key => key in taskValue);
    const hasValidFiles = files?.every(file => file.is_load) ?? true;
  
    const hasValidEducation =
      taskValue.is_recreate
        ? typeof education === "object" &&
          education &&
          ["city", "direction", "faculty", "level", "university"].every(
            key => typeof education[key] === "string" && education[key].trim()
          )
        : education != null &&
          (typeof education === "string" ? education.trim() : true);
  
    return hasRequiredKeys && hasValidFiles && hasValidEducation;
  };

  return (
    <div className="column_container">
        {!isLoadData && <Loading_Spinner />} 
        {(isLoading || showPopup) && <PopUpComponent isVisible={true} displayed={displayedPOP} onClose={() => {
          setShowPopup(false);
          window.history.back();
        }} />}
        
        {errors.length > 0 && (
          <div className="error-notifications">
            {errors.map((error, index) => (
              <div key={index} className="error-notification">
                {error}
              </div>
            ))}
          </div>
        )}
        
        <div className="sides_container">
          <div className="border_container">
              <div className="column_container">
                <Create_Task_Title />
                <Create_Task_Details onChange={handleChange} value={taskValue}/>
                <Create_Task_Description onChange={handleChange} value={taskValue}/>
                <Create_Task_Media onChange={handleChange} value={taskValue} onError={handleError}/>
                {taskValue.is_recreate ? <Recreate_Task_Education onChange={handleChange} value={taskValue} /> : <Create_Task_Education onChange={handleChange} value={taskValue} />}   
                <Create_Task_Additionally onChange={handleChange} value={taskValue}/>
                <BetweenBlocksElement height='100px'/>
                <Right_Button_Mobile_Section name="Создать" onClick={createNewTask} disabled={isFormValid()} />
              </div>
            </div>
            <Right_Button_Desktop_Section name='Создать' onClick={createNewTask} disabled={isFormValid} />
        </div>
    </div>
  );
}

export default Create_Order_Task;