import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Main_Page from './main/Main.js';
import Rules from './main/Rules.js';
import About_us from './main/About_us.js';
import Ready_Task from './tasks/Ready_Task.js';
import Order_Task from './tasks/Order_Task.js';
import Ready_Tasks_Search from './search/Ready_Task_Search.js';
import Order_Tasks_Seatch from './search/Order_Task_Search.js';
import Users_Search from './search/Users_Search.js';
import User_Profile_Contoller from './user/User_Profile_Controller.js';
import User_Sold_Tasks_Search from './search/User_Sold_Tasks.js';
import User_Purchased_Tasks from './search/User_Purchased_Tasks.js';

import Create_Ready_Task from './tasks/Create_Ready_Task.js';
import Create_Order_Task from './tasks/Create_Order_Task.js';
import Create_Report from './feedbacks/Create_Report.js';
import Create_Rate from './feedbacks/Rate_Task.js'
import Create_Refund from './refunds/Create_Refund.js';

import ResponsiveHeader from '../elements/ResponsiveHeader.js';
import Footer from '../elements/Footer';

import ScrollToTop from '../elements/ScrollToTop.js';

import ContextErrorPopUpComponent from '../elements/ContextPopUp.js'

import '../css/fonts.css';
import '../css/main_page.css'
import '../css/menu_elements.css' 
import '../css/main_elements.css'
import '../css/containers.css'
import '../css/login_component.css'
import '../css/layout.css'
import '../css/user_history.css'

import { AuthProvider } from '../context/AuthContext.js';
import { WebSocketProvider } from '../context/WebsocketContext.js'

function App() {
  return (
    <Router>
      <AuthProvider>
        <WebSocketProvider>
            <ScrollToTop />
              <div className="app_container">
              <ResponsiveHeader />
              <main className="main_content">
                <Routes>
                  <Route path="/" element={<Main_Page />} />
                  <Route path="/about_us" element={<About_us />} />
                  <Route path="/rules" element={<Rules />} /> 
                  <Route path="/create_ready" element={<Create_Ready_Task />} />
                  <Route path="/create_order" element={<Create_Order_Task />} />
                  <Route path="/ready_tasks" element={<Ready_Tasks_Search />} />
                  <Route path="/order_tasks" element={<Order_Tasks_Seatch />} />
                  <Route path="/ready/:taskId" element={<Ready_Task />} />
                  <Route path="/order/:taskId" element={<Order_Task />} />
                  <Route path="/users" element={<Users_Search />} />
                  <Route path="/user/:userId" element={<User_Profile_Contoller />} />
                  <Route path="/sold_tasks/:userId" element={<User_Sold_Tasks_Search />} />
                  <Route path="/buy_tasks" element={<User_Purchased_Tasks />} /> 
                  <Route path="/create_report" element={<Create_Report />} />  
                  <Route path="/create_refund" element={<Create_Refund />} /> 
                  <Route path="/rate_task" element={<Create_Rate />} /> 
                </Routes>
              </main>
              <Footer />
              <ContextErrorPopUpComponent />
              </div>
        </WebSocketProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;