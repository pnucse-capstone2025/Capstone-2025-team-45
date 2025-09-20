import React from 'react';
import { createBrowserRouter } from 'react-router-dom';

import MainLayout from '../components/layouts/mainlayout/MainLayout.jsx';
import Home from '../pages/home.jsx';
import SignUp from '../pages/signup.jsx';
import SignIn from '../pages/signin/signin.jsx';
import ProtectedRoute from './ProtectedRoute.jsx';
import Dashboard from '../pages/dashboard/dashboard.jsx';
import BehaviorLogs from '../pages/behavior-logs/behavior-logs.jsx'
import Topology from '../pages/topology/topology.jsx';
import Anomaly from '../pages/anomaly/Anomaly.jsx';
import PCs from '../pages/pc_status/PCs.jsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Home />
      },
      {
        path: 'signin',
        element: <SignIn />
      },
      {
        path: 'signup',
        element: <SignUp />
      },

      {
        path: ':oid',
        element: <ProtectedRoute />,
        children: [
          {
            path: 'dashboard',
            element: <Dashboard />
          },
          {
            path: 'behavior-logs',
            element: <BehaviorLogs />
          },
          {
            path: 'topology',
            element: <Topology />
          },
          {
            path: 'anomaly',
            element: <Anomaly />
          },
          {
            path: 'PCs',
            element: <PCs />
          }
        ]
      }
    ]
  }
]);

export default router;
