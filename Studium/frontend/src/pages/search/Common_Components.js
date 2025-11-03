import axios from 'axios';
import React, {useState, useEffect, useContext, useRef} from 'react';

import { useLocation } from 'react-router-dom';

import { ReactComponent as FilterIcon } from '../../media/svg/filter.svg';

import { Head_Searchbar, Loading_Spinner, PopUpComponent, DeletePopUpComponent, ShortPopUpComponent, Error_POP_Element} from '../../elements/main_elements';

import AuthContext from '../../context/AuthContext';

function Default_Search_Page(props) {
    const [showFilters, setShowFilters] = useState(false);
    
    const toggleFilters = () => {
      setShowFilters(!showFilters);
    };
  
    const closeFilters = () => {
      setShowFilters(false);
    };
  
    return (
      <div className='column_container'>
        <div className='row_container' id='head_container'>
            <Head_Searchbar 
                placeholder={props.addData?.isTaskSearch ? 'Название работы' : 'Имя исполнителя'} 
                data={props.searchData} 
                onChange={props.handleChange} 
                onClick={props.fetchData}
            />
            <div 
                className="mobile_menu_icon" 
                id='searchbar_filter_icon_wraper'
                onClick={toggleFilters}
            >
                <FilterIcon className='searchbar_filter_icon'/>
            </div>
        </div>
        
        <div className='sides_container'>
          <div className="left_align_column" id='search_border_container'>
            <div className='searchbar_text_container'>
              <div className='searchbar_text_inner_container'>
                <h1 className='little_text'>
                  Найдено {props.addData?.searchText}: <span className='little_bold_text' id='light_grey_font'>{props.totalFind}</span>
                </h1>
              </div>
            </div>
            <ul className='max_sizes_container'>
              {props.findValue.map((data, index) => (
                <props.searchElement key={index} data={data}/>
              ))}
            </ul>
          </div>
          
          <div id='search_sticky_container'>
            <props.rightSection 
              data={props.searchData} 
              handleChange={props.handleChange} 
              educationSelect={props.educationSelect} 
              onClick={props.fetchData} 
              reset={props.reset}
            />
          </div>
          
            <div className={`mobile-filters ${showFilters ? 'mobile-filters--visible' : ''}`}>
                <div className="mobile-filters-content">
                    <div className="mobile-filters-header">
                        <button className="mobile-filters-close" onClick={closeFilters}>
                            &times;
                        </button>
                    </div>
                    <div className="mobile-filters-body">
                        <props.rightSection 
                            data={props.searchData} 
                            handleChange={props.handleChange} 
                            educationSelect={props.educationSelect} 
                            onClick={props.fetchData}
                            reset={props.reset}
                        />
                    </div>
                </div>
                <div className="mobile-filters-overlay" onClick={closeFilters}></div>
            </div>
        </div>
      </div>
    );
  }

  function Extended_Search_Page(props) {
    const [activePopUp, setActivePopUp] = useState(null);
    const [taskID, setTaskID] = useState(null);
    const [showFilters, setShowFilters] = useState(false);
    const location = useLocation();

    const deletePopUpText = "Вы действительно хотите снять работу с публикации?"
    const ratePopUpText = "Вы действительно хотите оценить работу?";
    const conflictPopUpText = "Вы действительно хотите подать жалобу на эту работу?";
    
    const togglePopUp = ({ popUpId = null, taskId = null } = {}) => {
        setTaskID(taskId);
        setActivePopUp(prev => (prev === popUpId ? null : popUpId));
    };

    const toggleFilters = () => {
        setShowFilters(!showFilters);
    };

    const closeFilters = () => {
        setShowFilters(false);
    };

    let headerText = '';
    if (location.pathname.includes('sold_tasks')) {
        headerText = 'Работы, выставленные на продажу пользователем id:' + props.addData?.userId;
    } else if (location.pathname.includes('buy_tasks')) {
        headerText = 'Купленные работы пользователем id:' + props.addData;
    }

    return (
        <>
            {activePopUp === 'deletePop' && 
                <DeletePopUpComponent 
                    isVisible={true} 
                    id = {taskID}
                    text={deletePopUpText}
                    onClose={() => togglePopUp()} 
                />
            }

            {activePopUp === 'ratePop' && 
                <ShortPopUpComponent 
                    isVisible={true} 
                    text={ratePopUpText} 
                    link={`/rate_task`} 
                    data={{ id: taskID }} 
                    onClose={() => togglePopUp()} 
                />
            }

            {activePopUp === 'conflictPop' && 
                <ShortPopUpComponent 
                    isVisible={true} 
                    text={conflictPopUpText} 
                    link={`/create_report`} 
                    data={{ id: taskID, object: "ready_task" }} 
                    onClose={() => togglePopUp()} 
                />
            }

            <div className='column_container'>
                <div className='row_container' id='head_container'>
                    <Head_Searchbar 
                        placeholder={'Название работы'} 
                        data={props.searchData} 
                        onChange={props.handleChange} 
                        onClick={props.fetchData}
                    />
                    <div 
                        className="mobile_menu_icon" 
                        id='searchbar_filter_icon_wraper'
                        onClick={toggleFilters}
                    >
                        <FilterIcon className='searchbar_filter_icon'/>
                    </div>
                </div>

                <div className='sides_container'>
                    <div className="left_align_column" id='search_border_container'>
                        <div className='searchbar_text_container'>
                            <div className='searchbar_text_inner_container'>
                                <h1>{headerText}</h1>
                            </div>
                        </div>

                        <ul className='max_sizes_container'>
                            {props.findValue.map((data) => (
                                <props.searchElement key={data.id} data={data} isOwner={props.addData?.isOwner} togglePopUp={togglePopUp}/>
                            ))}
                        </ul>
                    </div>
                    
                    <div id='search_sticky_container'>
                        <props.rightSection 
                            data={props.searchData} 
                            handleChange={props.handleChange}  
                            educationSelect={props.educationSelect} 
                            onClick={props.fetchData} 
                            reset={props.reset}
                        />
                    </div>
                    
                    <div className={`mobile-filters ${showFilters ? 'mobile-filters--visible' : ''}`}>
                        <div className="mobile-filters-content">
                            <div className="mobile-filters-header">
                                <button className="mobile-filters-close" onClick={closeFilters}>
                                    &times;
                                </button>
                            </div>
                            <div className="mobile-filters-body">
                                <props.rightSection 
                                    data={props.searchData} 
                                    handleChange={props.handleChange} 
                                    educationSelect={props.educationSelect} 
                                    onClick={props.fetchData}
                                    reset={props.reset}
                                />
                            </div>
                        </div>
                        <div className="mobile-filters-overlay" onClick={closeFilters}></div>
                    </div>
                </div>
            </div>
        </>
    );
}


