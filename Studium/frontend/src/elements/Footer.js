import '../css/footer.css';

import {Navigation_Item} from './main_elements.js'

function PageFooter(){
    return(
        <footer>
            <div id="footer_container">
                <div className="footer_content">
                    <ul className='row_container_footer'>
                        <Navigation_Item item_name='Помощь' id='footer_link' link='/create_report'/>
                        <Navigation_Item item_name='О нас' id='footer_link' link='/about_us'/>
                        <Navigation_Item item_name='Правила сервиса' id='footer_link' link='/rules'/>
                    </ul>
                    
                    <div className="company_info">
                        <p>©2025 ИП Добрынин Тимофей Даниилович</p>
                        <p>ИНН: 663102805653</p>
                    </div>
                </div>
            </div>
        </footer>
    );
  }


  export default PageFooter;