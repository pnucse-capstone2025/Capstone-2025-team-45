import ReactDOM from 'react-dom/client';
import theme from './themes.jsx';
import router from './routes/Router.jsx';
import './index.css';
import reportWebVitals from './reportWebVitals.js';

import { AuthProvider } from './contexts/authContext.jsx';
import { MessageProvider } from './contexts/MessageContext.jsx';
import { RouterProvider } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ThemeProvider theme={theme}>
    <AuthProvider>
      <MessageProvider>
        <RouterProvider router={router} />
      </MessageProvider>
    </AuthProvider>
  </ThemeProvider>,
);

reportWebVitals();