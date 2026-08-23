import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <>
      <header className="app-header topo-bg">
        <div className="brand">
          <div className="badge">VP</div>
          <div className="brand-text">
            <div className="title">Quản lý nhân sự</div>
            <div className="subtitle">Văn phòng Đăng ký đất đai</div>
          </div>
        </div>
        <nav>
          <Link to="/">Tra cứu</Link>
          <Link to="/don-vi">Đơn vị</Link>
          <Link to="/chuc-vu">Chức vụ</Link>
          <Link to="/gioi-han-chuc-vu">Giới hạn chức vụ</Link>
          <Link to="/bao-cao">Báo cáo</Link>
          {(user.vai_tro === 'admin' || user.vai_tro === 'editor') && (
            <Link to="/can-bo/moi">+ Thêm hồ sơ</Link>
          )}
          <span className="user-chip">{user.ho_ten} · {user.vai_tro}</span>
          <button className="link-btn" onClick={handleLogout}>Đăng xuất</button>
        </nav>
      </header>
      <div className="container">{children}</div>
    </>
  )
}