import { useEffect, useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const RONG = { ma_don_vi: '', ten_don_vi: '', loai_don_vi: 'Phòng', don_vi_cha_id: '', dia_chi: '' }

export default function DonVi() {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(RONG)
  const [error, setError] = useState('')
  const { user } = useAuth()

  async function taiDanhSach() {
    setLoading(true)
    const res = await client.get('/don-vi')
    setDs(res.data)
    setLoading(false)
  }

  useEffect(() => {
    taiDanhSach()
  }, [])

  async function handleThem(e) {
    e.preventDefault()
    setError('')
    try {
      await client.post('/don-vi', { ...form, don_vi_cha_id: form.don_vi_cha_id || null })
      setForm(RONG)
      taiDanhSach()
    } catch (err) {
      setError(err.response?.data?.error || 'Có lỗi khi thêm đơn vị')
    }
  }

  async function handleXoa(id) {
    if (!confirm('Xóa đơn vị này?')) return
    try {
      await client.delete(`/don-vi/${id}`)
      taiDanhSach()
    } catch (err) {
      alert(err.response?.data?.error || 'Có lỗi khi xóa đơn vị')
    }
  }

  return (
    <Layout>
      <div className="page-title">Cơ cấu tổ chức</div>
      <div className="page-sub">Danh sách các đơn vị trực thuộc Sở Nông nghiệp và Môi trường.</div>

      <div className="card">
        {loading ? (
          <p>Đang tải...</p>
        ) : ds.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🏢</div>
            <div>Chưa có đơn vị nào.</div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Mã</th><th>Tên đơn vị</th><th>Loại</th><th>Đơn vị cha</th><th>Sĩ số</th>
                {user.vai_tro === 'admin' && <th></th>}
              </tr>
            </thead>
            <tbody>
              {ds.map((dv) => (
                <tr key={dv.id}>
                  <td>{dv.ma_don_vi}</td>
                  <td className="name-cell">{dv.ten_don_vi}</td>
                  <td>{dv.loai_don_vi || '—'}</td>
                  <td>{dv.don_vi_cha_ten || '—'}</td>
                  <td>{dv.si_so}</td>
                  {user.vai_tro === 'admin' && (
                    <td><button className="btn btn-danger btn-sm" onClick={() => handleXoa(dv.id)}>Xóa</button></td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {user.vai_tro === 'admin' && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="section-title">Thêm đơn vị mới</div>
          <form onSubmit={handleThem}>
            <div className="form-grid cols-3">
              <div className="f-group">
                <label>Mã đơn vị *</label>
                <input
                  value={form.ma_don_vi}
                  required
                  onChange={(e) => setForm((f) => ({ ...f, ma_don_vi: e.target.value }))}
                />
              </div>
              <div className="f-group span-2">
                <label>Tên đơn vị *</label>
                <input
                  value={form.ten_don_vi}
                  required
                  onChange={(e) => setForm((f) => ({ ...f, ten_don_vi: e.target.value }))}
                />
              </div>
              <div className="f-group">
                <label>Loại đơn vị</label>
                <select
                  value={form.loai_don_vi}
                  onChange={(e) => setForm((f) => ({ ...f, loai_don_vi: e.target.value }))}
                >
                  <option>Sở</option>
                  <option>Chi cục</option>
                  <option>Phòng</option>
                  <option>Đơn vị sự nghiệp</option>
                  <option>Trạm</option>
                </select>
              </div>
              <div className="f-group">
                <label>Trực thuộc</label>
                <select
                  value={form.don_vi_cha_id}
                  onChange={(e) => setForm((f) => ({ ...f, don_vi_cha_id: e.target.value }))}
                >
                  <option value="">— Không —</option>
                  {ds.map((dv) => (
                    <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>
                  ))}
                </select>
              </div>
              <div className="f-group">
                <label>Địa chỉ</label>
                <input
                  value={form.dia_chi}
                  onChange={(e) => setForm((f) => ({ ...f, dia_chi: e.target.value }))}
                />
              </div>
            </div>
            {error && <p className="flash error" style={{ marginTop: 12 }}>{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ marginTop: 14 }}>Thêm đơn vị</button>
          </form>
        </div>
      )}
    </Layout>
  )
}
