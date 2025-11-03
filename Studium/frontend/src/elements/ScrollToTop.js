import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToTop = ({ children }) => {
  const { pathname } = useLocation();

  useEffect(() => {
    // Плавный скролл вверх
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: "smooth"
    });
    
    // Дополнительно сбрасываем скролл для старых браузеров
    document.documentElement.scrollTop = 0;
  }, [pathname]);

  return children || null;
};

export default ScrollToTop;