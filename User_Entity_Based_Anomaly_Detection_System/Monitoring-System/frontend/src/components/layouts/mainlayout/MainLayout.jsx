import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Footer from './Footer';
import Header from './Header';
import VerticalNavbar from './verticalBar';

const MainLayout = () => {
  const [isNavExpanded, setIsNavExpanded] = useState(true);

  const toggleNavbar = () => {
      setIsNavExpanded(!isNavExpanded);
  }; 
  return (
    <div className="flex flex-col min-h-screen">
      <Header handleToggleNavbar={toggleNavbar} />

      <div className="flex flex-1">
        <VerticalNavbar isExpanded={isNavExpanded} />
        <main className="flex-1 p-4">
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  );
};

export default MainLayout;
