import { useEffect, useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const RONG = { ma_chuc_vu: '', ten_chuc_vu: '', cap_bac: '', mo_ta: '' }

export default function ChucVuPage() {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(RONG)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [editingId, setEditingId] = useState(null)
  const [search, setSearch] = useState('')
  const [sortAsc, setSortAsc] = useState(true)
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
    setError(''); setFieldErrors({})
    try {
      if (editingId) await client.put(`/chuc-vu/${editingId}`, form)
      else await client.post('/chuc-vu', form)
      setForm(RONG)
      setEditingId(null)
      taiDanhSach()
    } catch (err) {
      setError(err.response?.data?.error || 'Có lỗi khi thêm chức vụ')
      if (err.response?.data?.field) setFieldErrors({ [err.response.data.field]: err.response.data.error })
    }
  }

  function editPosition(cv) {
    setEditingId(cv.id)
    setForm({ ma_chuc_vu: cv.ma_chuc_vu || '', ten_chuc_vu: cv.ten_chuc_vu, cap_bac: cv.cap_bac, mo_ta: cv.mo_ta || '' })
    setError(''); setFieldErrors({})
  }

  const visible = ds.filter((cv) => `${cv.ma_chuc_vu || ''} ${cv.ten_chuc_vu}`.toLowerCase().includes(search.toLowerCase())).sort((a, b) => sortAsc ? a.cap_bac - b.cap_bac : b.cap_bac - a.cap_bac)

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
        <div className="toolbar"><input placeholder="Tìm theo mã hoặc tên chức vụ" value={search} onChange={(e) => setSearch(e.target.value)} /><button type="button" className="btn btn-outline btn-sm" onClick={() => setSortAsc((value) => !value)}>Cấp bậc {sortAsc ? '↑' : '↓'}</button></div>
        {loading ? (
          <p>Đang tải...</p>
        ) : ds.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🎖️</div>
            <div>Chưa có chức vụ nào.</div>
          </div>
        ) : (
          <div className="table-scroll"><table>
            <thead><tr><th>STT</th><th>Mã chức vụ</th><th>Tên chức vụ</th><th>Cấp bậc</th><th>Sĩ số</th><th>Mô tả</th>{user.vai_tro === 'admin' && <th></th>}</tr></thead>
            <tbody>
              {visible.map((cv, index) => (
                <tr key={cv.id}>
                  <td>{index + 1}</td><td>{cv.ma_chuc_vu || 'Chưa có mã'}</td>
                  <td className="name-cell">{cv.ten_chuc_vu}</td>
                  <td>{cv.cap_bac}</td>
                  <td>{cv.si_so}</td>
                  <td>{cv.mo_ta || '—'}</td>
                  {user.vai_tro === 'admin' && <td><button className="btn btn-outline btn-sm" onClick={() => editPosition(cv)}>Sửa</button> <button className="btn btn-danger btn-sm" onClick={() => handleXoa(cv.id)}>Xóa</button></td>}
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>

      {user.vai_tro === 'admin' && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="section-title">{editingId ? 'Sửa chức vụ' : 'Thêm chức vụ mới'}</div>
          <form onSubmit={handleThem}>
            <div className="form-grid cols-3">
              <div className="f-group">
                <label>Mã chức vụ *</label>
                <input required value={form.ma_chuc_vu} onChange={(e) => setForm((f) => ({ ...f, ma_chuc_vu: e.target.value }))} />
                {fieldErrors.ma_chuc_vu && <small className="field-error">{fieldErrors.ma_chuc_vu}</small>}
              </div>
              <div className="f-group span-2">
                <label>Tên chức vụ *</label>
                <input required value={form.ten_chuc_vu}
                  onChange={(e) => setForm((f) => ({ ...f, ten_chuc_vu: e.target.value }))} />
                {fieldErrors.ten_chuc_vu && <small className="field-error">{fieldErrors.ten_chuc_vu}</small>}
              </div>
              <div className="f-group">
                <label>Cấp bậc (số) *</label>
                <input type="number" required value={form.cap_bac}
                  onChange={(e) => setForm((f) => ({ ...f, cap_bac: e.target.value }))} />
              </div>
            </div>
            {error && <p className="flash error" style={{ marginTop: 12 }}>{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ marginTop: 14 }}>{editingId ? 'Lưu thay đổi' : 'Thêm'}</button>{editingId && <button type="button" className="btn btn-outline" style={{ marginTop: 14, marginLeft: 8 }} onClick={() => { setEditingId(null); setForm(RONG); setError('') }}>Hủy</button>}
          </form>
        </div>
      )}
    </Layout>
  )
}
