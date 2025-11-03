import axios from 'axios';
import React, {useState, useContext, useEffect} from 'react';

import { useLocation } from 'react-router-dom';

import AuthContext from '../../context/AuthContext';

import {Text_Section, PopUpComponent, Loading_POP_Element, Help_Button, Error_POP_Element, BetweenBlocksElement, Right_Button_Mobile_Section, Right_Button_Desktop_Section} from '../../elements/main_elements';

import {ReactComponent as StarIcon} from '../../media/svg/star.svg'


function Create_Rate_Title(props){
  return(
    <div className="page_container">
      <div className='left_align_column'>
          <div className='row_container'>
              <h1 className="page_create_conflict_title">Страница оценки работы</h1>
              <Help_Button hint_name='rate_task_hint.json'/>
          </div>
          {props.id && <h2 className="conflict_work_id_text" id='grey_font'>id:{props.id}</h2>}
      </div>
    </div>
  );
}

function StarRating ({ totalStars = 5, onRate }){
  const [rating, setRating] = useState(0);

  const handleClick = (index) => {
    setRating(index);
    if (onRate) onRate(index);
  };

  return (
    <div className="star_rate_container">
      {[...Array(totalStars)].map((_, index) => {
        const starIndex = index + 1;
        return (
          <StarIcon
            key={starIndex}
            className={`star`}
            id={starIndex <= rating ? "star_filled" : ""}
            onClick={() => handleClick(starIndex)}
          />
        );
      })}
    </div>
  );
};
  
function Create_Rate_Score ({ onChange, totalStars = 5 }){
    return (
      <div className="page_container">
        <h2 className="page_title_text">Оценка</h2>
        <div className="row_space_between_container">
          <h3 className="main_text">Ваша оценка</h3>
          <StarRating totalStars={totalStars} onRate={(value) => onChange({ target: { name: "rate", value } })} />
        </div>
      </div>
    );
  };

function Create_Rate_Feedback(props){
  return(
    <div className='page_container'>
      <h2 className="page_title_text">Отзыв</h2>
      <Text_Section onChange={props.onChange} name={'comment'}/>
    </div>
  );
}

function Create_Rate() {
    const { accessToken } = useContext(AuthContext);

    const location = useLocation();

    const [rateData, setRateData] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    const [displayedPOP, setDisplayedPOP] = useState(null);

    const requiredKeys = ["rate"];

    const createRate = async (event) => {
      event.preventDefault();

      let formData = new FormData();
      const objectId = location.state.data.id;

      if (objectId) {
          formData.append("task_id", objectId);
      }

      Object.entries(rateData).forEach(([key, value]) => {
        formData.append(key, value);
      });

      try {
        await axios.post("/api/rate/cr/", formData, { 
            headers: { 'Authorization': `Bearer ${accessToken}`, } 
        });
        setDisplayedPOP(
            <Loading_POP_Element 
                main_text="Ваш отзыв будет скоро размещен." 
                sub_text="После размещения вы получите уведомление."
            />
        );
      } catch (error) {
          setDisplayedPOP(
              <Error_POP_Element message={error.response?.data?.message || "Ошибка при размещении отзыва"} />
          );
      } finally {
          setIsLoading(true); 
      }
    };

    const handleChange = (event) => {      
      if (event?.target) {
          const { name, value } = event.target;
  
          setRateData(prevState => {
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
        setRateData(prevState => {
              const { [event.name]: _, ...rest } = prevState;
              return rest;
          });
      }
    };

    const isFormValid = () => {
        const hasRequiredKeys = requiredKeys.every(key => key in rateData);
        const hasValidFiles = rateData.files ? rateData.files.every(file => file.is_load) : true;
        
        return hasRequiredKeys && hasValidFiles;
    };

    return (
      <div className="column_container">
        {isLoading && <PopUpComponent isVisible={isLoading} displayed={displayedPOP} onClose={() => {{window.history.back();}}} />}
        <form className="sides_container">
          <div className="border_container">
              <div className='column_container'>
                <Create_Rate_Title id={location.state.data.id}/>
                <Create_Rate_Score onChange={handleChange}/>
                <Create_Rate_Feedback onChange={handleChange}/>
                <BetweenBlocksElement height='clamp(15px, 3vw, 25px)'/>
                <Right_Button_Mobile_Section name="Создать" onClick={createRate} disabled={isFormValid()} />
              </div>
            </div>
            <Right_Button_Desktop_Section name="Создать" onClick={createRate} disabled={isFormValid()} />
        </form>
      </div>
    );
}


export default Create_Rate;