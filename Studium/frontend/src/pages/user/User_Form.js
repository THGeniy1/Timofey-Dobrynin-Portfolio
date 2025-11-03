import axios from 'axios';
import React, { useState, useContext, useEffect, useCallback } from "react";

import AuthContext from '../../context/AuthContext';

import { Text_Section, City_Input, Place_Study_Input, Faculty_Input, Direction_Input, LevelSelect, Help_Button } from "../../elements/main_elements";

import { ReactComponent as addButtonImage} from "../../media/svg/add-button.svg";
import { ReactComponent as remove_image} from "../../media/svg/delete_1.svg";

import defaultAvatar from '../../media/png/User_avatar.png';
import Loading_Icon from '../../media/png/upload_files/grey_loading.png'

function User_Form_Title() {
    return (
      <div className="page_container">
        <div className="row_container">
            <h1 className="page_main_title_text">Личные данные</h1>
            <Help_Button hint_name='edit_profile_hint.json'/>
        </div>
      </div>
    );
}

function User_Main_Data(props) {
    const { userData, onChange, RightButtonActiveChange } = props;
    const isLocked = userData.is_inn_locked;
    
    return (
        <div className='page_container'>
            <div className='user_main_data_row'>
                <User_Avatar 
                    userData={userData} 
                    onChange={onChange} 
                    RightButtonActiveChange={RightButtonActiveChange} 
                />
                <div className="left_align_column" id="gap_container">
                    <User_Name_Input userData={userData} onChange={onChange} />
                    
                    <Foreign_Citizen_Checkbox 
                        userData={userData} 
                        onChange={onChange} 
                        disabled={isLocked} 
                    />

                    {!userData.is_foreign_citizen && (
                        <User_INN_Input 
                            userData={userData} 
                            onChange={onChange} 
                            disabled={isLocked} 
                        />
                    )}

                    <User_Gender_Selector userData={userData} onChange={onChange} />
                </div>
            </div>
        </div>
    );
}


function User_Name_Input({ userData, onChange }) {
    const [error, setError] = useState(null);
  
    const validateName = (name) => {
      if (name === "") return null;
      if (name.length > 50) return 'Имя не может быть длиннее 50 символов';
      if (!/^[а-яА-Яa-zA-Z\s-]+$/.test(name))
                               return 'Имя может содержать только буквы, пробелы и дефис';
      return null;
    };
  
    const handleChange = (e) => {
        const { name, value } = e.target;
        const validationError = validateName(value); 
        setError(validationError);
      
        if (!validationError) {
          onChange({ target: { name, value } });
        }
      };
  
    return (
        <div className="left_align_column">
            <h2 className="main_bold_text">Имя</h2>
            <div className="section_container" id="top_margin_container">
                <input
                className="section_input"
                type="text"
                name="name"
                placeholder="Ваше имя"
                value={userData.name}
                onChange={handleChange}
                required
                maxLength={50}
                />
            </div>
            {error && <div className="error_message">{error}</div>}
        </div>
    );
  }
  
  function User_INN_Input({ userData, onChange, disabled }) {
    const [error, setError] = useState(null);
    const hasInn = Boolean(userData?.has_inn);

    const validateInn = (inn) => {
        if (inn === "" || inn === null || inn === undefined) return null;
        if (!/^\d*$/.test(inn)) return 'ИНН может содержать только цифры';
        return null;
    };

    const handleChange = (e) => {
        if (disabled) return; // защищаем от изменения
        const { name } = e.target;
        const numericValue = (e.target.value || '').replace(/\D/g, '').slice(0, 12);
        const validationError = validateInn(numericValue);
        setError(validationError);
        onChange({ target: { name, value: numericValue } });
    };

    const handleBlur = () => {
        if (disabled) return;
        const inn = userData.inn || '';
        if (inn !== '' && inn.length !== 12) {
            setError('ИНН должен содержать 12 цифр');
        } else {
            setError(null);
        }
    };

    return (
        <div className="left_align_column">
            <h2 className="main_bold_text">ИНН</h2>
            <div className="section_container" id="top_margin_container">
                <input
                    className="section_input"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    name="inn"
                    placeholder="Ваш ИНН"
                    value={userData.inn || ''}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    maxLength={12}
                    style={{ borderColor: hasInn ? '#27ae60' : undefined }}
                    disabled={disabled} // добавлено
                />
            </div>
            {error && <div className="error_message">{error}</div>}
        </div>
    );
}

