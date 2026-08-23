import { useEffect, useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const RONG = { ma_don_vi: '', ten_don_vi: '', loai_don_vi: 'Phòng', don_vi_cha_id: '', dia_chi: '', ghi_chu: '' }

export default function DonVi() {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(RONG)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [editingId, setEditingId] = useState(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [parentFilter, setParentFilter] = useState('')
  const [page, setPage] = useState(1)
  const { user } = useAuth()

  const pageSize = 8
  const filtered = ds.filter((dv) => {
    const text = `${dv.ma_don_vi} ${dv.ten_don_vi}`.toLowerCase()
    return text.includes(search.toLowerCase()) && (!typeFilter || dv.loai_don_vi === typeFilter) &&
      (!parentFilter || String(dv.don_vi_cha_id || '') === parentFilter)
  })
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize)

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
    setFieldErrors({})
    try {
      const payload = { ...form, don_vi_cha_id: form.don_vi_cha_id || null }
      if (editingId) await client.put(`/don-vi/${editingId}`, payload)
      else await client.post('/don-vi', payload)
      setForm(RONG)
      setEditingId(null)
      taiDanhSach()
    } catch (err) {
      setError(err.response?.data?.error || 'Có lỗi khi thêm đơn vị')
      if (err.response?.data?.field) setFieldErrors({ [err.response.data.field]: err.response.data.error })
    }
  }

  function editUnit(dv) {
    setEditingId(dv.id)
    setForm({ ma_don_vi: dv.ma_don_vi, ten_don_vi: dv.ten_don_vi, loai_don_vi: dv.loai_don_vi || 'Phòng', don_vi_cha_id: dv.don_vi_cha_id || '', dia_chi: dv.dia_chi || '', ghi_chu: dv.ghi_chu || '' })
    setError('')
    setFieldErrors({})
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
      <div className="page-sub">Danh mục phòng ban và đơn vị thuộc Văn phòng Đăng ký đất đai.</div>

      <div className="card">
        <div className="toolbar">
          <input placeholder="Tìm theo mã hoặc tên đơn vị" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} />
          <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}><option value="">Mọi loại đơn vị</option>{['Sở', 'Chi cục', 'Phòng', 'Đơn vị sự nghiệp', 'Trạm'].map((type) => <option key={type}>{type}</option>)}</select>
          <select value={parentFilter} onChange={(e) => { setParentFilter(e.target.value); setPage(1) }}><option value="">Mọi đơn vị cấp trên</option>{ds.map((dv) => <option key={dv.id} value={dv.id}>{dv.ten_don_vi}</option>)}</select>
        </div>
        {loading ? (
          <p>Đang tải...</p>
        ) : ds.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🏢</div>
            <div>Chưa có đơn vị nào.</div>
          </div>
        ) : (
          <div className="table-scroll"><table>
            <thead>
              <tr>
                <th>STT</th><th>Mã</th><th>Tên đơn vị</th><th>Loại</th><th>Đơn vị cha</th><th>Sĩ số</th><th>Địa chỉ</th>
                {user.vai_tro === 'admin' && <th></th>}
              </tr>
            </thead>
            <tbody>
              {ds.map((dv) => (
                <tr key={dv.id}>
                  <td>{(page - 1) * pageSize + visible.indexOf(dv) + 1}</td>
                  <td>{dv.ma_don_vi}</td>
                  <td className="name-cell">{dv.ten_don_vi}</td>
                  <td>{dv.loai_don_vi || '—'}</td>
                  <td>{dv.don_vi_cha_ten || '—'}</td>
                  <td>{dv.si_so}</td>
                  <td>{dv.dia_chi || '—'}</td>
                  {user.vai_tro === 'admin' && (
                    <td><button className="btn btn-outline btn-sm" onClick={() => editUnit(dv)}>Sửa</button> <button className="btn btn-danger btn-sm" onClick={() => handleXoa(dv.id)}>Xóa</button></td>
                  )}
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
        {filtered.length > pageSize && <div className="pagination"><button className="btn btn-outline btn-sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Trước</button><span>Trang {page} / {Math.ceil(filtered.length / pageSize)}</span><button className="btn btn-outline btn-sm" disabled={page >= Math.ceil(filtered.length / pageSize)} onClick={() => setPage(page + 1)}>Sau</button></div>}
      </div>

      {user.vai_tro === 'admin' && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="section-title">{editingId ? 'Sửa đơn vị' : 'Thêm đơn vị mới'}</div>
          <form onSubmit={handleThem}>
            <div className="form-grid cols-3">
              <div className="f-group">
                <label>Mã đơn vị *</label>
                <input
                  value={form.ma_don_vi}
                  required
                  onChange={(e) => setForm((f) => ({ ...f, ma_don_vi: e.target.value }))}
                />
                {fieldErrors.ma_don_vi && <small className="field-error">{fieldErrors.ma_don_vi}</small>}
              </div>
              <div className="f-group span-2">
                <label>Tên đơn vị *</label>
                <input
                  value={form.ten_don_vi}
                  required
                  onChange={(e) => setForm((f) => ({ ...f, ten_don_vi: e.target.value }))}
                />
                {fieldErrors.ten_don_vi && <small className="field-error">{fieldErrors.ten_don_vi}</small>}
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
            <button type="submit" className="btn btn-primary" style={{ marginTop: 14 }}>{editingId ? 'Lưu thay đổi' : 'Thêm đơn vị'}</button>{editingId && <button type="button" className="btn btn-outline" style={{ marginTop: 14, marginLeft: 8 }} onClick={() => { setEditingId(null); setForm(RONG); setError('') }}>Hủy</button>}
          </form>
        </div>
      )}
    </Layout>
  )
}
