import { useCallback, useEffect, useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const EMPTY = { don_vi_id: '', chuc_vu_id: '', so_luong_toi_da: 1, ghi_chu: '' }

export default function GioiHanChucVu() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [units, setUnits] = useState([])
  const [positions, setPositions] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [editingId, setEditingId] = useState(null)
  const [filters, setFilters] = useState({ q: '', trang_thai: '' })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const [limits, unitList, positionList] = await Promise.all([
      client.get('/gioi-han-chuc-vu-don-vi', { params: filters }),
      client.get('/don-vi'),
      client.get('/chuc-vu'),
    ])
    setItems(limits.data); setUnits(unitList.data); setPositions(positionList.data); setLoading(false)
  }, [filters])

  useEffect(() => { load() }, [load])

  function setField(name, value) { setForm((current) => ({ ...current, [name]: value })) }

  async function submit(event) {
    event.preventDefault(); setError(''); setFieldErrors({})
    try {
      const payload = { ...form, don_vi_id: form.don_vi_id || null, chuc_vu_id: form.chuc_vu_id || null }
      if (editingId) await client.put(`/gioi-han-chuc-vu-don-vi/${editingId}`, payload)
      else await client.post('/gioi-han-chuc-vu-don-vi', payload)
      setForm(EMPTY); setEditingId(null); load()
    } catch (err) {
      setError(err.response?.data?.error || 'Không thể lưu cấu hình')
      if (err.response?.data?.field) setFieldErrors({ [err.response.data.field]: err.response.data.error })
    }
  }

  async function remove(id) {
    if (!confirm('Xóa cấu hình giới hạn này?')) return
    try { await client.delete(`/gioi-han-chuc-vu-don-vi/${id}`); load() } catch (err) { setError(err.response?.data?.error || 'Không thể xóa cấu hình') }
  }

  function edit(item) {
    setEditingId(item.id); setForm({ don_vi_id: item.don_vi_id, chuc_vu_id: item.chuc_vu_id, so_luong_toi_da: item.so_luong_toi_da, ghi_chu: item.ghi_chu || '' }); setError('')
  }

  return <Layout>
    <div className="page-title">Giới hạn chức vụ theo đơn vị</div>
    <div className="page-sub">Theo dõi định biên, số hiện tại và vị trí còn trống.</div>
    <div className="card">
      <div className="toolbar"><input placeholder="Tìm theo mã hoặc tên" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} /><select value={filters.trang_thai} onChange={(e) => setFilters({ ...filters, trang_thai: e.target.value })}><option value="">Mọi trạng thái</option><option value="con_vi_tri">Còn vị trí</option><option value="da_du">Đã đủ</option><option value="vuot">Vượt giới hạn</option></select></div>
      {loading ? <p>Đang tải...</p> : items.length === 0 ? <div className="empty-state"><div className="icon">▦</div><div>Chưa có cấu hình giới hạn.</div></div> : <div className="table-scroll"><table><thead><tr><th>STT</th><th>Mã đơn vị</th><th>Tên đơn vị</th><th>Mã chức vụ</th><th>Tên chức vụ</th><th>Tối đa</th><th>Hiện tại</th><th>Còn lại</th><th>Trạng thái</th><th>Ghi chú</th><th></th></tr></thead><tbody>{items.map((item, index) => <tr key={item.id}><td>{index + 1}</td><td>{item.ma_don_vi}</td><td>{item.ten_don_vi}</td><td>{item.ma_chuc_vu || 'Chưa có mã'}</td><td>{item.ten_chuc_vu}</td><td>{item.so_luong_toi_da}</td><td>{item.so_luong_hien_tai}</td><td>{item.so_luong_con_lai}</td><td><span className={`tag ${item.vuot_gioi_han ? 'tag-over' : item.da_dat_gioi_han ? 'tag-full' : item.so_luong_con_lai === 1 ? 'tag-warning' : 'tag-available'}`}>{item.vuot_gioi_han ? 'Vượt giới hạn' : item.da_dat_gioi_han ? 'Đã đủ' : item.so_luong_con_lai === 1 ? 'Sắp đủ' : 'Còn vị trí'}</span></td><td>{item.ghi_chu || '—'}</td><td>{user.vai_tro === 'admin' && <><button className="btn btn-outline btn-sm" onClick={() => edit(item)}>Sửa</button> <button className="btn btn-danger btn-sm" onClick={() => remove(item.id)}>Xóa</button></>}</td></tr>)}</tbody></table></div>}
    </div>
    {user.vai_tro === 'admin' && <div className="card" style={{ marginTop: 20 }}><div className="section-title">{editingId ? 'Sửa cấu hình' : 'Thêm cấu hình'}</div><form onSubmit={submit}><div className="form-grid cols-3"><div className="f-group"><label>Đơn vị *</label><select value={form.don_vi_id} onChange={(e) => setField('don_vi_id', e.target.value)} required><option value="">— Chọn đơn vị —</option>{units.map((item) => <option key={item.id} value={item.id}>{item.ma_don_vi} - {item.ten_don_vi}</option>)}</select>{fieldErrors.don_vi_id && <small className="field-error">{fieldErrors.don_vi_id}</small>}</div><div className="f-group"><label>Chức vụ *</label><select value={form.chuc_vu_id} onChange={(e) => setField('chuc_vu_id', e.target.value)} required><option value="">— Chọn chức vụ —</option>{positions.map((item) => <option key={item.id} value={item.id}>{item.ma_chuc_vu || 'Chưa có mã'} - {item.ten_chuc_vu}</option>)}</select>{fieldErrors.chuc_vu_id && <small className="field-error">{fieldErrors.chuc_vu_id}</small>}</div><div className="f-group"><label>Số lượng tối đa *</label><input type="number" min="1" value={form.so_luong_toi_da} onChange={(e) => setField('so_luong_toi_da', e.target.value)} required />{fieldErrors.so_luong_toi_da && <small className="field-error">{fieldErrors.so_luong_toi_da}</small>}</div><div className="f-group span-3"><label>Ghi chú</label><input value={form.ghi_chu} onChange={(e) => setField('ghi_chu', e.target.value)} /></div></div>{error && <p className="flash error">{error}</p>}<button type="submit" className="btn btn-primary">{editingId ? 'Lưu thay đổi' : 'Thêm cấu hình'}</button>{editingId && <button type="button" className="btn btn-outline" style={{ marginLeft: 8 }} onClick={() => { setEditingId(null); setForm(EMPTY) }}>Hủy</button>}</form></div>}
  </Layout>
}