function User_Gender_Selector(props){
    const [gender, setGender] = useState(props.userData.gender || '');
    
    const handleChange = (event) => {
        setGender(event.target.value);
        props.onChange({ target: { name: 'gender', value: event.target.value }});
    };

    return (
        <div className="left_align_column">
            <h2 className="main_bold_text">Пол</h2>
            <div className="user_gender_container">
                <div className="user_gender_selector_container">
                    <label className="radio_label">
                        <input
                        type="radio"
                        name="gender"
                        value="Мужчина"
                        checked={gender === "Мужчина"}
                        onChange={handleChange}
                        />
                        <span>Мужчина</span>
                    </label>
                </div>
                <div className="user_gender_selector_container">
                    <label className="radio_label">
                        <input
                        type="radio"
                        name="gender"
                        value="Женщина"
                        checked={gender === "Женщина"}
                        onChange={handleChange}
                        />
                        <span>Женщина</span>
                    </label>
                </div>
            </div>
        </div>
    );
}

function User_Avatar(props) {
    const {accessToken} = useContext(AuthContext);
    const [isLoading, setIsLoading] = useState(false);

    const [avatar, setAvatar] = useState(props.userData.avatar || defaultAvatar);

    const MAX_FILE_SIZE = 5 * 1024 * 1024;
    const ALLOWED_TYPES = ['image/jpeg', 'image/png'];

    const handleAvatarChange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!ALLOWED_TYPES.includes(file.type)) {
          alert('Допустимы только JPEG и PNG изображения');
          return;
        }
        
        if (file.size > MAX_FILE_SIZE) {
          alert('Максимальный размер файла 5MB');
          return;
        }

        const formData = new FormData();
        formData.append('file', file);
        
        setIsLoading(true);
        props.RightButtonActiveChange({ target: { value: false }})

        try {
            const response = await axios.put(`/api/up/me/la/`, formData, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            
            if (!response.data || !response.data.url) {
                throw new Error('Invalid server response');
            }
            
            setAvatar(response.data.url);
            props.onChange({ target: { name: 'avatar', value: response.data.path }});
        } catch (error) {
            alert(`Невозможно добавить фото`);
        } finally {
            setIsLoading(false);
            props.RightButtonActiveChange({ target: { value: true }})
        }
    };

    return (
        <div className="column_container">
            <h2 className="main_bold_text">Фото</h2>
            <label className='user_add_avatar_photo' htmlFor="avatar-upload" style={{ cursor: 'pointer' }}>
                <img 
                    className='user_avatar'
                    id='user_main_avatar'
                    src={isLoading ? Loading_Icon : avatar} 
                    alt="User Avatar" 
                />
            </label>
            <input 
                id="avatar-upload"
                type='file' 
                accept=".jpeg, .jpg, .png" 
                onChange={handleAvatarChange} 
                style={{ display: 'none' }}
            />
        </div>
    );
}

function User_Description(props){
    return(
        <div className='page_container'>
            <h2 className="main_bold_text">О себе</h2>
            <Text_Section value={props.userData.description || ""} name='description' placeholder="Напишите о себе" onChange={props.onChange}/>
        </div>
    );
}

