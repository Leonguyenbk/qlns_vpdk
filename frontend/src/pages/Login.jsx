import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [tenDangNhap, setTenDangNhap] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      await login(tenDangNhap, matKhau)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Đăng nhập thất bại')
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-heading">
          <div className="badge-lg">VPĐK</div>
          <h1>QUẢN LÝ NHÂN SỰ</h1>
          <p className="hint">Văn phòng Đăng ký đất đai — quản lý viên chức và người lao động.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="f-group">
            <label htmlFor="tdn">Tên đăng nhập</label>
            <input id="tdn" value={tenDangNhap} onChange={(e) => setTenDangNhap(e.target.value)} autoFocus />
          </div>
          <div className="f-group">
            <label htmlFor="mk">Mật khẩu</label>
            <input id="mk" type="password" value={matKhau} onChange={(e) => setMatKhau(e.target.value)} />
          </div>
          {error && <p className="error">{error}</p>}
          <button className="btn btn-primary" type="submit">Đăng nhập</button>
        </form>
      </div>
    </div>
  )
}