function Search_Function(props) {
    const location = useLocation();
    const { user, accessToken } = useContext(AuthContext);

    const [reset, setReset] = useState(false);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [findValue, setFindValue] = useState([]);
    const [totalFind, setTotalFind] = useState(0);
    const [searchData, setSearchData] = useState(() => {
        const params = new URLSearchParams(window.location.search);
        const typeParam = params.get("work_type") || params.get("type");
        const name = params.get("name");
        const initial = {};
        if (typeParam) initial.type = typeParam;
        if (name) initial.name = name;
        return initial;
    });

    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const observer = useRef();

    const Search_Page = props.isExtentedData ? Extended_Search_Page : Default_Search_Page;

    const resetFieldsMap = {
        city: ["university", "faculty", "level", "direction"],
        university: ["faculty", "level", "direction"],
        faculty: ["level", "direction"],
        level: ["direction"],
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const typeParam = params.get("work_type") || params.get("type");
        const name = params.get("name");
        const next = {};
        if (typeParam) next.type = typeParam;
        if (name) next.name = name;
        setSearchData(next);
    }, [location.search]);

    useEffect(() => {
        setPage(1);
        setHasMore(true);
        setFindValue([]);
    }, [searchData]);

    useEffect(() => {
        if (props.searchURL.includes('/me') && !accessToken) return;
    
        fetchData();
    }, [searchData, page, accessToken]);

    const fetchData = async () => {
        setLoading(true);

        try {
            const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {};

            const response = await axios.get(props.searchURL, {
                params: {
                    ...searchData,
                    page: page,
                },
                headers,
            });

            if (page === 1) {
                setFindValue(response.data.page_data);
            } else {
                setFindValue((prev) => [...prev, ...response.data.page_data]);
            }

            setTotalFind(response.data.total_count);
            setHasMore(response.data.has_next);
        } catch (error) {
            if (props.searchURL.includes('/me')) {
                setLoadError(true);
            } else {
                setFindValue([]);
                setTotalFind(0);
                setHasMore(false);
            }
        } finally {
            setLoading(false);
        }
    };


    const handleChange = (event) => {
        const { name, value } = event.target;

        setSearchData((prevData) => {
            const updatedData = { ...prevData, [name]: value };

            if (resetFieldsMap[name]) {
                setReset(true);
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
            setReset(false);
            setSearchData((prevData) => ({
                ...prevData,
                city: education.city,
                university: education.university,
                faculty: education.faculty,
                direction: education.direction,
                level: education.level,
            }));
        }
    };

    useEffect(() => {
        if (loading || !hasMore) return;

        const observerCallback = (entries) => {
            if (entries[0].isIntersecting) {
                setPage((prev) => prev + 1);
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
    }, [loading, hasMore]);
    
    return (
        <>
            {loading && page === 1 && <Loading_Spinner />}
            {loadError && (
                <PopUpComponent
                    isVisible={loadError}
                    displayed={<Error_POP_Element />}
                    onClose={() => {
                        setLoadError(false);
                        window.history.back();
                    }}
                />
            )}
            <Search_Page
                findValue={findValue}
                totalFind={totalFind}
                searchData={searchData}
                addData={props.addData}
                reset={reset}
                handleChange={handleChange}
                educationSelect={educationSelect}
                searchElement={props.searchElement}
                rightSection={props.rightSection}
            />

            <div id="load-more-trigger" style={{ height: "1px" }}></div>
            {loading && page > 1 && <div style={{ textAlign: "center", padding: "10px" }}>Загрузка...</div>}
        </>
    );
}

export {Search_Function};