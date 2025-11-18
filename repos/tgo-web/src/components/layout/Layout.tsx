import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

/**
 * Main layout component with sidebar and content area
 */
const Layout: React.FC = () => {
  return (
    <div className="bg-gray-100 h-screen overflow-hidden font-sans antialiased">
      <div className="flex h-full w-full">
        {/* Sidebar Navigation */}
        <Sidebar />

        {/* Main Content */}
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