function User_Educations(props) {
    const [forms, setForms] = useState(props.userData.educations || []);
  
    const AddIconComponent = addButtonImage;
  
    useEffect(() => {
      props.onChange({ target: { name: "educations", value: forms } });
    }, [forms]);
  
    const handleAddForm = () => {
      setForms([...forms, { city: "", university: "", faculty: "", level: "", direction: "", active: true }]);
    };
  
    const handleChange = useCallback((index, updatedForm) => {
        setForms(prevForms =>
            prevForms.map((form, i) =>
                i === index ? { ...form, [updatedForm.target.name]: updatedForm.target.value } : form
            )
        );
    }, [setForms]);
    
    const handleRemoveForm = useCallback((index) => {
        setForms(prevForms => prevForms.filter((_, i) => i !== index));
    }, [setForms]);
  
    return (
        <div className="page_container">
            <h2 className="main_bold_text">Образование</h2>
            <div className="row_container">
                <div className="educations_container">
                    <div className="column_container">
                        {forms.map((form, index) => (
                            <User_Education_Form
                                form_id={index}
                                form={form}
                                onChange={handleChange}
                                onRemove={handleRemoveForm}
                            />
                        ))}
                        <button className="add_education_button" type="button" onClick={handleAddForm}>
                            <AddIconComponent id="add_education_svg" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
  }

  function Foreign_Citizen_Checkbox({ userData, onChange, disabled }) {
    const [isForeign, setIsForeign] = useState(Boolean(userData.is_foreign_citizen));

    const handleToggle = (e) => {
        if (disabled) return; // защищаем от изменения
        const checked = e.target.checked;
        setIsForeign(checked);
        onChange({ target: { name: 'is_foreign_citizen', value: checked } });
        if (checked) {
            onChange({ target: { name: 'inn', value: '' } });
        }
    };

    return (
        <div className="left_align_column">
            <h2 className="main_bold_text">Статус</h2>
            <div className="column_container" id="top_margin_container">
                <label className="radio_label">
                    <input
                        type="checkbox"
                        name="is_foreign_citizen"
                        checked={isForeign}
                        onChange={handleToggle}
                        className="checkbox"
                        disabled={disabled} // добавлено
                    />
                    <span>Иностранный гражданин</span>
                </label>
            </div>
        </div>
    );
}

function User_Education_Form({ form_id, form, onChange, onRemove }) {
    const RemoveIconComponent = remove_image;
    const handleChange = (e) => {
        const { name } = e.target;
        const resetFields = {
            city: ['university', 'faculty', 'level', 'direction'],
            university: ['faculty', 'level', 'direction'],
            faculty: ['level', 'direction'],
            level: ['direction'],
        };
        if (resetFields[name]) {
            resetFields[name].forEach(field => {
                form[field] = '';
            });
        }
        onChange(form_id, e);
    };
    const handleRemoveClick = () => {
        onRemove(form_id); 
    };
    return (
        <form id='around_border_container' className="education_form_grid">
            <div className="education_form_item">
                <span className="small_bold_text">Город</span>
                <City_Input id="education_section_container" data={form} setData={handleChange} />
            </div>
            <div className="education_form_item">
                <span className="small_bold_text">Место учебы</span>
                <Place_Study_Input id="education_section_container" data={form} setData={handleChange} />
            </div>
            <div className="education_form_item">
                <span className="small_bold_text">Факультет</span>
                <Faculty_Input id="education_section_container" data={form} setData={handleChange} />
            </div>
            <div className="education_form_item">
                <span className="small_bold_text">Уровень образования</span>
                <LevelSelect id="education_section_container" data={form} setData={handleChange} />
            </div>
            <div className="education_form_item">
                <span className="small_bold_text">Направление обучения</span>
                <Direction_Input id="education_section_container" data={form} setData={handleChange} />
            </div>
            <div className="education_form_item">
                <span className="small_bold_text">Получено</span>
                <ActiveBox data={form} setData={handleChange} />
            </div>
            <button className="remove_button" type="button" onClick={handleRemoveClick}>
                <RemoveIconComponent id="remove_button_svg" />
            </button>
        </form>
    );
}

function ActiveBox(props) {
    const [isActive, setIsActive] = useState(props.data.active || false);

    const handleChange = (event) => {
        setIsActive(event.target.checked);
        props.setData({ target: { name: 'active', value: event.target.checked } });
    };

    return (
        <div className="column_container activebox-column-container">
            <div className='section_container'>
                <input
                    type="checkbox"
                    name="isActive"
                    checked={isActive}
                    onChange={handleChange}
                    className="checkbox"
                />
            </div>
        </div>
    );
}

function User_Form(props) {

    return (
        <form className="max_page_container">
            <User_Form_Title />
            <User_Main_Data userData={props.userData} onChange={props.handleChange} RightButtonActiveChange={props.RightButtonActiveChange}/>
            <User_Description userData={props.userData} onChange={props.handleChange} />
            <User_Educations userData={props.userData} onChange={props.handleChange} />
        </form>
    );
}

export default User_Form;