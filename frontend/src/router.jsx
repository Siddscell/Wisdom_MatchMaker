import { Link, createBrowserRouter } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import HomePage from './pages/HomePage.jsx';
import OutboxPage from './pages/OutboxPage.jsx';
import AuthPage from './pages/AuthPage.jsx';
import MyDashboardPage from './pages/MyDashboardPage.jsx';

function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-3xl font-semibold">Page not found</h1>
      <Link to="/" className="mt-4 inline-block text-accent underline underline-offset-2">
        Back to the start
      </Link>
    </div>
  );
}

export const routes = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'login', element: <AuthPage mode="login" /> },
      { path: 'register', element: <AuthPage mode="register" /> },
      { path: 'me', element: <MyDashboardPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'dev/outbox', element: <OutboxPage /> },
      { path: '*', element: <NotFound /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
