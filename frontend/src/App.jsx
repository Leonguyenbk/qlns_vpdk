import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import DanhSach from './pages/DanhSach'
import ChiTiet from './pages/ChiTiet'
import DonVi from './pages/DonVi'
import ChucVuPage from './pages/ChucVu'
import GioiHanChucVu from './pages/GioiHanChucVu'
import Form from './pages/Form'

function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><DanhSach /></PrivateRoute>} />
          <Route path="/can-bo/moi" element={<PrivateRoute><Form /></PrivateRoute>} />
          <Route path="/can-bo/:id" element={<PrivateRoute><ChiTiet /></PrivateRoute>} />
          <Route path="/can-bo/:id/sua" element={<PrivateRoute><Form /></PrivateRoute>} />
          <Route path="/don-vi" element={<PrivateRoute><DonVi /></PrivateRoute>} />
          <Route path="/chuc-vu" element={<PrivateRoute><ChucVuPage /></PrivateRoute>} />
          <Route path="/gioi-han-chuc-vu" element={<PrivateRoute><GioiHanChucVu /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}