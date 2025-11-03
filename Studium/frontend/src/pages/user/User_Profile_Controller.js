import axios from 'axios';
import React, {useEffect, useState, useContext} from 'react';
import { useParams } from 'react-router-dom';

import AuthContext from '../../context/AuthContext';

import {Loading_Spinner, Navigation_Item, Error_POP_Element, PopUpComponent, Right_Button_Mobile_Section, Right_Button_Desktop_Section, BetweenBlocksElement} from '../../elements/main_elements'

import User_Info from './User_Profile';
import User_Form from './User_Form';
import User_History from './User_History'

function TabbarNavigateElement({activeTab, onClick, name, tab}){
    return(
        <li className={`navigation_item ${activeTab === tab ? 'active_tab' : ''}`}>
          <a className='navigation_link' onClick={() => onClick(tab)}>{name}</a>
        </li>
    );
}
function UserProfileTabbar({ userId, isUserPage, onClick, activeTab }) {
    return (
      <div className="user_profile_tabbar_container">
        <div className="user_profile_tabbar_content">
          <div className="user_profile_tabbar">
            <TabbarNavigateElement activeTab={activeTab} onClick={onClick} name="Информация" tab="user_info" />
            <Navigation_Item item_name="Продаваемые задания" link={`/sold_tasks/${userId}`} />
            {isUserPage && <Navigation_Item item_name="Купленные задания" link={`/buy_tasks`} />}
            {isUserPage && <TabbarNavigateElement activeTab={activeTab} onClick={onClick} name="История платежей" tab="user_history" />}
            {isUserPage && <TabbarNavigateElement activeTab={activeTab} onClick={onClick} name="Редактировать" tab="user_form" />}
          </div>
        </div>
      </div>
    );
  }
  
function UserProfileMain({ isUserPage, isUserAuth, activeTab, userData, handleChange, RightButtonActiveChange}) {
    const renderActiveComponent = () => {
        switch (activeTab) {
            case 'user_info':
                return <User_Info userData={userData} isUserPage={isUserPage} isUserAuth={isUserAuth}/>;
            case 'user_form':
                return <User_Form userData={userData} handleChange={handleChange} RightButtonActiveChange={RightButtonActiveChange}/>;
            case 'user_history':
                return <User_History />;
            default:
                return <User_Info userData={userData} />;
        }
    };

    return renderActiveComponent();
}

function User_Profile_Element(props) {
    const [isActive, setIsActive] = useState(true);

    const RightButtonActiveChange = (event) => {
        setIsActive(event.target.value);
    };

    return (
        <div className="column_container page_section_element">
            <div className="sides_container">
                <div className="border_container">
                    <div className="column_container">
                        <UserProfileTabbar userId={props.userData.id} isUserPage={props.isUserPage} onClick={props.handleTabClick} activeTab={props.activeTab}/>
                        <UserProfileMain 
                            isUserPage={props.isUserPage}
                            isUserAuth={props.isUserAuth}
                            activeTab={props.activeTab} 
                            userData={props.userData} 
                            handleChange={props.handleChange} 
                            RightButtonActiveChange={RightButtonActiveChange} 
                        />
                        <BetweenBlocksElement height='100px'/>
                        
                        {props.isUserPage && props.activeTab === 'user_form' && (
                            <Right_Button_Mobile_Section 
                            name={props.activeTab == 'user_form' ? 'Сохранить' : undefined}
                            onClick={props.activeTab == 'user_form' ? props.onSubmit : undefined}
                            disabled={isActive}
                          />
                        )}
                    </div>
                </div>
                {props.isUserPage && props.activeTab === 'user_form' && (
                    <Right_Button_Desktop_Section name='Сохранить' onClick={props.onSubmit} disabled={isActive} />
                )}
            </div>
        </div>
    );
}

function User_Profile_Contoller() {
    const { user, updateUserData, error} = useContext(AuthContext);
  
    const [activeTab, setActiveTab] = useState('user_info');

    const [userData, setUserData] = useState({});

    const [loadError, setLoadError] = useState(false)

    const [loading, setLoading] = useState(true);
  
    const { userId: userIdString } = useParams();

    const userId = parseInt(userIdString, 10);
  
    const isUserPage = user && userId === user.id;

    const isUserAuth = user && Object.keys(user).length > 0;
    
    const getUserData = async () => {
        setLoading(true);
        setLoadError(false);
    
        if (!isUserPage) {
            try {
                const url = `/api/up/${encodeURIComponent(userId)}`;
                const response = await axios.get(url);
                setUserData(response.data);
            } catch (error) {
                setLoadError(true);
            } finally {
                setLoading(false);
            }
        } else {
            setUserData(user);
            setLoading(false);
        }
    };
    

    useEffect( () => {
        getUserData();
    }, [user, userId]);
    
    useEffect(()=>{
        if(error){
            setUserData(user);
        }
    }, [error])

    const onSubmit = async () => {
        setLoading(true);
        setLoadError(false);
    
        try {
            await updateUserData(userData);
            setActiveTab('user_info');
        } finally {
            setLoading(false);
        }
    };
  
    const handleTabClick = (tab) => {
        if(tab === 'user_info'){
            if (user !== userData){
                onSubmit();
            }
        }

        setActiveTab(tab);
    };

    const handleChange = (event) => {      
        if (event?.target) {
            const { name, value } = event.target;
    
            setUserData(prevState => {
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
            setUserData(prevState => {
                const { [event.name]: _, ...rest } = prevState;
                return rest;
            });
        }
    };

    return (
      <>
        {loading && <Loading_Spinner />}
        {loadError && <PopUpComponent isVisible={loadError} displayed={<Error_POP_Element/>} onClose={() => {setLoadError(false); window.history.back();}}/>}
        <User_Profile_Element isUserPage={isUserPage} isUserAuth={isUserAuth} handleTabClick={handleTabClick} 
        activeTab={activeTab} userData={userData} handleChange={handleChange} onSubmit={onSubmit}/>
      </>
    );
  }
  
  export default User_Profile_Contoller;