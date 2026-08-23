import { useEffect, useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const RONG = { ten_chuc_vu: '', cap_bac: '', mo_ta: '' }

export default function ChucVuPage() {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(RONG)
  const [error, setError] = useState('')
  const { user } = useAuth()

  async function taiDanhSach() {
    setLoading(true)
    const res = await client.get('/chuc-vu')
    setDs(res.data)
    setLoading(false)
  }

  useEffect(() => { taiDanhSach() }, [])

  async function handleThem(e) {
    e.preventDefault()
    setError('')
    try {
      await client.post('/chuc-vu', form)
      setForm(RONG)
      taiDanhSach()
    } catch (err) {
      setError(err.response?.data?.error || 'Có lỗi khi thêm chức vụ')
    }
  }

  async function handleXoa(id) {
    if (!confirm('Xóa chức vụ này?')) return
    try {
      await client.delete(`/chuc-vu/${id}`)
      taiDanhSach()
    } catch (err) {
      alert(err.response?.data?.error || 'Có lỗi khi xóa')
    }
  }

  return (
    <Layout>
      <div className="page-title">Danh mục chức vụ</div>
      <div className="page-sub">Sắp xếp theo cấp bậc — số càng nhỏ càng cao.</div>

      <div className="card">
        {loading ? (
          <p>Đang tải...</p>
        ) : ds.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🎖️</div>
            <div>Chưa có chức vụ nào.</div>
          </div>
        ) : (
          <table>
            <thead><tr><th>Cấp bậc</th><th>Tên chức vụ</th><th>Sĩ số</th>{user.vai_tro === 'admin' && <th></th>}</tr></thead>
            <tbody>
              {ds.map((cv) => (
                <tr key={cv.id}>
                  <td>{cv.cap_bac}</td>
                  <td className="name-cell">{cv.ten_chuc_vu}</td>
                  <td>{cv.si_so}</td>
                  {user.vai_tro === 'admin' && <td><button className="btn btn-danger btn-sm" onClick={() => handleXoa(cv.id)}>Xóa</button></td>}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {user.vai_tro === 'admin' && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="section-title">Thêm chức vụ mới</div>
          <form onSubmit={handleThem}>
            <div className="form-grid cols-3">
              <div className="f-group span-2">
                <label>Tên chức vụ *</label>
                <input required value={form.ten_chuc_vu}
                  onChange={(e) => setForm((f) => ({ ...f, ten_chuc_vu: e.target.value }))} />
              </div>
              <div className="f-group">
                <label>Cấp bậc (số) *</label>
                <input type="number" required value={form.cap_bac}
                  onChange={(e) => setForm((f) => ({ ...f, cap_bac: e.target.value }))} />
              </div>
            </div>
            {error && <p className="flash error" style={{ marginTop: 12 }}>{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ marginTop: 14 }}>Thêm</button>
          </form>
        </div>
      )}
    </Layout>
  )
}
