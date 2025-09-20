import { useContext } from 'react';
import { useParams } from 'react-router-dom';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from '../contexts/authContext.jsx';
import AnomalyAlertListener from '../components/Alert/AnomalyAlertListener.jsx';
const ProtectedRoute = () => {
  const { authState } = useContext(AuthContext);
  const { oid } = useParams();

  if (authState.isLoading) return null;
  if (!authState.isAuthenticated) return <Navigate to="/signin" />;

  const userOrgId = authState.user?.organization_id;
  if (userOrgId !== oid) {
    return <Navigate to={`/${userOrgId}/dashboard`} replace />;
  }

  return (
    <>
      <Outlet />
      <AnomalyAlertListener organizationid={oid} />
    </>
  );
};

export default ProtectedRoute;